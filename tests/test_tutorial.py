"""Teaching interactions and selectable traditional/KP matchmaking workflows."""
import functools
import importlib.util
import json
import re
import shutil
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

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
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True);self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.goto(self.url,timeout=60000);self.page.wait_for_function('window.KPTutorial && window.KPMatchmaking && document.getElementById("tut-lessons").children.length===12',timeout=60000)
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def tutorial(self):
        self.page.locator('#quick-tutorial').click();expect(self.page.locator('#tutorial')).to_be_visible()
    def draw(self,tool='pen'):
        self.page.locator('#tut-tool').select_option(tool);canvas=self.page.locator('#tut-canvas');canvas.scroll_into_view_if_needed();r=canvas.bounding_box();self.page.mouse.move(r['x']+r['width']*.3,r['y']+r['height']*.3);self.page.mouse.down();self.page.mouse.move(r['x']+r['width']*.6,r['y']+r['height']*.5,steps=7);self.page.mouse.up()
    def test_lessons_annotations_exports_and_preview_preserve_chart(self):
        self.tutorial();before=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})')
        expect(self.page.locator('#quick-tutorial .kp-quick-label')).to_have_text('TUT');expect(self.page.locator('#tut-chart [data-cusp]')).to_have_count(12);expect(self.page.locator('#tut-chart [data-planet]')).to_have_count(9)
        self.page.locator('#tut-house').select_option('7');self.page.locator('#tut-purpose').select_option('marriage');self.page.locator('#tut-planet').select_option('Ve');expect(self.page.locator('#tut-chart [data-cusp="7"]')).to_have_class(re.compile('tut-focus'));self.assertIn('2, 7, 11',self.page.locator('#tut-evidence').inner_text())
        self.draw();expect(self.page.locator('#tut-canvas [data-drawing]')).to_have_count(1);self.page.locator('#tut-undo').click();expect(self.page.locator('#tut-canvas [data-drawing]')).to_have_count(0);self.page.locator('#tut-redo').click();expect(self.page.locator('#tut-canvas [data-drawing]')).to_have_count(1)
        self.page.locator('#tut-notes').fill('Marathi notes: कुंडली\n<img src=x onerror=alert(1)>')
        with self.page.expect_download() as downloaded:self.page.locator('#tut-save-session').click()
        saved=Path(downloaded.value.path()).read_bytes();data=json.loads(saved);self.assertEqual(data['format'],'KP-Tutorial');self.assertEqual(len(data['state']['annotations']),1)
        self.page.locator('#tut-clear').click();self.page.locator('#tut-session-file').set_input_files({'name':'lesson.json','mimeType':'application/json','buffer':saved});expect(self.page.locator('#tut-canvas [data-drawing]')).to_have_count(1)
        with self.page.expect_download() as notes:self.page.locator('#tut-save-text').click()
        self.assertIn('कुंडली',Path(notes.value.path()).read_text(encoding='utf-8-sig'))
        self.page.locator('#tut-report-mode').select_option('lesson')
        with self.page.expect_popup() as opened:self.page.locator('#tut-preview').click()
        preview=opened.value;expect(preview.locator('.tut-print-notes')).to_contain_text('<img src=x onerror=alert(1)>');expect(preview.locator('img')).to_have_count(0);expect(preview.locator('[data-drawing]')).to_have_count(1);self.assertIn('tut-focus',preview.locator('[data-cusp="7"]').get_attribute('class'));preview.get_by_role('button',name='Zoom +',exact=True).click();self.assertEqual(preview.locator('.tut-paper').evaluate('n=>n.style.zoom'),'1.1');pdf=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True);self.assertGreater(len(pdf),10000);preview.get_by_role('button',name='Close preview',exact=True).click()
        self.assertEqual(before,self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})'))
    def test_marathi_progress_guides_and_mismatched_session(self):
        self.tutorial();self.page.locator('#tut-language').select_option('marathi');expect(self.page.locator('#tut-lesson-title')).to_have_text('जन्म माहिती');self.page.locator('#tut-mark').click();self.page.locator('#tut-notes').fill('पहिला धडा');self.page.locator('#tut-next').click();expect(self.page.locator('#tut-lesson-title')).to_have_text('राशी व भाव');self.page.locator('#tut-prev').click();expect(self.page.locator('#tut-notes')).to_have_value('पहिला धडा');self.page.locator('.tut-function-guide summary').click();self.page.locator('#tut-guide-search').fill('gemstone');expect(self.page.locator('#tut-guide article')).to_have_count(1)
        state=self.page.evaluate('KPTutorial.getState()');state['chartKey']='different chart';state['annotations']=[{'tool':'text','colour':'#123456','width':3,'points':[[50,50]],'text':'wrong chart'}];self.page.locator('#tut-session-file').set_input_files({'name':'other.json','mimeType':'application/json','buffer':json.dumps({'format':'KP-Tutorial','version':1,'state':state}).encode()});expect(self.page.locator('#tut-status')).to_contain_text('वेगळ्या कुंडली');expect(self.page.locator('#tut-canvas [data-drawing]')).to_have_count(0)
        self.page.reload(timeout=60000);self.page.wait_for_function('window.KPTutorial');self.tutorial();expect(self.page.locator('#tut-notes')).to_have_value('पहिला धडा');self.assertEqual(self.page.evaluate('KPTutorial.getState().done'),['birth']);self.page.set_viewport_size({'width':390,'height':844});self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
    def test_traditional_and_kp_modes_have_independent_selected_reports(self):
        self.page.locator('#quick-matchmaking').click();expect(self.page.locator('#mm-traditional-charts svg')).to_have_count(2);expect(self.page.locator('#mm-kp-panel')).to_be_visible();baseline=self.page.evaluate('KPMatchmaking.getData().ashtakoota.total');self.page.locator('#mm-analysis-mode').select_option('traditional');expect(self.page.locator('#mm-kp-panel')).to_be_hidden();expect(self.page.locator('#mm-traditional-panel')).to_be_visible();expect(self.page.locator('#mm-total')).to_be_visible();expect(self.page.locator('#mm-total')).to_have_text(str(baseline))
        report=self.page.evaluate('KPMatchmaking.snapshot()');self.assertIn('data-mm-report-mode="traditional"',report);self.assertIn('Traditional Ashtakoota',report);self.assertNotIn('configured KP compatibility index',report)
        self.page.locator('#mm-analysis-mode').select_option('kp');expect(self.page.locator('#mm-traditional-panel')).to_be_hidden();expect(self.page.locator('#mm-kp-panel')).to_be_visible();report=self.page.evaluate('KPMatchmaking.snapshot()');self.assertIn('configured KP compatibility index',report);self.assertNotIn('Traditional Ashtakoota',report)
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
        self.page.locator('input[name="dp-mode-radio"][value="manual"]').check()
        self.page.locator('#dp-house-0').fill('2 6 10 11');self.page.locator('#dp-house-0').dispatch_event('change')
        self.assertEqual(self.page.evaluate('KPDashaPromise.getData().layers[0].houses'),[2,6,10,11])
        self.page.locator('#dp-use-0').uncheck();self.assertFalse(self.page.evaluate('KPDashaPromise.getData().layers[0].enabled'))
        self.page.locator('#dp-calculate').click();expect(self.page.locator('#dp-status')).to_contain_text('Calculation complete',timeout=90000)
        self.assertTrue(self.page.evaluate('KPDashaPromise.getData().calculated'))
        # Every returned interval is inside the selected AD, including clipped birth ADs.
        valid=self.page.evaluate('''()=>{const d=KPDashaPromise.getData(),a=Date.parse(document.getElementById('dp-period').dataset.startUTC),b=Date.parse(document.getElementById('dp-period').dataset.endUTC),h=KPHomeDasha.getData();return [...d.outer,...d.sun].every(p=>Date.parse(p.start)>=a&&Date.parse(p.end)<=b&&Date.parse(p.start)<Date.parse(p.end))&&d.pd.every(p=>p.startMs-h.timeZoneHours*3600000>=a&&p.endMs-h.timeZoneHours*3600000<=b)}''')
        self.assertTrue(valid)
        with self.page.expect_popup() as opened:self.page.locator('#dasha-promise-preview').click()
        preview=opened.value;expect(preview.locator('.dp-report')).to_contain_text('Calculation complete');self.assertGreater(len(preview.pdf(format='A4')),10000);preview.close()
        self.page.locator('#dp-house-0').fill('13');self.page.locator('#dp-house-0').dispatch_event('change');expect(self.page.locator('#dp-status')).to_contain_text('house numbers 1–12')
        self.assertFalse(self.page.evaluate('KPDashaPromise.getData().ready'))

