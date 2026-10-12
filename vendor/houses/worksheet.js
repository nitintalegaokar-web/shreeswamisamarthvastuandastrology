/* Automatic Bhavsadhan uses the supplied tables; manual worksheets remain under ADM. */
(()=>{'use strict';
const $=id=>document.getElementById(id),value=id=>String($(id)?.value||'').trim(),H=[10,11,12,1,2,3],SIGNS=['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तुळ','वृश्चिक','धनु','मकर','कुंभ','मीन'];
const norm=x=>((x%360)+360)%360,delta=(a,b)=>norm(b-a+180)-180,table=KPHouseTable.create(JSON.parse($('kp-uploaded-house-data').textContent));let current=null,key='',timer;
const mode=()=>value('r5-house-source')||'automatic',enabled=()=>mode()!=='manual'&&value('chart-kind')!=='horary';
const set=(id,text)=>{if($(id))$(id).value=String(text??'');},copy=x=>x?JSON.parse(JSON.stringify(x)):null;
function seconds(text,maximum){const m=/^(\d{1,3}):([0-5]\d):([0-5]\d)$/.exec(text);if(!m)throw Error('Enter valid sidereal time and ayanamsha.');const n=Number(m[1])*3600+Number(m[2])*60+Number(m[3]);if(n>maximum)throw Error('Sidereal time or ayanamsha is outside its range.');return n;}
function dms(degrees){const n=Math.round(degrees*3600);return Math.floor(n/3600)+':'+String(Math.floor(n%3600/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');}
function tableValue(h,degrees){if(h!==1)return String(Math.round(norm(degrees))%360);const minutes=Math.round(norm(degrees)*60)%21600;return Math.floor(minutes/60)+':'+String(minutes%60).padStart(2,'0');}
const tr=text=>window.KPLanguage?.translate(text)||text;
function selectLatitude(latitude){
 if(typeof latitude!=='number'||!Number.isFinite(latitude)||latitude<0||latitude>90)throw Error('Use a valid northern latitude for the Raphael table.');
 const degrees=Math.floor(latitude);return degrees+(latitude-degrees>0.5?1:0);
}
function lookup(latitude,st,ayan=0,columns='printed'){
 const tableLatitude=selectLatitude(latitude);
 return {...table.lookup(tableLatitude,st,ayan,columns),latitude,tableLatitude,latitudeRule:'minutes-half-down'};
}
function sourceRows(data){
 const b=data?.brackets,automatic=enabled(),printed=automatic&&!!b,mr=window.KPPreferences?.get().language==='marathi';
 const extra=$('r5-source-latitude-details');if(extra)extra.hidden=!printed||b.latitudeLow===b.latitudeHigh;
 const note=$('r5-source-latitude-note');if(note){note.hidden=!printed;note.textContent=printed?(mr?'Excel साठी अक्षांश: '+data.tableLatitude+'° उ. (जन्मस्थळ: '+data.latitude.toFixed(5)+'° उ.). ३०′ पर्यंत चालू अंश; ३०′ पेक्षा जास्त असल्यास पुढील अंश.':'Excel table latitude: '+data.tableLatitude+'° N (birthplace: '+data.latitude.toFixed(5)+'° N). Up to 30′: current degree; above 30′: next degree.'):'';}
 for(const field of ['large','small','small2','diff3']){
  const cell=$('r5_'+field+'_10')?.closest('tr')?.firstElementChild;if(!cell)continue;
  if(!cell.dataset.originalSourceLabel)cell.dataset.originalSourceLabel=cell.textContent;
  cell.dataset.noLocalize='true';
  if(!automatic){cell.textContent=cell.dataset.originalSourceLabel;continue;}
  const name=field==='large'?(mr?'मो. सां. वेळ':'Larger ST'):field==='small'?(mr?'छो. सां. वेळ':'Smaller ST'):field==='small2'?(mr?'छोटी सां. वेळ · अं:मि:से':'Smaller ST · D:M:S'):(mr?'भाव फरक क्र. ३':'House difference 3');
  cell.textContent=name+(printed&&['large','small'].includes(field)?' · '+b.latitudeLow+'° '+(mr?'उ.':'N'):'');
 }
 if(!printed)return;
 for(const [field,corner,time] of [['small',2,b.timeLow],['large',3,b.timeHigh]]){
  const label=$('r5-source-high-'+field+'-label');if(label)label.textContent=b.latitudeHigh+'° '+(mr?'उ.':'N')+' · ST '+dms(time/3600);
  for(const [i,h] of H.entries()){const n=$('r5-source-high-'+field+'-'+h);if(n)n.textContent=tableValue(h,b.corners[corner][i]);}
 }
}
function status(data,error){const n=$('r5-house-status');if(!n)return;n.dataset.ready=String(!!data?.ready);n.textContent=error?tr('House calculation unavailable')+': '+tr(error):data?.source==='horary'?tr('Numbered KP Horary retains its exact Ascendant.'):!data?tr('Manual house-table entry.'):tr(data.source==='uploaded'?'Uploaded house tables':'Calculated Placidus fallback')+' · '+tr('Latitude')+' '+data.latitude.toFixed(5)+'°'+(data.tableLatitude!==undefined?' → '+tr('Raphael table latitude')+' '+data.tableLatitude+'° N':'')+' · ST '+dms(data.siderealSeconds/3600)+(data.brackets?' · '+dms(data.brackets.timeLow/3600)+' → '+dms(data.brackets.timeHigh/3600):'');}
function fromSidereal(moment,st,ayan,computed=false){
 if(!computed&&moment.latitude>=0&&selectLatitude(moment.latitude)<=60)return lookup(moment.latitude,st,ayan,'printed');
 const orientation=norm(st/240-Astronomy.SiderealTime(moment.date)*15+180)-180,houses=KPTransitHouses.calculate(moment.date,moment.latitude,orientation),dateAyan=KPEphemeris.ayanamsha(moment.date),tropicalCusps=houses.cusps.map(x=>norm(x+dateAyan));
 return {...houses,ready:true,source:'computed',latitude:moment.latitude,siderealSeconds:st,ayanamsha:ayan,tropicalCusps,cusps:tropicalCusps.map(x=>norm(x-ayan))};
}
function fromMoment(moment){const st=norm(Astronomy.SiderealTime(moment.date)*15+moment.longitude)*240;return fromSidereal(moment,st,KPEphemeris.ayanamsha(moment.date),mode()==='computed');}
function nativeSidereal(moment){
 if(value('st-ephemeris-source')!=='automatic')return seconds(value('birthPlaceSiderealTime'),86400);
 const reference=window.KPWorksheetEphemeris?.getSidereal();
 if(!reference?.ready||!Number.isFinite(reference.hours)||!Number.isFinite(reference.offset))throw Error('Automatic sidereal reference is unavailable.');
 const anchor=new Date(reference.utc);if(!Number.isFinite(anchor.getTime()))throw Error('Automatic sidereal reference date is invalid.');
 // Preserve the selected ephemeris ST (including the supplied +1 second).
 // Advance it by the actual sidereal rotation, then replace the standard
 // meridian with the native longitude. Do not round legacy LMT corrections.
 const rotation=(Astronomy.SiderealTime(moment.date)-Astronomy.SiderealTime(anchor))*15;
 return norm(reference.hours*15+rotation+moment.longitude-reference.offset*15)*240;
}
function write(data){
 const b=data.brackets;
 sourceRows(data);
 if(value('instant-prashna')==='1'||value('st-ephemeris-source')==='automatic')set('birthPlaceSiderealTime',dms(data.siderealSeconds/3600));
 set('stSmallTime',b?dms(b.timeLow/3600):dms(data.siderealSeconds/3600));set('stLargeTime',b?dms(b.timeHigh/3600):dms(data.siderealSeconds/3600));
 window.updateSampattikTimeDifferences?.();
 for(const [i,h] of H.entries()){
  const tropical=data.tropicalCusps[h-1],absolute=Math.round(data.cusps[h-1]*3600)%1296000,sign=Math.floor(absolute/108000),degree=absolute/3600;
  const difference=b?delta(b.small[i],b.large[i]):0,ishta=b?difference*b.timeFraction:0;
  // Source rows must be actual workbook entries, not fractional latitude blends.
  // The selected whole latitude is fixed; retain full-precision ST interpolation.
  for(const [field,n] of [['small',b?b.corners[0][i]:tropical],['small2',b?b.small[i]:tropical],['large',b?b.corners[1][i]:tropical],['diff3',difference],['ishta',ishta],['smallplus',tropical],['geoayan',data.ayanamsha],['nirayan',degree],['minus',sign*30],['bhava',degree-sign*30]])set('r5_'+field+'_'+h,['small','large'].includes(field)?tableValue(h,n):dms(n));
  set('r5_rashi_'+h,SIGNS[sign]);set('r5_opposite_'+h,SIGNS[(sign+6)%12]);
  set('r5_calc_diff1_'+h,value('stDiff1'));set('r5_calc_diff2_'+h,value('stDiff2'));set('r5_calc_diff3_'+h,dms(difference));set('r5_calc_ishta_'+h,(ishta*60).toFixed(6).replace(/\.?0+$/,''));
 }
}
function clear(){sourceRows(null);for(const h of H)for(const field of ['large','small','diff3','small2','ishta','smallplus','geoayan','nirayan','minus','bhava','rashi','opposite','calc_diff1','calc_diff2','calc_diff3','calc_ishta'])set('r5_'+field+'_'+h,'');for(const id of ['stLargeTime','stSmallTime'])set(id,'');window.updateSampattikTimeDifferences?.();}
function apply(){
 if(!enabled()){current=null;key='';sourceRows(null);status(value('chart-kind')==='horary'?{source:'horary',ready:true}:null);return null;}
 try{
  const moment=KPHorary.nativeMoment(),instant=value('instant-prashna')==='1',st=instant?norm(Astronomy.SiderealTime(moment.date)*15+moment.longitude)*240:nativeSidereal(moment),ayan=instant||window.KPAnnualAyanamsha?.enabled()?KPEphemeris.ayanamsha(moment.date):seconds(value('ayanValue'),1295999)/3600;
  const signature=[mode(),moment.date.toISOString(),moment.latitude,st,ayan].join('|');
  if(signature!==key){current=fromSidereal(moment,st,ayan,mode()==='computed');key=signature;}
  write(current);status(current);return copy(current);
 }catch(error){current=null;key='';clear();status(null,error.message);return null;}
}
function init(){
 const controls=document.createElement('div');controls.className='house-table-controls no-print';controls.innerHTML='<label>Bhavsadhan source <select id="r5-house-source"><option value="automatic">Uploaded tables · automatic</option><option value="computed">Date-specific Placidus</option><option value="manual">Manual table entry</option></select></label><small id="r5-house-status" role="status" data-no-localize></small>';$('raphael5').querySelector('.raphael5-sheet').prepend(controls);const units=document.createElement('small');units.className='house-table-units';units.textContent='Table units: X, XI, XII, II, III · whole degrees; Ascendant · D:M. Interpolation and final cusps · D:M:S.';controls.append(units);for(const h of H)for(const field of ['small','large']){const n=$('r5_'+field+'_'+h);if(n){n.dataset.houseTableUnit=h===1?'DM':'degrees';n.title=h===1?'Ascendant · degrees:minutes':'House '+h+' · whole degrees';}}
 const note=document.createElement('small');note.id='r5-source-latitude-note';note.dataset.noLocalize='true';controls.append(note);
 const extra=document.createElement('details');extra.id='r5-source-latitude-details';extra.className='r5-source-latitude-details';extra.hidden=true;extra.innerHTML='<summary>Additional latitude · Excel source rows</summary><table><thead><tr><th>Latitude / ST</th>'+H.map(h=>'<th>'+h+' · '+(h===1?'D:M':'°')+'</th>').join('')+'</tr></thead><tbody>'+['large','small'].map(field=>'<tr><th id="r5-source-high-'+field+'-label" data-no-localize></th>'+H.map(h=>'<td><output id="r5-source-high-'+field+'-'+h+'" data-no-localize></output></td>').join('')+'</tr>').join('')+'</tbody></table>';$('raphael5').querySelector('.raphael5-table').after(extra);
 const previous=window.updateRaphaelTable5;window.updateRaphaelTable5=function(...args){if(enabled())return apply();const result=previous.apply(this,args);apply();return result;};
 const sync=window.syncKPWorksheetPositions;window.syncKPWorksheetPositions=function(...args){if(enabled())apply();return sync.apply(this,args);};
 const manualEdit=e=>{if(enabled()&&(/^(r5_(large|small)_(10|11|12|1|2|3))$/.test(e.target?.id||'')||['stLargeTime','stSmallTime'].includes(e.target?.id)))set('r5-house-source','manual');};
 document.addEventListener('input',manualEdit,true);document.addEventListener('change',manualEdit,true);
 const changed=e=>{const id=e.target?.id||'';if(id==='r5-house-source'||['birthPlaceSiderealTime','lat','lon','ayanValue','kp-ayanamsha-source'].includes(id)){key='';clearTimeout(timer);timer=setTimeout(()=>window.calculateAll?.(),110);}};
 document.addEventListener('change',changed);document.addEventListener('input',changed);window.addEventListener('kp-preferences-changed',()=>{sourceRows(current);status(current);});window.KPLanguage?.localize(controls);window.calculateAll?.();
}
window.KPBhavSadhan=Object.freeze({enabled,apply,fromMoment,lookup,selectLatitude,metadata:table.metadata,getData:()=>copy(current)});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();
})();
