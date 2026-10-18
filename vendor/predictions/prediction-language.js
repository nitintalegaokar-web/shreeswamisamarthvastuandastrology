/* Never substitute another language's prediction when the selected translation is missing. */
(function(root){'use strict';
const normalize=x=>({en:'english',mr:'marathi',hi:'hindi'}[x]||x),language=()=>root.KPPreferences?.get?.().language||'english';
function message(kind='unavailable',lang=language()){const text={english:{unavailable:'A translation in the selected language is not available.',empty:'No matching predictions in the selected language.',birth:'Complete the natal chart to see predictions.'},marathi:{unavailable:'निवडलेल्या भाषेतील भाषांतर उपलब्ध नाही.',empty:'निवडलेल्या भाषेत लागू फलविचार उपलब्ध नाहीत.',birth:'फलविचार पाहण्यासाठी जन्मकुंडली पूर्ण करा.'},hindi:{unavailable:'चुनी हुई भाषा में अनुवाद उपलब्ध नहीं है।',empty:'चुनी हुई भाषा में लागू फलादेश उपलब्ध नहीं हैं।',birth:'फलादेश देखने के लिए जन्मकुंडली पूरी करें।'}};return text[lang]?.[kind]||'—';}
function clean(text,lang=language()){
 text=String(text??'');if(lang==='bilingual')return text;
 if(lang==='english')return text.split('\n').filter(line=>!/[\u0900-\u097f]/.test(line)).join('\n').trim();
 if(lang==='marathi'||lang==='hindi')return text.split('\n').map(line=>{
  const parts=line.split(/\s*\/\s*/);if(parts.length>1&&/[\u0900-\u097f]/.test(parts[0])&&parts.slice(1).every(p=>!/[\u0900-\u097f]/.test(p)))line=parts[0];
  if(lang==='marathi'&&/(?:^|\s)(?:है|हैं|नहीं|होगा|होंगे|आपका|आपकी|आपके|इसलिए|जिनके)(?:\s|[।.!?,]|$)/.test(line))return '';
  line=line.replace(/\s*\([^()]*[A-Za-z][^()]*\)/g,part=>/[\u0900-\u097f]/.test(part)?part:'');
  line=line.replace(/\b(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b/g,t=>root.KPLanguage?.translate(t,lang)||t);
  return /[A-Za-z]{3,}/.test(line)?'':line;
 }).filter(line=>line.trim()).join('\n').trim();
 return text;
}
function rowLanguage(row){if(row.language)return normalize(row.language);return /[\u0900-\u097f]/.test(row.text||'')?'marathi':'english';}
function filter(data,lang=language()){
 if(!data||lang==='bilingual')return data;
 if(!data.ready)return {...data,reason:clean(data.reason,lang)||message('birth',lang),rows:[]};
 const source=data.rows||[],rows=source.filter(r=>rowLanguage(r)===lang).map(r=>({...r,text:clean(r.text,lang),title:clean(root.KPLanguage?.translate(r.title||'',lang)||r.title,lang),...(r.bullets?{bullets:Object.fromEntries(Object.entries(r.bullets).map(([kind,items])=>[kind,items.map(item=>({...item,text:clean(item.text,lang)})).filter(item=>item.text)]))}:{})})).filter(r=>r.text);
 return {...data,rows,translationUnavailable:source.length>0&&!rows.length||data.translationUnavailable,language:lang,languageMessage:message(source.length||data.translationUnavailable?'unavailable':'empty',lang)};
}
root.KPPredictionLanguage=Object.freeze({language,normalize,clean,filter,message});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPPredictionLanguage;
})(typeof window==='undefined'?globalThis:window);
