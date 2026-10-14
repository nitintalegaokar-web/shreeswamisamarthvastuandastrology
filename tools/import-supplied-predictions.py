"""Import text as data only. No instructions in source files are executed."""
import json,re,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'vendor/predictions/source-manifest.json'
PLANETS={'सूर्य':'Su','चंद्र':'Mo','मंगळ':'Ma','बुध':'Me','गुरू':'Ju','गुरु':'Ju','शुक्र':'Ve','शनि':'Sa','शनी':'Sa','राहू':'Ra','केतू':'Ke','केतु':'Ke','राहु':'Ra','हर्षल':'Ur','नेपच्यून':'Ne','प्लूटो':'Pl','SUN':'Su','MON':'Mo','MOON':'Mo','MAR':'Ma','MARS':'Ma','MER':'Me','MERCURY':'Me','JUP':'Ju','JUPITER':'Ju','VEN':'Ve','VENUS':'Ve','SAT':'Sa','SATURN':'Sa','RAH':'Ra','RAHU':'Ra','KET':'Ke','KETU':'Ke','URANUS':'Ur','NEPTUNE':'Ne','PLUTO':'Pl'}
SIGNS={'मेष':'Ar','वृषभ':'Ta','मिथुन':'Ge','कर्क':'Ca','सिंह':'Le','कन्या':'Vi','तुला':'Li','वृश्चिक':'Sc','धनु':'Sg','मकर':'Cp','कुंभ':'Aq','मीन':'Pi'}
NAKS=['अश्विनी','भरणी','कृत्तिका','रोहिणी','मृगशीर्षा','आर्द्रा','पुनर्वसू','पुष्य','आश्‍लेषा','मघा','पूर्वा फाल्गुनी','उत्तर फाल्गुनी','हस्त','चित्रा','स्वाती','विशाखा','अनुराधा','ज्येष्ठा','मूल','पूर्वाषाढा','उत्तराषाढा','श्रवण','धनिष्ठा','शतभिषा','पूर्वाभाद्रपदा','उत्तराभाद्रपदा','रेवती']
ROMANS={r:i+1 for i,r in enumerate(['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'])}
DEC=str.maketrans('०१२३४५६७८९','0123456789')
CODE=re.compile(r'^[^\w]*((?:Bh\d+[A-Za-z]+\d*|(?:Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)InH\d+|(?:RaKeH|UrInH|NeInH|PlInH)\d+|Nak\d+[A-Za-z]+\d*|Y\d+))\b',re.I)
HOUSE=re.compile(r'^[^\w]*(\d{1,2}|[०-९]{1,2}|XII|XI|VIII|VII|VI|IV|III|II|IX|X|V|I)(?:st|nd|rd|th|ला|रा|था|वा|वी|वे)?\s*(?:भाव|House)\b',re.I)
PATS='|'.join(sorted(map(re.escape,PLANETS),key=len,reverse=True))
PAIR=re.compile(r'^[^\w]*('+PATS+r')\s*[-–—]\s*('+PATS+r')(?=\s*[:(०-९0-9])',re.I)
SIGN=re.compile(r'^[^\w]*('+PATS+r')\s+in\s*:?\s*([A-Za-z]+)(?:\s*\([^)]*\))?\s*:',re.I)
EN_SIGNS=dict(zip(['ARIES','TAURUS','GEMINI','CANCER','LEO','VIRGO','LIBRA','SCORPIO','SAGITTARIUS','CAPRICORN','AQUARIUS','PISCES'],SIGNS.values()))
records=[];sources=[];notes=[]
def clean(text):
 text=re.sub(r'^\s*\*\*?अनुवाद:\*\*?\s*','',text,flags=re.M)
 text=re.sub(r'^\s*[*_-]{3,}\s*$','',text,flags=re.M)
 return text.strip()
def lang(text):
 dev=len(re.findall(r'[\u0900-\u097f]',text));latin=len(re.findall(r'[A-Za-z]',text))
 return 'mr' if dev>8 and dev>latin*0.15 else 'en'
def emit(source,key,text,kind,**extra):
 text=clean(text)
 if not text:return
 original_key=key
 if kind=='yoga':
  ids=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke']
  header=text.splitlines()[0].split(key,1)[-1]
  header=re.sub(r'^\s*[=–—-]\s*','',header)
  header=re.split(r'\s*[-–—]\s*',header,1)[0]
  aliases={'sun':'Su','surya':'Su','moon':'Mo','chandra':'Mo','mars':'Ma','mercury':'Me','jupiter':'Ju','guru':'Ju','venus':'Ve','saturn':'Sa','rahu':'Ra','ketu':'Ke'}
  found=set(aliases[v.lower()] for v in re.findall(r'\b(?:Sun|Surya|Moon|Chandra|Mars|Mercury|Jupiter|Guru|Venus|Saturn|Rahu|Ketu)\b',header,re.I))
  for name,pid in PLANETS.items():
   if not name.isascii() and name in header and pid in ids:found.add(pid)
  if len(found)>=2:
   extra['planets']=[pid for pid in ids if pid in found]
   canonical='Y'+str(sum(1<<ids.index(pid) for pid in found))
   if canonical!=key:notes.append({'source':source,'reason':key+' heading names '+', '.join(extra['planets'])+'; matched by those explicit names ('+canonical+'), original text retained.'})
   key=canonical
  else:extra['mappingStatus']='review'
 records.append({'id':f'upload-{len(records)+1}','source':source,'key':key,'sourceKey':original_key,'text':text,'language':lang(text),'kind':kind,**extra})

