/* Lookup the supplied numeric cusps, with circular interpolation in ST and latitude. */
(()=>{'use strict';
const norm=x=>((x%360)+360)%360,delta=(a,b)=>norm(b-a+180)-180;
function create(data){
 const {times,values,metadata}=data;
 function lookup(latitude,siderealSeconds,ayanamsha=0){
  if(typeof latitude!=='number'||!Number.isFinite(latitude)||latitude<metadata.latitudeMin||latitude>metadata.latitudeMax)throw Error('Uploaded house tables cover 0°–60° north.');
  if(typeof siderealSeconds!=='number'||!Number.isFinite(siderealSeconds)||siderealSeconds<0||siderealSeconds>86400)throw Error('Use sidereal time from 00:00:00 through 24:00:00.');
  if(typeof ayanamsha!=='number'||!Number.isFinite(ayanamsha)||ayanamsha<0||ayanamsha>=360)throw Error('Enter a valid ayanamsha.');
  let left=0,right=times.length-1;
  while(right-left>1){const middle=Math.floor((left+right)/2);if(times[middle]<=siderealSeconds)left=middle;else right=middle;}
  const lowLat=Math.floor(latitude),highLat=Math.min(metadata.latitudeMax,Math.ceil(latitude)),latFraction=latitude-lowLat,timeFraction=(siderealSeconds-times[left])/(times[right]-times[left]);
  const mix=(a,b,f)=>norm(a+delta(a,b)*f);
  const small=values[lowLat][left].map((a,i)=>mix(a,values[highLat][left][i],latFraction));
  const large=values[lowLat][right].map((a,i)=>mix(a,values[highLat][right][i],latFraction));
  const tropical=small.map((a,i)=>mix(a,large[i],timeFraction)),tropicalCusps=Array(12);
  for(const [i,h] of metadata.houses.entries()){tropicalCusps[h-1]=tropical[i];tropicalCusps[(h+5)%12]=norm(tropical[i]+180);}
  return {ready:true,source:'uploaded',latitude,siderealSeconds,ayanamsha,tropicalCusps,cusps:tropicalCusps.map(x=>norm(x-ayanamsha)),brackets:{latitudeLow:lowLat,latitudeHigh:highLat,timeLow:times[left],timeHigh:times[right],latitudeFraction:latFraction,timeFraction,small,large,corners:[values[lowLat][left].slice(),values[lowLat][right].slice(),values[highLat][left].slice(),values[highLat][right].slice()]},system:'Placidus',units:'degrees'};
 }
 return Object.freeze({lookup,metadata:()=>JSON.parse(JSON.stringify(metadata))});
}
globalThis.KPHouseTable=Object.freeze({create});
if(typeof module!=='undefined')module.exports=globalThis.KPHouseTable;
})();
