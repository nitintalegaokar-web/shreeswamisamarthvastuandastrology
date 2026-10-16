"""Compact screen controls retain Horary inputs and the report action."""
import unittest
import test_personal_predictions as personal
class HoraryLayoutTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 def test_compact_desktop_and_mobile(self):
  context=self.browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   page.goto(self.url,timeout=90000);page.wait_for_selector('#hq-panel',state='attached');page.evaluate("document.querySelectorAll('main>section').forEach(s=>s.hidden=s.id!=='event-promise');document.getElementById('event-promise').style.display='block'");panel=page.locator('#hq-panel');panel.scroll_into_view_if_needed();self.assertLess(panel.bounding_box()['height'],300);self.assertLessEqual(panel.bounding_box()['width'],1200);page.locator('#hq-question').fill('Test question');page.locator('#hq-opinion').fill('Test opinion');page.locator('#hq-refresh').click();self.assertIn('Results updated',page.locator('#hq-status').inner_text());self.assertFalse(page.locator('#hq-preview').is_disabled());panel.screenshot(path='/tmp/kp-horary-compact.png');
   for cusp in range(1,13):
    page.locator('#ep-cusp').select_option(str(cusp));page.wait_for_function('(c)=>document.getElementById("ep-category").value===String(c)&&KPPrediction.getCatalogue().events.find(e=>String(e.id)===document.getElementById("hq-event").value).mainHouses.includes(Number(document.getElementById("ep-cusp").value))',arg=cusp);self.assertTrue(page.evaluate('(c)=>[...document.getElementById("hq-event").options].every(o=>KPPrediction.getCatalogue().events.find(e=>String(e.id)===o.value).mainHouses.includes(c))',cusp))
   page.locator('#ep-category').select_option('7');page.wait_for_function('document.getElementById("ep-cusp").value==="7"');options=page.locator('#hq-event option').evaluate_all('(os)=>os.map(o=>o.value)');page.locator('#hq-event').select_option(options[-1]);page.wait_for_function('KPPrediction.getCatalogue().events.find(e=>String(e.id)===document.getElementById("hq-event").value).mainHouses.includes(Number(document.getElementById("ep-cusp").value))');page.set_viewport_size({'width':390,'height':844});panel.scroll_into_view_if_needed();self.assertTrue(page.evaluate("(()=>{const p=document.getElementById('hq-panel');return p.scrollWidth<=p.clientWidth+1})()"));self.assertEqual(page.locator('#hq-question').input_value(),'Test question');self.assertEqual(errors,[])
  finally:
   context.close()
if __name__=='__main__':unittest.main()
