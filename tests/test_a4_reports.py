"""A4 output, report ordering/localization and chart-only uniform typography."""
import unittest,fitz
from playwright.sync_api import expect
import test_personal_predictions as personal
class A4ReportsTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__);tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__);setUp=personal.PersonalPredictionTests.setUp;tearDown=personal.PersonalPredictionTests.tearDown
 def test_report_list_and_all_available_report_borders_on_a4(self):
  p=self.page;p.wait_for_selector('#quick-online-account',state='attached')
  self.assertEqual(p.locator('#report-page-options input').nth(1).get_attribute('data-report-section'),'vedic-information');self.assertEqual(p.locator('#printReport>[data-report-section=basic],#report-page-options [data-report-section=basic]').count(),0)
  p.evaluate('KPReportPages.selectAll()')
  with p.expect_popup() as opened:p.evaluate('KPSelectedReport.preview()')
  w=opened.value;w.wait_for_selector('#kp-report-a4-contract',state='attached');w.evaluate('document.fonts.ready');w.wait_for_timeout(800)
  overflow=w.evaluate("""()=>[...document.querySelectorAll('body>.report-page')].flatMap(p=>{const b=p.getBoundingClientRect();return [...p.querySelectorAll('td,th,.v38-position,.bi-facts dd,.v-chart')].filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&(r.right>b.right+2||r.left<b.left-2)}).map(n=>p.dataset.reportSection+':'+n.textContent.slice(0,35))})""")
  self.assertEqual(overflow,[]);self.assertEqual(w.locator('body>.report-page').nth(1).get_attribute('data-report-section'),'vedic-information');self.assertNotIn('Natal Chart Data Entry',w.locator('body').inner_text());self.assertNotIn('Horary Chart Data Entry',w.locator('body').inner_text());w.emulate_media(media='print')
  pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertGreater(len(pdf),30)
  for pg in pdf:
   self.assertAlmostEqual(pg.rect.width,595.28,delta=.5);self.assertAlmostEqual(pg.rect.height,841.89,delta=.5)
   for b in pg.get_text('blocks'):self.assertGreaterEqual(b[0],27);self.assertLessEqual(b[2],568)
  pdf.close();w.close()
 def test_individual_previews_marathi_and_education_a4(self):
  p=self.page;p.wait_for_selector('#quick-online-account',state='attached');p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})')
  for section in ['vedic-information','single-page','kp-fourfold','kp-sixfold','kp-fourstep-section','prediction','dasha-fal','gemstones','muhurta','aspects','transit','transit-chart','transit-panchang','ephemeris','education-profession','disease','dasha-promise','event-promise','nadi-astrology','matchmaking','south9','hit-theory','vedic-rashi']:
   with p.expect_popup() as opened:p.evaluate('(id)=>KPReportPreview.open(id)',section)
   w=opened.value;w.wait_for_selector('.report-page');self.assertEqual(w.locator('html').get_attribute('lang'),'mr');self.assertEqual(w.locator('#kp-report-a4-contract').count(),1)
   if section=='vedic-information':expect(w.locator('.bi-facts')).to_contain_text('सूर्योदय');expect(w.locator('body')).not_to_contain_text('Sunrise');expect(w.locator('body')).not_to_contain_text('Natal Chart Data Entry')
   w.emulate_media(media='print');pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True),filetype='pdf')
   for pg in pdf:
    self.assertAlmostEqual(pg.rect.width,595.28,delta=.5);self.assertAlmostEqual(pg.rect.height,841.89,delta=.5)
    for b in pg.get_text('blocks'):self.assertGreaterEqual(b[0],27);self.assertLessEqual(b[2],568)
   pdf.close();w.close()
 def test_selected_tenth_house_profession_prints_without_cell_overlap(self):
  p=self.page;p.wait_for_selector('#ed-category',state='attached');p.locator('#quick-education-profession').click();p.locator('#ed-category').select_option('10')
  with p.expect_popup() as opened:p.locator('#education-profession-preview').click()
  w=opened.value;w.wait_for_selector('[data-education-cusp="10"]');self.assertEqual(w.locator('[data-education-cusp="4"],[data-education-cusp="9"]').count(),0);w.emulate_media(media='print')
  bad=w.evaluate("""()=>[...document.querySelectorAll('table')].flatMap(table=>[...table.rows].flatMap(row=>[...row.cells].filter(cell=>{const r=cell.getBoundingClientRect(),b=table.getBoundingClientRect();return r.right>b.right+1||r.left<b.left-1}).map(n=>n.textContent)))""");self.assertEqual(bad,[])
  pdf=fitz.open(stream=w.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertIn('Profession',''.join(pg.get_text() for pg in pdf))
  for pg in pdf:
   self.assertAlmostEqual(pg.rect.width,595.28,delta=.5);self.assertAlmostEqual(pg.rect.height,841.89,delta=.5)
   for b in pg.get_text('blocks'):self.assertGreaterEqual(b[0],27);self.assertLessEqual(b[2],568)
  pdf.save('/tmp/profession-a4-final.pdf');pdf.close();w.close()
 def test_font_and_bold_controls_keep_uniform_planets_and_leave_fields_unchanged(self):
  p=self.page;p.wait_for_selector('#quick-online-account',state='attached');fields=p.evaluate('()=>["name","birthTime"].map(id=>getComputedStyle(document.getElementById(id)).fontSize)')
  for size,bold in [(12,False),(18,True),(10,False)]:
   p.evaluate('(s)=>KPPreferences.save({...KPPreferences.get(),fontSize:s.size,fontBold:s.bold})',{'size':size,'bold':bold});p.wait_for_timeout(250)
   self.assertEqual(p.evaluate('()=>["name","birthTime"].map(id=>getComputedStyle(document.getElementById(id)).fontSize)'),fields)
   sizes=p.evaluate('()=>[...document.querySelectorAll("#home-kundali .v38-name")].map(n=>({size:getComputedStyle(n).fontSize,bold:getComputedStyle(n).fontWeight}))');self.assertTrue(sizes);self.assertEqual(len(set(n['size'] for n in sizes)),1);self.assertTrue(all(n['bold']==('700' if bold else '400') for n in sizes))
   if size==12:normal=float(sizes[0]['size'][:-2])
   if size==18:self.assertGreater(float(sizes[0]['size'][:-2]),normal)
   if size==10:self.assertLess(float(sizes[0]['size'][:-2]),normal)
  p.locator('#quick-online-account').click();expect(p.locator('#kp-account-dialog input[type=url]')).to_be_visible();expect(p.locator('#kp-account-dialog')).to_contain_text('hosted software address')
if __name__=='__main__':unittest.main()
