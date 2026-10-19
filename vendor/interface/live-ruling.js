(()=>{'use strict';const $=id=>document.getElementById(id),DAY=86400000,HOUR=3600000,dayLords=['Su','Mo','Ma','Me','Ju','Ve','Sa'],horaOrder=['Sa','Ju','Ma','Su','Ve','Me','Mo'];let current=null,solarCache=new Map();
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function validateLocation(raw){const p={place:String(raw.place||'Consultation place'),latitude:Number(raw.latitude),longitude:Number(raw.longitude),timezone:Number(raw.timezone)};if(!Number.isFinite(p.latitude)||Math.abs(p.latitude)>=89||!Number.isFinite(p.longitude)||Math.abs(p.longitude)>180||!Number.isFinite(p.timezone)||Math.abs(p.timezone)>14||[raw.latitude,raw.longitude,raw.timezone].some(v=>v===null||String(v).trim()===''))throw Error('Set valid consultation coordinates and UTC offset in Settings.');return p;}
function solarDay(instant,location){
 const local=new Date(instant.getTime()+location.timezone*HOUR),date=local.toISOString().slice(0,10),key=[date,location.latitude,location.longitude,location.timezone].join('|');
 if(!solarCache.has(key)){
  const midnight=Date.parse(date+'T00:00:00Z')-location.timezone*HOUR,observer=new Astronomy.Observer(location.latitude,location.longitude,0);
  const event=(direction,start)=>Astronomy.SearchRiseSet(Astronomy.Body.Sun,observer,direction,new Date(start),1)?.date.getTime()??null;
  const rise=event(1,midnight),previous=event(1,midnight-DAY),next=event(1,midnight+DAY);
  const between=(v,a,b)=>Number.isFinite(v)&&a<=v&&v<b;
  const today=between(rise,midnight,midnight+DAY)?rise:null,prior=between(previous,midnight-DAY,midnight)?previous:null,future=between(next,midnight+DAY,midnight+2*DAY)?next:null;
  solarCache.set(key,{today,prior,future,event});if(solarCache.size>4)solarCache.delete(solarCache.keys().next().value);
 }
 const cached=solarCache.get(key),now=instant.getTime(),start=cached.today!==null&&now>=cached.today?cached.today:cached.prior,end=start===cached.today?cached.future:cached.today;
 if(start===null||end===null||!(start<=now&&now<end))return {dayLord:null,hourLord:null,reason:'Day/hour lords unavailable: no complete sunrise cycle at this location.'};
 const set=cached.event(-1,start+1000);if(set===null||!(start<set&&set<end))return {dayLord:null,hourLord:null,reason:'Day/hour lords unavailable: no sunset inside this sunrise cycle.'};
 const weekday=new Date(start+location.timezone*HOUR).getUTCDay(),dayLord=dayLords[weekday],isDay=now<set,lower=isDay?start:set,upper=isDay?set:end,part=Math.min(11,Math.floor((now-lower)*12/(upper-lower))),hourIndex=(isDay?0:12)+part,hourLord=horaOrder[(horaOrder.indexOf(dayLord)+hourIndex)%7];
 return {dayLord,hourLord,weekday,hourNumber:hourIndex+1,phase:isDay?'Day':'Night',sunrise:new Date(start).toISOString(),sunset:new Date(set).toISOString(),nextSunrise:new Date(end).toISOString(),hourStart:new Date(lower+(upper-lower)*part/12).toISOString(),hourEnd:new Date(lower+(upper-lower)*(part+1)/12).toISOString(),reason:''};
}
function calculate(value=new Date(),raw=KPDefaultLocation.get(),options={}){
 const date=KPEphemeris.dateValue(value),location=validateLocation(raw),longitudes=KPEphemeris.positions(date),asc=KPEphemeris.ascendant(date,location.latitude,location.longitude);
 const points=[{id:'As',label:'Ascendant',...KPDisplay.longitudeDetails(asc*3600)},{id:'Mo',label:'Moon',...KPDisplay.longitudeDetails(longitudes.Mo*3600)}],solar=solarDay(date,location);
 const sources=[['Ascendant sign',points[0].sgl],['Ascendant star',points[0].stl],['Moon sign',points[1].sgl],['Moon star',points[1].stl],['Day lord',solar.dayLord]];
 const prefs=options.preferences===false?{}:window.KPPreferences?.get()||{};const civil=new Date(date.getTime()+location.timezone*HOUR);if(prefs.rpDayFromSunrise===false)solar.dayLord=dayLords[civil.getUTCDay()];if(prefs.rpHoraFromSunrise===false)solar.hourLord=horaOrder[(horaOrder.indexOf(dayLords[civil.getUTCDay()])+civil.getUTCHours())%7];
 const rulers=[...new Set([...sources.map(([,id])=>id),...points.flatMap(p=>[p.sl,p.ssl]),solar.hourLord].filter(Boolean))],retrograde={};
 const before=new Date(date.getTime()-60000),after=new Date(date.getTime()+60000);
 for(const id of KPDisplay.ids){const delta=KPEphemeris.normalize(KPEphemeris.longitude(after,id)-KPEphemeris.longitude(before,id)+180)-180;retrograde[id]=delta<0;}
 const chains=Object.fromEntries(KPDisplay.ids.map(id=>[id,KPDisplay.longitudeDetails(longitudes[id]*3600)]));
 const isRetro=id=>!['Ra','Ke'].includes(id)&&!!retrograde[id];
 const eligible=id=>{const c=chains[id];return (!isRetro(id)||prefs.rpIncludeRetrograde!==false)&&!(prefs.rpExcludeRetroStar&&isRetro(c.stl))&&!(prefs.rpExcludeRetroSub&&isRetro(c.sl))&&!(prefs.rpExcludeRetroBoth&&isRetro(c.stl)&&isRetro(c.sl));};
 const steps={Su:[7],Mo:[7],Ma:[4,7,8],Me:[7],Ju:[5,7,9],Ve:[7],Sa:[3,7,10],Ra:[5,7,9],Ke:prefs.ketuAspects?[5,7,9]:[]};
 const aspects=(a,b)=>steps[a].includes((Math.floor(longitudes[b]/30)-Math.floor(longitudes[a]/30)+12)%12+1);
 const nodes=['Ra','Ke'].map(id=>({id,aspected:KPDisplay.ids.filter(q=>q!==id&&aspects(q,id)),aspecting:KPDisplay.ids.filter(q=>q!==id&&aspects(id,q)),conjunction:KPDisplay.ids.filter(q=>q!==id&&Math.min(KPEphemeris.normalize(longitudes[q]-longitudes[id]),KPEphemeris.normalize(longitudes[id]-longitudes[q]))<=Number(prefs.conjunctionOrb??3))}));
 return {ready:true,utc:date.toISOString(),local:new Date(date.getTime()+location.timezone*HOUR).toISOString().slice(0,19),location,points,...solar,retrograde,nodes,excludedRulers:KPDisplay.ids.filter(id=>!eligible(id)),rulingPlanets:[...new Set(sources.map(([,id])=>id).filter(Boolean))].filter(eligible),sources:sources.filter(([,id])=>id&&eligible(id)).map(([source,planet])=>({source,planet})),ayanamsha:KPEphemeris.ayanamsha(date),convention:KPEphemeris.convention()};
}
function render(data){
 const root=$('kp-live-ruling');if(!root)return;root.dataset.ready=String(data.ready);root.dataset.utc=data.utc||'';
 const put=(id,text)=>{const node=$(id);if(node&&node.textContent!==text)node.textContent=text;};
 if(!data.ready){put('live-rp-clock','Ruling Planets');put('live-rp-summary',data.reason||'Calculation unavailable');put('live-rp-extra','');put('live-rp-time','—');put('live-rp-place','Check consultation location in Settings');$('live-rp-rows').innerHTML='';put('live-rp-evidence',data.reason||'');return;}
 const lord=id=>id?(data.excludedRulers.includes(id)?'—':id+(data.retrograde[id]&&!['Ra','Ke'].includes(id)?' R':'')):'—',a=data.points[0],m=data.points[1],date=data.local.slice(0,10).split('-').reverse().join('/'),offset='UTC'+(data.location.timezone>=0?'+':'')+data.location.timezone;
 put('live-rp-time',data.local.slice(11,19));put('live-rp-clock',date+' '+data.local.slice(11,19)+' · '+offset);put('live-rp-place',data.location.place);
 put('live-rp-summary','Asc '+[a.sgl,a.stl,a.sl].map(lord).join(' / ')+' · Moon '+[m.sgl,m.stl,m.sl].map(lord).join(' / '));
 put('live-rp-extra','Day '+lord(data.dayLord)+' · Hour '+lord(data.hourLord));
 const html=data.points.map(p=>'<tr><th scope="row">'+esc(p.label)+'</th><td>'+esc(p.signCode+' '+p.degree)+'</td>'+[p.sgl,p.stl,p.sl,p.ssl].map(id=>'<td>'+esc(lord(id))+'</td>').join('')+'</tr>').join('');if($('live-rp-rows').innerHTML!==html)$('live-rp-rows').innerHTML=html;
 let nodeBox=$('live-rp-nodes');if(!nodeBox){nodeBox=document.createElement('div');nodeBox.id='live-rp-nodes';$('live-rp-rows').closest('table').after(nodeBox);}const p=KPPreferences.get(),cols=[['aspected','rpNodeAspected',p.language==='marathi'?'राहू-केतूवरील दृष्टी':'Node aspected by'],['aspecting','rpNodeAspecting',p.language==='marathi'?'राहू-केतूची दृष्टी':'Node aspecting'],['conjunction','rpNodeConjunction',p.language==='marathi'?'राहू-केतू युती':'Node conjunction']].filter(c=>p[c[1]]!==false);nodeBox.innerHTML=cols.length?'<table><thead><tr><th>Node</th>'+cols.map(c=>'<th>'+c[2]+'</th>').join('')+'</tr></thead><tbody>'+data.nodes.map(n=>'<tr><th>'+n.id+'</th>'+cols.map(c=>'<td>'+n[c[0]].map(lord).join(', ')+'</td>').join('')+'</tr>').join('')+'</tbody></table>':'';
 const local=stamp=>new Date(Date.parse(stamp)+data.location.timezone*HOUR).toISOString().slice(11,19);
 put('live-rp-evidence',data.reason||data.phase+' hora '+data.hourNumber+' · '+local(data.hourStart)+' – '+local(data.hourEnd)+' · Sunrise '+local(data.sunrise)+' · Sunset '+local(data.sunset));
 put('live-rp-location',data.location.latitude.toFixed(5)+'°, '+data.location.longitude.toFixed(5)+'° · '+offset);
 put('live-rp-convention','Ruling planets: '+data.rulingPlanets.map(lord).join(', ')+' · '+data.convention+' · Day: '+(KPPreferences.get().rpDayFromSunrise?'sunrise':'civil midnight')+'; hora: '+(KPPreferences.get().rpHoraFromSunrise?'12 unequal hours each day/night':'equal hours from civil midnight')+'. R = retrograde.');
}
function refresh(){try{current=calculate();}catch(e){current={ready:false,reason:e.message,utc:new Date().toISOString()};}render(current);return current;}
function packet(){refresh();const text={};for(const id of ['live-rp-time','live-rp-clock','live-rp-place','live-rp-summary','live-rp-extra','live-rp-evidence','live-rp-location','live-rp-convention'])text[id]=$(id)?.textContent||'';return {data:current,text,rows:$('live-rp-rows')?.innerHTML||''};}
function init(){refresh();$('live-rp-settings').addEventListener('click',()=>{$('kp-live-ruling').open=false;$('quick-astrosettings')?.click();const panel=$('setting-astroPlace')?.closest('[role="tabpanel"]');if(panel){document.querySelector('[aria-controls="'+panel.id+'"]')?.click();} $('setting-astroPlace')?.focus();});
 let lastRefresh=Date.now();setInterval(()=>{const interval=Number(window.KPPreferences?.get().rpRefreshSeconds||1)*1000;if(!window.KPProtectedWorker&&!document.hidden&&Date.now()-lastRefresh>=interval){lastRefresh=Date.now();refresh();}},1000);document.addEventListener('visibilitychange',()=>{if(!document.hidden&&!window.KPProtectedWorker)refresh();});window.addEventListener('kp-preferences-changed',refresh);window.addEventListener('chart-saved',refresh);
}
window.KPLiveRuling=Object.freeze({calculate,refresh,getData:()=>current,packet});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
