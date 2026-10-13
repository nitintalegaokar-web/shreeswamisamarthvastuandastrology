"""Native 05:30 interpolation, coherent ST and explicit administrator manual saves."""
import math,json,unittest
from fractions import Fraction
from datetime import datetime,timezone
from playwright.sync_api import expect
import test_personal_predictions as personal
class NativeWorksheetTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def configure(self,**overrides):
  self.page.wait_for_function('typeof KPAutomaticCalculations!=="undefined"&&typeof KPWorksheetEphemeris.siderealCalculation==="function"')
  fields={'instant-prashna':'0','chart-kind':'natal','dob':'1950-12-20','birthTime':'05:02:00','lat':'10:46:00','lon':'76:42:00','birth-utc-offset':'5.5','birth-dst-minutes':'0','stdLon':'82:30:00',**overrides}
  self.page.evaluate('fields=>{for(const [id,value] of Object.entries(fields))document.getElementById(id).value=value;calculateAll()}',fields)
 def test_st_has_one_result_across_worksheet_house_and_repeated_calculation(self):
  p=self.page
  for lon,expected in [('76:42:00','10:30:46'),('89:10:00','11:20:38')]:
   self.configure(lon=lon)
   sample='()=>({st:document.getElementById("birthPlaceSiderealTime").value,house:KPBhavSadhan.getData().siderealSeconds,display:Object.fromEntries(["baseSidereal0530","stLmtDifference","stTenSixCorrection","stGrandTotal","st24Adjustment"].map(id=>[id,document.getElementById(id).value])),cusps:currentKPModel.houses.map(h=>h.longitude),planets:currentKPModel.planets.map(p=>p.longitude)})'
   original=p.evaluate(sample);self.assertEqual(original['st'],expected)
   self.assertEqual(p.evaluate('KPBhavSadhan.getData().tableLatitude'),11)
   # Independent Julian-date GMST difference checks the astronomical rotation.
   ref=p.evaluate('KPWorksheetEphemeris.getSidereal()');moment=p.evaluate('()=>{const m=KPHorary.nativeMoment();return {date:m.date.toISOString(),longitude:m.longitude}}')
   def gmst(stamp):
    days=(datetime.fromisoformat(stamp.replace('Z','+00:00'))-datetime(2000,1,1,12,tzinfo=timezone.utc)).total_seconds()/86400;t=days/36525
    return (280.46061837+360.98564736629*days+.000387933*t*t-t*t*t/38710000)%360
   reference=(ref['hours']*3600+(gmst(moment['date'])-gmst(ref['utc']))*240+(moment['longitude']-ref['offset']*15)*240)%86400
   self.assertLess(abs((original['house']-reference+43200)%86400-43200),.05)
   def seconds(text):
    nums=text.lstrip('-+ ').split(':');return (-1 if text.startswith('-') else 1)*sum(int(x)*m for x,m in zip(nums,[3600,60,1]))
   d=original['display'];self.assertEqual(seconds(d['stGrandTotal']),sum(seconds(d[k]) for k in ['baseSidereal0530','stLmtDifference','stTenSixCorrection']))
   self.assertEqual(seconds(d['stGrandTotal'])+seconds(d['st24Adjustment']),seconds(original['st']))
   for call in ['updateSiderealTimeCalculation()','calculateAll()','updateTab4SampattikKaal();updateRaphaelTable5()']:
    p.evaluate(call);self.assertEqual(p.evaluate(sample),original)
   saved=p.evaluate('getChartData()');p.reload(timeout=120000);p.wait_for_function('typeof KPAutomaticCalculations!=="undefined"');p.evaluate('x=>restoreChartData(x)',saved);p.wait_for_timeout(1300);self.assertEqual(p.evaluate(sample),original)
 def test_planets_use_the_requested_0530_boundary_and_signed_daily_motion(self):
  p=self.page
  for time,before in [('00:00:00',True),('05:02:00',True),('05:29:59',True),('05:30:00',False),('23:59:59',False)]:
   self.configure(birthTime=time)
   row=p.evaluate('()=>({data:KPWorksheetEphemeris.getData(),positions:currentKPModel.planets.map(p=>[p.id,p.longitude]),values:Object.fromEntries(["p6_row_date_1","p6_row_date_2","p6_add_0","p6_total_0"].map(id=>[id,document.getElementById(id).value]))})')
   self.assertEqual(row['data']['dates'],['1950-12-19','1950-12-20'] if before else ['1950-12-20','1950-12-21'])
   bt=sum(int(n)*d for n,d in zip(time.split(':'),[3600,60,1]));elapsed=bt-19800
   rows=row['data']['rows'];base=rows[1 if before else 0]['positions']
   for planet,actual in row['positions']:
    if planet=='Ke':continue
    first=math.floor(rows[0]['positions'][planet]*3600+.5);second=math.floor(rows[1]['positions'][planet]*3600+.5)
    daily=(second-first+648000)%1296000-648000
    correction=Fraction(daily*elapsed,86400);rounded=(1 if correction>=0 else -1)*((2*abs(correction.numerator)+correction.denominator)//(2*correction.denominator))
    expected=(math.floor(base[planet]*3600+.5)+rounded)%1296000
    self.assertEqual(actual,expected)
   if time=='05:02:00':self.assertEqual(row['values']['p6_add_0'],'244:26:48');self.assertEqual(row['values']['p6_total_0'],'-0:01:12')
   p.evaluate('document.getElementById("p6_row_date_1").value="2001-05-20";document.getElementById("p6_row_date_1").dataset.auto="0";calculateAll()')
   self.assertEqual(p.evaluate('KPWorksheetEphemeris.getData().dates'),row['data']['dates'])
 def test_legacy_restore_cannot_leave_stuck_manual_st_and_clear_button_is_persistent(self):
  p=self.page;self.configure(dob='2001-05-21',birthTime='01:01:00',lon='74:07:00')
  automatic=p.evaluate('getChartData()')
  p.locator('#quick-admin-calculations').click();p.locator('[name=admin-pin]').fill('684219');p.locator('[name=admin-confirm]').fill('684219');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible()
  # Legacy files have worksheet values but no explicit Save-manual record or source selectors.
  legacy=json.loads(json.dumps(automatic));legacy.pop('manualCalculations',None)
  for id in ('p6-ephemeris-source','st-ephemeris-source','r5-house-source','kp-ayanamsha-source'):legacy['fields'].pop(id,None)
  legacy['fields']['baseSidereal0530']['value']='21:20:52'
  p.evaluate('(chart)=>restoreChartData(chart)',legacy)
  self.assertEqual(p.evaluate("()=>['p6-ephemeris-source','st-ephemeris-source','r5-house-source','kp-ayanamsha-source'].map(id=>document.getElementById(id).value)"),['automatic','automatic','automatic','annual'])
  self.assertIsNotNone(p.evaluate('KPWorksheetEphemeris.getSidereal()'))
  self.assertEqual(p.locator('#birthPlaceSiderealTime').input_value(),'16:21:32')
  expect(p.locator('#admin-calculation-source-state')).to_contain_text('Automatic ephemeris')
  # Reproduce the reported manual 10/6 worksheet exactly, then save it explicitly.
  p.locator('[data-admin-worksheet="stcalc"]').click();p.locator('#st-ephemeris-source').select_option('manual');p.locator('#baseSidereal0530').fill('21:20:52');p.evaluate('updateSiderealTimeCalculation();updateRaphaelTable5()')
  self.assertEqual(p.evaluate("()=>Object.fromEntries(['lmtFinal','stLmtDifference','stTenSixCorrection','stGrandTotal','st24Adjustment','birthPlaceSiderealTime'].map(id=>[id,document.getElementById(id).value]))"),{'lmtFinal':'00:27:28','stLmtDifference':'18:57:28','stTenSixCorrection':'00:03:10','stGrandTotal':'40:21:30','st24Adjustment':'- 24:00:00','birthPlaceSiderealTime':'16:21:30'})
  p.evaluate('''()=>{const record=KPAutomaticCalculations.capture();KPAutomaticCalculations.setSaved(record);KPAutomaticCalculations.persist();}''')
  manual=p.evaluate('getChartData()');self.assertIn('manualCalculations',manual)
  p.evaluate('(chart)=>restoreChartData(chart)',manual);self.assertEqual(p.locator('#st-ephemeris-source').input_value(),'manual')
  expect(p.locator('#admin-use-automatic')).to_be_visible();expect(p.locator('#admin-calculation-source-state')).to_contain_text('Manual 10/6')
  expect(p.locator('#st-subtotal-explanation')).to_contain_text('Subtotal 40:21:30');expect(p.locator('#st-subtotal-explanation')).to_contain_text('Final sidereal time: 16:21:30')
  p.locator('#admin-use-automatic').click();self.assertIsNone(p.evaluate('KPAutomaticCalculations.getSaved()'));self.assertEqual(p.locator('#st-ephemeris-source').input_value(),'automatic');expect(p.locator('#admin-use-automatic')).to_be_hidden()
  p.locator('#admin-pin-lock').click();p.evaluate('calculateAll()');self.assertEqual(p.locator('#st-ephemeris-source').input_value(),'automatic');self.assertEqual(p.locator('#birthPlaceSiderealTime').input_value(),'16:21:32')
 def test_manual_save_cancel_and_reload_do_not_override_another_birth_chart(self):
  p=self.page;self.configure();p.locator('#quick-admin-calculations').click();p.locator('[name=admin-pin]').fill('684219');p.locator('[name=admin-confirm]').fill('684219');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible();expect(p.locator('#admin-save-manual')).to_be_hidden()
  p.locator('[data-admin-worksheet=planet]').click();p.locator('#p6-ephemeris-source').select_option('manual');expect(p.locator('#admin-save-manual')).to_be_visible()
  p.locator('#p6_d_0').fill('243:00:00');p.locator('#p6_t_0').fill('244:00:00');p.wait_for_timeout(250)
  p.evaluate('''()=>{window.testSaved=null;window.KPChartFiles={directory:async()=>null,save:async chart=>{window.testSaved=chart;return 'Saved manual.lkp'}}}''')
  p.locator('#admin-save-manual').click();expect(p.locator('#admin-save-status')).to_contain_text('Saved manual.lkp')
  saved=p.evaluate('window.testSaved');self.assertEqual(saved['manualCalculations']['fields']['p6_t_0']['value'],'244:00:00');self.assertNotIn('684219',json.dumps(saved))
  p.locator('#admin-pin-lock').click();p.evaluate('calculateAll()');self.assertEqual(p.locator('#p6_t_0').input_value(),'244:00:00');self.assertEqual(p.locator('#p6-ephemeris-source').input_value(),'manual');self.assertEqual(p.locator('#p6_add_0').input_value(),'243:58:50')
  p.reload(timeout=120000);p.wait_for_function('typeof KPAutomaticCalculations!=="undefined"');p.evaluate('x=>restoreChartData(x)',saved);p.wait_for_timeout(1300);self.assertEqual(p.locator('#p6_t_0').input_value(),'244:00:00');self.assertEqual(p.locator('#p6_add_0').input_value(),'243:58:50')
  self.configure(dob='1950-12-21');self.assertEqual(p.locator('#p6-ephemeris-source').input_value(),'automatic');self.assertNotEqual(p.locator('#p6_t_0').input_value(),'244:00:00');self.assertNotIn('manualCalculations',p.evaluate('getChartData()'))
  # Cancelled native saves cannot install a new manual baseline.
  p.locator('#quick-admin-calculations').click();p.locator('[name=admin-pin]').fill('684219');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible();p.locator('[data-admin-worksheet=planet]').click();p.locator('#p6-ephemeris-source').select_option('manual')
  previous=p.evaluate('KPAutomaticCalculations.getSaved()');p.evaluate("KPChartFiles={directory:async()=>null,save:async()=>{throw new DOMException('Save cancelled.','AbortError')}}");p.locator('#admin-save-manual').click();expect(p.locator('#admin-save-status')).to_contain_text('cancelled');self.assertEqual(p.evaluate('KPAutomaticCalculations.getSaved()'),previous)
