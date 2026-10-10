"""Native Vedic calculations, selected A4 reports and transient hover details."""
import json,subprocess,unittest
from pathlib import Path
import fitz
from playwright.sync_api import expect
import test_personal_predictions as personal
import test_protected_server as protected
ROOT=Path(__file__).resolve().parents[1]
class VedicArithmeticTests(unittest.TestCase):
 def run_js(self,expression):
  result=subprocess.run(['node','-e',"require('./vendor/vedic/engine.js');const M=KPVedicMath;"+expression],cwd=ROOT,check=True,capture_output=True,text=True);return json.loads(result.stdout)
 def test_classical_bindus_rotation_reductions_and_division_boundaries(self):
  data=self.run_js("""const points={Su:0,Mo:32,Ma:64,Me:96,Ju:128,Ve:160,Sa:192};const a=M.ashtakavarga(points,240),b=M.ashtakavarga(Object.fromEntries(Object.entries(points).map(([id,lon])=>[id,lon+90])),330);console.log(JSON.stringify({totals:a.bhinna.map(r=>r.reduce((s,v)=>s+v,0)),a,b,divisions:[M.varga(14.999,2),M.varga(15,2),M.varga(30,2),M.varga(45,2),M.varga(90,9),M.varga(30,9),M.varga(60,9),M.varga(18,30),M.varga(35,30),M.varga(360,60)],weights:Object.values(M.WEIGHTS).map(w=>Object.values(w).reduce((a,b)=>a+b,0)),friend:M.compound('Su','Ju',points)}));""")
  self.assertEqual(data['totals'],[48,49,39,54,56,52,39]);self.assertEqual(data['a']['total'],337);self.assertEqual(data['weights'],[20]*4)
  self.assertEqual([v['sign'] for v in data['divisions']],[4,3,3,4,3,9,6,2,5,0]);self.assertEqual(data['friend'],'neutral')
  for a,b in zip(data['a']['bhinna'],data['b']['bhinna']):self.assertEqual(b,a[-3:]+a[:-3])
  for i,row in enumerate(data['a']['ekadhipatya']):
   self.assertTrue(all(0<=v<=data['a']['trikona'][i][j] for j,v in enumerate(row)))
  for p in data['a']['pinda']:self.assertEqual(p['total'],p['rasi']+p['graha'])
  self.assertEqual(data['a']['bhinna'][0], [5,4,4,4,2,3,4,4,4,4,5,5])
 def test_strength_geometry_and_complete_context_requirement(self):
  d=self.run_js("""const p={Su:10,Mo:190,Ma:80,Me:125,Ju:250,Ve:310,Sa:340};const c={cusps:Array.from({length:12},(_,i)=>i*30),declinations:Object.fromEntries(M.IDS.map(id=>[id,0])),meanLongitudes:{...p},latitudes:Object.fromEntries(M.IDS.map(id=>[id,0])),dayProgress:.5,third:1,solarHourAngle:0,yearLord:'Su',monthLord:'Su',dayLord:'Su',hourLord:'Su'};let rejects=false;try{M.strength(p,0,null);}catch(_){rejects=true;}console.log(JSON.stringify({result:M.strength(p,0,c),rejects,aspects:[M.aspect('Su',0,0),M.aspect('Su',0,60),M.aspect('Su',0,90),M.aspect('Su',0,120),M.aspect('Su',0,180),M.aspect('Ma',0,90),M.aspect('Ma',0,210),M.aspect('Ju',0,120),M.aspect('Ju',0,240),M.aspect('Sa',0,60),M.aspect('Sa',0,270)]}));""")
  self.assertTrue(d['rejects']);self.assertEqual(d['aspects'],[0,15,45,30,60,60,60,60,60,60,60]);sun=d['result']['rows'][0];self.assertEqual(sun['parts']['uccha'],60);self.assertAlmostEqual(sun['dig'],80/3,places=2);self.assertEqual(sun['parts']['nat'],60);self.assertEqual(sun['parts']['abda'],15);self.assertEqual(sun['parts']['masa'],30);self.assertEqual(sun['parts']['vara'],45);self.assertEqual(sun['parts']['hora'],60);self.assertEqual(sun['parts']['ayan'],60)
  self.assertEqual([p['naisargika'] for p in d['result']['rows']],[60,51.43,17.14,25.71,34.29,42.86,8.57])
  for row in d['result']['rows']:self.assertAlmostEqual(row['total'],sum(row[k] for k in ['sthana','dig','kala','cheshta','naisargika','drik']),delta=.025)
class VedicInterfaceTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def test_native_solar_return_saturn_phases_and_full_period_reports(self):
  p=self.page;p.wait_for_function('document.getElementById("v-year")');native=p.evaluate('JSON.stringify(currentKPModel)')
  result=p.evaluate('''async()=>{const d=await KPVedic.calculate();return {data:d,solarError:KPVedicMath.angle(KPEphemeris.longitude(new Date(d.annual.date),'Su'),d.native.points.Su),saturnSigns:d.sade.rows.map(r=>KPVedicMath.sign(KPEphemeris.longitude(new Date((Date.parse(r.start)+Date.parse(r.end))/2),'Sa')))};}''')
  d=result['data'];self.assertTrue(d['calculated']);self.assertTrue(d['bala']['ready']);self.assertEqual(len(d['bala']['rows']),7);self.assertEqual(len(d['bala']['houses']),12);self.assertLess(result['solarError'],.00001);self.assertEqual(len(d['annual']['mudda']),9);self.assertEqual(d['annual']['mudda'][0]['start'],d['annual']['date']);self.assertEqual(d['annual']['mudda'][-1]['end'],d['annual']['next'])
  for a,b in zip(d['annual']['mudda'],d['annual']['mudda'][1:]):self.assertEqual(a['end'],b['start'])
  signs={a['id']:a['sign'] for a in d['sade']['phases']}
  for r,sign in zip(d['sade']['rows'],result['saturnSigns']):self.assertEqual(sign,signs[r['trackId']]);self.assertLess(r['start'],r['end'])
  self.assertTrue(d['dasha']['ready']);self.assertTrue(d['dasha']['all']);self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),native)
  p.locator('#quick-vedic-kundali').click();p.locator('[data-v-tab="strength"]').click();expect(p.locator('#v-results [data-vedic-strength] tbody tr')).to_have_count(7)
  with p.expect_popup() as opened:p.locator('#vedic-kundali-preview').click()
  preview=opened.value;expect(preview.locator('.v-table')).to_have_count(2);expect(preview.get_by_role('button',name='Zoom +',exact=True)).to_be_visible();preview.close()
  p.locator('#quick-report').click();p.evaluate('KPReportPages.selectSections(["vedic-sarva","vedic-varshaphal"])')
  with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
  preview=opened.value;expect(preview.locator('.v-report-page')).to_have_count(4,timeout=30000);expect(preview.locator('.v-sbc-cell')).to_have_count(81);expect(preview.locator('[data-nakshatra]')).to_have_count(28)
  pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(pdf),4);self.assertIn('337',''.join(page.get_text() for page in pdf));self.assertNotIn('Sheet1',''.join(page.get_text() for page in pdf));pdf.close();preview.close()
 def test_group_selection_all_divisions_marathi_and_hover(self):
  p=self.page;p.wait_for_function('document.getElementById("v-year")');p.locator('#quick-report').click();p.evaluate('KPReportPages.clear()');p.locator('[data-report-page-key="vedic-vargas"]').check();self.assertEqual(p.evaluate('KPReportPages.selected().length'),2);expect(p.locator('[data-report-page-key="vedic-vargas"]').locator('..')).to_contain_text('02')
  with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
  preview=opened.value;expect(preview.locator('.v-chart')).to_have_count(16);pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');self.assertEqual(len(pdf),2);pdf.close();preview.close()
  p.locator('#report-all-toggle').check();self.assertTrue(p.evaluate('KPReportPages.selected().length>30'));p.locator('#report-all-toggle').uncheck();self.assertEqual(p.evaluate('KPReportPages.selected().length'),0)
  p.locator('#quick-vedic-kundali').click();cell=p.locator('.v-chart-cell strong').filter(has_text='Su').first;font=p.evaluate('getComputedStyle(document.querySelector(".v-chart-cell strong")).fontSize');cell.hover();expect(p.locator('#kp-hover-detail')).to_be_visible();expect(p.locator('#kp-hover-detail')).to_contain_text('Su');p.mouse.move(1400,900);expect(p.locator('#kp-hover-detail')).to_be_hidden();self.assertEqual(p.evaluate('getComputedStyle(document.querySelector(".v-chart-cell strong")).fontSize'),font)
  p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})');expect(p.locator('#page-title')).to_have_text('वैदिक कुंडली');expect(p.locator('[data-v-tab="strength"]')).to_contain_text('बल');self.assertNotIn('Su',p.locator('#v-results').inner_text())
class VedicPrivateTests(unittest.TestCase):
 setUpClass=classmethod(protected.ProtectedServerTests.setUpClass.__func__);tearDownClass=classmethod(protected.ProtectedServerTests.tearDownClass.__func__);setUp=protected.ProtectedServerTests.setUp;tearDown=protected.ProtectedServerTests.tearDown;post=protected.ProtectedServerTests.post;go=protected.ProtectedServerTests.go;private=protected.ProtectedServerTests.private
 def test_private_vedic_reports_hover_and_pdf_download(self):
  self.go('vedic-kundali');expect(self.page.locator('#vedic-kundali .v-chart')).to_be_visible();self.assertEqual(self.page.evaluate('typeof KPVedicMath'),'undefined')
  cell=self.page.locator('.v-chart-cell strong').filter(has_text='Su').first;cell.hover();expect(self.page.locator('#kp-hover-detail')).to_be_visible();self.page.mouse.move(1540,800);expect(self.page.locator('#kp-hover-detail')).to_be_hidden()
  with self.page.expect_popup() as opened:self.page.locator('#vedic-kundali-preview').click()
  preview=opened.value;expect(preview.locator('.v-chart')).to_be_visible(timeout=30000);preview.close()
  self.go('report');self.private('KPReportPages.selectSections(["vedic-shadbala","vedic-vargas"])');self.page.reload();expect(self.page.locator('#page-title')).to_have_text('Your chart report',timeout=30000)
  with self.page.expect_popup() as opened:self.page.locator('#report-selection-preview').click()
  preview=opened.value;expect(preview.locator('.v-report-page')).to_have_count(3,timeout=30000);self.assertNotIn('KPVedicMath',preview.content());preview.close()
  response=self.page.request.get(self.url+'/report-pdf',timeout=90000);self.assertEqual(response.status,200);self.assertIn('attachment',response.headers['content-disposition']);pdf=fitz.open(stream=response.body(),filetype='pdf');self.assertEqual(len(pdf),3);pdf.close()
