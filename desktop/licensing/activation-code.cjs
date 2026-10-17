'use strict';
// Text transport for the existing signed envelopes. No signing or licence rules
// change: recipients still verify owner, device, dates and control revisions.
function toCode(envelope,status=false){
 if(!envelope||typeof envelope.payload!=='string'||typeof envelope.signature!=='string')throw Error('Invalid signed activation data.');
 const registration=!status&&JSON.parse(Buffer.from(envelope.payload,'base64url')).kind==='customer-registration';
 const code=(status?'KP-S1.':registration?'KP-R1.':'KP-A1.')+envelope.payload+'.'+envelope.signature;fromCode(code,status);return code;
}
function fromCode(text,status=false){
 if(typeof text!=='string'||text.length>16384)throw Error('Paste the complete key supplied by the owner.');
 const code=text.replace(/\s/g,''),parts=code.split('.');
 if(parts.length!==3||!(status?parts[0]==='KP-S1':['KP-A1','KP-R1'].includes(parts[0]))||! /^[A-Za-z0-9_-]{1,12000}$/.test(parts[1])||! /^[A-Za-z0-9_-]{86}$/.test(parts[2]))throw Error(status?'Paste a valid Activate / Deactivate status key (KP-S1…).':'Paste a valid activation key (KP-A1…).');
 return JSON.stringify({payload:parts[1],signature:parts[2]});
}
module.exports={toCode,fromCode};
