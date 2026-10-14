/* The supplied original KP Tables IV-A + IV-B are the only ayanamsha source.
 * Uploaded nirayan ephemeris rows remain authoritative; never subtract a second
 * ayanamsha from positions that are already nirayan.
 */
(()=>{'use strict';
if(window.KPEphemerisSources)return;
const SOURCES=Object.freeze(['uploaded-kp']);let installed=false,originals=null;
function install(){
 if(installed)return true;if(!window.KPEphemeris||!window.KPAnnualAyanamsha)return false;
 originals=Object.freeze({ephemeris:window.KPEphemeris,annual:window.KPAnnualAyanamsha,uploaded:window.KPUploadedEphemeris});
 const base=window.KPEphemeris;
 window.KPEphemeris=Object.freeze({...base,convention:()=> 'Original KP Tables IV-A + IV-B · exact annual + calendar-day addition'});
 installed=true;return true;
}
function setSource(value,options={}){
 // Old saved Swiss choices migrate to the user's newly approved original table.
 if(!['uploaded-kp','swiss-kp'].includes(value))throw Error('Only the supplied original KP table is supported.');
 install();if(options.prepare!==false)window.KPAnnualAyanamsha?.prepare();
 if(options.notify!==false)window.dispatchEvent(new CustomEvent('kp-ephemeris-source-changed',{detail:{source:'uploaded-kp'}}));
 return 'uploaded-kp';
}
window.KPEphemerisSources=Object.freeze({sources:SOURCES,defaultSource:'uploaded-kp',install,setSource,getSource:()=> 'uploaded-kp',isSwiss:()=>false,getOriginals:()=>originals});
if(!install()){window.addEventListener('kp-ephemeris-ready',install,{once:true});document.addEventListener('DOMContentLoaded',install,{once:true});}
})();
