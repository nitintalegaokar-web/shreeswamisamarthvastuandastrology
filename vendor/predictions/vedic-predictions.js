/* Natal placement selection from the uploaded Jyotish File.txt; no calculation changes. */
(function(root){'use strict';
const SOURCE=root.KPJyotishData,signs=['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तूळ','वृश्चिक','धनु','मकर','कुंभ','मीन'],names={Su:'रवी',Mo:'चंद्र',Ma:'मंगळ',Me:'बुध',Ju:'गुरु',Ve:'शुक्र',Sa:'शनि'};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function summary(text){const first=text.split(/\n/).map(s=>s.trim()).find(Boolean)?.replace(/^\d+[.)]\s*/,'')||'';const sentences=first.match(/[^.!?।]+[.!?।]?/g)||[first];return sentences.slice(0,2).join('').trim();}
function bulletPoints(text){
 const positive=/यश|सुख|संपत्त|धनवान|लाभ|पराक्रम|शूर|विद्व|गुणी|समृद्ध|उत्तम|सन्मान|प्रसिद्ध|कीर्ती|बुद्धिमान|सद्गुण|आनंद|सुंदर|दयाळू|सौंदर्य|धैर्य|चांगल|धार्मिक|उदार|हुषार|हुशार|बलवान|निरोगी|आयुष्यवान|निपुण|संतुष्ट|संतोष|कर्तबगार|उन्नती|समाधान|विजय/;
 const negative=/अपयश|नुकसान|कष्ट|रोग|आजारी|चिंता|भांडण|भांडखोर|भांडकुदळ|शत्रु|शत्रू|दारिद्र्य|दुःख|दरिद्री|दुर्बळ|अनिष्ट|अशुभ|वियोग|अडचण|त्रास|दुखापत|विवाद|वैर|भीती|दोष|आळशी|उतावळ|चिडखोर|शीघ्रकोपी|मंदबुद्धी|संघर्ष|क्रोध|दुर्व्यसन|अल्पायुष|मत्सर|चंचल|हानी|अपमान|तोटा|अविश्वास|फसव|दुष्ट|निर्दय|दुःखी|अभागी|असंतोष|असमाधान/;
 const conditional=/असल्यास|असता|असताना|असेल|असतील|आल्यास|केल्यास|झाल्यास|जर\s|तर\s|शुभसंबंध|अशुभसंबंध|दृष्टी|दृष्टियोग|युती|बिघडल्यास/;
 const out={positive:[],negative:[]},seen=new Set();
 for(const paragraph of String(text).split(/(?:प्रसिद्ध|ख्यातनाम|विख्यात)\s*(?:व्यक्ती|व्यक्ति|लोक)/u)[0].split(/\n+/)){let inherited=false;for(let sentence of paragraph.split(/(?<=[!?।])\s+|(?<!\bव)(?<=\.)\s+|[,;]\s*/u)){
  sentence=sentence.trim().replace(/^\d+[.)]\s*/,'');if(!sentence||sentence.length>450||seen.has(sentence)||/विख्यात|उदाहरणार्थ|प्रसिद्ध लोक|प्रसिद्ध व्यक्ती|रणांगण|जाळतील|वश करतात/.test(sentence))continue;
  const ownCondition=conditional.test(sentence);if(ownCondition)inherited=true;else if(inherited)continue;
  const relieved=sentence.replace(/(?:रोग|शत्रू|शत्रु|कष्ट|दुःख|दोष|नुकसान)[^,।.!?]{0,16}(?:नाश|विजय|मुक्त|नाही|नसते|नसतात)/g,'');
  const negatedBenefit=/(?:सुख|लाभ|यश|संपत्ती|धन|संतती|आरोग्य)\s*(?:मुळीच\s*|कधीच\s*)?(?:मिळत नाही|मिळत नस|नसते|नसतो|नसतात|नाही)/.test(sentence);
  const bad=negative.test(relieved)||negatedBenefit,good=positive.test(sentence)||relieved!==sentence;if(!bad&&!good)continue;
  seen.add(sentence);out[bad?'negative':'positive'].push({text:sentence,conditional:ownCondition,mixed:bad&&good&&!negatedBenefit});
 }}
 for(const key of ['positive','negative'])out[key]=out[key].sort((a,b)=>Number(a.conditional)-Number(b.conditional)||Number(a.mixed)-Number(b.mixed)).slice(0,2);
 return out;
}
function match(vedic=root.KPVedic?.core?.()){
 const lang=root.KPPreferences?.get?.().language||'marathi';
 const missing={ready:false,reason:'प्रथम पूर्ण जन्मकुंडली तयार करा. जन्मलग्न व सर्व ग्रहस्थिती आवश्यक आहेत.',rows:[]};
 const d1=vedic?.vargas?.[1],valid=p=>Number.isInteger(p?.sign)&&p.sign>=0&&p.sign<12;
 if(!SOURCE||!vedic?.ready||!Array.isArray(d1))return missing;
 const asc=d1.find(p=>p.id==='As');if(!valid(asc)||Object.keys(names).some(id=>!valid(d1.find(p=>p.id===id))))return missing;
 if(lang==='english'&&root.KPKalsarpa)return {ready:true,rows:[...root.KPKalsarpa.rows(vedic,lang),...(root.KPNatalPanchangPredictions?.rows(vedic,lang)||[])],chart:'D1',houseSystem:'whole-sign'};
 if(!['marathi','bilingual'].includes(lang))return {ready:true,rows:[],translationUnavailable:true,language:lang,languageMessage:root.KPPredictionLanguage?.message('unavailable',lang)||'A translation in the selected language is not available.'};
 const sign=asc.sign,rows=[];
 for(const entry of SOURCE.entries){let proof='',planet;
  if(entry.kind==='ascendant'&&entry.condition.sign===sign)proof='जन्मलग्न: '+signs[sign];
  if(entry.kind==='planet-house'){planet=d1.find(p=>p.id===entry.condition.planet);const house=planet?(planet.sign-sign+12)%12+1:0;if(planet&&house===entry.condition.house)proof=names[planet.id]+' · वैदिक D1 भाव '+house+' · '+signs[planet.sign];}
  if(!proof)continue;
  rows.push({language:'marathi',id:entry.id,kind:entry.kind,title:entry.kind==='ascendant'?signs[sign]+' लग्नाचे फल':names[planet.id]+' · '+entry.condition.house+' व्या भावातील फल',proof,text:entry.text,summary:summary(entry.text),bullets:bulletPoints(entry.text),status:'matched',source:{filename:SOURCE.metadata.filename,line:entry.line,endLine:entry.endLine},condition:{...entry.condition}});
 }
 if(rows.length!==8)return missing;
 rows.push(...(root.KPKalsarpa?.rows(vedic,lang)||[]),...(root.KPNatalPanchangPredictions?.rows(vedic,lang)||[]),...(root.KPVedicBhav?.rows(vedic,lang)||[]));
 return {ready:true,rows,context:'वैदिक D1 जन्मराशी कुंडली · पूर्ण राशीचे भाव',chart:'D1',houseSystem:'whole-sign',ascendantSign:sign,referenceCount:SOURCE.references.length};
}
function render(rows,print=false){if(!rows.length)return '';const group=(items,kind)=>'<section class="kp-vedic-polarity kp-vedic-'+kind+'"><h4>'+(kind==='positive'?'अनुकूल संकेत':'आव्हानात्मक संकेत')+'</h4>'+(items.length?'<ul>'+items.map(item=>'<li>'+(item.conditional?'<span class="kp-vedic-condition">सशर्त · </span>':item.mixed?'<span class="kp-vedic-condition">मिश्र फल · </span>':'')+esc(item.text)+'</li>').join('')+'</ul>':'<p class="kp-vedic-empty">या स्थितीसाठी स्वतंत्र '+(kind==='positive'?'अनुकूल':'आव्हानात्मक')+' संकेत दिलेला नाही.</p>')+'</section>';return '<div class="kp-vedic-results" lang="mr" data-no-localize>'+rows.map(r=>{if(['kalsarpa','natal-panchang'].includes(r.kind))return '<article class="kp-vedic-card" data-no-localize lang="'+(r.language==='marathi'?'mr':'en')+'" data-vedic-result="'+esc(r.id)+'"><h3>'+esc(r.title)+'</h3><p>'+esc(r.text)+'</p></article>';const points=r.bullets||bulletPoints(r.text);return '<article class="kp-vedic-card" data-vedic-result="'+esc(r.id)+'"><h3>'+esc(r.title)+'</h3><p class="kp-vedic-basis">'+esc(r.proof)+'</p>'+group(points.positive,'positive')+group(points.negative,'negative')+(print?'':'<details><summary>सविस्तर फलविचार</summary><p class="kp-vedic-source">'+esc(r.text)+'</p></details>')+'</article>';}).join('')+'</div>';}
function referenceInfo(){return {count:SOURCE.references.length,reason:'इतर शुभ/अशुभ योगांचे अस्पष्ट निकष आपोआप लागू केलेले नाहीत. कालसर्प परीक्षणासाठी स्वतंत्र जन्मराशी व अंशाधारित नियम वापरले आहेत.',titles:SOURCE.references.map(r=>r.title)};}
root.KPVedicPredictions=Object.freeze({match,render,bulletPoints,referenceInfo,metadata:()=>({...SOURCE.metadata})});
if(typeof module!=='undefined'&&module.exports)module.exports=root.KPVedicPredictions;
})(typeof window==='undefined'?globalThis:window);
