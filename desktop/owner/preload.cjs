'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('KPOwner',Object.freeze({
  status:()=>ipcRenderer.invoke('kp-owner:status'),
  create:password=>ipcRenderer.invoke('kp-owner:create',password),
  open:password=>ipcRenderer.invoke('kp-owner:open',password),
  lock:()=>ipcRenderer.invoke('kp-owner:lock'),
  exportPublic:()=>ipcRenderer.invoke('kp-owner:export-public'),
  history:()=>ipcRenderer.invoke('kp-owner:history'),
  issue:request=>ipcRenderer.invoke('kp-owner:issue',request)
}));
