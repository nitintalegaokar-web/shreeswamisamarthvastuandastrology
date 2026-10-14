/* Owner-approved Ishta Farak: reference image: round to the nearest arcminute; half a minute (30 arcseconds) advances. */
(()=>{'use strict';
function roundArcseconds(seconds){
 if(!Number.isFinite(seconds))throw Error('Use a finite Ishta Farak.');
 const absolute=Math.abs(seconds),minutes=Math.floor(absolute/60),remainder=absolute-minutes*60;
 const rounded=minutes+(remainder>=30-1e-8?1:0);
 return seconds<0?-rounded:rounded;
}
globalThis.KPIshtaFarak=Object.freeze({roundArcseconds});
if(typeof module!=='undefined')module.exports=globalThis.KPIshtaFarak;
})();
