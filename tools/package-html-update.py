"""Package the self-contained HTML app for direct customer download."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

root = Path(__file__).resolve().parents[1]
version = json.loads((root / 'desktop/package.json').read_text())['version']
archive = root / f'KP-MASTER-Updated-HTML-{version}.zip'
source = (root / 'index.html').read_bytes()
readme = f'''KP MASTER {version} - Updated HTML

Extract this ZIP completely, then open KP-MASTER/index.html in Chrome or Edge.

Latest updates:
- Datewise ephemeris-style transit results for the selected planets and event.
- Star lord AND sub lord must be event significators; DBA supplies dates only in Event significators mode.
- One scan supplies daily positions and exact matching windows; no second scan/progress restart.
- The requested rule-summary panel and Exact matching periods button are removed.
- Best matching dates count unique selected planets simultaneously and retain all tied windows.
- Rahu and Ketu use their natal Rashi lord houses in PD support checks; exclusions have reasons.
- Existing historical searches, RP selection, reports, customer features and backups are retained.

Daily rows are snapshots at the displayed local time. Exact windows are available under Best matching dates.
The separate Windows activation tool clears its visible history once on the first 1.2.11 launch, keeping a private local recovery copy and existing signing keys.
Customer activation checks signed issue/expiry timestamps; dated licences end at 23:59:59.999 UTC on the selected expiry date. Customer apps recheck periodically while open.
'''
with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=9) as output:
    output.writestr('KP-MASTER/index.html', source)
    output.writestr('KP-MASTER/START-HERE.txt', readme)
with ZipFile(archive) as check:
    assert check.testzip() is None
    assert check.read('KP-MASTER/index.html') == source
print(f'Verified {archive.name}: {archive.stat().st_size} bytes')
print('SHA256:', hashlib.sha256(archive.read_bytes()).hexdigest())
