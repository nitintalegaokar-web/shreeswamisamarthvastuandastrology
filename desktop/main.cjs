'use strict';
const {app, BrowserWindow, Menu, session, shell, dialog, ipcMain} = require('electron');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {isExternal, isPreview, safeFilename} = require('./policy.cjs');
const {createGate}=require('./licensing/gate.cjs');
const indexPath = path.join(__dirname, 'app', 'index.html');
const indexURL = pathToFileURL(indexPath).href;
let mainWindow;
let licenseGate;
function openExternal(url) {
  if (isExternal(url)) shell.openExternal(url).catch(() => {});
}
function secureWindow(win) {
  win.webContents.setWindowOpenHandler(({url}) => {
    if (licenseGate?.isActive() && isPreview(url)) return {action:'allow', overrideBrowserWindowOptions:{
      width:1120, height:850, autoHideMenuBar:true,
      webPreferences:{nodeIntegration:false, contextIsolation:true, sandbox:true, webSecurity:true}
    }};
    openExternal(url);
    return {action:'deny'};
  });
  win.webContents.on('will-navigate', (event, url) => {
    if (licenseGate?.isActive() && (url.split('#')[0] === indexURL || isPreview(url))) return;
    event.preventDefault();
    openExternal(url);
  });
  win.webContents.on('will-attach-webview', event => event.preventDefault());
  win.webContents.on('did-create-window', secureWindow);
}
if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => {
    if (mainWindow) {if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus();}
  });
  app.whenReady().then(async () => {
    const trusted = event => licenseGate?.isActive() && event.senderFrame?.url.split('#')[0] === indexURL && event.sender === mainWindow?.webContents;
    ipcMain.handle('kp-desktop:save-chart', async (event, text, filename) => {
      if (!trusted(event)) throw Error('Untrusted chart request.');
      if (typeof text !== 'string' || Buffer.byteLength(text, 'utf8') > 12*1024*1024) throw Error('Chart is too large.');
      JSON.parse(text);
      const selected = await dialog.showSaveDialog(mainWindow, {
        title:'Save kundali', defaultPath:path.join(app.getPath('documents'), safeFilename(filename)),
        filters:[{name:'KP Kundali', extensions:['lkp']}]
      });
      if (selected.canceled || !selected.filePath) return null;
      await fs.writeFile(selected.filePath, text, 'utf8');
      return path.basename(selected.filePath);
    });
    ipcMain.handle('kp-desktop:open-chart', async event => {
      if (!trusted(event)) throw Error('Untrusted chart request.');
      const selected = await dialog.showOpenDialog(mainWindow, {
        title:'Open kundali', properties:['openFile'], filters:[{name:'KP Kundali', extensions:['lkp']}]
      });
      if (selected.canceled || !selected.filePaths.length) return null;
      const chosen = selected.filePaths[0];
      if ((await fs.stat(chosen)).size > 12*1024*1024) throw Error('Choose a chart smaller than 12 MB.');
      const text = await fs.readFile(chosen, 'utf8');
      JSON.parse(text);
      return {name:path.basename(chosen), text};
    });
    ipcMain.handle('kp-desktop:whatsapp',async(event,text)=>{if(!trusted(event))throw Error('Untrusted share request.');const message=String(text||'').slice(0,12000),query=encodeURIComponent(message);try{await shell.openExternal('whatsapp://send?text='+query);}catch{await shell.openExternal('https://wa.me/?text='+query);}return true;});
    // Calculations, fonts, tables, and reports load from the packaged application.
    // Optional online accounts are opened in the user's normal browser.
    session.defaultSession.webRequest.onBeforeRequest({urls:['http://*/*','https://*/*','ws://*/*','wss://*/*']}, (_details, callback) => callback({cancel:true}));
    session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
    session.defaultSession.on('will-download', (_event, item) => {
      item.setSaveDialogOptions({
        title:'Save chart or report',
        defaultPath:path.join(app.getPath('documents'), safeFilename(item.getFilename()))
      });
    });
    // Keep the existing compact, language-aware application controls.
    Menu.setApplicationMenu(null);
    mainWindow = new BrowserWindow({
      width:900, height:670, minWidth:700, minHeight:580,
      title:'KP MASTER', backgroundColor:'#ffffe8', show:false,
      webPreferences:{nodeIntegration:false, contextIsolation:true, sandbox:true, webSecurity:true, preload:path.join(__dirname,'preload.cjs')}
    });
    secureWindow(mainWindow);
    mainWindow.once('ready-to-show', () => {mainWindow.maximize();mainWindow.show();});
    licenseGate=await createGate(app,mainWindow,indexPath);
    if(licenseGate.isActive()){mainWindow.setMinimumSize(950,650);mainWindow.maximize();}
  }).catch(error=>{
    dialog.showErrorBox('KP MASTER activation',error.message);app.quit();
  });
  app.on('window-all-closed', () => app.quit());
}
