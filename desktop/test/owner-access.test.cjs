'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {seal,unlock}=require('../owner/owner-access.cjs'),{keyId}=require('../licensing/core.cjs');
test('new owner access unlocks only with its separate code; no raw key or access code is bundled',()=>{
 const keys=crypto.generateKeyPairSync('ed25519'),code='KP-OWNER-'+crypto.randomBytes(18).toString('base64url'),bundle=seal(keys.privateKey,code),json=JSON.stringify(bundle),approved=[keyId(keys.publicKey)];
 assert.equal(json.includes(code),false);assert.equal(json.includes(keys.privateKey.export({type:'pkcs8',format:'der'}).toString('base64')),false);assert.equal(keyId(unlock(bundle,' '+code+'\n',approved)),approved[0]);
 assert.throws(()=>unlock(bundle,'Wrong-owner-access-code',approved),/incorrect/);assert.throws(()=>unlock(bundle,code,[]),/does not match/);
});
test('tampered encrypted owner credential and mismatched public identity are rejected',()=>{
 const keys=crypto.generateKeyPairSync('ed25519'),code='Temporary-owner-access-test',bundle=seal(keys.privateKey,code),approved=[keyId(keys.publicKey),'A'.repeat(24)];
 for(const field of ['salt','iv','ciphertext','tag']){const bytes=Buffer.from(bundle[field],'base64');bytes[0]^=1;assert.throws(()=>unlock({...bundle,[field]:bytes.toString('base64')},code,approved),/incorrect/);}
 assert.throws(()=>unlock({...bundle,ownerKeyId:'A'.repeat(24)},code,approved),/incorrect/);assert.throws(()=>unlock({...bundle,version:2},code,approved),/does not match/);
});
