"""Personal chart matching, automatic DBA and simplified consultation screens."""
import functools
import importlib.util
import shutil
import threading
import unittest
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
class PersonalPredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);cls.url=f'http://127.0.0.1:{cls.server.server_port}/index.html'
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.thread.join(timeout=5);cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000});self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.goto(self.url,timeout=60000);self.page.wait_for_function('document.getElementById("ep-simple-preview")&&document.getElementById("tr-simple-event-choice")&&document.getElementById("pred-subtabs")',timeout=60000)
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def test_prediction_sections_never_browse_common_source_records(self):
        self.page.locator('#quick-prediction').click();expect(self.page.locator('#pred-subtabs button')).to_have_count(7);expect(self.page.locator('#pred-tab-dasha-short')).to_have_count(0);expect(self.page.locator('#pred-tab-all,#pred-library-panel,#pred-reference-view')).to_have_count(0)
        for category in ['house-results','general-predictions','events','dasha-results','mahadasha-remedies','gemstones']:
            self.page.locator('#pred-tab-'+category).click();d=self.page.evaluate('KPPersonalPredictions.getData()');self.assertTrue(d['ready']);self.assertTrue(d['rows']);self.assertTrue(all(r['status']=='matched' and r['proof'] for r in d['rows']));report=self.page.evaluate('KPPersonalPredictions.snapshot()');self.assertNotIn('All source entries',report);self.assertNotIn('Reference sources',report);self.assertNotIn('data-reference-entry',report)
        self.assertEqual(self.page.evaluate('typeof KPPredictionLibrary'),'undefined')
        result=self.page.evaluate('''()=>{const m=structuredClone(currentKPModel);m.ready=false;return ['house-results','general-predictions','events','dasha-short','dasha-results','mahadasha-remedies','gemstones'].map(c=>KPPersonalPredictions.matchRules(c,m));}''');self.assertTrue(all(not r['ready'] and not r['rows'] for r in result))
    def test_house_matching_rejects_ambiguous_groups_and_requires_every_house(self):
        result=self.page.evaluate('''()=>{const decode=KPPersonalPredictions.decodeHouseGroup;const m=structuredClone(currentKPModel);m.fourfold.planets.forEach(r=>{r.A=[2,5];r.B=[];r.C=[];r.D=[];});const d=KPPersonalPredictions.matchRules('house-results',m);return {valid:decode('135810'),ambiguous:decode('12'),invalid:decode('22'),rows:d.rows};}''')
        self.assertEqual(result['valid'],[1,3,5,8,10]);self.assertIsNone(result['ambiguous']);self.assertIsNone(result['invalid']);self.assertTrue(result['rows']);self.assertTrue(all(set(self.page.evaluate(r'(k)=>KPPersonalPredictions.decodeHouseGroup(k.match(/R(\d+)$/i)[1])',r['key']))<={2,5} for r in result['rows']))
    def test_running_dba_uses_native_clock_and_exclusive_boundaries(self):
        self.page.locator('#quick-dasha-fal').click();expect(self.page.locator('#dasha-fal select,#dasha-fal input')).to_have_count(0);expect(self.page.locator('[data-df-level]')).to_have_count(3)
        result=self.page.evaluate('''()=>{const current=KPDashaFal.current(),t=KPTransit.currentPeriods(),h=KPHomeDasha.getData(),offset=h.timeZoneHours*3600000;const boundary=new Date(Date.parse(current.periods[2].end+'Z')-offset);const after=KPDashaFal.current(currentKPModel,boundary),before=KPDashaFal.current(currentKPModel,new Date(boundary.getTime()-1000));return {current:current.periods.map(p=>p.id),expected:Object.values(t.periods).map(p=>p.id),before:before.periods[2],after:after.periods[2],short:current.results.filter(r=>r.status==='matched'&&r.record.categoryId==='dasha-short').map(r=>r.record.id),html:KPDashaFal.snapshot()};}''')
        self.assertEqual(result['current'],result['expected']);self.assertEqual(result['before']['end'],result['after']['start']);self.assertNotEqual(result['before']['id'],result['after']['id']);self.assertTrue(result['short']);self.assertNotIn('Source file',result['html']);self.assertNotIn('<select',result['html']);self.assertEqual(self.page.locator('#df-results tr[data-status="matched"]').count(),min(40,len(result['short'])))
    def test_vedic_selects_1_5_11_lords_even_with_retrograde_markers(self):
        self.page.locator('#quick-prediction').click();self.page.locator('#pred-tab-gemstones').click();self.page.locator('#pred-open-gems').click();self.page.locator('#gem-mode').select_option('vedic');expect(self.page.locator('#gem-event')).to_be_hidden()
        result=self.page.evaluate('''()=>{const d=KPGemstones.getData(),lords=['Ma','Ve','Me','Mo','Su','Me','Ve','Ma','Ju','Sa','Sa','Ju'],lagna=currentKPModel.houses[0].signIndex;return {expected:[...new Set([1,5,11].map(h=>lords[(lagna+h-1)%12]))].sort(),actual:d.results.filter(r=>r.qualifies).map(r=>r.id).sort(),roles:d.results.filter(r=>r.qualifies).flatMap(r=>r.ownership),html:KPGemstones.snapshot()};}''');self.assertEqual(result['actual'],result['expected']);self.assertEqual(sorted(result['roles']),[1,5,11])
        with self.page.expect_popup() as opened:self.page.locator('#gemstones-preview').click()
        preview=opened.value;preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale');pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(pdf),1);self.assertIn('Lagnesh',pdf[0].get_text());self.assertIn('Panchamesh',pdf[0].get_text());self.assertIn('Labhesh',pdf[0].get_text());pdf.close();preview.close()
    def test_event_selection_gives_direct_verdict_and_one_a4_page(self):
        self.page.locator('#quick-event-promise').click();self.assertEqual(self.page.locator('#event-promise select:visible').count(),3);self.assertEqual(self.page.locator('#event-promise input[type=text]:visible').count(),0);expect(self.page.locator('#ep-mode-auto')).to_have_attribute('aria-pressed','true')
        cases=self.page.evaluate('''()=>{const options=[...document.getElementById('ep-event').options],found={};for(const o of options){document.getElementById('ep-event').value=o.value;const d=KPEventPromise.refresh(true),v=KPEventOutcome.assess(d);if(d.ready&&!v.qualified&&!d.cuspMismatch){const status=v.promised?'yes':'no';if(!found[status])found[status]=o.value;}if(found.yes&&found.no)break;}return found;}''');self.assertEqual(set(cases),{'yes','no'})
        for status,value in cases.items():
            self.page.locator('#ep-event').select_option(value);expect(self.page.locator('#ep-simple-result')).to_contain_text('Event is Promised' if status=='yes' else 'Event is not Promised');expect(self.page.locator('#ep-simple-result')).to_contain_text('Why?')
        with self.page.expect_popup() as opened:self.page.locator('#ep-simple-preview').click()
        preview=opened.value;preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale');pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(pdf),1);self.assertIn('Why?',pdf[0].get_text());pdf.close();expect(preview.get_by_role('button',name='Print / Save PDF',exact=True)).to_be_visible();preview.close()
    def test_removed_ruling_and_fixed_aspects_keep_other_tabs_working(self):
        expect(self.page.locator('[data-tab="ruling-planets"],#ruling-planets,#quick-ruling-planets,#ruling-clock,#settings-tab-ruling,#settings-pane-ruling')).to_have_count(0)
        self.assertEqual(self.page.evaluate('typeof KPRulingWorkspace+"/"+typeof KPRulingPlanets'),'undefined/undefined');self.assertEqual(self.page.request.get(self.url.replace('/index.html','')+'/ruling-clock').status,404)
        self.page.locator('#quick-aspects').click();expect(self.page.locator('.am-advanced,#western-orb,#am-header-colour')).to_have_count(0);expect(self.page.locator('#aspects .am-matrix')).to_be_visible();before=self.page.evaluate('KPWesternAspects.getSettings()');self.assertEqual(len(before['aspects']),20)
        self.page.evaluate('KPPreferences.save({...KPPreferences.get(),fontSize:13,themeType:"dark"})');self.assertEqual(self.page.evaluate('KPWesternAspects.getSettings()'),before);self.page.locator('#am-mode').select_option('cusp');expect(self.page.locator('#aspects .am-matrix caption')).to_contain_text('ग्रहांपासून भावांवर')
    def test_four_step_incoming_aspects_add_source_houses_without_recursion(self):
        result=self.page.evaluate("""()=>{const positions={Su:125,Mo:155,Ma:20,Me:185,Ju:245,Ve:65,Sa:15,Ra:95};Object.keys(positions).forEach(k=>positions[k]*=3600);const m=KPDisplay.build(Array.from({length:12},(_,i)=>i*30*3600),positions),star=m.fourstep.find(p=>p.id==='Ma').steps[1],levels=(m.houses[0].sl='Ma',KPEventPromise.analyze(m,{cusp:1,method:'fourstep',customHouses:'1,11',layers:['CSL']}));return {ready:m.ready,star,levels,nil:m.fourstep.flatMap(p=>p.steps).filter(p=>p.nil),all:m.fourstep};}""")
        self.assertTrue(result['ready']);star=result['star'];self.assertEqual(star['planet'],'Ve');self.assertEqual(star['baseHouses'],[2,3]);source=next(c for c in star['aspectContributions'] if c['planet']=='Sa');self.assertEqual(source['houses'],[1,11]);self.assertTrue({1,2,3,11}.issubset(star['houses']));self.assertTrue({1,11}.issubset(result['levels']['houses']))
        for card in result['all']:
            for step in card['steps']:
                expected=set(step['baseHouses'])|{h for source in step['aspectContributions'] for h in source['houses']};self.assertEqual(set(step['houses']),expected)
        self.assertTrue(result['nil']);self.assertTrue(all(not p['houses'] and not p['aspectContributions'] for p in result['nil']))
        self.page.locator('#quick-home').click();self.page.locator('[data-home-view="fourstep"]').click();expect(self.page.locator('#home-fourstep .kp-step-aspects').first).to_contain_text('Aspd:')

    def test_dba_prints_the_complete_native_timeline_and_significators(self):
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        data=self.page.evaluate('KPDbaPopup.data()');roots=data['roots']
        # Every displayed house comes from this kundali, including nodes with no ownership.
        points=self.page.evaluate('currentKPModel.planets');by_id={p['id']:p for p in points}
        for point in points:
            sig=data['significators'][point['id']]
            expected=[point['id'],point['stl'],point['sl'],by_id[point['sl']]['stl']]
            for layer,id in zip(['planet','star','sub','subStar'],expected):
                self.assertEqual(sig[layer]['id'],id);self.assertEqual(sig[layer]['occ'],by_id[id]['occ']);self.assertEqual(sig[layer]['own'],by_id[id]['own'])
        with self.page.expect_popup() as opened:self.page.locator('[data-tab="mdcalc"]').click()
        preview=opened.value;preview.wait_for_function('window.KPDBASelection')
        expect(preview.locator('.dba-tools select:visible,.dba-tools input:visible')).to_have_count(0)
        counts={'MD':len(roots),'AD':sum(len(m['children']) for m in roots),'PD':sum(len(a['children']) for m in roots for a in m['children'])}
        for level,count in counts.items():expect(preview.locator('tbody tr[data-level="'+level+'"]')).to_have_count(count)
        preview.locator('.dba-md-heading').nth(1).click();preview.locator('.dba-ad-choice').nth(2).click()
        preview.locator('tr[data-level="PD"][data-md="1"][data-ad="2"][data-index="4"] button').click()
        chosen=preview.evaluate('KPDBASelection.getData()');self.assertEqual([chosen[k] for k in ['md','ad','pd']],[1,2,4])
        self.assertEqual(chosen['periods'][2]['startMs'],roots[1]['children'][2]['children'][4]['startMs'])
        for level,count in counts.items():expect(preview.locator('tbody tr[data-level="'+level+'"]')).to_have_count(count)
        preview.evaluate('window.print=()=>window.testPrinted=true');preview.locator('#dba-print-selected').click();self.assertTrue(preview.evaluate('window.testPrinted'));self.assertEqual(preview.locator('body').get_attribute('data-print-mode'),'all')
        preview.emulate_media(media='print');expect(preview.locator('#dba-grid')).to_be_visible()
        pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');text=''.join(p.get_text() for p in pdf)
        self.assertGreater(len(pdf),1);self.assertGreater(pdf[0].rect.width,pdf[0].rect.height)
        for level,count in counts.items():self.assertEqual(text.count(level+' · '),count)
        self.assertIn('Sub’s star',text);self.assertIn('owned houses',text)
        # Repeated header bands identify the Dasha and keep all columns on the page.
        for page in pdf:
            self.assertIn('Star lord',page.get_text())
            for word in page.get_text('words'):self.assertLessEqual(word[2],page.rect.width-20)
        pdf.close();preview.close();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_dba_overview_keeps_all_md_ad_and_selected_antara_in_same_popup(self):
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        roots=self.page.evaluate('KPDbaPopup.data().roots')
        with self.page.expect_popup() as opened:self.page.locator('[data-tab="mdcalc"]').click()
        preview=opened.value;preview.wait_for_function('window.KPDBASelection')
        preview.locator('#dba-overview').click()
        expect(preview.locator('#dba-overview')).to_have_attribute('aria-pressed','true')
        expect(preview.locator('.dba-overview-card')).to_have_count(len(roots))
        expect(preview.locator('.dba-overview-card tbody tr')).to_have_count(sum(len(m['children']) for m in roots))
        self.assertEqual(preview.locator('.dba-grid').evaluate('n=>getComputedStyle(n).gridTemplateColumns.split(" ").length'),3)
        preview.locator('.dba-overview-card[data-md="1"] tr[data-index="2"] button').click()
        selected=preview.evaluate('KPDBASelection.getData()');self.assertEqual([selected[k] for k in ['md','ad','pd','view']],[1,2,0,'overview'])
        expected=roots[1]['children'][2]['children']
        expect(preview.locator('.dba-overview-antara tbody tr')).to_have_count(len(expected))
        self.assertEqual(preview.locator('.dba-overview-antara tbody tr').evaluate_all('nodes=>nodes.map(n=>[Number(n.dataset.start),Number(n.dataset.end)])'),[[r['startMs'],r['endMs']] for r in expected])
        preview.locator('.dba-overview-antara tr[data-index="4"] button').click()
        self.assertEqual(preview.evaluate('KPDBASelection.getData().pd'),4)
        preview.evaluate('window.print=()=>window.testPrinted=true');preview.locator('#dba-print-selected').click()
        self.assertTrue(preview.evaluate('window.testPrinted'));self.assertEqual(preview.locator('body').get_attribute('data-print-mode'),'overview')
        pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');text=''.join(p.get_text() for p in pdf)
        self.assertIn('Selected Antara',text)
        for page in pdf:
            for word in page.get_text('words'):self.assertLessEqual(word[2],page.rect.width-20)
        pdf.close()
        preview.locator('#dba-significators').click();self.assertEqual(preview.evaluate('KPDBASelection.getData().view'),'all')
        expect(preview.locator('tbody tr[data-level="PD"]')).to_have_count(sum(len(a['children']) for m in roots for a in m['children']))
        self.assertEqual(preview.evaluate('KPDBASelection.getData().pd'),4)
        preview.close();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_current_dba_print_has_all_current_bhukti_antaras_and_preserves_selection(self):
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        expect(self.page.locator('#dba-worksheet-calculations')).not_to_have_attribute('open','')
        self.assertFalse(self.page.locator('#dba-worksheet-calculations').evaluate('n=>n.open'))
        with self.page.expect_popup() as opened:self.page.locator('#quick-mdcalc').click()
        preview=opened.value;preview.wait_for_function('window.KPDBASelection')
        preview.on('pageerror',lambda e:self.errors.append(str(e)))
        expect(self.page.locator('#page-title')).to_have_text('Home')
        expect(self.page.locator('#mdcalc')).to_be_hidden()
        roots=preview.evaluate('KPDBASelection.timeline().roots')
        active=preview.evaluate("""()=>{const d=KPDBASelection.timeline(),at=Date.now()+d.offset*3600000;return d.roots.flatMap((m,mi)=>m.children.flatMap((a,ai)=>a.children.map((p,pi)=>({md:mi,ad:ai,pd:pi,start:p.startMs,end:p.endMs})))).find(p=>p.start<=at&&at<p.end);} """)
        self.assertTrue(active)
        selected=preview.evaluate('KPDBASelection.getData()')
        self.assertEqual([selected[k] for k in ['md','ad','pd']],[active[k] for k in ['md','ad','pd']])
        self.assertFalse(preview.locator('#dba-calculations').evaluate('n=>n.open'))
        preview.locator('#dba-calculations summary').click()
        expect(preview.locator('#dba-calculation-facts')).to_be_visible()
        expect(preview.locator('#dba-calculation-facts dt')).to_have_count(6)
        preview.locator('#dba-overview').click()
        preview.locator('.dba-overview-card[data-md="1"] tr[data-index="2"] button').click()
        preview.locator('.dba-overview-antara tr[data-index="4"] button').click()
        preview.locator('#dba-zoom-in').click()
        before=preview.evaluate('JSON.stringify(KPDBASelection.getData())')
        preview.evaluate("""()=>{const d=KPDBASelection.timeline(),at=d.roots[3].children[4].children[5].startMs+1000;Date.now=()=>at-d.offset*3600000;window.print=()=>window.prints=(window.prints||0)+1;}""")
        preview.locator('#dba-print-current').click()
        self.assertEqual(preview.evaluate('window.prints'),1)
        self.assertEqual(preview.evaluate('JSON.stringify(KPDBASelection.getData())'),before)
        self.assertEqual(preview.locator('#dba-report').evaluate('n=>n.style.zoom'),'1.1')
        expect(preview.locator('body')).to_have_attribute('data-print-mode','current')
        current=preview.locator('#dba-current-report')
        expect(current.locator('tbody tr[data-level="MD"]')).to_have_count(1)
        expect(current.locator('tbody tr[data-level="AD"]')).to_have_count(1)
        expect(current.locator('tbody tr[data-level="PD"]')).to_have_count(len(roots[3]['children'][4]['children']))
        self.assertEqual(current.locator('tr.current-period').get_attribute('data-index'),'5')
        expect(current).to_be_hidden()
        preview.emulate_media(media='print')
        expect(preview.locator('#dba-grid')).to_be_hidden();expect(preview.locator('#dba-calculations')).to_be_hidden();expect(current).to_be_visible()
        pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
        self.assertEqual(len(pdf),1);text=''.join(sheet.get_text() for sheet in pdf)
        self.assertEqual(text.count('MD · '),1);self.assertEqual(text.count('AD · '),1);self.assertEqual(text.count('PD · '),len(roots[3]['children'][4]['children']))
        self.assertIn('Sub’s star',text);self.assertNotIn('Moon position',text);self.assertNotIn('Complete native timeline',text)
        for sheet in pdf:
            for word in sheet.get_text('words'):
                self.assertGreaterEqual(word[0],20);self.assertLessEqual(word[2],sheet.rect.width-20)
        pdf.close()
        preview.emulate_media(media='screen');preview.evaluate("window.dispatchEvent(new Event('afterprint'))")
        expect(preview.locator('body')).to_have_attribute('data-print-mode','overview')
        preview.locator('#dba-print-selected').click();self.assertEqual(preview.evaluate('window.prints'),2)
        # End-exclusive boundary belongs to the next Antara, and outside times never print stale results.
        preview.evaluate("""()=>{const d=KPDBASelection.timeline();Date.now=()=>d.roots[3].children[4].children[5].endMs-d.offset*3600000;}""")
        preview.locator('#dba-print-current').click();self.assertEqual(current.locator('tr.current-period').get_attribute('data-index'),'6')
        preview.evaluate("""()=>{const d=KPDBASelection.timeline();Date.now=()=>d.roots.at(-1).endMs-d.offset*3600000;}""")
        preview.locator('#dba-print-current').click();self.assertEqual(preview.evaluate('window.prints'),3)
        expect(preview.locator('#dba-status')).to_contain_text('outside this native dasha timeline')
        preview.close();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_disease_screen_and_print_omit_source_and_explanatory_lines(self):
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        self.page.locator('#quick-disease').click()
        snapshot=self.page.evaluate('KPDisease.snapshot()')
        forbidden=['medical diagnosis','Astrological reference matches','Astrological matches','Disease.xlsx','Diseases (Sixth Bhava)','Source row','missing disease house criteria']
        screen=self.page.locator('#disease').inner_text()
        for phrase in forbidden:self.assertNotIn(phrase,screen);self.assertNotIn(phrase,snapshot)
        expect(self.page.locator('#disease-results [data-disease-layer]')).not_to_have_count(0)
        with self.page.expect_popup() as opened:self.page.locator('#disease-preview').click()
        preview=opened.value;preview.wait_for_selector('[data-disease-linked]')
        pdf=fitz.open(stream=preview.pdf(format='A4'),filetype='pdf');text=''.join(p.get_text() for p in pdf)
        for phrase in forbidden:self.assertNotIn(phrase,text)
        pdf.close();preview.close();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_significators_omit_completed_automatic_calculation_message(self):
        self.page.locator('[data-tab="karyesh"]').click()
        expect(self.page.locator('#kp-status')).to_have_attribute('data-ready','true')
        expect(self.page.locator('#kp-status')).to_have_text('');expect(self.page.locator('#kp-status')).to_be_hidden()
        self.assertNotIn('Calculated automatically from Tab 5',self.page.locator('#karyesh').inner_text())
        self.assertFalse(self.page.evaluate("()=>{renderReport();return document.getElementById('printReport').textContent.includes('Calculated automatically from Tab 5');}"))

    def test_profession_a4_print_has_safe_margins_no_overlapping_lines_and_compact_controls(self):
        self.page.locator('#quick-education-profession').click();self.page.locator('#ed-category').select_option('10')
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        self.assertLessEqual(self.page.locator('.ed-toolbar').bounding_box()['height'],40)
        expect(self.page.locator('#education-profession>.card>h2')).to_have_count(0)
        expect(self.page.locator('#ed-results [data-education-cusp="10"]')).to_have_count(1)
        for language in ['english','marathi']:
            self.page.evaluate('(language)=>{KPPreferences.save({...KPPreferences.get(),language});KPLanguage.apply();}',language)
            with self.page.expect_popup() as opened:self.page.locator('#education-profession-preview').click()
            preview=opened.value;preview.wait_for_selector('[data-profession-linked]')
            preview.get_by_role('button',name='Zoom +',exact=True).click() if language=='english' else None
            pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
            self.assertGreater(len(pdf),0)
            for page in pdf:
                self.assertAlmostEqual(page.rect.width,595.3,delta=1);self.assertAlmostEqual(page.rect.height,841.9,delta=1)
                for word in page.get_text('words'):
                    self.assertGreaterEqual(word[0],24);self.assertGreaterEqual(word[1],28)
                    self.assertLessEqual(word[2],page.rect.width-24);self.assertLessEqual(word[3],page.rect.height-28)
                lines=[fitz.Rect(line['bbox']) for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines']]
                for i,line in enumerate(lines):
                    for other in lines[i+1:]:
                        cross=line & other
                        self.assertFalse(not cross.is_empty and cross.width>5 and cross.height>3,'Printed text lines overlap')
            pdf.close();preview.close()
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_marathi_english_display_preserves_native_data_and_localizes_previews(self):
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        values=self.page.locator('#ed-category option').evaluate_all('nodes=>nodes.map(n=>n.value)')
        self.page.evaluate("KPPreferences.save({...KPPreferences.get(),language:'marathi',planetNotation:'short'});KPLanguage.apply()")
        expect(self.page.locator('.app-sidebar [data-tab="home"]')).to_contain_text('मुख्यपृष्ठ')
        self.assertEqual(self.page.evaluate("['Su','Mo','Ar','CSL'].map(x=>KPLanguage.translate(x))"),['रवी','चंद्र','मेष','भाव उपस्वामी'])
        self.page.locator('#quick-education-profession').click()
        with self.page.expect_popup() as opened:self.page.locator('#education-profession-preview').click()
        preview=opened.value
        expect(preview.get_by_role('button',name='छापा / पीडीएफ जतन करा · Print / Save PDF',exact=True)).to_be_visible()
        self.assertEqual(preview.locator('html').get_attribute('lang'),'mr');preview.close()
        self.page.evaluate("KPPreferences.save({...KPPreferences.get(),language:'english'});KPLanguage.apply()")
        expect(self.page.locator('.app-sidebar [data-tab="home"]')).to_contain_text('Home')
        expect(self.page.locator('#ed-category option').first).to_have_text('4th house · Basic education')
        self.assertEqual(self.page.evaluate("KPLanguage.translate('चंद्र · 2026-10-10','english')"),'Moon · 2026-10-10')
        self.assertEqual(self.page.locator('#ed-category option').evaluate_all('nodes=>nodes.map(n=>n.value)'),values)
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_education_house_selection_matches_screen_and_preview_without_source_rows(self):
        self.page.locator('#quick-education-profession').click()
        expect(self.page.locator('#ed-category option')).to_have_count(3)
        self.assertEqual(self.page.locator('#ed-category option').evaluate_all('nodes=>nodes.map(n=>n.value)'),['4','9','10'])
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        for cusp in [4,9,10]:
            self.page.locator('#ed-category').select_option(str(cusp))
            expect(self.page.locator('#ed-results [data-education-cusp]')).to_have_count(1)
            expect(self.page.locator('#ed-results [data-education-cusp]')).to_have_attribute('data-education-cusp',str(cusp))
            if cusp==10:expect(self.page.locator('#ed-profession-links')).to_be_visible()
            else:expect(self.page.locator('#ed-profession-links')).to_be_hidden()
            snapshot=self.page.evaluate('KPEducationProfession.snapshot()')
            self.assertNotIn('Sheet1 row',snapshot);self.assertNotIn('Source row',snapshot);self.assertNotIn('.xlsx',snapshot);self.assertNotIn('class="ed-source"',snapshot)
            for other in [4,9,10]:
                if other!=cusp:self.assertNotIn('data-education-cusp="'+str(other)+'"',snapshot)
            with self.page.expect_popup() as opened:self.page.locator('#education-profession-preview').click()
            preview=opened.value;preview.wait_for_selector('[data-education-cusp="'+str(cusp)+'"]')
            expected=self.page.locator('#ed-results [data-education-cusp]').inner_text()
            self.assertEqual(preview.locator('[data-education-cusp="'+str(cusp)+'"]').inner_text(),expected)
            expect(preview.get_by_role('button',name='Print / Save PDF',exact=True)).to_be_visible()
            pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');text=''.join(p.get_text() for p in pdf)
            self.assertNotIn('Sheet1 row',text);self.assertNotIn('Source row',text);self.assertNotIn('.xlsx',text);pdf.close();preview.close()
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        self.assertNotIn('Source row',self.page.evaluate('KPDisease.snapshot()'))

    def test_home_nadi_uses_plain_high_contrast_house_numbers(self):
        self.page.locator('#quick-home').click();self.page.locator('[data-home-view="nadi"]').click();expect(self.page.locator('#home-nadi-significators .na-tile')).to_have_count(9)
        styles=self.page.locator('#home-nadi-significators .ep-house').first.evaluate('n=>{const c=getComputedStyle(n);return {outline:c.outlineStyle,border:c.borderTopWidth,background:c.backgroundColor};}');self.assertEqual(styles['outline'],'none');self.assertEqual(styles['border'],'0px');self.assertEqual(styles['background'],'rgba(0, 0, 0, 0)');self.page.screenshot(path='/tmp/kp-nadi-clean.png',full_page=True)

    def test_notepad_typing_and_formatting_leave_chart_sizes_and_values_unchanged(self):
        self.page.locator('#quick-south9').click();self.page.locator('#quick-notepad').click();self.page.wait_for_timeout(250)
        before=self.page.evaluate("""()=>{window.noteChartChanges=0;window.noteObserver=new MutationObserver(m=>noteChartChanges+=m.length);noteObserver.observe(document.getElementById('kundali'),{subtree:true,childList:true,attributes:true});return {model:JSON.stringify(currentKPModel),sizes:[...document.querySelectorAll('#kundali .v38-name,#kundali .v38-degree,#kundali .v38-lords')].map(n=>getComputedStyle(n).fontSize)};}""")
        self.page.locator('#notepad-text').press_sequentially('Mars cusp 7: explanation of the kundali',delay=10);self.page.locator('#notepad-font').select_option('serif');self.page.locator('#notepad-size').fill('24');self.page.locator('#notepad-size').dispatch_event('change');self.page.locator('#notepad-colour').fill('#cc2222');self.page.locator('#notepad-colour').dispatch_event('input');self.page.wait_for_timeout(250)
        after=self.page.evaluate("""()=>({model:JSON.stringify(currentKPModel),sizes:[...document.querySelectorAll('#kundali .v38-name,#kundali .v38-degree,#kundali .v38-lords')].map(n=>getComputedStyle(n).fontSize)})""");self.assertEqual(before,after);self.assertEqual(self.page.evaluate('noteChartChanges'),0);self.assertEqual(self.page.locator('#notepad-text').evaluate('n=>getComputedStyle(n).fontSize'),'24px');self.page.locator('#notepad-close').click();expect(self.page.locator('#south-position-tables table')).to_have_count(2);expect(self.page.locator('#south-position-tables article').first.locator('tbody tr')).to_have_count(9);expect(self.page.locator('#south-position-tables article').last.locator('tbody tr')).to_have_count(12);self.assertNotIn('Automatic calculation mode',self.page.locator('#south9').inner_text());self.assertNotIn('Auto Fill Kundali',self.page.locator('#south9').inner_text())

    def test_simple_transit_search_explains_rejection_and_filters_actual_intervals(self):
        self.page.locator('#quick-transit').click();self.assertEqual(self.page.locator('#transit select:visible').count(),3);self.assertEqual(self.page.locator('#transit input:visible').count(),0)
        found=self.page.evaluate("""()=>{const select=document.getElementById('tr-event'),found={};for(const o of select.options){select.value=o.value;KPSimpleTransits.apply();try{const c=KPSimpleTransits.criteria(KPTransit.currentPeriods());if(!found.yes)found.yes={id:o.value,periods:c.periods,required:c.required};}catch(e){if(!found.no)found.no={id:o.value,reason:e.message};}if(found.yes&&found.no)break;}return found;}""")
        self.assertEqual(set(found),{'yes','no'});self.page.locator('#tr-event').select_option(found['no']['id']);self.page.locator('#tr-run').click();expect(self.page.locator('#tr-status')).to_have_attribute('data-state','error');expect(self.page.locator('#tr-status')).to_contain_text(found['no']['reason']);self.assertEqual(self.page.evaluate('KPTransit.getResults()'),[])
        self.page.locator('#tr-event').select_option(found['yes']['id']);self.page.locator('#tr-run').click();self.page.wait_for_function("document.getElementById('tr-status').dataset.state!=='running'",timeout=90000);self.assertNotEqual(self.page.locator('#tr-status').get_attribute('data-state'),'error')
        rows=self.page.evaluate('KPTransit.getResults()');self.assertTrue(rows)
        for row in rows:
            self.assertIn(row['planet'],['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke']);self.assertNotIn('undefined',row['label']);self.assertLess(row['start'],row['end']);self.assertTrue(any(row['start']>=p['start'] and row['end']<=p['end'] for p in found['yes']['periods']))

    def test_simple_matchmaking_panchang_and_ephemeris_still_calculate(self):
        self.page.locator('#quick-matchmaking').click();
        self.assertFalse(self.page.locator('.mm-traditional-detail').evaluate('n=>n.open'));expect(self.page.locator('.mm-simple-total')).to_contain_text('/ 36');expect(self.page.locator('[data-mm-method]')).to_have_count(3);self.page.locator('[data-mm-method="kp"]').click();expect(self.page.locator('#mm-kp-panel')).to_be_visible();expect(self.page.locator('#mm-traditional-panel')).to_be_hidden()
        self.page.locator('#quick-transit-panchang').click();self.assertEqual(self.page.locator('#transit-panchang button:visible').count(),3);self.page.locator('#tp-calculate').click();expect(self.page.locator('#tp-positions tbody tr')).to_have_count(10)
        self.page.locator('#quick-ephemeris').click();self.assertEqual(self.page.locator('#ephemeris button:visible').count(),2);self.page.locator('#eph-start').fill('2026-10-09');self.page.locator('#eph-end').fill('2026-10-10');self.page.locator('#eph-run').click();self.page.wait_for_function('KPDailyEphemeris.getData()?.ready');self.assertEqual(self.page.locator('#eph-table tbody tr').count(),18)
    def test_compact_event_manual_layers_and_native_evidence_preserve_chart(self):
        self.page.locator('#quick-event-promise').click()
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        self.page.locator('#ep-mode-manual').click()
        expect(self.page.locator('#ep-mode-manual')).to_have_attribute('aria-pressed','true')
        for role,houses in [('CSL','2 7'),('STL','11'),('SBL','4')]:
            self.page.locator('#ep-houses-'+role).fill(houses);self.page.locator('#ep-houses-'+role).dispatch_event('change')
        d=self.page.evaluate('KPEventPromise.refresh(true)')
        self.assertEqual(d['inputMode'],'manual');self.assertEqual(d['houses'],[2,4,7,11])
        self.page.locator('#ep-layer-SBL').uncheck()
        self.assertEqual(self.page.evaluate('KPEventPromise.refresh(true).houses'),[2,7,11])
        self.page.locator('#ep-houses-CSL').fill('13');self.page.locator('#ep-houses-CSL').dispatch_event('change')
        expect(self.page.locator('#ep-simple-result')).to_contain_text('House numbers must be from 1 through 12')
        expect(self.page.locator('#ep-simple-preview')).to_be_disabled()
        self.page.locator('#ep-mode-auto').click()
        d=self.page.evaluate('KPEventPromise.refresh(true)');self.assertTrue(d['ready'])
        expected=sorted({h for layer in d['layers'] if layer['selected'] for values in layer['levels'].values() for h in values})
        self.assertEqual(d['houses'],expected)
        self.page.locator('.ep-native-evidence summary').click()
        evidence=self.page.evaluate("""()=>{const d=KPEventPromise.refresh(true),c=currentKPModel.houses.find(p=>p.id===d.cusp);return {occ:c.occ.join(', ')||'Empty house',aspects:c.aspd.join(', ')||'None'}}""")
        expect(self.page.locator('#ep-cusp-occupants')).to_have_text(evidence['occ']);expect(self.page.locator('#ep-cusp-aspects')).to_have_text(evidence['aspects'])
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        self.page.screenshot(path='/tmp/compact-event-promise.png',full_page=True)

    def test_prediction_preview_has_only_selected_cusp_results_and_roman_house_selector(self):
        self.page.locator('#quick-prediction').click()
        expect(self.page.locator('#pred-analysis-options')).not_to_have_attribute('open','')
        original=self.page.evaluate('JSON.stringify(currentKPModel)')
        data=self.page.evaluate('KPPrediction.getData()')
        with self.page.expect_popup() as opened:self.page.locator('#prediction-preview').click()
        preview=opened.value
        text=preview.locator('.pred-plain-report').inner_text()
        self.assertNotIn('CSL',text);self.assertNotIn('Required:',text);self.assertNotIn('Matched:',text);self.assertNotIn('Source row',text)
        self.assertGreater(preview.locator('.pred-plain-results li').count(),0)
        pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
        self.assertIn('Kundali Analysis',''.join(p.get_text() for p in pdf));pdf.close();preview.close()
        self.page.locator('#pred-tab-house-results').click()
        self.assertEqual(self.page.locator('#pred-house-cusp option').all_text_contents(),['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'])
        for cusp in [1,4,9,10,12]:
            self.page.locator('#pred-house-cusp').select_option(str(cusp))
            d=self.page.evaluate('KPPersonalPredictions.getData()')
            expected=self.page.evaluate('(c)=>KPPersonalPredictions.matchRules("house-results").rows.filter(r=>Number(/^Bh(1[0-2]|[1-9])R/i.exec(r.key)[1])===c).map(r=>r.id)',cusp)
            self.assertEqual([r['id'] for r in d['rows']],expected);self.assertEqual(d['cusp'],cusp)
        self.page.locator('#pred-house-cusp').select_option('10');d=self.page.evaluate('KPPersonalPredictions.getData()')
        with self.page.expect_popup() as opened:self.page.locator('#prediction-preview').click()
        preview=opened.value;expect(preview.locator('.personal-prediction-report h2')).to_contain_text('Cusp X')
        self.assertEqual(preview.locator('[data-personal-result]').count(),len(d['rows']))
        self.assertEqual(preview.locator('[data-personal-result] small').count(),0)
        for row in d['rows']:self.assertNotIn(row['proof'],preview.locator('.personal-prediction-report').inner_text())
        preview.close();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),original)
        self.page.screenshot(path='/tmp/compact-house-results.png',full_page=True)

    def test_transit_three_modes_use_native_sectors_and_birth_clipped_periods(self):
        self.page.locator('#quick-transit').click();native=self.page.evaluate('JSON.stringify(currentKPModel)')
        for mode,count in [('event',9),('dasha',18),('sun',2)]:
            self.page.locator('#tr-mode').select_option(mode)
            result=self.page.evaluate("""()=>{const data=KPTransit.currentPeriods(),tracks=KPTransit.makeTracks(data),root=KPHomeDasha.getData().levels[0].rows[0],offset=data.timeZoneHours*3600000;return {count:tracks.length,criteria:document.getElementById('tr-mode').value==='event'?'event':KPSimpleTransits.criteria(data),birth:root.startMs-offset,periods:Object.values(data.periods),tracks:tracks.map(t=>({id:t.id,planet:t.planet,levels:t.levels}))}}""")
            self.assertEqual(result['count'],count)
            for period in result['periods']:self.assertGreaterEqual(period['startMs']-5.5*3600000,result['birth'])
            if mode=='event':continue
            self.assertIsNone(result['criteria']);expect(self.page.locator('#tr-event')).to_be_hidden()
            self.page.locator('#tr-run').click();self.page.wait_for_function("document.getElementById('tr-status').dataset.state!=='running'",timeout=90000)
            self.assertNotEqual(self.page.locator('#tr-status').get_attribute('data-state'),'error')
            validity=self.page.evaluate("""()=>{const tracks=KPTransit.makeTracks(KPTransit.currentPeriods()),r=KPTransit.currentRange();return KPTransit.getResults().every(p=>{const t=tracks.find(t=>t.id===p.trackId),mid=new Date((Date.parse(p.start)+Date.parse(p.end))/2),at=KPDisplay.longitudeDetails(KPEphemeris.longitude(mid,p.planet)*3600);return t&&t.test(at)&&Date.parse(p.start)>=r.start.getTime()&&Date.parse(p.end)<=r.end.getTime()&&p.start<p.end})}""")
            self.assertTrue(validity)
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        self.page.screenshot(path='/tmp/compact-transits.png',full_page=True)

    def test_rp_pd_filters_supporting_candidates_and_preserves_transit_results(self):
        self.page.locator('#quick-dasha-promise').click();native=self.page.evaluate('JSON.stringify(currentKPModel)')
        self.page.locator('#dp-md').select_option('1');self.page.locator('#dp-ad').select_option('2')
        event=self.page.evaluate(r'''()=>{const d=KPDashaPromise.getData(),union=[...new Set([...d.mdHouses,...d.adHouses])];return KPHandbook.getCatalogue().events.find(e=>e.automaticEligible&&e.supportingGroups.some(g=>g.every(h=>union.includes(h)))&&(!e.timingRaw||/^(?:1[0-2]|[1-9])(?:\s*,\s*(?:1[0-2]|[1-9]))*$/.test(e.timingRaw)&&e.timingRaw.split(',').map(Number).every(h=>union.includes(h)))).id}''')
        self.page.locator('#dp-event').select_option(str(event))
        self.page.locator('#dp-calculate').click();expect(self.page.locator('#dp-status')).to_contain_text('Calculation complete',timeout=90000)
        all_data=self.page.evaluate('KPDashaPromise.getData()');self.assertTrue(all_data['pdAll'])
        self.page.locator('#dp-rp-pd').click();expect(self.page.locator('#dp-rp-pd')).to_have_attribute('aria-pressed','true')
        filtered=self.page.evaluate('KPDashaPromise.getData()');self.assertTrue(filtered['rp']['ready'])
        actual={r['lord'] for r in filtered['pd']}
        expected=self.page.evaluate("""()=>{const d=KPDashaPromise.getData();return d.pdAll.filter(p=>d.rp.rulingPlanets.includes(KPDisplay.idByName[p.lord]||p.lord)).map(p=>p.lord)}""")
        self.assertEqual(actual,set(expected));self.assertEqual(filtered['sun'],all_data['sun']);self.assertEqual(filtered['outer'],all_data['outer'])
        self.assertEqual(len(filtered['rp']['sources']),5);self.assertEqual(filtered['md'],all_data['md']);self.assertEqual(filtered['ad'],all_data['ad'])
        if filtered['pd']:
            chosen=str(filtered['pd'][-1]['startMs']);self.page.locator('#dp-pd-choice').select_option(chosen)
            self.assertEqual(self.page.evaluate('KPDashaPromise.getData().selectedPD.startMs'),int(chosen))
            expect(self.page.locator('#dp-ad-windows tr.dp-selected-pd')).to_have_count(1)
        with self.page.expect_popup() as opened:self.page.locator('#dasha-promise-preview').click()
        preview=opened.value;expect(preview.locator('.dp-report')).to_contain_text('RP ·');preview.close()
        self.page.locator('#dp-rp-pd').click();restored=self.page.evaluate('KPDashaPromise.getData()');self.assertEqual(restored['pd'],all_data['pdAll'])
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        self.page.locator('#quick-matchmaking').click();self.assertEqual(self.page.get_by_text('Open / Delete Saved Chart',exact=True).count(),0)
        self.assertEqual(self.page.locator('[data-mm-method]').count(),3);expect(self.page.locator('#mm-settings-drawer')).not_to_have_attribute('open','')
        self.page.screenshot(path='/tmp/compact-matchmaking.png',full_page=True)
