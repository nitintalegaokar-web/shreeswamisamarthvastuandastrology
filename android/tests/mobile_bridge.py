"""Only Android adaptation checks; no changes to the approved calculator."""
from pathlib import Path
import sys,json,hashlib,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
from test_personal_predictions import PersonalPredictionTests as T
ROOT=Path(__file__).resolve().parents[2]
T.setUpClass();t=T();t.setUp()
try:
 p=t.page;p.set_viewport_size({'width':390,'height':844});before=p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')
 p.evaluate('window.KPAndroid={printReport:()=>window.mobilePrintCalled=true,saveFile:(name,mime,base64)=>window.mobileExport={name,mime,base64}}')
 p.evaluate((ROOT/'android/mobile.js').read_text());p.wait_for_selector('#kp-mobile-icons-toggle');p.locator('#kp-mobile-icons-toggle').click();assert p.locator('#kp-quick-tools').is_hidden();p.locator('#kp-mobile-icons-toggle').click();assert p.locator('#kp-quick-tools').is_visible();p.evaluate('window.print()');assert p.evaluate('mobilePrintCalled')
 p.evaluate('KPMobile.backup()');p.wait_for_function('window.mobileExport');backup=json.loads(p.evaluate('atob(mobileExport.base64)'));assert backup['format']=='KP-MASTER-mobile-backup' and backup['currentChart']
 p.evaluate('window.mobileExport=null;const a=document.createElement("a");a.download="chart.txt";a.href=URL.createObjectURL(new Blob(["my chart"],{type:"text/plain"}));document.body.append(a);a.click()')
 p.wait_for_function('window.mobileExport?.name==="chart.txt"');assert p.evaluate('atob(mobileExport.base64)')=='my chart'
 assert p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')==before
 p.locator('#quick-home').click();p.evaluate("KPChartStyle.setStyle('north')");p.wait_for_function("document.querySelector('#home .kp-mobile-planet-list')?.children.length===9")
 assert p.locator('#home .home-table-mount').first.evaluate('m=>m.scrollWidth>m.clientWidth')
 assert p.locator('#home .home-table-mount td').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=13
 assert p.locator('#home .kp-mobile-planet-list').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=14
 p.locator('#quick-event-promise').click();p.evaluate('KPEventPromise.refresh(true)')
 with p.expect_popup() as opened:p.locator('#ep-simple-preview').click()
 preview=opened.value;preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale')
 preview.set_viewport_size({'width':390,'height':844});preview.evaluate('window.KPAndroid={printReport:()=>{}}');preview.evaluate((ROOT/'android/mobile.js').read_text())
 assert preview.locator('body').evaluate('n=>n.scrollWidth>=740')
 import fitz
 pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
 assert len(pdf)==1 and 'Why?' in pdf[0].get_text()
 assert all(0<=b[0]<b[2]<=pdf[0].rect.width+1 and 0<=b[1]<b[3]<=pdf[0].rect.height+1 for b in pdf[0].get_text('blocks'))
 pdf.close();preview.close()
 assert p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')==before
 for edition in ['Owner','Customer']:
  with zipfile.ZipFile(ROOT/f'android/dist/KP-Master-{edition}-1.2.7.apk') as z:
   assert z.read('assets/index.html')==(ROOT/'index.html').read_bytes()
   assert 'classes.dex' in z.namelist()
 print('Mobile scrolling tables, nine North planets, A4 PDF bounds, exports, backup and unchanged calculator: PASS')
finally:t.tearDown();T.tearDownClass()
