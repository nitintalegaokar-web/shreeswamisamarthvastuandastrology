"""Store the supplied daily longitudes losslessly; derived source labels are unused."""
from pathlib import Path
import re,gzip,base64,struct,hashlib,json,datetime,html as entities
root=Path(__file__).resolve().parents[1];path=root/'vendor/transit/manual-tool.html';html=path.read_text();total=0
for match in list(re.finditer(r"const (c\d{4}(?:_\d{4})?)='([^']+)';",html)):
 name,encoded=match.groups();raw=gzip.decompress(base64.b64decode(encoded))
 if raw.startswith(b'KPDE1'):continue
 rows=json.loads(raw);first=datetime.date.fromisoformat(rows[0][0]);out=bytearray(b'KPDE1'+struct.pack('<IHBB',len(rows),first.year,first.month,first.day));previous=[0]*9;velocity=[0]*9;values=[]
 def emit(value):
  value=value*2 if value>=0 else -value*2-1
  while value>=128:out.append((value&127)|128);value>>=7
  out.append(value)
 for index,row in enumerate(rows):
  assert datetime.date.fromisoformat(row[0])==first+datetime.timedelta(days=index)
  for planet,value in enumerate(row[1:]):
   m=re.match(r'(\d+)°(\d+)\x27(\d+)',entities.unescape(value));assert m,value
   position=(int(m[1])*3600+int(m[2])*60+int(m[3]))%1296000;values.append(position)
   delta=position if index==0 else (position-previous[planet]+648000)%1296000-648000
   emit(delta-velocity[planet]);previous[planet]=position;velocity[planet]=delta
 # Independently decode every value before replacing its source chunk.
 offset=13;previous=[0]*9;velocity=[0]*9;decoded=[]
 for index in range(len(rows)):
  for planet in range(9):
   value=0;shift=0
   while True:
    byte=out[offset];offset+=1;value|=(byte&127)<<shift
    if not byte&128:break
    shift+=7
   acceleration=value//2 if value%2==0 else -(value//2)-1;delta=velocity[planet]+acceleration
   position=delta if index==0 else (previous[planet]+delta)%1296000
   decoded.append(position);previous[planet]=position;velocity[planet]=delta
 assert decoded==values and offset==len(out)
 packed=base64.b64encode(gzip.compress(out,compresslevel=9,mtime=0)).decode();html=html.replace("const "+name+"='"+encoded+"';","const "+name+"='"+packed+"';",1);total+=len(rows)
 print(name,len(encoded),'->',len(packed),'base64 bytes; verified',len(values),'longitudes')
path.write_text(html)
metadata=root/'vendor/transit/manual-tool-source.json';data=json.loads(metadata.read_text());data['storage']='KPDE1 lossless second-difference varint encoding of daily arcsecond longitudes; unused source lord labels omitted. All Sign/Star/Sub labels are derived by the existing KP engine.';metadata.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print('Verified daily rows',total)
