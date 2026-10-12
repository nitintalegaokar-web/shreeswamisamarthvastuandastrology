'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os');
const {readHistory,writeHistory,changeRemoval,historyText}=require('../owner/history.cjs');
const first={licenseId:'license-one',clientName:'Duplicate client',systemId:'same-computer',ownerKeyId:'owner-one',expiresAt:null,issuedAt:'2026-10-12T09:00:00Z',status:'deactivate',controlRevision:7,unknownSecret:'do-not-export'},second={...first,licenseId:'license-two',controlRevision:2};
test('removal targets the exact license, preserves control revision and restores original metadata',()=>{
 const original=[first,second],removed=changeRemoval(original,first.licenseId,true,new Date('2026-10-12T10:00:00Z'));assert.equal(removed.filter(row=>!row.removedAt).length,1);assert.equal(removed[0].controlRevision,7);assert.equal(removed[1],second);assert.deepEqual(original,[first,second]);assert.deepEqual(changeRemoval(removed,first.licenseId,false),original);assert.throws(()=>changeRemoval(original,'missing',true),/not found/);
});
test('legacy records and removed entries persist across atomic save/read; invalid history is reported',async t=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'kp-history-unit-'));t.after(()=>fs.rm(dir,{recursive:true,force:true}));const file=path.join(dir,'issued-licenses.json');assert.deepEqual(await readHistory(file),[]);
 const legacy={...first};delete legacy.status;delete legacy.controlRevision;const records=changeRemoval([legacy,second],second.licenseId,true);await writeHistory(file,records);assert.deepEqual(await readHistory(file),records);await writeHistory(file,changeRemoval(await readHistory(file),second.licenseId,false));assert.deepEqual(await readHistory(file),[legacy,second]);
 await fs.writeFile(file,'{');await assert.rejects(()=>readHistory(file),/saved license history is invalid/);assert.equal(await fs.readFile(file,'utf8'),'{');await assert.rejects(()=>writeHistory(file,[{}]),/invalid/);assert.equal(await fs.readFile(file,'utf8'),'{');
});
test('text export includes all retained entries, excludes removed entries and private/unexpected data',()=>{
 const records=Array.from({length:15},(_,i)=>({...first,licenseId:'license-'+i,clientName:'Client '+i}));const removed=changeRemoval(records,'license-1',true),text=historyText(removed,'en',new Date('2026-10-12T10:00:00Z'));assert.equal(text.charCodeAt(0),0xFEFF);assert.match(text,/Entries: 14/);assert.match(text,/Client: Client 14\r\n/);assert.doesNotMatch(text,/Client: Client 1\r\n/);assert.doesNotMatch(text,/do-not-export|unknownSecret/);assert.match(text,/Status revision: 7/);assert.match(text,/does not confirm activation/);
 const marathi=historyText([first],'mr');assert.match(marathi,/परवाना नोंदी/);assert.match(marathi,/निष्क्रियता दिली/);assert.match(marathi,/कायमस्वरूपी/);
});
