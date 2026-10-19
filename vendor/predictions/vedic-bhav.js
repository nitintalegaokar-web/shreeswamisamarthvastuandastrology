/* Traditional house ownership; Rahu/Ketu do not replace the classical sign lords. */
(function(root){'use strict';
const lords=['Ma','Ve','Me','Mo','Su','Me','Ve','Ma','Ju','Sa','Sa','Ju'];
function rows(vedic,lang='marathi'){
 if(!vedic?.ready||!['marathi','bilingual'].includes(lang))return [];
 const d1=vedic.vargas?.[1],asc=d1?.find(p=>p.id==='As');if(!Number.isInteger(asc?.sign))return [];
 const rows=[];
 for(let house=1;house<=12;house++){
  const lord=lords[(asc.sign+house-1)%12],planet=d1.find(p=>p.id===lord);if(!Number.isInteger(planet?.sign))continue;
  const occupied=(planet.sign-asc.sign+12)%12+1,entry=root.KPVedicBhavData?.entries.find(r=>r.lordHouse===house&&r.occupiedHouse===occupied);if(!entry)continue;
  rows.push({id:entry.id,kind:'bhav-fal',language:'marathi',title:house+' भावेश · '+occupied+' व्या भावातील फल',text:entry.text,proof:'वैदिक जन्मराशी · पूर्ण राशीचे भाव · पारंपरिक संदर्भ',status:'matched',condition:{lordHouse:house,occupiedHouse:occupied},lord});
 }
 return rows;
}
root.KPVedicBhav=Object.freeze({rows});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPVedicBhav;
})(typeof window==='undefined'?globalThis:window);
