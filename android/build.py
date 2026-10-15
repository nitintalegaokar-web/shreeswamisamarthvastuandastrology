"""Build the approved single-file calculator as two signed, offline Android APKs."""
from pathlib import Path
import os,subprocess,shutil,json,hashlib,secrets,zipfile
ROOT=Path(__file__).resolve().parents[1];APP=ROOT/'android';SDK=Path(os.environ.get('ANDROID_SDK_ROOT','/workspace/kp-android-toolchain/sdk'));TOOLS=SDK/'build-tools/35.0.0';API=SDK/'platforms/android-35/android.jar';VERSION='1.2.5'
KEYS=Path(os.environ.get('KP_ANDROID_SIGNING_DIR','/workspace/kp-master-android-signing'));KEYS.mkdir(exist_ok=True,mode=0o700);store=KEYS/'release.p12';password_file=KEYS/'store-password.txt'
def run(*args):subprocess.run([str(x) for x in args],check=True,cwd=APP)
if not store.exists():
 if (APP/'signing-certificate.sha256').exists():raise RuntimeError('Restore the original private Android signing directory before building an upgrade. A new signing identity must not replace the released app identity.')
 password_file.write_text(secrets.token_urlsafe(36));password_file.chmod(0o600)
 run('java','--module','java.base/sun.security.tools.keytool.Main','-genkeypair','-keystore',store,'-storetype','PKCS12','-storepass:file',password_file,'-alias','kp-master-android','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=KP MASTER Android, O=KP MASTER, C=IN')
 store.chmod(0o600)
cert=KEYS/'public-certificate.der'
run('java','--module','java.base/sun.security.tools.keytool.Main','-exportcert','-keystore',store,'-storepass:file',password_file,'-alias','kp-master-android','-file',cert)
certificateHash=hashlib.sha256(cert.read_bytes()).hexdigest()
pin=APP/'signing-certificate.sha256'
if pin.exists() and pin.read_text().strip()!=certificateHash:raise RuntimeError('The Android signing certificate differs from the released app. Restore the original signing key.')
pin.write_text(certificateHash+'\n')
run('node',APP/'tools/public-keys.cjs')
(APP/'dist').mkdir(exist_ok=True)
source=(ROOT/'index.html').read_bytes();sourceHash=hashlib.sha256(source).hexdigest()
for edition in ['owner','customer']:
 b=APP/'build'/edition;b.mkdir(parents=True,exist_ok=True);assets=b/'assets';assets.mkdir(exist_ok=True);(assets/'index.html').write_bytes(source);shutil.copy(APP/'mobile.js',assets/'mobile.js');shutil.copy(APP/'assets/owner-public-keys.json',assets/'owner-public-keys.json')
 config=b/'BuildConfig.java';config.write_text('package in.kpmaster.mobile; public final class BuildConfig {public static final boolean OWNER='+str(edition=='owner').lower()+';public static final String APP_ID="in.kpmaster.mobile.'+edition+'";public static final String VERSION="'+VERSION+'";}')
 manifest=b/'AndroidManifest.xml';manifest.write_text((APP/'AndroidManifest.xml').read_text().replace('android:label="KP MASTER"','android:label="KP MASTER '+edition.title()+'"'))
 run(TOOLS/'aapt2','compile','--dir',APP/'res','-o',b/'res.zip')
 run(TOOLS/'aapt2','link','-o',b/'unsigned.apk','--manifest',manifest,'-I',API,'--rename-manifest-package','in.kpmaster.mobile.'+edition,'--version-name',VERSION,'--version-code','10205','--min-sdk-version','28','--target-sdk-version','35',b/'res.zip')
 classes=b/'classes';classes.mkdir(exist_ok=True)
 run('java','--module','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-bootclasspath',str(TOOLS/'core-lambda-stubs.jar')+os.pathsep+str(API),'-classpath',APP/'vendor/bcprov-jdk15to18-1.81.jar','-d',classes,config,*sorted((APP/'src').rglob('*.java')))
 dex=b/'dex';dex.mkdir(exist_ok=True)
 run('java','-Xmx2g','-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.R8','--release','--min-api','28','--lib',API,'--pg-conf',APP/'shrink-rules.pro','--output',dex,*classes.rglob('*.class'),APP/'vendor/bcprov-jdk15to18-1.81.jar')
 with zipfile.ZipFile(b/'unsigned.apk','a',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in dex.glob('*.dex'):z.write(p,p.name)
  for p in assets.iterdir():z.write(p,'assets/'+p.name)
 run(TOOLS/'zipalign','-f','-p','4',b/'unsigned.apk',b/'aligned.apk')
 output=APP/'dist'/('KP-Master-'+edition.title()+'-'+VERSION+'.apk')
 run(TOOLS/'apksigner','sign','--ks',store,'--ks-key-alias','kp-master-android','--ks-pass','file:'+str(password_file),'--out',output,b/'aligned.apk')
 print(edition,output.name,output.stat().st_size,'bytes',flush=True)
(APP/'dist/build-manifest.json').write_text(json.dumps({'version':VERSION,'minimumAndroid':'9 (API 28)','targetAndroidAPI':35,'sourceSHA256':sourceHash,'mobileBridgeSHA256':hashlib.sha256((APP/'mobile.js').read_bytes()).hexdigest(),'signingCertificateSHA256':certificateHash,'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((APP/'dist').glob('*.apk'))]},indent=2)+'\n')
