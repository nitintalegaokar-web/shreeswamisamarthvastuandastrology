/* Settings and display-only outer planets.
 * Calculation math lives in vendor/ephemeris; this file only stores choices,
 * presents controls and renders optional Uranus/Neptune/Pluto values.
 */
(()=>{'use strict';
const KEY='kpCalculationSourcesV1',IDS=['Ur','Ne','Pl'];
const DEFAULTS=Object.freeze({ayanamshaSource:'uploaded-kp',outerUranus:false,outerNeptune:false,outerPluto:false});
const OUTER=Object.freeze({
 Ur:{body:'Uranus',name:'Uranus',mr:'युरेनस',short:'U',setting:'outerUranus',colour:'#176b87'},
 Ne:{body:'Neptune',name:'Neptune',mr:'नेपच्यून',short:'N',setting:'outerNeptune',colour:'#3658a7'},
 Pl:{body:'Pluto',name:'Pluto',mr:'प्लूटो',short:'P',setting:'outerPluto',colour:'#78428f'}
});
const SIGNS={english:['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'],marathi:['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तुळ','वृश्चिक','धनु','मकर','कुंभ','मीन']};
const $=id=>document.getElementById(id),copy=value=>JSON.parse(JSON.stringify(value)),norm=value=>((Number(value)%360)+360)%360;
let state=load(),queued=false,restoring=false;
function normalize(source){
 const next={...DEFAULTS};if(!source||typeof source!=='object'||Array.isArray(source))return next;
 if(['uploaded-kp','swiss-kp'].includes(source.ayanamshaSource))next.ayanamshaSource=source.ayanamshaSource;
 for(const key of ['outerUranus','outerNeptune','outerPluto'])if(typeof source[key]==='boolean')next[key]=source[key];
 return next;
}
function load(){try{return normalize(JSON.parse(localStorage.getItem(KEY)||'null'));}catch(_){return {...DEFAULTS};}}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch(_){/* Settings still apply for this session. */}}
const isSwiss=()=>state.ayanamshaSource==='swiss-kp',selected=()=>IDS.filter(id=>state[OUTER[id].setting]);
function dateValue(value){return window.KPEphemeris.dateValue(value);}
function dms(value){let seconds=Math.round(norm(value)*3600)%1296000;return Math.floor(seconds/3600)+'° '+String(Math.floor(seconds%3600/60)).padStart(2,'0')+'′ '+String(seconds%60).padStart(2,'0')+'″';}
function outerPositions(value){
 const date=dateValue(value),ayan=window.KPEphemeris.ayanamsha(date),result={};
 for(const id of selected()){
  const item=OUTER[id],vector=Astronomy.GeoVector(item.body,date,true),tropical=norm(Astronomy.Ecliptic(vector).elon),longitude=norm(tropical-ayan);
  result[id]={id,name:item.name,tropical,longitude,ayanamsha:ayan,date:date.toISOString(),displayOnly:true};
 }
 return result;
}
function nativeDate(){try{return window.KPHorary?.nativeMoment()?.date||null;}catch(_){return null;}}
function renderPanel(anchor,id,date,title){
 let panel=$(id);if(!panel){panel=document.createElement('aside');panel.id=id;panel.className='kp-outer-planets-panel no-print';anchor.insertAdjacentElement('afterend',panel);}
 const ids=selected();if(!ids.length||!date){panel.hidden=true;panel.replaceChildren();return;}
 const values=outerPositions(date),language=window.KPPreferences?.get().language==='marathi'?'marathi':'english';
 const heading=document.createElement('strong');heading.textContent=language==='marathi'?'बाह्य ग्रह UNP · फक्त प्रदर्शन':'Outer planets UNP · display only';
 const note=document.createElement('span');note.className='kp-outer-note';note.textContent=language==='marathi'?'KP कार्येश गणनेत समाविष्ट नाहीत':'Excluded from KP significator calculations';
 const list=document.createElement('div');list.className='kp-outer-values';
 for(const planetId of ids){const point=values[planetId],item=OUTER[planetId],badge=document.createElement('span');badge.className='kp-outer-value';badge.dataset.outerPlanet=planetId;badge.style.setProperty('--outer-colour',item.colour);badge.title=(language==='marathi'?item.mr:item.name)+' · '+dms(point.longitude)+' · '+(language==='marathi'?SIGNS.marathi:SIGNS.english)[Math.floor(point.longitude/30)]+' · '+note.textContent;badge.innerHTML='<b>'+item.short+'</b><span>'+(language==='marathi'?item.mr:item.name)+'</span><span>'+dms(point.longitude)+'</span>';list.append(badge);}
 panel.dataset.source=state.ayanamshaSource;panel.dataset.utc=date.toISOString();panel.setAttribute('aria-label',title+' · '+heading.textContent);panel.replaceChildren(heading,note,list);panel.hidden=false;
}
function renderOuter(){
 queued=false;const date=nativeDate(),kundali=$('kundali'),home=$('home-kundali');
 try{if(kundali)renderPanel(kundali,'kp-outer-planets-kundali',date,'Kundali');}catch(_){/* Optional display must not block native calculations. */}
 try{if(home)renderPanel(home,'kp-outer-planets-home',date,'Home Kundali');}catch(_){/* Optional display must not block native calculations. */}
 const transit=$('transit-chart');let tc=null;try{tc=window.KPTransitChart?.getData?.();}catch(_){tc=null;}
 let transitDate=null;try{transitDate=tc?.ready&&tc.utc?dateValue(tc.utc):null;}catch(_){transitDate=null;}
 try{if(transit)renderPanel(transit,'kp-outer-planets-transit',transitDate,'Transit chart');}catch(_){/* Optional display must not block transit calculations. */}
}
function queueRender(){if(queued)return;queued=true;requestAnimationFrame(renderOuter);}
function injectSettings(){
 const grid=$('settings-pane-calculation')?.querySelector('.settings-grid');if(!grid||$('setting-ayanamshaCalculation'))return;
 const card=document.createElement('section');card.className='kp-calculation-source-card settings-full';card.innerHTML='<div class="kp-source-heading"><span class="kp-source-icon" aria-hidden="true">☉</span><div><strong data-kp-source-en="Ayanamsha source" data-kp-source-mr="अयनांश स्रोत">Ayanamsha source</strong><small data-kp-source-en="Choose the sidereal reference used by automatic chart calculations." data-kp-source-mr="स्वयंचलित कुंडली गणनेसाठी निरयन संदर्भ निवडा.">Choose the sidereal reference used by automatic chart calculations.</small></div></div><label class="kp-source-field"><span data-kp-source-en="Calculation source" data-kp-source-mr="गणना स्रोत">Calculation source</span><select id="setting-ayanamshaCalculation"><option value="uploaded-kp">Uploaded KP ephemeris · current default</option><option value="swiss-kp">Swiss Ephemeris · Krishnamurti ayanamsha</option></select></label><p id="settings-ayanamsha-source-note" class="kp-source-note"></p>';
 const outer=document.createElement('fieldset');outer.className='kp-outer-settings settings-full';outer.innerHTML='<legend><span aria-hidden="true">♅</span> <span data-kp-source-en="Outer Planets UNP" data-kp-source-mr="बाह्य ग्रह UNP">Outer Planets UNP</span></legend><p data-kp-source-en="Display only. These planets are excluded from the traditional nine-graha KP logic." data-kp-source-mr="फक्त प्रदर्शनासाठी. पारंपरिक नऊ-ग्रह KP गणनेत हे ग्रह समाविष्ट नाहीत.">Display only. These planets are excluded from the traditional nine-graha KP logic.</p><div class="kp-outer-checks"><label><input id="setting-outerUranus" type="checkbox"><span class="kp-outer-dot kp-ur"></span>Uranus</label><label><input id="setting-outerNeptune" type="checkbox"><span class="kp-outer-dot kp-ne"></span>Neptune</label><label><input id="setting-outerPluto" type="checkbox"><span class="kp-outer-dot kp-pl"></span>Pluto</label></div>';
 const readonly=$('settings-ayan-summary')?.closest('.settings-readonly');if(readonly)readonly.before(card,outer);else grid.append(card,outer);
 syncControls();syncLanguage();updateSummary();card.addEventListener('change',markDraft);outer.addEventListener('change',markDraft);
 $('settings-save')?.addEventListener('click',saveControls);$('settings-cancel')?.addEventListener('click',()=>setTimeout(()=>{syncControls();syncLanguage();updateSummary();},0));
}
function readControls(){return normalize({ayanamshaSource:$('setting-ayanamshaCalculation')?.value,outerUranus:$('setting-outerUranus')?.checked,outerNeptune:$('setting-outerNeptune')?.checked,outerPluto:$('setting-outerPluto')?.checked});}
function syncControls(){if($('setting-ayanamshaCalculation'))$('setting-ayanamshaCalculation').value=state.ayanamshaSource;for(const key of ['outerUranus','outerNeptune','outerPluto'])if($('setting-'+key))$('setting-'+key).checked=state[key];}
function markDraft(){window.KPSettings?.setStatus(window.KPPreferences?.get().language==='marathi'?'बदल लागू करण्यासाठी जतन करा.':'Save to apply the calculation-source changes.');}
function saveControls(){
 if(document.querySelector('#kp-settings-shell [data-setting]:invalid'))return;
 const next=readControls(),changed=JSON.stringify(next)!==JSON.stringify(state);state=next;persist();syncControls();applySource();
 if(changed)setTimeout(()=>{try{window.calculateAll?.();window.KPTransitChart?.refresh?.();}catch(error){window.KPSettings?.setStatus(error.message);}queueRender();},0);
}
function applySource(){
 if(!window.KPEphemerisSources)throw Error('The ephemeris source adapter is unavailable.');
 window.KPEphemerisSources.setSource(state.ayanamshaSource,{prepare:true});updateSummary();queueRender();window.dispatchEvent(new CustomEvent('kp-calculation-source-changed',{detail:{settings:copy(state)}}));
}
function updateSummary(){
 const note=$('settings-ayanamsha-source-note'),summary=$('settings-ayan-summary'),birth=$('dob')?.value;
 if(note)note.textContent=isSwiss()?'Swiss Ephemeris 2.10.03 reference · Krishnamurti sidereal mode 5 · 1900–2100.':'Uses the uploaded annual KP ayanamsha and uploaded 05:30 ephemeris rows.';
 if(summary&&isSwiss())try{const value=window.KPSwissKrishnamurti.at((birth||'2000-01-01')+'T00:00:00Z');summary.textContent=window.KPSwissKrishnamurti.format(value)+(birth?' · '+birth:'')+' · Swiss Krishnamurti';}catch(_){summary.textContent='Swiss Krishnamurti · enter a valid birth date';}
}
function syncLanguage(){const language=window.KPPreferences?.get().language,marathi=language==='marathi';document.querySelectorAll('[data-kp-source-en]').forEach(node=>{const en=node.dataset.kpSourceEn,mr=node.dataset.kpSourceMr||en;node.textContent=marathi?mr:language==='bilingual'?en+' · '+mr:en;});}
function installSaveRestore(){
 if(typeof window.getChartData==='function'){const get=window.getChartData;window.getChartData=function(...args){const data=get.apply(this,args);data.calculationSources=copy(state);return data;};}
 if(typeof window.restoreChartData==='function'){const restore=window.restoreChartData;window.restoreChartData=function(data,...args){const next=data?.calculationSources?normalize(data.calculationSources):state,previous=state;restoring=true;state=next;try{window.KPEphemerisSources?.setSource(state.ayanamshaSource,{prepare:false,notify:false});const result=restore.call(this,data,...args);persist();syncControls();applySource();return result;}catch(error){state=previous;window.KPEphemerisSources?.setSource(previous.ayanamshaSource,{prepare:false,notify:false});throw error;}finally{restoring=false;}};}
}
function init(){
 injectSettings();installSaveRestore();syncControls();applySource();
 window.addEventListener('kp-preferences-changed',()=>{syncLanguage();updateSummary();queueRender();});window.addEventListener('chart-saved',queueRender);window.addEventListener('kundali-style-changed',queueRender);
 document.addEventListener('change',event=>{if(event.target?.id==='dob'){updateSummary();queueRender();}});
 const main=document.querySelector('main');if(main)new MutationObserver(records=>{if(records.some(record=>[...record.addedNodes].some(node=>node.nodeType===1&&!node.classList?.contains('kp-outer-planets-panel'))))queueRender();}).observe(main,{childList:true,subtree:true});
}
window.KPCalculationSources=Object.freeze({defaults:DEFAULTS,get:()=>copy(state),set:settings=>{state=normalize(settings);persist();syncControls();applySource();},swissAyanamsha:value=>window.KPSwissKrishnamurti.at(value),outerPositions,selected,metadata:()=>window.KPSwissKrishnamurti.metadata});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else setTimeout(init,0);
})();
