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
- Rashi labels appear once in Marathi; bilingual labels contain one pair.
- Muhurta includes Panchang Nirnay: editable notes, two-person birth-strength checks, and Gopal / Abhijit / Goraj local times.
- Vedic charts use compact text labels; symbols appear only in the reference and planetary tables.
- Vedic Kundali has a separate Complete Vedic Report preview for printing all report pages.
- Transit Results retain planet names on screen and in reports.
- Rahu/Ketu use the Rashi lord in Theft Prediction.
'''
with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=9) as output:
    output.writestr('KP-MASTER/index.html', source)
    output.writestr('KP-MASTER/START-HERE.txt', readme)
with ZipFile(archive) as check:
    assert check.testzip() is None
    assert check.read('KP-MASTER/index.html') == source
print(f'Verified {archive.name}: {archive.stat().st_size} bytes')
print('SHA256:', hashlib.sha256(archive.read_bytes()).hexdigest())
