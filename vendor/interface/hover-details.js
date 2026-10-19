/* A single presentation tooltip. Chart details are public rendered data only. */
(()=>{'use strict';
let tip,timer,target,originalTitles=[],point={x:0,y:0};
const clean=s=>String(s||'').replace(/\s+/g,' ').trim();
const planetNames={Su:'Sun',Mo:'Moon',Ma:'Mars',Me:'Mercury',Ju:'Jupiter',Ve:'Venus',Sa:'Saturn',Ra:'Rahu',Ke:'Ketu'};
const tr=s=>window.KPLanguage?.translate(s)||s;
function hide(){clearTimeout(timer);if(tip){tip.hidden=true;tip.replaceChildren();}for(const [node,value] of originalTitles)if(node.isConnected&&!node.hasAttribute('title'))node.setAttribute('title',value);originalTitles=[];target=null;}
function candidate(node){
 if(!(node instanceof Element)||window.KPPreferences?.get().tooltips===false||node.closest('dialog textarea,.preview-tools,#kp-hover-detail'))return null;
 const cell=node.closest('td,th');if(cell&&clipped(cell))return cell;
 const chart=node.closest('[data-hover-dms]'),reference=node.closest('.kp-planet-reference,[data-planet-ref]');
 if(chart||reference)return chart||reference;
 const heading=node.closest('th[scope=row]');if(heading?.closest('tr[data-house]'))return heading;
 return node.closest('[data-hover-detail],[title],td,th,.v38-name,.v38-degree,.v38-lords,.kp-house-reference,.home-table-cell,.kp-notation-marker');
}
function details(node){
 let entry=node.closest('[data-hover-dms]');
 const id=node.closest('[data-planet-ref]')?.dataset.planetRef;
 const house=node.closest('th[scope=row]')?.closest('tr[data-house]')?.dataset.house||node.dataset.houseRef;
 if(!entry&&(id||house))entry=[...document.querySelectorAll('[data-hover-dms]')].find(n=>id?n.dataset.planet===id:n.dataset.cusp===house);
 if(!entry)return null;
 const d=entry.dataset;
 const name=tr(d.hoverName||''),code=entry.dataset.planet;
 return {name:code&&window.KPPreferences?.get().language!=='marathi'?name+' ('+code+')':name,dms:[tr(d.hoverSign||''),d.hoverDms].filter(Boolean).join(' '),sgl:tr(planetNames[d.hoverSgl]||d.hoverSgl||'—'),stl:tr(planetNames[d.hoverStl]||d.hoverStl||'—'),sbl:tr(planetNames[d.hoverSbl]||d.hoverSbl||'—')};
}
function clipped(node){return [node,...node.querySelectorAll('span,strong,small,div')].some(n=>n.clientWidth>0&&(n.scrollWidth>n.clientWidth+1||n.scrollHeight>n.clientHeight+1));}
function fullCell(node){const clone=node.cloneNode(true),mr={Su:'रवी',Mo:'चंद्र',Ma:'मंगळ',Me:'बुध',Ju:'गुरु',Ve:'शुक्र',Sa:'शनि',Ra:'राहू',Ke:'केतू'};clone.querySelectorAll('[data-planet-ref]').forEach(ref=>{const id=ref.dataset.planetRef;if(planetNames[id])ref.textContent=window.KPPreferences?.get().language==='marathi'?mr[id]:tr(planetNames[id]);});return clean(clone.textContent);}
function information(node){if(!node||!node.getClientRects().length)return '';if(node.matches('td,th')&&clipped(node))return fullCell(node);const structured=details(node);if(structured)return structured;const explicit=clean(node.getAttribute('data-hover-detail')||node.getAttribute('title'));if(explicit)return explicit;const text=clean(node.textContent);return clipped(node)&&text?text:'';}

function render(data){
 const host=target?.closest('dialog[open]')||document.body;if(tip.parentElement!==host)host.append(tip);
 tip.replaceChildren();tip.classList.toggle('kp-hover-chart',typeof data==='object');
 if(typeof data==='string'){tip.textContent=data;return;}
 const heading=document.createElement('strong');heading.className='kp-hover-heading';heading.textContent=data.name;tip.append(heading);
 const rows=[['DMS',data.dms],['SGL',data.sgl],['STL',data.stl],['SBL',data.sbl]];
 for(const [key,value] of rows){const row=document.createElement('div');row.className='kp-hover-row';row.dataset.hoverRow=key;const label=document.createElement('span');label.className='kp-hover-label';label.textContent=window.KPPreferences?.get().language==='marathi'?({DMS:'अंश',SGL:'रा. स्वा.',STL:'न. स्वा.',SBL:'उ. स्वा.'})[key]:key;const text=document.createElement('b');text.textContent=value;row.append(label,text);tip.append(row);}
}
function suppressTitles(node){for(let n=node;n&&n!==document.body;n=n.parentElement)if(n.hasAttribute('title')){originalTitles.push([n,n.getAttribute('title')]);n.removeAttribute('title');}}
function position(){const width=tip.offsetWidth,height=tip.offsetHeight;tip.style.left=Math.max(8,Math.min(innerWidth-width-8,point.x+14))+'px';tip.style.top=Math.max(8,Math.min(innerHeight-height-8,point.y+16))+'px';}
function schedule(node){const data=information(node);if(!data)return;target=node;suppressTitles(node);timer=setTimeout(()=>{if(target!==node||!node.isConnected)return;render(data);tip.hidden=false;position();},180);}
function init(){
 if(document.getElementById('kp-hover-detail'))return;
 tip=document.createElement('div');tip.id='kp-hover-detail';tip.setAttribute('role','tooltip');tip.hidden=true;document.body.append(tip);
 const style=document.createElement('style');style.textContent='#kp-hover-detail{position:fixed;z-index:2147483000;max-width:min(290px,calc(100vw - 24px));padding:7px 10px;font:12px/1.45 Arial,"Nirmala UI",sans-serif;color:#183e47;background:rgba(238,250,247,.98);border:1px solid #84bfb5;border-radius:7px;box-shadow:0 4px 14px #174e4226;pointer-events:none;white-space:normal;overflow-wrap:anywhere}#kp-hover-detail.kp-hover-chart{min-width:210px;padding:0 10px 6px}.kp-hover-heading{display:block;margin:0 -10px 5px;padding:6px 10px;background:#17685f;color:#fff;border-radius:6px 6px 0 0;font-size:12px}.kp-hover-row{display:grid;grid-template-columns:50px 1fr;gap:9px;padding:4px 0;border-bottom:1px solid #cce6df}.kp-hover-row:last-child{border-bottom:0}.kp-hover-label{font-size:10px;font-weight:700;color:#52706e;align-self:center}.kp-hover-row b{font-size:12px;font-weight:600;color:#153d61}#kp-hover-detail[hidden]{display:none!important}body.dark-theme #kp-hover-detail{background:rgba(23,48,57,.98);color:#ecf6f4;border-color:#428a83}body.dark-theme .kp-hover-row{border-color:#315760}body.dark-theme .kp-hover-row b,body.dark-theme .kp-hover-label{color:#d8eeeb}@media print{#kp-hover-detail{display:none!important}}';document.head.append(style);
 document.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;point={x:e.clientX,y:e.clientY};const next=candidate(e.target);if(next===target){if(tip&&!tip.hidden)position();return;}hide();schedule(next);},{passive:true});
 document.addEventListener('pointerout',e=>{if(target&&(!e.relatedTarget||!target.contains(e.relatedTarget)))hide();},{passive:true});
 document.addEventListener('scroll',hide,{passive:true,capture:true});document.addEventListener('pointerdown',hide,{passive:true});window.addEventListener('blur',hide);document.addEventListener('keydown',hide);window.addEventListener('kp-preferences-changed',hide);
}
window.KPHoverDetails=Object.freeze({hide});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();})();
