'use strict';
const {app,BrowserWindow,ipcMain,dialog,Menu,session}=require('electron');
const fs=require('node:fs/promises');
const path=require('node:path');
const crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {issue,keyId,issueControl}=require('./license-core.cjs');
const ownerPath=path.join(__dirname,'index.html'),ownerURL=pathToFileURL(ownerPath).href;
let win,privateKey=null,publicPem='',privateFile='';
const cleanName=name=>String(name).replace(/[<>:"/\\|?*\x00-\x1f]/g,'_').replace(/[. ]+$/,'').slice(0,100);
function trusted(event){if(event.sender!==win.webContents||event.senderFrame?.url!==ownerURL)throw Error('Untrusted owner-tool request.');}
function requireKey(){if(!privateKey)throw Error('Create or open your owner key first.');}
function password(value){if(typeof value!=='string'||value.length<12||value.length>512)throw Error('Use an owner-key password of 12–512 characters.');return value;}
function setKey(key,file){if(key.asymmetricKeyType!=='ed25519')throw Error('Choose an Ed25519 owner key.');privateKey=key;publicPem=crypto.createPublicKey(key).export({format:'pem',type:'spki'});privateFile=file;}
function status(){return {unlocked:Boolean(privateKey),keyId:privateKey?keyId(publicPem):'',filename:privateFile?path.basename(privateFile):''};}
async function history(){try{return JSON.parse(await fs.readFile(path.join(app.getPath('userData'),'issued-licenses.json'),'utf8'));}catch{return [];}}
async function saveHistory(list){await fs.mkdir(app.getPath('userData'),{recursive:true});await fs.writeFile(path.join(app.getPath('userData'),'issued-licenses.json'),JSON.stringify(list.slice(0,5000),null,2),{encoding:'utf8',mode:0o600});}
if(!app.requestSingleInstanceLock())app.quit();else{
app.on('second-instance',()=>{if(win){if(win.isMinimized())win.restore();win.focus();}});
app.whenReady().then(()=>{
  Menu.setApplicationMenu(null);
  session.defaultSession.webRequest.onBeforeRequest({urls:['http://*/*','https://*/*','ws://*/*','wss://*/*']},(_details,callback)=>callback({cancel:true}));
  session.defaultSession.setPermissionRequestHandler((_w,_p,callback)=>callback(false));session.defaultSession.setPermissionCheckHandler(()=>false);
  win=new BrowserWindow({width:1020,height:780,minWidth:830,minHeight:680,show:false,title:'KP Master · Owner Activation',backgroundColor:'#f2f5f8',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,preload:path.join(__dirname,'preload.cjs')}});
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',event=>event.preventDefault());win.webContents.on('will-attach-webview',event=>event.preventDefault());
  ipcMain.handle('kp-owner:status',event=>{trusted(event);return status();});
  ipcMain.handle('kp-owner:create',async(event,passphrase)=>{
    trusted(event);password(passphrase);
    const selected=await dialog.showSaveDialog(win,{title:'Save encrypted owner private key',defaultPath:path.join(app.getPath('documents'),'KP-Owner.private-key.pem'),filters:[{name:'Encrypted owner key',extensions:['pem']}]});
    if(selected.canceled||!selected.filePath)return null;
    const keys=crypto.generateKeyPairSync('ed25519');
    const encrypted=keys.privateKey.export({format:'pem',type:'pkcs8',cipher:'aes-256-cbc',passphrase});
    await fs.writeFile(selected.filePath,encrypted,{encoding:'utf8',mode:0o600});setKey(keys.privateKey,selected.filePath);return status();
  });
  ipcMain.handle('kp-owner:open',async(event,passphrase)=>{
    trusted(event);password(passphrase);
    const selected=await dialog.showOpenDialog(win,{title:'Open encrypted owner private key',properties:['openFile'],filters:[{name:'Encrypted owner key',extensions:['pem']}]});
    if(selected.canceled||!selected.filePaths.length)return null;
    const file=selected.filePaths[0];if((await fs.stat(file)).size>16384)throw Error('Choose your encrypted owner key file.');
    const pem=await fs.readFile(file,'utf8');if(!pem.includes('-----BEGIN ENCRYPTED PRIVATE KEY-----'))throw Error('Choose an encrypted PKCS8 owner key.');
    let key;try{key=crypto.createPrivateKey({key:pem,format:'pem',passphrase});}catch{throw Error('The password or owner key file is incorrect.');}
    setKey(key,file);return status();
  });
  ipcMain.handle('kp-owner:lock',event=>{trusted(event);privateKey=null;publicPem='';privateFile='';return status();});
  ipcMain.handle('kp-owner:export-public',async event=>{
    trusted(event);requireKey();const selected=await dialog.showSaveDialog(win,{title:'Export public key for the client build',defaultPath:path.join(app.getPath('documents'),'KP-Owner-Public-Key.pem'),filters:[{name:'Public verification key',extensions:['pem']}]});
    if(selected.canceled||!selected.filePath)return false;
    await fs.writeFile(selected.filePath,publicPem,'utf8');return true;
  });
  ipcMain.handle('kp-owner:history',event=>{trusted(event);return history();});
  ipcMain.handle('kp-owner:issue',async(event,request)=>{
    trusted(event);requireKey();if(!request||typeof request!=='object')throw Error('Enter the client details.');
    const issuerKeyId=keyId(publicPem),license=issue(privateKey,request);const claims=JSON.parse(Buffer.from(license.payload,'base64url').toString('utf8'));
    const selected=await dialog.showSaveDialog(win,{title:'Save client activation license',defaultPath:path.join(app.getPath('documents'),cleanName(claims.clientName)+'-'+claims.systemId.slice(-9)+'.kplicense'),filters:[{name:'KP Activation License',extensions:['kplicense']}]});
    if(selected.canceled||!selected.filePath)return null;
    await fs.writeFile(selected.filePath,JSON.stringify(license,null,2),'utf8');
    const list=await history();list.unshift({...claims,ownerKeyId:issuerKeyId,controlRevision:0,status:'activate'});
    await saveHistory(list);
    return {filename:path.basename(selected.filePath),claims};
  });
  ipcMain.handle('kp-owner:set-status',async(event,request)=>{
    trusted(event);requireKey();if(!request||!['activate','deactivate'].includes(request.action))throw Error('Choose Activate or Deactivate.');
    const list=await history(),row=list.find(r=>r.licenseId===request.licenseId);if(!row)throw Error('The issued license was not found.');
    if(row.ownerKeyId!==keyId(publicPem))throw Error('Open the owner key that issued this license before changing its status.');
    if(request.action==='activate'&&row.expiresAt&&Date.parse(row.expiresAt)<Date.now())throw Error('This license has expired. Issue a new license to renew it.');
    const revision=(Number.isSafeInteger(row.controlRevision)?row.controlRevision:0)+1;
    const control=issueControl(privateKey,{licenseId:row.licenseId,systemId:row.systemId,action:request.action,revision});
    const selected=await dialog.showSaveDialog(win,{title:'Save signed '+request.action+' status file',defaultPath:path.join(app.getPath('documents'),cleanName(row.clientName)+'-'+request.action+'-'+revision+'.kpcontrol'),filters:[{name:'KP License Status',extensions:['kpcontrol']}]});
    if(selected.canceled||!selected.filePath)return null;
    await fs.writeFile(selected.filePath,JSON.stringify(control,null,2),'utf8');row.controlRevision=revision;row.status=request.action;row.statusIssuedAt=new Date().toISOString();await saveHistory(list);
    return {filename:path.basename(selected.filePath),action:request.action,licenseId:row.licenseId};
  });
  win.once('ready-to-show',()=>win.show());win.loadFile(ownerPath);
}).catch(error=>{dialog.showErrorBox('Owner activation tool',error.message);app.quit();});
app.on('window-all-closed',()=>{privateKey=null;app.quit();});}
