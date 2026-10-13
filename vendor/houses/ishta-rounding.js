/* Owner-approved Ishta Farak: advance one arcminute only at 50 arcseconds. */
(()=>{'use strict';
function roundArcseconds(seconds){
 if(!Number.isFinite(seconds))throw Error('Use a finite Ishta Farak.');
 const absolute=Math.abs(seconds),minutes=Math.floor(absolute/60),remainder=absolute-minutes*60;
 const rounded=minutes+(remainder>=50-1e-8?1:0);
 return seconds<0?-rounded:rounded;
}
globalThis.KPIshtaFarak=Object.freeze({roundArcseconds});
if(typeof module!=='undefined')module.exports=globalThis.KPIshtaFarak;
})();
