"""Preserve supplied Marathi fields literally and pair them with reviewed English translations."""
from pathlib import Path
import hashlib,json,re,shutil,sys
root=Path(__file__).resolve().parents[1];src=Path(sys.argv[1]);dest=root/'data/planet-karkatva-2026-10-18';en=json.loads((dest/'english.json').read_text());ids={'Sun':'Su','Moon':'Mo','Mars':'Ma','Mercury':'Me','Jupiter':'Ju','Venus':'Ve','Saturn':'Sa','Rahu':'Ra','Ketu':'Ke'};entries={};current=None
for line in src.read_text(encoding='utf-8-sig').splitlines():
 line=line.strip()
 if not line:continue
 m=re.fullmatch(r'(.+?)\s*\((\w+)\)',line)
 if m:
  current=ids[m[2]];entries[current]={'mrName':m[1],'enName':m[2],'mr':[],'en':en[current]};continue
 label,value=line.split(':',1);entries[current]['mr'].append({'label':label.strip(),'text':value.strip()})
assert len(entries)==9
for item in entries.values():assert len(item['mr'])==len(item['en'])==6
obj={'metadata':{'filename':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'languages':['marathi','english'],'policy':'Original Marathi preserved; English values translated from the supplied Marathi. Reference information only.'},'entries':entries}
shutil.copyfile(src,dest/'Planets karkatva.txt');(dest/'content.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');payload=json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');(root/'vendor/interface/planet-karkatva-data.js').write_text('/* Uploaded Marathi source and English translation. */\nglobalThis.KPPlanetKarkatvaData='+payload+';\n');print('Imported 9 planets, 54 source fields, 54 English translations.')
