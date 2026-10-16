"""Menu routing, below-chart controls and dark-mode contrast without formula changes."""
import unittest,fitz
import test_personal_predictions as personal
from test_calculation_protection import CalculationProtectionTests as Calc
class CompactNavigationTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_menu_groups_routes_shortcuts_and_control_placement(self):
  p=self.page;p.wait_for_selector('#kp-compact-navigation');self.assertEqual(p.locator('.kp-main-menu>button,.kp-main-menu>details').count(),11);self.assertEqual(p.locator('.kp-small-shortcuts>button').count(),9)
  p.locator('.kp-main-menu>details').filter(has=p.locator('summary',has_text='View')).locator('summary').click();p.locator('.kp-menu-options [data-kp-menu-action="transit-chart"]').click();self.assertIn('active',p.locator('#transit-chart').get_attribute('class'))
  p.locator('.kp-main-menu>[data-kp-menu-action="south9"]').click();d=p.evaluate('''()=>({below:!!(document.getElementById('kundali-north').compareDocumentPosition(document.querySelector('#south9 .kundali-toolbar'))&Node.DOCUMENT_POSITION_FOLLOWING),extra:document.querySelectorAll('.kp-chart-readable').length,asc:!!document.querySelector('#south9 .kundali-toolbar #kp-asc-moon-tool'),home:document.querySelectorAll('#kp-home-chart-controls [data-lord-control="home"]').length})''');self.assertTrue(d['below']);self.assertTrue(d['asc']);self.assertEqual(d['extra'],0);self.assertEqual(d['home'],1)
  p.locator('.kp-shortcut-toggle').click();self.assertTrue(p.locator('.kp-small-shortcuts').is_hidden());p.locator('.kp-shortcut-toggle').click();self.assertTrue(p.locator('.kp-small-shortcuts').is_visible())
 def test_dark_mode_tables_chart_and_menu_remain_readable(self):
  p=self.page;p.wait_for_selector('#kp-compact-navigation');before=p.evaluate('JSON.stringify(currentKPModel)');p.evaluate("KPPreferences.save({...KPPreferences.get(),themeType:'dark'})");p.wait_for_function("document.body.dataset.kpThemeType==='dark'")
  d=p.evaluate('''()=>{const c=s=>{const n=document.querySelector(s),v=getComputedStyle(n);return {background:v.backgroundColor,color:v.color};};return {cell:c('#home #home-planets td'),name:c('#home-kundali .v38-name'),label:c('#home-kundali .v38-position'),menu:c('#kp-compact-navigation')};}''');self.assertEqual(d['cell']['background'],'rgb(32, 55, 75)');self.assertNotEqual(d['cell']['background'],d['cell']['color']);self.assertIn(d['label']['background'],['rgba(0, 0, 0, 0)','transparent']);self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),before)
  p.screenshot(path='/tmp/kp-dark-compact-navigation.png',full_page=False)
 def test_panchang_summary_is_not_repeated_in_screen_or_print(self):
  p=self.page;p.wait_for_function('window.KPPanchangSingleSummary');p.evaluate("KPCompactNavigation.activate('transit-panchang');document.getElementById('tp-calculate').click()");p.wait_for_selector('#tp-daily-extension .tp-dinvisesh');self.assertTrue(p.locator('#tp-summary').is_hidden());self.assertEqual(p.locator('#tp-daily-extension .tp-summary-extras .almanac-value').count(),2);html=p.evaluate('KPTransitPanchang.snapshot()');self.assertNotIn('<dl class="almanac-grid">',html);self.assertEqual(html.count('class="tp-dinvisesh"'),1)
  p.evaluate('renderReport()');self.assertEqual(p.locator('#printReport [data-report-section="transit-panchang"] .tp-dinvisesh').count(),1)
 def test_approved_calculation_reference_after_new_navigation(self):
  p=self.page;p.wait_for_selector('#kp-compact-navigation');p.evaluate('''fields=>{for(const [id,value] of Object.entries(fields))document.getElementById(id).value=value;document.getElementById('lon').value='76:42:00';calculateAll();}''',Calc.FIELDS);baseline=p.evaluate(Calc.SNAPSHOT);self.assertEqual(baseline['siderealTime'],'10:30:45')
  for route in ['south9','aspects','karyesh','basic-information','home']:
   p.evaluate('(id)=>KPCompactNavigation.activate(id)',route);self.assertEqual(p.evaluate(Calc.SNAPSHOT),baseline)
  p.evaluate("KPPreferences.save({...KPPreferences.get(),themeType:'dark'});calculateAll()");self.assertEqual(p.evaluate(Calc.SNAPSHOT),baseline)
if __name__=='__main__':unittest.main()
