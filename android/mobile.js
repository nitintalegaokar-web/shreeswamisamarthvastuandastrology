(() => {
'use strict';
if(document.documentElement.dataset.kpMobileReady)return;
document.documentElement.dataset.kpMobileReady='true';
window.print=()=>KPAndroid.printReport();
const send=(blob,name)=>{if(blob.size>16*1024*1024){alert('This export is larger than the mobile file limit. Export smaller sections.');return;}const reader=new FileReader();reader.onload=()=>KPAndroid.saveFile(name||'KP-MASTER-export.txt',(blob.type||'application/octet-stream').split(';')[0],String(reader.result).split(',')[1]);reader.onerror=()=>alert('The file could not be prepared.');reader.readAsDataURL(blob);};
document.addEventListener('click',async event=>{const a=event.target.closest?.('a[download]');if(!a||!a.href.startsWith('blob:')&&!a.href.startsWith('data:'))return;event.preventDefault();event.stopImmediatePropagation();try{send(await (await fetch(a.href)).blob(),a.download);}catch(e){alert('Unable to save this file: '+e.message);}},true);
const keys=['kpRaphaelData','kpAstrologerSettings','kpResourcesV1','kpRaphaelSoftwarePreferencesV1','kpReportCoverPhoto','kpAboutPortraitV1','kpVedicChartStyleV1','kpCalculationSourcesV1','kpAspectTableColours'];
const allowed=k=>keys.includes(k)||k.startsWith('kpResourceImportedDocument:');
function backup(){const data={format:'KP-MASTER-mobile-backup',version:1,createdAt:new Date().toISOString(),storage:{},currentChart:typeof getChartData==='function'?getChartData():null};for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i);if(allowed(key))data.storage[key]=localStorage.getItem(key);}send(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),'KP-MASTER-mobile-backup.json');}
function restoreData(text){try{const data=JSON.parse(text);if(data.format!=='KP-MASTER-mobile-backup'||data.version!==1||!data.storage||Array.isArray(data.storage)||typeof data.storage!=='object')throw Error('Choose a KP MASTER mobile backup.');const entries=Object.entries(data.storage);if(entries.some(([k,v])=>!allowed(k)||typeof v!=='string'))throw Error('Invalid backup entries.');if(!confirm('Restore your saved charts, notes and settings from this backup? Existing matching saved data will be replaced.'))return false;const old=Array.from(new Set([...entries.map(([k])=>k),'kpRaphaelData'])).map(k=>[k,localStorage.getItem(k)]);try{for(const [k,v] of entries)localStorage.setItem(k,v);if(data.currentChart)localStorage.setItem('kpRaphaelData',JSON.stringify(data.currentChart));}catch(e){for(const [k,v] of old)if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v);throw e;}location.reload();return true;}catch(e){alert('Restore failed: '+e.message);return false;}}
function restore(){const input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.hidden=true;document.body.append(input);input.onchange=async()=>{try{const f=input.files[0];if(f){if(f.size>16*1024*1024)throw Error('Backup file is too large.');restoreData(await f.text());}}catch(e){alert(e.message);}finally{input.remove();}};input.click();}
window.KPMobile=Object.freeze({backup,restore,restoreData});
// Presentation only: preserve the approved chart and calculation objects.
const mobileStyle=document.createElement('style');mobileStyle.id='kp-mobile-readability';
mobileStyle.textContent=`
@media screen and (max-width:900px){
#home .home-dashboard{grid-template-columns:minmax(0,1fr)!important}
#home .home-table-mount{overflow-x:auto!important;-webkit-overflow-scrolling:touch}
#home .home-table-mount table{min-width:660px!important}
#home table :is(th,td){font-size:13px!important;line-height:1.5!important;padding:7px!important}
#home .home-panel h2,#home .home-view-buttons button{font-size:13px!important}
#home #home-fourstep .kp-step-grid{grid-template-columns:1fr!important}
.kp-mobile-chart-scroll{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
.kp-mobile-chart-scroll .north9-chart{width:760px!important;min-width:760px!important;max-width:none!important}
.kp-mobile-planet-list{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:8px 0;font:14px/1.5 sans-serif;color:#173b52}
.kp-mobile-planet-list span{background:#eef4f8;border:1px solid #cadce7;border-radius:6px;padding:6px;overflow-wrap:anywhere}
.kp-mobile-scroll-hint{font:12px/1.5 sans-serif;color:#36546b;margin:6px 0}
}
@media screen{body.kp-mobile-report{min-width:740px!important;overflow:auto!important}body.kp-mobile-report .report-page{margin-left:10px!important;margin-right:10px!important}}
@media print{.kp-mobile-scroll-hint,.kp-mobile-planet-list{display:none!important}.kp-mobile-chart-scroll{overflow:visible!important}body.kp-mobile-report{min-width:0!important}}
`;
document.head.append(mobileStyle);
function readableCharts(){
 if(!document.getElementById('home')&&document.querySelector('.report-page,.sheet,.kp-preview-tools,.preview-tools'))document.body.classList.add('kp-mobile-report');
 document.querySelectorAll('#home .home-table-mount').forEach(m=>{if(m.dataset.mobileScroll)return;m.dataset.mobileScroll='true';m.tabIndex=0;const hint=document.createElement('p');hint.className='kp-mobile-scroll-hint';hint.textContent='Swipe sideways to see all table columns.';m.before(hint);});
 document.querySelectorAll('#home .north9-chart,#kundali-north').forEach(chart=>{
  if(!chart.parentElement.classList.contains('kp-mobile-chart-scroll')){const wrap=document.createElement('div');wrap.className='kp-mobile-chart-scroll';chart.before(wrap);wrap.append(chart);}
  const wrap=chart.parentElement;
  let list=wrap.nextElementSibling;if(!list?.classList.contains('kp-mobile-planet-list')){list=document.createElement('div');list.className='kp-mobile-planet-list';wrap.after(list);}
  const entries=[...chart.querySelectorAll('svg text[data-planet]')].map(n=>[n.getAttribute('data-planet'),n.textContent,n.querySelector('title')?.textContent||'']);
  const signature=JSON.stringify(entries);if(list.dataset.signature===signature)return;list.dataset.signature=signature;list.replaceChildren();
  for(const [id,text,title] of entries){const row=document.createElement('span');row.textContent=title||text||id;list.append(row);}
 });
}
let readabilityPending=false;
new MutationObserver(()=>{if(readabilityPending)return;readabilityPending=true;requestAnimationFrame(()=>{readabilityPending=false;readableCharts();});}).observe(document.body,{childList:true,subtree:true});
readableCharts();
// Long-press opens the same chart/table enlargement as the approved double click.
let timer,start,target;
document.addEventListener('pointerdown',e=>{if(e.pointerType!=='touch')return;target=e.target.closest('table,.v38-grid,.si-chart,.north9-chart');if(!target)return;start=[e.clientX,e.clientY];timer=setTimeout(()=>{target.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));timer=null;},650);},{passive:true});
const cancel=()=>{clearTimeout(timer);timer=null;};document.addEventListener('pointerup',cancel,{passive:true});document.addEventListener('pointercancel',cancel,{passive:true});document.addEventListener('pointermove',e=>{if(start&&(Math.abs(e.clientX-start[0])>12||Math.abs(e.clientY-start[1])>12))cancel();},{passive:true});
})();
