"""Detailed South calculation views and current-time ruling planets."""
import unittest
import test_personal_predictions as public_fixture
import test_protected_server as private_fixture
from playwright.sync_api import expect

class LiveWorkspaceTests(unittest.TestCase):
    setUpClass=classmethod(public_fixture.PersonalPredictionTests.setUpClass.__func__)
    tearDownClass=classmethod(public_fixture.PersonalPredictionTests.tearDownClass.__func__)
    setUp=public_fixture.PersonalPredictionTests.setUp
    tearDown=public_fixture.PersonalPredictionTests.tearDown

    def test_detailed_south_tables_and_all_methods_preserve_native_chart(self):
        self.page.locator('#quick-south9').click()
        expect(self.page.locator('[data-south-method]')).to_have_count(5)
        tables=self.page.locator('#south-position-tables table')
        self.assertEqual(tables.nth(0).locator('thead th').all_text_contents(),['Pln','Sign','Deg','Nak','Occ','Own','SgL','StL','SL','SSL','CSL','CStL','Aspd','Aspg','Conj'])
        expect(tables.nth(0).locator('tbody tr')).to_have_count(9);expect(tables.nth(1).locator('tbody tr')).to_have_count(12)
        native=self.page.evaluate('JSON.stringify(currentKPModel)')
        for method in ['fourfold','sixfold']:
            self.page.locator('[data-south-method="'+method+'"]').click();expect(self.page.locator('#south-position-tables table')).to_have_count(2);expect(self.page.locator('#south-calculation-body')).to_contain_text('significators')
        self.page.locator('[data-south-method="fourstep"]').click();expect(self.page.locator('#south-position-tables .kp-step-card')).to_have_count(9);expect(self.page.locator('#south-position-tables')).to_contain_text('Aspd:')
        self.page.locator('[data-south-method="nadi"]').click();expect(self.page.locator('#south-position-tables .na-tile')).to_have_count(9)
        self.page.locator('[data-south-method="basic"]').click();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native);self.assertEqual(self.page.evaluate('KPHomeDashboard.getView()'),'basic')
        self.assertEqual(self.page.evaluate("document.querySelectorAll('#south-position-tables #kp-basic-planet,#south-position-tables [data-bridge-id]').length"),0)
        bounds=self.page.locator('#kundali').evaluate('n=>({chart:n.getBoundingClientRect().width,parent:n.parentElement.getBoundingClientRect().width})');self.assertLessEqual(bounds['chart'],bounds['parent']+1)
        self.page.screenshot(path='/tmp/kp-south-detailed-final.png',full_page=True)
        self.page.set_viewport_size({'width':390,'height':900});self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)

    def test_live_clock_and_positions_change_across_tabs_without_native_mutations(self):
        self.page.wait_for_function('KPLiveRuling.getData()?.ready');native=self.page.evaluate('JSON.stringify(currentKPModel)');first=self.page.locator('#kp-live-ruling').get_attribute('data-utc')
        self.page.locator('#quick-south9').click();expect(self.page.locator('#kp-live-ruling')).to_be_visible();self.page.wait_for_function('(utc)=>document.getElementById("kp-live-ruling").dataset.utc!==utc',arg=first)
        self.page.locator('#quick-notepad').click();self.page.locator('#notepad-text').fill('Explain the current ruling planets');self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native);self.page.locator('#notepad-close').click()
        self.page.locator('#kp-live-ruling summary').click();expect(self.page.locator('#live-rp-rows tr')).to_have_count(2);expect(self.page.locator('#live-rp-convention')).to_contain_text('local sunrise');self.page.locator('#live-rp-settings').click();expect(self.page.locator('#setting-astroPlace')).to_be_visible()
        self.page.locator('#quick-home').click();expect(self.page.locator('#kp-live-ruling')).to_be_visible();self.assertEqual(self.page.evaluate('JSON.stringify(currentKPModel)'),native)

    def test_ruling_calculation_matches_current_longitudes_and_sunrise_hour_boundaries(self):
        data=self.page.evaluate("""()=>{const loc={place:'Pune',latitude:18.52,longitude:73.85,timezone:5.5},date=new Date('2026-10-10T06:30:00Z'),r=KPLiveRuling.calculate(date,loc),before=KPLiveRuling.calculate(new Date(Date.parse(r.sunrise)-1000),loc),after=KPLiveRuling.calculate(new Date(Date.parse(r.sunrise)+1000),loc),edge=KPLiveRuling.calculate(new Date(Date.parse(r.hourEnd)+1000),loc);return {r,before,after,edge,ascendant:KPTransitHouses.ascendant(date,loc.latitude,loc.longitude)*3600,moon:KPEphemeris.longitude(date,'Mo')*3600};}""")
        r=data['r'];self.assertAlmostEqual(r['points'][0]['longitude'],data['ascendant'],places=6);self.assertAlmostEqual(r['points'][1]['longitude'],data['moon'],places=6);self.assertEqual(r['dayLord'],'Sa');self.assertEqual(data['before']['dayLord'],'Ve');self.assertEqual(data['after']['dayLord'],'Sa');self.assertEqual(data['after']['hourLord'],'Sa');self.assertEqual(data['after']['hourNumber'],1);self.assertEqual(data['edge']['hourNumber'],r['hourNumber']+1);self.assertNotEqual(data['edge']['hourLord'],r['hourLord']);self.assertEqual(r['local'],'2026-10-10T12:00:00');self.assertEqual(set(r['rulingPlanets']),{s['planet'] for s in r['sources']})
        shifted=self.page.evaluate("""()=>{const a=KPLiveRuling.calculate('2026-10-10T06:30:00Z',{place:'Pune',latitude:18.52,longitude:73.85,timezone:5.5}),b=KPLiveRuling.calculate('2026-10-10T06:30:00Z',{place:'Pune UTC display',latitude:18.52,longitude:73.85,timezone:0});return {a:a.points,b:b.points,local:b.local};}""");self.assertEqual(shifted['a'],shifted['b']);self.assertEqual(shifted['local'],'2026-10-10T06:30:00')

    def test_polar_day_does_not_fabricate_ruling_day_or_hour(self):
        result=self.page.evaluate("""()=>{const r=KPLiveRuling.calculate('2026-06-21T12:00:00Z',{place:'Polar',latitude:80,longitude:0,timezone:0});let invalid='';try{KPLiveRuling.calculate('2026-10-10T06:30:00Z',{place:'Invalid',latitude:'',longitude:0,timezone:0});}catch(e){invalid=e.message;}return {r,invalid};}""");self.assertIsNone(result['r']['dayLord']);self.assertIsNone(result['r']['hourLord']);self.assertIn('sunrise',result['r']['reason']);self.assertIn('coordinates',result['invalid'])

