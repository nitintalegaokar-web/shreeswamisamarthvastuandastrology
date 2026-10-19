"""Collect verified current Windows/web builds; never substitute stale APKs."""
from pathlib import Path
import json,hashlib,shutil,datetime
root=Path(__file__).resolve().parents[1]
files=[('Windows Customer','desktop/dist/setup/KP-Master-Setup-1.2.8-x64.exe','KP-Master-Customer-Setup-1.2.8-x64.exe'),('Windows Owner','desktop/owner-edition/dist/setup/KP-Master-Owner-Setup-1.2.8-x64.exe','KP-Master-Owner-Setup-1.2.8-x64.exe'),('Windows Owner Activation','desktop/owner/dist/setup/KP-Master-Owner-Activation-Setup-1.2.8-x64.exe','KP-Master-Owner-Activation-Setup-1.2.8-x64.exe')]
artifacts=[]
for edition,source,name in files:
 shutil.copyfile(root/source,root/name)
 artifacts.append({'edition':edition,'file':name})
# Keep the existing customer download path updated as well.
shutil.copyfile(root/'KP-Master-Customer-Setup-1.2.8-x64.exe',root/'KP-Master-Setup-1.2.8-x64.exe')
for edition in ['Customer','Owner']:artifacts.append({'edition':edition+' Web','file':f'KP-MASTER-{edition}-Web-1.2.8.zip'})
artifacts.append({'edition':'Tutorial PDF','file':'docs/KP-MASTER-User-Tutorial-1.2.8.pdf'})
for item in artifacts:
 p=root/item['file'];item.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
meta={'version':'1.2.8','builtAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':hashlib.sha256((root/'index.html').read_bytes()).hexdigest(),'artifacts':artifacts,'android':{'status':'blocked','reason':'Original release.p12 and store-password.txt signing files are unavailable; the released signing identity was not replaced.','expectedSigningCertificateSHA256':(root/'android/signing-certificate.sha256').read_text().strip(),'sourceVersionCode':10212,'oldAPKsIncluded':False},'validation':{'unitTestFilesPassed':29,'androidLicenseAssertionsPassed':20,'browserChecks':['gemstone exceptions and colour legend','responsive RP location and complete event houses','RP A4 print borders','expanded report evidence and repeating page frame','English/Marathi Vedic-only symbol legend','Help PDF view and download','owner package selection and customer feature restrictions','signed customer web activation and changed-claims rejection','clipped planet list hover in tables and modal dialogs'],'windowsInstallerPayloadParity':True,'windowsAsarParity':True,'windowsInstallationExecuted':False}}
fresh_path=root/'KP-MASTER-APK-Fresh-Install-1.2.8.json'
if fresh_path.exists():
 fresh=json.loads(fresh_path.read_text())
 if fresh.get('sourceSHA256')==meta['sourceSHA256']:
  meta['android']={'status':'fresh-install-built','version':fresh['version'],'versionCode':fresh['versionCode'],'files':fresh['files'],'signingCertificateSHA256':fresh['signingCertificateSHA256'],'requiresUninstallOfOldApps':True,'sourceParityVerified':True,'physicalDeviceTested':False}
(root/'KP-MASTER-UPDATED-1.2.8.json').write_text(json.dumps(meta,indent=2)+'\n')
(root/'KP-MASTER-UPDATED-1.2.8-SHA256SUMS.txt').write_text(''.join(p['sha256']+'  '+p['file']+'\n' for p in artifacts))
print(json.dumps({'version':'1.2.8','artifacts':[(a['file'],a['bytes']) for a in artifacts],'android':'blocked: original signing files missing'}))
