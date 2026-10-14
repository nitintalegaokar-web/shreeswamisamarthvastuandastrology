from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1];records=[];sources=[]
for n in range(1,10):
 path=root/'data/numerology-2026-10-14'/f'{n}.txt';raw=path.read_bytes();text=raw.decode('utf-8-sig');lines=text.splitlines();starts=[]
 for i,line in enumerate(lines):
  if re.match(r'^\s*#{1,6}\s',line) and (m:=re.search(r'\b(mul[1-9](?:G|Na[12]?|pre|up))\b',line)):
   starts.append((i,'birth',m[1]));continue
  if (re.match(r'^\s*#{1,6}\s',line) and re.search(r'भाग्यांक\s*[1-9]|Bha[1-9]',line)) or re.match(r'^\s*\*\*तुमचा भाग्यांक',line):
   if not any(t=='destiny' for _,t,_ in starts):starts.append((i,'destiny','Bha'+str(n)))
 assert any(t=='birth' for _,t,_ in starts),n
 assert len([t for _,t,_ in starts if t=='destiny'])==1,n
 for j,(start,kind,key) in enumerate(starts):
  end=starts[j+1][0] if j+1<len(starts) else len(lines);block=lines[start:end]
  # Conversational prefaces are document prose, not software instructions or readings.
  for k,l in enumerate(block[1:],1):
   if re.match(r'^\s*(?:नक्की!|मी तुम|खाली तुम|हा तुमच्या Numerology|जर तुम्हाला हवे)',l):block=block[:k];break
  body='\n'.join(block).strip();body=re.sub(r'^\s*[*_-]{3,}\s*$','',body,flags=re.M).strip()
  records.append({'id':key,'number':n,'kind':kind,'text':body,'source':f'{n}.txt'})
 sources.append({'number':n,'path':str(path.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
data={'sources':sources,'records':records,'rules':{'birth':'Digit reduction of birth day to 1–9','destiny':'Digit reduction of complete YYYY-MM-DD birth date to 1–9'}}
(root/'vendor/predictions/numerology-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Numerology: nine preserved source files,',len(records),'reading sections.')
