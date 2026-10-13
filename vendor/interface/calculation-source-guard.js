/* Keep legacy chart imports on automatic sources unless manual work was explicitly saved. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const DEFAULTS={
  'p6-ephemeris-source':'automatic',
  'st-ephemeris-source':'automatic',
  'r5-house-source':'automatic',
  'kp-ayanamsha-source':'annual'
};
const NATIVE=['dob','birthTime','lat','lon','birth-utc-offset','birth-dst-minutes','stdLon','chart-kind','instant-prashna'];
const tr=text=>window.KPLanguage?.translate(text)||text;
let wrapped=false,resetting=false;

function language(){return window.KPPreferences?.get?.().language||'english';}
function local(english,marathi){return language()==='marathi'?marathi:tr(english);}
function isManual(){return Object.keys(DEFAULTS).some(id=>$(id)?.value==='manual');}
function signature(){return JSON.stringify(NATIVE.map(id=>$(id)?.value||''));}
function hasSavedManual(){const saved=window.KPAutomaticCalculations?.getSaved?.();return Boolean(saved&&saved.signature===signature());}
function setDefaults(){
  for(const [id,value] of Object.entries(DEFAULTS))if($(id))$(id).value=value;
  for(const id of ['p6_row_date_1','p6_row_date_2','p6_birth_pos_date'])if($(id))$(id).dataset.auto='1';
}
function recalculate(){
  window.KPWorksheetEphemeris?.prepare?.();
  window.calculateAll?.();
}
function useAutomatic({announce=true}={}){
  if(resetting)return false;
  resetting=true;
  try{
    window.KPAutomaticCalculations?.setSaved?.(null);
    window.KPAutomaticCalculations?.persist?.();
    setDefaults();
    recalculate();
    if(announce&&$('admin-save-status'))$('admin-save-status').textContent=local('Automatic calculations restored. Saved manual overrides were cleared.','स्वयंचलित गणना पुनर्स्थापित केली. जतन केलेले मॅन्युअल बदल काढले.');
    update();
    return true;
  }finally{resetting=false;}
}
function sourceText(){
  const stManual=$('st-ephemeris-source')?.value==='manual',manual=isManual()||hasSavedManual();
  if(language()==='marathi')return stManual?'मॅन्युअल 10/6 स्रोत सुरू आहे':manual?'मॅन्युअल गणना ओव्हरराइड सुरू आहे':'स्वयंचलित एफेमेरिस · अचूक सांपातिक गती';
  return stManual?'Manual 10/6 source is active':manual?'A manual calculation override is active':'Automatic ephemeris · exact sidereal rotation';
}
function subtotalText(){
  const subtotal=$('stGrandTotal')?.value||'',adjustment=$('st24Adjustment')?.value||'',final=$('birthPlaceSiderealTime')?.value||'';
  if(!subtotal||!final)return '';
  if(language()==='marathi')return `उपबेरीज ${subtotal} ही ${adjustment||'24:00:00'} समायोजनापूर्वीची आहे. अंतिम सांपातिक वेळ: ${final}.`;
  return `Subtotal ${subtotal} is before the displayed ${adjustment||'24:00:00'} adjustment. Final sidereal time: ${final}.`;
}
function installControls(){
  const toolbar=document.querySelector('#admin-calculation-controls .admin-worksheet-tabs');
  if(!toolbar)return false;
  if(!$('admin-calculation-source-state')){
    const state=document.createElement('span');state.id='admin-calculation-source-state';state.setAttribute('role','status');
    const button=document.createElement('button');button.id='admin-use-automatic';button.type='button';button.textContent=local('Use automatic calculations','स्वयंचलित गणना वापरा');button.addEventListener('click',()=>useAutomatic());
    const lock=$('admin-pin-lock');toolbar.insertBefore(state,lock||null);toolbar.insertBefore(button,lock||null);
  }
  const sheet=$('stcalc');
  if(sheet&&!$('st-subtotal-explanation')){
    const note=document.createElement('p');note.id='st-subtotal-explanation';note.className='st-subtotal-explanation';note.setAttribute('role','note');sheet.append(note);
  }
  return true;
}
function update(){
  if(!installControls())return;
  const manual=isManual()||hasSavedManual(),state=$('admin-calculation-source-state'),button=$('admin-use-automatic'),note=$('st-subtotal-explanation');
  if(state){state.dataset.mode=manual?'manual':'automatic';state.textContent=sourceText();}
  if(button){button.hidden=!manual;button.textContent=local('Use automatic calculations','स्वयंचलित गणना वापरा');}
  if(note)note.textContent=subtotalText();
}
function wrapRestore(){
  if(wrapped||typeof window.restoreChartData!=='function'||!window.KPAutomaticCalculations)return;
  wrapped=true;
  const restore=window.restoreChartData;
  window.restoreChartData=function(data,...args){
    const result=restore.call(this,data,...args);
    // Explicit Save manual entries creates the only authoritative manual record.
    // Older files without that record must not leave ADM in a stale manual mode.
    if(!window.KPAutomaticCalculations.getSaved())useAutomatic({announce:false});
    update();
    return result;
  };
}
function init(){
  wrapRestore();
  if(!installControls()){
    const observer=new MutationObserver(()=>{if(installControls()){observer.disconnect();update();}});
    observer.observe(document.body,{childList:true,subtree:true});
  }
  update();
  document.addEventListener('input',event=>{if(event.target?.id in DEFAULTS||['stGrandTotal','st24Adjustment','birthPlaceSiderealTime'].includes(event.target?.id))queueMicrotask(update);},true);
  document.addEventListener('change',event=>{if(event.target?.id in DEFAULTS)queueMicrotask(update);},true);
  document.addEventListener('click',event=>{if(event.target.closest?.('[data-admin-worksheet],#admin-pin-submit,#admin-pin-lock'))setTimeout(update,0);},true);
  window.addEventListener('chart-saved',()=>setTimeout(update,0));
  window.addEventListener('kp-preferences-changed',()=>setTimeout(update,0));
}
window.KPCalculationSourceGuard=Object.freeze({useAutomatic,update});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else setTimeout(init,0);
})();
