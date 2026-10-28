"""Dependency-free Android SDK build. Requires SDK platform 35 and build-tools 35.0.0."""
from pathlib import Path
import os,subprocess,zipfile
root=Path(__file__).resolve().parent
sdk=Path(os.environ['KP_ANDROID_SDK'])
tools=sdk/'build-tools/35.0.0'
if not (tools/'aapt2').exists():tools=sdk/'build-tools/android-15'
jar=sdk/'platforms/android-35/android.jar'
if not jar.exists():jar=sdk/'platform/android-35/android.jar'
# Official zip folder names can vary; resolve only the installed SDK artifacts.
if not (tools/'aapt2').exists():tools=next((sdk/'build-tools').glob('*/aapt2')).parent
if not jar.exists():jar=next((sdk/'platform').glob('*/android.jar'))
build=root/'build';build.mkdir(exist_ok=True)
def run(*args):subprocess.run([str(x) for x in args],check=True,cwd=root)
run('python3',root/'stage.py')
for d in ['gen','classes','dex']:(build/d).mkdir(exist_ok=True)
run(tools/'aapt2','compile','--dir',root/'res','-o',build/'resources.zip')
manifest=root/'AndroidManifest.xml'
if os.environ.get('KP_ANDROID_DEBUG')=='1':
 manifest=build/'DebugManifest.xml'
 manifest.write_text((root/'AndroidManifest.xml').read_text().replace('<application ', '<application android:debuggable="true" '))
run(tools/'aapt2','link','-o',build/'unsigned.apk','-I',jar,'--manifest',manifest,'--java',build/'gen','--auto-add-overlay','-R',build/'resources.zip')
run('javac','--release','8','-classpath',jar,'-d',build/'classes',*sorted((root/'src').rglob('*.java')),*sorted((build/'gen').rglob('*.java')))
run(tools/'d8','--lib',jar,'--min-api','26','--output',build/'dex',*sorted((build/'classes').rglob('*.class')))
with zipfile.ZipFile(build/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((build/'assets').iterdir()):z.write(p,'assets/'+p.name)
 for p in sorted((build/'dex').glob('*.dex')):z.write(p,p.name)
run(tools/'zipalign','-p','-f','4',build/'unsigned.apk',build/'aligned.apk')
key=Path(os.environ['KP_ANDROID_KEYSTORE']);password=Path(os.environ['KP_ANDROID_PASSWORD_FILE'])
output=(build/'KP-Master-test.apk') if os.environ.get('KP_ANDROID_DEBUG')=='1' else root.parent/'downloads/KP-Master-Android-1.4.2.apk'
run(tools/'apksigner','sign','--ks',key,'--ks-key-alias','kp-master','--ks-pass','file:'+str(password),'--v4-signing-enabled','false','--out',output,build/'aligned.apk')
run(tools/'apksigner','verify','--verbose','--print-certs',output)
print('Built',output)
