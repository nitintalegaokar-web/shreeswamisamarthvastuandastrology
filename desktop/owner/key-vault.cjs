'use strict';
// Only the main process sees private key material. Windows DPAPI binds this
// local convenience copy to the current Windows account and computer.
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const {keyId}=require('./license-core.cjs');
function keyVault({safeStorage,file,approvedKeyIds,platform=process.platform}){
 const available=()=>platform==='win32'&&safeStorage.isEncryptionAvailable();
 async function exists(){try{await fs.access(file);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}}
 async function forget(){await fs.rm(file,{force:true});}
 async function save(key){
  if(!available())throw Error('Secure remembering is unavailable. You can still open your encrypted key for this session.');
  if(key.asymmetricKeyType!=='ed25519'||!approvedKeyIds.includes(keyId(key)))throw Error('Only an approved owner key can be remembered.');
  const bytes=safeStorage.encryptString(key.export({type:'pkcs8',format:'der'}).toString('base64'));
  await fs.mkdir(path.dirname(file),{recursive:true});const temp=file+'.tmp';
  try{await fs.writeFile(temp,bytes,{mode:0o600});await fs.rename(temp,file);}finally{await fs.rm(temp,{force:true});}
 }
 async function load(){
  if(!await exists())return null;
  if(!available())throw Error('Windows cannot unlock the remembered key. Open your original encrypted key again.');
  if((await fs.stat(file)).size>16384)throw Error('The remembered key is invalid. Open your original encrypted key again.');
  let key;try{key=crypto.createPrivateKey({key:Buffer.from(safeStorage.decryptString(await fs.readFile(file)),'base64'),format:'der',type:'pkcs8'});}catch{throw Error('Windows cannot unlock the remembered key. Open your original encrypted key again.');}
  if(key.asymmetricKeyType!=='ed25519'||!approvedKeyIds.includes(keyId(key)))throw Error('The remembered key is not approved for this software.');
  return key;
 }
 return {available,exists,save,load,forget};
}
module.exports={keyVault};
