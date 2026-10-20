/* Select native DBA periods and a civil date range without editing the natal chart. */
(()=>{'use strict';const $=id=>document.getElementById(id),LEVELS=['MD','AD','PD'];let roots=[],signature='',initialized=false,restoring=false;
const ids=['tr-dba-selection-source','tr-selected-md','tr-selected-ad','tr-selected-pd','tr-date-range-source','tr-search-date-start','tr-search-date-end'];
const code=lord=>KPDisplay.idByName[lord]||lord,copy=data=>JSON.parse(JSON.stringify(data));
const eventMode=()=>$('tr-mode')?.value==='event';
const source=()=>$('tr-dba-selection-source')?.value||'current',dateSource=()=>$('tr-date-range-source')?.value||'period';
function children(row){if(!row)return [];const birth=roots[0]?.startMs??-Infinity;return KPHomeDasha.subdivide(row).filter(child=>child.endMs>Math.max(row.startMs,birth)&&child.startMs<row.endMs);}
function selectedIndex(id,rows){const n=Number($(id)?.value);return Number.isInteger(n)&&n>=0&&n<rows.length?n:0;}
function optionText(row){const name=KPLanguage?.translate(code(row.lord))||code(row.lord),date=n=>new Date(n).toISOString().slice(0,10);return name+' · '+KPPreferences.formatDate(date(Math.max(row.startMs,roots[0]?.startMs??row.startMs)))+' → '+KPPreferences.formatDate(date(row.endMs));}
function options(id,rows,preferred){const n=$(id);if(!n)return;const index=Number.isInteger(preferred)&&preferred>=0&&preferred<rows.length?preferred:0;n.replaceChildren(...rows.map((p,i)=>new Option(optionText(p),String(i))));n.value=String(index);n.disabled=!rows.length;}
function sync(force=false){
 if(!initialized||eventMode())return;KPHomeDasha.refresh();const native=KPHomeDasha.getData(),next=JSON.stringify([$('dob')?.value,$('birthTime')?.value,native.timeZoneHours,native.levels?.[0]?.rows?.map(r=>[r.lord,r.startMs,r.endMs])]);
 const changed=next!==signature;if(changed){signature=next;roots=native.ready?native.levels[0].rows:[];if(!restoring)$('tr-dba-selection-source').value='current';}
 if(!force&&!changed&&!['current','auto-forward','date'].includes(source()))return;
 let md=selectedIndex('tr-selected-md',roots),ads=children(roots[md]),ad=selectedIndex('tr-selected-ad',ads),pds=children(ads[ad]),pd=selectedIndex('tr-selected-pd',pds);
 if(['current','auto-forward','date'].includes(source())){
  let instant=Date.now();if(source()==='date')try{instant=utc($('tr-search-date-start').value).getTime();}catch(_){}
  const civil=instant+Number(native.timeZoneHours)*3600000,at=rows=>Math.max(0,rows.findIndex(r=>r.startMs<=civil&&civil<r.endMs));md=at(roots);ads=children(roots[md]);ad=at(ads);pds=children(ads[ad]);pd=at(pds);
 }
 options('tr-selected-md',roots,md);options('tr-selected-ad',ads,ad);options('tr-selected-pd',pds,pd);
}
function periods(){
 if(!initialized)return null;if(eventMode())return {periods:{},selection:'event',timeZoneHours:Number($('tr-timezone').value)/60};sync();if(source()==='date'){const data=KPTransit.currentPeriods(utc($('tr-search-date-start').value));return {...data,selection:'date'};}if(source()!=='selected')return null;
 const native=KPHomeDasha.getData();if(!native.ready||!roots.length)throw Error('Calculate the native DBA timeline before selecting periods.');
 const md=roots[selectedIndex('tr-selected-md',roots)],ads=children(md),ad=ads[selectedIndex('tr-selected-ad',ads)],pds=children(ad),pd=pds[selectedIndex('tr-selected-pd',pds)];
 const offset=Number(native.timeZoneHours)*3600000,result={};let lower=-Infinity,upper=Infinity;
 for(const [i,row] of [md,ad,pd].entries()){if(!row)throw Error('Choose a valid MD, AD and PD.');lower=Math.max(lower,row.startMs);upper=Math.min(upper,row.endMs);result[LEVELS[i]]={...row,id:code(row.lord),startMs:lower,endMs:upper,startUTC:new Date(lower-offset).toISOString(),endUTC:new Date(upper-offset).toISOString()};}
 if(dateSource()==='custom'){try{const start=utc($('tr-search-date-start').value),end=utc($('tr-search-date-end').value),pd=result.PD;if(+end<=Date.parse(pd.startUTC)||+start>=Date.parse(pd.endUTC)){$('tr-date-range-source').value='period';$('tr-period').value='PD';setDefaults({start:new Date(pd.startUTC),end:new Date(pd.endUTC)});}}catch(_){} }
 return {periods:result,timeZoneHours:native.timeZoneHours,instant:new Date().toISOString(),selection:'selected'};
}
function utc(text){if(!/^\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?$/.test(text))throw Error('Choose valid start and end dates and times.');const offset=Number($('tr-timezone').value);const date=new Date(Date.parse(text+'Z')-offset*60000);if(!Number.isFinite(date.getTime()))throw Error('Choose valid start and end dates and times.');return date;}
function range(data){
 if(!initialized||!eventMode()&&dateSource()!=='custom')return null;const start=utc($('tr-search-date-start').value),end=utc($('tr-search-date-end').value);
 if(end<=start)throw Error('The end date must be after the start date.');if(end-start>7671*86400000)throw Error('Choose a search range of at most twenty-one years.');
 if(start.getUTCFullYear()<1900||end.getUTCFullYear()>2100)throw Error('Choose dates within the supported years 1900–2100.');
 return {start,end,level:'Dates',lord:eventMode()?'All nine planets · no DBA':LEVELS.map(level=>data.periods[level].id).join(' / ')};
}
function setDefaults(range){if(!initialized||eventMode()||dateSource()==='custom')return;const local=ms=>new Date(ms+Number($('tr-timezone').value)*60000).toISOString().slice(0,19);$('tr-search-date-start').value=local(Math.ceil(range.start.getTime()/1000)*1000);$('tr-search-date-end').value=local(Math.floor(range.end.getTime()/1000)*1000);}
function filterPeriods(rows,data){if(source()!=='selected')return rows;const pd=data.periods.PD,a=Date.parse(pd.startUTC),b=Date.parse(pd.endUTC);return rows.filter(row=>row.lords.every(lord=>lord.id===data.periods[lord.level].id)).map(row=>({...row,start:new Date(Math.max(a,Date.parse(row.start))).toISOString(),end:new Date(Math.min(b,Date.parse(row.end))).toISOString()})).filter(row=>row.end>row.start);}
function changed(event){
 const id=event.target.id;if(!ids.includes(id))return;if(eventMode()){KPTransit.cancel();KPTransit.refresh();return;}
 if(id==='tr-dba-selection-source'&&source()==='auto-forward'){window.KPTransitWorkspace?.setForwardDates();}
 if(id==='tr-dba-selection-source')$('tr-date-range-source').value=source()==='date'?'custom':source()==='current'?'period':dateSource();
 if(id==='tr-date-range-source'){if(dateSource()==='custom'&&['current','auto-forward','selected'].includes(source()))$('tr-dba-selection-source').value='date';else if(dateSource()==='period'&&source()==='date')$('tr-dba-selection-source').value='selected';}
 if(id==='tr-selected-md'||id==='tr-selected-ad'||id==='tr-selected-pd'||id==='tr-dba-selection-source'&&source()==='selected'){$('tr-dba-selection-source').value='selected';$('tr-date-range-source').value='period';$('tr-period').value='PD';}
 if(id==='tr-selected-md'){$('tr-selected-ad').value='0';$('tr-selected-pd').value='0';}else if(id==='tr-selected-ad')$('tr-selected-pd').value='0';
 if(id==='tr-search-date-start'||id==='tr-search-date-end'){$('tr-date-range-source').value='custom';$('tr-dba-selection-source').value='date';}
 sync(true);KPTransit.cancel();KPTransit.refresh();
}
function init(){
 const mount=document.createElement('details');mount.id='tr-date-dba-selection';mount.className='tr-selection no-print';mount.innerHTML='<summary>Select dates / DBA</summary><div class="tr-selection-grid"><label>DBA selection<select id="tr-dba-selection-source"><option value="current">Current DBA</option><option value="date">DBA at start date</option><option value="selected">Selected DBA</option></select></label><label>MD<select id="tr-selected-md"></select></label><label>AD<select id="tr-selected-ad"></select></label><label>PD<select id="tr-selected-pd"></select></label><label>Date range<select id="tr-date-range-source"><option value="period">Selected period</option><option value="custom">Custom dates</option></select></label><label>Start date / time<input id="tr-search-date-start" type="datetime-local" step="1"></label><label>End date / time<input id="tr-search-date-end" type="datetime-local" step="1"></label><button id="tr-use-current-dba" type="button">Use current DBA</button></div><p class="tr-selection-note">Times use the selected date/time zone. End time is exclusive.</p>';
 $('transit').querySelector('.tr-simple-choice').after(mount);initialized=true;sync(true);$('transit').addEventListener('change',changed,true);$('tr-use-current-dba').addEventListener('click',()=>{$('tr-dba-selection-source').value='current';$('tr-date-range-source').value='period';sync(true);KPTransit.cancel();KPTransit.refresh();});
 // Set custom-date mode before the core input handler refreshes period defaults.
 $('transit').addEventListener('input',event=>{if(['tr-search-date-start','tr-search-date-end'].includes(event.target.id))changed(event);},true);
 const restore=window.restoreChartData;window.restoreChartData=function(data,...args){restoring=true;try{const result=restore.call(this,data,...args);window.KPSimpleTransits?.restoreSelection(data);const apply=id=>{const field=data?.fields?.[id],n=$(id);if(field&&n&&typeof field.value==='string'&&(n.tagName!=='SELECT'||[...n.options].some(o=>o.value===field.value)))n.value=field.value;};
 for(const id of ['tr-dba-selection-source','tr-date-range-source','tr-search-date-start','tr-search-date-end'])apply(id);if(source()==='date'&&dateSource()==='period')$('tr-date-range-source').value='custom';if(source()==='current'&&dateSource()==='custom')$('tr-dba-selection-source').value='date';sync(true);
 // Restore dependent choices after their parent has rebuilt the valid children.
 for(const id of ['tr-selected-md','tr-selected-ad','tr-selected-pd']){apply(id);sync(true);}KPTransit.refresh();return result;}finally{restoring=false;}};
 window.addEventListener('kp-preferences-changed',()=>{sync(true);KPTransit.refresh();});KPTransit.refresh();KPLanguage?.localize(mount);
}
window.KPTransitSelection=Object.freeze({periods,range,setDefaults,filterPeriods,sync,isActive:()=>initialized,isSelected:()=>source()==='selected',getData:()=>copy({source:source(),dateSource:dateSource(),selection:Object.fromEntries(ids.map(id=>[id,$(id)?.value]))})});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
