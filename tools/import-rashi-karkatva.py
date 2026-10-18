"""Import supplied sign content without treating the duplicate Gemini as Cancer."""
from pathlib import Path
import re,json,hashlib,shutil,sys
root=Path(__file__).resolve().parents[1];src=Path(sys.argv[1]);dest=root/'data/rashi-karkatva-2026-10-18';en=json.loads((dest/'english.json').read_text());signs=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];blocks=[];current=None
for line in src.read_text(encoding='utf-8-sig').splitlines():
 line=line.strip()
 if not line:continue
 m=re.fullmatch(r'(.+?)\s*\((\w+)\)',line)
 if m:
  current={'sign':signs.index(m[2])+1,'mrName':m[1],'enName':m[2],'mr':[]};blocks.append(current);continue
 label,value=line.split(':',1);current['mr'].append({'label':label.strip(),'text':value.strip()})
original_missing=[name for i,name in enumerate(signs,1) if not any(e['sign']==i for e in blocks)]
supplements=[]
if len(sys.argv)>2:
 supplement=Path(sys.argv[2]);extra=supplement.read_text(encoding='utf-8-sig').splitlines();m=re.fullmatch(r'(.+?)\s*\((\w+)\)',extra[0].strip());item={'sign':signs.index(m[2])+1,'mrName':m[1],'enName':m[2],'mr':[]}
 for line in extra[1:]:
  if not line.strip():continue
  label,value=line.split(':',1);item['mr'].append({'label':label.strip(),'text':value.strip()})
 blocks.append(item);supplements.append({'filename':supplement.name,'sha256':hashlib.sha256(supplement.read_bytes()).hexdigest(),'source':'Exact Cancer text supplied by user in chat'})
entries={};duplicates=[]
for e in blocks:
 k=str(e['sign']);assert len(e['mr'])==10
 if k in entries:
  assert entries[k]['mr']==e['mr'],'Different duplicate must be reviewed';duplicates.append(e['enName']);continue
 e['en']=en[k];assert len(e['en'])==10;entries[k]=e
missing=[name for i,name in enumerate(signs,1) if str(i) not in entries]
obj={'metadata':{'filename':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'languages':['marathi','english'],'duplicates':duplicates,'missing':missing,'originalMissing':original_missing,'supplements':supplements,'policy':'Source Marathi preserved. Identical Gemini duplicate collapsed, not relabelled as Cancer. Cancer text supplied separately by the user is preserved as a supplement. Missing signs are never inferred.'},'entries':entries}
shutil.copyfile(src,dest/'RAshi Karkatva.txt');(dest/'content.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');payload=json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');(root/'vendor/interface/rashi-karkatva-data.js').write_text('/* Uploaded Rashi text and English translation. */\nglobalThis.KPRashiKarkatvaData='+payload+';\n');print('Imported signs:',len(entries),'missing:',missing,'duplicates:',duplicates)
