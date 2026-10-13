/* Offline Swiss Ephemeris Krishnamurti ayanamsha reference.
 *
 * This module is calculation-only. It has no settings, storage or DOM side
 * effects. The fit was produced from Swiss Ephemeris 2.10.03 sidereal mode 5
 * and is independently checked by validate_swiss_krishnamurti.py.
 */
(()=>{'use strict';
if(window.KPSwissKrishnamurti)return;
const METADATA=Object.freeze({
 engine:'Swiss Ephemeris 2.10.03',siderealMode:5,modeName:'Krishnamurti',
 start:'1900-01-01T00:00:00Z',endExclusive:'2101-01-01T00:00:00Z',
 startJD:2415020.5,endJD:2488434.5,maxReferenceErrorArcseconds:0.000016,
 coefficients:Object.freeze([23.767374768561112,1.4038517009258205,0.00015506283475881375,7.300019807173769e-10,2.0332944117239102e-10])
});
const norm=value=>((Number(value)%360)+360)%360;
function dateValue(value){
 const date=value instanceof Date?new Date(value.getTime()):new Date(value);
 if(!Number.isFinite(date.getTime())||date.getUTCFullYear()<1900||date.getUTCFullYear()>2100)throw Error('Swiss Krishnamurti ayanamsha supports dates from 1900 through 2100.');
 return date;
}
function at(value){
 const date=dateValue(value),jd=date.getTime()/86400000+2440587.5,x=(2*jd-METADATA.startJD-METADATA.endJD)/(METADATA.endJD-METADATA.startJD),c=METADATA.coefficients;
 let b1=0,b2=0;
 for(let index=c.length-1;index>=1;index--){const b0=2*x*b1-b2+c[index];b2=b1;b1=b0;}
 return x*b1-b2+c[0];
}
function format(value){let seconds=Math.round(norm(value)*3600)%1296000;return Math.floor(seconds/3600)+'° '+String(Math.floor(seconds%3600/60)).padStart(2,'0')+'′ '+String(seconds%60).padStart(2,'0')+'″';}
function formatField(value){let seconds=Math.round(norm(value)*3600)%1296000;return String(Math.floor(seconds/3600)).padStart(2,'0')+':'+String(Math.floor(seconds%3600/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
function details(value){const date=dateValue(value);return {date:date.toISOString(),degrees:at(date),...METADATA};}
window.KPSwissKrishnamurti=Object.freeze({at,details,dateValue,format,formatField,metadata:METADATA});
})();
