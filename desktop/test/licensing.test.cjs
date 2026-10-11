'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const core=require('../licensing/core.cjs');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const keys=crypto.generateKeyPairSync('ed25519');
const other=crypto.generateKeyPairSync('ed25519');
const now=new Date('2026-10-11T12:00:00Z');
const id=core.systemId({machineGuid:'00112233-4455-6677-8899-aabbccddeeff',hardwareUUID:'12345678-1234-1234-1234-123456789abc'});
const alternate=core.systemId({machineGuid:'00112233-4455-6677-8899-aabbccddee00',hardwareUUID:'12345678-1234-1234-1234-123456789abc'});
const request={systemId:id,clientName:'Test client',expiryDate:null};
test('System ID stays stable under identifier formatting and changes across computers',()=>{
  assert.equal(id,core.systemId({machineGuid:'{00112233-4455-6677-8899-AABBCCDDEEFF}',hardwareUUID:'12345678123412341234123456789ABC'}));
  assert.notEqual(id,alternate);assert.match(id,core.SYSTEM_ID);
  assert.throws(()=>core.systemId({machineGuid:''}));assert.throws(()=>core.systemId({machineGuid:'0'.repeat(32)}));
});
test('Correct owner signature and System ID activate without network access',()=>{
  const license=core.issue(keys.privateKey,request,now);
  const claims=core.verify(JSON.stringify(license),keys.publicKey,id,now);
  assert.equal(claims.clientName,'Test client');assert.equal(claims.expiresAt,null);
  assert.equal(core.verify(license,keys.publicKey,id,new Date('2050-01-01')).systemId,id);
});
test('A copied license, forged license, changed signed data, or different owner is rejected',()=>{
  const license=core.issue(keys.privateKey,request,now);
  assert.throws(()=>core.verify(license,keys.publicKey,alternate,now),/different computer/);
  assert.throws(()=>core.verify(license,other.publicKey,id,now),/software owner/);
  const changed={...license,payload:Buffer.from(JSON.stringify({...JSON.parse(Buffer.from(license.payload,'base64url')),systemId:alternate})).toString('base64url')};
  assert.throws(()=>core.verify(changed,keys.publicKey,alternate,now),/software owner/);
  assert.throws(()=>core.verify({...license,signature:'A'.repeat(86)},keys.publicKey,id,now),/software owner/);
});
test('Expiry and issuance clock checks reject expired or future licenses',()=>{
  const license=core.issue(keys.privateKey,{...request,expiryDate:'2026-10-12'},now);
  assert.equal(core.verify(license,keys.publicKey,id,new Date('2026-10-12T23:59:59.999Z')).systemId,id);
  assert.throws(()=>core.verify(license,keys.publicKey,id,new Date('2026-10-13T00:00:00Z')),/expired/);
  assert.throws(()=>core.verify(license,keys.publicKey,id,new Date('2026-10-10')),/date and time/);
  for(const expiryDate of ['','2026-02-30','2026-10-10','invalid'])assert.throws(()=>core.issue(keys.privateKey,{...request,expiryDate},now));
});
test('Malformed, oversized, wrong-product and missing-expiry licenses are rejected',()=>{
  assert.throws(()=>core.verify('{',keys.publicKey,id,now));assert.throws(()=>core.verify('A'.repeat(20000),keys.publicKey,id,now));
  assert.throws(()=>core.verify({payload:'!',signature:'A'},keys.publicKey,id,now));
  const good=core.issue(keys.privateKey,request,now);const claims=JSON.parse(Buffer.from(good.payload,'base64url'));
  for(const changed of [{...claims,product:'another-product'},{...claims,expiresAt:undefined}]){
    const data=Buffer.from(JSON.stringify(changed));const license={payload:data.toString('base64url'),signature:crypto.sign(null,data,keys.privateKey).toString('base64url')};
    assert.throws(()=>core.verify(license,keys.publicKey,id,now));
  }
});
test('Password-encrypted owner key cannot issue licenses without the correct password',()=>{
  const pem=keys.privateKey.export({type:'pkcs8',format:'pem',cipher:'aes-256-cbc',passphrase:'Test-password-only-123'});
  assert.match(pem,/BEGIN ENCRYPTED PRIVATE KEY/);
  assert.throws(()=>crypto.createPrivateKey({key:pem,passphrase:'incorrect-password'}));
  const reopened=crypto.createPrivateKey({key:pem,passphrase:'Test-password-only-123'});
  assert.equal(core.verify(core.issue(reopened,request,now),keys.publicKey,id,now).systemId,id);
});
test('Client preparation fails without a public key and rejects private-key inputs',()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'kp-public-key-guard-'));
  try{
    const supplied=path.join(directory,'not-public.pem');fs.writeFileSync(supplied,'-----BEGIN PRIVATE KEY-----\nnot a production key\n-----END PRIVATE KEY-----');
    for(const file of [supplied,path.join(directory,'missing.pem')]){
      const result=spawnSync(process.execPath,[path.join(__dirname,'..','prepare.cjs')],{env:{...process.env,KP_LICENSE_PUBLIC_KEY_FILE:file},encoding:'utf8'});
      assert.notEqual(result.status,0);assert.match(result.stderr,/PUBLIC key|public key/);
    }
  }finally{fs.rmSync(directory,{recursive:true,force:true});}
});
