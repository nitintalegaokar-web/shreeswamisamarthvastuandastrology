'use strict';
const fs=require('node:fs/promises');
const path=require('node:path');
const {execFile}=require('node:child_process');
const {promisify}=require('node:util');
const {systemId}=require('./core.cjs');
async function getSystemId(){
  if(process.platform==='win32'){
    const powershell=path.join(process.env.SystemRoot||'C:\\Windows','System32','WindowsPowerShell','v1.0','powershell.exe');
    const script='$ErrorActionPreference="Stop"; $g=(Get-ItemProperty -LiteralPath "HKLM:\\SOFTWARE\\Microsoft\\Cryptography" -Name MachineGuid).MachineGuid; $u=(Get-CimInstance -ClassName Win32_ComputerSystemProduct -OperationTimeoutSec 5).UUID; @{machineGuid=$g;hardwareUUID=$u}|ConvertTo-Json -Compress';
    try{const result=await promisify(execFile)(powershell,['-NoLogo','-NoProfile','-NonInteractive','-Command',script],{timeout:15000,maxBuffer:16384,windowsHide:true});return systemId(JSON.parse(result.stdout.replace(/^\uFEFF/,'')));}
    catch{throw Error('Cannot read the Windows System ID. Ensure Windows Management Instrumentation is running, then restart the software.');}
  }
  // Linux developer tests use the stable operating-system installation ID.
  // There is no environment flag or random-ID fallback that disables licensing.
  if(process.platform==='linux')return systemId({machineGuid:(await fs.readFile('/etc/machine-id','utf8')).trim()});
  throw Error('System-ID activation is supported on Windows computers.');
}
module.exports={getSystemId};
