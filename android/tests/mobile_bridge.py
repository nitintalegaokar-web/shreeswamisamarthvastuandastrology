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
 p.evaluate((ROOT/'android/mobile.js').read_text());p.evaluate('window.print()');assert p.evaluate('mobilePrintCalled')
 p.evaluate('KPMobile.backup()');p.wait_for_function('window.mobileExport');backup=json.loads(p.evaluate('atob(mobileExport.base64)'));assert backup['format']=='KP-MASTER-mobile-backup' and backup['currentChart']
 p.evaluate('window.mobileExport=null;const a=document.createElement("a");a.download="chart.txt";a.href=URL.createObjectURL(new Blob(["my chart"],{type:"text/plain"}));document.body.append(a);a.click()')
 p.wait_for_function('window.mobileExport?.name==="chart.txt"');assert p.evaluate('atob(mobileExport.base64)')=='my chart'
 assert p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')==before
 for edition in ['Owner','Customer']:
  with zipfile.ZipFile(ROOT/f'android/dist/KP-Master-{edition}-1.2.3.apk') as z:
   assert z.read('assets/index.html')==(ROOT/'index.html').read_bytes()
   assert 'classes.dex' in z.namelist()
 print('Mobile file export, PDF bridge, backup and unchanged APK calculator assets: PASS')
finally:t.tearDown();T.tearDownClass()
