/* Native calculations must not inherit stale manual rows from a saved chart. */
(()=>{'use strict';const $=id=>document.getElementById(id);
function prepare(){
 // Manual worksheets remain an explicit administrator operation. Normal chart
 // entry, imports and Calculate always derive rows from the native inputs.
 if(window.KPAdminCalculations?.isUnlocked())return;
 for(const [id,value] of [['p6-ephemeris-source','automatic'],['st-ephemeris-source','automatic'],['r5-house-source','automatic'],['kp-ayanamsha-source','annual']]){const n=$(id);if(n)n.value=value;}
 for(const id of ['p6_row_date_1','p6_row_date_2','p6_birth_pos_date']){const n=$(id);if(n)n.dataset.auto='1';}
}
function init(){const calculate=window.calculateAll;window.calculateAll=function(...args){prepare();return calculate.apply(this,args);};prepare();window.calculateAll();}
window.KPAutomaticCalculations=Object.freeze({prepare});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
