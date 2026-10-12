'use strict';
const {contextBridge,ipcRenderer} = require('electron');
contextBridge.exposeInMainWorld('KPDesktopFiles', Object.freeze({
  save:(text,filename) => ipcRenderer.invoke('kp-desktop:save-chart',text,filename),
  open:() => ipcRenderer.invoke('kp-desktop:open-chart')
}));
