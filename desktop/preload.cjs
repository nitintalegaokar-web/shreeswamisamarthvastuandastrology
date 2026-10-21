'use strict';
const {contextBridge,ipcRenderer} = require('electron');
contextBridge.exposeInMainWorld('KPLicensing',Object.freeze({continueDemo:()=>ipcRenderer.invoke('kp-demo:continue'),applyCode:code=>ipcRenderer.invoke('kp-license:apply-code',code),enterKey:()=>ipcRenderer.invoke('kp-license:show-code'),features:()=>ipcRenderer.invoke('kp-license:features'),upgrade:()=>ipcRenderer.invoke('kp-license:upgrade'),status:()=>ipcRenderer.invoke('kp-license:status'),retry:()=>ipcRenderer.invoke('kp-license:retry'),importControl:()=>ipcRenderer.invoke('kp-license:import-control'),copyId:()=>ipcRenderer.invoke('kp-license:copy-id'),exportId:()=>ipcRenderer.invoke('kp-license:export-id'),activate:()=>ipcRenderer.invoke('kp-license:activate')}));
contextBridge.exposeInMainWorld('KPDesktopFiles', Object.freeze({
  save:(text,filename) => ipcRenderer.invoke('kp-desktop:save-chart',text,filename),
  open:() => ipcRenderer.invoke('kp-desktop:open-chart')
}));

contextBridge.exposeInMainWorld('KPDemoNative',Object.freeze({status:()=>ipcRenderer.sendSync('kp-demo:request',{action:'status'}),use:(kind,signature,consume=true)=>ipcRenderer.sendSync('kp-demo:request',{action:'use',kind,signature,consume})}));
