"""Functional regression checks for recovered references and new analysis views."""
import functools
import importlib.util
import json
import os
from pathlib import Path
import shutil
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROMIUM = os.environ.get('CALCULATOR_CHROMIUM') or shutil.which('chromium')
FIXTURE_MODEL = """() => {
  const codes=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
  const positions=Object.fromEntries(codes.map((id,i)=>[id,(5+i*30)*3600]));
  positions.Ke=(positions.Ra+180*3600)%(360*3600);
  const model=KPDisplay.build(Array.from({length:12},(_,i)=>i*30*3600),positions);
  const sets={Su:[2,6,10,11],Mo:[2,5,11],Ma:[2,6,10,11],Me:[2],Ju:[5,11],Ve:[7],Sa:[8],Ra:[12],Ke:[3]};
  for(const method of ['fourfold','sixfold'])for(const row of model[method].planets){
    row.A=sets[row.id];for(const key of ['B','C','D','E','F'])row[key]=[];
  }
  return model;
}"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class FeatureUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=CHROMIUM, headless=True, args=['--no-sandbox'])
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/index.html'

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, timeout=60000)
        self.page.wait_for_function('window.KPTimeSlices && window.KPGemstones && document.getElementById("ts-scan")', timeout=60000)
        self.page.wait_for_timeout(450)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def test_original_prediction_catalogues_preserve_counts_conditions_and_duplicate_texts(self):
        data = self.page.evaluate("""() => {
          const pred=KPPrediction.getCatalogue(),ref=KPPredictionLibrary.getCatalogue();
          return {count:pred.events.length,eligible:pred.events.filter(r=>r.automaticEligible).length,
            references:ref.entries.length,short:ref.entries.filter(r=>r.categoryId==='dasha-short').length,
            malformed:ref.entries.find(r=>r.key==='DasaC34511H'&&r.categoryId==='dasha-short'),
            duplicates:ref.entries.filter(r=>r.categoryId==='dasha-short'&&r.duplicateCount>1),
            review:KPPrediction.getData().counts.review};
        }""")
        self.assertEqual((data['count'], data['eligible'], data['references'], data['short']), (1612, 1398, 6213, 391))
        self.assertEqual(data['review'], 214)
        self.assertNotEqual(data['malformed']['mappingStatus'], 'clear')
        self.assertIn('511', data['malformed']['houseMappingRaw'])
        self.assertTrue(data['duplicates'])
        self.assertEqual(len({r['id'] for r in data['duplicates']}), len(data['duplicates']))
        self.page.locator('nav [data-tab="prediction"]').click()
        expect(self.page.locator('#page-title')).to_have_text('Prediction')
        self.page.locator('#pred-tab-dasha-short').click()
        expect(self.page.locator('#pred-library-status')).to_contain_text('391 matching reference entries')

    def test_prediction_subtabs_chart_matches_and_selected_preview_controls(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        for category,count in [('house-results',2869),('general-predictions',824),('events',1046),('dasha-short',391),('dasha-results',1017),('mahadasha-remedies',48),('gemstones',18)]:
            self.page.locator('#pred-tab-'+category).click()
            expect(self.page.locator('#pred-tab-'+category)).to_have_attribute('aria-selected','true')
            expect(self.page.locator('#pred-library-status')).to_contain_text(str(count)+' matching reference entries')
        self.page.locator('#pred-open-gems').click()
        expect(self.page.locator('#page-title')).to_have_text('Gemstone guidance')
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-tab-general-predictions').click()
        self.page.locator('#pred-library-chart').select_option('matched')
        result=self.page.evaluate("""() => ({keys:KPPredictionLibrary.getData().rows.map(r=>r.key),
          expected:currentKPModel.planets.flatMap(p=>[p.id+'InH'+p.occ,p.id+'In'+p.signCode]),
          moon:currentKPModel.planets.find(p=>p.id==='Mo')})""")
        self.assertTrue(set(result['expected']).issubset(result['keys']))
        self.assertIn('Nak'+str(result['moon']['nakIndex']+1)+'C'+str(result['moon']['pada']),result['keys'])
        self.assertFalse(any(key.startswith('Y') for key in result['keys']))
        self.page.locator('#pred-library-search').fill('SuInH')
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-preview').click()
        preview=opened.value
        expect(preview.locator('[data-report-section="prediction"]')).to_be_visible()
        expect(preview.locator('[data-reference-entry]')).to_have_count(1)
        expect(preview.locator('.pred-library-chart-proof')).to_contain_text('Su occupies Bhav')
        preview.evaluate('() => {window.printInvocations=0;window.print=()=>{window.printInvocations++};}')
        preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
        self.assertEqual(preview.evaluate('window.printInvocations'),1)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
        preview.get_by_role('button',name='Zoom −',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1)
        preview.get_by_role('button',name='Close preview',exact=True).click()
        preview.wait_for_event('close') if not preview.is_closed() else None

    def test_long_reference_preview_prints_every_filtered_record_across_pdf_pages(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-tab-dasha-short').click()
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-preview').click()
        preview=opened.value
        expect(preview.locator('[data-reference-entry]')).to_have_count(391)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        preview.emulate_media(media='print')
        self.assertEqual(preview.locator('.report-page').evaluate('n=>getComputedStyle(n).zoom'),'1')
        output=Path('/tmp/kp-short-dasha-preview.pdf')
        preview.pdf(path=str(output),format='A4',prefer_css_page_size=True,print_background=True)
        self.assertGreater(output.stat().st_size,10000)
        if shutil.which('pdftotext'):
            import subprocess
            text=subprocess.check_output(['pdftotext',str(output),'-']).decode()
            self.assertIn('DasaC1911H',text)
            last=self.page.evaluate('KPPredictionLibrary.getData().rows.at(-1).key')
            self.assertIn(last,text)
            self.assertGreater(text.count('\f'),1)
        preview.close()

    def test_dasha_house_lists_are_explicit_and_conditional_or_invalid_rules_never_match(self):
        result = self.page.evaluate("""() => {
          const model=(""" + FIXTURE_MODEL + """)();
          const records=[
            {id:'clear',key:'ambiguous111',houses:[2,6,10,11],mappingStatus:'clear'},
            {id:'condition',key:'conditional',houses:[2,6],mappingStatus:'conditional'},
            {id:'invalid',key:'34511',houses:[3,4,511],mappingStatus:'clear'},
            {id:'partial',key:'partial',houses:[2,5,11],mappingStatus:'clear'}];
          return KPDashaFal.analyze(model,{lords:['Su'],method:'fourfold',records}).results;
        }""")
        self.assertEqual([r['status'] for r in result], ['matched', 'review', 'review', 'partial'])
        self.assertEqual(result[0]['required'], [2, 6, 10, 11])
        self.assertEqual(result[3]['missing'], [5])

    def test_user_gemstone_rules_choose_1_5_11_owners_and_highest_kp_coverage_with_ties(self):
        result = self.page.evaluate("""() => {
          const model=(""" + FIXTURE_MODEL + """)();
          const base={excluded:'',method:'fourfold',roles:['planet'],stones:{Su:'Ruby',Ma:'Coral',Mo:'Pearl'}};
          const select=rule=>KPGemstones.evaluate(model,{...base,...rule}).results.filter(r=>r.qualifies).map(r=>r.id);
          const unequal=(""" + FIXTURE_MODEL + """)();unequal.houses[4].sgl='Ju';unequal.houses[10].sgl='Mo';
          return {vedic:select({mode:'vedic'}),money:select({mode:'kp',required:'2,6,10,11'}),
            child:select({mode:'kp',required:'2,5,11'}),excluded:select({mode:'kp',required:'2,5,11',excluded:'6'}),
            none:select({mode:'kp',required:'4'}),
            unequalVedic:KPGemstones.evaluate(unequal,{...base,mode:'vedic'}).results.filter(r=>r.qualifies).map(r=>r.id)};
        }""")
        self.assertEqual(result['vedic'], ['Su', 'Ma', 'Sa'])  # Aries/Leo/Aquarius lords, not house 9's Jupiter.
        self.assertEqual(result['unequalVedic'], ['Su', 'Ma', 'Sa'])
        self.assertEqual(result['money'], ['Su', 'Ma'])
        self.assertEqual(result['child'], ['Mo'])
        self.assertEqual(result['excluded'], ['Mo'])
        self.assertEqual(result['none'], [])

    def test_gemstone_modes_and_custom_mapping_survive_chart_backup(self):
        self.page.locator('nav [data-tab="gemstones"]').click()
        self.page.locator('#gem-event').select_option('childbirth')
        expect(self.page.locator('#gem-required')).to_have_value('2,5,11')
        self.page.locator('#gem-mode').select_option('vedic')
        expect(self.page.locator('#gem-status')).to_contain_text('Labhesh (11)')
        expect(self.page.locator('#gem-required')).to_be_disabled()
        self.page.get_by_text('Your planet-to-gemstone mapping', exact=True).click()
        self.page.locator('#gem-stone-Su').fill('My ruby reference')
        chart = self.page.evaluate('getChartData()')
        self.assertEqual(chart['fields']['gem-stone-Su']['value'], 'My ruby reference')
        self.assertEqual(chart['fields']['gem-mode']['value'], 'vedic')
        self.page.evaluate('(chart)=>restoreChartData(chart)', chart)
        expect(self.page.locator('#gem-stone-Su')).to_have_value('My ruby reference')
        expect(self.page.locator('#gem-mode')).to_have_value('vedic')

    def test_one_year_dasha_uses_real_periods_and_clamps_leap_anniversary(self):
        result = self.page.evaluate("""() => {
          const data=KPDashaFal.year('2028-02-29','12:00:00',2,{records:[{id:'one',houses:[1],mappingStatus:'clear'}]});
          return {end:data.end,periods:data.periodCount,rows:data.results.map(r=>({start:r.periodStart,end:r.periodEnd,lords:r.lords}))};
        }""")
        self.assertEqual(result['end'], '2029-02-28T12:00:00')
        self.assertGreater(result['periods'], 0)
        self.assertEqual(result['rows'][0]['start'], '2028-02-29T12:00:00')
        self.assertEqual(result['rows'][-1]['end'], result['end'])
        for previous, current in zip(result['rows'], result['rows'][1:]):
            self.assertEqual(previous['end'], current['start'])
        self.assertTrue(all(len(row['lords']) == 2 for row in result['rows']))
        self.page.locator('nav [data-tab="dasha-fal"]').click()
        self.page.locator('#df-depth').select_option('2')
        expect(self.page.locator('#df-pd')).not_to_be_visible()
        expect(self.page.locator('#dasha-fal-preview')).to_be_enabled()

    def test_time_slices_include_endpoints_match_reference_geometry_and_preserve_native(self):
        result = self.page.evaluate("""async () => {
          const before=JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,d:document.getElementById('dob').value,t:document.getElementById('birthTime').value});
          const options={startDate:'2000-01-01',startTime:'12:00:00',endDate:'2000-01-01',endTime:'12:25:00',offset:0,latitude:51.5074,longitude:-0.1278,stepMinutes:10,cuspSource:'transit',eventId:'1',method:'fourfold'};
          const data=await KPTimeSlices.scan(options);
          const after=JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,d:document.getElementById('dob').value,t:document.getElementById('birthTime').value});
          return {ready:data.ready,rows:data.rows,expected:(24.01459044-KPEphemeris.ayanamsha(new Date('2000-01-01T12:00:00Z'))+360)%360,nativeUnchanged:before===after,csv:KPTimeSlices.csv()};
        }""")
        self.assertTrue(result['ready'])
        self.assertEqual([row['local'][11:] for row in result['rows']], ['12:00:00', '12:10:00', '12:20:00', '12:25:00'])
        self.assertAlmostEqual(result['rows'][0]['ascendant'], result['expected'], delta=0.003)
        self.assertNotEqual(result['rows'][0]['ascendant'], result['rows'][-1]['ascendant'])
        self.assertTrue(result['nativeUnchanged'])
        self.assertIn('2000-01-01T12:25:00.000Z', result['csv'])

    def test_time_slice_limits_cancel_and_edit_invalidation(self):
        result = self.page.evaluate("""async () => {
          const base={startDate:'2000-01-01',startTime:'00:00:00',endDate:'2000-01-01',endTime:'08:19:00',offset:5.5,latitude:20,longitude:74,stepMinutes:1,cuspSource:'transit',eventId:'1',method:'fourfold'};
          const invalid=[{stepMinutes:0},{latitude:NaN},{offset:15},{startDate:'2000-02-30'},{endDate:'1999-01-01'},{endDate:'2000-01-02'}].map(change=>{try{KPTimeSlices.validate({...base,...change});return false;}catch(_){return true;}});
          const job=KPTimeSlices.scan(base);KPTimeSlices.invalidate('User cancelled');const cancelled=await job;
          return {invalid,cancelled:cancelled.cancelled,ready:KPTimeSlices.getData().ready,busy:document.getElementById('time-slices').hasAttribute('aria-busy')};
        }""")
        self.assertTrue(all(result['invalid']))
        self.assertTrue(result['cancelled'])
        self.assertFalse(result['ready'])
        self.assertFalse(result['busy'])


class FeatureProtectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('feature_private_server', ROOT / 'protected/server.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.engine = cls.module.Engine()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), cls.module.Handler)
        cls.server.engine = cls.engine
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=CHROMIUM, headless=True, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.engine.close()

    def test_customer_feature_controls_previews_and_source_isolation(self):
        context = self.browser.new_context()
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home', timeout=60000)
            for tab in ['prediction', 'dasha-fal', 'gemstones', 'time-slices']:
                page.locator('nav [data-tab="'+tab+'"]').click()
                expect(page.locator('#'+tab)).to_be_visible(timeout=30000)
            page.locator('nav [data-tab="gemstones"]').click()
            page.locator('#gem-mode').select_option('vedic')
            expect(page.locator('#gem-status')).to_contain_text('Labhesh (11)', timeout=30000)
            exported = page.request.get(self.url+'/export').json()
            self.assertEqual(exported['fields']['gem-mode']['value'], 'vedic')
            page.locator('nav [data-tab="prediction"]').click()
            page.locator('#pred-tab-events').click()
            expect(page.locator('#pred-library-status')).to_contain_text('1046 matching reference entries',timeout=30000)
            page.locator('#pred-library-search').fill('Success in business')
            expect(page.locator('#pred-library-status')).to_contain_text('4 matching reference entries',timeout=30000)
            with page.expect_popup() as opened:
                page.locator('#prediction-preview').click()
            preview=opened.value
            expect(preview.locator('[data-reference-entry]')).to_have_count(4,timeout=90000)
            self.assertLess(preview.get_by_role('button',name='Print / Save PDF',exact=True).bounding_box()['y'],100)
            preview.evaluate('() => {window.printInvocations=0;window.print=()=>{window.printInvocations++};}')
            preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
            self.assertEqual(preview.evaluate('window.printInvocations'),1)
            preview.get_by_role('button',name='Zoom +',exact=True).click()
            self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
            preview.get_by_role('button',name='Zoom −',exact=True).click()
            self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1)
            preview.get_by_role('button',name='Close preview',exact=True).click()
            for section in ['prediction', 'dasha-fal', 'gemstones', 'time-slices']:
                response = page.request.get(self.url+'/'+section+'-preview', timeout=90000)
                self.assertEqual(response.status, 200, response.text()[:200])
                self.assertIn('data-report-section="'+section+'"', response.text())
            snapshot = page.request.get(self.url+'/snapshot').json()
            self.assertNotIn('<script', snapshot['html'])
            self.assertEqual(page.request.get(self.url+'/index.html').status, 404)
            self.assertEqual(errors, [])
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main()
