'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os');
const {keyVault}=require('../owner/key-vault.cjs'),{keyId,issue,verify,systemId}=require('../licensing/core.cjs');
// Test provider models account-bound authenticated encryption; native DPAPI
// itself must be verified on Windows, not by this Linux test.
function provider(secret=crypto.randomBytes(32)){return {isEncryptionAvailable:()=>true,encryptString(text){const iv=crypto.randomBytes(12),c=crypto.createCipheriv('aes-256-gcm',secret,iv),b=Buffer.concat([c.update(text,'utf8'),c.final()]);return Buffer.concat([iv,c.getAuthTag(),b]);},decryptString(b){const c=crypto.createDecipheriv('aes-256-gcm',secret,b.subarray(0,12));c.setAuthTag(b.subarray(12,28));return Buffer.concat([c.update(b.subarray(28)),c.final()]).toString('utf8');}};}
test('encrypted remembered key survives restart, signs valid licences, and is forgotten on lock',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'kp-vault-')),file=path.join(dir,'owner.dpapi'),owner=crypto.generateKeyPairSync('ed25519'),options={safeStorage:provider(),file,approvedKeyIds:[keyId(owner.publicKey)],platform:'win32'};
 try{let vault=keyVault(options);assert.equal(await vault.load(),null);await vault.save(owner.privateKey);assert.equal(await vault.exists(),true);
 const bytes=await fs.readFile(file),raw=owner.privateKey.export({format:'der',type:'pkcs8'});assert.equal(bytes.includes(raw),false);assert.equal(bytes.includes(Buffer.from(raw.toString('base64'))),false);
 vault=keyVault(options);const restored=await vault.load();assert.equal(keyId(restored),keyId(owner.publicKey));const id=systemId({machineGuid:'00112233445566778899aabbccddeeff'});assert.equal(verify(issue(restored,{systemId:id,clientName:'Vault test',expiryDate:null}),owner.publicKey,id).clientName,'Vault test');
 await assert.rejects(()=>keyVault({...options,safeStorage:provider()}).load(),/cannot unlock/);await vault.forget();assert.equal(await vault.exists(),false);assert.equal(await vault.load(),null);
 }finally{await fs.rm(dir,{recursive:true,force:true});}
});
test('unavailable secure storage, unapproved keys and tampering are rejected',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'kp-vault-reject-')),file=path.join(dir,'owner.dpapi'),owner=crypto.generateKeyPairSync('ed25519'),options={safeStorage:provider(),file,approvedKeyIds:[keyId(owner.publicKey)],platform:'win32'};
 try{const vault=keyVault(options);await assert.rejects(()=>keyVault({...options,platform:'linux'}).save(owner.privateKey),/unavailable/);assert.equal(await vault.exists(),false);
 await assert.rejects(()=>vault.save(crypto.generateKeyPairSync('ed25519').privateKey),/approved owner/);assert.equal(await vault.exists(),false);await vault.save(owner.privateKey);const bytes=await fs.readFile(file);bytes[bytes.length-1]^=1;await fs.writeFile(file,bytes);await assert.rejects(()=>vault.load(),/cannot unlock/);await fs.writeFile(file,Buffer.alloc(16385));await assert.rejects(()=>vault.load(),/invalid/);
 }finally{await fs.rm(dir,{recursive:true,force:true});}
});
