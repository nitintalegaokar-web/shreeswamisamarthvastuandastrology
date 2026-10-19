"""Import supplied Marathi house-lord paragraphs; no missing placements inferred."""
import csv,hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'data/vedic-bhav-2026-10-19/Pasted-text.txt'
pattern=re.compile(r'(?:\(([०-९0-9]+)\)|(?<!\S)([०-९0-9]+)\))')
entries=[]
for row in csv.reader(source.read_text().splitlines(keepends=True),delimiter='\t'):
 if len(row)<2 or not row[0].strip().isdigit():continue
 lord=int(row[0]);text=row[1];matches=list(pattern.finditer(text))
 for i,m in enumerate(matches):
  house=int(m.group(1) or m.group(2));body=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
  entries.append(dict(id=f'vedic-bhav-{lord}-{house}',lordHouse=lord,occupiedHouse=house,text=body))
assert len(entries)==143
assert len({(r['lordHouse'],r['occupiedHouse']) for r in entries})==143
data=dict(metadata=dict(filename=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),count=len(entries),language='marathi',missing=['House 7 lord in house 12 is not supplied.'],policy='D1 whole-sign house-lord placement. Conditional clauses retained as source references, not independently confirmed.'),entries=entries)
(root/'vendor/predictions/vedic-bhav-data.js').write_text('globalThis.KPVedicBhavData='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
print('Imported',len(entries),'explicit placements; seventh lord in twelfth is absent from source.')
