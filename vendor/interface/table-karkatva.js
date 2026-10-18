/* Reference popups for calculation tables only. Numeric degrees/dates are never house links. */
(()=>{'use strict';
const ROOTS='#home,#karyesh,#south9,#basic-information',HOUSE_FIELDS=new Set(['A','B','C','D','E','F','CSL','occ','own','csl','cstl','conj','Conj','aspg','Aspg']);let queued=false;
function mark(e,type,id){if(!e)return;e.dataset[type+'Karkatva']=String(id);e.setAttribute('role','button');e.setAttribute('tabindex','0');e.setAttribute('aria-haspopup','dialog');}
function houses(root){const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];while(walker.nextNode()){const n=walker.currentNode;if(n.parentElement.closest('[data-bhava-karkatva],[data-planet-ref],.kp-notations,.kp-notation-marker,.kp-step-label'))continue;if(/\b(?:[1-9]|1[0-2])\b/.test(n.nodeValue))nodes.push(n);}for(const n of nodes){const parts=n.nodeValue.split(/\b(1[0-2]|[1-9])\b/g),fragment=document.createDocumentFragment();parts.forEach((part,i)=>{if(i%2){const span=document.createElement('span');span.className='kp-house-reference';span.textContent=part;mark(span,'bhava',part);fragment.append(span);}else fragment.append(document.createTextNode(part));});n.replaceWith(fragment);}}
function refresh(){queued=false;const model=window.currentKPModel;if(!model?.ready)return;for(const root of document.querySelectorAll(ROOTS)){
 root.querySelectorAll('.kp-planet-label').forEach(e=>{const id=e.closest('[data-planet-ref]')?.dataset.planetRef;if(window.KPPlanetKarkatva?.get(id))mark(e,'planet',id);});
 root.querySelectorAll('tr[data-planet],tr[data-house]').forEach(row=>{const point=row.dataset.planet?model.planets.find(p=>p.id===row.dataset.planet):model.houses.find(h=>h.id===Number(row.dataset.house));if(!point)return;if(row.dataset.house)mark(row.querySelector('th'),'bhava',row.dataset.house);for(const cell of row.querySelectorAll('td[data-field]')){const field=cell.dataset.field;if(field==='signCode')mark(cell,'rashi',Math.floor(((point.longitude%1296000)+1296000)%1296000/108000)+1);else if(field==='nak'&&Number.isInteger(point.nakIndex))mark(cell,'nakshatra',point.nakIndex);else if(HOUSE_FIELDS.has(field))houses(cell);}});
 root.querySelectorAll('.kp-step strong').forEach(houses);
 root.querySelectorAll('.ep-house').forEach(e=>{const n=Number(e.textContent.trim());if(Number.isInteger(n)&&n>=1&&n<=12)mark(e,'bhava',n);});
 }}
function schedule(){if(!queued){queued=true;requestAnimationFrame(refresh);}}
function init(){refresh();const observer=new MutationObserver(schedule);document.querySelectorAll(ROOTS).forEach(e=>observer.observe(e,{childList:true,subtree:true}));window.addEventListener('kp-preferences-changed',schedule);window.addEventListener('chart-saved',schedule);}
window.KPTableKarkatva=Object.freeze({refresh});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
