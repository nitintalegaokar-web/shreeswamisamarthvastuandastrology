"""Real hosted registration, cookie sign-in, origin protection and logout."""
import importlib.util,json,tempfile,threading,unittest,sqlite3
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from protected.accounts import Accounts
from protected.server import Handler,ROOT
class AccountTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=tempfile.TemporaryDirectory();cls.db=Path(cls.folder.name)/'accounts.sqlite'
  class AccountHandler(Handler):
   def do_GET(self):
    if self.path=='/':
     self.respond('<html><head></head><body><div id="application"><div><button id="quick-basic">Birth details</button></div></div><script>window.KPOnlineAccountsHosted=true;</script><script src="/online-account.js"></script></body></html>','text/html');return
    super().do_GET()
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),AccountHandler);cls.server.accounts=Accounts(cls.db);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.server.server_port}';cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.thread.join();cls.server.server_close();cls.folder.cleanup()
 def test_registration_signin_logout_and_cookie_security(self):
  context=self.browser.new_context();p=context.new_page();p.goto(self.url);p.locator('#quick-online-account').click();p.get_by_role('button',name='Create account',exact=True).click();p.locator('[name=name]').fill('Test Astrologer');p.locator('[name=email]').fill('astrologer@example.com');p.locator('[name=password]').fill('StrongTestOnly421')
  with p.expect_navigation():p.locator('form>button').click()
  p.locator('#quick-online-account').click();expect(p.locator('#kp-account-dialog')).to_contain_text('Test Astrologer');cookie=next(c for c in context.cookies() if c['name']=='kp_account');self.assertTrue(cookie['httpOnly']);self.assertEqual(cookie['sameSite'],'Lax')
  raw=sqlite3.connect(self.db).execute('SELECT salt,digest FROM users').fetchone();self.assertNotIn('StrongTestOnly421',str(raw));self.assertEqual(len(raw[1]),64)
  token=cookie['value'];self.assertIsNotNone(self.server.accounts.user(token))
  with p.expect_navigation():p.get_by_role('button',name='Sign out',exact=True).click()
  self.assertIsNone(self.server.accounts.user(token));p.locator('#quick-online-account').click();p.locator('[name=email]').fill('astrologer@example.com');p.locator('[name=password]').fill('wrongPassword123');p.locator('form>button').click();expect(p.locator('[role=status]')).to_have_text('Email or password is incorrect.');p.locator('[name=password]').fill('StrongTestOnly421')
  with p.expect_navigation():p.locator('form>button').click()
  self.assertEqual(p.request.get(self.url+'/auth/me').json()['user']['email'],'astrologer@example.com');self.assertNotEqual(next(c['value'] for c in context.cookies() if c['name']=='kp_account'),token)
  for headers in [{},{'X-KP-Account':'1','Origin':'https://other.example'}]:self.assertEqual(p.request.post(self.url+'/auth/logout',data={},headers=headers).status,403)
  context.close()
 def test_validation_expiration_and_rate_limit(self):
  accounts=Accounts(Path(self.folder.name)/'other.sqlite')
  with self.assertRaises(ValueError):accounts.register({'name':'N','email':'bad','password':'1234567890'})
  token,user=accounts.register({'name':'N','email':'n@example.com','password':'LongEnough123'})
  with self.assertRaises(ValueError):accounts.register({'name':'N','email':'n@example.com','password':'LongEnough123'})
  with sqlite3.connect(accounts.path) as db:db.execute('UPDATE sessions SET expires=0')
  self.assertIsNone(accounts.user(token))
  for _ in range(15):accounts.limit('test')
  with self.assertRaises(ValueError):accounts.limit('test')

# Verify the account submit buttons coexist with the private bridge click handler.
import test_protected_server as protected
class HostedAccountBridgeTests(unittest.TestCase):
 setUpClass=classmethod(protected.ProtectedServerTests.setUpClass.__func__);tearDownClass=classmethod(protected.ProtectedServerTests.tearDownClass.__func__);setUp=protected.ProtectedServerTests.setUp;tearDown=protected.ProtectedServerTests.tearDown
 def test_online_account_controls_bypass_calculation_bridge(self):
  folder=tempfile.TemporaryDirectory();self.server.accounts=Accounts(Path(folder.name)/'online.sqlite');p=self.page
  p.locator('#quick-online-account').click();p.get_by_role('button',name='Create account',exact=True).click();p.locator('[name=name]').fill('Hosted User');p.locator('[name=email]').fill('hosted@example.com');p.locator('[name=password]').fill('HostedTestPass123')
  # Observe the real request rather than waiting for an unnecessary worker rebuild.
  with p.expect_response('**/auth/register') as registered:p.locator('#kp-account-dialog form>button').click()
  self.assertEqual(registered.value.status,200);self.assertEqual(p.request.get(self.url+'/auth/me').json()['user']['name'],'Hosted User');folder.cleanup()

if __name__=="__main__":unittest.main()
