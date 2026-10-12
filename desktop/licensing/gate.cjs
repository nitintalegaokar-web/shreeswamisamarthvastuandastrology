'use strict';
const {ipcMain,dialog,clipboard,BrowserWindow}=require('electron');
const fs=require('node:fs/promises');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {getSystemId}=require('./system-id.cjs');
const {keyId,verifyControl,applyControl}=require('./core.cjs');
const {parseAdditionalKeys,approvedKeys,verifyTrustedLicense,verifyTrustedControl}=require('./trust.cjs');
async function createGate(app,win,indexPath){
  const activationPath=path.join(__dirname,'activation.html');
  const activationURL=pathToFileURL(activationPath).href,indexURL=pathToFileURL(indexPath).href;
  const licensePath=path.join(app.getPath('userData'),'system-license.json');
  const identityPath=path.join(app.getPath('userData'),'system-identity.json');
  const controlsPath=path.join(app.getPath('userData'),'license-status.json');
  let id='',keys=[],configurationError='',claims=null,message='Activation is required.';
  let configuring;
  async function configure(){
    if(configuring)return configuring;
    configuring=(async()=>{
      id='';keys=[];configurationError='';claims=null;
      try{id=await getSystemId({cacheFile:identityPath});const folder=path.join(__dirname,'..','app'),primary=await fs.readFile(path.join(folder,'owner-public-key.pem'),'utf8'),extra=parseAdditionalKeys(await fs.readFile(path.join(folder,'additional-owner-public-keys.json'),'utf8'));keys=approvedKeys(primary,extra);}
      catch(error){configurationError=error.message;message=configurationError;}
    })();
    try{await configuring;}finally{configuring=null;}
  }
  await configure();
  const trusted=event=>event.sender===win.webContents&&event.senderFrame?.url.split('#')[0]===activationURL;
  function check(event){if(!trusted(event))throw Error('Untrusted activation request.');}
  async function controls(){
    try{const text=await fs.readFile(controlsPath,'utf8');if(text.length>1024*1024)throw Error('The saved license-status data is too large.');const data=JSON.parse(text);if(!data||typeof data!=='object'||Array.isArray(data))throw Error('Invalid license-status data.');return data;}
    catch(error){if(error.code==='ENOENT')return {};throw error;}
  }
  async function checkControl(nextClaims,signingKey){const current=(await controls())[nextClaims.licenseId];if(current&&verifyControl(current,signingKey,id).action==='deactivate')throw Error('This license was deactivated by the owner. Import the latest activation status file.');}
  async function refresh(){
    if(configurationError){claims=null;return;}
    let nextClaims=null,nextMessage='';
    try{if((await fs.stat(licensePath)).size>16384)throw Error('The license file is too large.');const verified=verifyTrustedLicense(await fs.readFile(licensePath,'utf8'),keys,id);nextClaims=verified.claims;await checkControl(nextClaims,verified.key);nextMessage='Activated';}
    catch(error){nextClaims=null;nextMessage=error.code==='ENOENT'?'Activation is required.':error.message;}
    claims=nextClaims;message=nextMessage;
  }
  const status=()=>({systemId:id,active:Boolean(claims),message,configured:!configurationError,ownerKeyIds:keys.map(keyId)});
  ipcMain.handle('kp-license:status',event=>{check(event);return status();});
  ipcMain.handle('kp-license:retry',async event=>{
    check(event);await configure();await refresh();const result=status();
    if(claims){win.setMinimumSize(950,650);win.setSize(1440,950);await win.loadFile(indexPath);}
    return result;
  });
  ipcMain.handle('kp-license:import-control',async event=>{
    const url=event.senderFrame?.url.split('#')[0];if(event.sender!==win.webContents||url!==activationURL&&!(claims&&url===indexURL))throw Error('Untrusted license-status request.');
    if(configurationError)throw Error(configurationError);
    const selected=await dialog.showOpenDialog(win,{title:'Import signed owner license status',properties:['openFile'],filters:[{name:'KP License Status',extensions:['kpcontrol']}]});if(selected.canceled||!selected.filePaths.length)return null;
    const file=selected.filePaths[0];if((await fs.stat(file)).size>16384)throw Error('The status file is too large.');
    const control=JSON.parse(await fs.readFile(file,'utf8')),verified=verifyTrustedControl(control,keys,id),command=verified.claims;
    let saved;try{if((await fs.stat(licensePath)).size>16384)throw Error('The license file is too large.');saved=verifyTrustedLicense(await fs.readFile(licensePath,'utf8'),keys,id);}catch(error){if(error.code==='ENOENT')throw Error('Import the activation license before applying a status file.');throw error;}
    if(saved.claims.licenseId!==command.licenseId)throw Error('This status file belongs to another license. Use the status file for this installed license.');
    if(saved.ownerKeyId!==verified.ownerKeyId)throw Error('This status file must be signed by the owner key that issued this license.');
    const next=applyControl(await controls(),control,verified.key,id);
    await fs.mkdir(path.dirname(controlsPath),{recursive:true});await fs.writeFile(controlsPath+'.tmp',JSON.stringify(next),{encoding:'utf8',mode:0o600});await fs.rename(controlsPath+'.tmp',controlsPath);await refresh();
    if(!claims){for(const popup of BrowserWindow.getAllWindows())if(popup!==win)popup.destroy();await win.loadFile(activationPath);}
    else if(url===activationURL){win.setMinimumSize(950,650);win.setSize(1440,950);await win.loadFile(indexPath);}
    return {action:command.action,active:Boolean(claims)};
  });
  ipcMain.handle('kp-license:copy-id',event=>{check(event);if(!id)throw Error(message);clipboard.writeText(id);return true;});
  ipcMain.handle('kp-license:export-id',async event=>{
    check(event);if(!id)throw Error(message);
    const selected=await dialog.showSaveDialog(win,{title:'Save customer activation request',defaultPath:path.join(app.getPath('documents'),'KP-System-ID.txt'),filters:[{name:'System ID',extensions:['txt']}]});
    if(selected.canceled||!selected.filePath)return false;
    await fs.writeFile(selected.filePath,'KP MASTER · Activation request · '+app.getVersion()+'\nSystem ID: '+id+'\nAccepted owner Key IDs: '+keys.map(keyId).join(', ')+'\n','utf8');return true;
  });
  ipcMain.handle('kp-license:activate',async event=>{
    check(event);if(configurationError)throw Error(configurationError);
    const selected=await dialog.showOpenDialog(win,{title:'Import owner activation license',properties:['openFile'],filters:[{name:'KP Activation License',extensions:['kplicense']}]});
    if(selected.canceled||!selected.filePaths.length)return false;
    const file=selected.filePaths[0];if((await fs.stat(file)).size>16384)throw Error('The license file is too large.');
    const text=await fs.readFile(file,'utf8'),verified=verifyTrustedLicense(text,keys,id);await checkControl(verified.claims,verified.key);
    await fs.mkdir(path.dirname(licensePath),{recursive:true});
    await fs.writeFile(licensePath+'.tmp',text,{encoding:'utf8',mode:0o600});await fs.rename(licensePath+'.tmp',licensePath);
    await refresh();if(!claims)throw Error(message);
    win.setMinimumSize(950,650);win.setSize(1440,950);await win.loadFile(indexPath);return true;
  });
  await refresh();
  await win.loadFile(claims?indexPath:activationPath);
  const timer=setInterval(async()=>{
    if(win.isDestroyed())return;
    const wasActive=Boolean(claims);await refresh();
    if(wasActive&&!claims){for(const popup of BrowserWindow.getAllWindows())if(popup!==win)popup.destroy();await win.loadFile(activationPath);}
  },60000);timer.unref();win.on('closed',()=>clearInterval(timer));
  return {isActive:()=>Boolean(claims),activationURL};
}
module.exports={createGate};
