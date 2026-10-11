/* A shared A4 contract for individual previews, selected reports and hosted PDFs. */
(()=>{'use strict';
const css=`@page{size:A4 portrait;margin:10mm}
html,body{margin:0!important;padding:0!important;background:#eef1f5}
body::before,body::after{display:none!important;content:none!important}
body>.report-page{display:block!important;box-sizing:border-box!important;width:190mm!important;max-width:190mm!important;margin:10px auto!important;padding:4mm!important;border:3px double #5c4434!important;border-radius:0!important;background:white!important;color:#17212b!important}
body>.report-page:not(.kp-a4-page){height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}
.report-page :is(.report-cover,.computed-report,.report-flow-content,.sp-page-inner){height:auto!important;min-height:0!important;max-height:none!important}
.report-page :is(.table-scroll,.table-wrap,.kp-table-wrap,.basic-table-scroll,.am-scroll,.kp-table-scroll,.worksheet-scroll,.v-table-wrap){width:100%!important;min-width:0!important;max-height:none!important;height:auto!important;overflow:visible!important}
.report-page table{box-sizing:border-box!important;width:100%!important;max-width:100%!important;min-width:0!important;table-layout:fixed!important;border-collapse:collapse!important}
.report-page :is(td,th){white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal;max-width:none!important;font-size:9px!important;padding:3px!important;vertical-align:top}
.report-page :is(p,li,dd,dt,h2,h3,h4){overflow-wrap:anywhere;max-width:100%}
.report-page :is(img,canvas){max-width:100%!important;height:auto}
.report-page :is(.v-report-content,.bi-facts,.sp-column){min-width:0!important;max-width:100%!important}
.report-page .v-report-content{overflow:visible!important}
.report-page thead{display:table-header-group!important}.report-page tfoot{display:table-footer-group!important}
.report-page :is(tr,.v-chart,.bi-facts>dl>div){break-inside:avoid!important;page-break-inside:avoid!important}
.report-page :is(h2,h3,h4){break-after:avoid!important}
@media print{html,body{background:white!important}.no-print,.kp-preview-tools,.preview-tools,.report-selection-preview-tools,.notepad-preview-tools{display:none!important}body>.report-page{margin:0!important;zoom:1!important;box-shadow:none!important;break-after:page!important;page-break-after:always!important}body>.report-page:last-child{break-after:auto!important;page-break-after:auto!important}}`;
function prepare(doc){if(!doc?.head)return;let style=doc.getElementById('kp-report-a4-contract');if(!style){style=doc.createElement('style');style.id='kp-report-a4-contract';doc.head.append(style);}style.textContent=css;const language=window.KPPreferences?.get().language||document.documentElement.dataset.kpLanguage||'english';doc.documentElement.lang=window.KPLanguage?.languages?.find?.(l=>l.value===language)?.code||(language==='marathi'?'mr':'en');doc.documentElement.dataset.kpLanguage=language;window.KPLanguage?.localize(doc);doc.querySelectorAll('.report-page .v38-name,.report-page .v38-degree').forEach(n=>n.style.setProperty('font-size',n.classList.contains('v38-name')?'9px':'8px','important'));doc.querySelectorAll('.report-page [data-report-id="basic"],.report-page .pc-entry-pair').forEach(n=>n.remove());}
function install(){const old=window.KPReportPreview;if(old)window.KPReportPreview=Object.freeze({...old,open(id){const w=old.open(id==='basic'?'vedic-information':id);if(w){prepare(w.document);w.document.fonts.ready.then(()=>{for(const page of w.document.querySelectorAll('.kp-a4-page'))window.KPA4Preview?.fit(w.document,page);});}return w;}});}
window.KPA4Reports=Object.freeze({css,prepare});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,0));else install();
})();
