/* Calculable restrictions from the user's 70-entry Panchang notebook.
 * No medical, supernatural-affliction or character claims are used as findings.
 */
(function(root){'use strict';
const allN=Array.from({length:27},(_,i)=>i),allD=[0,1,2,3,4,5,6],allT=Array.from({length:30},(_,i)=>i+1),goodD=[1,3,4,5],goodT=[2,3,5,7,10,12,13],notRikta=allT.filter(t=>![4,9,14].includes((t-1)%15+1)),U=[11,20,25];
const specs=[];
function add(id,en,mr,source,nak=allN,week=goodD,tithi=goodT,extra={}){specs.push({id,en,mr,kind:'supplied',eventId:null,nakshatras:nak,weekdays:week,tithis:[...new Set(tithi.map(t=>(t-1)%15+1))],absoluteTithis:tithi===goodT?goodT.flatMap(t=>[t,t+15]):tithi,sources:[source],...extra});}
add('new-stove','Lighting a new stove / gas burner','नवी चूल / गॅस प्रज्वलन',9,[2,4,6,7,9,14,15,17,21],[0,1,2,3,4,5]);
for(const [id,en,mr] of [['grass-timber','Grass and timber collection','तृणकाष्ठ संग्रह'],['roof-thatching','Roof thatching','घर शाकारणे'],['cot-weaving','Cot and bed weaving','बाज-पलंग विणणे']])add(id,en,mr,10,allN,allD,allT,{panchakMoon:true});
for(const id of ['travel','overseas','pilgrimage'])add(id,id==='travel'?'Start a journey':id==='pilgrimage'?'Pilgrimage / sacred bathing':'Overseas journey',id==='travel'?'प्रवास प्रारंभ':id==='pilgrimage'?'तीर्थयात्रा / तीर्थस्नान':'परदेश प्रवास',17,[0,3,4,7,11,12,16,18,20,21,22,25,26],goodD,goodT,{excludeBirthStar:true,reviews:[16,18,19,63],priority:'Ve'});
add('machinery-start','Start machinery / oil or sugar mill','यंत्रकृत्य प्रारंभ',20,[0,6,7,12,13,16,17,22,26]);
add('grain-storage','Grain storage','धान्य संग्रह',21,[0,3,4,7,...U,12,13,16,18,26]);
add('grain-threshing','Grain threshing','धान्य मळणी',21,[3,9,10,11,16,17,18,21,26]);
add('orchard-planting','Planting an orchard / banana garden','फळबाग / केळीची बाग',22,[0,3,7,...U,12,13,16,18,26],[0,1,3,4,5],notRikta.filter(t=>t!==30),{uttarayana:true});
add('sugarcane-planting','Sugarcane planting','ऊस लागवड',23,[5,7,...U,16,18,22,23,26],[0,2],goodT);
add('grain-harvest','Harvesting grain','धान्य कापणी',24,allN.filter(n=>![0,3,10,15,16,23,26].includes(n)),[0,1,3,4,5],notRikta);
for(const id of ['farming','seed-sowing'])add(id,id==='farming'?'Sowing / farming':'Seed sowing',id==='farming'?'पेरणी / शेती':'बीज पेरणी',25,[0,3,4,7,9,...U,12,13,14,16,18,22,26],goodD,goodT,{reviews:[25]});
add('ploughing','First ploughing','प्रथम नांगर धरणे',26,[0,3,4,6,7,9,...U,12,13,14,15,16,18,21,22,23,26]);
add('livestock-trade','Buying / selling livestock','जनावरांची देवघेव',27,[0,6,7,12,15,17,22,23,26]);
for(const id of ['buying-goods','vehicle','investment','property'])add(id,({vehicle:'Vehicle purchase',investment:'New investment',property:'Property purchase'})[id]||'Buying goods',({vehicle:'वाहन खरेदी',investment:'नवीन गुंतवणूक',property:'मालमत्ता खरेदी'})[id]||'वस्तू खरेदी',31,[0,13,14,21,23,26],goodD,goodT,{reviews:[29]});
add('selling-goods','Selling goods','वस्तू विक्री',31,[1,2,8,10,15,19,24]);
add('well-digging','Digging a well / pond','विहीर / तलाव खोदणे',33,[3,4,5,6,7,9,...U,12,13,14,16,21,22,23,26],goodD,goodT,{combust:true});
add('vastu-shanti','Vastu Shanti','वास्तुशांति',34,[0,3,4,6,7,...U,12,13,14,16,18,21,22,23,26],[1,3,4,5,6],allT.filter(t=>![1,4,9,14].includes((t-1)%15+1)&&t!==30),{months:[1,2,4,7,8,9,10,11],combust:true,reviews:[34,66]});
add('door-frame','Installing a door frame','दाराची चौकट बसविणे',35,[0,3,4,7,...U,12,14,21,26],goodD,goodT,{fixed:true});
for(const id of ['business','shop'])add(id,id==='business'?'Business opening':'Shop opening',id==='business'?'व्यवसाय प्रारंभ':'दुकान प्रारंभ',37,[0,3,4,7,11,12,13,16,26],[5],goodT,{requireChandra:true,eventId:46});
add('new-vow','New vow / Udyapan','नवे व्रत / उद्यापन',56,allN,goodD,goodT,{reviews:[56]});
add('chaul','Chaul / Chudakarana ceremony','चौल / चूडाकरण',54,allN,goodD,goodT,{combust:true,reviews:[44,56,60,62]});
add('mantra-initiation','Mantra initiation / Guru instruction','मंत्रदीक्षा / गुरु उपदेश',19,allN,goodD,goodT,{combust:true,reviews:[54,56],priority:'Sa'});
add('homa','Homa / fire offerings','होम / आहुती',39,allN,goodD,goodT,{grahaMouth:true,combust:true,reviews:[38]});
add('shanti-fire','Shanti fire ritual','शांतिकर्म अग्नी',40,allN,goodD,goodT,{earthFire:true});
add('adoption','Adoption ceremony','दत्तकविधान',42,[0,7,12,13,14,15,16,22],[0,2,4,5],notRikta,{fixed:true});
add('samavartana','Samavartana / graduation ceremony','समावर्तन / सोडमुंज',43,[3,4,6,7,...U,12,13,15,16,21,26],goodD,[2,3,5,6,7,10,11,12,13,17,18,20,21,22,25,26,27,28],{uttarayana:true,reviews:[43]});
add('mundan','First haircut / Javal','प्रथम केशखंडन / जावळ',44,[0,4,6,7,12,13,14,21,22,23,26],goodD,[3,5,10,13,18,20,25,28],{reviews:[44,54,56,60,62]});
add('feeding','Annaprashan','अन्नप्राशन',45,[0,3,4,5,6,7,...U,12,13,14,16,21,22,23,26],goodD,goodT,{childAge:'feeding',reviews:[60,62]});
add('ear-piercing','Ear piercing / Karnavedha','कर्णवेध',46,[0,4,6,7,...U,12,13,21,22,26],goodD,goodT,{childAge:'ears',reviews:[60,62]});
add('postnatal-temple','Postnatal temple visit','बाळंतिणीचे देवदर्शन',47,[0,4,6,7,12,16,21,22,26],goodD,[2,3,5,7,10,11,13,17,18,20,22,25,26,28],{childAge:'temple'});
add('birth-shanti','Birth Shanti (12th day)','बाराव्या दिवशी जननशांति',49,allN,goodD,goodT,{childAge:'cradle',reviews:[49],earthFire:false});
add('cradle','Cradle ceremony','पालकारोहण',48,allN,allD,allT.filter(t=>t!==30),{childAge:'cradle',reviews:[48],simplePurity:true});
add('baby-shower','Baby shower / Dohale Jevan','ओटी भरणे / डोहाळजेवण',50,[0,4,6,7,12,16,18,21],[0,2,4],allT.filter(t=>t<=20));
add('conception','Garbhadhana ceremony','गर्भाधान / फलशोभन',51,allN.filter(n=>![9,17,18,26].includes(n)),goodD,allT.filter(t=>![4,6,8,14,15].includes((t-1)%15+1)),{excludeBirthStar:true,excludeBirthWeekday:true,requireChandra:true,female:true,reviews:[51],combust:false});
add('wash-new-clothes','Washing new clothes','नवे वस्त्रक्षालन',52,[0,6,7,12,13,14,15,16,22],[0,1,2,4,5],allT.filter(t=>![4,6,9,14,15].includes((t-1)%15+1)),{noSankranti:true});
add('wear-new-clothes','Wearing new clothes','नवीन वस्त्रधारण',53,[0,6,7,...U,12,13,14,15,16,26],[3,4,5],notRikta);
add('bodan','Bodan family ritual','बोडण',55,allN,allD,allT,{simplePurity:true,combust:false,reviews:[55]});
// Named festival dates are screened separately from ordinary ceremony purity.
add('sade-teen','Three and a half auspicious days','साडेतीन मुहूर्त',30,allN,allD,allT,{festivalOnly:true,simplePurity:true,reviews:[30]});
const specialSources={marriage:[54,57,60,62,63,66],upanayan:[54,56,57,60,62,66],education:[54,60], 'higher-study':[54],construction:[54,56], 'house-entry':[54,63,67],installation:[54],puja:[38,39,40],naming:[60,62],engagement:[29,57,62,66]};
function merge(base){const out=base.map(p=>{const spec=specs.find(s=>s.id===p.id);return spec?{...p,...spec,eventId:spec.eventId??p.eventId}: {...p,tithis:goodT,absoluteTithis:goodT.flatMap(t=>[t,t+15])};});for(const spec of specs)if(!out.some(p=>p.id===spec.id))out.push({...spec});for(const p of out){if(specialSources[p.id]){p.sources=[...new Set([...(p.sources||[]),...specialSources[p.id]])];p.reviews=[...new Set([...(p.reviews||[]),...specialSources[p.id].filter(i=>![54].includes(i))])];}if(['marriage','upanayan','education','higher-study','construction','house-entry','installation','pilgrimage'].includes(p.id))p.combust=true;p.sources=[...new Set([19,61,...(p.sources||[])])];p.priority??=({marriage:'Ju',appointment:'Su',education:'Me','higher-study':'Me'})[p.id]||null;p.supplied=Boolean(p.sources?.length);if(p.supplied)p.sources=[...new Set([64,...p.sources])];}return out;}
function festival(p,month){return !month?.adhika&&((month?.index===0&&p.tithiIndex===0)||(month?.index===1&&p.tithiIndex===2)||(month?.index===6&&p.tithiIndex===9)||(month?.index===7&&p.tithiIndex===0));}
function combust(points,ms){const angle=(a,b)=>Math.abs(((a-b+540)%360)-180),out=[];if(angle(points.Ju,points.Su)<11)out.push('Ju');const a=angle(points.Ve,points.Su);if(a<8)out.push('Ve');else if(a<10){const before=root.KPEphemeris.longitude(new Date(ms-86400000),'Ve'),after=root.KPEphemeris.longitude(new Date(ms+86400000),'Ve');if(((after-before+540)%360)-180>=0)out.push('Ve');}return out;}
function check(f,day,profile,native,context={}){const reasons=[],review=[],p=f.p,points=f.positions,absolute=p.tithiIndex+1;
if(!f.festival&&profile.absoluteTithis&&!profile.absoluteTithis.includes(absolute))reasons.push('Supplied tithi restriction');
if(profile.panchakMoon&&((p.nakIndex===22&&points.Mo>=300)||p.nakIndex>=23))reasons.push('Grass / timber Panchak restriction');
if(profile.fixed&&![1,4,7,10].includes(f.ruleLagna))reasons.push('Fixed Lagna required');
if(profile.uttarayana&&!(points.Su>=270||points.Su<90)){if(profile.id==='samavartana'&&context.weddingException)review.push('Samavartana: marriage-related Dakshinayana exception selected');else reasons.push('Uttarayana required (sidereal Makara–Mithuna)');}
if(profile.months){if(!f.month)review.push('Lunar month calculation unavailable');else if(f.month.adhika||!profile.months.includes(f.month.index))reasons.push('Supplied lunar month restriction');}
if(profile.festivalOnly&&!(day.sadeTeen??festival(p,f.month)))reasons.push('Not a supplied Sade Teen festival tithi');
if(profile.noSankranti&&day.sankranti)reasons.push('Sankranti day excluded');
if(profile.combust){const c=f.vedic?.combust||combust(points,f.ms);if(['marriage','upanayan'].includes(profile.id)?c.includes('Ju')&&c.includes('Ve'):c.includes('Ju')||c.includes('Ve'))reasons.push('Jupiter / Venus combustion restriction');}
if(profile.earthFire&&![0,3].includes((absolute+day.weekday+2)%4))reasons.push('Agni Vasa not earthly');
if(profile.grahaMouth){const sunNak=Math.floor(points.Su/(360/27)),count=((p.nakIndex-sunNak+27)%27),lord=['Su','Me','Ve','Sa','Mo','Ma','Ju','Ra','Ke'][Math.floor(count/3)],benefics=root.KPVedicMath.benefics(points);if(!benefics.has(lord))reasons.push('Homa Graha Mukha is not benefic');}
if(profile.excludeBirthStar){if(native.ready){if(p.nakIndex===native.birthNak)reasons.push('Birth nakshatra excluded');}else review.push('Birth nakshatra required');}
if(profile.requireChandra){if(native.ready){const h=(p.moonSignIndex-native.birthSign+12)%12+1,good=root.KPMuhurtaNirnay.strength(p,native.birthSign,native.birthNak).chandra,pushya=p.nakIndex===7&&profile.id!=='marriage'&&[4,8,12].includes(h);if(!good&&!pushya)reasons.push('Required Chandrabala absent');}else review.push('Birth Rashi required for Chandrabala');}
if(profile.excludeBirthWeekday){if(context.birthDate){if(new Date(context.birthDate+'T12:00Z').getUTCDay()===day.weekday)reasons.push('Birth weekday excluded');}else review.push('Birth date required to exclude birth weekday');}
if(profile.childAge){if(!context.birthDate)review.push('Child birth date required for ceremony age');else{const start=Date.parse(context.birthDate+'T00:00Z'),date=Date.parse(day.date+'T00:00Z'),ageDay=Math.round((date-start)/86400000)+1,b=new Date(start),d=new Date(date);let months=(d.getUTCFullYear()-b.getUTCFullYear())*12+d.getUTCMonth()-b.getUTCMonth();if(d.getUTCDate()<b.getUTCDate())months--;const good=({ears:ageDay===12||ageDay===16,cradle:ageDay===12,feeding:months===5||months===7,temple:ageDay===12||months===2||months===3})[profile.childAge];if(!good)reasons.push('Supplied ceremony age restriction');}}
if(f.ruleLagna!==null&&f.ruleLagna!==undefined){const remainder=(p.tithiIndex+f.ruleLagna+1)%9;if([1,2,4,6,8].includes(remainder))review.push('Panchak '+remainder+': strong-Lagna exception requires individual assessment');}
if(profile.priority&&native.ready&&root.KPMuhurtaNirnay){const g=root.KPMuhurtaNirnay.graha(points,native.birthSign).find(g=>g.id===profile.priority);if(g&&!g.favourable)review.push(profile.priority+' Grahabala is not favourable; traditional remedy / ceremony review required');}
if(['travel','overseas','pilgrimage'].includes(profile.id)){if(!context.direction)review.push('Travel direction required for Kaal Rahu and Moon direction');else{const directions=['E','S','W','N'],heading=directions.indexOf(context.direction),kaal=[0,1,2,3,0,1,3][day.weekday],moon=[0,1,2,3][p.moonSignIndex%4];if(kaal===heading||kaal===(heading+1)%4)reasons.push('Kaal Rahu in front / to the right');if(!(moon===heading||moon===(heading+1)%4))reasons.push('Moon behind / to the left');}}
for(const i of profile.reviews||[])review.push(({25:'Phani Chakra: adverse / thief nakshatras must be checked',34:'Kalash / Vrisha Chakra must be checked',43:'Samavartana regional and emergency exceptions require review',51:'Parents’ Shraddha day and preceding day must be checked',60:'First-born birth month / star / weekday restrictions must be checked',62:'Sibling ceremony order and timing must be checked',66:'Family Ashaucha and ceremony prerequisites must be checked'})[i]||root.KPMuhurtaSuppliedData.entries[i].title);
if(['travel','overseas','pilgrimage'].includes(profile.id)&&[3,11,18,20,25].includes(p.nakIndex))review.push('Medium-quality journey nakshatra in supplied rule');
if(profile.id==='samavartana')review.push('Tuesday / Saturday emergency exception and Upanayan alternative require individual review');
if(profile.id==='cradle'&&day.sankranti)review.push('Check actual Sankranti Punyakala; entire day is not automatically rejected');
return {qualifies:!reasons.length,reasons,review:[...new Set(review)],sourceIndices:profile.sources||[]};}
function sourceHTML(profile,mr=false){if(!profile.sources?.length)return '';const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));return '<details class="mu-supplied-sources"><summary>'+(mr?'दिलेल्या पंचांग नियमांचा आधार':'Supplied Panchang rule references')+' · '+profile.sources.length+'</summary>'+profile.sources.map(i=>{const r=root.KPMuhurtaSuppliedData.entries[i];return '<h4>'+esc(r.title)+'</h4><p>'+esc(r.description)+'</p>';}).join('')+'</details>';}
root.KPMuhurtaSupplied={merge,check,festival,combust,sourceHTML,specs:()=>structuredClone(specs)};
})(globalThis);
