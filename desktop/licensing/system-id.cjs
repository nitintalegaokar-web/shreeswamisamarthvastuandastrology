'use strict';
const fs=require('node:fs/promises');
const path=require('node:path');
const {execFile}=require('node:child_process');
const {promisify}=require('node:util');
const {systemId}=require('./core.cjs');
const GUID=/^[a-f0-9]{32}$/;
function normalizeGuid(value){
  const guid=String(value||'').trim().replace(/[{}-]/g,'').toLowerCase();
  if(!GUID.test(guid)||/^(0+|f+)$/.test(guid))throw Error('Invalid Windows installation identifier.');
  return guid;
}
function uuid(value){try{return normalizeGuid(value);}catch{return '';}}
// Dependencies are injectable only for unit tests; the renderer cannot select
// identifiers, commands or paths. Production always reads this operating system.
function createReader({platform=process.platform,env=process.env,run=promisify(execFile),files=fs}={}){
  return async function getSystemId({cacheFile}={}){
    if(platform==='win32'){
      const root=env.SystemRoot||env.SYSTEMROOT||env.WINDIR||String.raw`C:\Windows`;
      const native=name=>path.win32.join(root,'System32',name);
      const powershell=native(String.raw`WindowsPowerShell\v1.0\powershell.exe`);
      const execute=(file,args,timeout=8000)=>run(file,args,{timeout,maxBuffer:16384,windowsHide:true,encoding:'utf8'});
      const shell=script=>execute(powershell,['-NoLogo','-NoProfile','-NonInteractive','-Command',script]);
      let machineGuid;
      try{
        const result=await execute(native('reg.exe'),['query',String.raw`HKLM\SOFTWARE\Microsoft\Cryptography`,'/v','MachineGuid','/reg:64']);
        const match=/^\s*MachineGuid\s+REG_SZ\s+(.+?)\s*$/im.exec(result.stdout.replace(/^\uFEFF/,''));
        machineGuid=normalizeGuid(match?.[1]);
      }catch{
        // Explicit Registry64 avoids redirected 32-bit registry views. PowerShell
        // uses literal single backslashes here; they are not escape characters.
        const script=String.raw`$ErrorActionPreference='Stop'; $b=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryView]::Registry64); try{$k=$b.OpenSubKey('SOFTWARE\Microsoft\Cryptography'); try{[Console]::Write([string]$k.GetValue('MachineGuid'))}finally{if($k){$k.Dispose()}}}finally{$b.Dispose()}`;
        try{machineGuid=normalizeGuid((await shell(script)).stdout.replace(/^\uFEFF/,''));}
        catch{throw Error('Cannot read the Windows installation ID. Click Retry ID. If it remains unavailable, check access to the Windows registry.');}
      }
      let cached=null;
      if(cacheFile)try{
        const text=await files.readFile(cacheFile,'utf8');if(text.length>2048)throw Error('Invalid identity cache.');
        const data=JSON.parse(text);
        if(data.version!==1||normalizeGuid(data.machineGuid)!==machineGuid||typeof data.hardwareUUID!=='string'||data.hardwareUUID&&uuid(data.hardwareUUID)!==data.hardwareUUID)throw Error('Identity cache does not match this Windows installation.');
        cached=data;
      }catch{}
      let liveUUID='';
      try{
        const script=String.raw`$ErrorActionPreference='Stop'; try{$u=Get-CimInstance -ClassName Win32_ComputerSystemProduct -OperationTimeoutSec 5 -ErrorAction Stop}catch{$u=Get-WmiObject -Class Win32_ComputerSystemProduct -ErrorAction Stop}; [Console]::Write([string]$u.UUID)`;
        liveUUID=uuid((await shell(script)).stdout.replace(/^\uFEFF/,''));
      }catch{} // WMI is optional, never a prerequisite for obtaining a System ID.
      let hardwareUUID=cached?cached.hardwareUUID:liveUUID;
      if(cached?.hardwareUUID&&liveUUID&&cached.hardwareUUID!==liveUUID)hardwareUUID=liveUUID;
      // A registry-only ID chosen during a WMI outage remains registry-only when
      // WMI returns. Cached UUID-based IDs survive temporary WMI failures. The
      // cache is accepted only after checking the live Windows MachineGuid.
      const identifier=systemId({machineGuid,hardwareUUID});
      if(cacheFile&&(!cached||cached.hardwareUUID!==hardwareUUID)){
        try{
          await files.mkdir(path.dirname(cacheFile),{recursive:true});
          await files.writeFile(cacheFile+'.tmp',JSON.stringify({version:1,machineGuid,hardwareUUID}),{encoding:'utf8',mode:0o600});
          await files.rename(cacheFile+'.tmp',cacheFile);
        }catch{throw Error('Cannot save the Windows System ID. Check access to the application-data folder, then click Retry ID.');}
      }
      return identifier;
    }
    if(platform==='linux')return systemId({machineGuid:(await files.readFile('/etc/machine-id','utf8')).trim()});
    throw Error('System-ID activation is supported on Windows computers.');
  };
}
module.exports={getSystemId:createReader(),createReader};
