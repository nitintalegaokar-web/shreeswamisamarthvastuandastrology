"""Owner's latest reference image: half-minute rounding and final cusp subtraction."""
import json,subprocess,unittest
from pathlib import Path
import test_personal_predictions as personal
ROOT=Path(__file__).resolve().parents[1]
class IshtaThresholdTests(unittest.TestCase):
 def test_owner_examples_and_exact_threshold(self):
  seconds=[45*60+19,43*60+49,45*60+50,45*60+59,29.999,30,0,3600,-30,-29]
  script="const api=require('./vendor/houses/ishta-rounding.js');console.log(JSON.stringify(JSON.parse(process.argv[1]).map(api.roundArcseconds)));"
  result=json.loads(subprocess.check_output(['node','-e',script,json.dumps(seconds)],cwd=ROOT))
  self.assertEqual(result,[45,44,46,46,0,1,0,60,-1,0])
class IshtaWorksheetTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_confirmed_13_north_st_141347_rounds_cusps_and_keeps_source_rows(self):
  p=self.page
  result=p.evaluate('''()=>{const d=KPBhavSadhan.lookup(13,14*3600+13*60+47,24);return {minutes:d.ishtaMinutes,small:d.brackets.small,large:d.brackets.large,cusps:d.cusps,tropical:d.tropicalCusps};}''')
  self.assertEqual(result['minutes'],[45,45,45,44,45,45])
  self.assertEqual(result['small'][5],3);self.assertEqual(result['large'][5],4)
  for house,value in [(10,215.75),(11,243.75),(12,269.75),(1,295+39/60+44/60),(2,329.75),(3,3.75)]:
   self.assertAlmostEqual(result['tropical'][house-1],value,places=10)
   self.assertAlmostEqual(result['cusps'][house-1],(value-24)%360,places=10)
   self.assertAlmostEqual((result['cusps'][(house+5)%12]-result['cusps'][house-1])%360,180,places=10)
  p.evaluate('''()=>{const values={'instant-prashna':'0','chart-kind':'natal','dob':'1931-10-10','birthTime':'05:02:00','lat':'13:00:00','lon':'80:15:00','birth-utc-offset':'5.5','stdLon':'82:30:00'};for(const [id,v] of Object.entries(values))document.getElementById(id).value=v;calculateAll();}''')
  p.locator('#quick-admin-calculations').click();p.locator('[name=admin-pin]').fill('684219');p.locator('[name=admin-confirm]').fill('684219');p.locator('#admin-pin-submit').click()
  p.evaluate('''()=>{document.getElementById('st-ephemeris-source').value='manual';document.getElementById('birthPlaceSiderealTime').value='14:13:47';updateRaphaelTable5();syncKPWorksheetPositions();}''')
  snapshot=p.evaluate('''()=>({d:KPBhavSadhan.getData(),display:[10,11,12,1,2,3].map(h=>[document.getElementById('r5_ishta_'+h).value,document.getElementById('r5_calc_ishta_'+h).value]),rows:[10,11,12,1,2,3].map(h=>['smallplus','geoayan','nirayan','bhava'].map(f=>document.getElementById('r5_'+f+'_'+h).value)),planets:currentKPModel.planets.map(p=>p.longitude)})''')
  self.assertEqual(snapshot['display'],[['0:45:00','45']]*3+[['0:44:00','44']]+[['0:45:00','45']]*2)
  self.assertEqual(snapshot['d']['ishtaRounding'],'minutes-half-up')
  self.assertEqual(snapshot['rows'],[
   ['215:45:00','22:48:18','192:56:42','12:56:42'],
   ['243:45:00','22:48:18','220:56:42','10:56:42'],
   ['269:45:00','22:48:18','246:56:42','6:56:42'],
   ['296:23:00','22:48:18','273:34:42','3:34:42'],
   ['329:45:00','22:48:18','306:56:42','6:56:42'],
   ['3:45:00','22:48:18','340:56:42','10:56:42']])
  p.evaluate('updateRaphaelTable5();syncKPWorksheetPositions()')
  self.assertEqual(p.evaluate('KPBhavSadhan.getData().cusps'),snapshot['d']['cusps'])
if __name__=='__main__':unittest.main()
