"""Content, interpretation matching and calculation-byte preservation only."""
import json,hashlib,re,unittest,subprocess
from pathlib import Path
import test_personal_predictions as personal
ROOT=Path(__file__).resolve().parents[1]
BASELINE='73963e841e1e61264b1bed57cbd773729f864799'
class PredictionSourceTests(unittest.TestCase):
 def test_all_supplied_files_preserved_and_calculation_blocks_unchanged(self):
  data=json.loads((ROOT/'vendor/predictions/supplied-content.json').read_text());self.assertEqual(data['metadata']['sourceCount'],82)
  self.assertEqual(len(data['sources']),82)
  for source in data['sources']:self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
  coverage={s for r in data['records'] for s in r['sources']};self.assertEqual(len(coverage),82)
  self.assertEqual(len({r['key'] for r in data['records'] if r['kind']=='dasha-pair'}),81)
  self.assertEqual(len({r['key'] for r in data['records'] if r['kind']=='house-lord'}),144)
  self.assertEqual(len({r['key'] for r in data['records'] if r['kind']=='transit-house'}),108)
  base=subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT,text=True)
  current=(ROOT/'index.html').read_text();ignore={'kp-personal-predictions-script','kp-supplied-prediction-data','kp-supplied-predictions','kp-numerology','kp-numerology-data','kp-resources-notes-script','kp-kaal-resources','kp-kaal-resource-data','kp-feature-updates-script','kp-gemstone-document','kp-horary-result-sheet','kp-additional-documents','kp-additional-document-data'}
  def blocks(text):
   output=[]
   for tag,attrs,body in re.findall(r'<(script|style)\b([^>]*)>(.*?)</\1>',text,re.S):
    m=re.search(r'id=["\']([^"\']+)',attrs)
    if m and m[1] in ignore:continue
    output.append((tag,attrs,body))
   return output
  self.assertEqual(blocks(base),blocks(current),'Any unrelated script, calculation or data change is forbidden.')
  self.assertTrue(any(r['sourceKey']=='Y11' and r['key']=='Y320' for r in data['records']))
class PredictionContentBrowserTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_marathi_matching_transit_dasha_references_and_print_without_native_mutation(self):
  p=self.page;p.wait_for_function('window.KPSuppliedPredictions && window.currentKPModel?.ready')
  p.evaluate("KPPreferences.save({...KPPreferences.get(),language:'marathi'})")
  before=p.evaluate("JSON.stringify({model:currentKPModel,periods:mdDashaPeriods,st:document.getElementById('birthPlaceSiderealTime').value,ayan:document.getElementById('ayanValue').value})")
  p.locator('#quick-prediction').click()
  for category in ['general-predictions','house-results','dasha-results','yoga-results','transit-results','numerology']:
   p.locator('#pred-tab-'+category).click()
   if category=='transit-results':p.locator('#pred-supplied-transit-refresh').click()
   result=p.evaluate('KPPersonalPredictions.getData()');self.assertTrue(result['ready'],result)
   if category in ['general-predictions','house-results','dasha-results','transit-results']:
    supplied=[r for r in result['rows'] if r.get('supplied')];self.assertTrue(supplied,category)
    self.assertTrue(all(r['proof'] for r in supplied))
    self.assertTrue(any(re.search('[\u0900-\u097f]',r['text']) for r in supplied),category)
   if category=='transit-results':self.assertEqual(len(result['rows']),9);self.assertIn('selected Transit Chart',result['context'])
   self.assertIn('personal-prediction',p.evaluate('KPPersonalPredictions.snapshot()'))
  self.assertEqual(p.evaluate("JSON.stringify({model:currentKPModel,periods:mdDashaPeriods,st:document.getElementById('birthPlaceSiderealTime').value,ayan:document.getElementById('ayanValue').value})"),before)
  p.locator('#pred-tab-general-predictions').click()
  with p.expect_popup() as opened:p.locator('#prediction-preview').click()
  preview=opened.value;preview.wait_for_function('document.querySelector(".personal-prediction-report")');preview.evaluate('document.fonts.ready')
  self.assertTrue(re.search('[\u0900-\u097f]',preview.locator('body').inner_text()))
  import fitz
  pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
  self.assertGreater(len(pdf),0)
  for page in pdf:self.assertAlmostEqual(page.rect.width,595.28,delta=1);self.assertAlmostEqual(page.rect.height,841.89,delta=1)
  pdf.close();preview.close()
