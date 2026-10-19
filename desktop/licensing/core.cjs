'use strict';
const crypto=require('node:crypto');
const {normalizeFeatures,edition}=require('./feature-policy.cjs');
const PRODUCT='kp-master-offline';
const SYSTEM_ID=/^KP1-(?:[A-F0-9]{4}-){7}[A-F0-9]{4}$/;
function systemId(input){
  const guid=String(input.machineGuid||'').replace(/[{}-]/g,'').toLowerCase();
  if(!/^[a-f0-9]{32}$/.test(guid)||/^(0+|f+)$/.test(guid))throw Error('A stable computer identifier is unavailable.');
  const uuid=String(input.hardwareUUID||'').replace(/[{}-]/g,'').toLowerCase();
  if(uuid&&!/^[a-f0-9]{32}$/.test(uuid))throw Error('The hardware identifier is invalid.');
  const hardware=/^(0+|f+)$/.test(uuid)?'':uuid;
  const hash=crypto.createHash('sha256').update(JSON.stringify([PRODUCT,1,guid,hardware])).digest('hex').slice(0,32).toUpperCase();
  return 'KP1-'+hash.match(/.{4}/g).join('-');
}
function normalizedId(id){const value=String(id||'').trim().toUpperCase();if(!SYSTEM_ID.test(value))throw Error('Enter the complete client System ID.');return value;}
function publicKey(key){const parsed=key?.type==='public'?key:crypto.createPublicKey(key);if(parsed.asymmetricKeyType!=='ed25519')throw Error('An Ed25519 owner public key is required.');return parsed;}
function keyId(key){return crypto.createHash('sha256').update(publicKey(key).export({type:'spki',format:'der'})).digest('hex').slice(0,24).toUpperCase();}
function issue(privateKey,request,now=new Date()){
  if(privateKey.asymmetricKeyType!=='ed25519')throw Error('An Ed25519 owner key is required.');
  const id=normalizedId(request.systemId),client=String(request.clientName||'').trim();
  if(!client||client.length>160||/[\x00-\x1f]/.test(client))throw Error('Enter a client name of 1–160 characters.');
  let expiresAt=null;
  if(request.expiryDate!==null&&request.expiryDate!==undefined){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(request.expiryDate))throw Error('Choose a valid expiry date.');
    const date=new Date(request.expiryDate+'T23:59:59.999Z');
    if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==request.expiryDate||date<now)throw Error('Choose an expiry date on or after today.');
    expiresAt=date.toISOString();
  }
  const claims={product:PRODUCT,version:1,licenseId:crypto.randomUUID(),systemId:id,clientName:client,issuedAt:now.toISOString(),expiresAt};
  if(request.features!==undefined){claims.features=normalizeFeatures(request.features);claims.edition=edition(request.edition);}
  const data=Buffer.from(JSON.stringify(claims),'utf8');
  return {payload:data.toString('base64url'),signature:crypto.sign(null,data,privateKey).toString('base64url')};
}
function signedClaims(license,key){
  if(typeof license==='string'){if(Buffer.byteLength(license)>16384)throw Error('The license file is too large.');try{license=JSON.parse(license);}catch{throw Error('Choose a valid KP license file.');}}
  if(!license||typeof license.payload!=='string'||typeof license.signature!=='string'||license.payload.length>12000||!/^[A-Za-z0-9_-]+$/.test(license.payload)||!/^[A-Za-z0-9_-]+$/.test(license.signature))throw Error('Choose a valid KP license file.');
  const data=Buffer.from(license.payload,'base64url'),signature=Buffer.from(license.signature,'base64url');
  if(signature.length!==64||!crypto.verify(null,data,publicKey(key),signature)){const error=Error('This license was not issued by your software owner, or has been changed.');error.code='KP_OWNER_SIGNATURE';throw error;}
  let claims;try{claims=JSON.parse(data.toString('utf8'));}catch{throw Error('The license data is invalid.');}
  return claims;
}
function verify(license,key,id,now=new Date()){
  const claims=signedClaims(license,key);
  if(claims.kind==='customer-registration')throw Error('This is a registration key, not a purchase key.');
  if(claims.kind&&claims.kind!=='customer-purchase')throw Error('This license belongs to another product or version.');
  if(claims.product!==PRODUCT||claims.version!==1||typeof claims.licenseId!=='string'||!claims.licenseId||typeof claims.clientName!=='string'||!claims.clientName)throw Error('This license belongs to another product or version.');
  if(normalizedId(claims.systemId)!==normalizedId(id))throw Error('This license belongs to a different computer. Send this computer’s System ID to the owner.');
  if(claims.features!==undefined){normalizeFeatures(claims.features);edition(claims.edition);}
  const issued=Date.parse(claims.issuedAt);
  if(!Number.isFinite(issued)||issued>now.getTime()+5*60000)throw Error('Check the computer date and time before activating.');
  if(claims.expiresAt!==null){const expires=Date.parse(claims.expiresAt);if(!Number.isFinite(expires)||expires<issued)throw Error('The license expiry is invalid.');if(now.getTime()>expires)throw Error('This license has expired. Contact the owner for renewal.');}
  return Object.freeze(claims);
}
const LICENSE_ID=/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i;
function issueControl(privateKey,request,now=new Date()){
  if(privateKey.asymmetricKeyType!=='ed25519')throw Error('An Ed25519 owner key is required.');
  if(!LICENSE_ID.test(request.licenseId)||!['activate','deactivate'].includes(request.action)||!Number.isSafeInteger(request.revision)||request.revision<1)throw Error('Choose a valid issued license and status action.');
  const claims={product:PRODUCT,version:1,kind:'license-status',commandId:crypto.randomUUID(),licenseId:request.licenseId,systemId:normalizedId(request.systemId),action:request.action,revision:request.revision,issuedAt:now.toISOString()};
  const data=Buffer.from(JSON.stringify(claims),'utf8');
  return {payload:data.toString('base64url'),signature:crypto.sign(null,data,privateKey).toString('base64url')};
}
function verifyControl(control,key,id,now=new Date()){
  const c=signedClaims(control,key);
  if(c.product!==PRODUCT||c.version!==1||c.kind!=='license-status'||!LICENSE_ID.test(c.licenseId)||!LICENSE_ID.test(c.commandId)||!['activate','deactivate'].includes(c.action)||!Number.isSafeInteger(c.revision)||c.revision<1)throw Error('Choose a valid owner license-status file.');
  if(normalizedId(c.systemId)!==normalizedId(id))throw Error('This status file belongs to a different computer.');
  const issued=Date.parse(c.issuedAt);if(!Number.isFinite(issued)||issued>now.getTime()+5*60000)throw Error('Check the computer date and time before applying this status file.');
  return Object.freeze(c);
}
function applyControl(controls,control,key,id,now=new Date()){
  const c=verifyControl(control,key,id,now),old=controls[c.licenseId];
  if(old){const previous=verifyControl(old,key,id,now);if(c.revision<previous.revision||c.revision===previous.revision&&c.commandId!==previous.commandId)throw Error('This status file is older than the status already applied. Import the latest owner file.');}
  return {...controls,[c.licenseId]:control};
}
function registrationId(key,request){const id=normalizedId(request.systemId),client=String(request.clientName||'').trim();if(!client||client.length>160||/[\x00-\x1f]/.test(client))throw Error('Enter a valid client name.');const h=crypto.createHash('sha256').update(JSON.stringify([keyId(key),id,client.toLowerCase()])).digest('hex').slice(0,32);return [h.slice(0,8),h.slice(8,12),h.slice(12,16),h.slice(16,20),h.slice(20)].join('-');}
function envelope(privateKey,claims){const data=Buffer.from(JSON.stringify(claims),'utf8');return {payload:data.toString('base64url'),signature:crypto.sign(null,data,privateKey).toString('base64url')};}
function issueRegistration(privateKey,request,now=new Date()){const registration=registrationId(privateKey,request);return envelope(privateKey,{product:PRODUCT,version:1,kind:'customer-registration',licenseId:registration,registrationId:registration,systemId:normalizedId(request.systemId),clientName:String(request.clientName).trim(),issuedAt:now.toISOString(),expiresAt:null});}
function issuePurchase(privateKey,request,now=new Date()){const base=issue(privateKey,request,now),claims=JSON.parse(Buffer.from(base.payload,'base64url'));return envelope(privateKey,{...claims,kind:'customer-purchase',registrationId:registrationId(privateKey,request)});}
function verifyRegistration(input,key,id,now=new Date()){const c=signedClaims(input,key);if(c.product!==PRODUCT||c.version!==1||c.kind!=='customer-registration'||!LICENSE_ID.test(c.registrationId)||c.licenseId!==c.registrationId||!c.clientName||c.expiresAt!==null||normalizedId(c.systemId)!==normalizedId(id))throw Error('Choose the registration key for this device.');const issued=Date.parse(c.issuedAt);if(!Number.isFinite(issued)||issued>now.getTime()+300000)throw Error('Check the device date and time.');return Object.freeze(c);}
module.exports={PRODUCT,SYSTEM_ID,systemId,normalizedId,publicKey,keyId,issue,verify,issueControl,verifyControl,applyControl,issueRegistration,issuePurchase,verifyRegistration,registrationId};
