"""Teaching interactions and selectable traditional/KP matchmaking workflows."""
import functools
import importlib.util
import json
import re
import shutil
import threading
import unittest
import fitz
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError, expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def close_report(preview):
    with preview.expect_event('close'):
        try:preview.get_by_role('button',name='Close preview',exact=True).click()
        except PlaywrightError:
            if not preview.is_closed():raise  # Chromium can close before the click response arrives.
    if not preview.is_closed():raise AssertionError('The Close preview button did not close its window.')

class TutorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/index.html'
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.thread.join(timeout=5);cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True);self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.goto(self.url,timeout=60000);self.page.wait_for_function('window.KPTutorial && window.KPMatchmaking && document.getElementById("kp-teaching-tools")',timeout=60000)
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def draw(self,tool='ellipse'):
        self.page.locator('#teach-tool').select_option(tool);canvas=self.page.locator('.kp-teach-canvas');r=canvas.bounding_box();self.page.mouse.move(r['x']+80,r['y']+100);self.page.mouse.down();self.page.mouse.move(r['x']+200,r['y']+150,steps=7);self.page.mouse.up()
    def test_compact_tools_work_across_tabs_and_preserve_chart(self):
        before=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})')
        self.page.locator('#quick-tutorial').click();expect(self.page.locator('#kp-teaching-tools')).to_be_visible();self.assertEqual(self.page.evaluate('KPTutorial.getState().tab'),'home');expect(self.page.locator('#tutorial')).to_have_count(0);expect(self.page.locator('#kp-teaching-tools button')).to_have_count(6)
        self.draw();expect(self.page.locator('[data-teaching-drawing]')).to_have_count(1);self.page.locator('#teach-undo').click();expect(self.page.locator('[data-teaching-drawing]')).to_have_count(0);self.page.locator('#teach-redo').click();expect(self.page.locator('[data-teaching-drawing]')).to_have_count(1)
        self.page.locator('#quick-nadi-astrology').click();self.page.wait_for_function('KPTutorial.getState().tab==="nadi-astrology"');expect(self.page.locator('[data-teaching-drawing]')).to_have_count(0);self.draw('arrow');expect(self.page.locator('[data-teaching-drawing]')).to_have_count(1);self.page.locator('#teach-zoom-in').click();expect(self.page.locator('#teach-zoom-label')).to_have_text('110%');self.page.locator('#teach-fit').click();expect(self.page.locator('#teach-zoom-label')).to_have_text('100%')
        self.page.locator('#quick-home').click();self.page.wait_for_function('KPTutorial.getState().tab==="home"');expect(self.page.locator('[data-teaching-drawing]')).to_have_count(1);self.page.locator('#teach-clear').click();expect(self.page.locator('[data-teaching-drawing]')).to_have_count(0);self.page.locator('#teach-tool').select_option('text');self.page.locator('#teach-label').fill('कुंडली <img src=x>');r=self.page.locator('.kp-teach-canvas').bounding_box();self.page.mouse.click(r['x']+80,r['y']+100);expect(self.page.locator('[data-teaching-drawing]')).to_have_text('कुंडली <img src=x>');expect(self.page.locator('.kp-teach-canvas img')).to_have_count(0)
        self.page.locator('#quick-tutorial').click();expect(self.page.locator('#kp-teaching-tools')).to_be_hidden();self.assertEqual(before,self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})'))
    def test_removed_csv_buttons_and_time_slice_workspace(self):
        self.page.locator('#quick-nadi-astrology').click();expect(self.page.locator('#na-print,#na-export')).to_have_count(0);expect(self.page.locator('#nadi-astrology-preview')).to_be_visible()
        self.page.locator('#quick-south9').click();expect(self.page.locator('#time-slices,.kundali-time-slices-link')).to_have_count(0)
        self.page.locator('#quick-prediction').click()
        for category in ['house-results','events']:self.page.locator('#pred-tab-'+category).click()
        self.page.locator('#quick-event-promise').click();expect(self.page.locator('#ep-timing-panel,#ep-find-time,#ep-query-date,#ep-show-aspects,#ep-aspect-mount')).to_have_count(0);self.assertNotIn('Event date / time search',self.page.evaluate('KPEventOutcome.snapshot()'));self.assertNotIn('Western aspect evidence',self.page.evaluate('KPEventOutcome.snapshot()'));expect(self.page.locator('#ep-outcome-result')).to_contain_text('Result:')
        expect(self.page.locator('#ep-simple-preview')).to_have_text('Preview · Print / PDF')
        with self.page.expect_popup() as opened:self.page.locator('#ep-simple-preview').click()
        preview=opened.value;expect(preview.get_by_role('button',name='Print / Save PDF',exact=True)).to_be_visible();preview.evaluate('()=>{window.printCalls=0;window.print=()=>window.printCalls++;}');preview.get_by_role('button',name='Print / Save PDF',exact=True).click();self.assertEqual(preview.evaluate('window.printCalls'),1);preview.get_by_role('button',name='Zoom +',exact=True).click();self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>Number(n.style.zoom)'),1.1);preview.get_by_role('button',name='Zoom −',exact=True).click();self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>Number(n.style.zoom)'),1);close_report(preview);self.assertTrue(preview.is_closed())
        self.assertEqual(self.page.evaluate("[...document.querySelectorAll('button,a')].filter(n=>/csv/i.test(n.textContent)).map(n=>n.textContent.trim())"),[])
        self.page.locator('#quick-tutorial').click();self.page.set_viewport_size({'width':390,'height':844});expect(self.page.locator('#kp-teaching-tools')).to_be_visible();self.assertLessEqual(self.page.locator('#kp-teaching-tools').bounding_box()['width'],390)
    def test_simple_gemstones_follow_rule_and_print_stotra_on_one_a4_page(self):
        self.page.locator('#quick-gemstones').click()
        self.assertEqual(self.page.locator('#gemstones select:visible').count(),2)
        self.assertEqual(self.page.locator('#gemstones input:visible').count(),0)
        native=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})');native_name=self.page.locator('#name').input_value()
        for mode in ['kp','vedic']:
            self.page.locator('#gem-mode').select_option(mode)
            if mode=='kp':self.page.locator('#gem-event').select_option('childbirth')
            data=self.page.evaluate('KPGemstones.getData()')
            self.assertTrue(data['ready']);self.assertEqual(data['roles'],['planet','star','sub']);self.assertEqual(data['required'],[2,5,11] if mode=='kp' else [1,5,11])
            selected=[r for r in data['results'] if r['qualifies']]
            self.assertEqual(self.page.locator('#gem-results tr').count(),len(selected))
            for row in selected:
                if mode=='kp':self.assertFalse(row['retrograde']);self.assertFalse(row['combust'])
                if mode=='kp':self.assertEqual(row['score'],max(r['score'] for r in data['results'] if r['eligible']))
                else:self.assertTrue(row['ownership'])
            with self.page.expect_popup() as opened:self.page.locator('#gemstones-preview').click()
            preview=opened.value;preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale')
            expect(preview.locator('[data-navagraha]')).to_have_count(9)
            expect(preview.locator('.gem-stotra-phala')).to_contain_text('व्यासविरचितं')
            original=self.page.evaluate('JSON.parse(document.getElementById("kp-personal-prediction-rules").textContent).entries.find(r=>r.categoryId==="gemstones"&&r.key==="RatnaH").value').replace(r'\n','\n')
            self.assertEqual(preview.locator('[data-ratna-key="RatnaH"] p').inner_text(),original)
            self.assertEqual(preview.locator('.gem-report-table tbody tr').count(),len(selected))
            bounds=preview.locator('.gem-one-page').evaluate('n=>({bottom:n.getBoundingClientRect().bottom,pageBottom:n.closest(".report-page").getBoundingClientRect().bottom,scale:n.closest(".report-page").dataset.a4Scale})')
            self.assertLessEqual(bounds['bottom'],bounds['pageBottom']);self.assertGreater(float(bounds['scale']),.75)
            document=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(document),1)
            text=document[0].get_text();self.assertIn('Original Ratna guidance',text);self.assertIn('affordability',text);self.assertIn('Gemstone recommendations',text);self.assertIn(native_name,text);self.assertIn('सम्पूर्णम्',text);document.close();preview.close()
        self.assertEqual(native,self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})'))

    def test_traditional_and_kp_modes_have_independent_selected_reports(self):
        self.page.locator('#quick-matchmaking').click();expect(self.page.locator('#mm-traditional-charts svg')).to_have_count(2);expect(self.page.locator('#mm-kp-panel')).to_be_visible();baseline=self.page.evaluate('KPMatchmaking.getData().ashtakoota.total');self.page.locator('[data-mm-method="traditional"]').click();expect(self.page.locator('#mm-kp-panel')).to_be_hidden();expect(self.page.locator('#mm-traditional-panel')).to_be_visible();expect(self.page.locator('#mm-total')).to_have_text(str(baseline))
        report=self.page.evaluate('KPMatchmaking.snapshot()');self.assertIn('data-mm-report-mode="traditional"',report);self.assertIn('Traditional Ashtakoota',report);self.assertNotIn('configured KP compatibility index',report)
        self.page.locator('[data-mm-method="kp"]').click();expect(self.page.locator('#mm-traditional-panel')).to_be_hidden();expect(self.page.locator('#mm-kp-panel')).to_be_visible();report=self.page.evaluate('KPMatchmaking.snapshot()');self.assertIn('configured KP compatibility index',report);self.assertNotIn('Traditional Ashtakoota',report)
        self.page.locator('[data-mm-method="both"]').click();report=self.page.evaluate('KPMatchmaking.snapshot()');self.assertIn('Traditional Ashtakoota',report);self.assertIn('configured KP compatibility index',report);self.assertEqual(baseline,self.page.evaluate('KPMatchmaking.getData().ashtakoota.total'))
    def test_dasha_promise_calculates_from_real_model_and_exact_home_periods(self):
        self.page.locator('#quick-dasha-promise').click()
        expect(self.page.locator('#dp-layers .dp-layer')).to_have_count(5)
        self.assertTrue(self.page.evaluate('KPDashaPromise.getData().ready'))
        # Position-only models must work without a caller-specific "ready" flag.
        self.assertTrue(self.page.evaluate('''()=>{const model=structuredClone(currentKPModel);delete model.ready;const d=KPDashaPromise.getData();return KPDashaPromise.analyze(model,d.rule,d.md,d.ad).ready}'''))
        expected=self.page.evaluate('''()=>{const h=KPHomeDasha.getData(),civil=Date.parse(document.getElementById('dp-date').value+'T'+document.getElementById('dp-time').value+'Z')+(h.timeZoneHours-Number(document.getElementById('dp-offset').value))*3600000,md=h.levels[0].rows.find(p=>p.startMs<=civil&&civil<p.endMs),ad=KPHomeDasha.subdivide(md).find(p=>p.startMs<=civil&&civil<p.endMs);return [new Date(Math.max(md.startMs,ad.startMs)-h.timeZoneHours*3600000).toISOString(),new Date(Math.min(md.endMs,ad.endMs)-h.timeZoneHours*3600000).toISOString()]}''')
        self.assertEqual(self.page.locator('#dp-period').get_attribute('data-start-u-t-c'),expected[0])
        self.assertEqual(self.page.locator('#dp-period').get_attribute('data-end-u-t-c'),expected[1])
        # Auto fills the current chain once, while both dropdowns remain editable.
        expect(self.page.locator('#dp-md')).to_be_enabled();expect(self.page.locator('#dp-ad')).to_be_enabled()
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        self.page.locator('#dp-md').select_option('1');self.page.locator('#dp-ad').select_option('2')
        chosen=self.page.evaluate('KPDashaPromise.refresh()')
        expect(self.page.locator('#dp-md')).to_have_value('1');expect(self.page.locator('#dp-ad')).to_have_value('2')
        self.page.locator('input[name="dp-mode-radio"][value="manual"]').check()
        self.page.locator('#dp-house-0').fill('2 6 10 11');self.page.locator('#dp-house-0').dispatch_event('change')
        self.assertEqual(self.page.evaluate('KPDashaPromise.getData().layers[0].houses'),[2,6,10,11])
        self.page.locator('#dp-use-0').uncheck();self.assertFalse(self.page.evaluate('KPDashaPromise.getData().layers[0].enabled'))
        self.page.locator('#dp-calculate').click();expect(self.page.locator('#dp-status')).to_contain_text('Calculation complete',timeout=90000)
        self.assertTrue(self.page.evaluate('KPDashaPromise.getData().calculated'))
        expect(self.page.locator('#dp-md')).to_have_value('1');expect(self.page.locator('#dp-ad')).to_have_value('2')
        self.assertEqual(self.page.evaluate('KPDashaPromise.getData().md'),chosen['md']);self.assertEqual(self.page.evaluate('KPDashaPromise.getData().ad'),chosen['ad'])
        expect(self.page.locator('#dp-sun-transits')).to_contain_text('Sun rule:')
        self.assertTrue(self.page.evaluate('''()=>{const d=KPDashaPromise.getData(),m=currentKPModel,md=KPDisplay.longitudeDetails(m.planets.find(p=>p.id===d.md).longitude),ad=KPDisplay.longitudeDetails(m.planets.find(p=>p.id===d.ad).longitude);return d.sun.length>0&&d.sun.every(row=>{const at=new Date((Date.parse(row.start)+Date.parse(row.end))/2),sun=KPDisplay.longitudeDetails(KPEphemeris.positions(at).Su*3600);return sun.signIndex===md.signIndex&&sun.nakIndex===ad.nakIndex||sun.signIndex===ad.signIndex&&sun.nakIndex===md.nakIndex;});}'''))
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        # Every returned interval is inside the selected AD, including clipped birth ADs.
        valid=self.page.evaluate('''()=>{const d=KPDashaPromise.getData(),a=Date.parse(document.getElementById('dp-period').dataset.startUTC),b=Date.parse(document.getElementById('dp-period').dataset.endUTC),h=KPHomeDasha.getData();return [...d.outer,...d.sun].every(p=>Date.parse(p.start)>=a&&Date.parse(p.end)<=b&&Date.parse(p.start)<Date.parse(p.end))&&d.pd.every(p=>p.startMs-h.timeZoneHours*3600000>=a&&p.endMs-h.timeZoneHours*3600000<=b)}''')
        self.assertTrue(valid)
        with self.page.expect_popup() as opened:self.page.locator('#dasha-promise-preview').click()
        preview=opened.value;expect(preview.locator('.dp-report')).to_contain_text('Calculation complete');self.assertGreater(len(preview.pdf(format='A4')),10000);preview.close()
        self.page.locator('#dp-house-0').fill('13');self.page.locator('#dp-house-0').dispatch_event('change');expect(self.page.locator('#dp-status')).to_contain_text('house numbers 1–12')
        self.assertFalse(self.page.evaluate('KPDashaPromise.getData().ready'))

    def test_sample_pair_short_range_diagnostics_next_period_and_moon_refinement(self):
        self.page.locator('#quick-matchmaking').click();self.page.locator('[data-mm-method="kp"]').click()
        records={'boy':{'name':'Aniket Kolate','date':'1999-06-02','time':'15:45:00','timezone':'5.5','dst':'0','place':'Pune','latitude':'18.52','longitude':'73.85'},'girl':{'name':'Vaishnavi Choudhari','date':'2002-08-16','time':'11:34:00','timezone':'5.5','dst':'0','place':'Loni Kalbhor','latitude':'18.48','longitude':'74.01'}}
        native=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})')
        self.page.evaluate("r=>{for(const [side,record] of Object.entries(r))for(const [key,value] of Object.entries(record))document.getElementById('mm-'+side+'-'+key).value=value;KPMatchmaking.refresh();}",records)
        self.page.locator('.mm-marriage-options summary').click()
        self.page.locator('#mm-kp-date').fill('2026-10-09');self.page.locator('#mm-kp-time').fill('00:00:00');self.page.locator('#mm-kp-range').select_option('month');self.page.locator('#mm-kp-find').click();self.page.wait_for_function('KPMatchmaking.getMarriageData().ready')
        month=self.page.evaluate('KPMatchmaking.getMarriageData()');self.assertEqual(month['rows'],[]);self.assertEqual(month['diagnostics']['boy']['count'],0);self.assertGreater(month['diagnostics']['girl']['count'],0);expect(self.page.locator('.mm-marriage-diagnostics article')).to_have_count(2)
        self.page.locator('#mm-kp-next-period').click();self.page.wait_for_function('KPMatchmaking.getMarriageData().ready');long=self.page.evaluate('KPMatchmaking.getMarriageData()');self.assertEqual(long['range'],'13years');self.assertGreater(len(long['rows']),0);expect(self.page.locator('#mm-kp-range')).to_have_value('13years')
        for row in long['rows']:
            self.assertGreaterEqual(row['start'],long['start']);self.assertLessEqual(row['end'],long['end']);self.assertLess(row['start'],row['end'])
            for side in ['boy','girl']:
                self.assertTrue(all(set(p['houses'])&{2,7,11} for p in row[side]));self.assertTrue({2,7,11}.issubset({h for p in row[side] for h in p['houses']}))
        self.page.locator('#mm-kp-refine').check();self.page.locator('#mm-kp-find').click();self.page.wait_for_function('KPMatchmaking.getMarriageData().ready',timeout=60000);refined=self.page.evaluate('KPMatchmaking.getMarriageData()');self.assertTrue(refined['refined']);self.assertEqual(refined['jointPeriodCount'],long['jointPeriodCount'])
        for row in refined['rows']:
            self.assertTrue(any(row['start']>=p['start'] and row['end']<=p['end'] for p in long['rows']));self.assertIn(row['star'],refined['allowedIds']);self.assertIn(row['sub'],refined['allowedIds'])
        self.page.locator('[data-mm-method="traditional"]').click()
        with self.page.expect_popup() as opened:self.page.locator('#mm-calculate').click()
        preview=opened.value;expect(preview.locator('.mm-format-planets')).to_have_count(2);expect(preview.locator('[data-mm-report-planet]')).to_have_count(18);expect(preview.locator('[data-mm-chart-planet]')).to_have_count(18);expect(preview.locator('.mm-format-scores')).to_be_visible();expect(preview.locator('.mm-format-report')).to_contain_text('गुण विचार');pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(pdf),1);self.assertIn('Astrologer:',pdf[0].get_text());self.assertIn('Aniket Kolate',pdf[0].get_text());pdf.close();preview.close()
        self.assertEqual(native,self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})'))

