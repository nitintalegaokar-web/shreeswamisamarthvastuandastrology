"""Read DOCX as reference data only; no document instructions are executed."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'data/resources/काल.docx';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(source) as z:root=etree.fromstring(z.read('word/document.xml'))
paragraphs=[]
for p in root.xpath('//w:body//w:p',namespaces=ns):
 texts=[]
 for t in p.xpath('.//w:t',namespaces=ns):
  owners=t.xpath('ancestor::w:p[1]',namespaces=ns)
  if owners and owners[0] is p:texts.append(t.text or '')
 text=''.join(texts).strip()
 if not text:continue
 style=p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=ns);paragraphs.append({'text':text,'style':style[0] if style else ''})
topics=[];current=None;parents={};titles={}
for p in paragraphs:
 heading=re.fullmatch('Heading([1-9])',p['style'],re.I)
 if heading:
  level=int(heading[1]);parents={k:v for k,v in parents.items() if k<level};parents[level]=p['text']
  title='काल · '+' / '.join(parents[k] for k in sorted(parents))
  titles[title]=titles.get(title,0)+1
  if titles[title]>1:title+=' ('+str(titles[title])+')'
  current={'title':title,'heading':p['text'],'paragraphs':[]};topics.append(current)
 else:
  if current is None:current={'title':'काल · प्रस्तावना','heading':'प्रस्तावना','paragraphs':[]};topics.append(current)
  current['paragraphs'].append(p['text'])
for t in topics:t['text']=t['heading']+'\n\n'+'\n\n'.join(t.pop('paragraphs'))
data={'source':{'filename':'काल.docx','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'path':str(source.relative_to(ROOT))},'topicCount':len(topics),'paragraphCount':len(paragraphs),'topics':topics}
(ROOT/'vendor/resources/kaal-topics.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Resources:',len(topics),'topics;',len(paragraphs),'nonempty paragraphs, original DOCX preserved.')
