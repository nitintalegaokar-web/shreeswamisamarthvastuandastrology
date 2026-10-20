"""Package owner and browser-profile activated customer web editions."""
from pathlib import Path
import json,zipfile,hashlib
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'desktop/package.json').read_text())['version']
html=(root/'index.html').read_text();rawkeys=json.loads((root/'android/assets/owner-public-keys.json').read_text());keys=[k if isinstance(k,str) else '-----BEGIN PUBLIC KEY-----\n'+k['der']+'\n-----END PUBLIC KEY-----' for k in rawkeys]
# These are the existing approved public verification keys, never private keys.
for edition in ['Owner','Customer']:
 source=html
 if edition=='Customer':
  head='<style>html.kp-web-locked body>:not(#kp-web-activation){display:none!important}</style>'
  source=source.replace('</head>',head+'</head>',1)
  scripts='<script id="kp-web-public-keys" type="application/json">'+json.dumps(keys)+'</script><script id="kp-web-activation-runtime">'+(root/'customer/web-activation.js').read_text()+'</script><script id="kp-customer-features">'+(root/'customer/features.js').read_text()+'</script>'
  at=source.rfind('</body>');source=source[:at]+scripts+source[at:]
 name=f'KP-MASTER-{edition}-Web-{version}.zip'
 with zipfile.ZipFile(root/name,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('index.html',source)
  z.write(root/'docs/KP-MASTER-User-Tutorial-1.2.9.pdf','docs/KP-MASTER-User-Tutorial-1.2.9.pdf')
  for folder in ['Kundali Backup','Report Photos']:
   for p in (root/folder).glob('*'):
    if p.is_file():z.write(p,str(p.relative_to(root)))
  z.writestr('READ-ME.txt','KP MASTER '+edition+' Web '+version+'\n\nExtract completely; open index.html in Chrome/Edge, or serve through HTTPS/localhost.\nThe PDF tutorial is in Help.\nFor iPhone, deploy the extracted files to an HTTPS website and open it in Safari; this ZIP is not an installable IPA. Native iPhone/Safari device verification has not been performed.\n'+('Owner is unlocked. Do not distribute it as a locked customer edition.\n' if edition=='Owner' else 'Customer activation is tied to this browser profile and site address. Save the System ID, obtain registration and purchase keys from Owner Activation, then apply them here. Clearing browser data can require new activation. This browser edition verifies signed package choices locally, but its source is inspectable; it is not equivalent to native distribution protection.\n'))
 print(name,(root/name).stat().st_size,hashlib.sha256((root/name).read_bytes()).hexdigest())
