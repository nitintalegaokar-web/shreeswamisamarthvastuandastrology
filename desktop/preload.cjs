'use strict';
const {contextBridge,ipcRenderer} = require('electron');
contextBridge.exposeInMainWorld('KPLicensing',Object.freeze({status:()=>ipcRenderer.invoke('kp-license:status'),copyId:()=>ipcRenderer.invoke('kp-license:copy-id'),exportId:()=>ipcRenderer.invoke('kp-license:export-id'),activate:()=>ipcRenderer.invoke('kp-license:activate')}));
contextBridge.exposeInMainWorld('KPDesktopFiles', Object.freeze({
  save:(text,filename) => ipcRenderer.invoke('kp-desktop:save-chart',text,filename),
  open:() => ipcRenderer.invoke('kp-desktop:open-chart')
}));
