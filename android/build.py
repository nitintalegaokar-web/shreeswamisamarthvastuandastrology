"""Build the approved single-file calculator as two signed, offline Android APKs."""
from pathlib import Path
import os,subprocess,shutil,json,hashlib,secrets,zipfile,sys
ROOT=Path(__file__).resolve().parents[1];APP=ROOT/'android';SDK=Path(os.environ.get('ANDROID_SDK_ROOT','/workspace/kp-android-toolchain/sdk'));TOOLS=SDK/'build-tools/35.0.0';API=SDK/'platforms/android-35/android.jar';VERSION=json.loads((ROOT/'desktop/package.json').read_text())['version'];VERSION_CODE=10217
FRESH='--fresh-install' in sys.argv
KEYS=Path(os.environ.get('KP_ANDROID_SIGNING_DIR','/workspace/kp-master-android-signing-fresh-128' if FRESH else '/workspace/kp-master-android-signing'));KEYS.mkdir(exist_ok=True,mode=0o700);store=KEYS/'release.p12';password_file=KEYS/'store-password.txt'
def run(*args):subprocess.run([str(x) for x in args],check=True,cwd=APP)
if not store.exists():
 if not FRESH and (APP/'signing-certificate.sha256').exists():raise RuntimeError('Restore the original private Android signing directory before building an upgrade. A new signing identity must not replace the released app identity.')
 password_file.write_text(secrets.token_urlsafe(36));password_file.chmod(0o600)
 run('java','--module','java.base/sun.security.tools.keytool.Main','-genkeypair','-keystore',store,'-storetype','PKCS12','-storepass:file',password_file,'-alias','kp-master-android','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=KP MASTER Android, O=KP MASTER, C=IN')
 store.chmod(0o600)
cert=KEYS/'public-certificate.der'
run('java','--module','java.base/sun.security.tools.keytool.Main','-exportcert','-keystore',store,'-storepass:file',password_file,'-alias','kp-master-android','-file',cert)
certificateHash=hashlib.sha256(cert.read_bytes()).hexdigest()
pin=APP/('fresh-install-signing-certificate.sha256' if FRESH else 'signing-certificate.sha256')
if pin.exists() and pin.read_text().strip()!=certificateHash:raise RuntimeError('The Android signing certificate differs from the released app. Restore the original signing key.')
pin.write_text(certificateHash+'\n')
run('node',APP/'tools/public-keys.cjs')
(APP/'dist').mkdir(exist_ok=True)
source=(ROOT/'index.html').read_bytes();sourceHash=hashlib.sha256(source).hexdigest()
startup=b'<style id="kp-android-startup">'+(APP/'startup.css').read_bytes()+b'</style>'
bridge=b'<script id="kp-android-mobile-bridge" src="mobile.js"></script>'
head=source.find(b'</head>');body=source.rfind(b'</body>')
if head<0 or body<head:raise RuntimeError('The application document boundaries are missing.')
packagedSource=source[:head]+startup+source[head:body]+bridge+source[body:]
assert packagedSource.replace(startup,b'',1).replace(bridge,b'',1)==source

for edition in ['owner','customer']:
 b=APP/'build'/edition;b.mkdir(parents=True,exist_ok=True);assets=b/'assets';assets.mkdir(exist_ok=True);(assets/'index.html').write_bytes(packagedSource if edition=='owner' else packagedSource.replace(bridge,bridge+b'<script id="kp-customer-demo-script" src="demo-ui.js"></script><script id="kp-customer-features" src="features.js"></script>',1).replace(b'function refresh(){if(!initialized)return null;try{data=calculate();',b'function refresh(){if(window.KPCustomerDemo&&!KPCustomerDemo.permitMatchRefresh())return null;if(!initialized)return null;try{data=calculate();',1));shutil.copy(APP/'mobile.js',assets/'mobile.js');shutil.copy(APP/'assets/owner-public-keys.json',assets/'owner-public-keys.json')
 shutil.copy(ROOT/'desktop/licensing/features.json',assets/'features.json')
 portrait_assets=assets/'assets';portrait_assets.mkdir(exist_ok=True)
 shutil.copy(ROOT/'assets/about-portrait.jpg',portrait_assets/'about-portrait.jpg')
 if edition=='customer':
  shutil.copy(ROOT/'customer/demo-ui.js',assets/'demo-ui.js')
  shutil.copy(ROOT/'customer/features.js',assets/'features.js')
 config=b/'BuildConfig.java';config.write_text('package in.kpmaster.mobile; public final class BuildConfig {public static final boolean OWNER='+str(edition=='owner').lower()+';public static final String APP_ID="in.kpmaster.mobile.'+edition+'";public static final String VERSION="'+VERSION+'";}')
 manifest=b/'AndroidManifest.xml';manifest.write_text((APP/'AndroidManifest.xml').read_text().replace('android:label="KP MASTER"','android:label="KP MASTER '+edition.title()+'"').replace('__KP_SHARE_AUTHORITY__','in.kpmaster.mobile.'+edition+'.share'))
 run(TOOLS/'aapt2','compile','--dir',APP/'res','-o',b/'res.zip')
 run(TOOLS/'aapt2','link','-o',b/'unsigned.apk','--manifest',manifest,'-I',API,'--rename-manifest-package','in.kpmaster.mobile.'+edition,'--version-name',VERSION,'--version-code',str(VERSION_CODE),'--min-sdk-version','28','--target-sdk-version','35',b/'res.zip')
 classes=b/'classes';classes.mkdir(exist_ok=True)
 run('java','--module','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-bootclasspath',str(TOOLS/'core-lambda-stubs.jar')+os.pathsep+str(API),'-classpath',APP/'vendor/bcprov-jdk15to18-1.81.jar','-d',classes,config,*sorted((APP/'src').rglob('*.java')))
 dex=b/'dex';dex.mkdir(exist_ok=True)
 run('java','-Xmx2g','-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.R8','--release','--min-api','28','--lib',API,'--pg-conf',APP/'shrink-rules.pro','--output',dex,*classes.rglob('*.class'),APP/'vendor/bcprov-jdk15to18-1.81.jar')
 with zipfile.ZipFile(b/'unsigned.apk','a',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in dex.glob('*.dex'):z.write(p,p.name)
  for p in assets.rglob('*'):
   if p.is_file():z.write(p,'assets/'+p.relative_to(assets).as_posix())
 run(TOOLS/'zipalign','-f','-p','4',b/'unsigned.apk',b/'aligned.apk')
 output=APP/'dist'/('KP-Master-'+edition.title()+'-'+VERSION+'.apk')
 run(TOOLS/'apksigner','sign','--ks',store,'--ks-key-alias','kp-master-android','--ks-pass','file:'+str(password_file),'--out',output,b/'aligned.apk')
 print(edition,output.name,output.stat().st_size,'bytes',flush=True)
(APP/'dist/build-manifest.json').write_text(json.dumps({'version':VERSION,'freshInstall':FRESH,'minimumAndroid':'9 (API 28)','targetAndroidAPI':35,'sourceSHA256':sourceHash,'packagedHTMLSHA256':hashlib.sha256(packagedSource).hexdigest(),'versionCode':VERSION_CODE,'mobileBridgeSHA256':hashlib.sha256((APP/'mobile.js').read_bytes()).hexdigest(),'signingCertificateSHA256':certificateHash,'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((APP/'dist').glob('*'+VERSION+'.apk'))]},indent=2)+'\n')
