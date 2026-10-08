"""Functional checks for the private calculation server and public interface."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kp_private_server',ROOT/'protected/server.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ProtectedServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=module.Engine()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler);cls.server.engine=cls.engine
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.thread.join();cls.server.server_close();cls.engine.close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1600,'height':1000})
        self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto(self.url);expect(self.page.locator('#page-title')).to_have_text('Home',timeout=30000)
        self.snapshot=self.page.request.get(self.url+'/snapshot').json();self.token=self.snapshot['token']
    def tearDown(self):
        self.context.close()
        token=self.token
        def discard():
            session=self.engine.sessions.pop(token,None)
            if session:session['context'].close()
        self.engine.executor.submit(discard).result()
        self.assertEqual(self.errors,[])
    def post(self,path,data,token=None):
        return self.page.request.post(self.url+path,data=data,headers={'X-KP-Session':token or self.token})
    def go(self,tab):
        self.page.locator(f'nav [data-tab="{tab}"]').click();self.page.wait_for_timeout(700)
    def private(self,expression):
        return self.engine.executor.submit(lambda:self.engine.sessions[self.token]['page'].evaluate(expression)).result()
    def test_computer_form_save_export_and_open_in_private_worker(self):
        self.go('basic')
        self.assertTrue(self.private('Boolean(window.KPProtectedWorker)'))
        name=self.page.locator('#pc-natal-name').get_attribute('data-bridge-id')
        save=self.page.locator('#pc-natal-save').get_attribute('data-bridge-id')
        self.assertEqual(self.post('/event',{'id':name,'kind':'change','value':'Private native'}).status,200)
        self.assertEqual(self.post('/event',{'id':save,'kind':'click'}).status,200)
        chart=self.page.request.get(self.url+'/export').json()
        self.assertEqual(chart['fields']['name']['value'],'Private native')
        self.assertFalse(any(k.startswith('pc-') for k in chart['fields']))
        self.assertEqual(self.post('/import',{'chart':chart}).status,200)
        self.assertEqual(self.private("document.getElementById('pc-natal-name').value"),'Private native')
        self.assertEqual(self.private('KPChartStyle.getStyle()'),'south')

    def test_quick_access_fonts_and_preferences_survive_new_session(self):
        for tab in module.PRIVATE_TABS:
            self.assertEqual(self.page.locator('#quick-'+tab).count(),0)
        self.page.locator('#quick-astrosettings').click()
        self.page.wait_for_timeout(600)
        self.page.locator('#font-zoom-in').click()
        self.page.wait_for_timeout(600)
        expect(self.page.locator('#setting-fontSize')).to_have_value('13')
        self.page.locator('#settings-save').click()
        self.page.wait_for_timeout(1100)
        saved=self.page.evaluate("JSON.parse(localStorage.getItem('kpProtectedPreferencesV1'))")
        self.assertEqual(saved['fontSize'],13)
        self.context.clear_cookies()
        self.page.reload()
        expect(self.page.locator('#page-title')).to_have_text('Home',timeout=30000)
        self.page.wait_for_timeout(1200)
        snapshot=self.page.request.get(self.url+'/snapshot').json()
        new_token=snapshot['token']
        self.assertEqual(snapshot['preferences']['fontSize'],13)
        self.engine.executor.submit(lambda:self.engine.sessions.pop(new_token)['context'].close()).result()

    def test_private_sources_and_calculation_controls_are_not_public(self):
        for path in ['/index.html','/protected/server.py','/../index.html','/tests/test_calculator.py']:
            self.assertEqual(self.page.request.get(self.url+path).status,404)
        public=self.snapshot['html']
        for secret in ['<script','function calculateAll','r5_nirayan_1','mdFormulaKala','id="settings-pane-calculation"']:
            self.assertNotIn(secret,public)
        forged=self.post('/event',{'id':'r5_nirayan_1','kind':'change','value':'0:00:00'})
        self.assertEqual(forged.status,400)
        field=self.page.locator('#name').get_attribute('data-bridge-id')
        self.assertEqual(self.post('/event',{'id':field,'kind':'change','value':'forged'},'wrong').status,403)
    def test_birth_edit_recalculates_automatic_houses_and_keeps_dasha(self):
        self.go('basic');self.page.locator('#name').fill('Native private');self.page.locator('#name').blur();self.page.wait_for_timeout(700)
        self.page.locator('[data-action="calculate"]').first.click();self.page.wait_for_timeout(1500)
        result=self.private("() => {const m=KPHorary.nativeMoment(),expected=KPTransitHouses.calculate(m.date,m.latitude,m.longitude).cusps;return {expected,actual:syncKPWorksheetPositions().cusps.map(n=>n/3600),md:document.getElementById('mdBirthDasha').value,name:document.getElementById('name').value};}")
        self.assertEqual(result['name'],'Native private');self.assertTrue(result['md'])
        for actual,expected in zip(result['actual'],result['expected']):self.assertAlmostEqual(actual,expected,delta=1/3600)
    def test_dms_input_preserves_user_coordinates_in_lkp(self):
        self.go('transit-chart');self.page.locator('.tc-reference-location > summary').click();self.page.wait_for_timeout(500)
        dms=self.page.locator('#tc-latitude-dms');expect(dms).to_be_visible()
        dms.fill('19:59:50 N');dms.blur();self.page.wait_for_timeout(700)
        chart=self.page.request.get(self.url+'/export').json()
        self.assertAlmostEqual(float(chart['fields']['tc-latitude']['value']),19+59/60+50/3600)
        self.assertFalse(any(k.startswith(('r5_','p6_')) for k in chart['fields']))
        self.assertEqual(self.post('/import',{'chart':chart}).status,200)
        self.assertAlmostEqual(self.private("()=>Number(document.getElementById('tc-latitude').value)"),19+59/60+50/3600)
    def test_print_selection_excludes_private_worksheets_and_repeats_double_frame(self):
        self.private("()=>KPReportPages.selectSections(['single-page','mdcalc','ayan'])")
        response=self.page.request.get(self.url+'/print');self.assertEqual(response.status,200)
        report=response.text()
        self.assertIn('data-report-section="single-page"',report)
        self.assertIn('data-report-section="mdcalc"',report)
        self.assertNotIn('data-report-section="ayan"',report)
        self.assertNotIn('id="mdFormulaKala"',report)
        self.assertIn('border:3px double',report)
        self.private('()=>KPReportPages.clear()')
        self.assertEqual(self.page.request.get(self.url+'/print').status,400)
    def test_transit_preview_routes_return_only_selected_report_without_auto_print(self):
        for section in ('transit','transit-chart','transit-panchang','ephemeris','event-promise','education-profession','disease','dasha-promise','nadi-astrology','south9'):
            response=self.page.request.get(self.url+'/'+section+'-preview')
            self.assertEqual(response.status,200,response.text()[:200])
            html=response.text()
            self.assertIn('data-report-section="'+section+'"',html)
            self.assertIn('Print / Save PDF',html)
            self.assertNotIn('window.onload=()=>setTimeout(()=>window.print()',html)

    def test_significator_method_preview_selects_current_method(self):
        self.private("()=>{document.getElementById('sig-method').value='kp-sixfold';}")
        response=self.page.request.get(self.url+'/significators-preview')
        self.assertEqual(response.status,200)
        self.assertIn('data-report-section="kp-sixfold"',response.text())

    def test_matchmaking_preview_does_not_automatically_print(self):
        response=self.page.request.get(self.url+'/match-preview')
        self.assertEqual(response.status,200)
        html=response.text()
        self.assertIn('mm-format-report',html)
        self.assertIn('Print / Save PDF',html)
        self.assertNotIn('window.onload=()=>setTimeout(()=>window.print()',html)
        self.assertEqual(html.count('class="mm-format-chart"'),2)

    def test_nadi_reference_panels_are_available_in_customer_interface(self):
        self.go('nadi-astrology')
        expect(self.page.locator('#na-cusp-table tbody tr')).to_have_count(12)
        expect(self.page.locator('#na-reference-planet-table tbody tr')).to_have_count(9)
        expect(self.page.locator('#na-reference-rp tbody tr')).to_have_count(4)
        expect(self.page.locator('#na-reference-dasha table tbody tr')).to_have_count(9)
        self.page.locator('#na-source').select_option('moment')
        self.page.wait_for_timeout(700)
        self.page.locator('#na-update').click()
        self.page.wait_for_timeout(700)
        expect(self.page.locator('#na-native-chart [data-nadi-source="moment"]')).to_be_visible()
        self.assertFalse(self.page.locator('#connection-status').count())

    def test_home_chart_context_menu_changes_style(self):
        chart=self.page.locator('#home [data-home-chart]')
        chart.click(button='right')
        expect(self.page.locator('#kundali-style-menu')).to_be_visible(timeout=10000)
        self.page.locator('#kundali-style-menu button[data-kundali-style="north"]').click()
        expect(self.page.locator('#home [data-home-chart]')).to_have_class(__import__('re').compile('.*north9-chart.*'),timeout=10000)
        self.assertFalse(self.page.locator('#connection-status').count())

    def test_csv_download_reaches_customer_browser(self):
        self.go('ephemeris')
        self.private("() => {document.getElementById('eph-start').value='2026-10-06';document.getElementById('eph-end').value='2026-10-07';document.getElementById('eph-run').click();}")
        snapshot=self.page.request.get(self.url+'/snapshot').json()
        self.page.reload();expect(self.page.locator('#eph-csv')).to_be_enabled(timeout=15000)
        with self.page.expect_download(timeout=15000) as download:
            self.page.locator('#eph-csv').click()
        data=download.value
        self.assertTrue(data.suggested_filename.endswith('.csv'))
        text=Path(data.path()).read_text(encoding='utf-8-sig')
        self.assertIn('2026-10-06',text);self.assertIn('2026-10-07',text)

    def test_sessions_do_not_share_native_data(self):
        self.go('basic');self.page.locator('#name').fill('Only first session');self.page.locator('#name').blur();self.page.wait_for_timeout(700)
        other=self.browser.new_context();page=other.new_page();page.goto(self.url)
        expect(page.locator('#page-title')).to_have_text('Home',timeout=30000)
        snapshot=page.request.get(self.url+'/snapshot').json();self.assertNotEqual(snapshot['token'],self.token)
        self.assertNotEqual(page.locator('#name').input_value(),'Only first session')
        token=snapshot['token'];other.close()
        self.engine.executor.submit(lambda:self.engine.sessions.pop(token)['context'].close()).result()

if __name__=='__main__':unittest.main()
