
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const value = id => byId(id)?.value || '';
  const IDS = ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
  const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
  const NS = 'http://www.w3.org/2000/svg';
  const DAY = 86400000;
  const norm = degrees => ((degrees % 360) + 360) % 360;
  const signed = degrees => ((degrees + 540) % 360) - 180;
  const escape = text => String(text ?? '').replace(/[&<>"']/g,character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  let model = null, calculationSignature = '', realTimeTimer = null, initialized = false;
  function validDate(text) {
    const date = new Date(text + 'T00:00:00Z');
    return /^\d{4}-\d{2}-\d{2}$/.test(text) && Number.isFinite(date.getTime()) && date.toISOString().slice(0,10) === text;
  }
  function coordinate(text) {
    const match = /^([+-]?\d+(?:\.\d+)?)(?::([0-5]?\d))?(?::([0-5]?\d))?$/.exec(String(text || '').trim());
    if (!match) return NaN;
    const magnitude = Math.abs(Number(match[1])) + Number(match[2] || 0) / 60 + Number(match[3] || 0) / 3600;
    return match[1].startsWith('-') ? -magnitude : magnitude;
  }
  function offset() {
    const text = value('tc-timezone');
    const timezone = Number(text);
    if (!text.trim() || !Number.isFinite(timezone) || Math.abs(timezone) > 14) throw new Error('Enter a UTC offset between −14 and +14 hours.');
    return timezone;
  }
  function readMoment() {
    const date = value('tc-date'), rawTime = value('tc-time');
    const time = /^\d{2}:\d{2}$/.test(rawTime) ? rawTime + ':00' : rawTime;
    if (!validDate(date) || date < '1900-01-01' || date > '2100-12-31') throw new Error('Choose a valid date from 1900 through 2100.');
    if (!/^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$/.test(time)) throw new Error('Choose a valid time including hours and minutes.');
    const timezone = offset(), dateUTC = new Date(Date.parse(date + 'T' + time + 'Z') - timezone * 3600000);
    const latitudeText = value('tc-latitude'), longitudeText = value('tc-longitude');
    const latitude = Number(latitudeText), longitude = Number(longitudeText);
    if (!latitudeText.trim() || !Number.isFinite(latitude) || Math.abs(latitude) >= 90) throw new Error('Enter latitude between −90° and +90°, excluding the poles.');
    if (!longitudeText.trim() || !Number.isFinite(longitude) || Math.abs(longitude) > 180) throw new Error('Enter longitude between −180° and +180°.');
    return {dateUTC, localDate:date, localTime:time, timezone, latitude, longitude, place:value('tc-place').trim(), cuspSource:value('tc-cusp-source')};
  }
  function setLocalMoment(date, timezone) {
    const local = new Date(date.getTime() + timezone * 3600000).toISOString();
    byId('tc-date').value = local.slice(0,10);
    byId('tc-time').value = local.slice(11,19);
  }
  function initializeDefaults() {
    if (initialized) return;
    initialized = true;
    const natalOffset = coordinate(value('stdLon')) / 15;
    if (!value('tc-timezone')) byId('tc-timezone').value = Number.isFinite(natalOffset) && Math.abs(natalOffset) <= 14 ? natalOffset : 5.5;
    if (!value('tc-latitude')) { const latitude = coordinate(value('lat')); byId('tc-latitude').value = Number.isFinite(latitude) ? latitude.toFixed(6) : ''; }
    if (!value('tc-longitude')) { const longitude = coordinate(value('lon')); byId('tc-longitude').value = Number.isFinite(longitude) ? longitude.toFixed(6) : ''; }
    if (!value('tc-place')) byId('tc-place').value = value('birthPlace');
    if (!value('tc-date')) {
      setLocalMoment(new Date(), Number(value('tc-timezone')));
      byId('tc-cusp-source').value = window.KPPreferences?.isConfigured()?window.KPPreferences.get().transitCusps:window.currentKPModel?.ready ? 'natal' : 'transit';
    }
  }
  function status(text, state = 'idle') {
    byId('tc-status').textContent = text;
    byId('tc-status').dataset.state = state;
  }
  function empty(text, state = 'idle') {
    model = null; calculationSignature = '';
    for (const [id,span] of [['tc-planets',8],['tc-cusps',7],['tc-planet-nakshatras',2],['tc-cusp-nakshatras',2],['tc-dasha',4],['tc-pd-periods',3]]) {
      byId(id).querySelector('tbody').innerHTML = '<tr><td colspan="' + span + '">' + escape(text) + '</td></tr>';
    }
    for (const id of ['tc-rashi-chart','tc-bhav-chart']) byId(id).textContent = text;
    window.KPFortuna?.updateInfo('tc-fortuna-info',null);
    byId('tc-dasha-status').textContent = 'No current dasha snapshot.';
    byId('tc-chart-source').textContent = 'Calculate the selected moment to show both charts.';
    status(text,state);
  }
  function signature() {
    const natal = window.currentKPModel;
    return JSON.stringify({controls:['tc-date','tc-time','tc-timezone','tc-latitude','tc-longitude','tc-place','tc-cusp-source','tc-kundali-style'].map(value),birth:value('dob'),ayanamsha:value('ayanValue'),ayanamshaSource:value('kp-ayanamsha-source'),houses:natal?.houses?.map(house => [house.id,house.longitude]),fortuna:[window.KPFortuna?.isVisible(),window.KPPreferences?.get?.().fortunaFormula],periods:(window.mdDashaPeriods || []).map(period => [period.lord,period.start,period.end,period.birthElapsedDays])});
  }
  function occupiedHouse(cusps, longitude) {
    for (let index = 0; index < 12; index++) if (norm(longitude - cusps[index]) < norm(cusps[(index + 1) % 12] - cusps[index])) return index + 1;
    throw new Error('The selected cusps do not form twelve ordered houses. Check the natal house calculations.');
  }
  function validateCusps(cusps) {
    if (cusps.length !== 12 || cusps.some(cusp => !Number.isFinite(cusp))) throw new Error('Complete all twelve natal house cusps or choose transit cusps.');
    const spans = cusps.map((cusp,index) => norm(cusps[(index + 1) % 12] - cusp));
    if (spans.some(span => span < 1e-8) || Math.abs(spans.reduce((total,span) => total + span,0) - 360) > 1e-5) throw new Error('Natal cusps must follow zodiac order without duplicate cusps. Choose transit cusps or correct the house worksheet.');
  }
  function dashaAt(localDate) {
    const md = mdFindPeriodAtDate(window.mdDashaPeriods || [],localDate);
    if (!md) return {ready:false, message:'The selected local date is outside the native\'s calculated MD timeline.'};
    const ad = mdFindPeriodAtDate(window.calculateAntardashas?.(md) || [],localDate);
    const periods = ad ? window.KPTransit?.calculatePratyantardashas(md,ad) || [] : [];
    const pd = mdFindPeriodAtDate(periods,localDate);
    if (!ad || !pd) return {ready:false, message:'No calculated AD / PD period covers the selected local date.'};
    return {ready:true, md, ad, pd, periods};
  }
  function degreeText(details) {
    const parts = details.degree.match(/\d+/g);
    return parts ? parts.map(part => part.padStart(2,'0')).join('–') : details.degree;
  }
  function dateText(date) { return window.KPPreferences?.isConfigured()?window.KPPreferences.formatDate(date):date.split('-').reverse().join('/'); }
  function makeRow(cells, attributes = {}) {
    const row = document.createElement('tr');
    for (const [key,val] of Object.entries(attributes)) row.dataset[key] = val;
    cells.forEach((cell,index) => { const element = document.createElement(index ? 'td' : 'th'); if (!index) element.scope = 'row'; element.textContent = cell; row.append(element); });
    return row;
  }
  function tables(data) {
    byId('tc-planets').querySelector('tbody').replaceChildren(...data.planets.map(planet => {
      const details = planet.details;
      const row = makeRow([planet.id,details.signCode,degreeText(details),['Ra','Ke'].includes(planet.id)?'—':planet.retrograde ? 'R' : 'D',details.sgl,details.stl,details.sl,details.ssl],{planet:planet.id,longitude:planet.longitude,motion:planet.motionDegreesPerDay,retrograde:planet.retrograde});
      row.children[2].className = 'tc-dms'; if (planet.retrograde) row.children[3].className = 'tc-retro'; return row;
    }));
    byId('tc-cusps').querySelector('tbody').replaceChildren(...data.cusps.map(cusp => {
      const details = cusp.details;
      const row = makeRow([ROMAN[cusp.id - 1],details.signCode,degreeText(details),details.sgl,details.stl,details.sl,details.ssl],{house:cusp.id,longitude:cusp.longitude}); row.children[2].className = 'tc-dms'; return row;
    }));
    byId('tc-planet-nakshatras').querySelector('tbody').replaceChildren(...data.planets.map(planet => makeRow([planet.id,planet.details.nakshatra + ' · ' + planet.details.pada],{planet:planet.id})));
    byId('tc-cusp-nakshatras').querySelector('tbody').replaceChildren(...data.cusps.map(cusp => makeRow([ROMAN[cusp.id - 1],cusp.details.nakshatra + ' · ' + cusp.details.pada],{house:cusp.id})));
    byId('tc-cusp-title').textContent = (data.cuspSource === 'natal' ? 'Natal house cusps' : 'Transit house cusps · Placidus') + ' · भाव स्पष्ट';
    byId('tc-chart-source').textContent = (data.cuspSource === 'natal' ? 'Natal cusps' : 'Transit Placidus cusps') + ' · Ascendant ' + data.cusps[0].details.sign + ' ' + data.cusps[0].details.degree + '. Current planet positions appear in both charts; R marks retrograde motion.';
    if (!data.dasha.ready) {
      byId('tc-dasha-status').textContent = data.dasha.message;
      byId('tc-dasha').querySelector('tbody').innerHTML = '<tr><td colspan="4">' + escape(data.dasha.message) + '</td></tr>';
      byId('tc-pd-periods').querySelector('tbody').innerHTML = '<tr><td colspan="3">No PD timeline for this date.</td></tr>';
    } else {
      byId('tc-dasha-status').textContent = data.localDate===value('dob')?'Native dasha lords at birth · displayed period dates are rounded to whole days.':'Native dasha lords on ' + dateText(data.localDate) + ' · local date; interval ends are exclusive.';
      byId('tc-dasha').querySelector('tbody').replaceChildren(...[['MD',data.dasha.md],['AD',data.dasha.ad],['PD',data.dasha.pd]].map(([role,period]) => makeRow([role,window.KPDisplay.idByName[period.lord] || period.lord,dateText(period.start),dateText(period.end)],{role,lord:period.lord,start:period.start,end:period.end})));
      byId('tc-pd-periods').querySelector('tbody').replaceChildren(...data.dasha.periods.map(period => { const row = makeRow([window.KPDisplay.idByName[period.lord] || period.lord,dateText(period.start),dateText(period.end)],{lord:period.lord,start:period.start,end:period.end}); row.classList.toggle('tc-active-period',period === data.dasha.pd); return row; }));
    }
  }
  const HOUSE_POLYGONS = [
    [[240,0],[360,100],[240,200],[120,100]], [[0,0],[240,0],[120,100]], [[0,0],[120,100],[0,200]],
    [[0,200],[120,100],[240,200],[120,300]], [[0,200],[120,300],[0,400]], [[0,400],[120,300],[240,400]],
    [[240,200],[360,300],[240,400],[120,300]], [[240,400],[360,300],[480,400]], [[360,300],[480,200],[480,400]],
    [[240,200],[360,100],[480,200],[360,300]], [[480,0],[480,200],[360,100]], [[240,0],[480,0],[360,100]]
  ];
  const CENTRES = [[240,100],[120,33],[40,100],[120,200],[40,300],[120,367],[240,300],[360,367],[440,300],[360,200],[440,100],[360,33]];
  function horizontalBounds(polygon,y) {
    const intersections = [];
    for (let index = 0; index < polygon.length; index++) {
      const left = polygon[index], right = polygon[(index + 1) % polygon.length];
      if (left[1] === right[1]) { if (Math.abs(y - left[1]) < 1e-6) intersections.push(left[0],right[0]); }
      else if (y >= Math.min(left[1],right[1]) && y <= Math.max(left[1],right[1])) intersections.push(left[0] + (y - left[1]) * (right[0] - left[0]) / (right[1] - left[1]));
    }
    return [Math.min(...intersections),Math.max(...intersections)];
  }
  function svgElement(name,attributes = {},text) {
    const element = document.createElementNS(NS,name);
    for (const [key,val] of Object.entries(attributes)) element.setAttribute(key,val);
    if (text !== undefined) element.textContent = text;
    return element;
  }
  function southChart(id,groups,ascSign,kind,cusps) {
    const svg=svgElement('svg',{viewBox:'0 0 480 400',role:'img','aria-label':'South Indian '+(kind==='rashi'?'Rashi':'Bhav')+' chart',preserveAspectRatio:'xMidYMid meet'});
    const slots=[[1,0],[2,0],[3,0],[3,1],[3,2],[3,3],[2,3],[1,3],[0,3],[0,2],[0,1],[0,0]],names=['Ar','Ta','Ge','Ca','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi'];
    const entries=Array.from({length:12},()=>[]);
    groups.forEach((planets,index)=>{const sign=kind==='rashi'?(ascSign+index)%12:cusps[index].details.signIndex;entries[sign].push({index,planets});});
    slots.forEach(([col,row],sign)=>{
      const x=col*120,y=row*100,g=svgElement('g',{'data-sign':sign+1});
      g.append(svgElement('rect',{x,y,width:120,height:100,fill:'#fffdf7',stroke:'#82995c'}));
      g.append(svgElement('text',{x:x+5,y:y+14,fill:'#437225','font-size':11},names[sign]));
      let line=0;
      entries[sign].forEach(({index,planets})=>{
        const label=kind==='bhav'?ROMAN[index]:(index===0?'Lagna':'');
        if(label)g.append(svgElement('text',{x:x+5,y:y+29+line++*12,fill:'#437225','font-size':10,'data-bhava':index+1},label));
        for(let start=0;start<planets.length;start+=3){const text=svgElement('text',{x:x+5,y:y+29+line++*12,'font-size':10,fill:'#293627'});planets.slice(start,start+3).forEach((p,i)=>{if(i)text.append(document.createTextNode(' '));text.append(svgElement('tspan',{'data-planet':p.id,'data-longitude':p.longitude},p.id+(p.retrograde&&!['Ra','Ke'].includes(p.id)?'ᴿ':'')));});g.append(text);}
      });svg.append(g);
    });
    svg.append(svgElement('text',{x:240,y:195,'text-anchor':'middle','font-size':15,fill:'#437225'},kind==='rashi'?'Rashi kundali':'Bhav kundali'));
    byId(id).replaceChildren(svg);
  }
  function chart(id,groups,ascSign,kind,cusps) {
    if(value('tc-kundali-style')==='south')return southChart(id,groups,ascSign,kind,cusps);
    const svg = svgElement('svg',{viewBox:'0 0 480 400',role:'img','aria-label':kind === 'rashi' ? 'North Indian Rashi chart' : 'North Indian Bhav chart',preserveAspectRatio:'xMidYMid meet'});
    svg.append(svgElement('rect',{x:1,y:1,width:478,height:398,fill:'#fffdf7',stroke:'#82995c','stroke-width':2}));
    svg.append(svgElement('path',{d:'M0 0L480 400M480 0L0 400M240 0L480 200L240 400L0 200Z',fill:'none',stroke:'#a4b48d','stroke-width':1.2}));
    groups.forEach((planets,index) => {
      const house = index + 1, sign = kind === 'bhav' ? cusps[index].details.signIndex + 1 : (ascSign + index) % 12 + 1;
      const group = svgElement('g',{'data-house':house,'data-sign':sign});
      const [cx,cy] = CENTRES[index], labelY = cy - 17;
      const bounds = horizontalBounds(HOUSE_POLYGONS[index],labelY);
      group.append(svgElement('text',{x:(bounds[0] + bounds[1]) / 2,y:labelY,'text-anchor':'middle',fill:'#437225','font-size':12,'font-weight':600,...(kind==='bhav'?{'data-bhava':house,'data-no-localize':''}:{})},kind === 'rashi' ? sign + (index === 0 ? ' · Lagna' : '') : ROMAN[index]));
      const rows = [];
      for (let start = 0; start < planets.length; start += 3) rows.push(planets.slice(start,start + 3));
      rows.forEach((row,rowIndex) => {
        const y = cy + rowIndex * 14 + 2, available = horizontalBounds(HOUSE_POLYGONS[index],y);
        const x = (available[0] + available[1]) / 2;
        const text = svgElement('text',{x,y,'text-anchor':'middle',fill:'#293627','font-size':12,'font-weight':500});
        row.forEach((planet,planetIndex) => {
          if (planetIndex) text.append(document.createTextNode('  '));
          text.append(svgElement('tspan',{'data-planet':planet.id,'data-longitude':planet.longitude,fill:planet.retrograde ? '#a84b20' : '#293627'},planet.id + (planet.retrograde&&!['Ra','Ke'].includes(planet.id) ? 'ᴿ' : '')));
        });
        group.append(text);
      });
      svg.append(group);
    });
    byId(id).replaceChildren(svg);
  }
  function calculate() {
    initializeDefaults();
    try {
      const moment = readMoment();
      if (!window.KPEphemeris || !window.KPDisplay) throw new Error('The offline ephemeris is unavailable.');
      const date = window.KPEphemeris.dateValue(moment.dateUTC);
      const positions = window.KPEphemeris.positions(date);
      const beforeTime = Math.max(Date.UTC(1900,0,1),date.getTime() - 21600000);
      const afterTime = Math.min(Date.UTC(2101,0,1) - 1,date.getTime() + 21600000);
      const before = window.KPEphemeris.positions(new Date(beforeTime)), after = window.KPEphemeris.positions(new Date(afterTime));
      const planets = IDS.map(id => {
        const motionDegreesPerDay = signed(after[id] - before[id]) * DAY / (afterTime - beforeTime);
        return {id,longitude:positions[id],details:window.KPDisplay.longitudeDetails(positions[id] * 3600),motionDegreesPerDay,retrograde:motionDegreesPerDay < 0};
      });
      let cuspPositions, cuspSystem;
      if (moment.cuspSource === 'natal') {
        const worksheet = window.syncKPWorksheetPositions?.();
        const natalCusps = worksheet?.cusps || window.currentKPModel?.houses?.map(house => house.longitude);
        if (!natalCusps || natalCusps.length !== 12 || natalCusps.some(cusp => cusp === null || !Number.isFinite(cusp))) throw new Error('Complete the natal house cusp worksheet, or choose transit cusps. Natal planet entries are not required for the transit chart.');
        cuspPositions = natalCusps.map(cusp => cusp / 3600); cuspSystem = 'Natal worksheet';
      } else if (moment.cuspSource === 'transit') {
        if (!window.KPTransitHouses) throw new Error('The transit house calculation is unavailable.');
        const calculated = window.KPTransitHouses.calculate(date,moment.latitude,moment.longitude);
        cuspPositions = calculated.cusps; cuspSystem = calculated.system;
      } else throw new Error('Choose natal or transit house cusps.');
      validateCusps(cuspPositions);
      const cusps = cuspPositions.map((longitude,index) => ({id:index + 1,longitude,details:window.KPDisplay.longitudeDetails(longitude * 3600)}));
      const ascSign = cusps[0].details.signIndex;
      const rashiGroups = Array.from({length:12},() => []), bhavGroups = Array.from({length:12},() => []);
      planets.forEach(planet => { rashiGroups[(planet.details.signIndex - ascSign + 12) % 12].push(planet); bhavGroups[occupiedHouse(cuspPositions,planet.longitude) - 1].push(planet); });
      model = {ready:true,utc:date.toISOString(),localDate:moment.localDate,localTime:moment.localTime,latitude:moment.latitude,longitude:moment.longitude,timezone:moment.timezone,place:moment.place,cuspSource:moment.cuspSource,cuspSystem,ayanamsha:window.KPEphemeris.ayanamsha(date),planets,cusps,rashiGroups,bhavGroups,dasha:dashaAt(moment.localDate)};
      const fortuna=window.KPFortuna?.getTransit(model);
      const displayRashiGroups=rashiGroups.map(group=>[...group]),displayBhavGroups=bhavGroups.map(group=>[...group]);
      if(fortuna){
        const point={id:'Fo',longitude:fortuna.longitudeDegrees,details:fortuna,retrograde:false};
        displayRashiGroups[(fortuna.signIndex-ascSign+12)%12].push(point);
        displayBhavGroups[occupiedHouse(cuspPositions,point.longitude)-1].push(point);
      }
      window.KPFortuna?.updateInfo('tc-fortuna-info',fortuna);
      tables(model); chart('tc-rashi-chart',displayRashiGroups,ascSign,'rashi',cusps); chart('tc-bhav-chart',displayBhavGroups,ascSign,'bhav',cusps);
      calculationSignature = signature();
      status(dateText(model.localDate) + ' · ' + (window.KPPreferences?.isConfigured()?window.KPPreferences.formatTime(model.localTime):model.localTime) + ' · UTC ' + (model.timezone >= 0 ? '+' : '') + model.timezone + (model.place ? ' · ' + model.place : '') + ' · ' + (model.cuspSource === 'natal' ? 'Natal cusps' : 'Transit Placidus cusps'),'ready');
      return getData();
    } catch (error) { empty(error.message || 'The selected moment could not be calculated.','error'); stopRealTime(); return null; }
  }
  function getData() { return model ? JSON.parse(JSON.stringify(model)) : null; }
  function refresh() { initializeDefaults(); return calculate(); }
  function stopRealTime() {
    clearInterval(realTimeTimer); realTimeTimer = null;
    byId('tc-realtime').textContent = 'Start real time'; byId('tc-realtime').setAttribute('aria-pressed','false');
  }
  function now() { initializeDefaults(); try { setLocalMoment(new Date(),offset()); return calculate(); } catch (error) { empty(error.message,'error'); return null; } }
  function step(direction) {
    stopRealTime(); initializeDefaults();
    try {
      const moment = readMoment(), local = new Date(moment.localDate + 'T' + moment.localTime + 'Z'), unit = value('tc-step-size');
      if (unit === 'hour') local.setUTCHours(local.getUTCHours() + direction);
      else if (unit === 'day' || unit === 'week') local.setUTCDate(local.getUTCDate() + direction * (unit === 'week' ? 7 : 1));
      else if (unit === 'month' || unit === 'year') {
        const originalDay = local.getUTCDate(); local.setUTCDate(1);
        if (unit === 'month') local.setUTCMonth(local.getUTCMonth() + direction); else local.setUTCFullYear(local.getUTCFullYear() + direction);
        const end = new Date(local.getTime()); end.setUTCMonth(end.getUTCMonth() + 1,0); local.setUTCDate(Math.min(originalDay,end.getUTCDate()));
      } else throw new Error('Choose an hour, day, week, month or year step.');
      const stamp = local.toISOString(); byId('tc-date').value = stamp.slice(0,10); byId('tc-time').value = stamp.slice(11,19); return calculate();
    } catch (error) { empty(error.message,'error'); return null; }
  }
  function staticClone(id) {
    const source = byId(id), clone = source.cloneNode(true);
    [clone,...clone.querySelectorAll('*')].forEach(element => {
      if (element.id) { element.dataset.reportId = element.id; element.removeAttribute('id'); }
      [...element.attributes].forEach(attribute => { if (/^on/i.test(attribute.name) || ['contenteditable','tabindex','aria-labelledby','aria-controls'].includes(attribute.name)) element.removeAttribute(attribute.name); });
    });
    return clone.outerHTML;
  }
  function snapshot() {
    initializeDefaults(); if (!model || calculationSignature !== signature()) calculate();
    if (!model) return '<div class="tc-report"><p>' + escape(byId('tc-status').textContent) + '</p></div>';
    const metadata = dateText(model.localDate) + ' ' + (window.KPPreferences?.isConfigured()?window.KPPreferences.formatTime(model.localTime):model.localTime) + ' · UTC ' + (model.timezone >= 0 ? '+' : '') + model.timezone + (model.place ? ' · ' + model.place : '') + ' · ' + model.latitude.toFixed(6) + '° N, ' + model.longitude.toFixed(6) + '° E · ' + (model.cuspSource === 'natal' ? 'Natal cusps' : 'Transit Placidus cusps');
    const article = (heading,id) => '<article><h3>' + escape(heading) + '</h3>' + staticClone(id) + '</article>';
    return '<div class="tc-report"><p class="tc-report-summary">' + escape(metadata) + '</p>' + (window.KPFortuna?.getTransit(model)?'<p class="kp-fortuna-info">'+escape(window.KPFortuna.description(window.KPFortuna.getTransit(model)))+'</p>':'') + '<div class="tc-report-grid">' + article('Transit planet positions','tc-planets') + article('Rashi chart','tc-rashi-chart') + article(model.cuspSource === 'natal' ? 'Natal house cusps' : 'Transit house cusps · Placidus','tc-cusps') + article('Bhav chart','tc-bhav-chart') + article('Planet Nakshatra · Pada','tc-planet-nakshatras') + article('Cusp Nakshatra · Pada','tc-cusp-nakshatras') + '<article class="tc-report-dashas"><h3>Native MD / AD / PD at selected date</h3><p class="tc-report-note">' + escape(byId('tc-dasha-status').textContent) + '</p>' + staticClone('tc-dasha') + '<h4>PD periods within this AD</h4>' + staticClone('tc-pd-periods') + '</article></div><p class="tc-report-note">Sidereal geocentric ephemeris; '+escape(window.KPEphemeris.convention())+'. Mean lunar nodes. R denotes retrograde motion. Rashi chart uses whole signs from the selected Ascendant; Bhav chart uses exact selected cusps.</p></div>';
  }
  function initialize() {
    byId('tc-calculate').addEventListener('click',() => { stopRealTime(); calculate(); });
    byId('tc-now').addEventListener('click',() => { stopRealTime(); now(); });
    byId('tc-backward').addEventListener('click',() => step(-1)); byId('tc-forward').addEventListener('click',() => step(1));
    byId('tc-realtime').addEventListener('click',() => {
      if (realTimeTimer) { stopRealTime(); return; }
      if (!now()) return;
      byId('tc-realtime').textContent = 'Stop real time'; byId('tc-realtime').setAttribute('aria-pressed','true');
      realTimeTimer = setInterval(() => { if (!byId('transit-chart').classList.contains('active') || document.hidden) stopRealTime(); else now(); },1000);
    });
    byId('tc-print').addEventListener('click',() => {
      snapshot(); window.renderReport?.(); document.querySelector('.app-sidebar [data-tab="report"]')?.click(); window.KPReportPages?.refresh();
      window.KPReportPages?.selectSections(['transit-chart']); byId('report-page-options')?.focus();
    });
    byId('transit-chart').addEventListener('input',event => { if (!['tc-step-size','tc-kundali-style'].includes(event.target.id)) { stopRealTime(); empty('Settings changed. Calculate to update the transit chart.'); } });
    byId('transit-chart').addEventListener('change',event => { if (['tc-cusp-source','tc-kundali-style'].includes(event.target.id)) { stopRealTime(); calculate(); } });
    const observer = new MutationObserver(() => { if (!byId('transit-chart').classList.contains('active')) stopRealTime(); }); observer.observe(byId('transit-chart'),{attributes:true,attributeFilter:['class']});
    document.addEventListener('visibilitychange',() => { if (document.hidden) stopRealTime(); });
    setTimeout(() => { initializeDefaults(); calculate(); },350);
  }
  window.KPTransitChart = Object.freeze({calculate,refresh,getData,snapshot,step,now,stopRealTime});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',initialize); else initialize();
})();
