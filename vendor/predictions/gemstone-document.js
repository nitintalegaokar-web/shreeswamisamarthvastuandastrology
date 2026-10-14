(() => {
'use strict';
const unique=a=>[...new Set(a)].sort((a,b)=>a-b);
function evaluate(model,rule) {
 if(!model?.ready)throw Error('Complete the kundali first.');
 const method=rule.method==='sixfold'?'sixfold':'fourfold',fields=method==='sixfold'?['A','B','C','D','E','F']:['A','B','C','D'];
 const cusp=model.houses.find(h=>h.id===11),sub=model.planets.find(p=>p.id===cusp?.sl),star=model.planets.find(p=>p.id===sub?.stl);
 if(!star)throw Error('The 11th cusp sub lord and its star lord are required.');
 const required=[1,2,11];
 const results=model.planets.map(p=>{
  const sig=model[method]?.planets.find(r=>r.id===p.id);if(!sig)throw Error('Complete the significators first.');
  const houses=unique(fields.flatMap(f=>sig[f]||[])),hits=required.filter(h=>houses.includes(h)),qualifies=p.id===star.id&&hits.length>0;
  return {id:p.id,stone:String(rule.stones?.[p.id]||''),houses,layers:[{role:'star of XI CSL',id:p.id,houses}],missing:required.filter(h=>!houses.includes(h)),blocked:[],retrograde:p.retrograde===true,combust:false,ownership:[],score:hits.length,eligible:p.id===star.id,qualifies,priority:qualifies?1:null};
 });
 results.sort((a,b)=>Number(b.qualifies)-Number(a.qualifies));
 const proof='XI CSL '+sub.id+' → its star lord '+star.id+' → houses '+results.find(r=>r.id===star.id).houses.join(', ')+'. Required: at least one of 1, 2, 11.';
 return {favorableLords:[1,10,9].map(id=>({cusp:id,id:model.houses.find(h=>h.id===id)?.sgl})),ready:true,mode:'kp',required,excluded:[],method,roles:['star of XI CSL'],highest:Math.max(0,...results.filter(r=>r.qualifies).map(r=>r.score)),results,proof,cuspSub:sub.id,starLord:star.id,documentRule:true};
}
window.KPGemstoneDocument=Object.freeze({evaluate});
})();
