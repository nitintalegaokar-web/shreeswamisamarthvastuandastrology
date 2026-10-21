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
 p.evaluate((ROOT/'android/mobile.js').read_text());p.wait_for_selector('#menu-toggle');assert p.locator('#kp-compact-navigation').is_hidden();p.locator('#menu-toggle').click();assert p.locator('.app-sidebar').is_visible();p.locator('.sidebar-close').click();assert p.locator('.app-sidebar').is_hidden();assert p.locator('#kp-mobile-icons-toggle').count()==0;p.evaluate("KPCompactNavigation.activate('event-promise');window.print()");assert p.evaluate('mobilePrintCalled')
 p.evaluate('KPMobile.previewSinglePage()');p.wait_for_selector('#kp-mobile-kundali-preview[open]');p.wait_for_function("document.querySelector('#kp-mobile-kundali-preview iframe').contentDocument.querySelector('.kp-a4-page')?.dataset.a4Scale");p.locator('[data-preview-close]').click()
 p.evaluate('KPMobile.backup()');p.wait_for_function('window.mobileExport');backup=json.loads(p.evaluate('atob(mobileExport.base64)'));assert backup['format']=='KP-MASTER-mobile-backup' and backup['currentChart']
 p.evaluate('window.mobileExport=null;const a=document.createElement("a");a.download="chart.txt";a.href=URL.createObjectURL(new Blob(["my chart"],{type:"text/plain"}));document.body.append(a);a.click()')
 p.wait_for_function('window.mobileExport?.name==="chart.txt"');assert p.evaluate('atob(mobileExport.base64)')=='my chart'
 assert p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')==before
 p.evaluate("KPCompactNavigation.activate('home')");p.evaluate("KPChartStyle.setStyle('north')");p.wait_for_function("(()=>{const chart=document.querySelector('#home-kundali'),list=document.querySelector('#home .kp-mobile-planet-list');const ids=new Set([...chart.querySelectorAll('svg text[data-planet]')].map(n=>n.dataset.planet));return ids.size>=9&&list?.children.length===ids.size;})()")
 assert p.locator('#home .home-table-mount').first.evaluate('m=>m.scrollWidth>m.clientWidth')
 assert p.locator('#home .home-table-mount td').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=13
 assert p.locator('#home .kp-mobile-planet-list').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=14
 p.evaluate("KPCompactNavigation.activate('event-promise')");p.evaluate('KPEventPromise.refresh(true)')
 with p.expect_popup() as opened:p.locator('#ep-simple-preview').click()
 preview=opened.value;preview.wait_for_function('document.querySelector(".kp-a4-page")?.dataset.a4Scale')
 preview.set_viewport_size({'width':390,'height':844});preview.evaluate('window.KPAndroid={printReport:()=>{}}');preview.evaluate((ROOT/'android/mobile.js').read_text())
 assert preview.locator('body').evaluate('n=>n.scrollWidth>=740')
 import fitz
 pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf')
 assert len(pdf)>=1 and 'Why?' in ''.join(page.get_text() for page in pdf)
 assert all(0<=b[0]<b[2]<=sheet.rect.width+1 and 0<=b[1]<b[3]<=sheet.rect.height+1 for sheet in pdf for b in sheet.get_text('blocks'))
 pdf.close();preview.close()
 assert p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')==before
 for edition in ['Owner','Customer']:
  with zipfile.ZipFile(ROOT/('android/dist/KP-Master-'+edition+'-'+json.loads((ROOT/'desktop/package.json').read_text())['version']+'.apk')) as z:
   packaged=z.read('assets/index.html');startup=b'<style id="kp-android-startup">'+(ROOT/'android/startup.css').read_bytes()+b'</style>';bridge=b'<script id="kp-android-mobile-bridge" src="mobile.js"></script>';assert startup in packaged and bridge in packaged;normalized=packaged.replace(startup,b'',1).replace(bridge,b'',1); normalized=normalized.replace(b'<script id="kp-customer-demo" src="demo-ui.js"></script><script id="kp-customer-features" src="features.js"></script>',b'',1).replace(b'function refresh(){if(window.KPCustomerDemo&&!KPCustomerDemo.permitMatchRefresh())return null;if(!initialized)return null;try{data=calculate();',b'function refresh(){if(!initialized)return null;try{data=calculate();',1);assert normalized==(ROOT/'index.html').read_bytes()
   assert 'classes.dex' in z.namelist()
 print('Mobile scrolling tables, visible North planets, A4 PDF bounds, exports, backup and unchanged calculator: PASS')
finally:t.tearDown();T.tearDownClass()
