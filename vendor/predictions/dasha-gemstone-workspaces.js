(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const val = id => String($(id)?.value ?? '').trim();
  const escape = text => String(text ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const unique = values => [...new Set(values)].sort((a,b) => a-b);
  const codes = ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
  const names = {Su:'Sun',Mo:'Moon',Ma:'Mars',Me:'Mercury',Ju:'Jupiter',Ve:'Venus',Sa:'Saturn',Ra:'Rahu',Ke:'Ketu'};
  const records = JSON.parse($('kp-personal-prediction-rules').textContent).entries;
  const dashaRecords = records.filter(record => record.categoryId === 'dasha-short' || record.categoryId === 'dasha-results' && record.group === 'Dasha combinations');
  const readable = text => String(text ?? '').replace(/\\n/g, '\n');
  const csvCell = value => {const text=String(value??'');return '"'+(/^[\s\u0000-\u001f]*[=+@-]/.test(text)?"'":'')+text.replaceAll('"','""')+'"';};
  const csv = rows => '\uFEFF'+rows.map(row=>row.map(csvCell).join(',')).join('\r\n');
  function download(text, filename) {
    const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');
    link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function showReport(section) {
    window.renderReport?.();document.querySelector('nav [data-tab="report"]')?.click();window.KPReportPages?.selectSections([section]);
  }
  function civilMs(date,time) {
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!/^\d{2}:\d{2}(?::\d{2})?$/.test(time))throw Error('Enter a valid date and time.');
    const parts=time.split(':').map(Number);if(parts.some((n,i)=>!Number.isInteger(n)||n<0||n>=(i?60:24)))throw Error('Enter a valid time.');
    const result=Date.parse(date+'T'+(time.length===5?time+':00':time)+'Z');
    if(!Number.isFinite(result)||new Date(result).toISOString().slice(0,10)!==date)throw Error('Enter a valid calendar date.');
    return result;
  }
  function lordHouses(model,id,method) {
    const row=model?.[method]?.planets?.find(row=>row.id===id),fields=method==='sixfold'?['A','B','C','D','E','F']:['A','B','C','D'];
    if(!row)throw Error('Complete the chart’s planet significators.');
    return unique(fields.flatMap(field=>row[field]||[]).filter(house=>Number.isInteger(house)&&house>=1&&house<=12));
  }
  function dashaAt(date,time) {
    window.KPHomeDasha?.refresh();const data=window.KPHomeDasha?.getData(),when=civilMs(date,time),result=[];
    let rows=data?.levels?.[0]?.rows||[];
    for(let level=0;level<3;level++) {
      const period=rows.find(period=>period.startMs<=when&&when<period.endMs);if(!period)break;
      const id=window.KPDisplay?.idByName?.[period.lord];if(!codes.includes(id))break;
      result.push({level:['MD','AD','PD'][level],id,start:period.start,end:period.end});rows=window.KPHomeDasha.subdivide(period);
    }
    if(result.length!==3)throw Error('The selected date/time is outside the available native MD/AD/PD timeline.');
    return result;
  }
  const planetOptions = optional => (optional?'<option value="">None</option>':'')+codes.map(id=>'<option value="'+id+'">'+names[id]+' · '+id+'</option>').join('');
  let dashaData={ready:false,results:[]},dashaPage=0;
  function analyzeDasha(model,options={}) {
    const method=options.method==='sixfold'?'sixfold':'fourfold',lords=(options.lords||[]).map(id=>String(id));
    if(!model?.ready)throw Error(model?.reason||'Complete the natal chart before calculating Dasha Fal.');
    if(!lords.length||lords.some(id=>!codes.includes(id)))throw Error('Select valid MD, AD or PD lords.');
    const layers=lords.map((id,index)=>({level:['MD','AD','PD'][index],id,houses:lordHouses(model,id,method)}));
    const houses=unique(layers.flatMap(layer=>layer.houses)),scope=options.scope==='each'?'each':'joint';
    const selected=options.records||dashaRecords;
    const results=selected.map(record=>{
      const required=record.houses||[],clear=record.mappingStatus==='clear'&&required.length>0&&required.every(house=>Number.isInteger(house)&&house>=1&&house<=12);
      const missing=required.filter(house=>scope==='each'?layers.some(layer=>!layer.houses.includes(house)):!houses.includes(house));
      return {record,required:[...required],missing,signifiedHouses:[...houses],status:!clear?'review':!missing.length?'matched':missing.length<required.length?'partial':'unmatched'};
    });
    return {ready:true,method,scope,layers,houses,results};
  }
  function currentDasha(model=window.currentKPModel,instant=new Date()) {
    if(!model?.ready)throw Error(model?.reason||'Complete the natal kundali to see the running DBA.');
    const utc=new Date(instant).getTime();if(!Number.isFinite(utc))throw Error('Invalid current time.');
    window.KPHomeDasha.refresh();const offset=window.KPHomeDasha.getData().timeZoneHours;
    if(!Number.isFinite(offset))throw Error('Complete the native UTC offset.');
    const local=new Date(utc+offset*3600000).toISOString(),date=local.slice(0,10),time=local.slice(11,19),periods=dashaAt(date,time);
    return {...analyzeDasha(model,{lords:periods.map(p=>p.id),method:'fourfold',scope:'joint'}),periods,date,time,offset,source:'automatic',mode:'current'};
  }
  function filteredDasha() {
    return (dashaData.results||[]).filter(row=>row.status==='matched'&&row.record.categoryId==='dasha-short');
  }
  function analyzeDashaYear(date,time,depth,options={}) {
    if(depth!==2&&depth!==3)throw Error('Choose two or three Dasa levels.');
    const start=civilMs(date,time),anchor=new Date(start),year=anchor.getUTCFullYear()+1,month=anchor.getUTCMonth();
    const last=new Date(Date.UTC(year,month+1,0)).getUTCDate();
    const end=Date.UTC(year,month,Math.min(anchor.getUTCDate(),last),anchor.getUTCHours(),anchor.getUTCMinutes(),anchor.getUTCSeconds());
    window.KPHomeDasha.refresh();const roots=window.KPHomeDasha.getData().levels[0].rows;
    if(!roots.some(period=>period.startMs<=start&&start<period.endMs)||!roots.some(period=>period.startMs<end&&end<=period.endMs))throw Error('The complete year must fall inside the native dasha timeline.');
    const periods=[];
    function walk(parent,chain) {
      for(const child of window.KPHomeDasha.subdivide(parent)) {
        if(child.endMs<=start||child.startMs>=end)continue;
        const next=[...chain,child];
        if(next.length===depth)periods.push({chain:next,startMs:Math.max(child.startMs,start),endMs:Math.min(child.endMs,end)});
        else walk(child,next);
      }
    }
    for(const root of roots)if(root.endMs>start&&root.startMs<end)walk(root,[root]);
    const results=periods.flatMap(period=>{
      const lords=period.chain.map(item=>window.KPDisplay.idByName[item.lord]);
      const analysis=analyzeDasha(window.currentKPModel,{...options,lords});
      return analysis.results.map(result=>({...result,lords,periodStart:new Date(period.startMs).toISOString().slice(0,19),periodEnd:new Date(period.endMs).toISOString().slice(0,19)}));
    });
    return {ready:true,results,periodCount:periods.length,method:options.method==='sixfold'?'sixfold':'fourfold',scope:options.scope==='each'?'each':'joint',date,time,source:'automatic',mode:'year',depth,end:new Date(end).toISOString().slice(0,19),layers:[]};
  }
  function dashaRows(rows) {
    return rows.map(row=>'<tr data-df-record="'+escape(row.record.id)+'" data-status="matched"><td class="kp-feature-text">'+escape(readable(row.record.value))+'</td></tr>').join('');
  }
  function drawDasha() {
    const rows=filteredDasha(),pages=Math.max(1,Math.ceil(rows.length/40));dashaPage=Math.max(0,Math.min(dashaPage,pages-1));
    $('df-results').innerHTML=dashaRows(rows.slice(dashaPage*40,(dashaPage+1)*40))||'<tr><td>'+escape(dashaData.ready?'No supplied Dasha result matches the running DBA house groups.':dashaData.reason||'Complete the natal kundali.')+'</td></tr>';
    $('df-page').textContent=rows.length+' results · '+(dashaPage+1)+' / '+pages;$('df-prev').disabled=!dashaPage;$('df-next').disabled=dashaPage>=pages-1;
    $('df-prev').hidden=$('df-next').hidden=pages===1;$('dasha-fal-preview').disabled=!dashaData.ready;
  }
  function refreshDasha() {
    if(!$('df-status'))return dashaData;
    try {
      dashaData=currentDasha();
      $('df-status').dataset.ready='true';$('df-status').textContent='Currently running · '+dashaData.date+' '+dashaData.time+' · Native local time (UTC'+(dashaData.offset>=0?'+':'')+dashaData.offset+')';
      $('df-periods').innerHTML=dashaData.periods.map((p,i)=>'<article data-df-level="'+p.level+'"><span>'+['Mahadasha · महादशा','Antardasha · अंतर्दशा','Pratyantardasha · प्रत्यंतरदशा'][i]+'</span><strong>'+escape(names[p.id])+' · '+p.id+'</strong><small>'+escape(p.start.replace('T',' '))+' → '+escape(p.end.replace('T',' '))+'</small></article>').join('');
      $('df-evidence').textContent=dashaData.layers.map(p=>p.level+' '+p.id+': '+p.houses.join(', ')).join(' · ');
    }catch(error){dashaData={ready:false,reason:error.message,results:[]};$('df-status').dataset.ready='false';$('df-status').textContent=error.message;$('df-periods').innerHTML='';$('df-evidence').textContent='';}
    drawDasha();return dashaData;
  }
  function dashaSnapshot() {
    refreshDasha();if(!dashaData.ready)return '<div class="kp-feature-report"><p>'+escape(dashaData.reason)+'</p></div>';
    const rows=filteredDasha();
    return '<div class="kp-feature-report df-text-report">'+rows.map(row=>'<article data-df-result-text="'+escape(row.record.id)+'"><p>'+escape(readable(row.record.value))+'</p></article>').join('')+(rows.length?'':'<p>No Dasha result text matches the selected filters.</p>')+'</div>';
  }
  function dashaCSV() {
    refreshDasha();return csv([['Source ID','Source file','Source line','Key','House mapping','Mapping source line','Result text','Analysis','Missing houses','Method','Selected lords','Signified houses','Reference date','Reference time','Period start','Period end'],...filteredDasha().map(row=>[row.record.id,row.record.file,row.record.line,row.record.key,row.record.houseMappingRaw,row.record.houseMappingLine,readable(row.record.value),row.status,row.missing.join(', '),dashaData.method,row.lords?.join(', ')||dashaData.layers?.map(layer=>layer.id).join(', '),row.signifiedHouses?.join(', '),dashaData.date,dashaData.time,row.periodStart||'',row.periodEnd||''])]);
  }

  // User rule: Vedic 1/5/11 sign lords; KP greatest unique event-house coverage.
  const defaultStones={Su:'Ruby',Mo:'Pearl',Ma:'Red coral',Me:'Emerald',Ju:'Yellow sapphire',Ve:'Diamond',Sa:'Blue sapphire',Ra:'Hessonite',Ke:"Cat’s eye"};
  let gemstoneData={ready:false,results:[]};
  function evaluateGemstones(model,rule) {
    if(!model?.ready)throw Error(model?.reason||'Complete the natal chart before applying the gemstone rule.');
    const mode=rule.mode==='vedic'?'vedic':'kp';
    if(mode==='kp'&&window.KPGemstoneDocument)return window.KPGemstoneDocument.evaluate(model,rule);
    const required=mode==='vedic'?[1,5,11]:window.KPEventPromise.parseHouses(rule.required),excluded=window.KPEventPromise.parseHouses(rule.excluded);
    if(!required.length)throw Error('Enter the required houses from your automatic selection rule.');
    if(mode==='kp'&&required.some(house=>excluded.includes(house)))throw Error('A house cannot be both required and excluded.');
    const method=rule.method==='sixfold'?'sixfold':'fourfold',roles=(rule.roles||[]).filter(role=>['planet','star','sub'].includes(role));
    if(!roles.length)throw Error('Select at least one significator layer for your rule.');
    const results=model.planets.map(planet=>{
      const byRole={planet:planet.id,star:planet.stl,sub:planet.sl};
      const layers=roles.map(role=>({role,id:byRole[role],houses:lordHouses(model,byRole[role],method)})),houses=unique(layers.flatMap(layer=>layer.houses));
      const missing=required.filter(house=>!houses.includes(house)),blocked=excluded.filter(house=>houses.includes(house));
      const markers=window.KPDisplay?.getNotations(planet.id,model)||[],retrograde=planet.retrograde===true||markers.includes('[R]'),combust=markers.includes('[C]');
      const signLords=['Ma','Ve','Me','Mo','Su','Me','Ve','Ma','Ju','Sa','Sa','Ju'],lagna=model.houses[0].signIndex;
      const ownership=mode==='vedic'?required.filter(house=>signLords[(lagna+house-1)%12]===planet.id):[];
      const score=mode==='vedic'?ownership.length:required.length-missing.length;
      const eligible=mode==='vedic'||(!blocked.length&&!(rule.excludeRetrograde&&retrograde)&&!(rule.excludeCombust&&combust));
      return {id:planet.id,stone:String(rule.stones?.[planet.id]||'').trim(),houses,layers,missing,blocked,retrograde,combust,ownership,score,eligible,qualifies:false};
    });
    const highest=Math.max(0,...results.filter(row=>row.eligible).map(row=>row.score));
    results.forEach(row=>{row.qualifies=row.eligible&&row.score>0&&(mode==='vedic'||row.score===highest);row.priority=row.qualifies?(mode==='vedic'?Math.min(...row.ownership.map(house=>[1,5,11].indexOf(house)+1)):1):null;});
    results.sort((a,b)=>Number(b.qualifies)-Number(a.qualifies)||(a.priority??99)-(b.priority??99)||Number(b.eligible)-Number(a.eligible)||b.score-a.score||codes.indexOf(a.id)-codes.indexOf(b.id));
    return {ready:true,mode,required,excluded,method,roles,highest,results};
  }
  const gemstoneEvents=new Map();
  function mountGemstoneEvents(){
    const select=$('gem-event'),catalogue=window.KPPrediction.getCatalogue();
    const important=new Set([198,850,841,959,1354,1237,562,1574,1597,923,194,1481]);
    const addGroup=label=>{const group=document.createElement('optgroup');group.label=label;select.append(group);return group;};
    const life=addGroup('Important life events · your KP catalogue'),byHouse=new Map();
    for(const event of catalogue.events){
      if(!event.automaticEligible)continue;
      const house=event.mainHouses[0];if(!byHouse.has(house))byHouse.set(house,addGroup('Your KP events · main cusp '+house));
      event.supportingGroups.forEach((houses,index)=>{
        const id='kp:'+event.id+':'+index,label=(event.event.en||event.event.mr)+' · '+houses.join(', '),option=document.createElement('option');
        option.value=id;option.textContent=label;gemstoneEvents.set(id,{houses:[...houses],proof:'Prediction catalogue #'+event.id+' · Main cusp '+event.mainHouses.join(', ')+' · explicit house group '+houses.join(', ')});
        (important.has(event.id)?life:byHouse.get(house)).append(option);
      });
    }
    select.value='money';updateGemstoneEventProof();
  }
  function updateGemstoneEventProof(){
    const entry=gemstoneEvents.get(val('gem-event'));
    $('gem-event-proof').textContent=entry?.proof||({money:'Your money / business rule: 2, 6, 10, 11',childbirth:'Your childbirth rule: 2, 5, 11',custom:'Your entered event house group'}[val('gem-event')]||'');
  }
  function selectGemstoneEvent(){
    const entry=gemstoneEvents.get(val('gem-event')),preset={money:[2,6,10,11],childbirth:[2,5,11]}[val('gem-event')];
    if(entry||preset)$('gem-required').value=(entry?.houses||preset).join(',');updateGemstoneEventProof();
  }
  function filterGemstoneEvents(){
    const query=val('gem-event-search').toLocaleLowerCase();
    for(const option of $('gem-event').options)option.hidden=!['money','childbirth','custom'].includes(option.value)&&option.value!==val('gem-event')&&!option.textContent.toLocaleLowerCase().includes(query);
    for(const group of $('gem-event').querySelectorAll('optgroup'))group.hidden=[...group.children].every(option=>option.hidden);
  }
  function gemstoneRule() {
    return {mode:val('gem-mode'),purpose:val('gem-event'),required:val('gem-required'),excluded:'',method:'fourfold',roles:['planet','star','sub'],excludeRetrograde:true,excludeCombust:true,stones:Object.fromEntries(codes.map(id=>[id,val('gem-stone-'+id)]))};
  }
  function gemstoneRows(data) {
    const labels={1:'Lagnesh',5:'Panchamesh',11:'Labhesh'},matched=data.results.filter(row=>row.qualifies);
    return matched.map(row=>'<tr data-gem-planet="'+row.id+'" data-qualifies="true" data-gem-priority="'+row.priority+'"><td><span class="gem-priority-badge">'+row.priority+(data.mode==='kp'&&matched.length>1?' · shared':'')+'</span></td><td>'+escape(names[row.id])+(data.mode==='vedic'?((row.retrograde?' · R':'')+(row.combust?' · C':'')):'')+'</td><td><strong>'+escape(row.stone||'Gemstone not specified')+'</strong></td><td>'+(data.mode==='vedic'?row.ownership.map(h=>labels[h]).join(' · '):row.score+'/'+data.required.length+' houses: '+data.required.filter(h=>row.houses.includes(h)).join(', '))+'</td></tr>').join('');
  }
  function refreshGemstones() {
    if(!$('gem-required'))return gemstoneData;
    try {
      gemstoneData=evaluateGemstones(window.currentKPModel,gemstoneRule());const matched=gemstoneData.results.filter(row=>row.qualifies);
      $('gem-status').dataset.ready='true';$('gem-status').textContent=matched.length?(matched.length+' recommended '+(matched.length===1?'gemstone':'gemstones')+' · '+(gemstoneData.mode==='vedic'?'Lagnesh, Panchamesh and Labhesh':gemstoneData.proof)):(gemstoneData.proof||'No eligible planet matches this rule.');
      $('gem-event').disabled=gemstoneData.mode==='vedic';$('gem-event').closest('div').hidden=gemstoneData.mode==='vedic';updateGemstoneEventProof();$('gem-event-proof').hidden=gemstoneData.mode==='vedic';if(gemstoneData.mode==='kp')$('gem-event-proof').textContent+=' · Purpose reference; gemstone follows XI cusp rule.';document.querySelector('#gemstones .gem-rule-summary').textContent=gemstoneData.mode==='vedic'?'House 1: Lagnesh · House 5: Panchamesh · House 11: Labhesh. R = retrograde, C = combust.':(gemstoneData.proof||'');
      $('gem-results').innerHTML=gemstoneRows(gemstoneData);
    } catch(error) {
      gemstoneData={ready:false,reason:error.message,results:[]};$('gem-status').dataset.ready='false';$('gem-status').textContent=error.message;$('gem-results').innerHTML='';
    }
    $('gemstones-preview').disabled=!gemstoneData.ready;return gemstoneData;
  }
  const navagrahaStotra=[
    ['सूर्य','जपाकुसुमसंकाशं काश्यपेयं महाद्युतिम् ।\nतमोऽरिं सर्वपापघ्नं प्रणतोऽस्मि दिवाकरम् ॥१॥'],
    ['चंद्र','दधिशङ्खतुषाराभं क्षीरोदार्णवसम्भवम् ।\nनमामि शशिनं सोमं शम्भोर्मुकुटभूषणम् ॥२॥'],
    ['मंगळ','धरणीगर्भसम्भूतं विद्युत्कान्तिसमप्रभम् ।\nकुमारं शक्तिहस्तं तं मङ्गलं प्रणमाम्यहम् ॥३॥'],
    ['बुध','प्रियङ्गुकलिकाश्यामं रूपेणाप्रतिमं बुधम् ।\nसौम्यं सौम्यगुणोपेतं तं बुधं प्रणमाम्यहम् ॥४॥'],
    ['गुरु','देवानां च ऋषीणां च गुरुं काञ्चनसन्निभम् ।\nबुद्धिभूतं त्रिलोकेशं तं नमामि बृहस्पतिम् ॥५॥'],
    ['शुक्र','हिमकुन्दमृणालाभं दैत्यानां परमं गुरुम् ।\nसर्वशास्त्रप्रवक्तारं भार्गवं प्रणमाम्यहम् ॥६॥'],
    ['शनि','नीलाञ्जनसमाभासं रविपुत्रं यमाग्रजम् ।\nछायामार्तण्डसम्भूतं तं नमामि शनैश्चरम् ॥७॥'],
    ['राहू','अर्धकायं महावीर्यं चन्द्रादित्यविमर्दनम् ।\nसिंहिकागर्भसम्भूतं तं राहुं प्रणमाम्यहम् ॥८॥'],
    ['केतू','पलाशपुष्पसंकाशं तारकाग्रहमस्तकम् ।\nरौद्रं रौद्रात्मकं घोरं तं केतुं प्रणमाम्यहम् ॥९॥']
  ];
  function gemstoneSnapshot() {
    if(!$('gem-status'))return '<div class="kp-feature-report"><p>Gemstone rule is initializing.</p></div>';
    refreshGemstones();const guidance=readable(records.find(record=>record.categoryId==='gemstones'&&record.key==='RatnaH')?.value||'');
    const selected=new Set(gemstoneData.results.filter(row=>row.qualifies).map(row=>codes.indexOf(row.id)));
    return '<article class="kp-feature-report gem-one-page" data-no-localize><div class="gem-report-heading"><h2>Gemstone recommendations · रत्न मार्गदर्शन</h2><p>'+escape(val('name')||val('nativeName')||'')+'</p></div><p><strong>'+(gemstoneData.mode==='vedic'?'Vedic · Lagnesh, Panchamesh, Labhesh':'KP · '+escape($('gem-event').selectedOptions[0]?.textContent||''))+'</strong></p><p>'+escape($('gem-status').textContent)+'</p>'+(gemstoneData.ready?'<table class="gem-report-table"><thead><tr><th>Priority</th><th>Planet</th><th>Gemstone</th><th>Reason</th></tr></thead><tbody>'+gemstoneRows(gemstoneData)+'</tbody></table>':'')+'<p class="gem-report-rule">'+(gemstoneData.mode==='vedic'?'Whole-sign Lagna houses 1, 5 and 11. R = retrograde, C = combust.':escape(gemstoneData.proof||''))+' Stone names use Navaratna correspondence.</p><section class="gem-ratna-guidance" data-ratna-key="RatnaH"><h3>Original Ratna guidance</h3><p class="kp-feature-text">'+escape(guidance)+'</p></section><section class="gem-stotra" lang="sa"><h3>॥ नवग्रह स्तोत्रम् ॥</h3><div class="gem-stotra-grid">'+navagrahaStotra.map(([title,verse],index)=>'<div class="gem-stotra-verse'+(selected.has(index)?' gem-stotra-selected':'')+'" data-navagraha="'+codes[index]+'"><strong>'+escape(title)+'</strong><p>'+escape(verse)+'</p></div>').join('')+'</div><div class="gem-stotra-phala"><strong>फलश्रुती</strong><p>इति व्यासमुखोद्गीतं यः पठेत्सुसमाहितः । दिवा वा यदि वा रात्रौ विघ्नशान्तिर्भविष्यति ॥१०॥<br>नरनारीनृपाणां च भवेद्दुःस्वप्ननाशनम् । ऐश्वर्यमतुलं तेषामारोग्यं पुष्टिवर्धनम् ॥११॥<br>ग्रहनक्षत्रजाः पीडास्तस्कराग्निसमुद्भवाः । ताः सर्वाः प्रशमं यान्ति व्यासो ब्रूते न संशयः ॥१२॥</p><p>॥ इति श्रीव्यासविरचितं नवग्रहस्तोत्रं सम्पूर्णम् ॥</p></div></section></article>';
  }
  function gemstoneCSV() {
    refreshGemstones();return csv([['Planet','Gemstone','Signified houses','Qualifies','Missing houses','Excluded houses present','Target houses','Excluded houses','Mode','Score','Selected-house ownership','Method'],...gemstoneData.results.map(row=>[row.id,row.stone,row.houses.join(', '),row.qualifies,row.missing.join(', '),row.blocked.join(', '),gemstoneData.required.join(', '),gemstoneData.excluded.join(', '),gemstoneData.mode,row.score,row.ownership.join(', '),gemstoneData.method])]);
  }

  let sliceData={ready:false,rows:[]},generation=0;
  function sliceOptions() {
    return {startDate:val('ts-start-date'),startTime:val('ts-start-time'),endDate:val('ts-end-date'),endTime:val('ts-end-time'),offset:val('ts-offset')===''?NaN:Number(val('ts-offset')),latitude:val('ts-latitude')===''?NaN:Number(val('ts-latitude')),longitude:val('ts-longitude')===''?NaN:Number(val('ts-longitude')),stepMinutes:val('ts-step')===''?NaN:Number(val('ts-step')),cuspSource:val('ts-cusps'),eventId:val('ts-event'),method:val('ts-method')};
  }
  function validateSlice(options) {
    const startLocal=civilMs(options.startDate,options.startTime),endLocal=civilMs(options.endDate,options.endTime);
    for(const field of ['offset','latitude','longitude','stepMinutes'])if(!Number.isFinite(options[field]))throw Error('Enter valid numeric scan settings.');
    if(Math.abs(options.offset)>14)throw Error('UTC offset must be between −14 and +14 hours.');
    if(Math.abs(options.latitude)>90||Math.abs(options.longitude)>180)throw Error('Check the latitude and longitude ranges.');
    if(options.cuspSource!=='transit'&&options.cuspSource!=='natal')throw Error('Choose computed or native cusps.');
    if(options.cuspSource==='transit'&&Math.abs(options.latitude)>=66.56)throw Error('Computed Placidus cusps need a location below the polar circle; choose native cusps or another location.');
    if(!Number.isInteger(options.stepMinutes)||options.stepMinutes<1||options.stepMinutes>1440)throw Error('Use an interval of 1–1440 whole minutes.');
    if(endLocal<startLocal)throw Error('The end must be at or after the start.');
    const start=startLocal-options.offset*3600000,end=endLocal-options.offset*3600000;
    if(start<Date.UTC(1900,0,1)||end>=Date.UTC(2101,0,1))throw Error('The full UTC scan range must be within 1900–2100.');
    const times=[];for(let time=start;time<=end;time+=options.stepMinutes*60000){times.push(time);if(times.length>500)throw Error('This range exceeds 500 samples. Increase the interval or shorten the range.');}
    if(times[times.length-1]!==end)times.push(end);if(times.length>500)throw Error('This range exceeds 500 samples. Increase the interval or shorten the range.');
    const event=window.KPPrediction.getCatalogue().events.find(event=>String(event.id)===String(options.eventId));if(!event)throw Error('Choose an event from your Prediction catalogue.');
    if(options.cuspSource==='natal'&&!window.currentKPModel?.ready)throw Error('Complete the native chart before using its cusps.');
    return {times,event};
  }
  function sampleChart(date,options,native,event) {
    const positions=window.KPEphemeris.positions(date),cusps=options.cuspSource==='natal'?native.houses.map(house=>house.longitude):window.KPTransitHouses.calculate(date,options.latitude,options.longitude).cusps.map(longitude=>longitude*3600);
    const model=window.KPDisplay.build(cusps,Object.fromEntries(Object.entries(positions).map(([id,longitude])=>[id,longitude*3600])),native?.options||{});
    if(!model.ready)throw Error(model.reason||'A sample chart could not be calculated.');
    const analysis=window.KPPrediction.analyze(model,{method:options.method,layers:['CSL','STL','SBL'],catalogue:{events:[event],metadata:{},issues:[]}}),result=analysis.results[0];
    return {utc:date.toISOString(),local:new Date(date.getTime()+options.offset*3600000).toISOString().slice(0,19),ascendant:model.houses[0].longitude/3600,mc:model.houses[9].longitude/3600,moon:model.planets.find(planet=>planet.id==='Mo').longitude/3600,ascStar:model.houses[0].stl,ascSub:model.houses[0].sl,status:result.status,signified:result.proof?.signifiedHouses||[],missing:result.proof?.missingHouses||[]};
  }
  function zodiac(longitude) {
    const signs=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'],total=((Math.round(longitude*3600)%1296000)+1296000)%1296000,sign=Math.floor(total/108000),within=total%108000;
    return signs[sign]+' '+Math.floor(within/3600)+'°'+String(Math.floor(within%3600/60)).padStart(2,'0')+'′'+String(within%60).padStart(2,'0')+'″';
  }
  function sliceRows(rows,print=false) {
    return rows.map((row,index)=>'<tr data-ts-status="'+escape(row.status)+'" data-ts-utc="'+escape(row.utc)+'"><td>'+escape(row.local.replace('T',' '))+'</td><td>'+escape(zodiac(row.ascendant))+'</td><td>'+escape(zodiac(row.moon))+'</td><td>'+row.ascStar+' / '+row.ascSub+'</td><td><span class="ts-match-badge" data-status="'+escape(row.status)+'">'+escape({matched:'House group matched',partial:'Partial house group',unmatched:'House group absent',review:'Additional rule review',incomplete:'Chart incomplete'}[row.status])+'</span><small>Union: '+row.signified.join(', ')+' · Missing: '+(row.missing.join(', ')||'None')+'</small></td>'+(print?'':'<td><button type="button" data-ts-transit="'+index+'">Transit chart</button><button type="button" data-ts-nadi="'+index+'">Nadi</button></td>')+'</tr>').join('');
  }
  function invalidateSlices(message='Inputs changed. Run the scan again.') {
    generation++;sliceData={ready:false,rows:[],reason:message};if(!$('ts-status'))return;
    $('ts-status').textContent=message;$('ts-status').dataset.ready='false';$('ts-results').innerHTML='';$('ts-scan').disabled=false;$('ts-cancel').disabled=true;$('time-slices').removeAttribute('aria-busy');$('time-slices-preview').disabled=true;
  }
  async function scanSlices(override) {
    invalidateSlices('Preparing scan…');const token=generation,options=override||sliceOptions();
    try {
      const {times,event}=validateSlice(options),native=window.currentKPModel,rows=[];
      $('ts-scan').disabled=true;$('ts-cancel').disabled=false;$('time-slices').setAttribute('aria-busy','true');
      for(let index=0;index<times.length;index++) {
        if(token!==generation)return {ready:false,cancelled:true,rows:[]};
        rows.push(sampleChart(new Date(times[index]),options,native,event));
        $('ts-status').textContent='Calculating sample '+(index+1)+' / '+times.length+'…';
        if(index%5===0)await new Promise(resolve=>setTimeout(resolve,0));
      }
      if(token!==generation)return {ready:false,cancelled:true,rows:[]};
      sliceData={ready:true,rows,options:{...options},event:{id:event.id,label:event.event.en||event.event.mr}};
      $('ts-results').innerHTML=sliceRows(rows);$('ts-status').dataset.ready='true';$('ts-status').textContent=rows.length+' samples · '+sliceData.event.label+' · '+rows.filter(row=>row.status==='matched').length+' matching samples. Samples are snapshots; transitions between them are not calculated.';
      $('time-slices-preview').disabled=false;return sliceData;
    } catch(error) {if(token===generation)invalidateSlices(error.message);return {ready:false,reason:error.message,rows:[]};}
    finally {if(token===generation){$('ts-scan').disabled=false;$('ts-cancel').disabled=true;$('time-slices').removeAttribute('aria-busy');}}
  }
  function transferSlice(index,tab) {
    if(!Number.isInteger(index)||!['transit-chart','nadi-astrology'].includes(tab))throw Error('Choose a valid sample and chart.');
    const row=sliceData.rows[index],options=sliceData.options;if(!sliceData.ready||!row)throw Error('Run a time-slice scan and select an available sample.');
    const prefix=tab==='transit-chart'?'tc':'na';
    const fields={date:row.local.slice(0,10),time:row.local.slice(11),timezone:options.offset,latitude:options.latitude,longitude:options.longitude,place:'Time-slice location'};
    for(const [field,value] of Object.entries(fields))if($(prefix+'-'+field))$(prefix+'-'+field).value=String(value);
    if(prefix==='tc')$('tc-cusp-source').value=options.cuspSource==='natal'?'natal':'transit';
    else {$('na-source').value='moment';$('na-cusp-source').value=options.cuspSource==='natal'?'natal':'transit';}
    window.KPClientPresentation?.refreshCoordinates();
    if(prefix==='tc'){window.KPTransitChart?.stopRealTime();window.KPTransitChart?.refresh();}else{window.KPNadiAstrology?.stopRealTime();window.KPNadiAstrology?.calculate();}
    if(!window.KPProtectedWorker)return window.KPReportPreview?.open(tab);return true;
  }
  function sliceSnapshot() {
    if(!sliceData.ready)return '<div class="kp-feature-report"><p>'+escape(sliceData.reason||'Run a time-slice scan first.')+'</p></div>';
    return '<div class="kp-feature-report"><p>'+escape($('ts-status').textContent)+'</p><p>UTC offset '+escape(sliceData.options.offset)+' · Latitude '+escape(sliceData.options.latitude)+' · Longitude '+escape(sliceData.options.longitude)+' · '+escape(sliceData.options.cuspSource)+' cusps · '+escape(sliceData.options.method)+'. Both range endpoints are included; no event boundaries between samples are inferred.</p><table><thead><tr><th>Local time</th><th>Ascendant</th><th>Moon</th><th>Asc star/sub</th><th>Event evidence</th></tr></thead><tbody>'+sliceRows(sliceData.rows,true)+'</tbody></table></div>';
  }
  function sliceCSV() {
    return csv([['Local time','UTC','UTC offset','Latitude','Longitude','Cusp source','Event','Status','Ascendant degrees','MC degrees','Moon degrees','Asc star','Asc sub','Signified houses','Missing houses'],...(sliceData.ready?sliceData.rows:[]).map(row=>[row.local,row.utc,sliceData.options.offset,sliceData.options.latitude,sliceData.options.longitude,sliceData.options.cuspSource,sliceData.event.label,row.status,row.ascendant,row.mc,row.moon,row.ascStar,row.ascSub,row.signified.join(', '),row.missing.join(', ')])]);
  }
  function refreshSlices(){return sliceData;}
  function seedSlices() {
    let moment;try{moment=window.KPHorary.nativeMoment();}catch(_){return;}
    const now=new Date(Date.now()+moment.timezone*3600000),end=new Date(now.getTime()+3600000);
    for(const [prefix,date] of [['start',now],['end',end]]){$('ts-'+prefix+'-date').value=date.toISOString().slice(0,10);$('ts-'+prefix+'-time').value=date.toISOString().slice(11,19);}
    $('ts-offset').value=String(moment.timezone);$('ts-latitude').value=String(moment.latitude);$('ts-longitude').value=String(moment.longitude);
  }
  function initialize() {
    $('dasha-fal').innerHTML='<article class="kp-feature-card"><h2>Dasha Fal · दशाफल</h2><p id="df-status" class="kp-feature-status" role="status" aria-live="polite"></p><div id="df-periods" class="df-running-periods"></div><div class="kp-feature-actions"><button id="dasha-fal-preview" type="button">Preview · Print / PDF</button><button id="df-prev" type="button">Previous</button><span id="df-page"></span><button id="df-next" type="button">Next</button></div><table class="kp-feature-table"><thead><tr><th>Running DBA results · चालू दशाफल</th></tr></thead><tbody id="df-results"></tbody></table><details><summary>House evidence · भाव संकेत</summary><p id="df-evidence"></p></details></article>';
    $('df-prev').addEventListener('click',()=>{dashaPage--;drawDasha();});$('df-next').addEventListener('click',()=>{dashaPage++;drawDasha();});$('dasha-fal-preview').addEventListener('click',()=>window.KPReportPreview?.open('dasha-fal'));
    new MutationObserver(()=>{if($('dasha-fal').classList.contains('active')){dashaPage=0;refreshDasha();}}).observe($('dasha-fal'),{attributes:true,attributeFilter:['class']});
    setInterval(()=>{if($('dasha-fal').classList.contains('active'))refreshDasha();},60000);

    $('gemstones').innerHTML='<article class="kp-feature-card gem-simple-card"><h2>Gemstone recommendations · रत्न मार्गदर्शन</h2><div class="gem-simple-actions"><div><label for="gem-mode">Rule</label><select id="gem-mode"><option value="kp">KP · uploaded XI cusp rule</option><option value="vedic">Vedic · Lagnesh, Panchamesh, Labhesh</option></select></div><div><label for="gem-event">Purpose</label><select id="gem-event"><option value="money">Money / business · 2, 6, 10, 11</option><option value="childbirth">Childbirth · 2, 5, 11</option></select></div><button id="gemstones-preview" type="button">Preview / Print / PDF</button></div><small id="gem-event-proof"></small><p id="gem-status" class="kp-feature-status" role="status" aria-live="polite"></p><table class="kp-feature-table"><thead><tr><th>Priority</th><th>Planet</th><th>Gemstone</th><th>Reason</th></tr></thead><tbody id="gem-results"></tbody></table><p class="gem-rule-summary">Planet + star lord + sub lord · Retrograde and combust planets excluded.</p><div hidden><input id="gem-required" value="2,6,10,11"><input id="gem-excluded"><input id="gem-event-search"><select id="gem-method"><option value="fourfold">Four-fold</option></select><div id="gem-layers"><input id="gem-layer-planet" type="checkbox" value="planet" checked><input id="gem-layer-star" type="checkbox" value="star" checked><input id="gem-layer-sub" type="checkbox" value="sub" checked></div><input id="gem-exclude-retro" type="checkbox" checked><input id="gem-exclude-combust" type="checkbox" checked>'+codes.map(id=>'<input id="gem-stone-'+id+'" value="'+escape(defaultStones[id])+'">').join('')+'</div><details><summary>Original Ratna guidance</summary><p class="kp-feature-text">'+escape(readable(records.find(record=>record.categoryId==='gemstones'&&record.key==='RatnaH')?.value||''))+'</p></details></article>';
    mountGemstoneEvents();$('gem-event').addEventListener('change',selectGemstoneEvent);
    $('gemstones').addEventListener('change',refreshGemstones);$('gemstones-preview').addEventListener('click',()=>window.KPReportPreview?.open('gemstones'));

    const nativeFields=new Set(['dob','birthTime','lat','lon','stdLon','dayAyan','daySum','kp-ayanamsha-source','chart-kind','birth-utc-offset','birth-dst-minutes','pc-natal-date','pc-natal-time']);
    let timer;function changed(event){if(event?.target&&!nativeFields.has(event.target.id))return;clearTimeout(timer);timer=setTimeout(()=>{refreshDasha();refreshGemstones();window.KPPersonalPredictions?.refresh();invalidateSlices();},180);}
    document.addEventListener('input',changed);document.addEventListener('change',changed);['chart-saved','chart-manual-change','kp-preferences-changed'].forEach(name=>window.addEventListener(name,changed));
    $('prediction').addEventListener('click',event=>{if(event.target.closest('#pred-print'))window.KPReportPreview?.open('prediction');});
    refreshDasha();refreshGemstones();window.renderReport?.();
  }
  window.KPDashaFal=Object.freeze({analyze:analyzeDasha,year:analyzeDashaYear,refresh:refreshDasha,getData:()=>refreshDasha(),csv:dashaCSV,snapshot:dashaSnapshot,at:dashaAt,current:currentDasha});
  window.KPGemstones=Object.freeze({evaluate:evaluateGemstones,refresh:refreshGemstones,getData:()=>refreshGemstones(),csv:gemstoneCSV,snapshot:gemstoneSnapshot});
  window.KPTimeSlices=Object.freeze({scan:scanSlices,validate:validateSlice,sample:sampleChart,openSample:transferSlice,getData:()=>sliceData,refresh:refreshSlices,invalidate:invalidateSlices,csv:sliceCSV,snapshot:sliceSnapshot});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize);else initialize();
})();
