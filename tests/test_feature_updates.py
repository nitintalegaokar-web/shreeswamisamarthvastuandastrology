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

from playwright.sync_api import Error as PlaywrightError, expect, sync_playwright

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


def close_preview(preview):
    """Assert the Close control closes its window, including early click completion."""
    with preview.expect_event('close'):
        try:
            preview.get_by_role('button',name='Close preview',exact=True).click(no_wait_after=True)
        except PlaywrightError:
            if not preview.is_closed():
                raise


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

    def test_transit_current_periods_use_exact_native_boundaries_and_refresh_lords(self):
        self.page.locator('nav [data-tab="transit"]').click()
        expect(self.page.locator('#tr-period')).to_have_value('PD')
        expect(self.page.locator('#tr-start')).not_to_be_visible()
        expect(self.page.locator('#tr-end')).not_to_be_visible()
        expect(self.page.locator('#tr-reference')).to_have_count(0)
        expect(self.page.locator('[data-current-period]')).to_have_count(3)
        result = self.page.evaluate("""() => {
          const now=KPTransit.currentPeriods(),home=KPHomeDasha.getData();
          const nativeCivil=Date.parse(now.instant)+home.timeZoneHours*3600000;
          let rows=home.levels[0].rows;const checks=[];
          for(const level of ['MD','AD','PD']){
            const expected=rows.find(p=>p.startMs<=nativeCivil&&nativeCivil<p.endMs),p=now.periods[level];
            checks.push(p.startMs===expected.startMs&&p.endMs===expected.endMs&&Date.parse(p.startUTC)===p.startMs-home.timeZoneHours*3600000&&Date.parse(p.endUTC)===p.endMs-home.timeZoneHours*3600000);
            rows=KPHomeDasha.subdivide(expected);
          }
          const next=KPTransit.currentPeriods(new Date(now.periods.PD.endUTC));
          let outside=false;try{KPTransit.currentPeriods(new Date('2300-01-01T00:00:00Z'));}catch(_){outside=true;}
          return {checks,outside,nextStart:next.periods.PD.startUTC,previousEnd:now.periods.PD.endUTC};
        }""")
        self.assertTrue(all(result['checks']))
        self.assertTrue(result['outside'])
        self.assertEqual(result['nextStart'], result['previousEnd'])
        self.page.locator('#tr-mode').select_option('dasha')
        for level in ['MD', 'AD', 'PD']:
            self.page.locator('#tr-period').select_option(level)
            data = self.page.evaluate("""() => {
              const p=KPTransit.currentPeriods(),r=KPTransit.currentRange(p),summary=document.getElementById('tr-period-summary');
              return {start:r.start.toISOString(),end:r.end.toISOString(),summaryStart:summary.dataset.start,summaryEnd:summary.dataset.end,lords:KPTransit.autoDasha(p),selected:['tr-md','tr-ad','tr-pd'].map(id=>document.getElementById(id).value)};
            }""")
            self.assertEqual(data['start'],data['summaryStart'])
            self.assertEqual(data['end'],data['summaryEnd'])
            self.assertEqual(data['selected'],[data['lords'][level] for level in ['MD','AD','PD']])
        self.page.locator('#tr-timezone').select_option('0')
        utc = self.page.evaluate('KPTransit.currentRange().start.toISOString()')
        self.assertEqual(utc,data['start'])
        expect(self.page.locator('#tr-period-summary')).to_contain_text('UTC')

    def test_transit_search_uses_current_pd_and_accepts_complete_twenty_year_md(self):
        self.page.locator('nav [data-tab="transit"]').click()
        self.page.locator('#tr-mode').select_option('sun')
        self.page.locator('#tr-run').click()
        expect(self.page.locator('#tr-status')).to_contain_text('matching transit interval',timeout=60000)
        result = self.page.evaluate("""async () => {
          const range=KPTransit.currentRange(),found=KPTransit.getResults();
          const start=new Date('2000-01-01T12:34:56Z'),end=new Date('2020-01-01T12:34:56Z');
          const long=await KPTransit.scan({start,end,tracks:[{id:'whole',planet:'Su',label:'whole range',levels:[],test:()=>true}]});
          return {within:found.every(row=>Date.parse(row.start)>=range.start.getTime()&&Date.parse(row.end)<=range.end.getTime()),long};
        }""")
        self.assertTrue(result['within'])
        self.assertEqual(len(result['long']),1)
        self.assertEqual(result['long'][0]['start'],'2000-01-01T12:34:56.000Z')
        self.assertEqual(result['long'][0]['end'],'2020-01-01T12:34:56.000Z')
        self.page.locator('#tr-period').select_option('AD')
        self.assertEqual(self.page.evaluate('KPTransit.getResults().length'),0)

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
        close_preview(preview)
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

    def test_kundali_comparison_highlights_matches_and_opens_sample_chart_popups(self):
        expect(self.page.locator('nav [data-tab="time-slices"]')).to_have_count(0)
        expect(self.page.locator('#south9 #time-slices')).to_have_count(1)
        expect(self.page.locator('#mm-csv,#ts-csv,#gem-csv,#df-csv')).to_have_count(0)
        self.page.locator('nav [data-tab="south9"]').click()
        before=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,d:document.getElementById("dob").value})')
        result=self.page.evaluate("""async () => KPTimeSlices.scan({startDate:'2000-01-01',startTime:'12:00:00',endDate:'2000-01-01',endTime:'12:20:00',offset:0,latitude:51.5074,longitude:-0.1278,stepMinutes:10,cuspSource:'transit',eventId:'1',method:'fourfold'})""")
        self.assertTrue(result['ready'])
        for index,row in enumerate(result['rows']):
            expect(self.page.locator('#ts-results tr').nth(index)).to_have_attribute('data-ts-status',row['status'])
        matched=self.page.locator('#ts-results tr[data-ts-status="matched"]')
        self.assertGreater(matched.count(),0)
        self.assertEqual(matched.first.locator('td').first.evaluate('n=>getComputedStyle(n).backgroundColor'),'rgb(232, 245, 236)')
        for index,view,attribute in [(0,'transit-chart','transit'),(1,'nadi-astrology','nadi')]:
            with self.page.expect_popup() as opened:
                self.page.locator('[data-ts-'+attribute+'="'+str(index)+'"]').click()
            preview=opened.value
            expect(preview.locator('[data-report-section="'+view+'"]')).to_be_visible()
            expect(self.page.locator('#south9')).to_have_class('tab active')
            expect(preview.get_by_role('button',name='Print / Save PDF',exact=True)).to_be_visible()
            prefix='tc' if attribute=='transit' else 'na'
            self.assertEqual(self.page.locator('#'+prefix+'-date').input_value(),'2000-01-01')
            self.assertEqual(self.page.locator('#'+prefix+'-time').input_value(),['12:00:00','12:10:00'][index])
            close_preview(preview)
        after=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,d:document.getElementById("dob").value})')
        self.assertEqual(before,after)
        expect(self.page.locator('#printReport [data-report-section="south9"] #ts-scan')).to_have_count(0)

    def test_gemstone_event_groups_compact_line_and_original_ratna_printing(self):
        self.page.locator('nav [data-tab="gemstones"]').click()
        self.page.locator('#gem-event').select_option('kp:1354:0')
        expect(self.page.locator('#gem-required')).to_have_value('2,6,10,11')
        expect(self.page.locator('#gem-event-proof')).to_contain_text('Prediction catalogue #1354')
        self.page.locator('#gem-event-search').fill('promotion')
        self.assertFalse(self.page.locator('#gem-event option[value="kp:1354:0"]').evaluate('n=>n.hidden'))
        self.assertTrue(self.page.locator('#gem-event option[value="kp:841:0"]').evaluate('n=>n.hidden'))
        choices=self.page.locator('#gem-event option').evaluate_all('nodes=>nodes.filter(n=>n.value.startsWith("named:")).map(n=>({value:n.value,text:n.textContent}))')
        self.assertGreater(len(choices),1000)
        # A name-only uploaded event cannot acquire an invented house rule.
        self.page.locator('#gem-event-search').fill('')
        self.page.locator('#gem-event').select_option(choices[0]['value'])
        expect(self.page.locator('#gem-required')).to_have_value('')
        expect(self.page.locator('#gem-status')).to_have_attribute('data-ready','false')
        self.page.locator('#gem-required').fill('2,5,11')
        expect(self.page.locator('#gem-status')).to_have_attribute('data-ready','true')
        self.page.set_viewport_size({'width':1440,'height':1000})
        tops=self.page.locator('.gem-rule-line input').evaluate_all('nodes=>nodes.map(n=>n.getBoundingClientRect().top)')
        self.assertLess(max(tops)-min(tops),2)
        self.assertLessEqual(self.page.locator('#gemstones-preview').bounding_box()['height'],30)
        original=self.page.evaluate('KPPredictionLibrary.getCatalogue().entries.find(r=>r.categoryId==="gemstones"&&r.key==="RatnaH").value').replace(r'\n','\n')
        with self.page.expect_popup() as opened:
            self.page.locator('#gemstones-preview').click()
        preview=opened.value
        self.assertEqual(preview.locator('[data-ratna-key="RatnaH"] p').inner_text(),original)
        preview.close()
        chart=self.page.evaluate('getChartData()')
        self.assertEqual(chart['fields']['gem-event']['value'],choices[0]['value'])

    def test_dasha_report_contains_only_original_filtered_result_text(self):
        self.page.locator('nav [data-tab="dasha-fal"]').click()
        self.page.locator('#df-source').select_option('manual')
        self.page.locator('#df-md').select_option('Su')
        self.page.locator('#df-ad').select_option('')
        self.page.locator('#df-pd').select_option('')
        self.page.locator('#df-filter').select_option('all')
        expected=[text.replace(r'\n','\n') for text in self.page.evaluate('KPDashaFal.getData().results.filter(r=>r.record.categoryId==="dasha-short").map(r=>r.record.value)')]
        with self.page.expect_popup() as opened:
            self.page.locator('#dasha-fal-preview').click()
        preview=opened.value
        expect(preview.locator('.df-text-report table')).to_have_count(0)
        expect(preview.locator('[data-df-result-text]')).to_have_count(391)
        self.assertEqual(preview.locator('[data-df-result-text] p').all_text_contents(),expected)
        text=preview.locator('.df-text-report').inner_text()
        self.assertNotIn('Dahs Fal Short.txt',text)
        self.assertNotIn('Mapping source line',text)
        self.assertNotIn('House group matched',text)
        preview.close()

    def test_prediction_reports_scope_to_selected_cusp_and_chain_preview_is_separate(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-main-house').select_option('7')
        self.page.locator('#pred-match-filter').select_option('all')
        expect(self.page.locator('#pred-status')).to_contain_text('Cusp 7')
        with self.page.expect_popup() as opened:
            self.page.locator('#pred-print').click()
        preview=opened.value
        expect(preview.locator('[data-pred-print-chains]')).to_have_count(0)
        expect(preview.locator('.pred-report')).to_have_attribute('data-main-cusp','7')
        mains=preview.locator('[data-pred-event]>td:nth-child(3)').all_text_contents()
        self.assertTrue(mains and all(main=='7' for main in mains))
        self.assertFalse(self.page.locator('#printReport [data-report-section="prediction-chains"]').count())
        preview.close()
        self.page.locator('#prediction-chains-preview').locator('..').locator('summary').click()
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-chains-preview').click()
        preview=opened.value
        expect(preview.locator('[data-pred-cusp]')).to_have_count(1)
        expect(preview.locator('[data-pred-cusp]')).to_have_attribute('data-pred-cusp','7')
        preview.evaluate('() => {window.calls=0;window.print=()=>{window.calls++};}')
        preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
        self.assertEqual(preview.evaluate('window.calls'),1)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
        preview.get_by_role('button',name='Zoom −',exact=True).click()
        close_preview(preview)
        self.page.locator('#pred-main-house').select_option('0')
        expect(self.page.locator('#pred-print')).to_be_disabled()
        expect(self.page.locator('#prediction-preview')).to_be_disabled()


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
            page.locator('nav [data-tab="transit"]').click()
            expect(page.locator('#tr-period')).to_have_value('PD',timeout=30000)
            expect(page.locator('[data-current-period]')).to_have_count(3)
            expect(page.locator('#tr-start')).not_to_be_visible()
            page.locator('#tr-period').select_option('AD')
            expect(page.locator('#tr-period-summary')).to_contain_text('Current AD',timeout=30000)
            for tab in ['prediction', 'dasha-fal', 'gemstones', 'south9']:
                page.locator('nav [data-tab="'+tab+'"]').click()
                expect(page.locator('#'+tab)).to_be_visible(timeout=30000)
            expect(page.locator('#south9 #time-slices')).to_be_visible()
            expect(page.locator('nav [data-tab="time-slices"]')).to_have_count(0)
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
            close_preview(preview)
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

    def test_private_sample_popups_chain_preview_and_restricted_reports(self):
        context=self.browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('nav [data-tab="south9"]').click()
            expect(page.locator('#south9')).to_have_class('tab active',timeout=30000)
            snapshot=page.request.get(self.url+'/snapshot').json()
            token=snapshot['token']
            before=page.request.get(self.url+'/export').json()['fields']
            for id,value in [('ts-start-date','2000-01-01'),('ts-start-time','12:00:00'),('ts-end-date','2000-01-01'),('ts-end-time','12:20:00'),('ts-offset','0'),('ts-latitude','51.5074'),('ts-longitude','-0.1278')]:
                response=page.request.post(self.url+'/event',data={'id':page.locator('#'+id).get_attribute('data-bridge-id'),'kind':'change','value':value},headers={'X-KP-Session':token})
                self.assertEqual(response.status,200,response.text()[:300])
            page.locator('#ts-scan').click()
            expect(page.locator('#ts-status')).to_contain_text('3 samples',timeout=30000)
            expect(page.locator('#ts-results tr[data-ts-status="matched"]')).to_have_count(3)
            for attribute,index,section in [('transit',0,'transit-chart'),('nadi',1,'nadi-astrology')]:
                with page.expect_popup() as opened:
                    page.locator('[data-ts-'+attribute+'="'+str(index)+'"]').click()
                preview=opened.value
                expect(preview.locator('[data-report-section="'+section+'"]')).to_be_visible(timeout=60000)
                expect(page.locator('#south9')).to_have_class('tab active')
                self.assertLess(preview.get_by_role('button',name='Print / Save PDF',exact=True).bounding_box()['y'],100)
                close_preview(preview)
            self.assertEqual(page.request.get(self.url+'/time-slice-chart-preview?index=-1&view=transit-chart').status,400)
            self.assertEqual(page.request.get(self.url+'/time-slice-chart-preview?index=0&view=ayan').status,400)
            after=page.request.get(self.url+'/export').json()['fields']
            for id in ['name','dob','birthTime']:
                self.assertEqual(before.get(id),after.get(id))
            page.locator('nav [data-tab="prediction"]').click()
            expect(page.locator('#prediction')).to_have_class('tab active',timeout=30000)
            page.locator('#pred-main-house').select_option('7')
            expect(page.locator('#pred-status')).to_contain_text('Cusp 7',timeout=30000)
            response=page.request.get(self.url+'/prediction-preview')
            self.assertEqual(response.status,200)
            self.assertNotIn('data-pred-print-chains',response.text())
            self.assertIn('data-main-cusp="7"',response.text())
            page.locator('#prediction-chains-preview').locator('..').locator('summary').click()
            expect(page.locator('#prediction-chains-preview')).to_be_visible(timeout=30000)
            with page.expect_popup() as opened:
                page.locator('#prediction-chains-preview').click()
            preview=opened.value
            expect(preview.locator('[data-pred-cusp]')).to_have_count(1,timeout=60000)
            expect(preview.locator('[data-pred-cusp]')).to_have_attribute('data-pred-cusp','7')
            preview.close()
            response=page.request.get(self.url+'/dasha-fal-preview')
            self.assertEqual(response.status,200)
            self.assertIn('df-text-report',response.text())
            self.assertNotIn('data-df-record',response.text())
            response=page.request.get(self.url+'/gemstones-preview')
            self.assertEqual(response.status,200)
            self.assertIn('data-ratna-key="RatnaH"',response.text())
            self.assertEqual(errors,[])
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main()