for n,row in enumerate(json.loads(MANIFEST.read_text()),1):
 path=Path(row['path']);path=path if path.is_absolute() else ROOT/path;raw=path.read_bytes();text=raw.decode('utf-8-sig');dest=ROOT/'data/predictions-2026-10-14'/row['group']/path.name;dest.parent.mkdir(parents=True,exist_ok=True);
 if path.resolve()!=dest.resolve():shutil.copyfile(path,dest)
 sid=f'source-{n}';sources.append({'id':sid,'group':row['group'],'filename':path.name,'path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
 before=len(records);group=row['group'];pid=PLANETS.get(row['name']);blocks=[]
 if group=='nakshatra':
  idx=NAKS.index(row['name'])+1;pieces=re.split(r'^\s*English\s*$',text,flags=re.M|re.I)
  for piece in pieces:emit(sid,'nak'+str(idx),piece,'nakshatra',nak=idx)
 else:
  lines=text.splitlines();starts=[]
  for i,line in enumerate(lines):
   m=CODE.match(line)
   if m:
    key=m[1]
    if key.startswith('RaKeH') and pid:key=pid+'InH'+key[len('RaKeH'):]
    # Intro lines such as “MaInH : 12 houses” are not matching records.
    kind='coded'
    if re.fullmatch(r'Y\d+',key):kind='yoga'
    elif re.fullmatch(r'Bh\d+L\d+',key):kind='house-lord'
    elif re.fullmatch(r'Bh\d+LH',key):kind='heading'
    elif re.fullmatch(r'(?:Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke|Ur|Ne|Pl)InH\d+',key):kind='planet-house'
    elif re.fullmatch(r'Nak\d+[RC]\d+',key):kind='nakshatra-code'
    starts.append((i,key,kind,{}));continue
   if group=='dasha' and (m:=PAIR.match(line)):
    md,ad=PLANETS[m[1].upper() if m[1].isascii() else m[1]],PLANETS[m[2].upper() if m[2].isascii() else m[2]]
    starts.append((i,md+'AD'+ad,'dasha-pair',{'md':md,'ad':ad}));continue
   if group=='signs' and (m:=SIGN.match(line)):
    planet=PLANETS[m[1].upper() if m[1].isascii() else m[1]];sign=EN_SIGNS.get(m[2].upper())
    if not sign:continue
    if sign!=SIGNS[row['name']]:notes.append({'source':sid,'reason':m[1]+' heading says '+m[2]+'; retained under that sign, not the filename sign.'})
    starts.append((i,planet+'In'+sign,'planet-sign',{'planet':planet,'sign':sign}));continue
   if group in ('transit','planet-houses') and (m:=HOUSE.match(line)):
    token=m[1].translate(DEC);house=ROMANS.get(token.upper(),int(token) if token.isdigit() else 0)
    if 1<=house<=12:starts.append((i,pid+('TransitH' if group=='transit' else 'InH')+str(house),'transit-house' if group=='transit' else 'planet-house',{'planet':pid,'house':house}))
  for i,(start,key,kind,extra) in enumerate(starts):
   end=starts[i+1][0] if i+1<len(starts) else len(lines)
   emit(sid,key,'\n'.join(lines[start:end]),kind,**extra)
 if len(records)==before and group=='planet-houses' and pid in ('Ur','Ne','Pl'):
  emit(sid,pid+'Reference',text,'outer-reference',planet=pid)
 if len(records)==before:notes.append({'source':sid,'reason':'No safely recognized heading; source retained for review.'})
# Stable duplicate handling: preserve different supplied texts and languages;
# exact repeated text for the same key appears only once.
unique={}
for r in records:
 token=(r['kind'],r['key'],r['language'],r['text'])
 if token not in unique:unique[token]={**r,'sources':[r['source']]}
 elif r['source'] not in unique[token]['sources']:unique[token]['sources'].append(r['source'])
records=list(unique.values())
data={'metadata':{'date':'2026-10-14','sourceCount':len(sources),'recordCount':len(records),'importPolicy':'Literal source text; no calculation formula is imported or modified.'},'sources':sources,'records':records,'review':list({(n['source'],n['reason']):n for n in notes}.values())}
(ROOT/'vendor/predictions/supplied-content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(json.dumps({'sources':len(sources),'records':len(records),'kinds':dict(Counter(r['kind'] for r in records)),'languages':dict(Counter(r['language'] for r in records)),'review':list({(n['source'],n['reason']):n for n in notes}.values())},ensure_ascii=False))
