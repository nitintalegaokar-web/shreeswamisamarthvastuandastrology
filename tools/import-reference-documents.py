from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import json,hashlib,shutil,re
root=Path(__file__).resolve().parents[1]; dest=root/'data/resources';dest.mkdir(exist_ok=True)
files=[(str(dest/name),name) for name in ['KP Gems stone.docx', 'KP Horary Que 6 Fold.docx', 'KP Horary Que 4 fold.docx', 'KP Numbers 1 to 249.docx']]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};topics=[];sources=[];numbers=[]
for src,name in files:
 # Sources are retained under data/resources.
 b=(dest/name).read_bytes();sources.append({'filename':name,'path':'data/resources/'+name,'sha256':hashlib.sha256(b).hexdigest()})
 with ZipFile(dest/name) as z:doc=etree.fromstring(z.read('word/document.xml'))
 if 'Numbers' in name:
  rows=doc.findall('.//w:tbl/w:tr',ns)
  for row in rows[2:]:numbers.append([''.join(c.xpath('.//w:t/text()',namespaces=ns)) for c in row.findall('./w:tc',ns)])
  for start in range(0,len(numbers),25):
   chunk=numbers[start:start+25];topics.append({'title':f'KP Numbers · {chunk[0][0]}–{chunk[-1][0]} · Sub-lord reference','text':'No. | Sign | From DMS | To DMS | Nakshatra | Star lord | Sub lord\n\n'+'\n'.join(' | '.join(r) for r in chunk)})
 else:
  text='\n'.join(''.join(p.xpath('.//w:t/text()',namespaces=ns)) for p in doc.findall('.//w:p',ns))
  if name=='KP Gems stone.docx':
   text='रत्न मार्गदर्शन\n\nलग्नेश, दशमेश व भाग्येश शुभदायक असतात. लाभस्थानाचा उपनक्षत्र स्वामी पाहावा. तो ज्या नक्षत्रात असेल, त्या नक्षत्रस्वामीने प्रथम, धन किंवा लाभस्थान (१, २, ११) दर्शविल्यास त्या नक्षत्रस्वामीचे रत्न वापरावे.\n\nसॉफ्टवेअरमधील नियम: अकराव्या भावाचा उपनक्षत्र स्वामी → त्याचा नक्षत्र स्वामी → त्या ग्रहाचे विद्यमान चार किंवा सहा स्तरांतील कार्येशत्व. १, २, ११ पैकी किमान एका भावाचे कार्येशत्व असल्यास त्या नक्षत्रस्वामीचे रत्न दर्शविले जाते.\n\nकार्य: विवाह, संतानप्राप्ती, आजारातून मुक्तता, शिक्षण, सर्व कार्यात यश, धनप्राप्ती, वैवाहिक आनंद, नोकरी, प्रमोशन, ट्रान्सफर, घरप्राप्ती, विदेशगमन, लॉटरी, मानसन्मान व रागावर नियंत्रण. या कार्यांसाठी स्वतंत्र भावसमूह किंवा रत्न-निवडीचे स्वतंत्र नियम दस्तऐवजात दिलेले नाहीत.'
  topics.append({'title':name.removesuffix('.docx'),'text':text})
assert len(numbers)==249 and [int(r[0]) for r in numbers]==list(range(1,250))
(root/'vendor/resources/additional-documents.json').write_text(json.dumps({'sources':sources,'numbers':numbers,'topics':topics},ensure_ascii=False,indent=2)+'\n')
