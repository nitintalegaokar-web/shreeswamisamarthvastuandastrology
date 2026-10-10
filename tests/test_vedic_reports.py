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
class VedicWorkflowTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def test_vedic_chart_report_border_and_dense_division_labels(self):
  p=self.page;p.wait_for_selector('#v-year',state='attached');p.locator('#quick-report').click();p.evaluate('KPReportPages.selectSections(["vedic-rashi","vedic-vargas"])')
  for language in ['english','marathi']:
   p.evaluate('language=>KPPreferences.save({...KPPreferences.get(),language})',language)
   for style in ['south','north']:
    p.evaluate('style=>KPVedicUI.setChartStyle(style)',style)
    with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
    w=opened.value;expect(w.locator('.v-chart')).to_have_count(17);w.evaluate('document.fonts.ready')
    for media in ['screen','print']:
     w.emulate_media(media=media)
     defects=w.evaluate('''()=>{const issues=[];for(const page of document.querySelectorAll('.v-report-page')){const r=page.getBoundingClientRect(),s=getComputedStyle(page),inset=parseFloat(s.paddingLeft)+parseFloat(s.borderLeftWidth);for(const n of page.querySelectorAll('table,.v-chart,.v-native,h2')){const b=n.getBoundingClientRect();if(b.left<r.left+inset-1||b.right>r.right-inset+1||b.bottom>r.bottom-inset+1)issues.push(n.className);}for(const chart of page.querySelectorAll('.v-chart')){const c=chart.getBoundingClientRect();for(const n of chart.querySelectorAll('strong span')){const b=n.getBoundingClientRect(),cell=n.closest('.v-chart-cell')?.getBoundingClientRect()||c;if(b.left<cell.left-1||b.right>cell.right+1||b.top<cell.top-1||b.bottom>cell.bottom+1)issues.push(n.textContent);}}}if(getComputedStyle(document.body,'::before').content!=='none')issues.push('decorative body border');return issues;}''')
     self.assertEqual(defects,[],msg=f'{language} {style} {media}: {defects}')
    self.assertEqual(w.locator('.v-chart strong span').count(),170)
    if language=='english' and style=='south':
     pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');pdf.save('/tmp/vedic-bordered-native.pdf');self.assertEqual(len(pdf),3,msg=w.evaluate('()=>[...document.querySelectorAll(".v-report-page")].map(p=>({height:p.getBoundingClientRect().height,grid:p.querySelector(".v-varga-print-grid")?.getBoundingClientRect().height,charts:[...p.querySelectorAll(".v-chart")].map(c=>c.getBoundingClientRect().height)}))'))
     for page in pdf:
      for block in page.get_text('blocks'):
       self.assertGreaterEqual(block[0],35);self.assertLessEqual(block[2],560);self.assertGreaterEqual(block[1],35);self.assertLessEqual(block[3],808)
     pdf.close()
    if language=='marathi':w.screenshot(path=f'/tmp/vedic-bordered-{style}.png')
    w.close()
 def test_right_click_chart_styles_and_automatic_sade_sati(self):
  p=self.page;p.wait_for_selector('#v-year',state='attached');native=p.evaluate('JSON.stringify(currentKPModel)');p.locator('#quick-vedic-kundali').click()
  self.assertEqual(p.locator('#v-calculate,#report-vedic-calculate').count(),0)
  p.locator('#v-results .v-chart').click(button='right');expect(p.locator('#v-chart-menu')).to_be_visible();p.locator('[data-v-chart-style="north"]').click()
  expect(p.locator('#v-results .v-chart-north')).to_be_visible();expect(p.locator('#v-results [data-vedic-house]')).to_have_count(12)
  sizes=p.evaluate('()=>{const c=document.querySelector("#v-results .v-chart-north"),s=c.querySelector("svg");return [c.clientWidth,c.clientHeight,s.getBoundingClientRect().width,s.getBoundingClientRect().height];}');self.assertAlmostEqual(sizes[0],sizes[2],delta=1);self.assertAlmostEqual(sizes[1],sizes[3],delta=1)
  asc=p.evaluate('KPVedic.core().vargas[1][0].sign');self.assertEqual(p.locator('#v-results [data-vedic-house="1"]').get_attribute('data-vedic-sign'),str(asc))
  p.locator('#v-division').select_option('9');asc=p.evaluate('KPVedic.core().vargas[9][0].sign');self.assertEqual(p.locator('#v-results [data-vedic-house="1"]').get_attribute('data-vedic-sign'),str(asc))
  for n in p.locator('#v-results .v-north-house').all():
   sign=int(n.get_attribute('data-vedic-sign'));expected=p.evaluate('sign=>KPVedic.core().vargas[9].filter(r=>r.sign===sign).map(r=>r.id)',sign);self.assertEqual(n.locator('strong span').all_text_contents(),expected)
  compared=p.evaluate('''async()=>{const tracks=Array.from({length:12},(_,i)=>({id:String(i),planet:'Sa',levels:['sign'],test:d=>d.signIndex===i})),options={start:new Date('2027-01-01T00:00:00Z'),end:new Date('2028-06-01T00:00:00Z'),tracks};return {daily:await KPTransit.scan(options),weekly:await KPTransit.scan({...options,signStepDays:7})};}''')
  self.assertGreater(len(compared['daily']),2);self.assertEqual(len(compared['daily']),len(compared['weekly']))
  for a,b in zip(compared['daily'],compared['weekly']):
   self.assertEqual(a['trackId'],b['trackId'])
   for edge in ['start','end']:self.assertLessEqual(abs(p.evaluate('v=>Date.parse(v[0])-Date.parse(v[1])',[a[edge],b[edge]])),2000)
  p.screenshot(path='/tmp/vedic-north-final.png')
  with p.expect_popup() as opened:p.locator('#vedic-kundali-preview').click()
  preview=opened.value;expect(preview.locator('.v-chart-north')).to_be_visible();preview.close()
  p.locator('#v-results .v-chart').click(button='right');p.locator('[data-v-chart-style="south"]').click();expect(p.locator('#v-results [data-vedic-chart-style="south"]')).to_be_visible()
  p.locator('[data-v-tab="sade"]').click();p.wait_for_function('KPVedic.core().sade.ready',timeout=90000);expect(p.locator('#v-results [data-vedic-sade-report]')).to_contain_text('Current phase');rows=p.evaluate('KPVedic.core().sade.rows.length');expect(p.locator('#v-results [data-vedic-sade-report] tbody tr')).to_have_count(rows)
  with p.expect_popup() as opened:p.locator('#vedic-kundali-preview').click()
  preview=opened.value;expect(preview.locator('[data-vedic-sade-report] tbody tr')).to_have_count(rows);preview.close();self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),native)
  p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})');expect(p.locator('[data-v-tab="sade"]')).to_contain_text('साडेसाती');p.screenshot(path='/tmp/vedic-sade-final.png')
 def test_annual_selection_grows_automatically_preview_print_and_direct_pdf(self):
  p=self.page;p.wait_for_selector('#v-year',state='attached');p.locator('#quick-report').click();p.evaluate('KPReportPages.clear()');p.locator('[data-report-page-key="vedic-varshaphal"]').check()
  p.wait_for_function('KPVedic.core().calculated&&!document.getElementById("report").matches("[aria-busy=true]")',timeout=90000)
  self.assertEqual(p.evaluate('KPReportPages.selected().map(p=>p.dataset.reportSection)'),['vedic-varshaphal']*3);self.assertEqual(p.locator('#report-vedic-calculate,#v-calculate').count(),0)
  with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
  preview=opened.value;expect(preview.locator('.v-report-page')).to_have_count(3);self.assertNotIn('Calculate Vedic reports',preview.locator('body').inner_text());preview.close()
  self.context.add_init_script('window.print=()=>{window.__testPrinted=(window.__testPrinted||0)+1;}')
  with p.expect_popup() as opened:p.locator('#print-selected-report').click()
  preview=opened.value;preview.wait_for_function('window.__testPrinted===1');expect(preview.locator('.v-report-page')).to_have_count(3);preview.close()
  p.evaluate('KPReportPages.selectSections(["vedic-shadbala","vedic-vargas"])')
  with p.expect_download(timeout=90000) as download:p.locator('#report-selection-pdf').click()
  file=download.value;self.assertEqual(file.suggested_filename,'KP-Selected-Report.pdf');file.save_as('/tmp/vedic-actual-export.pdf');pdf=fitz.open('/tmp/vedic-actual-export.pdf');self.assertEqual(len(pdf),3)
  for page in pdf:
   self.assertTrue(page.get_images());self.assertGreater(len(page.get_pixmap().samples),10000)
   for img in page.get_images():
    for rect in page.get_image_rects(img[0]):self.assertGreaterEqual(rect.x0,27);self.assertLessEqual(rect.x1,568);self.assertLessEqual(rect.y1,815)
  pdf.close()
  p.evaluate('KPReportPages.selectSections(["vedic-dasha-bhukti"])')
  with p.expect_download(timeout=90000) as download:p.locator('#report-selection-pdf').click()
  download.value.save_as('/tmp/vedic-long-export.pdf');pdf=fitz.open('/tmp/vedic-long-export.pdf');self.assertGreaterEqual(len(pdf),2);self.assertTrue(any(len(page.get_images())>1 for page in pdf))
  for page in pdf:
   rects=[rect for img in page.get_images() for rect in page.get_image_rects(img[0])]
   for rect in rects:self.assertLessEqual(rect.y1,815)
   for i,a in enumerate(rects):
    for b in rects[i+1:]:self.assertTrue(a.y1<=b.y0+.05 or b.y1<=a.y0+.05)
  pdf.close();p.evaluate('KPReportPages.clear()')
  with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
  preview=opened.value;preview.wait_for_event('close') if not preview.is_closed() else None;expect(p.locator('#report-page-selection-status')).to_contain_text('Select at least one page')
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

 def test_private_right_click_sade_sati_and_actual_report_buttons(self):
  self.go('vedic-kundali');p=self.page;native=self.private('JSON.stringify(currentKPModel)');self.assertEqual(p.locator('#v-calculate,#report-vedic-calculate').count(),0)
  p.locator('#v-results .v-chart').click(button='right');expect(p.locator('#v-chart-menu')).to_be_visible(timeout=30000);p.locator('[data-v-chart-style="north"]').click();expect(p.locator('#v-results .v-chart-north')).to_be_visible(timeout=30000)
  self.assertEqual(p.evaluate('typeof KPVedicUI'),'undefined');p.locator('[data-v-tab="sade"]').click();expect(p.locator('#v-results [data-vedic-sade-report] tbody tr').first).to_be_visible(timeout=90000)
  rows=self.private('KPVedic.core().sade.rows.length')
  with p.expect_popup() as opened:p.locator('#vedic-kundali-preview').click()
  preview=opened.value;expect(preview.locator('[data-vedic-sade-report] tbody tr')).to_have_count(rows,timeout=90000);self.assertNotIn('KPVedic.calculate',preview.content());preview.close();self.assertEqual(self.private('JSON.stringify(currentKPModel)'),native)
  self.go('report');self.private('KPReportPages.selectSections(["vedic-varshaphal"])');p.reload();expect(p.locator('#report-page-options')).to_be_visible(timeout=60000)
  with p.expect_popup() as opened:p.locator('#report-selection-preview').click()
  preview=opened.value;expect(preview.locator('.v-report-page')).to_have_count(3,timeout=90000);preview.close()
  self.context.add_init_script('window.print=()=>{window.__testPrinted=(window.__testPrinted||0)+1;}')
  with p.expect_popup() as opened:p.locator('#print-selected-report').click()
  preview=opened.value;preview.wait_for_function('window.__testPrinted===1',timeout=90000);expect(preview.locator('.v-report-page')).to_have_count(3);preview.close()
  with p.expect_download(timeout=90000) as downloaded:p.locator('#report-selection-pdf').click()
  downloaded.value.save_as('/tmp/vedic-private-button-export.pdf');pdf=fitz.open('/tmp/vedic-private-button-export.pdf');self.assertEqual(len(pdf),3);self.assertIn('Mudda', ''.join(page.get_text() for page in pdf));pdf.close()
