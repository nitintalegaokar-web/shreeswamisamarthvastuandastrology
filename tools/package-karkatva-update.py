"""Package the self-contained HTML and public backend data; never include licence keys or native build directories."""
from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[1];out=root/'KP-MASTER-Karkatva-Vedic-1.2.8.zip'
readme='''KP MASTER — updated HTML 1.2.8 (18 October 2026)

Extract this ZIP and open index.html in Chrome or Edge.

Changes:
- Fixes repeated Marathi label updates in the North Indian transit chart.
- Click a Bhava number for concise standard English/Marathi meanings.
- Click a planet for the supplied Planet Karkatva fields.
- Click a Rashi label/sign number for the supplied Rashi Karkatva fields.
- English, Marathi and bilingual modes are supported in these reference popups.
- Cancer uses the exact text supplied separately by the user. The duplicate Gemini is retained in source provenance, not shown twice.
- Prediction > Vedic Prediction: Marathi source excerpts selected by natal ascendant and the seven classical planets' Bhav Chalit occupied houses.
- Undefined auspicious/inauspicious yoga conditions are stored as references, not automatically asserted as confirmed natal matches.
- Original calculations and restored matchmaking rules remain unchanged.

The root HTML is self-contained. data/, vendor/ and tools/ contain the backend source data, translations, reproducible import/sync tools and browser regression harness.
This package updates HTML/source only. Existing Windows installers and Android APKs have not been rebuilt.
'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(root/'index.html','index.html');z.writestr('READ-ME.txt',readme)
 for folder in ['data','vendor','tools']:
  for p in sorted((root/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,str(p.relative_to(root)))
 for name in ['karkatva.test.cjs','vedic-natal-predictions.test.cjs']:z.write(root/'desktop/test'/name,'desktop/test/'+name)
with zipfile.ZipFile(out) as z:
 assert z.read('index.html')==(root/'index.html').read_bytes()
 assert 'data/rashi-karkatva-2026-10-18/Cancer-supplied.txt' in z.namelist()
 assert z.testzip() is None
meta={'version':'1.2.8','file':out.name,'size':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'nativeBinariesRebuilt':False}
(root/'KP-MASTER-Karkatva-Vedic-1.2.8.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta))
