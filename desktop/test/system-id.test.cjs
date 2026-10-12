'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const os=require('node:os');
const {createReader}=require('../licensing/system-id.cjs');
const {systemId}=require('../licensing/core.cjs');
const guid='00112233-4455-6677-8899-aabbccddeeff';
const hardware='12345678-1234-1234-1234-123456789abc';
const otherGuid='10112233-4455-6677-8899-aabbccddeeff';
const otherHardware='22345678-1234-1234-1234-123456789abc';
function simulated({machine=guid,hardwareUUID=hardware,regFails=false,shellRegistryFails=false,hardwareFails=false}={}){
  const calls=[];
  const run=async(file,args,options)=>{
    calls.push({file,args,options});
    if(path.win32.basename(file)==='reg.exe'){
      if(regFails)throw Error('reg unavailable');
      return {stdout:'\r\nHKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography\r\n    MachineGuid    REG_SZ    '+machine+'\r\n'};
    }
    if(args.at(-1).includes('OpenBaseKey')){
      if(shellRegistryFails)throw Error('registry denied');
      return {stdout:'\uFEFF'+machine+'\r\n'};
    }
    if(hardwareFails)throw Error('WMI disabled or PowerShell blocked');
    return {stdout:'\uFEFF'+hardwareUUID+'\r\n'};
  };
  return {read:createReader({platform:'win32',env:{SystemRoot:String.raw`C:\Windows`},run}),calls};
}
async function cache(t){const dir=await fs.mkdtemp(path.join(os.tmpdir(),'kp-id-unit-'));t.after(()=>fs.rm(dir,{recursive:true,force:true}));return path.join(dir,'system-identity.json');}
test('Windows uses literal native paths and Registry64; healthy IDs match earlier releases',async()=>{
  const {read,calls}=simulated();assert.equal(await read(),systemId({machineGuid:guid,hardwareUUID:hardware}));
  assert.equal(calls[0].file,String.raw`C:\Windows\System32\reg.exe`);
  assert.deepEqual(calls[0].args,['query',String.raw`HKLM\SOFTWARE\Microsoft\Cryptography`,'/v','MachineGuid','/reg:64']);
  assert.equal(calls[1].file,String.raw`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`);
  assert.match(calls[1].args.at(-1),/Get-CimInstance/);assert.match(calls[1].args.at(-1),/Get-WmiObject/);
  for(const c of calls){assert.equal(c.options.windowsHide,true);assert.equal(c.options.timeout,8000);}
});
test('Registry64 PowerShell fallback uses single-backslash subkey and handles BOM',async()=>{
  const {read,calls}=simulated({regFails:true});assert.equal(await read(),systemId({machineGuid:guid,hardwareUUID:hardware}));
  const script=calls[1].args.at(-1);assert.match(script,/RegistryView\]::Registry64/);
  assert.ok(script.includes(String.raw`'SOFTWARE\Microsoft\Cryptography'`));
  assert.ok(!script.includes(String.raw`SOFTWARE\\Microsoft`));
});
test('Missing WMI or blocked PowerShell still yields a stable Windows registry ID',async t=>{
  const file=await cache(t),unavailable=simulated({hardwareFails:true});
  const id=await unavailable.read({cacheFile:file});assert.equal(id,systemId({machineGuid:guid}));
  assert.equal(await unavailable.read({cacheFile:file}),id);
  assert.equal(await simulated().read({cacheFile:file}),id,'Restoring WMI must not change the already-issued ID.');
  assert.equal(JSON.parse(await fs.readFile(file,'utf8')).hardwareUUID,'');
});
test('Cached UUID-based IDs survive WMI outages while hardware changes require a new ID',async t=>{
  const file=await cache(t),id=await simulated().read({cacheFile:file});
  assert.equal(await simulated({hardwareFails:true}).read({cacheFile:file}),id);
  assert.equal(await simulated().read({cacheFile:file}),id);
  const changed=await simulated({hardwareUUID:otherHardware}).read({cacheFile:file});
  assert.notEqual(changed,id);assert.equal(changed,systemId({machineGuid:guid,hardwareUUID:otherHardware}));
});
test('Copying an identity cache to another Windows installation does not copy its System ID',async t=>{
  const file=await cache(t),first=await simulated().read({cacheFile:file});
  const second=await simulated({machine:otherGuid,hardwareFails:true}).read({cacheFile:file});
  assert.notEqual(second,first);assert.equal(second,systemId({machineGuid:otherGuid}));
  assert.equal(JSON.parse(await fs.readFile(file,'utf8')).machineGuid,otherGuid.replace(/-/g,''));
});
test('Invalid SMBIOS values fall back to the actual installation ID',async()=>{
  for(const hardwareUUID of ['', '00000000-0000-0000-0000-000000000000','FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF','vendor-default']){
    assert.equal(await simulated({hardwareUUID}).read(),systemId({machineGuid:guid}));
  }
});
test('Missing or invalid real MachineGuid never generates a random ID or trusts a copied cache',async t=>{
  const file=await cache(t);await simulated().read({cacheFile:file});
  await assert.rejects(()=>simulated({regFails:true,shellRegistryFails:true}).read({cacheFile:file}),/Windows installation ID/);
  for(const machine of ['', '0'.repeat(32),'f'.repeat(32),'invalid']){
    await assert.rejects(()=>simulated({machine}).read({cacheFile:file}),/Windows installation ID/);
  }
});
test('A malformed identity cache is rebuilt from real identifiers',async t=>{
  const file=await cache(t);await fs.writeFile(file,'{');
  assert.equal(await simulated().read({cacheFile:file}),systemId({machineGuid:guid,hardwareUUID:hardware}));
  assert.equal(JSON.parse(await fs.readFile(file,'utf8')).version,1);
});
test('Identity cache persistence failures report a writable-folder problem',async()=>{
  const read=createReader({platform:'win32',env:{},run:async(file,args,options)=>{
    if(path.win32.basename(file)==='reg.exe')return {stdout:'MachineGuid REG_SZ '+guid};
    throw Error('WMI unavailable');
  },files:{readFile:async()=>{throw Error('missing');},mkdir:async()=>{throw Error('denied');}}});
  await assert.rejects(()=>read({cacheFile:'/tmp/no-write.json'}),/application-data folder/);
});