class PrivateTutorialTests(unittest.TestCase):
    def test_private_teaching_and_both_matchmaking_methods(self):
        spec=importlib.util.spec_from_file_location('tutorial_private_server',ROOT/'protected/server.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);engine=module.Engine();server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler);server.engine=engine;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));url=f'http://127.0.0.1:{server.server_port}';page.goto(url);expect(page.locator('#quick-tutorial')).to_be_visible(timeout=60000);page.locator('#quick-tutorial').click();expect(page.locator('#tutorial')).to_be_visible(timeout=30000);expect(page.locator('#tut-chart [data-cusp]')).to_have_count(12);page.locator('#tut-house').select_option('7');expect(page.locator('#tut-chart [data-cusp="7"]')).to_have_class(re.compile('tut-focus'));page.locator('#tut-notes').fill('Private teaching notes');page.locator('#tut-language').select_option('marathi');expect(page.locator('#tut-lesson-title')).to_have_text('जन्म माहिती')
                with page.expect_popup() as opened:page.locator('#tut-preview').click()
                preview=opened.value;expect(preview.locator('.tut-print-notes')).to_have_text('Private teaching notes');preview.close();page.locator('#quick-matchmaking').click();expect(page.locator('#mm-traditional-charts svg')).to_have_count(2,timeout=30000);page.locator('#mm-analysis-mode').select_option('traditional');expect(page.locator('#mm-kp-panel')).to_be_hidden(timeout=30000);expect(page.locator('#mm-traditional-panel')).to_be_visible();page.locator('#mm-analysis-mode').select_option('kp');expect(page.locator('#mm-kp-panel')).to_be_visible(timeout=30000);expect(page.locator('#mm-traditional-panel')).to_be_hidden();page.locator('#quick-dasha-promise').click();expect(page.locator('#dp-layers .dp-layer')).to_have_count(5,timeout=30000);page.locator('#dp-calculate').click();expect(page.locator('#dp-status')).to_contain_text('Calculation complete',timeout=90000)
                with page.expect_popup() as opened:page.locator('#dasha-promise-preview').click()
                preview=opened.value;expect(preview.locator('.dp-report')).to_contain_text('Calculation complete',timeout=30000);preview.close();self.assertEqual(errors,[]);self.assertEqual(page.request.get(url+'/index.html').status,404);self.assertEqual(page.request.get(url+'/tutorial.js').status,200);browser.close()
        finally:
            server.shutdown();thread.join(timeout=5);server.server_close();engine.close()
