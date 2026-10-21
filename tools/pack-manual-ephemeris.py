"""Store the supplied daily longitudes losslessly; derived source labels are unused."""
from pathlib import Path
import re,gzip,base64,struct,hashlib,json,datetime,html as entities
root=Path(__file__).resolve().parents[1];path=root/'vendor/transit/manual-tool.html';html=path.read_text();total=0
for match in list(re.finditer(r"const (c\d{4}(?:_\d{4})?)='([^']+)';",html)):
 name,encoded=match.groups()
 if encoded.startswith('4b50444532'):continue
 raw=gzip.decompress(base64.b64decode(encoded))
 if raw.startswith(b'KPDE1'):raise ValueError('Use the original supplied JSON data to repack this legacy layout.')
 rows=json.loads(raw);first=datetime.date.fromisoformat(rows[0][0]);out=bytearray(b'KPDE2'+struct.pack('<IHBB',len(rows),first.year,first.month,first.day));previous=[0]*9;velocity=[0]*9;values=[]
 def emit(value):
  value=value*2 if value>=0 else -value*2-1
  while value>=128:out.append((value&127)|128);value>>=7
  out.append(value)
 for planet in range(9):
  for index,row in enumerate(rows):
   assert datetime.date.fromisoformat(row[0])==first+datetime.timedelta(days=index)
   value=row[planet+1]
   m=re.match(r'(\d+)°(\d+)\x27(\d+)',entities.unescape(value));assert m,value
   position=(int(m[1])*3600+int(m[2])*60+int(m[3]))%1296000;values.append(position)
   delta=position if index==0 else (position-previous[planet]+648000)%1296000-648000
   emit(delta-velocity[planet]);previous[planet]=position;velocity[planet]=delta
 # Independently decode every value before replacing its source chunk.
 offset=13;previous=[0]*9;velocity=[0]*9;decoded=[]
 for planet in range(9):
  for index in range(len(rows)):
   value=0;shift=0
   while True:
    byte=out[offset];offset+=1;value|=(byte&127)<<shift
    if not byte&128:break
    shift+=7
   acceleration=value//2 if value%2==0 else -(value//2)-1;delta=velocity[planet]+acceleration
   position=delta if index==0 else (previous[planet]+delta)%1296000
   decoded.append(position);previous[planet]=position;velocity[planet]=delta
 assert decoded==values and offset==len(out)
 packed=out.hex();html=html.replace("const "+name+"='"+encoded+"';","const "+name+"='"+packed+"';",1);total+=len(rows)
 print(name,len(encoded),'->',len(packed),'base64 bytes; verified',len(values),'longitudes')
path.write_text(html)
metadata=root/'vendor/transit/manual-tool-source.json';data=json.loads(metadata.read_text());data['storage']='KPDE2 lossless per-planet second-difference varints, encoded as hexadecimal. All original daily arcsecond longitudes are retained; Sign/Star/Sub labels use the existing KP engine.';metadata.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print('Verified daily rows',total)
