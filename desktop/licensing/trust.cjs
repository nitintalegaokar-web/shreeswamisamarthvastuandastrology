'use strict';
const {publicKey,keyId,verify,verifyControl,verifyRegistration}=require('./core.cjs');
// This list is bundled by the builder. Keys supplied by a license or renderer
// never become trusted, and only explicitly approved public keys are packaged.
function parseAdditionalKeys(text){
  if(typeof text!=='string'||Buffer.byteLength(text)>65536)throw Error('Invalid bundled owner public-key list.');
  let data;try{data=JSON.parse(text);}catch{throw Error('Invalid bundled owner public-key list.');}
  if(!data||data.version!==1||!Array.isArray(data.publicKeys)||data.publicKeys.length>8)throw Error('Invalid bundled owner public-key list.');
  return data.publicKeys.map(pem=>{
    if(typeof pem!=='string'||!pem.includes('-----BEGIN PUBLIC KEY-----')||pem.includes('PRIVATE KEY'))throw Error('Use only exported PUBLIC keys in the bundled owner public-key list.');
    return publicKey(pem).export({type:'spki',format:'pem'});
  });
}
function approvedKeys(primary,additional=[]){
  const keys=new Map();for(const pem of [primary,...additional]){const key=publicKey(pem);keys.set(keyId(key),key);}return [...keys.values()];
}
function verifyTrusted(input,keys,id,now,check){
  if(!Array.isArray(keys)||!keys.length)throw Error('No approved owner public key is configured.');
  for(const key of keys){
    try{return {claims:check(input,key,id,now),key,ownerKeyId:keyId(key)};}
    catch(error){if(error.code!=='KP_OWNER_SIGNATURE')throw error;}
  }
  throw Error('This license was not issued by an approved software owner, or has been changed. Accepted owner Key IDs: '+keys.map(keyId).join(', ')+'.');
}
function verifyTrustedLicense(input,keys,id,now=new Date()){return verifyTrusted(input,keys,id,now,verify);}
function verifyTrustedControl(input,keys,id,now=new Date()){return verifyTrusted(input,keys,id,now,verifyControl);}
function verifyTrustedRegistration(input,keys,id,now=new Date()){return verifyTrusted(input,keys,id,now,verifyRegistration);}
module.exports={verifyTrustedRegistration,parseAdditionalKeys,approvedKeys,verifyTrustedLicense,verifyTrustedControl};
