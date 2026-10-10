"""Muhurta boundary, natal evidence and consultation UI regression checks."""
import functools
import threading
import unittest
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import fitz
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass
class MuhurtaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);cls.url=f'http://127.0.0.1:{cls.server.server_port}/index.html'
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.thread.join(timeout=5);cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000});self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.goto(self.url);self.page.wait_for_selector('#quick-muhurta');self.page.wait_for_selector('#pred-dba-select',state='attached');self.page.wait_for_timeout(300)
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def search(self):
        self.page.locator('#quick-muhurta').click();self.page.locator('#mu-start').fill('2026-10-10');self.page.locator('#mu-span').select_option('30');self.page.locator('#mu-find').click();self.page.wait_for_function('KPMuhurta.getData().ready',timeout=60000);return self.page.evaluate('KPMuhurta.getData()')
    def test_panchang_windows_avoid_solar_periods_and_refine_actual_boundaries(self):
        original=self.page.evaluate('JSON.stringify(currentKPModel)');d=self.search();self.assertGreater(len(d['windows']),0);self.assertFalse(d['native']['ready']);self.assertGreaterEqual(self.page.locator('#mu-purpose option').count(),25)
        for w in d['windows']:
            day=next(x for x in d['dayData'] if x['date']==w['date']);self.assertGreaterEqual(w['start'],day['rise']);self.assertLessEqual(w['end'],day['set']);self.assertLess(w['start'],w['end']);self.assertEqual(w['start']%1000,0);self.assertEqual(w['end']%1000,0)
            for excluded in day['excluded']:self.assertTrue(w['end']<=excluded['start'] or w['start']>=excluded['end'])
            self.assertIn(w['panchang']['tithiIndex']%15+1,d['profile']['tithis']);self.assertIn(w['panchang']['nakIndex'],d['profile']['nakshatras']);self.assertNotEqual(w['panchang']['karana'],'Vishti');self.assertNotIn(w['panchang']['yogaIndex'],[0,5,8,9,12,14,16,18,26]);self.assertEqual(w['kp']['status'],'Not assessed')
            for t in [w['start']+1000,(w['start']+w['end'])/2,w['end']-1000]:
                p=self.page.evaluate('''t=>{const d=new Date(t),su=KPEphemeris.longitude(d,'Su'),mo=KPEphemeris.longitude(d,'Mo');return KPSinglePageReport.panchang(su*3600,mo*3600,'2026-10-28')}''',t)
                for key in ['halfTithiIndex','yogaIndex','nakIndex','moonSignIndex']:self.assertEqual(p[key],w['panchang'][key])
        self.assertEqual(original,self.page.evaluate('JSON.stringify(currentKPModel)'))
        # Wednesday Rahu Kalam is the fifth daylight eighth, not a fixed clock slot.
        day=next(x for x in d['dayData'] if x['weekday']==3);rahu=day['excluded'][0];self.assertAlmostEqual((rahu['start']-day['rise'])/(day['set']-day['rise']),.5,places=7)
        self.assertEqual(self.page.locator('#quick-gemstones').count(),0)
        self.page.locator('#mu-purpose').select_option('marriage');expect(self.page.locator('#muhurta-preview')).to_be_disabled();expect(self.page.locator('#mu-results tbody tr')).to_have_count(0)
    def test_natal_tara_moon_and_supplied_kp_house_evidence_are_required(self):
        d=self.page.evaluate('''async()=>{
          document.getElementById('instant-prashna').value='0';document.getElementById('dob').value='1986-07-15';document.getElementById('birthTime').value='15:45:00';
          const m=structuredClone(currentKPModel),moon=m.planets.find(p=>p.id==='Mo');moon.nakIndex=0;moon.signIndex=1;
          for(const p of m.fourfold.planets){p.A=Array.from({length:12},(_,i)=>i+1);p.B=p.C=p.D=[];}window.currentKPModel=m;
          const options={purpose:'vehicle',start:'2026-10-10',days:30,location:{place:'Pune',latitude:18.52,longitude:73.85,timezone:5.5}};
          const supported=await KPMuhurta.search(options);
          for(const p of m.fourfold.planets){p.A=[8];p.B=p.C=p.D=[];}window.currentKPModel=m;
          const rejected=await KPMuhurta.search(options);
          return {supported,rejected};}''')
        supported=d['supported'];self.assertTrue(supported['native']['ready']);self.assertGreater(len(supported['windows']),0)
        for w in supported['windows']:
            self.assertIn(w['tarabala'],[2,4,6,8,9]);self.assertIn(w['moonHouse'],[1,3,6,7,10,11]);self.assertEqual(w['kp']['status'],'Supported');self.assertEqual(w['kp']['event']['id'],128);self.assertEqual(len(w['kp']['DBA']),3)
        self.assertEqual(len(d['rejected']['windows']),len(supported['windows']))
        self.assertTrue(all(w['kp']['status']=='Not supported' for w in d['rejected']['windows']))
    def test_polar_missing_sunrise_invalid_dates_and_cancellation_have_no_fabricated_results(self):
        result=self.page.evaluate('''async()=>{const base={purpose:'general',start:'2026-06-20',days:1,location:{place:'Tromso',latitude:69.65,longitude:18.96,timezone:2}},polar=await KPMuhurta.search(base);let invalid='',cancel='';try{await KPMuhurta.search({...base,start:'2026-02-30'})}catch(e){invalid=e.message}try{await KPMuhurta.search({...base,location:{place:'Pune',latitude:18.52,longitude:73.85,timezone:5.5}},()=>{},()=>true)}catch(e){cancel=e.message}return {polar,invalid,cancel};}''')
        self.assertEqual(result['polar']['windows'],[]);self.assertEqual(result['polar']['skipped'],['2026-06-20']);self.assertTrue(result['invalid']);self.assertEqual(result['cancel'],'Search cancelled.')
    def test_preview_prints_every_window_on_a4_with_safe_margins_and_marathi_controls(self):
        d=self.search()
        with self.page.expect_popup() as opened:self.page.locator('#muhurta-preview').click()
        preview=opened.value;expect(preview.locator('.kp-preview-tools button')).to_have_count(4);expect(preview.locator('[data-muhurta-row]')).to_have_count(len(d['windows']));preview.get_by_role('button',name='Zoom +',exact=True).click();self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>Number(n.style.zoom)'),1.1);preview.get_by_role('button',name='Zoom −',exact=True).click();preview.emulate_media(media='print');pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');text='\n'.join(p.get_text() for p in pdf)
        for w in d['windows']:self.assertIn(w['date'],text)
        for page in pdf:
            self.assertAlmostEqual(page.rect.width,595.28,delta=1);self.assertAlmostEqual(page.rect.height,841.89,delta=1)
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        if span['text'].strip():self.assertGreaterEqual(span['bbox'][0],25);self.assertLessEqual(span['bbox'][2],page.rect.width-25);self.assertLessEqual(span['bbox'][3],page.rect.height-25)
        pdf.close();preview.close();self.page.evaluate("KPPreferences.save({...KPPreferences.get(),language:'marathi'});KPLanguage.apply()");expect(self.page.locator('#mu-find')).to_contain_text('मुहूर्त शोधा');expect(self.page.locator('#mu-find')).to_contain_text('Find Muhurta');expect(self.page.locator('#mu-purpose option').first).to_have_text('सामान्य शुभकार्य');self.page.set_viewport_size({'width':390,'height':844});self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
    def test_vedic_lagna_and_kp_native_methods_filter_actual_intervals(self):
        self.page.locator('#quick-muhurta').click();expect(self.page.locator('#mu-method')).to_have_value('parashari');expect(self.page.locator('#mu-kp-event-wrap')).to_be_hidden()
        native=self.page.evaluate('JSON.stringify(currentKPModel)');vedic=self.search();self.assertEqual(vedic['method'],'parashari');self.assertTrue(vedic['windows'])
        for w in vedic['windows']:
            self.assertTrue(w['vedic']['qualifies']);self.assertNotIn(w['vedic']['lordHouse'],[6,8,12]);self.assertNotIn(w['vedic']['moonHouse'],[6,8,12]);self.assertTrue(w['vedic']['support']);self.assertNotIn(w['vedic']['lord'],w['vedic']['combust'])
            for t in [w['start']+1000,(w['start']+w['end'])/2,w['end']-1000]:
                value=self.page.evaluate('t=>{const d=new Date(t),l=KPMuhurta.getData().location;return KPMuhurta.parashari(KPEphemeris.positions(d),KPEphemeris.ascendant(d,l.latitude,l.longitude),d)}',t)
                self.assertTrue(value['qualifies']);self.assertEqual(value['key'],w['vedic']['key'])
        self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)
        self.page.locator('#mu-method').select_option('kp');expect(self.page.locator('#mu-kp-event-wrap')).to_be_visible();expect(self.page.locator('#muhurta-preview')).to_be_disabled();self.page.locator('#mu-find').click();self.page.wait_for_function('!KPMuhurta.busy()');self.assertFalse(self.page.evaluate('KPMuhurta.getData().ready'));expect(self.page.locator('#mu-status')).to_contain_text('native birth kundali')
        outcome=self.page.evaluate("""async()=>{document.getElementById('instant-prashna').value='0';document.getElementById('dob').value='1986-07-15';document.getElementById('birthTime').value='15:45:00';const m=structuredClone(currentKPModel);for(const p of m.fourfold.planets){p.A=Array.from({length:12},(_,i)=>i+1);p.B=p.C=p.D=[];}window.currentKPModel=m;const options={method:'kp',purpose:'vehicle',start:'2026-10-10',days:7,location:{place:'Pune',latitude:18.52,longitude:73.85,timezone:5.5}},supported=await KPMuhurta.search(options);for(const p of m.fourfold.planets)p.A=[8];const unsupported=await KPMuhurta.search(options);return {supported,unsupported};}""")
        self.assertTrue(outcome['supported']['windows']);self.assertTrue(all(w['kp']['status']=='Supported' for w in outcome['supported']['windows']));self.assertEqual(outcome['unsupported']['windows'],[])
        self.assertTrue(any(w['start']<next(day for day in outcome['supported']['dayData'] if day['date']==w['date'])['rise'] or w['end']>next(day for day in outcome['supported']['dayData'] if day['date']==w['date'])['set'] for w in outcome['supported']['windows']))

    def test_events_use_current_dba_and_keep_manual_selection_in_preview(self):
        self.page.locator('#quick-prediction').click();self.page.locator('#pred-tab-events').click();data=self.page.evaluate('KPPersonalPredictions.getData()');current=self.page.evaluate('KPTransit.currentPeriods().periods');self.assertEqual(data['mode'],'current');self.assertEqual([p['id'] for p in data['periods']],[current[k]['id'] for k in ['MD','AD','PD']])
        for row in data['rows']:
            required=set(row['requiredHouses']);self.assertTrue(required.issubset({h for p in row['dba'] for h in p['houses']}));self.assertTrue(all(required&set(p['houses']) for p in row['dba']))
        self.page.locator('#pred-dba-select').click();self.page.locator('#pred-event-md').select_option('1');self.page.locator('#pred-event-ad').select_option('2');self.page.locator('#pred-event-pd').select_option('3');manual=self.page.evaluate('KPPersonalPredictions.getData()');self.assertEqual(manual['mode'],'selected');self.assertNotEqual([p['key'] for p in manual['periods']],[p['key'] for p in data['periods']]);self.page.locator('#quick-home').click();self.page.locator('#quick-prediction').click();self.assertEqual(self.page.evaluate('KPPersonalPredictions.getData().periods'),manual['periods'])
        with self.page.expect_popup() as opened:self.page.locator('#prediction-preview').click()
        preview=opened.value;expect(preview.locator('.personal-prediction-report')).to_contain_text('Selected DBA');expect(preview.locator('[data-personal-result]')).to_have_count(len(manual['rows']));preview.close();self.page.locator('#pred-dba-current').click();self.assertEqual(self.page.evaluate('KPPersonalPredictions.getData().mode'),'current');expect(self.page.locator('#pred-tab-dasha-short')).to_have_count(0)
    def test_matchmaking_has_one_collapsed_settings_arrow_and_retains_search(self):
        self.page.locator('#quick-matchmaking').click();self.page.locator('[data-mm-method="kp"]').click();expect(self.page.locator('#mm-settings-drawer')).not_to_have_attribute('open','');expect(self.page.locator('#mm-kp-find')).to_be_hidden();expect(self.page.locator('#mm-settings-evidence')).to_contain_text('KP subtotal');self.page.locator('#mm-settings-drawer>summary').click();expect(self.page.locator('#mm-kp-find')).to_be_visible();expect(self.page.locator('#mm-settings-common .mm-simple-options')).to_have_count(1);self.page.locator('#mm-kp-date').fill('2026-10-10');self.page.locator('#mm-kp-find').click();self.page.wait_for_function('KPMatchmaking.getMarriageData().ready',timeout=90000);self.page.locator('#mm-settings-drawer>summary').click();expect(self.page.locator('#mm-kp-find')).to_be_hidden();expect(self.page.locator('#mm-kp-analysis .ep-date-answer')).to_be_visible()
