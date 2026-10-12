'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {systemId,issue,verify,issueControl,verifyControl,applyControl}=require('../licensing/core.cjs');
const keys=crypto.generateKeyPairSync('ed25519'),other=crypto.generateKeyPairSync('ed25519');
const id=systemId({machineGuid:'00112233445566778899aabbccddeeff'}),wrongId=systemId({machineGuid:'112233445566778899aabbccddeeff00'}),now=new Date('2026-10-12T12:00:00Z');
const license=issue(keys.privateKey,{clientName:'Test client',systemId:id,expiryDate:'2026-10-31'},now),claims=verify(license,keys.publicKey,id,now);
const control=(action,revision,overrides={})=>issueControl(keys.privateKey,{licenseId:claims.licenseId,systemId:id,action,revision,...overrides},now);
test('signed Activate/Deactivate controls are bound to license, owner and computer',()=>{
 for(const action of ['activate','deactivate']){const c=control(action,1),v=verifyControl(c,keys.publicKey,id,now);assert.equal(v.action,action);assert.equal(v.licenseId,claims.licenseId);assert.throws(()=>verifyControl(c,other.publicKey,id,now),/software owner/);assert.throws(()=>verifyControl(c,keys.publicKey,wrongId,now),/different computer/);assert.throws(()=>verify(c,keys.publicKey,id,now),/another product/);}
 assert.throws(()=>verifyControl(license,keys.publicKey,id,now),/valid owner/);
});
test('controls reject altered payloads, invalid revisions and future dates',()=>{
 const c=control('deactivate',1);const data=JSON.parse(Buffer.from(c.payload,'base64url'));data.action='activate';assert.throws(()=>verifyControl({...c,payload:Buffer.from(JSON.stringify(data)).toString('base64url')},keys.publicKey,id,now),/changed/);
 for(const revision of [0,-1,1.5,NaN,Number.MAX_SAFE_INTEGER+1])assert.throws(()=>control('deactivate',revision),/valid issued/);
 assert.throws(()=>control('arbitrary',1),/valid issued/);assert.throws(()=>control('activate',1,{licenseId:'__proto__'}),/valid issued/);
 assert.throws(()=>verifyControl(c,keys.publicKey,id,new Date('2026-10-11')),/date and time/);
});
test('latest revision persists, identical reimport is allowed and replay cannot change status',()=>{
 const deact=control('deactivate',1),act=control('activate',2);let data=applyControl({},deact,keys.publicKey,id,now);assert.equal(verifyControl(data[claims.licenseId],keys.publicKey,id,now).action,'deactivate');data=JSON.parse(JSON.stringify(data));data=applyControl(data,act,keys.publicKey,id,now);assert.deepEqual(applyControl(data,act,keys.publicKey,id,now),data);assert.throws(()=>applyControl(data,deact,keys.publicKey,id,now),/older/);assert.throws(()=>applyControl(data,control('deactivate',2),keys.publicKey,id,now),/older/);
 assert.equal(verifyControl(data[claims.licenseId],keys.publicKey,id,now).action,'activate');
});
test('status commands cannot extend expiry or replace an activation license',()=>{
 const command=control('activate',1);assert.equal(verifyControl(command,keys.publicKey,id,new Date('2026-11-01')).action,'activate');assert.throws(()=>verify(license,keys.publicKey,id,new Date('2026-11-01')),/expired/);assert.throws(()=>verify(command,keys.publicKey,id,now),/another product/);
});
