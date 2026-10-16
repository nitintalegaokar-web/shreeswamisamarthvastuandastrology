"""Manual cusp input lifecycle, current DBA workflow and A4 report regression."""
import json,unittest,fitz
import test_personal_predictions as personal
class ChartWorkspaceTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_manual_cusps_saved_restored_and_automatic_reset(self):
  p=self.page;p.wait_for_function('window.KPManualCusps&&window.KPTransitWorkspace')
  d=p.evaluate('''()=>{const baseline=syncKPWorksheetPositions().cusps.slice(),planets=JSON.stringify(currentKPModel.planets),edited=baseline.map(n=>(n+60)%1296000);KPManualCusps.apply(edited);const applied=currentKPModel.houses.map(h=>h.longitude),save=getChartData();KPManualCusps.reset();const reset=currentKPModel.houses.map(h=>h.longitude);restoreChartData(save);const restored=currentKPModel.houses.map(h=>h.longitude);KPManualCusps.reset();let invalid=false;try{KPManualCusps.apply(Array(12).fill(0));}catch(e){invalid=true;}return {baseline,edited,applied,reset,restored,invalid,planetsUnchanged:JSON.stringify(currentKPModel.planets)===planets,saved:!!save.manualCuspOverrides};}''')
  self.assertEqual(d['edited'],d['applied']);self.assertEqual(d['restored'],d['edited']);self.assertEqual(d['baseline'],d['reset']);self.assertTrue(d['invalid']);self.assertTrue(d['saved']);self.assertTrue(d['planetsUnchanged'])
 def test_current_dba_and_sun_uses_three_lords(self):
  p=self.page;p.wait_for_function('window.KPTransitWorkspace');d=p.evaluate('''()=>{const data=KPTransitWorkspace.current(),tracks=KPTransitWorkspace.sunTracks(data);return {tracks:tracks.map(t=>({label:t.label,levels:t.levels})),source:document.getElementById('tr-dba-selection-source').value,range:document.getElementById('tr-date-range-source').value};}''');self.assertEqual(d['source'],'current');self.assertEqual(d['range'],'period');self.assertEqual(len(d['tracks']),6)
  for t in d['tracks']:
   self.assertEqual(t['levels'],['sign','star','sub']);self.assertTrue(all(k in t['label'] for k in ['MD','AD','PD']))
 def test_transit_results_count_whole_sign_houses_from_natal_moon(self):
  p=self.page;p.wait_for_function('window.KPSuppliedPredictions');d=p.evaluate("""()=>{const previous=window.KPTransitChart,m=structuredClone(currentKPModel),moon=m.planets.find(p=>p.id==='Mo');let failures=[];try{for(let natal=0;natal<12;natal++)for(let sign=0;sign<12;sign++){moon.signIndex=natal;window.KPTransitChart={getData:()=>({ready:true,localDate:'2026-10-16',localTime:'12:00',planets:[{id:'Sa',details:{signIndex:sign}}],bhavGroups:Array.from({length:12},()=>[])})};const result=KPSuppliedPredictions.match('transit-results',m,new Date()),expected=(sign-natal+12)%12+1;const saturn=result.rows.filter(r=>r.key?.startsWith('SaTransitH'));if(!saturn.length||saturn.some(r=>r.key!=='SaTransitH'+expected))failures.push({natal,sign,expected});}return failures;}finally{window.KPTransitChart=previous;}}""");self.assertEqual(d,[])
 def test_selected_dasha_only_and_uploaded_bhavanusar_text(self):
  p=self.page;p.locator('#quick-prediction').click();p.locator('#pred-tab-dasha-results').click()
  for level in ['MD','AD','PD']:
   p.locator('#pred-dasha-level').select_option(level);data=p.evaluate('KPPersonalPredictions.getData()');self.assertEqual(len(data['periods']),1);self.assertEqual(data['periods'][0]['level'],level)
  p.locator('#pred-tab-planet-house-results').click();data=p.evaluate('KPPersonalPredictions.getData()');self.assertTrue(data['rows']);self.assertTrue(all('Bhav' in r['proof'] for r in data['rows']))
 def test_rules_editor_backup_and_print(self):
  p=self.page;p.wait_for_function('window.KPRules');self.assertEqual(p.evaluate('KPRules.all().length'),82);p.evaluate('KPRules.open()');p.locator('.kp-rules-dialog [data-new]').click();p.locator('.kp-rules-dialog [data-title]').fill('Owner test rule');p.locator('.kp-rules-dialog [data-rule-topic]').fill('Career');p.locator('.kp-rules-dialog [data-text]').fill('Reference houses: 2, 6, 10, 11.');p.locator('.kp-rules-dialog [data-save]').click();self.assertEqual(p.evaluate('KPRules.all().length'),83);self.assertEqual(p.evaluate('getChartData().predictionRules.custom[0].title'),'Owner test rule')
  with p.expect_popup() as opened:p.locator('.kp-rules-dialog [data-print]').click()
  w=opened.value;w.wait_for_selector('article');self.assertIn('Owner test rule',w.locator('article').inner_text());w.emulate_media(media='print');pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True),filetype='pdf');self.assertEqual(len(pdf),1);pdf.close();w.close()
 def test_fixed_developer_credit_is_separate_from_editable_astrologer(self):
  p=self.page;p.wait_for_function('window.KPDeveloperCredit');p.evaluate("document.getElementById('astroName').value='Customer Astrologer';document.getElementById('astroAddress').value='Customer address';document.getElementById('astroMobile').value='1234567890';saveAstrologerSettings();renderReport()")
  self.assertIn('Nitin Rajendra Talegaonkar',p.locator('#softwareDeveloperFooter').inner_text());self.assertNotIn('Customer Astrologer',p.locator('#softwareDeveloperFooter').inner_text())
  with p.expect_popup() as opened:p.evaluate('KPReportPreview.open("south9")')
  w=opened.value;w.wait_for_selector('[data-fixed-developer="true"]');text=w.locator('.report-developer-footer').inner_text();self.assertIn('Customer Astrologer',text);self.assertIn('Customer address',text);self.assertIn('Nitin Rajendra Talegaonkar',text);self.assertIn('+918412098690',text);w.close()
 def test_south_report_has_one_pair_of_tables_and_a4_pdf(self):
  p=self.page;p.wait_for_function('window.KPChartWorkspace');p.evaluate('renderReport()');self.assertEqual(p.locator('#printReport [data-report-section="south9"] table').count(),2)
  with p.expect_popup() as opened:p.evaluate('KPReportPreview.open("south9")')
  w=opened.value;w.wait_for_selector('#kp-report-a4-contract',state='attached');w.evaluate('document.fonts.ready');self.assertEqual(w.locator('.report-page table').count(),2)
  w.emulate_media(media='print');pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertGreater(len(pdf),0)
  for pg in pdf:
   self.assertAlmostEqual(pg.rect.width,595.28,delta=.5);self.assertAlmostEqual(pg.rect.height,841.89,delta=.5)
   for b in pg.get_text('blocks'):
    self.assertGreaterEqual(b[0],27);self.assertLessEqual(b[2],568)
  pdf.save('/tmp/kp-south-report-updated.pdf');pdf.close();w.close()
if __name__=='__main__':unittest.main()
