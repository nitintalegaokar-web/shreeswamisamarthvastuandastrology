(function(root){'use strict';
function match(model=root.currentKPModel,lang=root.KPPreferences?.get?.().language||'english'){
 const cusp=model?.houses?.find(h=>h.id===3);if(!model?.ready||!cusp)return {ready:false,rows:[],reason:lang==='marathi'?'तृतीय भावासह पूर्ण कुंडली आवश्यक.':'A complete chart including the third cusp is required.'};
 const signIndex=Number.isInteger(cusp.signIndex)?cusp.signIndex:Number.isFinite(cusp.longitude)?Math.floor(((cusp.longitude%1296000)+1296000)%1296000/108000):null;
 const entry=root.KPThirdCuspMindsetData?.entries.find(r=>r.signIndex===signIndex&&r.sgl===cusp.sgl&&r.stl===cusp.stl&&r.sl===cusp.sl),rows=[];
 for(const language of lang==='bilingual'?['english','marathi']:[lang]){
  if(!['english','marathi'].includes(language))continue;const mr=language==='marathi';
  rows.push({id:'third-cusp-mindset-'+(entry?.number||'missing')+'-'+language,language,title:mr?'तृतीय भाव · मनोवृत्ती':'Third cusp · Mindset',text:entry?entry[mr?'marathi':'english']:(mr?'या अचूक ग्रहसंयोगासाठी दिलेल्या तक्त्यात मनोवृत्तीचे फल उपलब्ध नाही.':'The supplied table has no mindset entry for this exact combination.'),status:entry?'matched':'reference',sourceNumber:entry?.number});
 }
 return {ready:true,rows};
}
root.KPThirdCuspMindset=Object.freeze({match});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPThirdCuspMindset;
})(typeof window==='undefined'?globalThis:window);
