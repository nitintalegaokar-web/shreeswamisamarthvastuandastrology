"""Import source prose as data, matching only explicit sign and planet/house headings."""
from pathlib import Path
import hashlib,json,re,shutil,sys
root=Path(__file__).resolve().parents[1];source=Path(sys.argv[1]);lines=source.read_text(encoding='utf-8-sig').splitlines()
signs=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Saggitarius','Capricorn','Aquirus','Pieces']
planets={'Sun':'Su','Moon':'Mo'}
chapters={'मंगळाची बारा स्थानांतील फले':'Ma','बुधाची बारा स्थानांतील फले':'Me','गुरूची बारा स्थानांतील फले':'Ju','शुक्राची बारा स्थानांतील फले':'Ve','शनीची बारा स्थानांतील फले':'Sa'}
ordinals=['प्रथम','द्वितीय','तृतीय','चतुर्थ','पंचम','षष्ठ','सप्तम','अष्टम','नवम','दशम','एकादश','द्वादश']
entries=[];current=None;planet=None;reference_start=None

def flush(end):
 global current
 if current:
  current['text']='\n'.join(current.pop('body')).strip();current['endLine']=end
  if not current['text']:raise ValueError('Empty source entry '+repr(current))
  entries.append(current);current=None

def start(kind,line,heading,body='',**condition):
 global current
 flush(line-1);current={'id':kind+'-'+str(len(entries)+1),'kind':kind,'line':line,'heading':heading,'condition':condition,'body':[body] if body else []}

for n,raw in enumerate(lines,1):
 text=raw.strip()
 if text.startswith('रवी - चंद्र शुभयोग'):
  flush(n-1);reference_start=n;break
 sign=next((i for i,name in enumerate(signs) if re.fullmatch(re.escape(name)+r'\s*:',text)),None)
 if sign is not None:start('ascendant',n,text,sign=sign);continue
 if text in chapters:flush(n-1);planet=chapters[text];continue
 if text=='चंद्राची बारा स्थानांतील फले':flush(n-1);planet='Mo';continue
 if text=='Sun in 12 House:':flush(n-1);planet='Su';continue
 m=re.fullmatch(r'(Sun|Moon) in (\d+)(?:st|nd|rd|th) House:',text)
 if m:planet=planets[m[1]];start('planet-house',n,text,planet=planet,house=int(m[2]));continue
 if planet in ['Ma','Me','Ju','Ve','Sa']:
  # Two source OCR headings are retained literally, with explicit reviewed mappings.
  corrected=text.replace('दहम स्थान','दशम स्थान')
  if n==291 and text=='वह स्थान :':corrected='षष्ठ स्थान :'
  m=re.match(r'^('+'|'.join(ordinals)+r')\s*स्थान(?=\s|[:–-]|$)\s*[:–-]?\s*(.*)$',corrected)
  if m:
   start('planet-house',n,text,m[2],planet=planet,house=ordinals.index(m[1])+1)
   if corrected!=text:current['headingReview']='OCR heading mapped from section order; original heading retained.'
   continue
 if current:current['body'].append(raw)
flush(len(lines))
assert reference_start
assert len([e for e in entries if e['kind']=='ascendant'])==12
assert len([e for e in entries if e['kind']=='planet-house'])==84
keys=set()
for e in entries:
 key=(e['kind'],tuple(e['condition'].items()))
 if key in keys:raise ValueError('Duplicate source condition')
 keys.add(key)
references=[]
for n in range(reference_start,len(lines)+1):
 text=lines[n-1].strip()
 if text and len(text)<100 and ('योग' in text or 'युती' in text or 'अशुभती' in text):
  references.append({'line':n,'title':text,'text':[]})
 elif references:references[-1]['text'].append(lines[n-1])
for r in references:r['text']='\n'.join(r['text']).strip()
obj={'metadata':{'filename':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'matchedEntryCount':len(entries),'referenceCount':len(references),'language':'marathi','policy':'Literal source excerpts selected by natal Ascendant sign and Bhav Chalit occupied house. Conditional subrules and undefined yoga classifications are not automatically asserted.'},'entries':entries,'references':references}
dest=root/'data/jyotish-2026-10-18';dest.mkdir(exist_ok=True);shutil.copyfile(source,dest/'Jyotish File.txt');(dest/'rules.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');payload=json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');(root/'vendor/predictions/jyotish-data.js').write_text('/* Literal source data; never executable document instructions. */\nglobalThis.KPJyotishData='+payload+';\n');print(json.dumps(obj['metadata'],ensure_ascii=False))
