"""Numerology-only content checks; no astrology recalculation."""
import json,re,hashlib,subprocess,unittest
from pathlib import Path
import test_personal_predictions as personal
ROOT=Path(__file__).resolve().parents[1]
class NumerologySourceTests(unittest.TestCase):
 def test_nine_sources_and_unchanged_other_calculation_blocks(self):
  data=json.loads((ROOT/'vendor/predictions/numerology-data.json').read_text());self.assertEqual(len(data['sources']),9)
  for source in data['sources']:self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
  for n in range(1,10):
   self.assertTrue(any(r['number']==n and r['kind']=='birth' for r in data['records']))
   self.assertEqual(sum(r['number']==n and r['kind']=='destiny' for r in data['records']),1)
  base=subprocess.check_output(['git','show','555a5fc55d13495c8f5b7c4997d39d6ebae677be:index.html'],cwd=ROOT,text=True)
  current=(ROOT/'index.html').read_text();allowed={'kp-personal-predictions-script','kp-supplied-predictions','kp-numerology','kp-numerology-data','kp-resources-notes-script','kp-kaal-resources','kp-kaal-resource-data','kp-feature-updates-script','kp-gemstone-document','kp-horary-result-sheet','kp-additional-documents','kp-additional-document-data'}
  def blocks(s):
   result=[]
   for tag,attrs,body in re.findall(r'<(script|style)\b([^>]*)>(.*?)</\1>',s,re.S):
    m=re.search(r'id=["\']([^"\']+)',attrs)
    if not m or m[1] not in allowed:result.append((tag,attrs,body))
   return result
  self.assertEqual(blocks(base),blocks(current))
  def workspace(text):return re.search(r'<script id="kp-feature-updates-script">(.*?)</script>',text,re.S)[1].strip()
  old,new=workspace(base),workspace(current)
  # Only the gemstone recommendation code changes in this mixed workspace.
  self.assertEqual(old.split('  // User rule:')[0],new.split('  // User rule:')[0])
  self.assertEqual(old.split('  let sliceData=')[1].replace('KP · event house matches','KP · uploaded XI cusp rule'),new.split('  let sliceData=')[1])
class NumerologyBrowserTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_numerology_tab_birthday_selection_and_preview(self):
  p=self.page;p.wait_for_function('window.KPNumerology')
  self.assertEqual(p.locator('#pred-tab-outer-references').count(),0)
  self.assertEqual(p.evaluate("KPNumerology.numbers('1931-10-10')"),{'date':'1931-10-10','birth':1,'destiny':7})
  self.assertEqual(p.evaluate("KPNumerology.numbers('2000-02-29')"),{'date':'2000-02-29','birth':2,'destiny':6})
  self.assertTrue(p.evaluate("()=>{try{KPNumerology.numbers('2001-02-29');return false}catch(e){return true}}"))
  p.evaluate("document.getElementById('dob').value='1931-10-10'")
  before=p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')
  p.locator('#quick-prediction').click();p.locator('#pred-tab-numerology').click()
  d=p.evaluate('KPPersonalPredictions.getData()');self.assertTrue(d['ready']);self.assertEqual(d['numerology']['birth'],1);self.assertEqual(d['numerology']['destiny'],7)
  self.assertTrue(any(r['key']=='Bha7' for r in d['rows']));self.assertFalse(any(r['key']=='Bha1' for r in d['rows']))
  self.assertTrue(all(r['key'].startswith('mul1') or r['key']=='Bha7' for r in d['rows']))
  self.assertEqual(p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})'),before)
  with p.expect_popup() as opened:p.locator('#prediction-preview').click()
  preview=opened.value;preview.wait_for_function('document.querySelector(".personal-prediction-report")')
  text=preview.locator('body').inner_text();self.assertIn('भाग्यांक 7',text);self.assertIn('मूलांक 1',text);preview.close()
