/* Interpretation lookup only. Reuses existing model, periods and aspect results;
 * never changes a position, cusp, ayanamsha, ST, table value or Dasha date.
 */
(()=>{'use strict';
const catalogue=JSON.parse(document.getElementById('kp-supplied-prediction-data').textContent);
const groups=new Map(),names={Su:'Sun',Mo:'Moon',Ma:'Mars',Me:'Mercury',Ju:'Jupiter',Ve:'Venus',Sa:'Saturn',Ra:'Rahu',Ke:'Ketu',Ur:'Uranus',Ne:'Neptune',Pl:'Pluto'};
const marathiNames={Su:'रवी',Mo:'चंद्र',Ma:'मंगळ',Me:'बुध',Ju:'गुरु',Ve:'शुक्र',Sa:'शनि',Ra:'राहू',Ke:'केतू',Ur:'हर्षल',Ne:'नेपच्यून',Pl:'प्लूटो'};
function transitTitle(planet,house){const en=names[planet]+' · '+house+' from Moon',mr=marathiNames[planet]+' · चंद्रापासून भाव '+house;return language()==='marathi'?mr:language()==='bilingual'?en+'\n'+mr:en;}
const classical=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
for(const row of catalogue.records){if(row.kind==='yoga'&&row.mappingStatus==='review')continue;const key=row.kind+'|'+row.key;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row);}
const titles={'yoga-results':['Conjunction Results','युती फल'],'transit-results':['Transit Results','गोचर फल'],'numerology':['Numerology','अंकशास्त्र']};
function title(category){const pair=titles[category];if(!pair)return '';return language()==='marathi'?pair[1]:language()==='bilingual'?pair.join(' · '):pair[0];}
function language(){return window.KPPreferences?.get?.().language||'english';}
function readable(text){return String(text||'').replace(/\\n/g,'\n').replace(/^[ \t]*#{1,6}[ \t]*/gm,'').replace(/\*\*/g,'').replace(/^\s*[*_-]{3,}\s*$/gm,'').trim();}
function textFor(rows,fallback){
 const lang=language(),code=window.KPLanguage?.languages.find(l=>l.value===lang)?.code||({english:'en',marathi:'mr',hindi:'hi'}[lang]||lang);
 const pick=lang==='bilingual'?rows.filter(r=>['mr','en'].includes(r.language)):rows.filter(r=>r.language===code||r.language===lang);
 const texts=pick.map(r=>readable(r.text));
 if(fallback&&(lang==='english'||lang==='bilingual')&&!pick.some(r=>r.language==='en'))texts.push(readable(fallback.text));
 return [...new Set(texts)].join('\n\n');
}
function result(rows,proof,title,fallback,status='matched'){
 const first=rows[0];return {id:'supplied-'+first.kind+'-'+first.key,key:first.key,language:language(),title,proof,text:textFor(rows,fallback),status,supplied:true,sources:[...new Set(rows.flatMap(r=>r.sources||[r.source]))]};
}
function placement(key,model){
 const moon=model.planets.find(p=>p.id==='Mo');let m;
 if((m=/^(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke|Ur|Ne|Pl)InH(1[0-2]|[1-9])$/.exec(key))){const p=model.planets.find(p=>p.id===m[1]);return p?.occ===Number(m[2])?{proof:names[p.id]+' · Bhav '+m[2],title:names[p.id]+' · Bhav '+m[2]}:null;}
 if((m=/^(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)In(Ar|Ta|Ge|Ca|Le|Vi|Li|Sc|Sg|Cp|Aq|Pi)$/.exec(key))){const p=model.planets.find(p=>p.id===m[1]);return p?.signCode===m[2]?{proof:names[p.id]+' · '+p.sign,title:names[p.id]+' · '+p.sign}:null;}
 if((m=/^(?:nak)(\d+)$/.exec(key))||(m=/^Nak(\d+)R([1-3])$/.exec(key)))return moon?.nakIndex===Number(m[1])-1?{proof:'Moon · '+moon.nakshatra,title:moon.nakshatra}:null;
 if((m=/^Nak(\d+)C([1-4])$/.exec(key)))return moon?.nakIndex===Number(m[1])-1&&moon.pada===Number(m[2])?{proof:'Moon · '+moon.nakshatra+' · Pada '+moon.pada,title:moon.nakshatra+' · Pada '+moon.pada}:null;
 return null;
}
function matching(category,model,instant,periods){
 if(!model?.ready)return {ready:false,reason:'Complete the natal chart to read its supplied interpretations.',rows:[]};
 const rows=[];let context='';
 if(category==='planet-house-results'){
  for(const group of groups.values())if(group[0].kind==='planet-house'){const match=placement(group[0].key,model);if(match)rows.push({group,...match});}
 }else if(category==='general-predictions'){
  for(const group of groups.values())if(['planet-house','planet-sign','nakshatra','nakshatra-code'].includes(group[0].kind)){const match=placement(group[0].key,model);if(match)rows.push({group,...match});}
 }else if(category==='house-results'){
  for(const group of groups.values())if(group[0].kind==='house-lord'){
   const m=/^Bh(1[0-2]|[1-9])L(1[0-2]|[1-9])$/.exec(group[0].key);if(!m)continue;
   const cusp=model.houses.find(h=>h.id===Number(m[1])),lord=model.planets.find(p=>p.id===cusp?.sgl);
   if(lord?.occ===Number(m[2]))rows.push({group,title:'House '+m[1]+' lord · '+names[lord.id]+' in Bhav '+m[2],proof:'Cusp '+m[1]+' · sign lord '+lord.id+' · occupied house '+lord.occ});
  }
 }else if(category==='dasha-results'){
  try{periods=periods||window.KPDashaFal.current(model,instant).periods;}catch(error){return {ready:false,reason:error.message,rows:[]};}
  for(const group of groups.values()){const r=group[0];if(r.kind==='dasha-pair'&&r.md===periods[0]?.id&&r.ad===periods[1]?.id)rows.push({group,title:'MD '+names[r.md]+' · AD '+names[r.ad],proof:'Running native MD '+r.md+' → AD '+r.ad});}
 }else if(category==='yoga-results'){
  // Use the existing approved aspect engine and its existing configured orbs.
  const aspects=window.KPWesternAspects.calculate(model.planets,model.houses,window.KPWesternAspects.getSettings()).planetToPlanet.filter(r=>r.angle===0);
  const pair=new Set(aspects.map(r=>[r.source,r.target].sort().join('|')));
  for(const group of groups.values())if(group[0].kind==='yoga'){
   const mask=Number(group[0].key.slice(1));if(!Number.isInteger(mask)||mask<1||mask>511)continue;
   const planets=group[0].planets||classical.filter((id,i)=>mask&(1<<i));
   if(planets.length<2||!planets.every((id,i)=>planets.slice(i+1).every(other=>pair.has([id,other].sort().join('|')))))continue;
   rows.push({group,title:planets.map(id=>names[id]).join(' + '),proof:'Conjunction matches from the existing aspect engine · '+planets.join(', ')});
  }
 }else if(category==='transit-results'){
  const data=window.KPTransitChart?.getData?.();
  if(!data?.ready)return {ready:false,reason:'Calculate the selected Transit Chart to see its transit-house interpretations.',rows:[]};
  const moon=model.planets.find(p=>p.id==='Mo');if(!Number.isInteger(moon?.signIndex))return {ready:false,reason:'Calculate the natal Moon sign first.',rows:[]};
  context=data.localDate+' '+data.localTime+' · '+(data.place||'')+' · whole-sign houses counted from natal Moon '+(moon.sign||moon.signCode||moon.signIndex+1);
  for(const group of groups.values()){const r=group[0];if(r.kind!=='transit-house')continue;
   const planet=data.planets?.find(p=>p.id===r.planet),sign=planet?.details?.signIndex;if(Number.isInteger(sign)&&((sign-moon.signIndex+12)%12)+1===r.house)rows.push({group,title:transitTitle(r.planet,r.house),proof:'Natal Moon sign '+(moon.sign||moon.signCode||moon.signIndex+1)+' · transit '+r.planet+' sign '+(sign+1)+' · house '+r.house+' from Moon · '+data.localDate+' '+data.localTime});
  }
 }else if(category==='outer-references'){
  for(const group of groups.values())if(group[0].kind==='outer-reference')rows.push({group,title:names[group[0].planet]+' · supplied reference',proof:'Reference text only; no new outer-planet calculations or Dasha lords.',status:'reference'});
 }
 return {ready:true,rows,context};
}
function merge(base,category,model,instant=new Date(),periods){
 if(!['general-predictions','house-results','dasha-results'].includes(category))return base;
 const matched=matching(category,model,instant,periods);if(!matched.ready)return base;
 const replacements=new Map(matched.rows.map(item=>[item.group[0].key,item]));
 const retained=base.filter(row=>!replacements.has(row.key));
 return [...retained,...matched.rows.map(item=>result(item.group,item.proof,item.title,base.find(r=>r.key===item.group[0].key),item.status))];
}
function match(category,model,instant){const data=matching(category,model,instant);return {...data,rows:data.rows.map(item=>result(item.group,item.proof,item.title,null,item.status))};}
window.KPSuppliedPredictions=Object.freeze({merge,match,title,metadata:()=>({...catalogue.metadata}),records:()=>JSON.parse(JSON.stringify(catalogue.records)),sources:()=>JSON.parse(JSON.stringify(catalogue.sources))});
function controls(){
 const panel=document.getElementById('pred-personal-panel');if(!panel)return;
 const button=document.createElement('button');button.type='button';button.id='pred-supplied-transit-refresh';button.className='pred-supplied-transit-refresh';button.textContent='Use selected Transit Chart';button.addEventListener('click',()=>{window.KPTransitChart.refresh();window.KPPersonalPredictions.refresh();});panel.prepend(button);
 const update=()=>{button.hidden=window.KPPersonalPredictions?.getData().category!=='transit-results';button.textContent=language()==='marathi'?'निवडलेल्या गोचर कुंडलीचे फल':'Use selected Transit Chart';for(const category of Object.keys(titles)){const b=document.getElementById('pred-tab-'+category);if(b)b.textContent=title(category);}};
 document.getElementById('pred-subtabs').addEventListener('click',()=>setTimeout(update,0));update();
 window.addEventListener('kp-preferences-changed',()=>{window.KPPersonalPredictions?.refresh();update();});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(controls,20));else setTimeout(controls,20);
})();
