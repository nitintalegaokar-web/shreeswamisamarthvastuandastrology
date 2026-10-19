/* Natal D1 whole-sign classification, requiring degree-level nodal enclosure. */
(function(root){'use strict';
const types=[
 ['Anant','अनंत','Marriage obstacles, fluctuating circumstances, sustained struggle, relationship differences, legal or lending losses and difficulty obtaining support.','विवाहात अडथळे; जीवनात चढ-उतार; प्रगतीसाठी संघर्ष; वैवाहिक मतभेद; न्यायालयीन किंवा कर्जव्यवहारात नुकसान; मदत मिळण्यात अडचणी.'],
 ['Kulik','कुलिक','Family tension, financial worries, debt, high expenditure, hard work with limited returns and domestic dissatisfaction.','कुटुंबात तणाव; आर्थिक विवंचना; कर्ज; खर्च जास्त; परिश्रमाच्या मानाने यश कमी; संसारात असंतोष.'],
 ['Vasuki','वासुकी','Difficulties involving siblings, relatives or friends, opposition, career or business obstacles and struggle for recognition.','भावंडे, नातेवाईक किंवा मित्रांशी अडचणी; विरोध; नोकरी-व्यवसायात अडथळे; प्रतिष्ठेसाठी संघर्ष.'],
 ['Shankhpal','शंखपाल','Domestic disputes, property and vehicle-related losses, employment fluctuations, financial strain and educational obstacles.','गृहकलह; मालमत्ता किंवा वाहनांमुळे नुकसान; नोकरीत चढ-उतार; आर्थिक ताण; शिक्षणात अडथळे; घरात असमाधान.'],
 ['Padma','पद्म','Concerns involving children, romance or education, limited gains, hidden opposition and losses through gambling or speculation.','संततीची चिंता; प्रेम व शिक्षणात अडथळे; लाभ कमी; गुप्त विरोध; कुटुंबात असंतोष; जुगार किंवा सट्ट्यात नुकसान.'],
 ['Mahapadma','महापद्म','Opposition, rising expenses, repeated difficulties, legal or romantic setbacks, discouragement and reduced confidence.','विरोधकांचा त्रास; खर्चवाढ; वारंवार संकटे; न्यायालयीन किंवा प्रेमातील अपयश; निराशा; आत्मविश्वास कमी; सतत कष्ट.'],
 ['Takshak','तक्षक','Marriage and partnership disagreements, romantic setbacks, blocked work, anger, unrecovered loans and increasing opposition.','विवाह व भागीदारीत मतभेद; प्रेमात अपयश; कामात अडथळे; राग; दिलेली रक्कम परत न मिळणे; विरोधक वाढणे.'],
 ['Karkotak','कर्कोटक','Major fluctuations, family disputes, obstacles to progress and difficulties receiving inherited property.','मोठे चढ-उतार; कुटुंबात वाद; प्रगतीत अडथळे; पैतृक संपत्ती मिळण्यात अडचणी.'],
 ['Shankhnaad','शंखनाद','Delays in fortune, travel obstacles, reduced paternal comfort, business losses, legal concerns and disappointments involving friends.','भाग्योदयास विलंब; प्रवासात अडथळे; पितृसुख कमी; व्यापारात नुकसान; न्यायालयीन चिंता; मित्रांकडून निराशा.'],
 ['Ghatak / Patak','घातक / पातक','Career instability, disagreements with the father, relocation, business setbacks and a difficult domestic environment.','करिअर अस्थिर; पित्याशी मतभेद; घरबदल; व्यवसायात अपयश किंवा नुकसान; कौटुंबिक कष्ट.'],
 ['Chitrakoot / Vishdhar','चित्रकूट / विषधर','Unfulfilled wishes, romantic setbacks, living away from the birthplace, higher-education obstacles and misunderstandings with relatives.','इच्छापूर्तीत अडथळे; प्रेमात अपयश; जन्मस्थानापासून दूर वास्तव्य; उच्च शिक्षणात अडथळे; नातेवाईकांशी गैरसमज.'],
 ['Sheshnag','शेषनाग','Rising expenses, foreign-place difficulties, hidden opposition, domestic disputes, reputation concerns, delays and lost property.','खर्चवाढ; परदेशात अडचणी; गुप्त विरोध; गृहकलह; बदनामीची चिंता; कामात विलंब; पैशाची चिंता; वस्तू हरवणे.']
];
const classical=['Su','Mo','Ma','Me','Ju','Ve','Sa'],mod=n=>(n%360+360)%360;
function analyze(vedic){
 const p=vedic?.native?.points,asc=vedic?.native?.asc;
 if(!vedic?.ready||!p||!Number.isFinite(asc)||!['Ra','Ke',...classical].every(id=>Number.isFinite(p[id])))return {ready:false,detected:false,status:'incomplete'};
 const rahu=mod(p.Ra),ketu=mod(p.Ke),eps=1e-7;
 if(Math.abs(mod(ketu-rahu)-180)>1e-5)return {ready:false,detected:false,status:'invalid-axis'};
 const positions=classical.map(id=>({id,offset:mod(p[id]-rahu)}));
 if(positions.some(p=>p.offset<eps||360-p.offset<eps||Math.abs(p.offset-180)<eps))return {ready:true,detected:false,status:'boundary-review'};
 const enclosed=positions.every(p=>p.offset>0&&p.offset<180)||positions.every(p=>p.offset>180&&p.offset<360);
 const house=(Math.floor(rahu/30)-Math.floor(mod(asc)/30)+12)%12+1,ketuHouse=(house+5)%12+1;
 return {ready:true,detected:enclosed,status:enclosed?'detected':'absent',rahuHouse:house,ketuHouse,type:enclosed?types[house-1]:null,houseSystem:'whole-sign',chart:'D1'};
}
function rows(vedic,language='marathi'){
 const data=analyze(vedic);if(!data.ready)return [];
 return (language==='bilingual'?['english','marathi']:[language]).filter(l=>['english','marathi'].includes(l)).map(lang=>{
 const mr=lang==='marathi',title=mr?'कालसर्प योग परीक्षण':'Kalsarpa assessment';
 let text=data.status==='boundary-review'?(mr?'एखादा ग्रह राहू-केतू अक्षावर आहे. सीमेवरील या स्थितीचे स्वतंत्र परीक्षण आवश्यक आहे; पूर्ण कालसर्प योग निश्चित केलेला नाही.':'A classical planet is on the nodal axis. This boundary case requires separate review; a full Kalsarpa configuration is not confirmed.'):
 data.detected?(mr?data.type[1]+' कालसर्प योगाचे संकेत. राहू भाव '+data.rahuHouse+'; केतू भाव '+data.ketuHouse+'. पारंपरिक फल: '+data.type[3]:data.type[0]+' Kalsarpa configuration indicated. Rahu house '+data.rahuHouse+'; Ketu house '+data.ketuHouse+'. Traditional interpretation: '+data.type[2]):
 (mr?'पूर्ण कालसर्प योग आढळत नाही. सर्व सात पारंपरिक ग्रह राहू-केतू अक्षाच्या एकाच बाजूस नाहीत.':'A full Kalsarpa configuration is not present: the seven classical planets are not all on one side of the nodal axis.');
 if(data.detected)text+=mr?' हे पारंपरिक संकेत आहेत; निश्चित घटना, आजार किंवा आयुर्मानाचे भाकीत नाही.':' These are traditional associations, not established predictions of events, disease or lifespan.';
 return {id:'vedic-kalsarpa-'+lang,kind:'kalsarpa',language:lang,title,text,status:data.status,assessment:data};
 });
}
root.KPKalsarpa=Object.freeze({analyze,rows,types});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPKalsarpa;
})(typeof window==='undefined'?globalThis:window);
