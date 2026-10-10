/* Read-only native facts; the same snapshot is printed as General Information. */
(()=>{'use strict';
const $=id=>document.getElementById(id),val=id=>$(id)?.value||'—',esc=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SIGNS=['Ar','Ta','Ge','Ca','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi'],ANIMALS=['Horse','Elephant','Sheep','Serpent','Dog','Cat','Rat','Cow','Buffalo','Tiger','Deer','Monkey','Mongoose','Lion'];
const lord=id=>KPDisplay.idByName[val(id)]||val(id),duration=id=>KPPreferences.get().language==='marathi'?val(id):val(id).replace(/वर्ष/g,'years').replace(/महिने/g,'months').replace(/दिवस/g,'days');
function facts(){
 const model=window.currentKPModel;if(!model?.ready)return {ready:false,reason:'Calculate the native kundali first.'};
 try{
  const native=KPVedic.core().native;if(!native)throw Error('Enter valid birth date, time and coordinates.');
  const p=KPSinglePageReport.panchang(native.points.Su*3600,native.points.Mo*3600,val('dob')),moon=KPMatchmaking.score(native.points.Mo,native.points.Mo).boy;
  const clock=utc=>new Date(Date.parse(utc)+native.location.timezone*3600000).toISOString().slice(11,19);
  let sunrise='—',sunset='—';try{const solar=KPLiveRuling.calculate(new Date(native.date),native.location);sunrise=solar.sunrise?clock(solar.sunrise):'—';sunset=solar.sunset?clock(solar.sunset):'—';}catch(_){}
  const kind=$('chart-kind'),gender=$('chart-gender');
  return {ready:true,groups:[
   [['Chart type',kind?.selectedOptions[0]?.textContent||'—'],['Name',val('name')],['Gender',gender?.selectedOptions[0]?.textContent||'—'],['Place',val('birthPlace')],['Longitude',KPClientPresentation.formatCoordinate(native.location.longitude,true)],['Latitude',KPClientPresentation.formatCoordinate(native.location.latitude,false)],['Birth date',KPPreferences.formatDate(val('dob'))],['Weekday',p.weekday],['Birth time',val('birthTime')],['UTC offset',native.location.timezone],['DST correction',val('birth-dst-minutes')+' min'],['Local mean time',val('lmtFinal')],['Sidereal time',val('birthPlaceSiderealTime')],['Ayanamsha',KPDisplay.formatDegree(native.ayanamsha*3600)],['House system','Placidus']],
   [['Ascendant',SIGNS[Math.floor(native.asc/30)]],['Moon sign',p.rashi],['Sun sign',SIGNS[Math.floor(native.points.Su/30)]],['Nakshatra',p.nakshatra],['Pada',p.pada],['Star lord',p.nakLord],['Tithi',p.paksha+' · '+p.tithi],['Yoga',p.yoga],['Karana',p.karana],['Gana',['Deva','Manushya','Rakshasa'][moon.gana]],['Nadi',['Adi','Madhya','Antya'][moon.nadi]],['Yoni',ANIMALS[moon.yoni]],['Varna',({1:'Shudra',2:'Vaishya',3:'Kshatriya',4:'Brahmin'})[moon.varna]],['Vashya',['Quadruped','Human','Water','Forest','Insect'][moon.vashya]]],
   [['Sunrise',sunrise],['Sunset',sunset],['Birth Dasha',lord('mdBirthDasha')],['Remaining birth Dasha',duration('mdBhogyaDuration')],['Birth Bhukti',lord('adBirthLord')],['Remaining birth Bhukti',duration('adBirthBalance')],['Birth Dasha end',val('mdDashaEnd')],['Native UTC',native.date.replace('T',' ').replace('.000Z',' UTC')]]
  ]};
 }catch(e){return {ready:false,reason:e.message};}
}
function snapshot(){const d=facts();return d.ready?'<div class="bi-facts">'+d.groups.map(group=>'<dl>'+group.map(([label,value])=>'<div><dt>'+esc(label)+'</dt><dd'+(['Name','Place','Native UTC','Birth date','Birth time'].includes(label)?' data-no-localize':'')+'>'+esc(value)+'</dd></div>').join('')+'</dl>').join('')+'</div>':'<p>'+esc(d.reason)+'</p>';}
function refresh(){const mount=$('basic-information-data');if(mount){mount.innerHTML=snapshot();KPLanguage?.localize(mount);}}
function init(){const tab=$('basic-information');tab.innerHTML='<article class="bi-window"><header><h2>Basic Information</h2><button id="basic-information-preview" type="button">Preview · Print / Save PDF</button></header><div id="basic-information-data"></div></article>';
 $('basic-information-preview').addEventListener('click',()=>{KPReportPages.selectSections(['vedic-information']);KPSelectedReport.preview();});
 new MutationObserver(()=>{if(tab.classList.contains('active'))refresh();}).observe(tab,{attributes:true,attributeFilter:['class']});
 const status=$('kp-status');if(status)new MutationObserver(()=>{if(tab.classList.contains('active'))refresh();}).observe(status,{childList:true,subtree:true});
 window.addEventListener('kp-preferences-changed',refresh);refresh();renderReport();KPReportPages.refresh();
}
window.KPBasicInformation=Object.freeze({facts,snapshot,refresh});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();
})();
