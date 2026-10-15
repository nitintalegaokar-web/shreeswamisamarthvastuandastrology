'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('KPOwner',Object.freeze({
  copyCode:code=>ipcRenderer.invoke('kp-owner:copy-code',code),
  status:()=>ipcRenderer.invoke('kp-owner:status'),
  create:password=>ipcRenderer.invoke('kp-owner:create',password),
  open:password=>ipcRenderer.invoke('kp-owner:open',password),
  remember:()=>ipcRenderer.invoke('kp-owner:remember'),
  lock:()=>ipcRenderer.invoke('kp-owner:lock'),
  exportPublic:()=>ipcRenderer.invoke('kp-owner:export-public'),
  history:()=>ipcRenderer.invoke('kp-owner:history'),
  removedHistory:()=>ipcRenderer.invoke('kp-owner:removed-history'),
  removeHistory:licenseId=>ipcRenderer.invoke('kp-owner:remove-history',licenseId),
  restoreHistory:licenseId=>ipcRenderer.invoke('kp-owner:restore-history',licenseId),
  help:language=>ipcRenderer.invoke('kp-owner:help',language),
  exportText:request=>ipcRenderer.invoke('kp-owner:export-text',request),
  importRequest:()=>ipcRenderer.invoke('kp-owner:import-request'),
  issue:request=>ipcRenderer.invoke('kp-owner:issue',request),
  setStatus:request=>ipcRenderer.invoke('kp-owner:set-status',request)
}));
