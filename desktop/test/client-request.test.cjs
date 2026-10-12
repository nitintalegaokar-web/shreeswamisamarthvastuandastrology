'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {parseClientRequest,checkClientKey}=require('../owner/client-request.cjs');
const id='KP1-84C4-9E96-6994-D585-4EC7-8BBE-9CE8-C913',key='FFD543E7AFCE69618D61325E',other='D5909EAD14FB2D4717E98A8C';
test('activation request and old System ID text preserve the exact computer ID',()=>{
  assert.deepEqual(parseClientRequest('KP MASTER · Activation request · 1.2.0\nSystem ID: '+id+'\nAccepted owner Key IDs: '+key+', '+other+'\n'),{systemId:id,ownerKeyIds:[key,other]});
  assert.deepEqual(parseClientRequest('KP Master · Client System ID\n'+id+'\n'),{systemId:id,ownerKeyIds:null});
});
test('ambiguous or invalid request files cannot select a computer',()=>{
  assert.throws(()=>parseClientRequest('System ID unavailable'),/one complete/);
  assert.throws(()=>parseClientRequest(id+'\nKP1-C475-7CC2-1C63-D734-8190-6C42-5EFA-3CB3'),/one complete/);
  assert.throws(()=>parseClientRequest(id+'\nAccepted owner Key IDs: incorrect'),/invalid owner/);
  assert.throws(()=>parseClientRequest('x'.repeat(16385)),/text file/);
});
test('request-supplied Key IDs cannot authorize an unapproved owner key',()=>{
  assert.equal(checkClientKey(key,[key,other],{ownerKeyIds:[key]}),true);
  assert.throws(()=>checkClientKey(other,[key],{ownerKeyIds:[other]}),/does not match Customer/);
  assert.throws(()=>checkClientKey(key,[key,other],{ownerKeyIds:[other]}),/different owner key/);
  assert.equal(checkClientKey(key,[key],null),true);
});
