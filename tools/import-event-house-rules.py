"""Import each language independently: source row counts/order are different."""
from pathlib import Path
import csv,json,re,hashlib
root=Path(__file__).resolve().parents[1];entries=[];sources={}
for lang,file,start in [('english','English.txt',20001),('marathi','Marathi.txt',21001)]:
 p=root/'data/event-house-2026-10-18'/file;sources[lang]={'filename':file,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};rows=list(csv.reader(p.open(),delimiter='\t'))
 for row_no,row in enumerate(rows[1:],2):
  if not any(c.strip() for c in row):continue
  assert len(row)==4,(lang,row_no,row)
  category,matter,primary,raw=[c.strip() for c in row];houses=[int(n) for n in re.findall(r'\d+',primary) if 1<=int(n)<=12]
  if '<any of 12>' in primary:houses=list(range(1,13))
  expression=re.sub(r'^\s*\d+\s*=\s*','',raw);prefix=re.match(r'^([\d\s,+]+)',expression);group=sorted(set(int(n) for n in re.findall(r'\d+',prefix[1] if prefix else '') if 1<=int(n)<=12));groups=[group] if group else []
  # A wholly numeric expression is fully specified. Qualifiers are never discarded.
  numeric=bool(re.fullmatch(r'[\d\s,+]+',expression)) and bool(group)
  planet=None
  for en,mr,code in [('Saturn','शनी','Sa'),('Saturn','शनि','Sa'),('Rahu','राहू','Ra'),('Ketu','केतू','Ke')]:
   if re.fullmatch(r'(?:'+en+r' as (?:house )?sub lord|'+mr+r' (?:सबलॉर्ड|सबलोर्ड))',raw,re.I):planet=code
  extra=not numeric and planet is None
  if not groups and planet is None:extra=True
  sensitive=bool(re.search(r'disease|health|illness|blind|suicide|rape|raping|crime|criminal|madness|insanity|retarded|deaf|dumb|miscarriage|abortion|no child|enunch|lowly|christian|caste|आजार|विकार|नैराश्य|वेडे|वंध्य|गर्भपात|गुन्ह|लैंगिक|मानसिक|दृष्टीहानी|कर्णबधिर|संतती नाही',matter+' '+raw,re.I))
  ident=start+len([e for e in entries if e['language']==lang]);entries.append({'id':ident,'language':lang,'category':category,'matter':matter,'primaryRaw':primary,'mainHouses':list(dict.fromkeys(houses)),'supportingRaw':raw,'supportingGroups':groups,'extraConditions':extra,'cslPlanet':planet,'sensitiveReference':sensitive,'sourceRow':row_no,'sourceFilename':file})
 sources[lang]['count']=len([e for e in entries if e['language']==lang])
out={'metadata':{'sources':sources,'policy':'Language files are independent source tables; never pair rows by index. Numeric comma/plus lists are joint groups. Unparsed qualifiers and missing primary houses remain review-only. Existing majority-match convention is used for house support.'},'entries':entries}
(root/'data/event-house-2026-10-18/rules.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(root/'vendor/predictions/event-house-data.js').write_text('globalThis.KPEventHouseData='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n');print({lang:v['count'] for lang,v in sources.items()})
