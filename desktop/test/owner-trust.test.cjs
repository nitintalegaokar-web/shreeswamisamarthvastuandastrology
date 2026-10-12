'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {issue,issueControl,systemId,keyId}=require('../licensing/core.cjs');
const {approvedKeys,parseAdditionalKeys,verifyTrustedLicense,verifyTrustedControl}=require('../licensing/trust.cjs');
const old=crypto.generateKeyPairSync('ed25519'),current=crypto.generateKeyPairSync('ed25519'),unapproved=crypto.generateKeyPairSync('ed25519');
const id=systemId({machineGuid:'0123456789abcdef0123456789abcdef'}),other=systemId({machineGuid:'1123456789abcdef0123456789abcdef'}),now=new Date('2026-10-12T12:00:00Z');
const pem=key=>key.export({type:'spki',format:'pem'}),keys=approvedKeys(old.publicKey,[pem(current.publicKey)]);
const license=key=>issue(key,{systemId:id,clientName:'Owner migration test',expiryDate:'2026-10-14'},now);
test('both approved owners activate their own signed licenses and preserve signer identity',()=>{
 for(const owner of [old,current]){const verified=verifyTrustedLicense(license(owner.privateKey),keys,id,now);assert.equal(verified.ownerKeyId,keyId(owner.publicKey));assert.equal(keyId(verified.key),verified.ownerKeyId);assert.equal(verified.claims.systemId,id);}
 assert.equal(approvedKeys(old.publicKey,[pem(old.publicKey),pem(current.publicKey)]).length,2);
});
test('an additional owner key never bypasses System ID, dates, expiry or signature validation',()=>{
 const valid=license(current.privateKey);assert.throws(()=>verifyTrustedLicense(valid,keys,other,now),/different computer/);assert.throws(()=>verifyTrustedLicense(valid,keys,id,new Date('2026-10-15')),/expired/);assert.throws(()=>verifyTrustedLicense(valid,keys,id,new Date('2026-10-11')),/date and time/);
 assert.throws(()=>verifyTrustedLicense(license(unapproved.privateKey),keys,id,now),/Accepted owner Key IDs/);
 const changed={...valid,payload:Buffer.from(JSON.stringify({...JSON.parse(Buffer.from(valid.payload,'base64url')),systemId:other})).toString('base64url')};assert.throws(()=>verifyTrustedLicense(changed,keys,other,now),/changed/);
 assert.throws(()=>verifyTrustedLicense(license(old.privateKey),keys,id,new Date('2026-10-15')),/expired/,'Do not hide an old-key expiry behind a new-key signature error.');
});
test('controls identify their actual approved signer; signed status does not replace a license',()=>{
 const verified=verifyTrustedLicense(license(old.privateKey),keys,id,now);
 for(const owner of [old,current]){const control=issueControl(owner.privateKey,{licenseId:verified.claims.licenseId,systemId:id,action:'deactivate',revision:1},now);const result=verifyTrustedControl(control,keys,id,now);assert.equal(result.ownerKeyId,keyId(owner.publicKey));assert.throws(()=>verifyTrustedLicense(control,keys,id,now),/another product/);}
 const rogue=issueControl(unapproved.privateKey,{licenseId:verified.claims.licenseId,systemId:id,action:'activate',revision:2},now);assert.throws(()=>verifyTrustedControl(rogue,keys,id,now),/approved software owner/);
});
test('bundled additional keys accept public Ed25519 exports and reject malformed or private input',()=>{
 assert.deepEqual(parseAdditionalKeys(JSON.stringify({version:1,publicKeys:[pem(current.publicKey)]})),[pem(current.publicKey)]);
 const bad=['{',JSON.stringify({version:2,publicKeys:[]}),JSON.stringify({version:1,publicKeys:Array(9).fill(pem(current.publicKey))}),JSON.stringify({version:1,publicKeys:[old.privateKey.export({format:'pem',type:'pkcs8'})]}),JSON.stringify({version:1,publicKeys:['invalid']})];
 for(const input of bad)assert.throws(()=>parseAdditionalKeys(input));assert.throws(()=>parseAdditionalKeys('a'.repeat(65537)));assert.throws(()=>verifyTrustedLicense(license(old.privateKey),[],id,now),/No approved/);
});
