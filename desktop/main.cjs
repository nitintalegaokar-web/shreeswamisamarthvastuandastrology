const { app, BrowserWindow, Menu, shell, session, dialog } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const pagePath = path.join(__dirname, 'app', 'Remedy.html');
const pageUrl = pathToFileURL(pagePath).href;
let window;
// A stable user-data path retains the library across application updates.
app.setPath('userData', path.join(app.getPath('appData'), 'SwamiSamarthRemedies'));
const isAllowedExternal = value => {
  try { const url = new URL(value); return url.protocol === 'https:' && url.hostname === 'wa.me'; }
  catch { return false; }
};
if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => {
    if (window) { if (window.isMinimized()) window.restore(); window.show(); window.focus(); }
  });
  app.whenReady().then(() => {
    session.defaultSession.setPermissionRequestHandler((_contents, permission, callback) => {
      callback(permission === 'clipboard-sanitized-write');
    });
    window = new BrowserWindow({
      width: 1380, height: 960, minWidth: 760, minHeight: 600,
      title: 'KP Master', backgroundColor: '#f5f3ee',
      icon: path.join(__dirname, 'icon.ico'), show: false,
      webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true, webSecurity: true }
    });
    window.webContents.setWindowOpenHandler(({ url }) => {
      if (isAllowedExternal(url)) shell.openExternal(url).catch(() => {});
      return { action: 'deny' };
    });
    window.webContents.on('will-navigate', (event, url) => {
      if (url !== pageUrl) event.preventDefault();
    });
    window.webContents.on('will-attach-webview', event => event.preventDefault());
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      { label: 'File', submenu: [
        { label: 'Backup guidance', click: () => dialog.showMessageBox(window, {
          type: 'info', title: 'Keep your data safe',
          message: 'Export your remedies, bookings, CRM, accounts, documents and settings regularly.',
          detail: 'Use remedy Export (JSON), booking Export booking backup, CRM Backup CRM, accounts Backup accounts, Quotations & Invoices Backup documents and Settings Export settings. Each has its own import option. Browser data is separate: export it from the browser before importing here. Moving or uninstalling software is not a substitute for backups.'
        }) }, { type: 'separator' }, { role: 'quit' }
      ] },
      { label: 'Edit', submenu: [{ role: 'undo' }, { role: 'redo' }, { type: 'separator' }, { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
      { label: 'View', submenu: [{ role: 'reload' }, { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }, { role: 'togglefullscreen' }] },
      { label: 'Help', submenu: [{ label: 'About', click: () => dialog.showMessageBox(window, {
          type: 'info', title: 'KP Master',
          message: 'Shree Swami Samarth Vastu & Astrology Consultancy',
          detail: `Version ${app.getVersion()}\n209 bundled remedies · 49 subjects\nCRM · Collections & Expenses · Reports · Invoices\nMatrugaya bookings · Settings · A5 printing\nContact: 8412098690\nWorks offline. WhatsApp sharing requires an Internet connection.`
      }) }] }
    ]));
    window.once('ready-to-show', () => window.show());
    window.loadFile(pagePath);
  });
  app.on('window-all-closed', () => app.quit());
}
