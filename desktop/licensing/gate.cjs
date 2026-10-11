'use strict';
const {ipcMain,dialog,clipboard,BrowserWindow}=require('electron');
const fs=require('node:fs/promises');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {getSystemId}=require('./system-id.cjs');
const {verify,keyId}=require('./core.cjs');
async function createGate(app,win,indexPath){
  const activationPath=path.join(__dirname,'activation.html');
  const activationURL=pathToFileURL(activationPath).href,indexURL=pathToFileURL(indexPath).href;
  const licensePath=path.join(app.getPath('userData'),'system-license.json');
  let id='',key='',configurationError='',claims=null,message='Activation is required.';
  try{id=await getSystemId();key=await fs.readFile(path.join(__dirname,'..','app','owner-public-key.pem'),'utf8');keyId(key);}
  catch(error){configurationError=error.message;message=configurationError;}
  const trusted=event=>event.sender===win.webContents&&event.senderFrame?.url.split('#')[0]===activationURL;
  function check(event){if(!trusted(event))throw Error('Untrusted activation request.');}
  async function refresh(){
    if(configurationError){claims=null;return;}
    let nextClaims=null,nextMessage='';
    try{if((await fs.stat(licensePath)).size>16384)throw Error('The license file is too large.');nextClaims=verify(await fs.readFile(licensePath,'utf8'),key,id);nextMessage='Activated';}
    catch(error){nextMessage=error.code==='ENOENT'?'Activation is required.':error.message;}
    claims=nextClaims;message=nextMessage;
  }
  ipcMain.handle('kp-license:status',event=>{check(event);return {systemId:id,active:Boolean(claims),message,configured:!configurationError};});
  ipcMain.handle('kp-license:copy-id',event=>{check(event);if(!id)throw Error(message);clipboard.writeText(id);return true;});
  ipcMain.handle('kp-license:export-id',async event=>{
    check(event);if(!id)throw Error(message);
    const selected=await dialog.showSaveDialog(win,{title:'Save client System ID',defaultPath:path.join(app.getPath('documents'),'KP-System-ID.txt'),filters:[{name:'System ID',extensions:['txt']}]});
    if(selected.canceled||!selected.filePath)return false;
    await fs.writeFile(selected.filePath,'KP Master · Client System ID\n'+id+'\n','utf8');return true;
  });
  ipcMain.handle('kp-license:activate',async event=>{
    check(event);if(configurationError)throw Error(configurationError);
    const selected=await dialog.showOpenDialog(win,{title:'Import owner activation license',properties:['openFile'],filters:[{name:'KP Activation License',extensions:['kplicense']}]});
    if(selected.canceled||!selected.filePaths.length)return false;
    const file=selected.filePaths[0];if((await fs.stat(file)).size>16384)throw Error('The license file is too large.');
    const text=await fs.readFile(file,'utf8');verify(text,key,id);
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
