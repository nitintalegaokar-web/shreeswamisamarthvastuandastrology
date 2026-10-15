'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {toCode,fromCode}=require('../licensing/activation-code.cjs'),core=require('../licensing/core.cjs');
const key=crypto.generateKeyPairSync('ed25519'),id=core.systemId({machineGuid:'00112233445566778899aabbccddeeff'}),now=new Date('2026-10-15T00:00:00Z');
test('activation code preserves device-bound signature and expiry with whitespace-tolerant pasting',()=>{
 const license=core.issue(key.privateKey,{systemId:id,clientName:'Code customer',expiryDate:'2026-10-16'},now),code=toCode(license),pasted=' \n'+code.slice(0,40)+'\n'+code.slice(40)+' ';
 assert.equal(JSON.stringify(license),fromCode(pasted));assert.equal(core.verify(fromCode(pasted),key.publicKey,id,now).clientName,'Code customer');assert.throws(()=>core.verify(fromCode(code),key.publicKey,id,new Date('2026-10-17')),/expired/);
 const other=core.systemId({machineGuid:'10112233445566778899aabbccddeeff'});assert.throws(()=>core.verify(fromCode(code),key.publicKey,other,now),/different computer/);
});
test('status codes retain replay protection and cannot replace activation keys',()=>{
 const license=core.issue(key.privateKey,{systemId:id,clientName:'Status code',expiryDate:null},now),claims=core.verify(license,key.publicKey,id,now);
 const status=n=>core.issueControl(key.privateKey,{systemId:id,licenseId:claims.licenseId,action:n===1?'deactivate':'activate',revision:n},now);
 const old=status(1),latest=status(2),code=toCode(latest,true);assert.equal(core.verifyControl(fromCode(code,true),key.publicKey,id,now).action,'activate');
 assert.throws(()=>fromCode(code),/activation key/);assert.throws(()=>fromCode(toCode(license),true),/status key/);
 assert.throws(()=>core.applyControl(core.applyControl({},JSON.parse(fromCode(code,true)),key.publicKey,id,now),JSON.parse(fromCode(toCode(old,true),true)),key.publicKey,id,now),/older/);
});
test('truncated, oversized, malformed and tampered codes fail',()=>{
 for(const code of [null,'','abcd','KP-A1.a.b','KP-A1.a.'+'a'.repeat(87),'x'.repeat(16385)])assert.throws(()=>fromCode(code));
 const license=core.issue(key.privateKey,{systemId:id,clientName:'Tampered',expiryDate:null},now),code=toCode({...license,signature:(license.signature[0]==='a'?'b':'a')+license.signature.slice(1)});
 assert.throws(()=>core.verify(fromCode(code),key.publicKey,id,now),/changed/);
});
