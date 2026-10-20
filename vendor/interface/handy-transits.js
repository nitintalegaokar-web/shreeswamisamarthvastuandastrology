/* Compact transit workflow. Delegate every date, track and scan to approved APIs. */
(()=>{'use strict';
const $=id=>document.getElementById(id),MODES=['event','dasha','sun'];let queued=false,lastRows='',matches=0;
const mr=()=>window.KPPreferences?.get().language==='marathi';
const text=(en,m)=>mr()?m:en;
function label(id){return $(id)?.closest('label')||$(id)?.parentElement;}
function dispatch(id){$(id).dispatchEvent(new Event('change',{bubbles:true}));}
function setText(node,value){if(node&&node.textContent!==value)node.textContent=value;}
function mode(value){if(!MODES.includes(value))return; $('tr-mode').value=value;dispatch('tr-mode');window.KPTransitWorkspace?.current();schedule();}
function filterEvents(){
 const query=document.querySelector('[data-tr-event-filter]')?.value.trim().toLocaleLowerCase()||'',select=$('tr-event');
 const options=[...select.options];let first=null;matches=0;
 for(const option of options){const visible=!query||option.textContent.toLocaleLowerCase().includes(query);option.hidden=!visible;option.disabled=!visible;if(visible){matches++;first||=option;}}
 if(first&&select.selectedOptions[0]?.disabled){select.value=first.value;dispatch('tr-event');}
 setText($('tr-event-match-count'),query?text(matches+' events match','जुळणाऱ्या घटना: '+matches):'');schedule();
}
function localTime(iso){const date=new Date(Date.parse(iso)+Number($('tr-timezone').value)*60000),stamp=date.toISOString();return KPPreferences.formatDate(stamp.slice(0,10))+' '+stamp.slice(11,19);}
function formatRows(rows){
 const signature=JSON.stringify([rows,$('tr-timezone').value,KPPreferences.get().dateFormat]);if(signature===lastRows)return;lastRows=signature;
 const nodes=[...$('tr-result-rows').querySelectorAll('tr[data-track]')];
 rows.forEach((row,i)=>{const node=nodes[i];if(!node)return;node.dataset.planet=row.planet;
  for(const [column,key,clipped] of [[2,'start','startClipped'],[3,'end','endClipped']]){const cell=node.children[column];cell.replaceChildren(document.createTextNode(localTime(row[key])));if(row[clipped]){const note=document.createElement('small');note.textContent=text('range limit','निवडलेल्या कालावधीची सीमा');cell.append(note);}}
 });
}
function update(){
 const current=$('tr-mode').value,event=current==='event',dasha=current==='dasha';
 for(const button of document.querySelectorAll('[data-tr-search-mode]')){const active=button.dataset.trSearchMode===current;button.setAttribute('aria-pressed',String(active));setText(button,currentLabel(button.dataset.trSearchMode));}
 $('transit').querySelector('.tr-simple-choice').hidden=false;$('tr-handy-event-rules').hidden=false;label('tr-match').hidden=!event;$('tr-handy-planets').hidden=!event;$('tr-handy-dba-rules').hidden=event;$('tr-mutual-controls').hidden=!dasha;
 setText($('tr-handy-title'),text('Find transit dates','गोचर दिनांक शोधा'));
 setText($('tr-event-filter-label'),text('Search event','घटना शोधा'));
 setText($('tr-handy-csv'),text('Save dates · CSV','दिनांक जतन करा · CSV'));
 setText($('tr-all-planets'),text('All planets','सर्व ग्रह'));setText($('tr-no-planets'),text('Clear','निवड काढा'));
 setText($('tr-handbook-note'),event?text('Entry / exit times satisfy the selected transit rule. Use Advanced rules for natal promise and DBA support.','प्रवेश / निर्गमन वेळा निवडलेल्या गोचर नियमाशी जुळतात. जन्मकुंडलीचे वचन व दशा समर्थनासाठी अतिरिक्त नियम वापरा.'):dasha?text('All six MD / AD / PD directions, using the selected natal or lord-ruled sectors.','निवडलेल्या जन्मस्थान किंवा स्वामीच्या क्षेत्रातून MD / AD / PD च्या सहाही दिशा.'):text('Sun through MD and AD: MD sign + AD star, and AD sign + MD star.','MD व AD मधून सूर्य: MD राशी + AD नक्षत्र आणि AD राशी + MD नक्षत्र.'));
 const running=$('tr-status').dataset.state==='running',rows=(window.KPTransitWorkspace?.getResults()||KPTransit.getResults()),zero=/No matching intervals|जुळणारे गोचर नाही/.test($('tr-result-rows').textContent),complete=rows.length>0||zero;
 const table=$('transit').querySelector('.tr-result-mount');table.hidden=!complete;formatRows(rows);
 $('tr-handy-csv').disabled=!rows.length;$('transit-preview').disabled=running||!complete;
 setText($('tr-run'),running?text('Searching…','शोध सुरू…'):text('Find transit dates','गोचर दिनांक शोधा'));
 if(event&&!matches&&!running)$('tr-run').disabled=true;
 $('tr-event-match-count').classList.toggle('is-empty',Boolean(document.querySelector('[data-tr-event-filter]').value)&&!matches);
 for(const card of $('tr-current-periods').children){const span=card.querySelector('span');if(span)card.title=span.textContent;}
}
function currentLabel(value){return value==='event'?text('1 · Event significators','१ · घटनेचे कार्येश'):value==='dasha'?text('2 · DBA through each other','२ · परस्पर दशा गोचर'):text('3 · Sun through DBA','३ · दशेतून सूर्य गोचर');}
function schedule(){if(queued)return;queued=true;queueMicrotask(()=>{queued=false;update();});}
function csv(){
 const rows=(window.KPTransitWorkspace?.getResults()||KPTransit.getResults());if(!rows.length)return;
 const quote=value=>'"'+String(value).replace(/"/g,'""')+'"';
 const columns=['Search mode','Event','Planet','Transit condition','MD','AD','PD','Chain','LSRD rank','RP query UTC','Entry UTC','Exit UTC','Entry local','Exit local','UTC offset minutes'];
 const search=$('tr-mode').selectedOptions[0].textContent,event=$('tr-event').selectedOptions[0]?.textContent||'';
 const body=[columns,...rows.map(r=>[search,event,r.planet,r.label,r.DBA?.MD||'',r.DBA?.AD||'',r.DBA?.PD||'',r.chainKind||'',r.rulingRank||'',r.rulingQueryUTC||'',r.start,r.end,localTime(r.start),localTime(r.end),$('tr-timezone').value])].map(r=>r.map(quote).join(',')).join('\r\n');
 const url=URL.createObjectURL(new Blob(['\ufeff'+body],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='KP-MASTER-Transit-dates.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function init(){
 const section=$('transit'),card=section?.querySelector('.tr-card');if(!card||!window.KPTransitSelection)return;
 card.classList.add('tr-handy');section.classList.add('tr-handy-section');
 const header=card.querySelector('.tr-compact-header'),heading=header.querySelector('h2');heading.id='tr-handy-title';
 const save=document.createElement('button');save.id='tr-handy-csv';save.type='button';save.disabled=true;save.addEventListener('click',csv);header.insertBefore(save,$('transit-preview'));
 const modes=document.createElement('div');modes.className='tr-handy-modes';modes.setAttribute('role','group');modes.setAttribute('aria-label','Transit search type');
 for(const value of MODES){const button=document.createElement('button');button.type='button';button.dataset.trSearchMode=value;button.addEventListener('click',()=>mode(value));modes.append(button);}
 header.after(modes);modes.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key)||!event.target.dataset.trSearchMode)return;event.preventDefault();const value=MODES[(MODES.indexOf(event.target.dataset.trSearchMode)+(event.key==='ArrowRight'?1:2))%3];mode(value);modes.querySelector('[data-tr-search-mode="'+value+'"]').focus();});
 const originalMode=$('tr-mode'),modeLabel=label('tr-mode');$('tr-calculation-fields').append(originalMode);modeLabel.hidden=true;
 const query=document.createElement('label');query.className='tr-event-query';query.innerHTML='<span id="tr-event-filter-label"></span><input type="search" data-tr-event-filter aria-label="Search event" placeholder="Type event name…"><small id="tr-event-match-count" aria-live="polite"></small>';
 $('tr-simple-event-choice').before(query);query.querySelector('input').addEventListener('input',filterEvents);
 const datebar=document.createElement('div');datebar.className='tr-handy-dates';datebar.id='tr-handy-dates';
 modes.after(datebar);for(const id of ['tr-date-range-source','tr-search-date-start','tr-search-date-end','tr-timezone'])datebar.append(label(id));
 const dba=$('tr-date-dba-selection');dba.open=true;dba.querySelector('.tr-selection-grid').append(...datebar.children);dba.querySelector('.tr-selection-note')?.remove();
 const actions=card.querySelector('.tr-actions');actions.append($('tr-use-current-dba'));modes.after(card.querySelector('.tr-simple-choice'));
 const eventRules=document.createElement('div');eventRules.id='tr-handy-event-rules';eventRules.className='tr-handy-rules';for(const id of ['tr-houses','tr-significator-method','tr-match'])eventRules.append(label(id));dba.after(eventRules);
 const dbaRules=document.createElement('div');dbaRules.id='tr-handy-dba-rules';dbaRules.className='tr-handy-dba-rules';dbaRules.append(label('tr-zone'),$('tr-mutual-controls'));eventRules.after(dbaRules);
 const planets=$('tr-planet-options').closest('fieldset');planets.id='tr-handy-planets';const tools=document.createElement('div');tools.className='tr-handy-planet-tools';
 for(const [id,checked] of [['tr-all-planets',true],['tr-no-planets',false]]){const b=document.createElement('button');b.id=id;b.type='button';b.addEventListener('click',()=>{const boxes=[...$('tr-planet-options').querySelectorAll('input')];boxes.forEach(n=>n.checked=checked);if(boxes.length)boxes[0].dispatchEvent(new Event('change',{bubbles:true}));});tools.append(b);}planets.append(tools);dbaRules.after(planets);
 const advanced=$('tr-rule-options');advanced.querySelector('summary').textContent=text('Advanced rules / significator evidence','अतिरिक्त नियम / कार्येश माहिती');advanced.querySelector('.tr-compact-options').prepend($('tr-search-scope'));advanced.open=false;
 $('tr-event-panel').querySelector('label[for="tr-event"]')?.parentElement.remove();
 const note=document.createElement('p');note.id='tr-handbook-note';note.className='tr-handy-note';actions.after(note);$('tr-simple-rule-note').hidden=true;
 const observer=new MutationObserver(schedule);observer.observe($('tr-status'),{childList:true,attributes:true,attributeFilter:['data-state']});observer.observe($('tr-result-rows'),{childList:true});observer.observe($('tr-current-periods'),{childList:true});
 new MutationObserver(()=>{filterEvents();schedule();}).observe($('tr-event'),{childList:true,subtree:true});
 section.addEventListener('change',schedule);window.addEventListener('kp-preferences-changed',()=>{lastRows='';schedule();});
 const restore=window.restoreChartData;window.restoreChartData=function(...args){query.querySelector('input').value='';filterEvents();const result=restore.apply(this,args);filterEvents();schedule();return result;};
 filterEvents();schedule();
}
window.KPHandyTransits=Object.freeze({mode,filterEvents,saveDates:csv});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();
})();
