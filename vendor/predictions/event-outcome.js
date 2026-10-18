
(() => {
  'use strict';
  const $=id=>document.getElementById(id),val=id=>String($(id)?.value??'').trim();
  const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const DAY=86400000,HOUR=3600000,RANGES={day:{label:'Within 24 hours',planet:'As',name:'Ascendant'},month:{label:'Within one month',planet:'Mo',name:'Moon'},year:{label:'Within one year',planet:'Su',name:'Sun'},'13years':{label:'Within 13 years',planet:'Ju',name:'Jupiter'}};
  const unique=list=>[...new Set(list)];
  function assess(data){
    if(!data?.ready)return {promised:false,incomplete:true,reason:data?.reason||'Complete the chart.'};
    if(data.cuspMismatch)return {promised:false,reason:'The selected cusp is not the event’s main cusp.'};
    const uploaded=window.KPEventHouseRules?.assess?.(data);if(uploaded)return uploaded;const marriage=window.KPMarriagePoints?.assess?.(data);if(marriage)return marriage;
    const houses=data.houses||[], label=String(data.rule?.label||'');
    // Customer-requested majority convention; this is an explicit scoring policy,
    // not an additional source-book rule or a prediction of actual lifespan.
    const longevity=/^(short|middle|long) life(?:$| \()/i.exec(label);
    if(longevity){
      const good=[1,5,9,10].filter(h=>houses.includes(h)),adverse=[6,8,12].filter(h=>houses.includes(h));
      const g=good.length/4,a=adverse.length/3;
      if(!g&&!a)return {promised:false,qualified:true,reason:'No longevity-group houses are present; there is insufficient support to classify this selection.'};
      const strongest=g>.5&&a>.5?'middle':g===a?'middle':g>a?'long':'short';
      const selected=longevity[1].toLowerCase(),promised=selected===strongest;
      return {promised,qualified:true,basis:'majority-comparison',strongest,coverage:{supporting:g,adverse:a},reason:'Comparative house support: supporting group '+good.length+'/4 ('+(good.join(', ')||'none')+'); adverse group '+adverse.length+'/3 ('+(adverse.join(', ')||'none')+'). Strongest category: '+strongest+' life'+(g>.5&&a>.5?' (mixed majority support)':'')+'. '+(promised?'The selected category has the strongest support.':'The selected category is weaker than the strongest category.')+' This comparison is not a confirmed lifespan; Saturn, badhaka/maraka and the relevant cusps still require review.'};
    }
    const proofs=data.proofs||[],best=[...proofs].filter(p=>p.required?.length).sort((a,b)=>(b.matched?.length||0)/b.required.length-(a.matched?.length||0)/a.required.length)[0];
    const ratio=best?(best.matched?.length||0)/best.required.length:0;
    const excluded=String(data.rule.remarks||'').match(/not connected to\s+((?:1[0-2]|[1-9])(?:\s*,\s*(?:1[0-2]|[1-9]))*)/i);
    if(excluded){const prohibited=excluded[1].split(',').map(Number),conflicts=houses.filter(h=>prohibited.includes(h));if(conflicts.length)return {promised:false,reason:'The handbook excludes houses '+prohibited.join(', ')+', but the selected chain also signifies '+conflicts.join(', ')+'.'};}
    if(ratio<=.5)return {promised:false,coverage:ratio,reason:'Insufficient house support: '+(best?.matched.length||0)+'/'+(best?.required.length||0)+' required houses match. A strict majority (more than half) is needed; missing: '+(best?.missing.join(', ')||'no evaluable group')+'.'};
    const partial=ratio<1;
    return {promised:true,qualified:partial||data.status==='review',coverage:ratio,basis:partial?'majority-match':'complete-match',reason:(partial?'Majority-match convention: ':'Complete house match: ')+best.matched.length+'/'+best.required.length+' houses match ('+best.matched.join(', ')+').'+(partial?' Remaining houses: '+best.missing.join(', ')+'. Partial support is provisional and does not override additional source conditions.':'')};
  }
  function explanation(data){
    const verdict=assess(data);if(verdict.incomplete)return '<h3>Result: Chart incomplete</h3><p>'+escape(verdict.reason)+'</p>';
    const layers=data.layers.filter(l=>l.selected).map(l=>l.role+' '+l.id+' → '+l.houses.join(', ')).join('; ');
    return '<h3>Result: '+(verdict.promised?'Event is Promised':'Event is not Promised')+(verdict.qualified?' · house criteria':'')+'</h3><p><strong>Reason:</strong> '+escape(verdict.reason)+'</p><p>Cusp '+data.cusp+' · '+escape(data.rule.label)+' · '+escape(layers)+'</p>'+(verdict.qualified?'<p>Additional source conditions: '+escape(data.rule.remarks||data.rule.issues.join('; '))+'. Timing matches remain provisional while these conditions need review.</p>':'');
  }
  function calendarRange(options){
    const date=String(options.startDate||''),time=String(options.startTime||''),offset=options.offset;
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!/^\d{2}:\d{2}(?::\d{2})?$/.test(time)||!Number.isFinite(offset)||Math.abs(offset)>14)throw Error('Enter a valid search start date, time and UTC offset.');
    const parts=time.split(':').map(Number);if(parts.some((n,i)=>n<0||n>=(i?60:24)))throw Error('Enter a valid search start time.');
    const civil=Date.parse(date+'T'+(time.length===5?time+':00':time)+'Z');
    if(!Number.isFinite(civil)||new Date(civil).toISOString().slice(0,10)!==date)throw Error('Enter a valid calendar date.');
    const config=RANGES[options.range];if(!config)throw Error('Select a search period.');
    const endCivil=new Date(civil);
    if(options.range==='day')endCivil.setTime(civil+DAY);
    else{
      const day=endCivil.getUTCDate();endCivil.setUTCDate(1);
      if(options.range==='month')endCivil.setUTCMonth(endCivil.getUTCMonth()+1);
      else endCivil.setUTCFullYear(endCivil.getUTCFullYear()+(options.range==='year'?1:13));
      const last=new Date(Date.UTC(endCivil.getUTCFullYear(),endCivil.getUTCMonth()+1,0)).getUTCDate();endCivil.setUTCDate(Math.min(day,last));
    }
    const start=new Date(civil-offset*HOUR),end=new Date(endCivil.getTime()-offset*HOUR);
    if(start.getTime()<Date.UTC(1900,0,1)||end.getTime()>=Date.UTC(2101,0,1))throw Error('The full search range must be within 1900–2100.');
    return {start,end,config};
  }
  function validate(options){
    const range=calendarRange(options);
    if(!Number.isFinite(options.latitude)||!Number.isFinite(options.longitude)||Math.abs(options.latitude)>=89||Math.abs(options.longitude)>180)throw Error('Enter valid search coordinates.');
    if(options.range==='day'&&Math.abs(options.latitude)>=66.5)throw Error('24-hour Ascendant timing requires a location below 66.5° latitude.');
    const required=KPEventPromise.parseHouses(options.required);if(!required.length)throw Error('Enter the event timing house group. Compound source conditions require an explicit house group.');
    return {...range,required};
  }
  function housesFor(model,id,method,strongest=false){
    if(method==='fourstep')return unique((model.fourstep?.find(row=>row.id===id)?.steps||[]).filter(step=>!step.nil).flatMap(step=>step.houses||[]));
    const row=model[method]?.planets?.find(row=>row.id===id);if(!row)throw Error('Complete the native significator table.');
    let fields=method==='sixfold'?['A','B','C','D','E','F']:['A','B','C','D'];if(strongest&&method==='fourfold')fields=fields.filter(field=>row[field]?.length).slice(0,1);
    return unique(fields.flatMap(field=>row[field]||[]));
  }
  function periodMatches(model,data,range,required,native=KPHomeDasha.getData()){
    const offset=Number(native.timeZoneHours)*HOUR,roots=native.levels?.[0]?.rows||[],lower=range.start.getTime(),upper=range.end.getTime();
    if(!native.ready||!Number.isFinite(offset)||!roots.length)throw Error('Calculate the native Moon and MD / AD / PD timeline first.');
    let covered=lower;for(const root of roots){const a=root.startMs-offset,b=root.endMs-offset;if(b<=covered)continue;if(a>covered)break;covered=Math.max(covered,b);if(covered>=upper)break;}
    if(covered<upper)throw Error('The full search range must lie within the calculated native MD / AD / PD timeline.');
    const cache=new Map(),house=id=>{if(!cache.has(id))cache.set(id,housesFor(model,id,data.method,data.strongest));return cache.get(id);},found=[];
    function walk(parent,chain,a,b){
      if(chain.length===3){
        const layers=chain.map((p,i)=>{const id=KPDisplay.idByName[p.lord]||p.lord;return {level:['MD','AD','PD'][i],id,houses:house(id)};});
        const combined=unique(layers.flatMap(p=>p.houses));
        if(layers.every(p=>required.some(h=>p.houses.includes(h)))&&required.every(h=>combined.includes(h)))found.push({start:new Date(a).toISOString(),end:new Date(b).toISOString(),lords:layers,coverage:layers.map(p=>p.houses.filter(h=>required.includes(h)).length)});
        return;
      }
      for(const child of KPHomeDasha.subdivide(parent)){const from=Math.max(a,child.startMs-offset),to=Math.min(b,child.endMs-offset);if(to>from)walk(child,[...chain,child],from,to);}
    }
    for(const root of roots){const a=Math.max(lower,root.startMs-offset),b=Math.min(upper,root.endMs-offset);if(b>a)walk(root,[root],a,b);}
    return found.sort((a,b)=>a.start.localeCompare(b.start));
  }
  function intersect(transits,periods){
    const found=[];let first=0;
    for(const transit of transits){const a=Date.parse(transit.start),b=Date.parse(transit.end);while(first<periods.length&&Date.parse(periods[first].end)<=a)first++;
      for(let i=first;i<periods.length&&Date.parse(periods[i].start)<b;i++){
        const p=periods[i],start=Math.max(a,Date.parse(p.start)),end=Math.min(b,Date.parse(p.end));
        if(end>start)found.push({...transit,...p,start:new Date(start).toISOString(),end:new Date(end).toISOString(),transitStart:transit.start,transitEnd:transit.end,trigger:transit.planet,startClipped:start!==a||transit.startClipped});
      }
    }
    return found.sort((a,b)=>a.start.localeCompare(b.start));
  }
  function result(){
    if($('ep-outcome-result'))$('ep-outcome-result').innerHTML=explanation(KPEventPromise.getData());
  }
  function snapshot(){return '<div class="ep-outcome-report">'+explanation(KPEventPromise.getData())+'</div>'+KPEventPromise.snapshot();}
  function init(){
    const section=$('event-promise');if(!section)return;
    const resultBox=document.createElement('div');resultBox.id='ep-outcome-result';resultBox.className='ep-outcome-card';$('ep-source-mount')?.after(resultBox);result();
    new MutationObserver(result).observe($('ep-proof-mount'),{childList:true,subtree:true});
    section.addEventListener('change',result);
    ['chart-saved','chart-manual-change','kp-preferences-changed'].forEach(name=>window.addEventListener(name,result));
  }
  window.KPEventOutcome=Object.freeze({snapshot,validate,calendarRange,periodMatches,intersect,assess});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
