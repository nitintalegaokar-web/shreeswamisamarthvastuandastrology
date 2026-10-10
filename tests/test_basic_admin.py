"""Native Basic Information reports and local administrator worksheet access."""
import json,unittest
import fitz
from playwright.sync_api import expect
import test_personal_predictions as personal
import test_protected_server as protected
class BasicAdminTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def test_native_basic_information_matches_general_report_and_a4(self):
  p=self.page;p.wait_for_selector('#admin-pin-form',state='attached');p.locator('#quick-basic-information').click();expect(p.locator('#basic-information-data')).to_contain_text('Sunrise')
  facts=p.evaluate('KPBasicInformation.facts()');self.assertTrue(facts['ready']);values=dict(row for group in facts['groups'] for row in group)
  self.assertEqual(values['Name'],p.locator('#name').input_value());self.assertEqual(values['Birth time'],p.locator('#birthTime').input_value());self.assertEqual(values['Longitude'],p.evaluate('KPClientPresentation.formatCoordinate(KPVedic.core().native.location.longitude,true)'));self.assertEqual(values['Pada'],p.evaluate('KPDisplay.longitudeDetails(currentKPModel.planets.find(p=>p.id==="Mo").longitude).pada'))
  self.assertEqual(values['Star lord'],p.evaluate('KPSinglePageReport.panchang(currentKPModel.planets.find(p=>p.id==="Su").longitude,currentKPModel.planets.find(p=>p.id==="Mo").longitude,document.getElementById("dob").value).nakLord'))
  native=p.evaluate('JSON.stringify(currentKPModel)');screen=p.locator('#basic-information-data .bi-facts').inner_text()
  with p.expect_popup() as opened:p.locator('#basic-information-preview').click()
  w=opened.value;expect(w.locator('.bi-facts')).to_be_visible();self.assertEqual(w.locator('.bi-facts').inner_text(),screen);self.assertEqual(w.locator('.v-report-page').count(),1)
  w.emulate_media(media='print');pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');self.assertEqual(len(pdf),1);self.assertIn('General information',pdf[0].get_text());self.assertIn(values['Name'],pdf[0].get_text())
  for b in pdf[0].get_text('blocks'):self.assertGreaterEqual(b[0],35);self.assertLessEqual(b[2],560)
  pdf.close();w.close();self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),native)
  p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})');expect(p.locator('#basic-information-data')).to_contain_text('गण');expect(p.locator('#page-title')).to_have_text('मूलभूत तपशील');expect(p.locator('#basic-information-data')).not_to_contain_text('years');p.screenshot(path='/tmp/basic-information-final.png')
 def test_pin_gates_six_worksheets_persists_and_stays_out_of_chart_files(self):
  p=self.page;p.wait_for_selector('#admin-pin-form',state='attached')
  for id in ['ayan','lmt','stcalc','raphael5','planet']:
   expect(p.locator('#quick-'+id)).to_be_hidden();expect(p.locator('.app-sidebar [data-tab="'+id+'"]').first).to_be_hidden();expect(p.locator('#'+id)).to_be_hidden()
  self.assertFalse(p.evaluate('KPAdminCalculations.select("planet")'));self.assertNotIn('calculationDetails',p.evaluate('KPDbaPopup.data()'));self.assertNotIn('id="dba-calculations"',p.evaluate('KPDbaPopup.document()'))
  self.assertEqual(p.locator('#report-page-options [data-report-page-key="mdcalc"],#report-page-options [data-report-page-key="planet"]').count(),0)
  p.locator('#quick-admin-calculations').click();p.locator('[name="admin-pin"]').fill('638294');p.locator('[name="admin-confirm"]').fill('111111');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-pin-status')).to_contain_text('do not match');self.assertFalse(p.evaluate('KPAdminCalculations.isUnlocked()'))
  p.locator('[name="admin-confirm"]').fill('638294');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible();saved=p.evaluate('localStorage.getItem("kpAdministratorPinV1")');self.assertNotIn('638294',saved);self.assertEqual(len(json.loads(saved)['hash']),64)
  for id in ['ayan','lmt','stcalc','raphael5','planet','mdcalc']:
   p.locator('[data-admin-worksheet="'+id+'"]').click();expect(p.locator('#'+id)).to_be_visible()
  expect(p.locator('#dba-worksheet-calculations')).to_have_attribute('open','');self.assertNotIn('638294',p.evaluate('JSON.stringify(getChartData())'))
  self.assertEqual(p.locator('#report-page-options [data-report-page-key="mdcalc"]').count(),1)
  p.locator('#quick-basic').click();self.assertFalse(p.evaluate('KPAdminCalculations.isUnlocked()'));expect(p.locator('#admin-calculation-host')).to_be_hidden()
  p.reload();p.wait_for_selector('#admin-pin-form',state='attached');p.locator('#quick-admin-calculations').click();expect(p.locator('#admin-pin-confirm-row')).to_be_hidden();p.locator('[name="admin-pin"]').fill('000000');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-pin-status')).to_contain_text('Incorrect');expect(p.locator('#admin-calculation-host')).to_be_hidden()
  p.locator('[name="admin-pin"]').fill('638294');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible();p.locator('#admin-pin-lock').click();expect(p.locator('#admin-calculation-host')).to_be_hidden()
class BasicPrivateTests(unittest.TestCase):
 setUpClass=classmethod(protected.ProtectedServerTests.setUpClass.__func__);tearDownClass=classmethod(protected.ProtectedServerTests.tearDownClass.__func__);setUp=protected.ProtectedServerTests.setUp;tearDown=protected.ProtectedServerTests.tearDown;post=protected.ProtectedServerTests.post;go=protected.ProtectedServerTests.go;private=protected.ProtectedServerTests.private
 def test_public_basic_facts_and_report_without_private_worksheets(self):
  p=self.page;self.go('basic-information');expect(p.locator('#basic-information-data')).to_contain_text('Nakshatra');self.assertEqual(p.evaluate('typeof KPBasicInformation'),'undefined');expect(p.locator('#quick-admin-calculations')).to_be_hidden()
  with p.expect_popup() as opened:p.locator('#basic-information-preview').click()
  w=opened.value;expect(w.locator('.bi-facts')).to_be_visible(timeout=30000);self.assertNotIn('PBKDF2',w.content());self.assertNotIn('md-formula-row',w.locator('body').inner_html());pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');self.assertEqual(len(pdf),1);pdf.close();w.close()
