
(function () {
 'use strict';
 const KEY='kpRaphaelSoftwarePreferencesV1';
 const DEFAULTS=Object.freeze({shortcutHome:true,shortcutNatal:true,shortcutHorary:true,shortcutInstant:true,shortcutOpen:true,shortcutTransit:true,shortcutRP:true,shortcutEphemeris:true,shortcutSettings:true,shortcutNotepad:true,shortcutHelp:true,rpExcludeRetroStar:false,rpExcludeRetroSub:false,rpExcludeRetroBoth:false,rpNodeAspected:true,rpNodeAspecting:true,rpNodeConjunction:true,rpDayFromSunrise:true,rpHoraFromSunrise:true,rpIncludeRetrograde:true,rpShowSub:true,rpShowSubSub:true,rpRefreshSeconds:1,sigShowCSL:true,sigShowAspd:true,sigShowAspg:true,sigShowConj:true,houseShowAspd:true,houseShowConj:true,westernOrb0:Number(document.getElementById('western-orb-0')?.value||5),westernEnabled0:document.getElementById('western-angle-0')?.checked!==false,westernOrb180:Number(document.getElementById('western-orb-180')?.value||5),westernEnabled180:document.getElementById('western-angle-180')?.checked!==false,westernOrb120:Number(document.getElementById('western-orb-120')?.value||5),westernEnabled120:document.getElementById('western-angle-120')?.checked!==false,westernOrb90:Number(document.getElementById('western-orb-90')?.value||5),westernEnabled90:document.getElementById('western-angle-90')?.checked!==false,westernOrb60:Number(document.getElementById('western-orb-60')?.value||5),westernEnabled60:document.getElementById('western-angle-60')?.checked!==false,westernOrb150:Number(document.getElementById('western-orb-150')?.value||5),westernEnabled150:document.getElementById('western-angle-150')?.checked!==false,westernOrb30:Number(document.getElementById('western-orb-30')?.value||5),westernEnabled30:document.getElementById('western-angle-30')?.checked!==false,westernOrb45:Number(document.getElementById('western-orb-45')?.value||5),westernEnabled45:document.getElementById('western-angle-45')?.checked!==false,chartStyle:'south',interpretiveSize:'medium',planetSize:'medium',degreeSize:'medium',tableSize:'medium',resolution:'auto',planetSymbols:false,showFortuna:false,birthInfo:true,tooltips:true,dateFormat:'DD/MM/YYYY',timeFormat:'24',fortunaFormula:'sect',transitCusps:'natal',planetNotation:'full',houseNotation:'roman',degreePrecision:'seconds',notationMarkers:true,combustionRule:'planet-specific',homeView:'basic',conjunctionOrb:3,ketuAspects:false,language:'english',astroPlace:document.getElementById('birthPlace').value||'Default consultation place',astroLatitude:document.getElementById('lat').value,astroLongitude:document.getElementById('lon').value,astroUtcOffset:5.5,fontSize:12,fontFamily:'Arial',fontBold:false,fontColor:'#111111',sidebarColor:'#f1f5f9',sidebarAccent:'#dbeafe',sidebarHidden:false,theme:'forest',themeType:'light',themeHeader:'#6c913b',themeBackground:'#ffffe4',themeStripe:'#e4ecda',themeButton:'#0089f7',planetColorSu:'#a64800',planetColorMo:'#155da6',planetColorMa:'#c52828',planetColorMe:'#087c45',planetColorJu:'#945a00',planetColorVe:'#88499b',planetColorSa:'#455780',planetColorRa:'#624735',planetColorKe:'#6d5276'});
 const ENUMS={fontFamily:['Arial','Georgia','monospace'],chartStyle:['south','north'],interpretiveSize:['small','medium','large'],planetSize:['small','medium','large'],degreeSize:['small','medium','large'],tableSize:['small','medium','large'],resolution:['auto','compact','wide'],dateFormat:['DD/MM/YYYY','MM/DD/YYYY','YYYY-MM-DD'],timeFormat:['12','24'],fortunaFormula:['sect','day','night'],transitCusps:['natal','transit'],planetNotation:['full','short'],houseNotation:['roman','numeric'],degreePrecision:['seconds','minutes'],combustionRule:['planet-specific','uniform'],homeView:['basic','fourfold','sixfold','fourstep','nadi'],language:["english", "marathi", "hindi", "tamil", "gujarati", "kannada", "telugu", "bengali", "assamese", "bodo", "dogri", "kashmiri", "konkani", "maithili", "malayalam", "manipuri", "nepali", "odia", "punjabi", "sanskrit", "santali", "sindhi", "urdu", "bilingual"],theme:['sky','royal-blue','forest','red','yellow','lavender','light','classic'],themeType:['light','dark']};
 const NUMBERS={rpRefreshSeconds:[1,300],westernOrb0:[0,15],westernOrb180:[0,15],westernOrb120:[0,15],westernOrb90:[0,15],westernOrb60:[0,15],westernOrb150:[0,15],westernOrb30:[0,15],westernOrb45:[0,15],astroUtcOffset:[-14,14],fontSize:[10,22],conjunctionOrb:[0,10],aspectOrb:[0,15]};
 const ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
 const NAMES={Su:['Sun','रवी','☉'],Mo:['Moon','चंद्र','☽'],Ma:['Mars','मंगळ','♂'],Me:['Mercury','बुध','☿'],Ju:['Jupiter','गुरु','♃'],Ve:['Venus','शुक्र','♀'],Sa:['Saturn','शनि','♄'],Ra:['Rahu','राहू','☊'],Ke:['Ketu','केतू','☋'],Fo:['Fortuna','फॉर्चुना','⊗']};
 const ID_BY_LABEL=Object.fromEntries(Object.entries(NAMES).flatMap(([id,names])=>[[id,id],...names.map(name=>[name,id])]));
 let settings={...DEFAULTS},applying=false,queued=false,initialized=false,configured=false;
 const byId=id=>document.getElementById(id);
 function normalize(source) {
   if(!source || typeof source!=='object' || Array.isArray(source)) return {...DEFAULTS};
   const result={...DEFAULTS};
   for(const key of Object.keys(DEFAULTS)) {
     const value=source[key];
     if(ENUMS[key]) { if(ENUMS[key].includes(value)) result[key]=value; }
     else if(NUMBERS[key]) { if(typeof value==='number' && Number.isFinite(value) && value>=NUMBERS[key][0] && value<=NUMBERS[key][1]) result[key]=value; }
     else if(Object.hasOwn(DEFAULTS,key) && /^(theme(Header|Background|Stripe|Button)|planetColor|fontColor|sidebar(Color|Accent))/.test(key)) {if(typeof value==='string' && /^#[0-9a-f]{6}$/i.test(value))result[key]=value;}
     else if(key==='astroPlace'&&typeof value==='string'&&value.length<=200)result[key]=value.trim();
     else if(['astroLatitude','astroLongitude'].includes(key)&&typeof value==='string'){const m=value.trim().match(/^([+-]?\d{1,3}):([0-5]?\d):([0-5]?\d(?:\.\d+)?)\s*([NSEW])?$/i);if(m){const n=Math.abs(Number(m[1]))+Number(m[2])/60+Number(m[3])/3600,h=(m[4]||'').toUpperCase();if(n<(key==='astroLatitude'?89:180.000001)&&(!h||(key==='astroLatitude'?'NS':'EW').includes(h)))result[key]=value.trim();}}
     else if(typeof value==='boolean') result[key]=value;
   }
   return result;
 }
 function parse(source) {try {return normalize(JSON.parse(source || '{}'));} catch(error) {return {...DEFAULTS};}}
 function storeCurrent(persist=true) {
   const input=byId('kp-software-settings'); if(input) input.value=configured?JSON.stringify(settings):'';
   if(persist) {try{if(configured)localStorage.setItem(KEY,JSON.stringify(settings));else localStorage.removeItem(KEY);}catch(error){/* Applying preferences still works when browser storage is unavailable. */}}
 }
 function get() {return {...settings,chartStyle:window.KPChartStyle?.getStyle() || settings.chartStyle};}
 function isConfigured() {return configured;}
 function formatDate(source) {
   const value=String(source??''),match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
   if(!match) return value || '—';
   const date=new Date(value+'T12:00:00Z');
   if(Number.isNaN(date.getTime()) || date.toISOString().slice(0,10)!==value) return value;
   return settings.dateFormat==='YYYY-MM-DD'?value:settings.dateFormat==='MM/DD/YYYY'?match[2]+'/'+match[3]+'/'+match[1]:match[3]+'/'+match[2]+'/'+match[1];
 }
 function formatTime(source) {
   const value=String(source??''),match=/^(\d{1,2}):([0-5]\d)(?::([0-5]\d))?$/.exec(value);
   if(!match || Number(match[1])>23) return value || '—';
   const hour=Number(match[1]),tail=':'+match[2]+(match[3]!==undefined?':'+match[3]:'');
   return settings.timeFormat==='12'?(hour%12||12)+tail+' '+(hour<12?'AM':'PM'):String(hour).padStart(2,'0')+tail;
 }
 function planetLabel(id,original) {
   const names=NAMES[id]; if(!names) return original;
   if(settings.planetSymbols) return names[2];
   const marathi=window.KPLanguage?.translate(names[0],'marathi')||names[1];
   if(settings.planetNotation==='short') return window.KPPlanetNotation?.label(id,settings.language)||id;
   if(settings.language==='english') return names[0];
   if(settings.language==='marathi') return marathi;
   if(settings.language!=='bilingual')return window.KPLanguage?.translate(names[0],settings.language)||names[0];
   return original;
 }
 function degreeLabel(original,longitude) {
   if(settings.degreePrecision==='seconds') return original;
   let local=Number(longitude);
   if(Number.isFinite(local)) local=((local%108000)+108000)%108000;
   else {const match=/(\d+)°\s*(\d+)[′'’]\s*(\d+)?/.exec(original); if(!match)return original;local=Number(match[1])*3600+Number(match[2])*60+Number(match[3]||0);}
   const minutes=Math.round(local/60),retro=/\bR\b|ᴿ/.test(original)?' R':'';
   return Math.floor(minutes/60)+'°'+String(minutes%60).padStart(2,'0')+'′'+retro;
 }
 function remember(node,key,value) {if(node.dataset[key]===undefined)node.dataset[key]=value;return node.dataset[key];}
 function setText(node,text) {if(node && node.textContent!==text)node.textContent=text;}
 function hoverFields(entry,point,name,degree,lords) {
   const fields={hoverName:name,hoverDms:degree,hoverSign:point?.sign||entry.dataset.hoverSign||'',hoverSgl:point?.sgl||lords?.dataset.sgl||entry.dataset.hoverSgl||'—',hoverStl:point?.stl||lords?.dataset.stl||entry.dataset.hoverStl||'—',hoverSbl:point?.sl||point?.sbl||lords?.dataset.sbl||entry.dataset.hoverSbl||'—'};
   const longitude=Number(entry.dataset.longitude??point?.longitude);
   if(Number.isFinite(longitude))fields.hoverSign=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'][Math.floor(((longitude%1296000)+1296000)%1296000/108000)];
   for(const [key,value] of Object.entries(fields))if(entry.dataset[key]!==String(value))entry.dataset[key]=String(value);
   if(entry.hasAttribute('title'))entry.removeAttribute('title');
   for(const title of entry.querySelectorAll('title'))title.remove();
   const svg=entry.closest('svg');if(svg)for(const title of svg.querySelectorAll(':scope > title'))title.remove();
 }
 function southEntry(entry) {
   if(entry.closest('[data-manual-text],[contenteditable]'))return;
   const label=entry.querySelector('.v38-name'),degree=entry.querySelector('.v38-degree');if(!label || !degree)return;
   const originalName=remember(label,'kpOriginalName',label.textContent),originalDegree=remember(degree,'kpOriginalDegree',degree.textContent);
   remember(entry,'kpOriginalTitle',entry.getAttribute('title')||'');
   const cusp=entry.dataset.kind==='cusp';
   const house=Number(entry.dataset.cusp)||ROMAN.indexOf(originalName)+1;
   const id=entry.dataset.planet || ID_BY_LABEL[originalName];
   const modelPoint=cusp?window.currentKPModel?.houses?.find(point=>point.id===house):window.currentKPModel?.planets?.find(point=>point.id===id);
   const longitude=entry.dataset.longitude!==undefined?Number(entry.dataset.longitude):modelPoint?.longitude;
   const relative=cusp&&entry.closest('#home-kundali')?Number(entry.dataset.relativeHouse):0,shownHouse=Number.isInteger(relative)&&relative>=1&&relative<=12?relative:house;
   setText(label,cusp && settings.houseNotation==='numeric'?String(shownHouse):cusp&&relative?ROMAN[shownHouse-1]:cusp?originalName:planetLabel(id,originalName));
   setText(degree,degreeLabel(['Ra','Ke'].includes(id)?originalDegree.replace(/\s*R\s*$/,''):originalDegree,longitude));
   const lords=entry.querySelector('.v38-lords');
   hoverFields(entry,modelPoint,cusp?'House '+house:NAMES[id]?.[0]||originalName,originalDegree,lords);
 }
 function northEntry(entry) {
   const textNode=[...entry.childNodes].find(node=>node.nodeType===3);if(!textNode)return;
   const original=remember(entry,'kpOriginalLabel',textNode.nodeValue);
   const id=entry.dataset.planet,house=Number(entry.dataset.cusp);
   const originalName=entry.dataset.originalName || (house?ROMAN[house-1]:id);
   const point=house?window.currentKPModel?.houses?.find(item=>item.id===house):window.currentKPModel?.planets?.find(item=>item.id===id);
   const originalDegree=(entry.dataset.originalDegree || point?.degree || '').replace(/\s*R\s*$/,'');
   const retro=!['Ra','Ke'].includes(id)&&original.includes('ᴿ')?'ᴿ':'';
   const label=house && settings.houseNotation==='numeric'?String(house):house?originalName:planetLabel(id,originalName);
   const degree=originalDegree?degreeLabel(originalDegree,entry.dataset.longitude):'';
   const value=label+retro+(degree?' '+degree:'');
   let degreeSpan=entry.querySelector('[data-kp-degree-label]');
   if(degree && !degreeSpan) {degreeSpan=document.createElementNS('http://www.w3.org/2000/svg','tspan');degreeSpan.dataset.kpDegreeLabel='';entry.insertBefore(degreeSpan,textNode.nextSibling);}
   const nameText=label+retro+(degree?' ':'');if(textNode.nodeValue!==nameText)textNode.nodeValue=nameText;
   if(degreeSpan)setText(degreeSpan,degree);
   hoverFields(entry,point,house?'House '+house:NAMES[id]?.[0]||originalName,originalDegree,null);
   const base=Number(remember(entry,'kpOriginalSize',entry.getAttribute('font-size')||'10.5'));
   const planetRatio=({small:.85,medium:1,large:1.2})[settings.planetSize],degreeRatio=({small:.85,medium:1,large:1.15})[settings.degreeSize];
   const ratio=Math.max(planetRatio,degreeRatio);
   // A chart label keeps the horizontal space its original renderer reserved.
   const size=Math.min(base*ratio,base*Math.max(1,original.length)/Math.max(1,value.length));
   const nameSize=size*(house?degreeRatio:planetRatio)/ratio;
   if(Math.abs(Number(entry.getAttribute('font-size'))-nameSize)>.001)entry.setAttribute('font-size',String(nameSize));
   if(degreeSpan && Math.abs(Number(degreeSpan.getAttribute('font-size'))-size*degreeRatio/ratio)>.001)degreeSpan.setAttribute('font-size',String(size*degreeRatio/ratio));
 }
 function fitSouth(root) {
   const needsFit=settings.planetSize!=='medium'||settings.degreeSize!=='medium'||settings.planetSymbols||settings.planetNotation!=='full'||settings.language!=='bilingual'||settings.showFortuna;
   for(const entry of root.querySelectorAll('.v38-item')) {
     if(entry.closest('[data-manual-text],[contenteditable]'))continue;
     entry.style.removeProperty('--kp-preference-fit');
     if(!needsFit || !entry.getClientRects().length)continue;
     const position=entry.querySelector('.v38-position'),lords=entry.querySelector('.v38-lords');if(!position)continue;
     const box=entry.getBoundingClientRect(),first=position.getBoundingClientRect(),second=lords?.getBoundingClientRect();
     const gap=parseFloat(getComputedStyle(entry).rowGap)||0;
     const width=Math.max(first.width,second?.width||0),height=first.height+(second?.height||0)+gap;
     const fit=Math.min(1,Math.max(.1,(box.width-.5)/Math.max(.1,width)),Math.max(.1,(box.height-.5)/Math.max(.1,height)));
     if(fit<.999)entry.style.setProperty('--kp-preference-fit',String(fit));
   }
 }
 function resetDecorations(root) {
   root.querySelectorAll('.v38-item').forEach(entry=>{
     if(entry.closest('[data-manual-text],[contenteditable]'))return;
     const name=entry.querySelector('.v38-name'),degree=entry.querySelector('.v38-degree');
     if(name?.dataset.kpOriginalName!==undefined)setText(name,name.dataset.kpOriginalName);
     if(degree?.dataset.kpOriginalDegree!==undefined)setText(degree,degree.dataset.kpOriginalDegree);
     entry.style.removeProperty('--kp-preference-fit');
     if(entry.dataset.kpOriginalTitle!==undefined){if(entry.dataset.kpOriginalTitle)entry.title=entry.dataset.kpOriginalTitle;else entry.removeAttribute('title');}
   });
   root.querySelectorAll('.north9-chart svg text[data-kp-original-label]').forEach(entry=>{
     const textNode=[...entry.childNodes].find(node=>node.nodeType===3);if(textNode && textNode.nodeValue!==entry.dataset.kpOriginalLabel)textNode.nodeValue=entry.dataset.kpOriginalLabel;
     entry.querySelector('[data-kp-degree-label]')?.remove();
     if(entry.dataset.kpOriginalSize)entry.setAttribute('font-size',entry.dataset.kpOriginalSize);
     if(!entry.querySelector('title') && entry.dataset.kpOriginalTitle){const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=entry.dataset.kpOriginalTitle;entry.append(title);}
   });
   root.querySelectorAll('.tc-diagram svg tspan[data-kp-original-label],.tc-report svg tspan[data-kp-original-label]').forEach(entry=>setText(entry,entry.dataset.kpOriginalLabel));
   root.querySelectorAll('.tc-diagram svg text[data-kp-original-size],.tc-report svg text[data-kp-original-size]').forEach(row=>row.setAttribute('font-size',row.dataset.kpOriginalSize));
   root.querySelectorAll('#tc-bhav-chart svg g[data-house]>text:first-child,[data-report-id="tc-bhav-chart"] svg g[data-house]>text:first-child').forEach(label=>{label.setAttribute('data-no-localize','');setText(label,ROMAN[Number(label.parentElement.dataset.house)-1]);});
 }
 function decorate(root=document) {
   if(!configured){resetDecorations(root);return;}
   root.querySelectorAll('.v38-item').forEach(southEntry);
   root.querySelectorAll('.north9-chart svg text[data-longitude]').forEach(northEntry);
   // Transit diagrams use short, degree-free labels in their packed SVG rows.
   root.querySelectorAll('.tc-diagram svg tspan[data-planet],.tc-report svg tspan[data-planet]').forEach(entry=>{
     const original=remember(entry,'kpOriginalLabel',entry.textContent),id=entry.dataset.planet,retro=original.includes('ᴿ')?'ᴿ':'';
     const label=settings.planetSymbols?NAMES[id]?.[2]:settings.language==='marathi'?NAMES[id]?.[1]:id;
     if(label)setText(entry,label+retro);
   });
   const polygons=[[[240,0],[360,100],[240,200],[120,100]],[[0,0],[240,0],[120,100]],[[0,0],[120,100],[0,200]],[[0,200],[120,100],[240,200],[120,300]],[[0,200],[120,300],[0,400]],[[0,400],[120,300],[240,400]],[[240,200],[360,300],[240,400],[120,300]],[[240,400],[360,300],[480,400]],[[360,300],[480,200],[480,400]],[[240,200],[360,100],[480,200],[360,300]],[[480,0],[480,200],[360,100]],[[240,0],[480,0],[360,100]]];
   root.querySelectorAll('.tc-diagram svg text:has(tspan[data-planet]),.tc-report svg text:has(tspan[data-planet])').forEach(row=>{
     const polygon=polygons[Number(row.parentElement.dataset.house)-1];if(!polygon)return;
     const y=Number(row.getAttribute('y')),intersections=[];
     polygon.forEach((a,index)=>{const b=polygon[(index+1)%polygon.length];if(a[1]!==b[1] && y>=Math.min(a[1],b[1]) && y<=Math.max(a[1],b[1]))intersections.push(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]));});
     const base=Number(remember(row,'kpOriginalSize',row.getAttribute('font-size')||'12'));
     const requested=Math.min(13.4,base*({small:.85,medium:1,large:1.2})[settings.planetSize]);row.setAttribute('font-size',String(requested));
     const width=row.getComputedTextLength?.()||0,available=Math.max(...intersections)-Math.min(...intersections)-8;
     if(width>available && available>0)row.setAttribute('font-size',String(requested*available/width));
   });
   root.querySelectorAll('#tc-bhav-chart svg g[data-house]>text:first-child,[data-report-id="tc-bhav-chart"] svg g[data-house]>text:first-child').forEach(label=>{
     label.setAttribute('data-no-localize','');const house=Number(label.parentElement.dataset.house);setText(label,settings.houseNotation==='numeric'?String(house):ROMAN[house-1]);
   });
   fitSouth(root);
 }
 function presentationStyles() {
   if(!configured){const target=byId('kp-preference-values');if(target?.textContent)target.textContent='';return;}
   const factor=settings.fontSize/12,p=({small:.85,medium:1,large:1.2})[settings.planetSize]*factor,d=({small:.85,medium:1,large:1.15})[settings.degreeSize]*factor;
   const table=({small:.9,medium:1,large:1.08})[settings.tableSize],interpret=({small:.9,medium:1,large:1.12})[settings.interpretiveSize];
   const chart=':is(#kundali,[data-report-id="kundali"])';
   let css=`${chart} .v38-name{font-size:calc(11 * var(--v38-unit) * var(--v38-lane-scale) * ${p} * var(--kp-preference-fit,1))!important}${chart} .v38-degree{font-size:calc(9.5 * var(--v38-unit) * var(--v38-lane-scale) * ${d} * var(--kp-preference-fit,1))!important}${chart} .v38-lords{font-size:calc(8 * var(--v38-unit) * var(--v38-lane-scale) * var(--kp-preference-fit,1))!important}`;
   css+=`#home [data-home-chart] .v38-name{font-size:calc(16 * var(--home-chart-unit) * var(--v38-lane-scale) * ${p} * var(--kp-preference-fit,1))!important}#home [data-home-chart] .v38-degree{font-size:calc(14 * var(--home-chart-unit) * var(--v38-lane-scale) * ${d} * var(--kp-preference-fit,1))!important}#home [data-home-chart] .v38-lords{font-size:calc(11 * var(--home-chart-unit) * var(--v38-lane-scale) * var(--kp-preference-fit,1))!important}`;
   css+=`@media screen{body.app-ready main :is(.v38-name,.v38-degree,.v-planet,.v-planets,.north9-chart text[data-longitude]){font-family:${settings.fontFamily}!important;font-weight:${settings.fontBold?700:400}!important;color:${settings.themeType==='dark'&&settings.fontColor==='#111111'?'#eef2f7':settings.fontColor}!important}}`;
   if(!settings.birthInfo)css+=':is(#kundali,[data-report-id="kundali"],[data-home-chart]).v38-chart .v38-center:not([data-manual-text]) .v38-data{display:none!important}';
   if(table!==1)css+=`@media screen{body.app-ready main:not(#astrosettings) table :is(td,th){font-size:${11*table}px!important}#home table :is(td,th){font-size:${9*table}px!important}}@media print{.report-cover table :is(td,th){font-size:${7.5*table}px!important}.computed-report table :is(td,th),.tc-report table :is(td,th){font-size:${8*table}px!important}.report-cover .kp-basic-calculations :is(td,th){font-size:${6.5*table}px!important}}`;
   if(table>1)css+='@media screen{#home .home-summary-column{gap:8px}}';
   if(interpret!==1)css+=`.kp-step-card .kp-step{font-size:${12*interpret}px!important}#home .kp-step-card .kp-step{font-size:${10*interpret}px!important}.kp-step-label{font-size:${10*interpret}px!important}#home .kp-step-label{font-size:${9*interpret}px!important}`;
   const target=byId('kp-preference-values');if(target && target.textContent!==css)target.textContent=css;
 }
 function apply(options={}) {
   applying=true;
   try {
     if(document.body) {document.body.dataset.kpTheme=configured?settings.theme:'classic';document.body.dataset.kpThemeType=settings.themeType;document.body.dataset.kpResolution=configured?settings.resolution:'auto';}
     document.documentElement.lang=window.KPLanguage?.languages.find(x=>x.value===settings.language)?.code||'en';
     presentationStyles();
     if(configured && window.KPChartStyle?.getStyle()!==settings.chartStyle)window.KPChartStyle?.setStyle(settings.chartStyle);
     decorate(document);
     storeCurrent(options.persist!==false);
   }finally{applying=false;}
   return get();
 }
 function notify(previous,action) {window.dispatchEvent(new CustomEvent('kp-preferences-changed',{detail:{settings:get(),previous:{...previous},action}}));}
 function save(draft) {const previous=get();settings=normalize(draft);configured=true;apply();notify(previous,'saved');return get();}
 function restore(options={}) {
   const previous=get(),field=byId('kp-software-settings');
   configured=Boolean(field?.value);settings=parse(field?.value);
   // Legacy .lkp files have no preference JSON. Their chart-style field remains valid.
   if(!field?.value && ['south','north'].includes(byId('kundali-chart-style')?.value))settings.chartStyle=byId('kundali-chart-style').value;
   apply({persist:options.persist!==false});if(options.notify!==false)notify(previous,'restored');return get();
 }
 function schedule() {if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;decorate(document);});}
 function initialize() {
   if(initialized)return;initialized=true;
   const field=byId('kp-software-settings');let saved='';try{saved=localStorage.getItem(KEY)||'';}catch(error){}
   configured=Boolean(field?.value || saved);settings=parse(saved || field?.value);apply({persist:false});
   new MutationObserver(schedule).observe(document.querySelector('main')||document.body,{childList:true,subtree:true});
   if(typeof ResizeObserver==='function') {const observer=new ResizeObserver(schedule);['kundali','home-kundali'].forEach(id=>{const chart=byId(id);if(chart)observer.observe(chart);});}
   window.addEventListener('kundali-style-changed',event=>{if(applying)return;const style=event.detail?.style;if(!ENUMS.chartStyle.includes(style))return;settings={...settings,chartStyle:style};storeCurrent();schedule();});
   window.addEventListener('chart-saved',event=>{if(event.detail?.action==='loaded')restore();});
   window.addEventListener('kp-ephemeris-ready',schedule);
 }
 window.KPPreferences=Object.freeze({defaults:DEFAULTS,get,save,apply,restore,normalize,decorate,formatDate,formatTime,isConfigured,storageKey:KEY});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize);else initialize();
})();
