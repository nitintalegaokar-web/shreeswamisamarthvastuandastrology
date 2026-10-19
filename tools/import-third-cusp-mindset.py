"""Import explicit bilingual mindset keys, preserving malformed source ranges as provenance."""
import csv,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'data/third-cusp-mindset-2026-10-19/Pasted-text.txt'
signs='Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces'.split();names=dict(zip('sun moon mars mercury jupiter venus saturn rahu ketu'.split(),'Su Mo Ma Me Ju Ve Sa Ra Ke'.split()))
entries=[]
for line in csv.reader(p.read_text().splitlines(),delimiter='\t',quoting=csv.QUOTE_NONE):
 if not line or not line[0].strip().isdigit():continue
 assert len(line)==9
 number,sign,start,end,sgl,stl,sl,en,mr=[x.strip() for x in line]
 entries.append(dict(number=int(number),signIndex=signs.index(sign),sgl=names[sgl.lower()],stl=names[stl.lower()],sl=names[sl.lower()],english=en,marathi=mr,rawFrom=start,rawTo=end))
assert len(entries)==248
assert len({(r['signIndex'],r['sgl'],r['stl'],r['sl']) for r in entries})==248
missing=sorted(set(range(1,250))-{r['number'] for r in entries})
data=dict(metadata=dict(filename=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),count=len(entries),missing=missing,matching='Third cusp sign and exact sign/star/sub lords. Malformed printed degree ranges are not used.'),entries=entries)
(root/'vendor/predictions/third-cusp-mindset-data.js').write_text('globalThis.KPThirdCuspMindsetData='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
print('Imported',len(entries),'mindset records; missing',missing)
