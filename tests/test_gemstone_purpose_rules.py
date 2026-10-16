"""Bilingual KP/Vedic rule selection, unchanged approved gemstone evaluator and reports."""
import unittest
import test_personal_predictions as personal
class KPOnlyGemstoneTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_sixteen_bilingual_purposes_rank_maximum_relevant_houses(self):
  p=self.page;p.wait_for_function('window.KPCompactNavigation&&document.getElementById("gem-mode").options.length===2');p.evaluate("KPCompactNavigation.activate('gemstones')")
  self.assertEqual(p.locator('#gem-mode option').count(),2);self.assertEqual(p.locator('#gem-mode').input_value(),'kp');self.assertEqual(p.locator('#gem-event option').count(),16);self.assertEqual(p.locator('#gem-companion-panel').count(),0)
  before=p.evaluate('JSON.stringify(currentKPModel)')
  for option in p.locator('#gem-event option').evaluate_all('(nodes)=>nodes.map(n=>({value:n.value,text:n.textContent}))'):
   self.assertIn(' / ',option['text']);self.assertTrue(any('\u0900'<=c<='\u097f' for c in option['text']));p.locator('#gem-event').select_option(option['value'])
   if option['value']=='anger':self.assertEqual(p.locator('#gem-required').input_value(),'1,5,9')
   if option['value']=='all-wishes':self.assertEqual(p.locator('#gem-required').input_value(),'11')
   data=p.evaluate('KPGemstones.getData()');self.assertTrue(data['ready']);self.assertEqual(data['mode'],'kp');self.assertTrue(data['eventRanking']);maximum=max(r['score'] for r in data['results']);self.assertTrue(all(r['score']==maximum for r in data['results'] if r['qualifies']))
  self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),before)
  html=p.evaluate('KPGemstones.snapshot()');self.assertIn('KP event-based',html);self.assertNotIn('According to Vedic',html);self.assertNotIn('gem-companion-panel',html)
 def test_vedic_rule_and_saved_selection_preserve_approved_lords(self):
  p=self.page;p.wait_for_function('document.getElementById("gem-mode").options.length===2');p.evaluate("KPCompactNavigation.activate('gemstones')");p.locator('#gem-mode').select_option('vedic');data=p.evaluate('KPGemstones.getData()');self.assertEqual(data['mode'],'vedic');self.assertEqual(data['required'],[1,5,11]);self.assertTrue(p.locator('#gem-event').is_hidden());self.assertIn('Vedic gemstone guidance',p.evaluate('KPGemstones.snapshot()'))
  expected=p.evaluate("()=>{const lords=['Ma','Ve','Me','Mo','Su','Me','Ve','Ma','Ju','Sa','Sa','Ju'],lagna=currentKPModel.houses[0].signIndex;return [...new Set([1,5,11].map(h=>lords[(lagna+h-1)%12]))].sort();}");self.assertEqual(sorted(r['id'] for r in data['results'] if r['qualifies']),expected)
  p.evaluate('()=>{const save=getChartData();restoreChartData(save);}');self.assertEqual(p.evaluate('KPGemstones.getData().mode'),'vedic');p.locator('#gem-mode').select_option('kp');self.assertEqual(p.evaluate('KPGemstones.getData().mode'),'kp')
if __name__=='__main__':unittest.main()
