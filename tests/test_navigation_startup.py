"""Legacy navigation never appears during startup; shortcut collapse survives reopening."""
import unittest
import test_personal_predictions as personal
class NavigationStartupTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 def test_no_legacy_icon_flash_and_saved_shortcut_visibility(self):
  context=self.browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script('''window.legacyNavigationFlashes=[];new MutationObserver(()=>{for(const n of document.querySelectorAll('#kp-quick-tools')){const s=getComputedStyle(n);if(s.display!=='none'&&s.visibility!=='hidden'&&n.getBoundingClientRect().width>0)window.legacyNavigationFlashes.push(n.id||n.className);}}).observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['class','hidden']});''')
  try:
   page.goto(self.url,timeout=90000);page.wait_for_selector('#kp-compact-navigation');self.assertEqual(page.evaluate('legacyNavigationFlashes'),[]);self.assertEqual(page.locator('.kp-main-menu>button,.kp-main-menu>details').count(),11);self.assertEqual(page.locator('.kp-small-shortcuts>button').count(),10)
   self.assertTrue(page.evaluate("document.head.contains(document.getElementById('kp-navigation-startup-guard'))"));page.locator('.kp-shortcut-toggle').click();self.assertTrue(page.locator('.kp-small-shortcuts').is_hidden());page.reload(timeout=90000);page.wait_for_selector('#kp-compact-navigation');self.assertTrue(page.locator('.kp-small-shortcuts').is_hidden());self.assertEqual(page.locator('.kp-shortcut-toggle').get_attribute('aria-expanded'),'false');self.assertEqual(page.evaluate('legacyNavigationFlashes'),[])
   page.locator('.kp-shortcut-toggle').click();self.assertTrue(page.locator('.kp-small-shortcuts').is_visible());self.assertEqual(page.evaluate("localStorage.getItem('kp-master-small-shortcuts-visible-v1')"),'true');page.locator('#kp-left-panel-toggle').click();self.assertFalse(page.locator('.app-sidebar').is_visible()==(page.locator('#kp-left-panel-toggle').get_attribute('aria-expanded')=='false'));page.evaluate("KPPreferences.save({...KPPreferences.get(),sidebarHidden:false})");self.assertTrue(page.locator('.app-sidebar').is_visible());page.reload(timeout=90000);page.wait_for_selector('#kp-compact-navigation');self.assertTrue(page.locator('.app-sidebar').is_visible());self.assertGreaterEqual(page.locator('main').bounding_box()['x'],page.locator('.app-sidebar').bounding_box()['width']-1)
   page.locator('#kp-live-ruling>summary').click();page.wait_for_selector('.live-rp-popover');self.assertTrue(page.evaluate('''()=>{const p=document.querySelector('.live-rp-popover'),r=p.getBoundingClientRect(),n=document.querySelector('#kp-compact-navigation').getBoundingClientRect(),x=Math.max(r.left+20,Math.min(r.right-20,n.left+100)),y=Math.max(r.top+10,Math.min(r.bottom-10,n.bottom-5));return p.contains(document.elementFromPoint(x,y));}'''));page.screenshot(path='/tmp/kp-navigation-popup-fixed.png');self.assertEqual(errors,[])
  finally:context.close()
 def test_rp_popup_starts_below_navigation(self):
  context=self.browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page()
  try:
   page.goto(self.url,timeout=90000);page.wait_for_selector('#kp-left-panel-toggle');page.locator('#kp-live-ruling>summary').click();page.wait_for_selector('.live-rp-popover');page.wait_for_function("document.querySelector('.live-rp-popover').getBoundingClientRect().top>=document.getElementById('kp-compact-navigation').getBoundingClientRect().bottom+7");page.screenshot(path='/tmp/kp-navigation-popup-final.png')
  finally:context.close()
if __name__=='__main__':unittest.main()
