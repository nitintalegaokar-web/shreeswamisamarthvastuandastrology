/* Chart lord-label sizing, large double-click viewer and manual birth-time nudging. */
(()=>{'use strict';
const LORD_KEY='kpSglStlSblScaleV1',LORD_MIN=.7,LORD_MAX=2,LORD_STEP=.1;
let lordScale=readScale(),lordQueued=false,internalBirthChange=false,baseline=null,dialog=null,zoom=1;
const $=id=>document.getElementById(id);
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
function readScale(){try{const value=Number(localStorage.getItem(LORD_KEY));return Number.isFinite(value)?clamp(value,LORD_MIN,LORD_MAX):1;}catch(_){return 1;}}
function writeScale(value){lordScale=Math.round(clamp(value,LORD_MIN,LORD_MAX)*10)/10;try{localStorage.setItem(LORD_KEY,String(lordScale));}catch(_){}refreshLordControls();queueLords();}
function language(){return window.KPPreferences?.get?.().language==='marathi'?'marathi':'english';}
function colourizeLordLabel(node){
  if(!(node instanceof Element)||node.closest('#printReport,[contenteditable],[data-manual-text]'))return;
  const values=[node.dataset.sgl,node.dataset.stl,node.dataset.sbl];
  if(values.some(value=>!value))return;
  const signature=values.join('|');if(node.dataset.kpLordColours===signature)return;
  const roles=['sgl','stl','sbl'];node.replaceChildren(document.createTextNode('('));
  values.forEach((value,index)=>{const part=document.createElement('span');part.className='kp-lord-role-'+roles[index];part.dataset.lordRole=roles[index];part.textContent=value;node.append(part);if(index<2){const separator=document.createElement('span');separator.className='kp-lord-separator';separator.textContent='–';node.append(separator);}});
  node.append(document.createTextNode(')'));node.dataset.kpLordColours=signature;
  node.setAttribute('aria-label','SGL '+values[0]+', STL '+values[1]+', SBL '+values[2]);
}
function lordSize(node,settings){
  const chart=node.closest('.v38-chart');if(!chart)return null;
  const width=chart.getBoundingClientRect().width||Number.parseFloat(getComputedStyle(chart).width)||480;
  const home=chart.hasAttribute('data-home-chart')||Boolean(chart.closest('#home'));
  const font=clamp(Number(settings.fontSize)||12,8,28)/12;
  const planet=({small:.85,medium:1,large:1.2})[settings.planetSize]||1;
  const responsive=clamp(width/480,.72,1.6),base=home?9.2:7.2;
  return clamp(base*responsive*font*planet*lordScale,5.5,28);
}
function refreshLords(){
  lordQueued=false;const settings=window.KPPreferences?.get?.()||{fontSize:12,planetSize:'medium',fontFamily:'Arial',fontBold:false};
  for(const node of document.querySelectorAll('.v38-chart .v38-lords')){
    if(node.closest('#printReport,[contenteditable],[data-manual-text]'))continue;
    colourizeLordLabel(node);const size=lordSize(node,settings);if(!size)continue;
    node.style.setProperty('font-size',size.toFixed(2)+'px','important');
    node.style.setProperty('font-family',String(settings.fontFamily||'Arial'),'important');
    node.style.setProperty('font-weight',settings.fontBold?'700':'500','important');
  }
  refreshLordControls();
}
function queueLords(){if(lordQueued)return;lordQueued=true;requestAnimationFrame(refreshLords);}
function lordControl(context){
  const box=document.createElement('div');box.className='kp-lord-size-control no-print';box.dataset.lordControl=context;box.setAttribute('role','group');
  const minus=document.createElement('button');minus.type='button';minus.dataset.lordSize='decrease';minus.textContent='−';
  const reset=document.createElement('button');reset.type='button';reset.className='kp-lord-size-reset';reset.dataset.lordSize='reset';reset.innerHTML='<span class="kp-lord-role-sgl">SGL</span><span class="kp-lord-role-stl">STL</span><span class="kp-lord-role-sbl">SBL</span><span class="kp-lord-size-value"></span>';
  const plus=document.createElement('button');plus.type='button';plus.dataset.lordSize='increase';plus.textContent='+';box.append(minus,reset,plus);
  box.addEventListener('click',event=>{const action=event.target.closest('button')?.dataset.lordSize;if(!action)return;event.preventDefault();event.stopPropagation();if(action==='decrease')writeScale(lordScale-LORD_STEP);else if(action==='increase')writeScale(lordScale+LORD_STEP);else writeScale(1);});
  return box;
}
function refreshLordControls(){
  const marathi=language()==='marathi',percent=Math.round(lordScale*100)+'%';
  document.querySelectorAll('.kp-lord-size-control').forEach(control=>{
    const minus=control.querySelector('[data-lord-size="decrease"]'),plus=control.querySelector('[data-lord-size="increase"]'),reset=control.querySelector('[data-lord-size="reset"]');
    minus.disabled=lordScale<=LORD_MIN+.001;plus.disabled=lordScale>=LORD_MAX-.001;
    minus.setAttribute('aria-label',marathi?'SGL, STL, SBL अक्षर आकार कमी करा':'Decrease SGL, STL and SBL size');
    plus.setAttribute('aria-label',marathi?'SGL, STL, SBL अक्षर आकार वाढवा':'Increase SGL, STL and SBL size');
    reset.setAttribute('aria-label',marathi?'SGL, STL, SBL आकार 100 टक्के करा':'Reset SGL, STL and SBL size');
    const value=control.querySelector('.kp-lord-size-value');if(value)value.textContent=percent;
  });
}
function mountLordControls(){
  const homeHeading=document.querySelector('#home .home-chart-panel .home-panel-heading');
  if(homeHeading&&!document.querySelector('#home [data-lord-control="home"]'))homeHeading.append(lordControl('home'));
  const toolbar=document.querySelector('#south9 .kundali-toolbar');
  if(toolbar&&!toolbar.querySelector('[data-lord-control="chart"]'))toolbar.append(lordControl('chart'));
  const fontBox=document.querySelector('#settings-pane-display .font-control-box');
  if(fontBox&&!fontBox.querySelector('.kp-lord-settings-row')){
    const row=document.createElement('div');row.className='kp-lord-settings-row';
    const copy=document.createElement('div');copy.className='kp-lord-settings-copy';copy.innerHTML='<strong>SGL · STL · SBL size</strong><small>Follows chart font size; this control adds a separate adjustment.</small>';
    row.append(copy,lordControl('settings'));fontBox.append(row);
  }
  refreshLordControls();
}

const CHART_SELECTOR=['.v38-chart','.north9-chart','.tc-diagram','.v-chart','.v-north-chart','.sp-chart','[data-home-chart]','[data-chart-enlarge]'].join(',');
function enlargeCandidate(target){
  if(!(target instanceof Element)||target.closest('#kp-enlarge-dialog,#printReport,[contenteditable],button,a'))return null;
  const field=target.closest('input,select,textarea');if(field&&!field.disabled&&!field.readOnly)return null;
  let chart=target.closest(CHART_SELECTOR);
  if(!chart){const possible=target.closest('[id*="chart" i],[class*="chart" i]');if(possible?.querySelector('svg,canvas,.v38-cell'))chart=possible;}
  const table=target.closest('table');const candidate=chart||table;
  if(!candidate||candidate.hidden||!candidate.getClientRects().length)return null;
  return candidate;
}
function sourceTitle(source){
  const caption=source.querySelector?.(':scope > caption')?.textContent?.trim();if(caption)return caption;
  const label=source.getAttribute('aria-label')||source.getAttribute('title');if(label)return label;
  const region=source.closest('article,section,.card,.home-panel');
  const heading=region?.querySelector('h1,h2,h3,.south9-title,.sheet-title');
  return heading?.textContent?.trim()||'Chart / table preview';
}
function removeCloneIds(root,source){
  if(source.id)root.dataset.kpSourceId=source.id;
  if(root.matches('.v38-chart'))root.dataset.reportId='kundali';
  [root,...root.querySelectorAll('[id]')].forEach(node=>node.removeAttribute('id'));
  root.querySelectorAll('label[for]').forEach(label=>label.removeAttribute('for'));
  root.querySelectorAll('button,.no-print,script').forEach(node=>node.remove());
  root.querySelectorAll('input,select,textarea').forEach(control=>{
    const output=document.createElement('span');output.className='kp-enlarge-readonly-value';
    if(control instanceof HTMLSelectElement)output.textContent=control.selectedOptions[0]?.textContent||control.value;
    else if(control.type==='checkbox'||control.type==='radio')output.textContent=control.checked?'✓':'—';
    else output.textContent=control.value||'—';control.replaceWith(output);
  });
  root.querySelectorAll('details').forEach(item=>item.open=true);
}
function copyCanvases(source,clone){
  const sources=[...source.querySelectorAll('canvas')],clones=[...clone.querySelectorAll('canvas')];
  sources.forEach((canvas,index)=>{const target=clones[index];if(!target)return;target.width=canvas.width;target.height=canvas.height;try{target.getContext('2d')?.drawImage(canvas,0,0);}catch(_){}});
}
function setZoom(value){
  zoom=clamp(Math.round(value*10)/10,.5,2.5);const content=dialog?.querySelector('.kp-enlarge-content');if(content)content.style.zoom=String(zoom);
  const output=dialog?.querySelector('.kp-enlarge-zoom-value');if(output)output.textContent=Math.round(zoom*100)+'%';
  const minus=dialog?.querySelector('[data-enlarge-action="out"]'),plus=dialog?.querySelector('[data-enlarge-action="in"]');if(minus)minus.disabled=zoom<=.5;if(plus)plus.disabled=zoom>=2.5;
}
function createDialog(){
  const modal=document.createElement('dialog');modal.id='kp-enlarge-dialog';modal.className='no-print';modal.innerHTML='<div class="kp-enlarge-shell"><header class="kp-enlarge-toolbar"><h2 id="kp-enlarge-title">Chart / table preview</h2><button type="button" data-enlarge-action="out" aria-label="Zoom out">−</button><output class="kp-enlarge-zoom-value">100%</output><button type="button" data-enlarge-action="in" aria-label="Zoom in">+</button><button type="button" data-enlarge-action="reset">100%</button><button type="button" class="kp-enlarge-close" data-enlarge-action="close">Close</button></header><div class="kp-enlarge-viewport"><div class="kp-enlarge-stage"><div class="kp-enlarge-content"></div></div></div></div>';
  modal.setAttribute('aria-labelledby','kp-enlarge-title');modal.addEventListener('click',event=>{
    const action=event.target.closest('[data-enlarge-action]')?.dataset.enlargeAction;
    if(action==='out')setZoom(zoom-.1);else if(action==='in')setZoom(zoom+.1);else if(action==='reset')setZoom(1);else if(action==='close')modal.close();
    else if(event.target===modal)modal.close();
  });
  modal.addEventListener('close',()=>{modal.querySelector('.kp-enlarge-content').replaceChildren();document.body.classList.remove('kp-enlarge-open');});document.body.append(modal);return modal;
}
function preserveTransitPresentation(source,clone){
  if(!source.matches('.tc-diagram')||!source.closest('#transit-chart'))return false;
  const properties=['fill','fill-opacity','stroke','stroke-width','stroke-opacity','stroke-dasharray','opacity','color','font-family','font-size','font-weight','font-style','text-anchor','dominant-baseline','paint-order','transform','transform-origin','transform-box','background-color'];
  const originals=[...source.querySelectorAll('svg,svg *')],copies=[...clone.querySelectorAll('svg,svg *')];
  originals.forEach((node,index)=>{const copy=copies[index];if(!copy)return;const style=getComputedStyle(node);for(const property of properties){const value=style.getPropertyValue(property);if(value)copy.style.setProperty(property,value,'important');}});
  const style=getComputedStyle(source),rect=source.getBoundingClientRect();clone.dataset.kpPreserveTransit='true';clone.style.setProperty('--kp-transit-preview-aspect',String(rect.width/Math.max(1,rect.height)));clone.style.backgroundColor=style.backgroundColor;clone.style.border=style.border;clone.setAttribute('data-no-localize','');return true;
}
function openEnlarged(source){
  if(!(source instanceof Element))return false;dialog=dialog||createDialog();const clone=source.cloneNode(true),preserved=preserveTransitPresentation(source,clone);removeCloneIds(clone,source);copyCanvases(source,clone);
  const content=dialog.querySelector('.kp-enlarge-content');content.replaceChildren(clone);dialog.querySelector('#kp-enlarge-title').textContent=sourceTitle(source);
  window.KPHoverDetails?.hide?.();document.body.classList.add('kp-enlarge-open');if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');
  const rect=source.getBoundingClientRect(),available=Math.max(320,Math.min(window.innerWidth*.82,900));setZoom(source.matches('table')||preserved||clone.querySelector('.kp-paired-north')?1:clamp(available/Math.max(rect.width,1),1,1.5));dialog.querySelector('.kp-enlarge-close')?.focus({preventScroll:true});return true;
}

function readBirth(){
  const date=$('dob')?.value||'',raw=$('birthTime')?.value||'';if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return null;
  const match=/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(raw);if(!match)return null;
  const hour=Number(match[1]),minute=Number(match[2]),second=Number(match[3]||0);if(hour>23||minute>59||second>59)return null;
  const moment=new Date(date+'T'+String(hour).padStart(2,'0')+':'+String(minute).padStart(2,'0')+':'+String(second).padStart(2,'0')+'Z');return Number.isNaN(moment.getTime())?null:{date,time:String(hour).padStart(2,'0')+':'+String(minute).padStart(2,'0')+':'+String(second).padStart(2,'0'),ms:moment.getTime()};
}
function birthSignature(value=readBirth()){return value?value.date+'|'+value.time:'';}
function setBirth(moment,status){
  const date=$('dob'),time=$('birthTime');if(!date||!time)return false;const iso=new Date(moment).toISOString();internalBirthChange=true;
  try{date.value=iso.slice(0,10);time.value=iso.slice(11,19);date.dispatchEvent(new Event('input',{bubbles:true}));time.dispatchEvent(new Event('input',{bubbles:true}));time.dispatchEvent(new Event('change',{bubbles:true}));}
  finally{internalBirthChange=false;}
  if(typeof window.calculateAll==='function')requestAnimationFrame(()=>window.calculateAll());
  window.dispatchEvent(new CustomEvent('birth-time-rectified',{detail:{date:date.value,time:time.value,baseline:baseline?birthSignature(baseline):'',status}}));updateRectifier(status);return true;
}
function adjustBirth(seconds){const current=readBirth();if(!current){updateRectifier('Enter a valid birth date and time first.');return;}if(!baseline)baseline={...current};setBirth(current.ms+seconds*1000,(seconds>0?'+':'−')+Math.abs(seconds)+' seconds applied.');}
function resetBirth(){if(!baseline)return;const target=baseline.ms;setBirth(target,'Restored the time captured before rectification.');baseline={...readBirth()};}
function formatBirthDate(date){if(!date)return '—';try{return window.KPPreferences?.isConfigured?.()?window.KPPreferences.formatDate(date):date.split('-').reverse().join('/');}catch(_){return date;}}
function updateRectifier(status){
  const card=$('kp-birth-rectifier');if(!card)return;const current=readBirth(),marathi=language()==='marathi';
  card.querySelector('.kp-rectify-label').textContent=marathi?'सध्याची वेळ':'Current';card.querySelector('.kp-rectify-time').textContent=current?.time||'—';card.querySelector('.kp-rectify-date').textContent=formatBirthDate(current?.date);
  const changed=Boolean(current&&baseline&&birthSignature(current)!==birthSignature(baseline));const reset=card.querySelector('.kp-rectify-reset');reset.disabled=!changed;reset.textContent=marathi?'मूळ वेळ':'Reset';
  card.querySelector('.kp-rectify-title-text').textContent=marathi?'जन्मवेळ शुद्धीकरण':'Rectify birth time';
  card.querySelector('.kp-rectify-help').textContent=marathi?'जन्मवेळ लहान टप्प्यांनी बदला. प्रत्येक बदलानंतर लग्न, भाव आणि त्यांच्या उपस्वामींची पुन्हा गणना होते.':'Adjust the stored birth time in small steps. Ascendant, cusps and their sub lords recalculate after every change.';
  const message=card.querySelector('.kp-rectify-status');if(status)message.textContent=status;else if(changed){const seconds=Math.round((current.ms-baseline.ms)/1000),sign=seconds>=0?'+':'−';message.textContent=(marathi?'मूळ वेळेपासून ':'From starting time ')+sign+Math.abs(seconds)+' sec';}else message.textContent=marathi?'बदल करण्यापूर्वीची वेळ Reset साठी जतन केली जाते.':'The starting time is kept for Reset.';
}
function createRectifier(){
  const card=document.createElement('section');card.id='kp-birth-rectifier';card.className='kp-birth-rectifier no-print';card.setAttribute('aria-label','Birth time rectification controls');
  card.innerHTML='<div class="kp-rectify-copy"><h3 class="kp-rectify-title"><span class="kp-rectify-clock" aria-hidden="true">◷</span><span class="kp-rectify-title-text">Rectify birth time</span></h3><p class="kp-rectify-help"></p><p class="kp-rectify-current"><span class="kp-rectify-label">Current</span><output class="kp-rectify-time">—</output><time class="kp-rectify-date">—</time></p></div><div class="kp-rectify-actions" aria-label="Birth time steps"></div><div class="kp-rectify-footer"><button type="button" class="kp-rectify-reset">Reset</button><span class="kp-rectify-status" role="status" aria-live="polite"></span></div>';
  const actions=card.querySelector('.kp-rectify-actions');for(const [seconds,label] of [[15,'15 sec'],[60,'1 min'],[900,'15 min'],[3600,'1 hr']]){const minus=document.createElement('button');minus.type='button';minus.textContent='−';minus.dataset.rectifySeconds=String(-seconds);minus.setAttribute('aria-label','Subtract '+label);const text=document.createElement('span');text.textContent=label;const plus=document.createElement('button');plus.type='button';plus.textContent='+';plus.dataset.rectifySeconds=String(seconds);plus.setAttribute('aria-label','Add '+label);actions.append(minus,text,plus);}
  card.addEventListener('click',event=>{const step=event.target.closest('[data-rectify-seconds]');if(step){event.preventDefault();adjustBirth(Number(step.dataset.rectifySeconds));}else if(event.target.closest('.kp-rectify-reset')){event.preventDefault();resetBirth();}});return card;
}
function mountRectifier(){const mount=$('home-kundali');if(!mount||$('kp-birth-rectifier'))return;mount.after(createRectifier());baseline=readBirth();updateRectifier();}
function init(){
  mountLordControls();mountRectifier();queueLords();
  const observer=new MutationObserver(()=>{mountLordControls();mountRectifier();queueLords();});
  ['home-kundali','kundali','kundali-north','na-native-chart'].forEach(id=>{const node=$(id);if(node)observer.observe(node,{childList:true,subtree:true});});
  document.addEventListener('dblclick',event=>{const candidate=enlargeCandidate(event.target);if(!candidate)return;event.preventDefault();event.stopPropagation();openEnlarged(candidate);},true);
  document.addEventListener('input',event=>{if((event.target?.id==='dob'||event.target?.id==='birthTime')&&!internalBirthChange){baseline=readBirth();updateRectifier();}if(event.target?.matches?.('#setting-fontSize,#setting-planetSize,#setting-fontFamily,#setting-fontBold'))queueLords();},true);
  window.addEventListener('resize',queueLords);window.addEventListener('kp-preferences-changed',()=>{queueLords();updateRectifier();});window.addEventListener('chart-saved',event=>{if(event.detail?.action==='loaded')baseline=readBirth();queueLords();updateRectifier();});
  for(const name of ['kundali-style-changed','birth-time-rectified'])window.addEventListener(name,queueLords);
}
window.KPLordLabelSize=Object.freeze({get:()=>lordScale,set:writeScale,refresh:refreshLords});
window.KPChartEnlarger=Object.freeze({open:openEnlarged,close:()=>dialog?.close(),getZoom:()=>zoom});
window.KPBirthTimeRectifier=Object.freeze({adjust:adjustBirth,reset:resetBirth,getBaseline:()=>baseline?{date:baseline.date,time:baseline.time}:null,refresh:updateRectifier});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
