'use strict';
const {normalizedId}=require('./license-core.cjs');
function parseClientRequest(text){
  if(typeof text!=='string'||Buffer.byteLength(text)>16384)throw Error('Choose the customer System ID text file.');
  const ids=[...new Set(text.toUpperCase().match(/\bKP1-(?:[A-F0-9]{4}-){7}[A-F0-9]{4}\b/g)||[])];
  if(ids.length!==1)throw Error('The request must contain exactly one complete customer System ID.');
  const line=text.match(/^Accepted owner Key IDs:\s*([^\r\n]+)$/mi);let ownerKeyIds=null;
  if(line){ownerKeyIds=line[1].split(',').map(id=>id.trim().toUpperCase());if(!ownerKeyIds.length||ownerKeyIds.length>9||ownerKeyIds.some(id=>!/^[A-F0-9]{24}$/.test(id)))throw Error('The customer request contains invalid owner Key IDs.');}
  return {systemId:normalizedId(ids[0]),ownerKeyIds};
}
function checkClientKey(id,approved,request){
  if(!approved.includes(id))throw Error('This owner key does not match Customer 1.2.7. Open your existing approved owner key. Accepted Key IDs: '+approved.join(', ')+'.');
  if(request?.ownerKeyIds&&!request.ownerKeyIds.includes(id))throw Error('This customer request uses a different owner key. Install Customer 1.2.7 on the customer device, then save and open a NEW System ID file.');
  return true;
}
module.exports={parseClientRequest,checkClientKey};
