/* Automatic native inputs, with explicitly saved manual administrator overrides. */
(()=>{'use strict';const $=id=>document.getElementById(id),KEY='kpSavedManualCalculationsV1';
const MODES={'p6-ephemeris-source':['planet','automatic'],'st-ephemeris-source':['stcalc','automatic'],'r5-house-source':['raphael5','automatic'],'kp-ayanamsha-source':['ayan','annual']};
const NATIVE=['dob','birthTime','lat','lon','birth-utc-offset','birth-dst-minutes','stdLon','chart-kind','instant-prashna'];let saved=null;
const signature=()=>JSON.stringify(NATIVE.map(id=>$(id)?.value||'')),copy=x=>x?JSON.parse(JSON.stringify(x)):null;
function eligible(id){const n=$(id);return n&&!n.readOnly&&!n.disabled&&(Object.hasOwn(MODES,id)||Object.values(MODES).some(([section])=>n.closest('#'+section)));}
function validate(record){if(!record)return null;if(record.version!==1||typeof record.signature!=='string'||record.signature.length>2000||!record.fields||Array.isArray(record.fields)||typeof record.fields!=='object'||Object.keys(record.fields).length>1000)throw Error('Saved manual calculations are invalid.');
 const fields={};for(const [id,field] of Object.entries(record.fields)){if(!eligible(id)||!field||typeof field.value!=='string'||field.value.length>10000||Object.hasOwn(MODES,id)&&field.value!=='manual')throw Error('Saved manual calculations are invalid.');fields[id]={value:field.value};if(typeof field.checked==='boolean')fields[id].checked=field.checked;if(['0','1'].includes(field.auto))fields[id].auto=field.auto;}
 return {version:1,signature:record.signature,fields};}
function manual(){return Object.keys(MODES).some(id=>$(id)?.value==='manual');}
function capture(){if(!manual())throw Error('Select a manual calculation source before saving.');const fields={};for(const [id,[section]] of Object.entries(MODES)){if($(id)?.value!=='manual')continue;fields[id]={value:'manual'};for(const n of $(section).querySelectorAll('input[id],select[id],textarea[id]')){if(!eligible(n.id)||Object.hasOwn(MODES,n.id))continue;fields[n.id]={value:n.value};if(['checkbox','radio'].includes(n.type))fields[n.id].checked=n.checked;if(n.dataset.auto!==undefined)fields[n.id].auto=n.dataset.auto;}}
 return validate({version:1,signature:signature(),fields});}
function persist(){
 // The saved .lkp file is authoritative. Hosted workers have no persistent
 // browser origin; an unavailable optional local cache must not reject imports.
 if(window.KPProtectedWorker)return;
 try{if(saved)localStorage.setItem(KEY,JSON.stringify(saved));else localStorage.removeItem(KEY);}catch(_){}
}
function prepare(){const locked=!window.KPAdminCalculations?.isUnlocked();if(!locked)return;
 const current=saved?.signature===signature()?saved:null;
 for(const [id,[,value]] of Object.entries(MODES))if($(id))$(id).value=current?.fields[id]?.value||value;
 if(current)for(const [id,field] of Object.entries(current.fields)){const n=$(id);if(!eligible(id))continue;n.value=field.value;if(field.checked!==undefined)n.checked=field.checked;if(field.auto!==undefined)n.dataset.auto=field.auto;}
 if(!current||!current.fields['p6-ephemeris-source'])for(const id of ['p6_row_date_1','p6_row_date_2','p6_birth_pos_date'])if($(id))$(id).dataset.auto='1';
}
function init(){try{saved=validate(JSON.parse(localStorage.getItem(KEY)||'null'));}catch(_){saved=null;}
 const get=window.getChartData;window.getChartData=function(...args){const data=get.apply(this,args);if(saved?.signature===signature())data.manualCalculations=copy(saved);return data;};
 const restore=window.restoreChartData;window.restoreChartData=function(data,...args){const next=validate(data?.manualCalculations),previous=saved;saved=next;try{const result=restore.call(this,data,...args);persist();return result;}catch(error){saved=previous;throw error;}};
 const calculate=window.calculateAll;window.calculateAll=function(...args){prepare();return calculate.apply(this,args);};prepare();window.calculateAll();}
window.KPAutomaticCalculations=Object.freeze({prepare,hasManual:manual,capture,getSaved:()=>copy(saved),setSaved:record=>{saved=validate(record);},persist});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
