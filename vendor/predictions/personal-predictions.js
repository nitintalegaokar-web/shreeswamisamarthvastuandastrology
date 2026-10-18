(() => {
  'use strict';
  const $=id=>document.getElementById(id),val=id=>String($(id)?.value||'').trim();
  const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const read=x=>String(x||'').replace(/\\n/g,'\n');
  const records=JSON.parse($('kp-personal-prediction-rules').textContent).entries;
  const titles={'marriage-points':'Marriage Points','event-house-rules':'Event House Rules','eighth-cusp-rules':'Eighth Cusp Rules','childbirth':'Childbirth',analysis:'Kundali Analysis','vedic-predictions':'Vedic Prediction · वैदिक भविष्य','house-results':'Bhav Phal · भाव फल','planet-house-results':'Bhavanusar Phal · भावानुसार फल','general-predictions':'General Predictions',events:'Events','dasha-results':'Dasha Results','mahadasha-remedies':'Remedies',gemstones:'Gemstone Guidance','yoga-results':'Conjunction Results','transit-results':'Transit Results','numerology':'Numerology'};
  const mrTitles={'marriage-points':'विवाह नियम','event-house-rules':'घटना भाव नियम','eighth-cusp-rules':'अष्टम भाव नियम','childbirth':'संतती परीक्षण',analysis:'कुंडली विश्लेषण','vedic-predictions':'वैदिक भविष्य','house-results':'भाव फल','planet-house-results':'भावानुसार फल','general-predictions':'सर्वसाधारण फल','events':'घटना फल','dasha-results':'दशा फल','mahadasha-remedies':'उपाय','gemstones':'रत्न मार्गदर्शन','yoga-results':'युती फल','transit-results':'गोचर फल','numerology':'अंकशास्त्र'};
  function heading(id=active){const en=(titles[id]||id).split(' · ')[0],mr=mrTitles[id]||en,lang=window.KPPredictionLanguage.language();return lang==='marathi'?mr:lang==='bilingual'?en+' · '+mr:lang==='english'?en:window.KPLanguage?.translate(en,lang)||en;}
  const names={Su:'Sun',Mo:'Moon',Ma:'Mars',Me:'Mercury',Ju:'Jupiter',Ve:'Venus',Sa:'Saturn',Ra:'Rahu',Ke:'Ketu'};
  let active='analysis',page=0,initialized=false,houseCusp=1;const roman=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
  const isActive=()=>active!=='analysis';
  function decodeHouseGroup(text){
    function walk(rest,min){if(!rest)return [[]];const found=[];for(let h=min;h<=12;h++){const token=String(h);if(rest.startsWith(token))for(const tail of walk(rest.slice(token.length),h+1))found.push([h,...tail]);}return found;}
    if(!/^\d{1,15}$/.test(text))return null;const groups=walk(text,1);return groups.length===1?groups[0]:null;
  }
  function houses(model,id){const r=model.fourfold?.planets?.find(p=>p.id===id);return [...new Set(['A','B','C','D'].flatMap(f=>r?.[f]||[]))].sort((a,b)=>a-b);}
  function placementProof(record,model){
    const moon=model.planets.find(p=>p.id==='Mo'),key=record.key;let m;
    m=/^(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)InH(1[0-2]|[1-9])$/.exec(key);
    if(m&&model.planets.some(p=>p.id===m[1]&&p.occ===Number(m[2])))return names[m[1]]+' · Bhav '+m[2];
    m=/^(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke)In(Ar|Ta|Ge|Ca|Le|Vi|Li|Sc|Sg|Cp|Aq|Pi)$/.exec(key);
    if(m&&model.planets.some(p=>p.id===m[1]&&p.signCode===m[2]))return names[m[1]]+' · '+m[2];
    m=/^(?:nak)([1-9]|1[0-9]|2[0-7])$/.exec(key)||/^Nak([1-9]|1[0-9]|2[0-7])R[1-3]$/.exec(key);
    if(m&&moon?.nakIndex===Number(m[1])-1)return 'Moon · '+moon.nakshatra;
    m=/^Nak([1-9]|1[0-9]|2[0-7])C([1-4])$/.exec(key);
    if(m&&moon?.nakIndex===Number(m[1])-1&&moon.pada===Number(m[2]))return 'Moon · '+moon.nakshatra+' · Pada '+moon.pada;
    return '';
  }

  let eventSelection=null,eventChart='';
  function eventRows(){const d=KPHomeDasha.getData();return d.ready?d.levels[0].rows:[];}
  function eventPeriod(ms){const d=KPHomeDasha.getData(),offset=Number(d.timeZoneHours)*3600000;return new Date(ms).toISOString().slice(0,19).replace('T',' ')+' · UTC '+d.timeZoneHours;}
  function eventADRows(md){return md?KPHomeDasha.subdivide(md).filter(p=>p.endMs>md.startMs&&p.startMs<md.endMs):[];}
  function eventPDRows(md,ad){return ad?KPHomeDasha.subdivide(ad).filter(p=>p.endMs>Math.max(md.startMs,ad.startMs)&&p.startMs<Math.min(md.endMs,ad.endMs)):[];}
  function clippedEventPeriods(rows,offset){return rows.map((p,i)=>{const startMs=Math.max(...rows.slice(0,i+1).map(r=>r.startMs)),endMs=Math.min(...rows.slice(0,i+1).map(r=>r.endMs));return {...p,level:['MD','AD','PD'][i],id:eventCode(p.lord),startMs,endMs,startUTC:new Date(startMs-offset).toISOString(),endUTC:new Date(endMs-offset).toISOString()};});}
  function eventCode(lord){return Object.keys(KPDisplay.names).find(id=>KPDisplay.names[id]===lord)||lord;}
  function selectedEventDBA(instant=new Date()){
    const key=JSON.stringify([val('dob'),val('birthTime'),val('birth-utc-offset'),window.currentKPModel]);if(key!==eventChart){eventSelection=null;eventChart=key;}
    if(!eventSelection){const d=KPTransit.currentPeriods(instant),periods=clippedEventPeriods(['MD','AD','PD'].map(k=>d.periods[k]),Number(d.timeZoneHours)*3600000);return {mode:'current',periods,startUTC:periods[2].startUTC,endUTC:periods[2].endUTC};}
    KPHomeDasha.refresh();const roots=eventRows(),md=roots[eventSelection.md],ad=eventADRows(md)[eventSelection.ad],pd=eventPDRows(md,ad)[eventSelection.pd],offset=Number(KPHomeDasha.getData().timeZoneHours)*3600000;
    if(!md||!ad||!pd)throw Error('Select a valid MD, AD and PD from the native kundali.');
    const periods=clippedEventPeriods([md,ad,pd],offset);
    return {mode:'selected',periods,startUTC:periods[2].startUTC,endUTC:periods[2].endUTC};
  }
  function syncEventSelection(){
    if(!['events','dasha-results'].includes(active))return;KPHomeDasha.refresh();const roots=eventRows();let d;try{d=selectedEventDBA();}catch(e){$('pred-dba-period').textContent=e.message;return;}
    const indices=eventSelection?{...eventSelection}:{md:roots.findIndex(r=>r.key===d.periods[0].key),ad:0,pd:0};
    const md=roots[indices.md];if(!md)return;const ads=eventADRows(md);if(!eventSelection)indices.ad=ads.findIndex(r=>r.key===d.periods[1].key);
    const ad=ads[indices.ad];if(!ad)return;const pds=eventPDRows(md,ad);if(!eventSelection)indices.pd=pds.findIndex(r=>r.key===d.periods[2].key);
    for(const [id,rows,index] of [['pred-event-md',roots,indices.md],['pred-event-ad',ads,indices.ad],['pred-event-pd',pds,indices.pd]]){const select=$(id);select.innerHTML=rows.map((r,i)=>'<option value="'+i+'">'+esc(names[eventCode(r.lord)]||r.lord)+' · '+esc(new Date(id==='pred-event-md'?r.startMs:Math.max(r.startMs,md.startMs,id==='pred-event-pd'?ad.startMs:md.startMs)).toISOString().slice(0,10))+' – '+esc(new Date(id==='pred-event-md'?r.endMs:Math.min(r.endMs,md.endMs,id==='pred-event-pd'?ad.endMs:md.endMs)).toISOString().slice(0,10))+'</option>').join('');select.value=String(index);}
    $('pred-dba-period').textContent=(d.mode==='current'?'Current DBA':'Selected DBA')+' · '+d.periods.map(p=>p.level+' '+p.id).join(' → ')+' · '+eventPeriod(d.periods[2].startMs)+' → '+eventPeriod(d.periods[2].endMs)+' · end exclusive';
    $('pred-dba-select').setAttribute('aria-expanded',String(!$('pred-event-dba').hidden));
  }
  function chooseEventPeriod(level){const indices={md:Number(val('pred-event-md')),ad:Number(val('pred-event-ad')),pd:Number(val('pred-event-pd'))};if(level==='md'){indices.ad=0;indices.pd=0;}if(level==='ad')indices.pd=0;eventSelection=indices;page=0;refresh();}

  function matchRulesRaw(category,model=window.currentKPModel,instant=new Date()){
    if(category==='marriage-points')return window.KPMarriagePoints.evaluate(model);
    if(category==='event-house-rules')return window.KPEventHouseRules.match(model);
    if(category==='eighth-cusp-rules')return window.KPEighthCuspRules.match(model,val('pred-eighth-scope')||'applicable');
    if(category==='childbirth')return window.KPChildbirth.analyze(model,Number(val('pred-child-cusp'))||5);
    if(category==='vedic-predictions')return window.KPVedicPredictions.match();
    if(category==='numerology'&&window.KPNumerology)return window.KPNumerology.match();
    if(!model?.ready||model.planets?.length!==9||model.houses?.length!==12)return {ready:false,reason:model?.reason||'Complete the native kundali to see personal results.',rows:[]};
    if(['planet-house-results','yoga-results','transit-results'].includes(category)&&window.KPSuppliedPredictions)return window.KPSuppliedPredictions.match(category,model,instant);
    const rows=[],add=(r,proof,title='',text=r.value)=>rows.push({id:r.id,key:r.key,language:r.language||'english',title,proof,text:read(text),status:'matched'});
    if(category==='house-results'){
      for(const r of records.filter(r=>r.categoryId===category)){
        const m=/^Bh(1[0-2]|[1-9])R(\d+)$/i.exec(r.key);if(!m)continue;
        const required=decodeHouseGroup(m[2]);if(!required?.length)continue;
        const cusp=model.houses.find(c=>c.id===Number(m[1])),lord=model.planets.find(p=>p.id===cusp?.sl);if(!lord)continue;
        const union=[...new Set([...houses(model,lord.id),...houses(model,lord.stl)])];
        if(!required.every(h=>union.includes(h)))continue;
        const heading=records.find(h=>h.categoryId===category&&h.key.toLowerCase()===('Bh'+m[1]+'RH'+m[2]).toLowerCase())?.value||'House '+m[1];
        add(r,'Cusp '+m[1]+' · CSL '+lord.id+' + star '+lord.stl+' · matched houses '+required.join(', '),heading);
      }
    }else if(category==='general-predictions'){
      for(const r of records.filter(r=>r.categoryId===category)){const proof=placementProof(r,model);if(proof&&!/\{\d+\}/.test(r.value))add(r,proof,proof);}
    }else if(category==='events'){
      const data=window.KPPrediction.analyze(model);
      if(!data.ready)return {ready:false,reason:data.reason,rows:[]};
      let d;try{d=selectedEventDBA(instant);}catch(error){return {ready:false,reason:error.message,rows:[]};}
      const contributions=d.periods.map(p=>({level:p.level,id:p.id,houses:houses(model,p.id)})),union=[...new Set(contributions.flatMap(p=>p.houses))];
      for(const r of data.results.filter(r=>r.status==='matched'&&r.automaticEligible&&r.proof?.complete)){
        const p=(r.proofs||[r.proof]).find(p=>p.complete&&p.requiredHouses.length&&p.requiredHouses.every(h=>union.includes(h))&&contributions.every(l=>l.houses.some(h=>p.requiredHouses.includes(h))));if(!p)continue;
        rows.push({id:'event-'+r.id,language:window.KPPredictionLanguage.language(),title:window.KPPredictionLanguage.language()==='marathi'?r.event.mr:r.event.en,text:window.KPPredictionLanguage.language()==='marathi'?r.event.mr:r.event.en,proof:'Cusp '+p.cusp+' · '+p.chain.CSL+' → '+p.chain.STL+' → '+p.chain.SBL+' · matched houses '+p.requiredHouses.join(', ')+' · DBA '+contributions.map(l=>l.id+' ['+l.houses.join(', ')+']').join(' → '),status:'matched',requiredHouses:p.requiredHouses,dba:contributions});
      }
      return {ready:true,rows,periods:d.periods,mode:d.mode,startUTC:d.startUTC,endUTC:d.endUTC};
    }else if(['dasha-short','dasha-results','mahadasha-remedies'].includes(category)){
      let d;try{if(category==='dasha-results'){const selected=selectedEventDBA(instant),level=val('pred-dasha-level')||'MD',period=selected.periods.find(p=>p.level===level);d={...KPDashaFal.analyze(model,{lords:[period.id],method:'fourfold',scope:'joint'}),periods:[period],selectedDBA:selected.periods,date:period.startUTC.slice(0,10),time:period.startUTC.slice(11,19)};}else d=window.KPDashaFal.current(model,instant);}catch(error){return {ready:false,reason:error.message,rows:[]};}
      const chain=d.periods.map(p=>p.level+' '+p.id).join(' → ');
      if(category==='mahadasha-remedies'){
        const moon=model.planets.find(p=>p.id==='Mo');
        for(const r of records.filter(r=>r.categoryId===category)){
          if(r.key==='unak'+(moon.nakIndex+1))add(r,'Moon · '+moon.nakshatra,'Birth nakshatra remedy');
          if(r.key!=='U'+d.periods[0].id)continue;
          const md=names[d.periods[0].id],ad=names[d.periods[1].id],rx=new RegExp('^\\s*'+md+'\\s*[-–—]\\s*'+ad+'(?:\\s|:)','i');
          const lines=read(r.value).split('\n').filter(line=>rx.test(line));
          for(const line of lines)add(r,chain,'Running Dasha remedy',line);
        }
      }else{
        for(const row of d.results.filter(row=>row.status==='matched'&&row.record.categoryId===category))add(row.record,chain+' · matched houses '+row.required.join(', '),'Running DBA');
        if(category==='dasha-results')for(const r of records.filter(r=>r.categoryId===category)){
          const m=/^Dasa([1-9])(1[0-2]|[1-9])$/.exec(r.key);if(!m)continue;
          const id=Object.keys(names)[Number(m[1])-1],p=model.planets.find(p=>p.id===id);
          if(d.periods.some(l=>l.id===id)&&p.occ===Number(m[2]))add(r,chain+' · '+id+' occupies Bhav '+m[2],names[id]+' · Bhav '+m[2]);
        }
      }
      return {ready:true,rows:window.KPSuppliedPredictions?.merge(rows,category,model,instant,d.selectedDBA&&val('pred-dasha-level')==='AD'?d.selectedDBA.slice(0,2):d.periods)||rows,periods:d.periods,date:d.date,time:d.time};
    }else if(category==='gemstones'){
      const d=window.KPGemstones.getData();if(!d.ready)return {ready:false,reason:d.reason,rows:[]};
      for(const r of d.results.filter(r=>r.qualifies))rows.push({id:'gem-'+r.id,title:names[r.id]+' · '+r.stone,text:r.stone,proof:d.mode==='vedic'?r.ownership.map(h=>({1:'Lagnesh',5:'Panchamesh',11:'Labhesh'})[h]).join(' · '):(d.proof||'Priority '+r.priority+' · '+r.score+'/'+d.required.length+' event houses'),status:'matched'});
    }
    return {ready:true,rows:window.KPSuppliedPredictions?.merge(rows,category,model,instant)||rows};
  }
  function matchRules(...args){return window.KPPredictionLanguage.filter(matchRulesRaw(...args));}
  function getData(){const data=matchRules(active);if(active==='house-results')data.rows=data.rows.filter(r=>Number(/^Bh(1[0-2]|[1-9])[RL]/i.exec(r.key)?.[1])===houseCusp);return {...data,active:isActive(),category:active,page:page+1,cusp:active==='house-results'?houseCusp:active==='childbirth'?data.cusp:null};}
  function cards(rows,print=false){if(active==='eighth-cusp-rules')return window.KPEighthCuspRules.render(rows);if(active==='vedic-predictions')return window.KPVedicPredictions.render(rows,print);return rows.map(r=>'<article data-no-localize lang="'+(window.KPPredictionLanguage.language()==='marathi'?'mr':'en')+'" class="personal-prediction" data-personal-result="'+esc(r.id)+'" data-status="'+esc(r.status||'matched')+'">'+(!print&&r.title&&r.title!==r.text?'<h3>'+esc(r.title)+'</h3>':'')+'<p class="personal-result-text">'+esc(r.text)+'</p>'+'</article>').join('');}
  function refresh(){
    if(!initialized)return;
    $('pred-analysis-panel').hidden=isActive();$('pred-personal-panel').hidden=!isActive();
    for(const b of $('pred-subtabs').querySelectorAll('button')){b.setAttribute('data-no-localize','');b.textContent=heading(b.dataset.predTab);b.setAttribute('aria-selected',String(b.dataset.predTab===active));b.tabIndex=b.dataset.predTab===active?0:-1;}
    $('prediction-preview').disabled=active==='analysis'?!window.currentKPModel?.ready||!Number(val('pred-main-house')):!window.currentKPModel?.ready;
    if(!isActive())return;
    $('pred-house-event-wrap').hidden=active!=='event-house-rules';window.KPEventHouseRules.controls(active==='event-house-rules');
    const data=getData(),pages=Math.max(1,Math.ceil(data.rows.length/30));page=Math.max(0,Math.min(page,pages-1));
    $('pred-house-cusp-wrap').hidden=active!=='house-results';$('pred-personal-heading').textContent=heading()+(active==='house-results'?(window.KPPredictionLanguage.language()==='marathi'?' · भाव ':' · House ')+roman[houseCusp-1]:'');
    $('pred-personal-status').textContent=!data.ready?data.reason:data.rows.length+(active==='outer-references'?' supplied references':' kundali-matched results')+(data.context?' · '+data.context:'')+(data.periods?' · '+data.periods.map(p=>p.level+' '+p.id).join(' → '):'');
    if(active==='vedic-predictions'&&window.KPPredictionLanguage.language()==='marathi')$('pred-personal-status').textContent=data.ready?'वैदिक जन्मकुंडलीनुसार '+data.rows.length+' लागू फलविचार':data.reason;
    const selectedLanguage=window.KPPredictionLanguage.language();$('pred-personal-heading').setAttribute('data-no-localize','');$('pred-personal-status').setAttribute('data-no-localize','');if(selectedLanguage==='marathi')$('pred-personal-status').textContent=data.ready?data.rows.length+' लागू फलविचार':data.reason;else if(selectedLanguage==='english')$('pred-personal-status').textContent=data.ready?data.rows.length+' matching predictions':data.reason;
    if(data.translationUnavailable)$('pred-personal-status').textContent=data.languageMessage||window.KPPredictionLanguage.message();
    $('pred-personal-results').innerHTML=cards(data.rows.slice(page*30,(page+1)*30))||'<p>'+esc(data.ready?(data.languageMessage||window.KPPredictionLanguage.message('empty')):data.reason)+'</p>';
    $('pred-personal-page').textContent=pages>1?(page+1)+' / '+pages:'';
    $('pred-personal-prev').hidden=$('pred-personal-next').hidden=pages===1;$('pred-personal-prev').disabled=page===0;$('pred-personal-next').disabled=page===pages-1;
    $('pred-eighth-scope-wrap').hidden=active!=='eighth-cusp-rules';for(const option of $('pred-eighth-scope').options)option.textContent=window.KPPredictionLanguage.language()==='marathi'?(option.value==='all'?'सर्व ४० संदर्भनियम':'लागू ग्रहस्थिती व तपासणीचे नियम'):(option.value==='all'?'All 40 source rules':'Matching placements / review');$('pred-child-cusp-wrap').hidden=active!=='childbirth';$('pred-child-gender').hidden=active!=='childbirth';$('pred-child-gender').textContent=window.KPPredictionLanguage.language()==='marathi'?'बाललिंग परीक्षण · A4':'Child Gender · A4';$('pred-open-gems').hidden=active!=='gemstones';
    $('pred-dasha-level-wrap').hidden=active!=='dasha-results';$('pred-dba-select').hidden=!['events','dasha-results'].includes(active);if(!['events','dasha-results'].includes(active))$('pred-event-dba').hidden=true;syncEventSelection();
    $('prediction-preview').disabled=!data.ready;
    return data;
  }
  function snapshot(){

    const data=getData();return '<div class="personal-prediction-report"><h2 data-no-localize>'+esc(heading()+(active==='house-results'?(window.KPPredictionLanguage.language()==='marathi'?' · भाव ':' · House ')+roman[houseCusp-1]:''))+'</h2><p>'+esc(val('name'))+' · '+esc(active==='transit-results'?window.KPPredictionLanguage.clean(data.context):val('dob'))+'</p>'+(data.periods?'<p>'+esc(data.periods.map(p=>p.level+' '+names[p.id]).join(' → '))+'</p>':'')+(active==='events'&&data.periods?'<p>'+esc((data.mode==='current'?'Current DBA':'Selected DBA')+' · '+eventPeriod(data.periods[2].startMs)+' → '+eventPeriod(data.periods[2].endMs)+' · end exclusive')+'</p>':'')+cards(data.rows,true)+(data.rows.length?'':'<p>'+esc(data.ready?(data.languageMessage||window.KPPredictionLanguage.message('empty')):data.reason)+'</p>')+'</div>';
  }
  function initialize(){
    const section=$('prediction'),analysis=document.createElement('div');analysis.id='pred-analysis-panel';while(section.firstChild)analysis.append(section.firstChild);
    const toolbar=document.createElement('div');toolbar.className='pred-workspace-toolbar';toolbar.innerHTML='<h2>Prediction · कुंडली फल</h2><button id="prediction-preview" type="button">Preview</button>';
    const tabs=document.createElement('div');tabs.id='pred-subtabs';tabs.className='pred-subtabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Personal prediction sections');
    for(const [id,label] of Object.entries(titles)){const b=document.createElement('button');b.id='pred-tab-'+id;b.type='button';b.dataset.predTab=id;b.setAttribute('role','tab');b.textContent=label;tabs.append(b);}
    tabs.addEventListener('click',e=>{const b=e.target.closest('[data-pred-tab]');if(!b)return;active=b.dataset.predTab;page=0;refresh();});
    tabs.addEventListener('keydown',e=>{const buttons=[...tabs.querySelectorAll('[data-pred-tab]')],i=buttons.indexOf(e.target);if(i<0||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?buttons.length-1:(i+(e.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;buttons[n].click();buttons[n].focus();});
    const panel=document.createElement('div');panel.id='pred-personal-panel';panel.className='kp-feature-card';panel.hidden=true;panel.innerHTML='<h2 id="pred-personal-heading"></h2><p id="pred-personal-status" role="status" aria-live="polite"></p><div class="kp-feature-actions"><label id="pred-house-cusp-wrap" for="pred-house-cusp" hidden>Cusp <select id="pred-house-cusp" aria-label="Select house cusp">'+roman.map((r,i)=>'<option value="'+(i+1)+'">'+r+'</option>').join('')+'</select></label><label id="pred-dasha-level-wrap" hidden>Show selected dasha <select id="pred-dasha-level"><option value="MD">MD · Mahadasha</option><option value="AD">AD · Antardasha</option><option value="PD">PD · Pratyantardasha</option></select></label><button id="pred-dba-select" type="button" aria-controls="pred-event-dba" aria-expanded="false" hidden>DBA selection</button><button id="pred-open-gems" type="button" hidden>Gemstone rule</button><button id="pred-personal-prev" type="button">Previous</button><span id="pred-personal-page"></span><button id="pred-personal-next" type="button">Next</button></div><div id="pred-event-dba" class="pred-event-dba" hidden><div class="pred-event-dba-controls"><label>MD / Dasha<select id="pred-event-md"></select></label><label>AD / Bhukti<select id="pred-event-ad"></select></label><label>PD / Antara<select id="pred-event-pd"></select></label><button id="pred-dba-current" type="button">Current DBA</button></div><p id="pred-dba-period"></p></div><div id="pred-personal-results"></div>';
    const houseEvent=document.createElement('label');houseEvent.id='pred-house-event-wrap';houseEvent.hidden=true;houseEvent.style.cssText='min-width:0;max-width:100%;flex:1 1 280px';houseEvent.setAttribute('data-no-localize','');houseEvent.innerHTML='<select id="pred-house-event" aria-label="Supplied event rule" style="max-width:100%;min-width:0;width:100%"></select>';panel.querySelector('.kp-feature-actions').prepend(houseEvent);houseEvent.querySelector('select').onchange=()=>{window.KPEventHouseRules.select(val('pred-house-event'));page=0;refresh();};
    const eighthControl=document.createElement('label');eighthControl.id='pred-eighth-scope-wrap';eighthControl.hidden=true;eighthControl.setAttribute('data-no-localize','');eighthControl.innerHTML='<select id="pred-eighth-scope" aria-label="Rule view"><option value="applicable">Matching placements / review</option><option value="all">All 40 source rules</option></select>';panel.querySelector('.kp-feature-actions').prepend(eighthControl);eighthControl.querySelector('select').onchange=()=>{page=0;refresh();};
    const childControl=document.createElement('label');childControl.id='pred-child-cusp-wrap';childControl.hidden=true;childControl.setAttribute('data-no-localize','');childControl.innerHTML='<select id="pred-child-cusp" aria-label="Child cusp"><option value="5">1 · V</option><option value="7">2 · VII</option><option value="9">3 · IX</option></select>';const genderButton=document.createElement('button');genderButton.id='pred-child-gender';genderButton.type='button';genderButton.hidden=true;genderButton.setAttribute('data-no-localize','');genderButton.onclick=()=>window.KPChildGenderSheet.open();panel.querySelector('.kp-feature-actions').prepend(childControl,genderButton);childControl.querySelector('select').addEventListener('change',()=>{page=0;refresh();});
    section.append(toolbar,tabs,analysis,panel);
    const compactBar=document.createElement('div');compactBar.className='pred-compact-topbar';section.prepend(compactBar);compactBar.append(tabs,$('prediction-preview'));toolbar.remove();
    $('pred-dasha-level').addEventListener('change',()=>{page=0;refresh();});$('pred-house-cusp').addEventListener('change',()=>{houseCusp=Number(val('pred-house-cusp'));page=0;refresh();});$('prediction-preview').addEventListener('click',()=>['childbirth','eighth-cusp-rules','event-house-rules','marriage-points'].includes(active)?window.KPChildGenderSheet.preview({title:heading(),lang:window.KPPredictionLanguage.language(),html:'<article class="cg-page">'+snapshot()+'</article>'}):window.KPReportPreview.open('prediction'));$('pred-personal-prev').addEventListener('click',()=>{page--;refresh();});$('pred-personal-next').addEventListener('click',()=>{page++;refresh();});$('pred-open-gems').addEventListener('click',()=>document.querySelector('[data-tab="gemstones"]').click());
    $('pred-dba-select').addEventListener('click',()=>{const panel=$('pred-event-dba');panel.hidden=!panel.hidden;syncEventSelection();});$('pred-dba-current').addEventListener('click',()=>{eventSelection=null;page=0;refresh();});for(const level of ['md','ad','pd'])$('pred-event-'+level).addEventListener('change',()=>chooseEventPeriod(level));
    window.addEventListener('kp-preferences-changed',()=>{page=0;refresh();});initialized=true;refresh();setInterval(()=>{if(section.classList.contains('active')&&isActive())refresh();},60000);
  }
  window.KPPersonalPredictions=Object.freeze({isActive,refresh,getData,snapshot,matchRules,decodeHouseGroup,selectedEventDBA});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(initialize,0));else initialize();
})();
