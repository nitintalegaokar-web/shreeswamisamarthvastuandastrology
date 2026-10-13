/* Optional ephemeris-source adapter.
 *
 * The installed default is an exact delegation layer: every uploaded-KP call
 * returns the original engine's result without reconstruction or rounding.
 * Swiss Krishnamurti behavior is entered only after setSource('swiss-kp').
 */
(()=>{'use strict';
if(window.KPEphemerisSources)return;
const SOURCES=Object.freeze(['uploaded-kp','swiss-kp']),PLANETS=Object.freeze(['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke']);
const $=id=>document.getElementById(id),norm=value=>((Number(value)%360)+360)%360;
let source='uploaded-kp',baseEphemeris=null,baseAnnual=null,baseUploaded=null,installed=false;
const swiss=()=>window.KPSwissKrishnamurti,isSwiss=()=>source==='swiss-kp';
function prepareSwissWorksheet(){
 try{
  const text=$('dob')?.value||'',date=swiss().dateValue(text+'T00:00:00Z');if(date.toISOString().slice(0,10)!==text)throw Error('Enter a valid birth date.');
  const value=swiss().at(date),formatted=swiss().formatField(value);
  if($('dayAyan'))$('dayAyan').value=formatted;if($('daySum'))$('daySum').value='00:00:00';if($('ayanValue'))$('ayanValue').value=formatted;
  const status=$('kp-ayanamsha-status');if(status){status.textContent='Swiss Ephemeris 2.10.03 · Krishnamurti ayanamsha · '+text+': '+swiss().format(value)+'. The uploaded KP table remains unchanged and is used again when selected in Settings.';status.dataset.state='ready';status.dataset.ready='true';}
 }catch(error){const status=$('kp-ayanamsha-status');if(status){status.textContent='Swiss Krishnamurti ayanamsha unavailable: '+error.message;status.dataset.state='error';status.dataset.ready='false';}}
 return true;
}
function install(){
 if(installed)return true;if(!window.KPEphemeris||!swiss())return false;
 baseEphemeris=window.KPEphemeris;baseAnnual=window.KPAnnualAyanamsha||null;baseUploaded=window.KPUploadedEphemeris||null;
 const ayanamsha=(...args)=>isSwiss()?swiss().at(args[0]):baseEphemeris.ayanamsha(...args);
 const tropical=(...args)=>baseEphemeris.tropical(...args);
 const longitude=(...args)=>isSwiss()?norm(tropical(...args)-ayanamsha(args[0])):baseEphemeris.longitude(...args);
 const positions=(...args)=>{if(!isSwiss())return baseEphemeris.positions(...args);const date=swiss().dateValue(args[0]),ayan=ayanamsha(date);return Object.fromEntries(PLANETS.map(id=>[id,norm(tropical(date,id)-ayan)]));};
 const ascendant=(value,latitude,longitudeEast)=>{
  if(!isSwiss())return baseEphemeris.ascendant(value,latitude,longitudeEast);
  const date=swiss().dateValue(value),lat=Number(latitude),lon=Number(longitudeEast);
  if(!Number.isFinite(lat)||Math.abs(lat)>=89||!Number.isFinite(lon)||Math.abs(lon)>180)throw Error('Use latitude between −89° and 89° and longitude between −180° and 180°.');
  const r=Math.PI/180,theta=(Astronomy.SiderealTime(date)*15+lon)*r,eps=Astronomy.e_tilt(Astronomy.MakeTime(date)).tobl*r;
  const tropicalAsc=norm(Math.atan2(Math.cos(theta),-Math.sin(theta)*Math.cos(eps)-Math.tan(lat*r)*Math.sin(eps))/r);
  return norm(tropicalAsc-ayanamsha(date));
 };
 const convention=()=>isSwiss()?'Swiss Ephemeris 2.10.03 · Krishnamurti ayanamsha (sidereal mode 5) · offline reference fit':baseEphemeris.convention();
 window.KPEphemeris=Object.freeze({...baseEphemeris,ayanamsha,tropical,longitude,positions,ascendant,convention});
 if(baseAnnual)window.KPAnnualAyanamsha=Object.freeze({...baseAnnual,enabled:()=>isSwiss()||baseAnnual.enabled(),at:(...args)=>isSwiss()?swiss().at(args[0]):baseAnnual.at(...args),details:(...args)=>isSwiss()?swiss().details(args[0]):baseAnnual.details(...args),prepare:(...args)=>isSwiss()?prepareSwissWorksheet():baseAnnual.prepare(...args)});
 if(baseUploaded)window.KPUploadedEphemeris=Object.freeze({...baseUploaded,get:(...args)=>isSwiss()?null:baseUploaded.get(...args)});
 window.KPSwissAyanamsha=Object.freeze({enabled:isSwiss,at:value=>swiss().at(value),details:value=>swiss().details(value),format:value=>swiss().format(value),metadata:swiss().metadata});
 installed=true;window.dispatchEvent(new CustomEvent('kp-ephemeris-source-adapter-ready'));return true;
}
function setSource(value,options={}){
 if(!SOURCES.includes(value))throw Error('Unknown ephemeris source: '+value);const previous=source;source=value;install();
 if(options.prepare!==false)window.KPAnnualAyanamsha?.prepare?.();
 if(options.notify!==false&&previous!==source)window.dispatchEvent(new CustomEvent('kp-ephemeris-source-changed',{detail:{source,previous}}));
 return source;
}
window.KPEphemerisSources=Object.freeze({sources:SOURCES,defaultSource:'uploaded-kp',install,setSource,getSource:()=>source,isSwiss,getOriginals:()=>Object.freeze({ephemeris:baseEphemeris,annual:baseAnnual,uploaded:baseUploaded})});
if(!install()){window.addEventListener('kp-ephemeris-ready',install,{once:true});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});}
})();
