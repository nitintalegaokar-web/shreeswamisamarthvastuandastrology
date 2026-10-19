/* Vedic presentation symbols. Reuses approved motion, combustion and relationship calculations. */
(function(root){'use strict';
const glyphs={Su:'☉',Mo:'☽',Ma:'♂',Me:'☿',Ju:'♃',Ve:'♀',Sa:'♄',Ra:'☊',Ke:'☋'},names={NatalAsc:['Natal Ascendant','जन्मलग्न'],As:['Ascendant','लग्न'],Su:['Sun','रवी'],Mo:['Moon','चंद्र'],Ma:['Mars','मंगळ'],Me:['Mercury','बुध'],Ju:['Jupiter','गुरु'],Ve:['Venus','शुक्र'],Sa:['Saturn','शनि'],Ra:['Rahu','राहू'],Ke:['Ketu','केतू']},signsEN=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'],signsMR=['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तूळ','वृश्चिक','धनु','मकर','कुंभ','मीन'];
const exalt={Su:10,Mo:33,Ma:298,Me:165,Ju:95,Ve:357,Sa:200},states={retrograde:['℞','Retrograde','वक्री'],direct:['↔','Direct','मार्गी'],combust:['☄','Combust','अस्त'],exalted:['↑','Exalted','उच्च'],'deep-exalted':['↑↑','Deep exaltation','परम उच्च'],debilitated:['↓','Debilitated','नीच'],'deep-debilitated':['↓↓','Deep debilitation','परम नीच'],friend:['+','Friend','मित्र'],enemy:['−','Enemy','शत्रू'],neutral:['*','Neutral','सम'],'great-friend':['++','Great friend','अधिमित्र'],'great-enemy':['−−','Great enemy','अधिशत्रू']};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),language=()=>root.KPPreferences?.get?.().language||'english',choose=(en,mr,lang=language())=>lang==='marathi'?mr:lang==='bilingual'?en+' · '+mr:en;
function describe(point,rows,model=root.currentKPModel,options={}){
 const id=point.id,math=root.KPVedicMath,markers=[];
 if(!glyphs[id])return markers;
 const notes=root.KPDisplay?.getNotations?.(id,model)||[];
 const add=key=>markers.push({key,symbol:states[key][0],label:choose(states[key][1],states[key][2])});
 if(options.motion!==false&&!['Ra','Ke'].includes(id))add(notes.includes('[R]')?'retrograde':'direct');
 if(options.motion!==false&&notes.includes('[C]'))add('combust');
 if(math.IDS.includes(id)){
  const dignity=math.dignity(id,point.sign),deep=point.factor===1&&Number.isFinite(point.longitude);
  if(dignity==='Exalted')add(deep&&math.angle(point.longitude,exalt[id])<=.5/3600?'deep-exalted':'exalted');
  if(dignity==='Debilitated')add(deep&&math.angle(point.longitude,math.mod(exalt[id]+180))<=.5/3600?'deep-debilitated':'debilitated');
  const owner=math.LORDS[point.sign],points=Object.fromEntries(rows.filter(p=>Number.isFinite(p.longitude)).map(p=>[p.id,p.longitude]));
  if(owner!==id&&Number.isFinite(points[id])&&Number.isFinite(points[owner])){const relation=math.compound(id,owner,points);if(states[relation])add(relation);}
 }
 return markers;
}
function badges(markers){return markers.map(m=>'<span class="v-planet-state" data-vedic-state="'+m.key+'" title="'+esc(m.label)+'" aria-label="'+esc(m.label)+'">'+m.symbol+'\ufe0e</span>').join(' ');}
function planet(point,rows,compact=false,options={}){const lang=language(),label=compact&&lang==='english'?point.id:choose(...(names[point.id]||[point.id,point.id])),markers=describe(point,rows,undefined,options);return '<span class="v-planet-symbol-label" data-no-localize data-vedic-planet="'+esc(point.id)+'"><span class="v-planet-glyph" aria-hidden="true">'+(glyphs[point.id]?glyphs[point.id]+'\ufe0e':'')+'</span> '+esc(label)+(compact&&markers.length?' <sup>'+badges(markers)+'</sup>':'')+'</span>';}
function signLabel(sign,compact=false){return '<span class="v-sign-symbol-label" data-no-localize><span class="v-sign-glyph" aria-hidden="true">'+String.fromCodePoint(0x2648+sign)+'\ufe0e'+'</span> '+esc(choose(compact?['Ar','Ta','Ge','Ca','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi'][sign]:signsEN[sign],signsMR[sign]))+'</span>';}
function positionTable(rows,options={}){const heads=[choose('Planet','ग्रह'),choose('Sign','राशी'),choose('Degree','अंश'),choose('House','भाव'),choose('Planetary properties','ग्रहाचे गुणधर्म')],asc=rows.find(p=>p.id==='As')?.sign??rows[0]?.sign;return '<div class="v-table-wrap"><table class="v-table v-symbol-positions" data-no-localize data-vedic-symbol-positions><thead><tr>'+heads.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(p=>'<tr data-vedic-position="'+esc(p.id)+'"><td>'+planet(p,rows,false,options)+'</td><td>'+signLabel(p.sign)+'</td><td>'+esc(root.KPDisplay.formatDegree(p.longitude*3600))+'</td><td>'+(root.KPVedicMath.mod(p.sign-asc,12)+1)+'</td><td>'+badges(describe(p,rows,undefined,options))+'</td></tr>').join('')+'</tbody></table></div>';}
root.KPVedicSymbols=Object.freeze({describe,planet,signLabel,positionTable});if(typeof module!=='undefined'&&module.exports)module.exports=root.KPVedicSymbols;
})(typeof window==='undefined'?globalThis:window);
