/* Explicit user-supplied CSL significator rules. No star-lord house union. */
(function(root){'use strict';
function match(model,lang=root.KPPreferences?.get?.().language||'english'){
 if(!model?.ready)return [];
 const data=root.KPCuspalSuppliedData?.rules||[],rows=[];
 for(const [i,r] of data.entries()){
  const cusp=model.houses?.find(h=>h.id===r.cusp),lord=model.planets?.find(p=>p.id===cusp?.sl);
  if(!lord||r.planet&&lord.id!==r.planet)continue;
  const level=model.fourfold?.planets?.find(p=>p.id===lord.id);
  if(!level&&r.houses.length)continue;
  const contacts=new Set([lord.id,lord.sgl,lord.stl,lord.sl,...(Array.isArray(lord.aspd)?lord.aspd:[]),...(Array.isArray(lord.aspg)?lord.aspg:[]),...(Array.isArray(lord.conj)?lord.conj:[])]);
  if(r.contacts&&!r.contacts.every(id=>contacts.has(id)))continue;
  const houses=[...new Set(['A','B','C','D'].flatMap(k=>level?.[k]||[]))];
  if(!r.houses.every(n=>houses.includes(n)))continue;
  for(const language of lang==='bilingual'?['english','marathi']:[lang]){
   const text=language==='english'?r.en:language==='marathi'?r.mr:null;if(!text)continue;
   rows.push({id:'supplied-cuspal-'+i+'-'+language,language,key:'Bh'+r.cusp+'R'+r.houses.join(''),title:language==='marathi'?r.cusp+' भावाचे फल': 'House '+r.cusp+' prediction',text,status:'matched',condition:{cusp:r.cusp,houses:r.houses},lord:lord.id});
  }
 }
 return rows;
}
root.KPCuspalSupplied=Object.freeze({match});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPCuspalSupplied;
})(typeof window==='undefined'?globalThis:window);
