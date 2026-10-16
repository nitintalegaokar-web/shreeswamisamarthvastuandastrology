/* Keep Event Promise and Horary query controls on one selected cusp. */
(function(){'use strict';
const $=id=>document.getElementById(id);let busy=false;
function sync(source){if(busy||!$('hq-event')||!$('ep-cusp'))return;busy=true;
try{
 const events=KPPrediction.getCatalogue().events,find=id=>events.find(e=>String(e.id)===String(id));
 let cusp=Number($('ep-cusp').value),wanted=$('ep-event').value,query=$('hq-event').value;const handbook=KPHandbook.getCatalogue().events;
 if(source==='ep-category'&&Number($('ep-category').value))cusp=Number($('ep-category').value);
 if(source==='hq-event'){const e=find(query);if(e&&!e.mainHouses.includes(cusp))cusp=e.mainHouses[0];}
 if(source==='ep-event'){const e=handbook.find(e=>String(e.id)===wanted);if(e&&!e.mainHouses.includes(cusp))cusp=e.mainHouses[0];}
 $('ep-auto-cusp').checked=false;$('ep-cusp').value=String(cusp);$('ep-category').value=String(cusp);
 if(source==='ep-cusp')$('ep-search').value='';
 $('ep-category').dispatchEvent(new Event('change',{bubbles:true}));
 const allowed=events.filter(e=>e.mainHouses.includes(cusp));
 if(!handbook.some(e=>String(e.id)===wanted&&e.mainHouses.includes(cusp)))wanted=$('ep-event').value;
 if(!allowed.some(e=>String(e.id)===query))query=allowed.length?String(allowed[0].id):'';
 if([...$('ep-event').options].some(o=>o.value===wanted))$('ep-event').value=wanted;
 $('hq-event').replaceChildren(...allowed.map(e=>new Option(e.id+' · '+(e.event.en||e.event.mr),String(e.id))));$('hq-event').value=query;
 $('ep-cusp').value=String(cusp);$('ep-event').dispatchEvent(new Event('change',{bubbles:true}));
 $('hq-event').value=query;window.KPHoraryResults?.refresh();
}finally{busy=false;}}
document.addEventListener('change',e=>{if(!busy&&['ep-cusp','ep-category','ep-event','hq-event'].includes(e.target.id)){const id=e.target.id;queueMicrotask(()=>sync(id));}});
function init(){if(!$('hq-event')||!$('ep-cusp'))return false;sync('ep-cusp');return true;}
if(!init()){const observer=new MutationObserver(()=>{if(init())observer.disconnect();});observer.observe(document,{childList:true,subtree:true});}
})();
