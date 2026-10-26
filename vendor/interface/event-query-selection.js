/* One handbook event/cusp selection shared by Event Promise and its Horary sheet. */
(function(){'use strict';const $=id=>document.getElementById(id);let busy=false;
function sync(source){if(busy||!$('hq-event')||!$('ep-cusp'))return;busy=true;
try{const events=KPHandbook.getCatalogue().events;let cusp=Number($('ep-cusp').value),wanted=source==='hq-event'?$('hq-event').value:$('ep-event').value;const chosen=events.find(e=>String(e.id)===wanted);
 if(source==='hq-cusp')cusp=Number($('hq-cusp').value)||cusp;
 if(source==='ep-category'&&Number($('ep-category').value))cusp=Number($('ep-category').value);
 if(['hq-event','ep-event'].includes(source)&&chosen&&chosen.mainHouses.length&&!chosen.mainHouses.includes(cusp))cusp=chosen.mainHouses[0];
 $('ep-auto-cusp').checked=false;$('ep-cusp').value=String(cusp);$('ep-category').value=String(cusp);if($('hq-cusp'))$('hq-cusp').value=String(cusp);if(['ep-cusp','hq-event','hq-cusp'].includes(source))$('ep-search').value='';
 $('ep-category').dispatchEvent(new Event('change',{bubbles:true}));$('ep-event').querySelector('[value="custom"]')?.remove();
 const options=[...$('ep-event').options];for(const option of options)option.textContent=option.textContent.replace(/^\s*\d+\s*[·.:-]\s*/, '');if(!options.some(o=>o.value===wanted))wanted=options[0]?.value||'';
 $('ep-event').value=wanted;$('hq-event').dataset.catalogue='handbook';$('hq-event').replaceChildren(...options.map(o=>new Option(o.textContent,o.value)));$('hq-event').value=wanted;
 $('ep-event').dispatchEvent(new Event('change',{bubbles:true}));$('ep-cusp').value=String(cusp);KPEventPromise.refresh(true);for(const option of $('ep-event').options)option.textContent=option.textContent.replace(/^\s*\d+\s*[·.:-]\s*/, '');window.KPHoraryResults?.refresh();
}finally{busy=false;}}
document.addEventListener('change',e=>{if(!busy&&['ep-cusp','ep-category','ep-event','ep-search','hq-event','hq-cusp'].includes(e.target.id)){const id=e.target.id;queueMicrotask(()=>sync(id));}});
function init(){if(!$('hq-event')||!$('ep-cusp'))return false;sync('ep-cusp');return true;}
if(!init()){const observer=new MutationObserver(()=>{if(init())observer.disconnect();});observer.observe(document,{childList:true,subtree:true});}
})();
