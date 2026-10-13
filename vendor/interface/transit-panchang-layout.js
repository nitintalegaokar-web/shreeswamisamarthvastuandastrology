/* Compact screen layout; retain the original inputs, location events and calculations. */
(()=>{'use strict';
function init(){const section=document.getElementById('transit-panchang'),controls=section?.querySelector('.almanac-controls');if(!controls)return;
 const organize=()=>{const panel=section.querySelector('.kp-india-picker[data-place-for="tp-place"]');if(!panel||panel.querySelector('.tp-location-filters'))return !!panel;
  const details=document.createElement('details');details.className='tp-location-filters';const summary=document.createElement('summary');summary.textContent='Location filters / source';details.append(summary);
  for(const selector of ['.kp-india-picker-head','.kp-india-picker-filters','.kp-india-picker-source']){const node=panel.querySelector(selector);if(node)details.append(node);}
  panel.prepend(details);controls.append(panel);window.KPLanguage?.localize(details);return true;
 };
 if(!organize()){const observer=new MutationObserver(()=>{if(organize())observer.disconnect();});observer.observe(section,{childList:true,subtree:true});}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
