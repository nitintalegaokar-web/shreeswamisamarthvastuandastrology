from pathlib import Path
from urllib.request import urlopen
import hashlib,zipfile,xml.etree.ElementTree as ET,json,os,subprocess
r=Path(os.environ.get('KP_ANDROID_TOOLCHAIN_DIR','/workspace/kp-android-toolchain'));r.mkdir(exist_ok=True)
if (r/'sdk/platforms/android-35/android.jar').exists() and (r/'sdk/build-tools/35.0.0/apksigner').exists():
 print('Android SDK platform 35 and build-tools 35.0.0 already installed.');raise SystemExit(0)
if (r/'sdk/cmdline-tools/latest/bin/android').exists():
 env=os.environ.copy();env.update({'ANDROID_USER_HOME':str(r/'user'),'XDG_DATA_HOME':str(r/'data'),'XDG_CACHE_HOME':'/tmp/kp-android-cache'})
 subprocess.run([str(r/'sdk/cmdline-tools/latest/bin/android'),'--no-metrics','--sdk='+str(r/'sdk'),'sdk','install','platforms;android-35','build-tools;35.0.0','platform-tools'],env=env,check=True)
 raise SystemExit(0)
xml=ET.fromstring(urlopen('https://dl.google.com/android/repository/repository2-1.xml').read())
pkg=next(e for e in xml.iter('remotePackage') if e.get('path')=='cmdline-tools;latest')
a=next(a for a in pkg.findall('./archives/archive') if a.findtext('host-os')=='linux').find('complete');name=a.findtext('url');p=r/name
with urlopen('https://dl.google.com/android/repository/'+name,timeout=120) as inp,p.open('wb') as out:
 while b:=inp.read(1048576):out.write(b)
assert hashlib.sha1(p.read_bytes()).hexdigest()==a.findtext('checksum')
with zipfile.ZipFile(p) as z:z.extractall(r/'sdk'/'cmdline-tools'/'unpacked')
(r/'sdk'/'cmdline-tools'/'unpacked'/'cmdline-tools').rename(r/'sdk'/'cmdline-tools'/'latest')
for f in (r/'sdk'/'cmdline-tools'/'latest'/'bin').iterdir():f.chmod(0o755)
(r/'sdk-tools-source.json').write_text(json.dumps({'url':'https://dl.google.com/android/repository/'+name,'sha1':a.findtext('checksum')},indent=2))
print('Official Android tools downloaded and checksum verified',flush=True)

env=os.environ.copy();env.update({'ANDROID_USER_HOME':str(r/'user'),'XDG_DATA_HOME':str(r/'data'),'XDG_CACHE_HOME':'/tmp/kp-android-cache'})
subprocess.run([str(r/'sdk/cmdline-tools/latest/bin/android'),'--no-metrics','--sdk='+str(r/'sdk'),'sdk','install','platforms;android-35','build-tools;35.0.0','platform-tools'],env=env,check=True)
