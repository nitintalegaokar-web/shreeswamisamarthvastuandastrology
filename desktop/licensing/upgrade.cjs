'use strict';
const {entitlements}=require('./feature-policy.cjs');
function validateUpgrade(current,next){
 if(current.ownerKeyId!==next.ownerKeyId)throw Error('Use an upgrade issued by the owner who activated this package.');
 const a=current.claims,b=next.claims;
 if(b.kind!=='customer-purchase'||a.systemId!==b.systemId||!a.registrationId||a.registrationId!==b.registrationId||a.clientName.trim().toLowerCase()!==b.clientName.trim().toLowerCase())throw Error('Choose the upgrade file for this registered customer and device.');
 if(a.licenseId===b.licenseId)throw Error('This package is already installed.');
 const previous=entitlements(a),granted=new Set(entitlements(b));
 if(previous.some(id=>!granted.has(id)))throw Error('This file removes purchased features. Ask the owner for an upgrade that includes your existing features.');
 if((!a.expiresAt&&b.expiresAt)||(a.expiresAt&&b.expiresAt&&Date.parse(b.expiresAt)<Date.parse(a.expiresAt)))throw Error('An upgrade must preserve or extend your current activation period.');
 if(Date.parse(b.issuedAt)<Date.parse(a.issuedAt))throw Error('Choose the latest upgrade file.');
 return b;
}
module.exports={validateUpgrade};
