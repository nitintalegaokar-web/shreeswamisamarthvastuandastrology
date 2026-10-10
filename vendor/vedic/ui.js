(()=>{'use strict';const $=id=>document.getElementById(id),M=KPVedicMath,esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),SIGNS=['Ar','Ta','Ge','Ca','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi'],ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'],VARGA={1:'Rashi',2:'Hora',3:'Drekkana',4:'Chaturthamsa',7:'Saptamsa',9:'Navamsa',10:'Dasamsa',12:'Dwadashamsa',16:'Shodasamsa',20:'Vimsamsa',24:'Siddhamsa',27:'Nakshatramsa',30:'Trimsamsa',40:'Khavedamsa',45:'Akshavedamsa',60:'Shashtyamsa'};let active='chart',busy=false,preparing=null,autoTimer;
let chartStyle='south';try{chartStyle=localStorage.getItem('kpVedicChartStyleV1')==='north'?'north':'south';}catch(_){}
const DEFINITIONS=[['vedic-information','General information'],['vedic-rashi','Birth Kundali'],['vedic-cusps','Cuspal positions'],['vedic-vargas','Divisional charts · Shodashavarga'],['vedic-shadbala','Shadbala'],['vedic-bhava-bala','Bhava Bala'],['vedic-vimshopaka','Vimshopaka Bala'],['vedic-vaisheshika','Vaisheshikamsa'],['vedic-ashtakavarga','Bhinna Ashtakavarga'],['vedic-sarva','Sarvashtakavarga / Sarvatobhadra'],['vedic-shodhana','Ashtakavarga Shodhana'],['vedic-prastara','Prastara Ashtakavarga'],['vedic-ashtaka-summary','Ashtakavarga summary'],['vedic-aspects','Vedic aspect relationships'],['vedic-maitri','Graha Maitri'],['vedic-dasha-bhukti','Dasha / Bhukti'],['vedic-current-bhukti','Current Bhukti / Antara'],['vedic-current-antara','Current Antara / Sukshma'],['vedic-current-sukshma','Current Sukshma / Prana'],['vedic-ishta','Ishta / Kashta Phala'],['vedic-nakshatra','Birth Nakshatra results'],['vedic-pada','Birth Nakshatra Pada results'],['vedic-planets','Planet results'],['vedic-house-results','House Results · all twelve cusps'],['vedic-dasha-results','Dasha Results'],['vedic-remedies','Remedies'],['vedic-manglik','Manglik details'],['vedic-sade-sati','Sade Sati'],['vedic-varshaphal','Varshaphal']];
function table(head,rows,attrs=''){return '<div class="v-table-wrap"><table class="v-table" '+attrs+'><thead><tr>'+head.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function number(x){return Number.isFinite(x)?M.round(x):'—';}
function stamp(utc){const offset=KPVedic.core().native?.location.timezone||0;return new Date(Date.parse(utc)+offset*3600000).toISOString().slice(0,19).replace('T',' ');}
function civil(ms){return new Date(ms).toISOString().slice(0,19).replace('T',' ');}
function message(data){return '<p class="v-message">'+esc(data?.reason||'Complete the native kundali.')+'</p>';}
function chart(rows,title){
 const bySign=Array.from({length:12},()=>[]);for(const row of rows)bySign[row.sign].push(row.id);
 const planets=sign=>'<strong data-hover-detail="'+esc(SIGNS[sign]+' · '+bySign[sign].join(', '))+'">'+bySign[sign].map(id=>'<span>'+esc(id)+'</span>').join(' ')+'</strong>';
 if(chartStyle==='north'){
  const asc=rows.find(p=>p.id==='As')?.sign??rows[0].sign;
  const centres=[[50,24],[25,9],[9,26],[24,50],[9,74],[25,91],[50,76],[75,91],[91,74],[76,50],[91,26],[75,9]];
  return '<div class="v-chart v-chart-north" role="img" data-vedic-chart-style="north" aria-label="'+esc(title)+'"><svg class="v-north-lines" viewBox="0 0 100 100" aria-hidden="true"><path d="M0 0H100V100H0ZM0 0L100 100M100 0L0 100M50 0L100 50L50 100L0 50Z"/></svg><div class="v-north-title">'+esc(title)+'</div>'+centres.map(([x,y],i)=>{const sign=(asc+i)%12;return '<div class="v-north-house" data-vedic-sign="'+sign+'" data-vedic-house="'+(i+1)+'" style="left:'+x+'%;top:'+y+'%;width:'+([2,4,8,10].includes(i)?17:27)+'%"><small><span>'+SIGNS[sign]+'</span> · '+(sign+1)+'</small>'+planets(sign)+'</div>';}).join('')+'</div>';
 }
 const cells=[11,0,1,2,10,-1,-1,3,9,-1,-1,4,8,7,6,5];
 return '<div class="v-chart" role="img" data-vedic-chart-style="south" aria-label="'+esc(title)+'"><div class="v-chart-center">'+esc(title)+'</div>'+cells.map(r=>'<div class="v-chart-cell"'+(r<0?' data-empty="true"':' data-vedic-sign="'+r+'"')+'>'+(r>=0?'<small>'+SIGNS[r]+'</small>'+planets(r):'')+'</div>').join('')+'</div>';
}
function positionTable(rows){return table(['Planet','Sign','Degree','House'],rows.map(p=>[p.id,SIGNS[p.sign],KPDisplay.formatDegree(p.longitude*3600),M.mod(p.sign-rows[0].sign,12)+1]));}
function identity(data){return '<p class="v-native" data-no-localize>'+esc(data.native.name)+' · '+esc(stamp(data.native.date))+' · '+esc(data.native.location.place)+' · UTC '+esc(data.native.location.timezone)+'</p>';}
function paragraphs(rows){return rows.length?rows.map(row=>'<article class="v-prediction"><p>'+esc(row.text)+'</p></article>').join(''):'<p>No supplied rule matches this kundali for this section.</p>';}
function matches(category){return KPPersonalPredictions.matchRules(category).rows||[];}
function strengthTable(data){return data.bala.ready?table(['Planet','Sthana','Dig','Kala','Cheshta','Naisargika','Drik','Total','Rupas','Required','Ratio'],data.bala.rows.map(p=>[p.id,p.sthana,p.dig,p.kala,p.cheshta,p.naisargika,p.drik,p.total,p.rupas,p.minRupas,p.ratio]),'data-vedic-strength="true"'):message(data.bala);}
function binduTable(rows,labels){return table(['Planet',...SIGNS,'Total'],rows.map((row,i)=>[labels[i],...row,row.reduce((n,v)=>n+v,0)]));}
function subperiodReport(groups,title){if(!groups?.length)return '<p>No native periods are available in this range.</p>';return groups.map(group=>'<article class="v-period-block"><h3>'+esc(title+' · '+group.parent.lord)+' · '+esc(civil(group.parent.startMs))+' → '+esc(civil(group.parent.endMs))+'</h3>'+table(['Lord','Start','End (exclusive)'],group.children.map(p=>[p.lord,civil(p.startMs),civil(p.endMs)]))+'</article>').join('');}
function starFacts(data){const moon=KPDisplay.longitudeDetails(data.native.points.Mo*3600);return table(['Moon sign','Nakshatra','Pada','Star lord'],[[SIGNS[moon.signIndex],moon.nakshatra,moon.pada,moon.stl]]);}
function sarvatobhadra(data){
 const names=['Ashwini','Bharani','Krittika','Rohini','Mrigashirsha','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati','Abhijit'];
 const labels=[['ii',23,24,25,26,27,1,2,'a'],[22,'rii','g','s','d','ch','l','u',3],[28,'kh','ai',11,12,1,'lu','a',4],[21,'j',10,'ah','Rikta · Friday','o',2,'v',5],[20,'bh',9,'Jaya · Thursday','Purna · Saturday','Nanda · Sunday / Tuesday',3,'k',6],[19,'y',8,'am','Bhadra · Monday / Wednesday','au',4,'h',7],[18,'n','e',7,6,5,'luu','d',8],[17,'ri','t','r','p','t~','m','uu',9],['i',16,15,14,13,12,11,10,'aa']];
 const occupancy=Array.from({length:28},()=>[]);for(const [id,longitude] of Object.entries(data.native.points)){const lon=M.mod(longitude),index=lon>=276+40/60&&lon<280+53/60+20/3600?27:Math.floor(lon/(40/3));occupancy[index].push(id);}
 return '<div class="v-sbc" role="table" aria-label="Sarvatobhadra Chakra">'+labels.flatMap((row,r)=>row.map((value,c)=>{const outer=r===0||r===8||c===0||c===8,numeric=typeof value==='number',text=numeric?(outer?names[value-1]:SIGNS[value-1]):value,planets=numeric&&outer?occupancy[value-1]:[];return '<div role="cell" class="v-sbc-cell"'+(numeric&&outer?' data-nakshatra="'+value+'"':'')+'><span>'+esc(text)+'</span>'+(planets.length?'<strong>'+planets.map(id=>'<span>'+esc(id)+'</span>').join(' ')+'</strong>':'')+'</div>';})).join('')+'</div>';
}
function contents(section,data){if(!data?.ready)return [message(data)];const ast=data.ashtaka,rows=data.vargas[1],allGeneral=()=>matches('general-predictions');
 switch(section){case 'vedic-information':if(window.KPBasicInformation)return [KPBasicInformation.snapshot()];return [identity(data)+starFacts(data)+table(['Ayanamsha','Latitude','Longitude'],[[number(data.native.ayanamsha),data.native.location.latitude,data.native.location.longitude]])];
 case 'vedic-rashi':return ['<div class="v-chart-layout">'+chart(rows,'D1 · Rashi')+positionTable(rows)+'</div>'];
 case 'vedic-cusps':return [table(['Cusp','Sign','Position','Star','Sub'],currentKPModel.houses.map(p=>[ROMAN[p.id-1],p.signCode,p.degree,p.stl,p.sl]))];
 case 'vedic-vargas':return [0,8].map(start=>'<div class="v-varga-print-grid">'+M.DIVISIONS.slice(start,start+8).map(d=>'<article>'+chart(data.vargas[d],'D'+d+' · '+VARGA[d])+'</article>').join('')+'</div>');
 case 'vedic-shadbala':return [strengthTable(data)];
 case 'vedic-bhava-bala':return [data.bala.ready?table(['House','Sign','Lord','Adhipati','Dig','Drik','Total','Rupas'],data.bala.houses.map(p=>[ROMAN[p.house-1],SIGNS[p.sign],p.owner,p.adhipati,p.dig,p.drik,p.total,p.rupas])):message(data.bala)];
 case 'vedic-vimshopaka':return [table(['Planet','Shadvarga /20','Saptavarga /20','Dashavarga /20','Shodashavarga /20'],data.divisionStrength.map(p=>[p.id,p.vimshopaka[6],p.vimshopaka[7],p.vimshopaka[10],p.vimshopaka[16]]))];
 case 'vedic-vaisheshika':return [table(['Planet','Favorable divisions /16','Own / exalted divisions'],data.divisionStrength.map(p=>[p.id,p.vaisheshika,p.favorable.map(d=>'D'+d).join(', ')]))];
 case 'vedic-ashtakavarga':return [binduTable(ast.bhinna,M.IDS)];
 case 'vedic-sarva':return [table(['Sign',...SIGNS,'Total'],[['SAV',...ast.sarva,ast.total]])+'<h3>Sarvatobhadra Chakra</h3>'+sarvatobhadra(data)];
 case 'vedic-shodhana':return ['<h3>Trikona reduction</h3>'+binduTable(ast.trikona,M.IDS)+'<h3>Ekadhipatya reduction</h3>'+binduTable(ast.ekadhipatya,M.IDS)];
 case 'vedic-prastara':return [0,4].map(start=>M.IDS.slice(start,start+4).map((id,j)=>'<h3>'+id+' · Prastara</h3>'+binduTable(ast.prastara[start+j],[...M.IDS,'As'])).join(''));
 case 'vedic-ashtaka-summary':return [table(['Planet','Rashi Pinda','Graha Pinda','Shodhya Pinda'],ast.pinda.map(p=>[p.id,p.rasi,p.graha,p.total]))+'<h3>Sarvashtakavarga · '+ast.total+'</h3>'+table(['Sign','Bindus'],ast.sarva.map((v,r)=>[SIGNS[r],v]))];
 case 'vedic-aspects':return [table(['Planet','Sign aspects','Planets aspected'],codes().map(id=>{const r=M.sign(data.native.points[id]),houses=id==='Ma'?[4,7,8]:id==='Ju'?[5,7,9]:id==='Sa'?[3,7,10]:[7],targets=houses.map(h=>M.mod(r+h-1,12));return [id,targets.map(s=>SIGNS[s]).join(', '),codes().filter(p=>p!==id&&targets.includes(M.sign(data.native.points[p]))).join(', ')];}))];
 case 'vedic-maitri':return ['<h3>Natural relationships</h3>'+table(['Planet',...M.IDS],data.relationships.map(p=>[p.id,...p.relations.map(r=>r.natural)]))+'<h3>Compound relationships · native Rashi</h3>'+table(['Planet',...M.IDS],data.relationships.map(p=>[p.id,...p.relations.map(r=>r.compound)]))];
 case 'vedic-dasha-bhukti':return [data.dasha.ready?subperiodReport(data.dasha.all,'Dasha / Bhukti'):message(data.dasha)];
 case 'vedic-current-bhukti':return [data.dasha.ready?subperiodReport(data.dasha.bhukti,'Bhukti / Antara'):message(data.dasha)];
 case 'vedic-current-antara':return [data.dasha.ready?subperiodReport(data.dasha.antara,'Antara / Sukshma'):message(data.dasha)];
 case 'vedic-current-sukshma':return [data.dasha.ready?subperiodReport(data.dasha.sukshma,'Sukshma / Prana'):message(data.dasha)];
 case 'vedic-ishta':return [data.bala.ready?table(['Planet','Ishta Phala','Kashta Phala'],data.bala.rows.map(p=>[p.id,p.ishta,p.kashta])):message(data.bala)];
 case 'vedic-nakshatra':return [starFacts(data)+paragraphs(allGeneral().filter(r=>/^(?:nak\d+|Nak\d+R\d+)$/i.test(r.key)))];
 case 'vedic-pada':return [starFacts(data)+paragraphs(allGeneral().filter(r=>/^Nak\d+C[1-4]$/i.test(r.key)))];
 case 'vedic-planets':return [paragraphs(allGeneral().filter(r=>/^(?:Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)In/.test(r.key)))];
 case 'vedic-house-results':{const matched=matches('house-results');return Array.from({length:12},(_,i)=>'<h3>Cusp '+ROMAN[i]+'</h3>'+paragraphs(matched.filter(r=>Number(/^Bh(1[0-2]|[1-9])R/i.exec(r.key)?.[1])===i+1)));}
 case 'vedic-dasha-results':return [paragraphs(matches('dasha-results'))];
 case 'vedic-remedies':return [paragraphs(matches('mahadasha-remedies'))];
 case 'vedic-manglik':return [table(['Reference','Mars house','Manglik screening'],data.manglik.map(p=>[p.base,p.house,p.flagged?'Present':'Absent']))+'<p>Mars is checked in houses 1, 2, 4, 7, 8 and 12. Cancellation is not assumed.</p>'];
 case 'vedic-sade-sati':{const phase={rising:'Rising phase',peak:'Middle phase',setting:'Setting phase',outside:'Outside Sade Sati'};return ['<article data-vedic-sade-report><h3>Sade Sati</h3>'+(data.sade.ready?'<p><strong>Current phase:</strong> <span>'+esc(phase[data.sade.current]||data.sade.current)+'</span> · <span>Birth Moon</span>: <span>'+SIGNS[data.sade.moonSign]+'</span></p>'+table(['Phase','Entry','Exit (exclusive)'],data.sade.rows.map(p=>[phase[p.trackId]||p.label,stamp(p.start)+(p.startClipped?' · range limit':''),stamp(p.end)+(p.endClipped?' · range limit':'')])):message(data.sade))+'</article>'];}
 case 'vedic-varshaphal':{const a=data.annual;if(!a.ready)return [message(a)];return ['<h3>Sidereal solar return · '+a.year+'</h3><p>'+esc(stamp(a.date))+' → '+esc(stamp(a.next))+'</p><div class="v-chart-layout">'+chart(a.chart,'Varshaphal · '+a.year)+positionTable(a.chart)+'</div>',table(['Year','Completed age','Muntha','Muntha house','Muntha lord','Annual Ascendant lord','Natal Ascendant lord','Day / night lord'],[[a.year,a.age,SIGNS[a.muntha],a.munthaHouse,a.munthaLord,a.annualAscLord,a.natalAscLord,a.dayNightLord]]),'<h3>Mudda Vimshottari</h3>'+table(['Lord','Start','End (exclusive)'],a.mudda.map(p=>[p.id,stamp(p.start),stamp(p.end)]))];}
 default:return [];
 }}
function codes(){return [...M.IDS,'Ra','Ke'];}
function renderReports(){const mount=$('printReport');if(!mount)return;mount.querySelectorAll('[data-vedic-report]').forEach(p=>p.remove());const data=KPVedic.core();for(const [id,title] of DEFINITIONS){const blocks=contents(id,data);blocks.forEach((html,index)=>{const page=document.createElement('section');page.className='report-page v-report-page';page.dataset.reportSection=id;page.dataset.vedicReport='true';page.innerHTML='<h2 class="report-page-title">'+esc(title)+(blocks.length>1?' · '+(index+1)+' / '+blocks.length:'')+'</h2>'+(data.ready?identity(data):'')+'<div class="v-report-content">'+html+'</div>';mount.append(page);});}}
function refresh(){
 const data=KPVedic.core(),mount=$('v-results');if(!mount)return;
 if(!busy)$('v-status').textContent=data.ready?'Vedic calculations from the native kundali':data.reason;
 let html;if(!data.ready)html=message(data);else if(active==='chart'){const d=Number($('v-division').value),rows=data.vargas[d];html='<div class="v-chart-layout">'+chart(rows,'D'+d+' · '+VARGA[d])+positionTable(rows)+'</div>';}
 else if(active==='strength')html=contents('vedic-shadbala',data).join('')+contents('vedic-bhava-bala',data).join('');
 else if(active==='ashtaka')html=contents('vedic-ashtakavarga',data).join('')+contents('vedic-ashtaka-summary',data).join('');
 else html=contents(active==='sade'?'vedic-sade-sati':'vedic-varshaphal',data).join('');
 mount.innerHTML=html;$('v-division-wrap').hidden=active!=='chart';$('v-year-wrap').hidden=active!=='annual';
 for(const b of document.querySelectorAll('[data-v-tab]'))b.setAttribute('aria-pressed',String(b.dataset.vTab===active));
 $('vedic-kundali-preview').disabled=!data.ready;
 $('vedic-kundali').setAttribute('aria-busy',String(busy));$('report').setAttribute('aria-busy',String(busy));
 window.KPLanguage?.localize($('vedic-kundali'));
}
function needsPreparation(){return KPVedic.core().ready&&!KPVedic.core().calculated;}
async function prepareReports(){
 if(preparing)return preparing;
 if(!needsPreparation())return KPVedic.core();
 busy=true;$('v-status').textContent='Preparing selected reports…';$('report-vedic-message').textContent='Preparing selected reports…';$('report-vedic-status').hidden=false;for(const id of ['v-progress','report-vedic-progress']){$(id).hidden=false;$(id).value=0;}let progressAt=0;
 preparing=(async()=>{try{
  let data;do{const signature=KPVedic.core().signature;data=await KPVedic.calculate(p=>{const now=performance.now();if(now-progressAt<200&&p<1)return;progressAt=now;for(const id of ['v-progress','report-vedic-progress'])$(id).value=Math.round(p*100);});if(signature===KPVedic.core().signature)break;}while(KPVedic.core().ready);
  return data;
 }finally{busy=false;preparing=null;refresh();renderReport();KPReportPages.refresh();for(const id of ['v-progress','report-vedic-progress'])$(id).hidden=true;$('report-vedic-message').textContent=KPVedic.core().calculated?'Vedic reports ready':KPVedic.core().reason||'';window.KPLanguage?.localize($('report-vedic-status'));}})();
 refresh();return preparing;
}
function selectedNeedsPreparation(){return KPReportPages.selected().some(p=>['vedic-sade-sati','vedic-varshaphal'].includes(p.dataset.reportSection));}
function automatic(){clearTimeout(autoTimer);autoTimer=setTimeout(()=>{if((($('vedic-kundali').classList.contains('active'))||($('report').classList.contains('active')&&selectedNeedsPreparation()))&&needsPreparation())prepareReports().catch(e=>{$('v-status').textContent=e.message;$('report-vedic-message').textContent=e.message;});},0);}
function snapshot(){const data=KPVedic.core();return '<div class="v-report">'+(data.ready?identity(data):'')+($('v-results')?.innerHTML||message(data))+'</div>';}
function closeMenu(){$('v-chart-menu').hidden=true;}
function setChartStyle(style){if(!['north','south'].includes(style))return false;chartStyle=style;try{localStorage.setItem('kpVedicChartStyleV1',style);}catch(_){}closeMenu();refresh();renderReport();return true;}
function init(){const section=$('vedic-kundali');section.innerHTML='<article class="v-window"><header><h2>Vedic Kundali</h2><button id="vedic-kundali-preview" type="button">Preview · Print / Save PDF</button></header><div class="v-toolbar"><div class="v-tabs"><button data-v-tab="chart" aria-pressed="true">Kundali</button><button data-v-tab="strength">Strengths</button><button data-v-tab="ashtaka">Ashtakavarga</button><button data-v-tab="sade">Sade Sati</button><button data-v-tab="annual">Annual</button></div><label id="v-division-wrap">Division<select id="v-division">'+M.DIVISIONS.map(d=>'<option value="'+d+'">D'+d+' · '+VARGA[d]+'</option>').join('')+'</select></label><label id="v-year-wrap" hidden>Annual year<input id="v-year" type="number" min="1901" max="2099" value="'+Math.max(new Date().getUTCFullYear(),Number($('dob').value.slice(0,4))+1)+'"></label></div><p id="v-status" role="status"></p><progress id="v-progress" max="100" aria-label="Preparing selected reports…" hidden></progress><div id="v-results"></div><details class="v-conventions"><summary>Calculation details</summary><p>Traditional Parashari divisions and whole-sign houses use the native sidereal planets and Ascendant. Strengths use the seven classical planets; solar time and declination come from the birth moment. Shadbala uses virupas, with 60 virupas per rupa. Saturn phase intervals and the sidereal solar return are refined to one second. Mudda periods span the calculated solar-return year.</p></details></article><div id="v-chart-menu" class="v-chart-menu no-print" role="menu" hidden><button type="button" role="menuitemradio" data-v-chart-style="north">North Indian kundali</button><button type="button" role="menuitemradio" data-v-chart-style="south">South Indian kundali</button></div>';
 section.addEventListener('click',e=>{const style=e.target.closest('[data-v-chart-style]');if(style){setChartStyle(style.dataset.vChartStyle);return;}const tab=e.target.closest('[data-v-tab]');if(tab){active=tab.dataset.vTab;refresh();automatic();}});
 section.addEventListener('contextmenu',e=>{if(!e.target.closest('.v-chart'))return;e.preventDefault();const menu=$('v-chart-menu');menu.hidden=false;for(const b of menu.querySelectorAll('[data-v-chart-style]'))b.setAttribute('aria-checked',String(b.dataset.vChartStyle===chartStyle));menu.style.left=Math.max(8,Math.min(innerWidth-220,e.clientX))+'px';menu.style.top=Math.max(8,Math.min(innerHeight-90,e.clientY))+'px';});
 document.addEventListener('pointerdown',e=>{if(!e.target.closest('#v-chart-menu'))closeMenu();});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});window.addEventListener('scroll',closeMenu,{passive:true});
 $('v-division').addEventListener('change',refresh);$('v-year').addEventListener('change',()=>{KPVedic.cancel();refresh();automatic();});$('vedic-kundali-preview').addEventListener('click',()=>KPSelectedReport.preview(false,{vedic:true}));
 const old=window.renderReport;window.renderReport=function(...args){const result=old.apply(this,args);renderReports();return result;};
 const status=document.createElement('p');status.id='report-vedic-status';status.setAttribute('role','status');status.className='report-vedic-status';status.hidden=true;status.innerHTML='<span id="report-vedic-message"></span> <progress id="report-vedic-progress" max="100" aria-label="Preparing selected reports…" hidden></progress>';$('report').querySelector('.report-selection-window h2')?.after(status);
 $('report-page-options').addEventListener('change',automatic);$('report-all-toggle').addEventListener('change',automatic);
 new MutationObserver(()=>{if(section.classList.contains('active')){refresh();automatic();}}).observe(section,{attributes:true,attributeFilter:['class']});
 new MutationObserver(automatic).observe($('report'),{attributes:true,attributeFilter:['class']});
 const nativeUpdated=()=>{if(section.classList.contains('active')||$('report').classList.contains('active')){refresh();automatic();}};
 const nativeStatus=$('kp-status');if(nativeStatus)new MutationObserver(nativeUpdated).observe(nativeStatus,{childList:true,subtree:true});
 for(const event of ['chart-saved','chart-manual-change'])window.addEventListener(event,nativeUpdated);
 window.addEventListener('kp-preferences-changed',()=>{refresh();automatic();});window.addEventListener('vedic-calculated',refresh);
 refresh();renderReport();KPReportPages.refresh();
}
window.KPVedicUI=Object.freeze({refresh,snapshot,contents,sarvatobhadra,renderReports,definitions:DEFINITIONS,prepareReports,needsPreparation,setChartStyle,getChartStyle:()=>chartStyle,needsViewPreparation:()=>['annual','sade'].includes(active)});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,0));else init();})();
