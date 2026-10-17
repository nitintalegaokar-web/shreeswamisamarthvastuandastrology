(() => {
'use strict';
if(document.documentElement.dataset.kpMobileReady)return;
document.documentElement.dataset.kpMobileReady='true';
window.print=()=>{if(document.querySelector('body>.report-single-page')&&KPAndroid.saveSinglePageKundali)KPAndroid.saveSinglePageKundali();else KPAndroid.printReport();};
const send=(blob,name)=>{if(blob.size>16*1024*1024){alert('This export is larger than the mobile file limit. Export smaller sections.');return;}const reader=new FileReader();reader.onload=()=>KPAndroid.saveFile(name||'KP-MASTER-export.txt',(blob.type||'application/octet-stream').split(';')[0],String(reader.result).split(',')[1]);reader.onerror=()=>alert('The file could not be prepared.');reader.readAsDataURL(blob);};
document.addEventListener('click',async event=>{const a=event.target.closest?.('a[download]');if(!a||!a.href.startsWith('blob:')&&!a.href.startsWith('data:'))return;event.preventDefault();event.stopImmediatePropagation();try{send(await (await fetch(a.href)).blob(),a.download);}catch(e){alert('Unable to save this file: '+e.message);}},true);
const keys=['kp-master-small-shortcuts-visible-v1','kpMobileIconsHidden','kpRaphaelData','kpAstrologerSettings','kpResourcesV1','kpRaphaelSoftwarePreferencesV1','kpReportCoverPhoto','kpAboutPortraitV1','kpVedicChartStyleV1','kpCalculationSourcesV1','kpAspectTableColours'];
const allowed=k=>keys.includes(k)||k.startsWith('kpResourceImportedDocument:');
function backup(){const data={format:'KP-MASTER-mobile-backup',version:1,createdAt:new Date().toISOString(),storage:{},currentChart:typeof getChartData==='function'?getChartData():null};for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i);if(allowed(key))data.storage[key]=localStorage.getItem(key);}send(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),'KP-MASTER-mobile-backup.json');}
function restoreData(text){try{const data=JSON.parse(text);if(data.format!=='KP-MASTER-mobile-backup'||data.version!==1||!data.storage||Array.isArray(data.storage)||typeof data.storage!=='object')throw Error('Choose a KP MASTER mobile backup.');const entries=Object.entries(data.storage);if(entries.some(([k,v])=>!allowed(k)||typeof v!=='string'))throw Error('Invalid backup entries.');if(!confirm('Restore your saved charts, notes and settings from this backup? Existing matching saved data will be replaced.'))return false;const old=Array.from(new Set([...entries.map(([k])=>k),'kpRaphaelData'])).map(k=>[k,localStorage.getItem(k)]);try{for(const [k,v] of entries)localStorage.setItem(k,v);if(data.currentChart)localStorage.setItem('kpRaphaelData',JSON.stringify(data.currentChart));}catch(e){for(const [k,v] of old)if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v);throw e;}location.reload();return true;}catch(e){alert('Restore failed: '+e.message);return false;}}
function restore(){const input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.hidden=true;document.body.append(input);input.onchange=async()=>{try{const f=input.files[0];if(f){if(f.size>16*1024*1024)throw Error('Backup file is too large.');restoreData(await f.text());}}catch(e){alert(e.message);}finally{input.remove();}};input.click();}
let savingSinglePage=false;
async function singlePagePDF(){
 if(savingSinglePage)return;savingSinglePage=true;let frame;
 try{
  if(!window.currentKPModel?.ready)throw Error('Calculate the kundali first.');
  renderReport();const source=document.querySelector('#printReport>[data-report-section="single-page"]');if(!source)throw Error('The single-page kundali is unavailable.');
  frame=document.createElement('iframe');frame.style.cssText='position:fixed;left:-10000px;top:0;width:820px;height:1200px;border:0';document.body.append(frame);const doc=frame.contentDocument;doc.open();doc.write('<!doctype html><html><head><meta charset="utf-8">'+[...document.querySelectorAll('style')].map(n=>'<style>'+n.textContent+'</style>').join('')+'</head><body>'+source.outerHTML+'</body></html>');doc.close();
  KPA4Reports.prepare(doc);KPA4Preview.normalize(doc);await doc.fonts.ready;KPA4Preview.fit(doc);const page=doc.querySelector('.report-page');page.style.setProperty('margin','0','important');
  const canvas=await html2canvas(page,{scale:2,backgroundColor:'#ffffff',logging:false,windowWidth:820,windowHeight:1200});const pdf=new jspdf.jsPDF({orientation:'portrait',unit:'mm',format:'a4'});pdf.addImage(canvas.toDataURL('image/png'),'PNG',10,10,190,277);send(pdf.output('blob'),'KP-Kundali-Single-Page.pdf');
 }catch(e){alert('Single-page PDF: '+e.message);}finally{frame?.remove();savingSinglePage=false;}
}
function preparePrint(){if(document.querySelector('body>.report-single-page')){KPAndroid.saveSinglePageKundali();return false;}if(document.querySelector('#home.active,#south9.active')){singlePagePDF();return false;}return true;}
window.KPMobile=Object.freeze({backup,restore,restoreData,singlePagePDF,preparePrint});
document.addEventListener('click',event=>{if(event.target.closest('#home-single-page-print,#south-single-page-print')){event.preventDefault();event.stopImmediatePropagation();singlePagePDF();}},true);
// Presentation only: preserve the approved chart and calculation objects.
function installMobileNavigation(){
 if(!document.getElementById('home'))return;document.body.classList.add('kp-mobile-sidebar-navigation');document.getElementById('kp-compact-navigation')?.remove();document.getElementById('kp-mobile-icons-toggle')?.remove();
 const nav=document.querySelector('.app-sidebar nav');if(nav&&!document.getElementById('kp-mobile-ruling-link')){const button=document.createElement('button');button.id='kp-mobile-ruling-link';button.type='button';button.textContent='Ruling Planet';button.onclick=event=>{event.stopPropagation();document.querySelector('.sidebar-close')?.click();KPRulingFinder.open();};nav.append(button);}
}

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
html body.kp-mobile-sidebar-navigation #kp-compact-navigation{display:none!important}
html body.app-ready.kp-compact-navigation.kp-mobile-sidebar-navigation :is(.workspace-topbar,main,.software-footer){margin-left:0!important}
html body.app-ready.kp-compact-navigation.kp-mobile-sidebar-navigation .app-sidebar{display:none!important}
html body.app-ready.kp-compact-navigation.kp-mobile-sidebar-navigation.menu-open .app-sidebar{display:flex!important;position:fixed!important;left:0!important;top:0!important;bottom:0!important;width:min(280px,85vw)!important;transform:none!important;z-index:200!important;overflow:auto!important}
html body.kp-mobile-sidebar-navigation #menu-toggle{display:inline-flex!important}
#kp-mobile-icons-toggle{display:block;margin:5px 8px;padding:7px 12px;border:1px solid #aecad9;border-radius:8px;background:#eaf4fa;color:#174b69;font:600 13px sans-serif;min-height:36px}#kp-quick-tools.kp-mobile-icons-hidden{display:none!important}
@media print{#kp-mobile-icons-toggle{display:none!important}.kp-mobile-scroll-hint,.kp-mobile-planet-list{display:none!important}.kp-mobile-chart-scroll{overflow:visible!important}body.kp-mobile-report{min-width:0!important}}
`;
document.head.append(mobileStyle);
function readableCharts(){
 installMobileNavigation();
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
