/* Source references are not diagnostic findings or treatment recommendations. */
(function(root){'use strict';
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function references(model=root.currentKPModel,lang=root.KPPreferences?.get?.().language||'english'){
 if(!model?.ready)return [];
 const out=[];
 for(const language of lang==='bilingual'?['english','marathi']:[lang]){
  if(!['english','marathi'].includes(language))continue;const mr=language==='marathi';
  out.push({language,title:mr?'आरोग्यविषयक पारंपरिक संदर्भ':'Traditional health references',text:mr?'हे ऐतिहासिक ज्योतिषीय संदर्भ आहेत. कुंडलीवरून आजाराचे निदान, रोगाचा धोका किंवा योग्य उपचार ठरत नाही. वैद्यकीय निर्णयासाठी पात्र डॉक्टरांचा सल्ला आवश्यक आहे.':'These are historical astrological associations. A chart cannot diagnose illness, establish medical risk or select appropriate treatment. Medical decisions require a qualified clinician.'});
  for(const [kind,cusp] of [['health',6],['treatment',5]]){
   const id=model.houses?.find(h=>h.id===cusp)?.sl,pair=root.KPDiseaseSuppliedData?.[kind]?.[id];
   if(pair)out.push({language,title:mr?(kind==='health'?'षष्ठ उपस्वामी · स्रोतामधील विषय':'पंचम उपस्वामी · उपचारपरंपरेचा संदर्भ'):(kind==='health'?'Sixth CSL · source associations':'Fifth CSL · historical therapy association'),text:pair[mr?1:0]+(kind==='treatment'?(mr?' ही परिणामकारकतेची खात्री किंवा उपचाराची शिफारस नाही.':' This is not a claim of effectiveness or a treatment recommendation.'):'')});
  }
 }
 return out;
}
function html(){const rows=references(),finance=(root.KPCuspalSupplied?.match(root.currentKPModel)||[]).filter(r=>r.condition.cusp===6);return '<section id="disease-supplied-references" data-no-localize>'+[...finance,...rows].map(r=>'<article class="pd-layer" lang="'+(r.language==='marathi'?'mr':'en')+'"><h3>'+esc(r.title)+'</h3><p>'+esc(r.text)+'</p></article>').join('')+'</section>';}
function install(){const old=root.KPDisease;if(!old)return;const target=document.getElementById('disease-results');
 const append=()=>{if(!target||target.querySelector('#disease-supplied-references'))return;target.insertAdjacentHTML('beforeend',html());};
 root.KPDisease=Object.freeze({...old,analyze:(...args)=>({...old.analyze(...args),suppliedReferences:references(...args)}),snapshot:()=>old.snapshot()+html(),refresh:()=>{const d=old.refresh();append();return d;},suppliedReferences:references});
 if(target)new MutationObserver(append).observe(target,{childList:true});append();root.addEventListener('kp-preferences-changed',()=>root.KPDisease.refresh());
}
root.KPDiseaseSupplied=Object.freeze({references});if(root.document){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,0));else install();}
})(typeof window==='undefined'?globalThis:window);
