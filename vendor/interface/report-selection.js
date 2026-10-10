/* Selected reports: prepare native calculations before preview, print or PDF. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const FLOW_CSS=`html,body{margin:0;padding:0;background:#edf1f5}
body>.report-page{display:block!important;margin:10px auto!important;box-sizing:border-box}
body>.report-page:not(.kp-a4-page){width:190mm!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}
.report-selection-preview-tools{position:sticky;top:0;z-index:100;padding:8px;background:#f7f9fc;display:flex;justify-content:center;gap:7px;flex-wrap:wrap}
.report-selection-preview-tools button{font-size:12px;min-height:29px;padding:4px 10px}
@page{size:A4;margin:10mm}
@media print{.report-selection-preview-tools{display:none!important}body>.report-page{display:block!important;margin:0!important;zoom:1!important}
body>.report-page:not(.kp-a4-page){width:190mm!important;min-height:0!important;height:auto!important;overflow:visible!important;break-after:page}
body>.report-page:last-child{break-after:auto}}`;
const PDF_CSS=`html,body{background:white!important;margin:0!important;padding:0!important}
body>.report-page{display:block!important;margin:0!important;zoom:1!important;box-shadow:none!important}
.report-page{break-after:auto!important}.v-report-page .v-table :is(th,td){font-size:9px!important}
.report-page .v-table-wrap{overflow:visible!important}.no-print{display:none!important}`;
const tr=s=>window.KPLanguage?.translate(s)||s;
function fail(message){const status=$('report-page-selection-status');status.textContent=message;status.dataset.printError='true';status.tabIndex=-1;status.focus();window.showToast?.(message,'error');}
function styles(){return [...document.querySelectorAll('style')].map(n=>'<style>'+n.textContent.replace(/#kundali\b/g,'[data-report-id="kundali"]')+'</style>').join('');}
function normalize(doc){for(const page of doc.querySelectorAll('[data-report-section="event-promise"],[data-report-section="gemstones"],[data-report-section="nadi-astrology"],[data-report-section="kp-fourfold"],[data-report-section="kp-sixfold"],[data-report-section="kp-fourstep-section"]'))window.KPA4Preview?.normalize(doc,page);window.KPLanguage?.localize(doc);}
async function prepare(options={}){
 // Capture report groups at the click, including pages added by calculation.
 const sections=new Set(KPReportPages.selected().map(p=>p.dataset.reportSection));
 if(!options.vedic&&!sections.size)throw Error(tr('Select at least one page to print.'));
 const needs=options.vedic?KPVedicUI.needsViewPreparation():[...sections].some(id=>['vedic-sade-sati','vedic-varshaphal'].includes(id));
 if(needs)await KPVedicUI.prepareReports();
 window.renderReport?.();window.KPLanguage?.localize($('printReport'));
 if(options.vedic){const page=document.createElement('section');page.className='report-page v-report-page';page.dataset.reportSection='vedic-kundali';page.innerHTML='<h2 class="report-page-title">Vedic Kundali</h2>'+KPVedicUI.snapshot();window.KPLanguage?.localize(page);return [page];}
 return [...$('printReport').children].filter(p=>p.classList.contains('report-page')&&sections.has(p.dataset.reportSection));
}
function writePreview(preview,pages){
 preview.document.open();preview.document.write('<!doctype html><html><head><meta charset="UTF-8"><title>Selected report</title>'+styles()+'<style>'+FLOW_CSS+'</style></head><body><div class="report-selection-preview-tools no-print"><button id="preview-save-pdf" onclick="window.print()">Print / Save PDF</button><button onclick="document.querySelectorAll(\'.report-page\').forEach(p=>p.style.zoom=Math.min(2,(parseFloat(p.style.zoom)||1)+.1))">Zoom +</button><button onclick="document.querySelectorAll(\'.report-page\').forEach(p=>p.style.zoom=Math.max(.5,(parseFloat(p.style.zoom)||1)-.1))">Zoom −</button><button onclick="window.close()">Close preview</button></div>'+pages.map(p=>p.outerHTML).join('')+'</body></html>');preview.document.close();normalize(preview.document);
}
async function selectedPreview(print=false,options={}){
 // Open synchronously inside the user's click, before rendering or awaiting.
 const preview=window.open('','_blank');if(!preview){fail(tr('Allow popups to preview or print reports.'));return null;}
 preview.document.body.textContent=tr('Preparing selected reports…');
 try{const pages=await prepare(options);if(preview.closed)return null;writePreview(preview,pages);
  await preview.document.fonts.ready;
  if(print){await new Promise(resolve=>preview.requestAnimationFrame(()=>preview.requestAnimationFrame(resolve)));preview.focus();preview.print();}
  return preview;
 }catch(e){if(!preview.closed)preview.close();fail(e.message);return null;}
}
function intervals(page){const top=page.getBoundingClientRect().top;
 return [...page.querySelectorAll('tr,p,li,h1,h2,h3,h4,img,.v-chart,.v-sbc')].map(n=>{const r=n.getBoundingClientRect();let bottom=r.bottom;
  // Keep a heading with the beginning of the following block.
  if(/^H[1-4]$/.test(n.tagName)&&n.nextElementSibling){const next=n.nextElementSibling;bottom=(next.querySelector('tr,p,li')||next).getBoundingClientRect().bottom;}
  return {top:r.top-top,bottom:bottom-top};}).filter(r=>r.bottom>r.top);
}
function continuationHeader(page,start){if(start<1)return null;const top=page.getBoundingClientRect().top;
 return [...page.querySelectorAll('table')].find(t=>t.tHead&&t.getBoundingClientRect().top-top<start-1&&t.getBoundingClientRect().bottom-top>start+1)?.tHead||null;
}
function safeCut(start,limit,total,blocks){let cut=Math.min(start+limit,total);if(cut>=total)return total;
 for(let pass=0;pass<blocks.length;pass++){const crossing=blocks.filter(r=>r.top>start+1&&r.top<cut-0.5&&r.bottom>cut+0.5&&r.bottom-r.top<=limit);if(!crossing.length)break;cut=Math.min(...crossing.map(r=>r.top));}
 return cut>start+1?cut:Math.min(start+limit,total);
}
async function exportPDF(){let frame;const button=$('report-selection-pdf');button.disabled=true;
 try{
  const pages=await prepare();if(typeof html2canvas!=='function'||!window.jspdf?.jsPDF)throw Error(tr('PDF export is unavailable. Use Print / Save PDF.'));
  frame=document.createElement('iframe');frame.style.cssText='position:fixed;left:-10000px;top:0;width:820px;height:1200px;border:0';frame.setAttribute('aria-hidden','true');document.body.append(frame);
  const doc=frame.contentDocument;doc.open();doc.write('<!doctype html><html><head><meta charset="UTF-8">'+styles()+'<style>'+FLOW_CSS+PDF_CSS+'</style></head><body></body></html>');doc.close();await doc.fonts.ready;
  const pdf=new jspdf.jsPDF({orientation:'portrait',unit:'mm',format:'a4',compress:true});let sheet=0;
  for(const source of pages){const page=doc.importNode(source,true);doc.body.replaceChildren(page);normalize(doc);await doc.fonts.ready;
   page.style.setProperty('margin','0','important');page.style.setProperty('zoom','1','important');const width=page.getBoundingClientRect().width,total=Math.ceil(page.getBoundingClientRect().height),maxHeight=width*277/190,blocks=intervals(page);let start=0;
   while(start<total-0.5){const header=continuationHeader(page,start),headerHeight=header?.getBoundingClientRect().height||0,end=safeCut(start,maxHeight-headerHeight,total,blocks);
    if(sheet++)pdf.addPage();let y=10;
    if(header){const rect=header.getBoundingClientRect(),left=rect.left-page.getBoundingClientRect().left,canvas=await html2canvas(header,{scale:2,backgroundColor:'#ffffff',logging:false});pdf.addImage(canvas.toDataURL('image/png'),'PNG',10+left*190/width,y,rect.width*190/width,headerHeight*190/width,undefined,'FAST');canvas.width=canvas.height=0;y+=headerHeight*190/width;}
    const canvas=await html2canvas(page,{scale:2,backgroundColor:'#ffffff',logging:false,x:0,y:start,width,height:end-start,scrollX:0,scrollY:0,windowWidth:820,windowHeight:1200});pdf.addImage(canvas.toDataURL('image/png'),'PNG',10,y,190,(end-start)*190/width,undefined,'FAST');canvas.width=canvas.height=0;start=end;
   }
  }
  pdf.save('KP-Selected-Report.pdf');
 }catch(e){fail(e.message);}finally{frame?.remove();button.disabled=false;}
}
function init(){const card=$('report').querySelector('.card.no-print'),heading=card.querySelector('h2');heading.textContent='Select reports to print';card.classList.add('report-selection-window');$('report-page-picker').querySelector('legend').textContent='Report pages';$('report-page-picker').querySelector('p').textContent='Choose reports. Long reports continue onto additional A4 pages.';
 const actions=$('print-selected-report').parentElement;actions.className='actions report-selection-footer';const print=$('print-selected-report');print.textContent='Print';print.removeAttribute('onclick');print.addEventListener('click',()=>selectedPreview(true));
 for(const [id,text,handler] of [['report-selection-preview','Preview',()=>selectedPreview()],['report-selection-pdf','Export to PDF',exportPDF],['report-selection-close','Close',()=>document.querySelector('.app-sidebar [data-tab="home"]').click()]]){const b=document.createElement('button');b.id=id;b.type='button';b.textContent=text;b.addEventListener('click',handler);actions.append(b);}
 const all=document.createElement('label');all.className='report-select-all-label';all.innerHTML='<input id="report-all-toggle" type="checkbox">Select all';$('report-page-selection-status').before(all);all.firstChild.addEventListener('change',e=>{if(e.target.checked)KPReportPages.selectAll();else KPReportPages.clear();});
 function sync(){const inputs=[...$('report-page-options').querySelectorAll('input[data-report-page-key]')],checked=inputs.filter(n=>n.checked).length,box=$('report-all-toggle');box.checked=inputs.length>0&&checked===inputs.length;box.indeterminate=checked>0&&checked<inputs.length;}
 $('report-page-options').addEventListener('change',sync);new MutationObserver(sync).observe($('report-page-selection-status'),{childList:true});sync();$('report-select-all').parentElement.hidden=true;
}
window.KPSelectedReport=Object.freeze({preview:selectedPreview,exportPDF,prepare});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