class PrivateTutorialTests(unittest.TestCase):
    def test_private_teaching_and_both_matchmaking_methods(self):
        spec=importlib.util.spec_from_file_location('tutorial_private_server',ROOT/'protected/server.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);engine=module.Engine();server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler);server.engine=engine;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));url=f'http://127.0.0.1:{server.server_port}';page.goto(url);expect(page.locator('#quick-tutorial')).to_be_visible(timeout=60000);page.locator('#quick-tutorial').click();expect(page.locator('#kp-teaching-tools')).to_be_visible();page.locator('#teach-tool').select_option('ellipse');r=page.locator('.kp-teach-canvas').bounding_box();page.mouse.move(r['x']+80,r['y']+100);page.mouse.down();page.mouse.move(r['x']+200,r['y']+150,steps=5);page.mouse.up();expect(page.locator('[data-teaching-drawing]')).to_have_count(1)
                page.locator('#quick-matchmaking').click();expect(page.locator('#mm-traditional-charts svg')).to_have_count(2,timeout=30000);expect(page.locator('#kp-teaching-tools')).to_be_visible();page.locator('#teach-tool').select_option('pointer');page.locator('[data-mm-method="traditional"]').click();expect(page.locator('#mm-kp-panel')).to_be_hidden(timeout=30000);expect(page.locator('#mm-traditional-panel')).to_be_visible();page.locator('#teach-tool').select_option('pointer')
                with page.expect_popup() as opened:page.locator('#mm-calculate').click()
                preview=opened.value;expect(preview.locator('.mm-format-scores')).to_be_visible(timeout=30000)
                import fitz
                pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');self.assertEqual(len(pdf),1);self.assertIn('Astrologer:',pdf[0].get_text());pdf.close();preview.close();page.locator('[data-mm-method="kp"]').click();expect(page.locator('#mm-kp-panel')).to_be_visible(timeout=30000);page.locator('#mm-kp-find').click();expect(page.locator('.mm-marriage-diagnostics article')).to_have_count(2,timeout=60000);page.locator('#quick-south9').click();expect(page.locator('#time-slices')).to_have_count(0,timeout=30000);self.assertEqual(page.evaluate("[...document.querySelectorAll('button')].filter(n=>/csv/i.test(n.textContent)).length"),0);page.locator('#quick-tutorial').click();page.locator('#quick-event-promise').click();expect(page.locator('#event-promise')).to_have_class('tab active',timeout=30000);expect(page.locator('#ep-timing-panel,#ep-find-time')).to_have_count(0);expect(page.locator('#ep-simple-preview')).to_have_text('Preview · Print / PDF')
                with page.expect_popup() as opened:page.locator('#ep-simple-preview').click()
                event_preview=opened.value;expect(event_preview.get_by_role('button',name='Print / Save PDF',exact=True)).to_be_visible(timeout=30000);self.assertNotIn('Event date / time search',event_preview.locator('body').inner_text());event_preview.get_by_role('button',name='Zoom +',exact=True).click();self.assertAlmostEqual(event_preview.locator('.report-page').evaluate('n=>Number(n.style.zoom)'),1.1);event_preview.get_by_role('button',name='Zoom −',exact=True).click();self.assertAlmostEqual(event_preview.locator('.report-page').evaluate('n=>Number(n.style.zoom)'),1);close_report(event_preview);self.assertTrue(event_preview.is_closed());page.locator('#quick-gemstones').click();expect(page.locator('#gemstones')).to_have_class('tab active',timeout=30000);self.assertEqual(page.locator('#gemstones select:visible').count(),2);self.assertEqual(page.locator('#gemstones input:visible').count(),0)
                page.locator('#gem-event').select_option('childbirth');expect(page.locator('#gem-event-proof')).to_contain_text('2, 5, 11',timeout=30000)
                with page.expect_popup() as opened:page.locator('#gemstones-preview').click()
                preview=opened.value;expect(preview.locator('[data-navagraha]')).to_have_count(9,timeout=30000);preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale');document=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(document),1);self.assertIn('affordability',document[0].get_text());self.assertIn('सम्पूर्णम्',document[0].get_text());document.close();preview.close()
                report=page.request.get(url+'/print');self.assertEqual(report.status,200);self.assertIn('"gemstones"',report.text());self.assertEqual(errors,[]);self.assertEqual(page.request.get(url+'/index.html').status,404);self.assertEqual(page.request.get(url+'/tutorial.js').status,200);browser.close()

        finally:
            server.shutdown();thread.join(timeout=5);server.server_close();engine.close()
