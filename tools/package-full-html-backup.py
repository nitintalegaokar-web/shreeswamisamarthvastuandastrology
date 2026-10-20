"""Archive the current standalone HTML and available workspace reference/backup data."""
from pathlib import Path
import json,hashlib,zipfile,subprocess
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'desktop/package.json').read_text())['version']
files=[root/'index.html']
for folder in ['data','docs','Kundali Backup','Report Photos']:
 files.extend(p for p in (root/folder).rglob('*') if p.is_file() and not p.is_symlink())
tracked=subprocess.check_output(['git','ls-files','-z','vendor'],cwd=root).decode().split('\0')
files.extend(root/p for p in tracked if p and (root/p).is_file())
files=sorted(set(files))
manifest={'version':version,'sourceSHA256':hashlib.sha256((root/'index.html').read_bytes()).hexdigest(),'scope':'Standalone HTML, bundled data/source references, docs and available workspace backup folders. Browser/device-local data is not available here.','files':[{'file':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
archive=root/f'KP-MASTER-HTML-All-Data-{version}.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,'KP-MASTER/'+p.relative_to(root).as_posix())
 z.writestr('KP-MASTER/BACKUP-MANIFEST.json',json.dumps(manifest,indent=2))
 z.writestr('KP-MASTER/START-HERE.txt',f'KP MASTER {version} — HTML and available backup data\n\nExtract completely and open index.html in Chrome or Edge.\nThis is the unlocked HTML calculator for the owner. The separately distributed Customer app retains activation.\nAll available data/, vendor/ reference sources, docs/, Kundali Backup/ and Report Photos/ are included. The latter folders currently contain instructions only; no actual saved kundali or photo files are present in this workspace.\nBrowser-local notes, edited rules, saved charts, Android data and Windows user data cannot be read by this cloud build; export those from the installed software and retain that export separately.\nSigning keys, activation private keys and device activation state are not included.\nBACKUP-MANIFEST.json lists every archived source file and its SHA-256 checksum.\n')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for row in manifest['files']:assert hashlib.sha256(z.read('KP-MASTER/'+row['file'])).hexdigest()==row['sha256'],row['file']
print(json.dumps({'file':archive.name,'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
