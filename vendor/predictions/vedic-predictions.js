/* Natal placement selection from the uploaded Jyotish File.txt; no calculation changes. */
(function(root){'use strict';
const SOURCE=root.KPJyotishData,signs=['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तूळ','वृश्चिक','धनु','मकर','कुंभ','मीन'],names={Su:'रवी',Mo:'चंद्र',Ma:'मंगळ',Me:'बुध',Ju:'गुरु',Ve:'शुक्र',Sa:'शनि'};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function summary(text){const first=text.split(/\n/).map(s=>s.trim()).find(Boolean)?.replace(/^\d+[.)]\s*/,'')||'';const sentences=first.match(/[^.!?।]+[.!?।]?/g)||[first];return sentences.slice(0,2).join('').trim();}
function match(model=root.currentKPModel){
 const missing={ready:false,reason:'प्रथम पूर्ण जन्मकुंडली तयार करा. जन्मलग्न व सर्व ग्रहस्थिती आवश्यक आहेत.',rows:[]};
 if(!SOURCE||!model?.ready||model.houses?.length!==12||model.planets?.length!==9)return missing;
 const asc=model.houses.find(h=>h.id===1)?.longitude;
 if(typeof asc!=='number'||!Number.isFinite(asc)||asc<0||asc>=1296000)return missing;
 const sign=Math.floor(asc/108000),rows=[];
 for(const entry of SOURCE.entries){let proof='',planet;
  if(entry.kind==='ascendant'&&entry.condition.sign===sign)proof='जन्मलग्न: '+signs[sign];
  if(entry.kind==='planet-house'){planet=model.planets.find(p=>p.id===entry.condition.planet);if(planet&&Number.isInteger(planet.occ)&&planet.occ===entry.condition.house)proof=names[planet.id]+' · भावचलित भाव '+planet.occ;}
  if(!proof)continue;
  rows.push({id:entry.id,kind:entry.kind,title:entry.kind==='ascendant'?signs[sign]+' लग्नाचे फल':names[planet.id]+' · '+entry.condition.house+' व्या भावातील फल',proof,text:entry.text,summary:summary(entry.text),status:'matched',source:{filename:SOURCE.metadata.filename,line:entry.line,endLine:entry.endLine},condition:{...entry.condition}});
 }
 if(rows.length!==8)return missing;
 return {ready:true,rows,context:'जन्मलग्न आणि सात ग्रहांची भावचलित स्थिती',ascendantSign:sign,referenceCount:SOURCE.references.length};
}
function render(rows,print=false){return '<div class="kp-vedic-results" lang="mr" data-no-localize><p class="kp-vedic-intro">जन्मलग्न व भावचलित ग्रहस्थितीनुसार आपल्या फाइलमधील फलविचार. मूळ मजकुरातील शुभ-अशुभ ग्रहयोगांच्या अटी स्वतंत्रपणे तपासाव्यात.</p>'+rows.map(r=>'<article class="kp-vedic-card" data-vedic-result="'+esc(r.id)+'"><h3>'+esc(r.title)+'</h3><p class="kp-vedic-basis">'+esc(r.proof)+'</p><p>'+esc(r.summary)+'</p>'+(print?'':'<details><summary>संपूर्ण मूळ फलविचार व सशर्त नियम</summary><p class="kp-vedic-source">'+esc(r.text)+'</p><small>'+esc(r.source.filename)+' · ओळी '+r.source.line+'–'+r.source.endLine+'</small></details>')+'</article>').join('')+'</div>';}
function referenceInfo(){return {count:SOURCE.references.length,reason:'शुभ/अशुभ योगांचे अचूक निकष आणि कालसर्प निर्मितीचे नियम फाइलमध्ये स्पष्ट नाहीत; त्यांना आपोआप लागू केलेले नाही.',titles:SOURCE.references.map(r=>r.title)};}
root.KPVedicPredictions=Object.freeze({match,render,referenceInfo,metadata:()=>({...SOURCE.metadata})});
if(typeof module!=='undefined'&&module.exports)module.exports=root.KPVedicPredictions;
})(typeof window==='undefined'?globalThis:window);
