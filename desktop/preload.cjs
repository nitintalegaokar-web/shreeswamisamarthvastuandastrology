'use strict';
const {contextBridge,ipcRenderer} = require('electron');
contextBridge.exposeInMainWorld('KPLicensing',Object.freeze({applyCode:code=>ipcRenderer.invoke('kp-license:apply-code',code),enterKey:()=>ipcRenderer.invoke('kp-license:show-code'),status:()=>ipcRenderer.invoke('kp-license:status'),retry:()=>ipcRenderer.invoke('kp-license:retry'),importControl:()=>ipcRenderer.invoke('kp-license:import-control'),copyId:()=>ipcRenderer.invoke('kp-license:copy-id'),exportId:()=>ipcRenderer.invoke('kp-license:export-id'),activate:()=>ipcRenderer.invoke('kp-license:activate')}));
contextBridge.exposeInMainWorld('KPDesktopFiles', Object.freeze({
  save:(text,filename) => ipcRenderer.invoke('kp-desktop:save-chart',text,filename),
  open:() => ipcRenderer.invoke('kp-desktop:open-chart')
}));
