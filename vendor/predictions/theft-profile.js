/* Traditional archetypes only: these are not evidence identifying an offender. */
(function(root){'use strict';
const signLords=['Ma','Ve','Me','Mo','Su','Me','Ve','Ma','Ju','Sa','Sa','Ju'];
const profiles={
 Su:['A middle-aged, confident, authoritative man; strong build and a bright or stern expression. Proud, bold and status-conscious. Traditional role associations: official, officer, senior or prominent person.','मध्यम वयाचा, आत्मविश्वासू व अधिकारवाणी पुरुष; मजबूत बांधा; तेजस्वी किंवा रागीट भाव. अभिमानी, धाडसी व प्रतिष्ठेला महत्त्व देणारा. पारंपरिक क्षेत्रसंबंध: सरकारी कर्मचारी, अधिकारी, वरिष्ठ किंवा प्रतिष्ठित व्यक्ती.'],
 Mo:['A young woman or emotionally sensitive person; round face and changeable manner. Restless, apprehensive or emotional. Traditional role associations: a familiar woman, household woman or nurse.','तरुण स्त्री किंवा भावनिक व्यक्ती; गोल चेहरा व बदलता स्वभाव. चंचल, घाबरणारी किंवा भावनिक वृत्ती. पारंपरिक क्षेत्रसंबंध: परिचित महिला, घरातील स्त्री किंवा परिचारिका.'],
 Ma:['A strongly built, assertive man; a household guard, male employee or bold person. Quick-tempered and impulsive. Traditional role associations: watchman, driver, worker or security guard.','मजबूत बांधा व धाडसी किंवा आक्रमक देहबोली असलेला पुरुष. रागीट व उतावळी वृत्ती. पारंपरिक क्षेत्रसंबंध: रखवालदार, पुरुष नोकर, वॉचमन, ड्रायव्हर, कामगार किंवा सुरक्षा कर्मचारी.'],
 Me:['An outsider who is clever, talkative and quick-moving; intelligent and methodical. Traditional role associations: trader, agent, courier, friend or young man.','बाहेरील, हुशार, बोलकी, चतुर व वेगाने काम करणारी व्यक्ती; बुद्धिमान व योजनाबद्ध वृत्ती. पारंपरिक क्षेत्रसंबंध: व्यापारी, एजंट, कुरिअर, मित्र किंवा तरुण पुरुष.'],
 Ju:['A religious or knowledgeable-looking person with a fuller or imposing build; calm and able to gain trust. Traditional role associations: priest, teacher, adviser or lawyer.','धार्मिक किंवा ज्ञानी दिसणारी व्यक्ती; जाडसर किंवा प्रभावी बांधा; शांत व विश्वास संपादन करणारी वृत्ती. पारंपरिक क्षेत्रसंबंध: पुजारी, शिक्षक, सल्लागार किंवा वकील.'],
 Ve:['A mature woman with an attractive, well-dressed appearance; comfort-loving and private. Traditional role associations: beauty services, an artist or a familiar woman.','प्रौढ स्त्री; आकर्षक व्यक्तिमत्त्व व व्यवस्थित पोशाख; आरामप्रिय व खाजगी स्वभाव. पारंपरिक क्षेत्रसंबंध: सौंदर्य व्यवसाय, कलाकार किंवा परिचित महिला.'],
 Sa:['An older, lean person with a serious expression; patient, quiet and discreet. Traditional role associations: a long-serving employee, worker, watchman or labourer.','वृद्ध किंवा कृश व्यक्ती; गंभीर चेहरा; शांत, धीराने व गुप्तपणे काम करणारी वृत्ती. पारंपरिक क्षेत्रसंबंध: जुना नोकर, कामगार, चौकीदार किंवा मजूर.']
};
function match(model=root.currentKPModel,lang=root.KPPreferences?.get?.().language||'english'){
 const cusp=model?.houses?.find(h=>h.id===7),lord=model?.planets?.find(p=>p.id===cusp?.sl);
 if(!model?.ready||!lord)return {ready:false,rows:[],reason:lang==='marathi'?'पूर्ण कुंडली व सप्तम उपस्वामी आवश्यक.':'A complete chart and seventh cusp sub lord are required.'};
 const node=['Ra','Ke'].includes(lord.id),sign=Number.isFinite(lord.longitude)?Math.floor(((lord.longitude%1296000)+1296000)%1296000/108000):Number.isInteger(lord.signIndex)&&lord.signIndex>=0&&lord.signIndex<12?lord.signIndex:null,profileLord=node?(sign===null?lord.sgl:signLords[sign]):lord.id;
 const rows=[];
 for(const selected of lang==='bilingual'?['english','marathi']:[lang]){
  if(!['english','marathi'].includes(selected))continue;const mr=selected==='marathi',pair=profiles[profileLord];
  const notice=mr?'ही अप्रमाणित पारंपरिक रूपरेषा आहे. यावरून चोराची ओळख किंवा कोणाचाही दोष ठरत नाही; वय, लिंग, व्यवसाय किंवा दिसण्यावरून कोणावर आरोप करू नये.':'This is an unverified traditional profile. It cannot identify a thief or establish guilt; age, gender, occupation or appearance is not evidence against anyone.';
  rows.push({id:'theft-notice-'+selected,language:selected,title:mr?'ओळखीचा पुरावा नाही':'Not identification evidence',text:notice,status:'reference'});
  rows.push({id:'theft-profile-'+lord.id+'-'+selected,language:selected,title:mr?'पारंपरिक संभाव्य रूपरेषा':'Traditional possible profile',text:pair?pair[mr?1:0]:mr?'राहू किंवा केतूच्या राशीस्वामीची माहिती अपुरी आहे; ग्रहस्थिती पूर्ण करा.':'The node’s Rashi lord is unavailable; complete its sign position.',status:'reference'});
 }
 return {ready:true,rows,lord:lord.id,profileLord:profiles[profileLord]?profileLord:null,usedRashiLord:node};
}
root.KPTheftProfile=Object.freeze({match});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPTheftProfile;
})(typeof window==='undefined'?globalThis:window);
