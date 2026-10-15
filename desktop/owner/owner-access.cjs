'use strict';
// A public installer carries only an authenticated encrypted owner credential.
// The random access code is delivered separately to the owner, never bundled.
const crypto=require('node:crypto');
const {keyId}=require('./license-core.cjs');
function derive(code,salt){if(typeof code!=='string'||code.trim().length<12||code.length>128)throw Error('Enter the complete owner access code.');return crypto.scryptSync(code.trim(),salt,32,{N:32768,r:8,p:1,maxmem:64*1024*1024});}
function seal(key,code){
 const salt=crypto.randomBytes(16),iv=crypto.randomBytes(12),derived=derive(code,salt),plain=key.export({format:'der',type:'pkcs8'});
 try{const cipher=crypto.createCipheriv('aes-256-gcm',derived,iv),encrypted=Buffer.concat([cipher.update(plain),cipher.final()]);return {version:1,ownerKeyId:keyId(key),salt:salt.toString('base64'),iv:iv.toString('base64'),ciphertext:encrypted.toString('base64'),tag:cipher.getAuthTag().toString('base64')};}
 finally{derived.fill(0);plain.fill(0);}
}
function unlock(bundle,code,approved){
 if(!bundle||bundle.version!==1||!approved.includes(bundle.ownerKeyId))throw Error('The owner access package does not match this software.');
 let derived,plain;
 try{
  const field=(name,length)=>{if(typeof bundle[name]!=='string'||bundle[name].length>1024||!/^[A-Za-z0-9+/]+={0,2}$/.test(bundle[name]))throw Error('Invalid owner access package.');const b=Buffer.from(bundle[name],'base64');if(length&&b.length!==length)throw Error('Invalid owner access package.');return b;};
  const salt=field('salt',16),iv=field('iv',12),tag=field('tag',16),bytes=field('ciphertext');derived=derive(code,salt);const decipher=crypto.createDecipheriv('aes-256-gcm',derived,iv);decipher.setAuthTag(tag);plain=Buffer.concat([decipher.update(bytes),decipher.final()]);
  const key=crypto.createPrivateKey({key:plain,type:'pkcs8',format:'der'});if(key.asymmetricKeyType!=='ed25519'||keyId(key)!==bundle.ownerKeyId)throw Error('Invalid owner access package.');return key;
 }catch{throw Error('The owner access code is incorrect. Copy the complete new code supplied with this version.');}
 finally{derived?.fill(0);plain?.fill(0);}
}
module.exports={seal,unlock};
