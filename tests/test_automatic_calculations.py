"""Saved native charts recalculate from automatic ephemeris and house sources."""
import json,unittest
from playwright.sync_api import expect
import test_personal_predictions as personal
class AutomaticCalculationTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def test_fixed_birth_chart_reload_and_legacy_rows_are_deterministic(self):
  p=self.page;p.wait_for_function('typeof KPAutomaticCalculations!=="undefined"');p.wait_for_timeout(200)
  p.evaluate('''()=>{for(const [id,value] of Object.entries({'instant-prashna':'0','name':'Fixed native','dob':'1986-07-15','birthTime':'13:11:00','lat':'18:48:00','lon':'74:13:00','birth-utc-offset':'5.5','stdLon':'82:30:00'}))document.getElementById(id).value=value;calculateAll();}''')
  sample='()=>({ready:currentKPModel.ready,planets:currentKPModel.planets.map(p=>p.longitude),cusps:currentKPModel.houses.map(p=>p.longitude),source:KPBhavSadhan.getData().source,ephemeris:KPWorksheetEphemeris.getData(),ayan:document.getElementById("ayanValue").value})'
  for h in [10,11,12,2,3]:
   self.assertNotIn(':',p.locator(f'#r5_small_{h}').input_value());self.assertEqual(p.locator(f'#r5_small_{h}').get_attribute('data-house-table-unit'),'degrees')
  self.assertRegex(p.locator('#r5_small_1').input_value(),r'^\d+:\d{2}$');self.assertEqual(p.locator('#r5_small_1').get_attribute('data-house-table-unit'),'DM')
  original=p.evaluate(sample);self.assertTrue(original['ready']);self.assertEqual(original['source'],'uploaded');self.assertTrue(original['ephemeris']['ready'])
  saved=p.evaluate('getChartData()');self.assertEqual(saved['fields']['p6-ephemeris-source']['value'],'automatic');self.assertEqual(saved['fields']['r5-house-source']['value'],'automatic')
  for _ in range(3):p.evaluate('calculateAll()');self.assertEqual(p.evaluate(sample),original)
  p.reload(timeout=120000);p.wait_for_function('typeof KPAutomaticCalculations!=="undefined"');p.evaluate('chart=>restoreChartData(chart)',saved);p.wait_for_timeout(400);self.assertEqual(p.evaluate(sample),original)
  legacy=json.loads(json.dumps(saved))
  for id in ['p6-ephemeris-source','st-ephemeris-source','r5-house-source','kp-ayanamsha-source']:legacy['fields'].pop(id,None)
  for id in ['p6_row_date_1','p6_row_date_2']:legacy['fields'][id]={'value':'2000-01-01','auto':'0'}
  for id in ['p6_d_0','p6_t_0','r5_nirayan_1','ayanValue']:legacy['fields'][id]={'value':'01:02:03'}
  p.evaluate('chart=>restoreChartData(chart)',legacy);p.wait_for_timeout(400);self.assertEqual(p.evaluate(sample),original)
  p.evaluate('document.getElementById("birthTime").value="14:11:00";calculateAll()');changed=p.evaluate(sample);self.assertNotEqual(changed['cusps'],original['cusps']);self.assertNotEqual(changed['planets'],original['planets']);self.assertEqual(changed['ephemeris']['dates'],['1986-07-15','1986-07-16'])
  p.evaluate('document.getElementById("birthTime").value="13:11:00";calculateAll()');self.assertEqual(p.evaluate(sample),original)
if __name__=='__main__':unittest.main()