class ProtectedLiveWorkspaceTests(unittest.TestCase):
    setUpClass=classmethod(private_fixture.ProtectedServerTests.setUpClass.__func__)
    tearDownClass=classmethod(private_fixture.ProtectedServerTests.tearDownClass.__func__)
    setUp=private_fixture.ProtectedServerTests.setUp
    tearDown=private_fixture.ProtectedServerTests.tearDown
    private=private_fixture.ProtectedServerTests.private

    def test_live_private_data_polls_without_replacing_the_native_chart(self):
        self.page.locator('#quick-south9').click();expect(self.page.locator('[data-south-method]')).to_have_count(5,timeout=30000);self.page.locator('[data-south-method="sixfold"]').click();expect(self.page.locator('#south-calculation-body')).to_contain_text('Six-fold significators',timeout=30000)
        native=self.private('JSON.stringify(currentKPModel)');first=self.page.locator('#kp-live-ruling').get_attribute('data-utc');self.page.wait_for_function('(utc)=>document.getElementById("kp-live-ruling").dataset.utc!==utc',arg=first,timeout=15000);self.assertEqual(native,self.private('JSON.stringify(currentKPModel)'))
        response=self.page.request.get(self.url+'/live-ruling-planets');self.assertEqual(response.status,200);packet=response.json();self.assertTrue(packet['data']['ready']);self.assertEqual(len(packet['data']['points']),2);self.assertNotIn('function calculate',response.text());self.assertEqual(self.page.request.get(self.url+'/ruling-clock').status,404)
        self.page.locator('#kp-live-ruling summary').click();expect(self.page.locator('#live-rp-rows tr')).to_have_count(2);self.page.wait_for_timeout(2200);self.assertTrue(self.page.locator('#kp-live-ruling').evaluate('n=>n.open'));self.assertEqual(native,self.private('JSON.stringify(currentKPModel)'))
        self.page.locator('#quick-notepad').click();self.page.locator('#notepad-text').fill('Live RP stays active during a consultation');self.page.locator('#notepad-close').click();self.assertEqual(native,self.private('JSON.stringify(currentKPModel)'))
        self.assertTrue(self.private('document.getElementById("kp-live-ruling").open'));self.page.locator('#live-rp-settings').click();expect(self.page.locator('#setting-astroPlace')).to_be_visible(timeout=30000)
