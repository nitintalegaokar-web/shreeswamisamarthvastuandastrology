/* User-requested traditional category, not an actuarial or medical life-expectancy estimate. */
(function(root){'use strict';
function analyze(model=root.currentKPModel){
 const asc=model?.houses?.find(h=>h.id===1),lord=model?.planets?.find(p=>p.id===asc?.sl),star=model?.planets?.find(p=>p.id===lord?.stl),sign=Number.isInteger(asc?.signIndex)?asc.signIndex:Number.isFinite(asc?.longitude)?Math.floor(((asc.longitude%1296000)+1296000)%1296000/108000):null;
 const ff=model?.fourfold?.planets?.find(p=>p.id===star?.id);
 if(!model?.ready||!lord||!star||!ff||sign===null)return {ready:false};
 const houses=[...new Set(['A','B','C','D'].flatMap(k=>ff[k]||[]))].sort((a,b)=>a-b),badhaka=[11,9,7][sign%3],maraka=houses.some(h=>h===2||h===7),bad=houses.includes(badhaka),category=maraka&&bad?'short':maraka||bad?'middle':'long';
 return {ready:true,category,ascendantSign:sign,modality:['movable','fixed','dual'][sign%3],lord:lord.id,star:star.id,depositedHouse:star.occ,ownedHouses:model.houses.filter(h=>h.sgl===star.id).map(h=>h.id),significators:houses,marakaHouses:[2,7],badhakaHouse:badhaka,hasMaraka:maraka,hasBadhaka:bad,referenceBand:category==='short'?'Under 33 years':category==='middle'?'33–66 years':'Over 66 years',minAge:null,maxAge:null};
}
function assess(selected,model=root.currentKPModel,lang=root.KPPreferences?.get?.().language||'english'){
 const data=analyze(model),mr=lang==='marathi';if(!data.ready)return {promised:false,incomplete:true,basis:'lagna-star-maraka-badhaka',reason:mr?'लग्न उपस्वामी, त्याचा नक्षत्रस्वामी व चार-पदरी कार्येशांची पूर्ण माहिती आवश्यक.':'Complete Lagna CSL, its star lord and four-fold significators are required.'};
 const category=selected==='medium'?'middle':selected,band=mr?{short:'३३ वर्षांपेक्षा कमी',middle:'३३ ते ६६ वर्षे',long:'६६ वर्षांपेक्षा अधिक'}[data.category]:data.referenceBand;
 const reason=mr?'पारंपरिक वर्ग: '+band+'. लग्न उपस्वामीचा नक्षत्रस्वामी '+data.star+'; कार्येश भाव '+data.significators.join(', ')+'. मारक २/७: '+(data.hasMaraka?'होय':'नाही')+'; बाधक भाव '+data.badhakaHouse+': '+(data.hasBadhaka?'होय':'नाही')+'. हा वैद्यकीय किंवा प्रत्यक्ष आयुर्मानाचा अंदाज नाही.':'Traditional source band: '+band+'. Lagna CSL star lord '+data.star+'; signified houses '+data.significators.join(', ')+'. Maraka 2/7: '+(data.hasMaraka?'yes':'no')+'; badhaka '+data.badhakaHouse+': '+(data.hasBadhaka?'yes':'no')+'. This is not a medical or reliable estimate of actual lifespan.';
 return {promised:category===data.category,qualified:true,basis:'lagna-star-maraka-badhaka',strongest:data.category,reference:data,reason};
}
root.KPLifespanReference=Object.freeze({analyze,assess});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPLifespanReference;
})(typeof window==='undefined'?globalThis:window);
