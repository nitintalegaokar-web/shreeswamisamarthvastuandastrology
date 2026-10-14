/* Transit Panchang daily details and calendar preview.
 *
 * This layer reads the existing Transit Panchang inputs and calculation APIs.
 * It does not alter the natal chart, ephemeris, ayanamsha, or house defaults.
 */
(() => {
  'use strict';

  const HOUR = 3600000;
  const IDS = ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
  const WEEKDAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const $ = id => document.getElementById(id);
  const value = id => String($(id)?.value || '').trim();
  const esc = text => String(text ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const norm = angle => ((Number(angle) % 360) + 360) % 360;
  const tr = text => window.KPLanguage?.translate(text) || text;
  let state = null;
  let working = false;
  let calendarSerial = 0;
  let reportInstalled = false;

  function dateOK(text) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return false;
    const date = new Date(text + 'T00:00:00Z');
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0,10) === text && text >= '1900-01-01' && text <= '2100-12-31';
  }

  function coordinate(text) {
    const match = /^([+-]?\d+(?:\.\d+)?)(?::([0-5]?\d))?(?::([0-5]?\d))?$/.exec(String(text || '').trim());
    if (!match) return NaN;
    return (match[1].startsWith('-') ? -1 : 1) * (Math.abs(Number(match[1])) + Number(match[2] || 0) / 60 + Number(match[3] || 0) / 3600);
  }

  function settings() {
    const date = value('tp-date');
    const offset = Number(value('tp-timezone'));
    const latitude = coordinate(value('tp-latitude'));
    const longitude = coordinate(value('tp-longitude'));
    if (!dateOK(date)) throw new Error(tr('Choose a valid date from 1900 through 2100.'));
    if (!Number.isFinite(offset) || Math.abs(offset) > 14) throw new Error(tr('Enter a UTC offset between −14 and +14 hours.'));
    if (!Number.isFinite(latitude) || Math.abs(latitude) >= 89) throw new Error(tr('Enter latitude between −89° and +89°, excluding these limits.'));
    if (!Number.isFinite(longitude) || Math.abs(longitude) > 180) throw new Error(tr('Enter longitude between −180° and +180°.'));
    return {date, offset, latitude, longitude, place:value('tp-place')};
  }

  function localUTC(date, time, offset) {
    return window.KPTransitPanchangDailyEngine.localUTC(date,time,offset);
  }

  function localStamp(moment, offset) {
    return new Date(new Date(moment).getTime() + offset * HOUR).toISOString();
  }

  function dateText(date) {
    return window.KPPreferences?.isConfigured() ? window.KPPreferences.formatDate(date) : date.slice(8,10) + '/' + date.slice(5,7) + '/' + date.slice(0,4);
  }

  function timeTextFromMs(milliseconds, offset) {
    if (!Number.isFinite(milliseconds)) return '—';
    const time = localStamp(new Date(milliseconds), offset).slice(11,19);
    return window.KPPreferences?.isConfigured() ? window.KPPreferences.formatTime(time) : time.slice(0,5);
  }

  function timeRange(interval, offset) {
    if (!interval || !Number.isFinite(interval.start) || !Number.isFinite(interval.end)) return '—';
    return timeTextFromMs(interval.start, offset) + '–' + timeTextFromMs(interval.end, offset);
  }

  function buildChart(config) {
    try {
      if (!window.KPTransitHouses || !window.KPDisplay || !window.KPSouthChart) return {element:null,error:tr('The Transit Kundali calculation is unavailable.')};
      const moment = localUTC(config.date,'05:30:00',config.offset);
      const positions = window.KPEphemeris.positions(moment);
      const houses = window.KPTransitHouses.calculate(moment,config.latitude,config.longitude);
      const before = window.KPEphemeris.positions(new Date(moment.getTime() - 6 * HOUR));
      const after = window.KPEphemeris.positions(new Date(moment.getTime() + 6 * HOUR));
      const retrograde = Object.fromEntries(IDS.map(id => [id,norm(after[id] - before[id]) > 180]));
      const model = window.KPDisplay.build(houses.cusps.map(point => point * 3600),Object.fromEntries(Object.entries(positions).map(([id,longitude]) => [id,longitude * 3600])),{retrograde,conjunctionOrb:window.KPPreferences?.get().conjunctionOrb,ketuAspects:Boolean(window.KPPreferences?.get().ketuAspects)});
      if (!model.ready) throw new Error(model.reason || 'The Transit Kundali could not be calculated.');
      model.planets.forEach(planet => { planet.retrograde = Boolean(retrograde[planet.id]); });
      const element = window.KPSouthChart.fromModel({source:'moment',model,moment:{date:config.date,time:'05:30:00',latitude:config.latitude,longitude:config.longitude,place:config.place}});
      element.classList.add('tp-0530-chart');
      element.dataset.transitPanchangChart = '0530';
      const title = element.querySelector('.v38-title');
      if (title) title.textContent = tr('Transit Kundali · 05:30 AM');
      const info = element.querySelector('.v38-data');
      if (info) {
        info.replaceChildren();
        const rows = [[tr('Date'),dateText(config.date)],[tr('Time'),'05:30'],[tr('Place'),config.place || '—'],[tr('Latitude'),String(config.latitude)],[tr('Longitude'),String(config.longitude)]];
        rows.forEach(([label,text],index) => { if (index) info.append(document.createElement('br')); const strong=document.createElement('b');strong.textContent=label+':';info.append(strong,document.createTextNode(' '+text)); });
      }
      return {element,model,moment:moment.toISOString(),error:null};
    } catch (error) {
      return {element:null,error:error.message || tr('The Transit Kundali could not be calculated.')};
    }
  }

  function calculateDay(config,options={}) {
    if (!window.KPTransitPanchangDailyEngine) throw new Error(tr('The daily Panchang engine is unavailable.'));
    const result = window.KPTransitPanchangDailyEngine.calculate(config,{time:options.time || value('tp-time') || '12:00:00',transitions:options.transitions,useSunrise:Boolean(options.useSunrise)});
    if (options.chart !== false) result.chart = buildChart(config);
    return result;
  }

  function signature(config) {
    return JSON.stringify([config.date,value('tp-time'),config.offset,config.latitude,config.longitude,config.place,value('kp-ayanamsha-source'),value('ayanValue')]);
  }

  function transitionCard(label,current,transition,offset,note='') {
    const end = transition ? timeTextFromMs(transition.end,offset) : '';
    return '<article class="tp-transition-card"><span>'+esc(tr(label))+'</span><strong>'+esc(current)+'</strong><small>'+(transition ? esc(tr('until')+' '+end+' · '+tr('then')+' '+transition.next) : '—')+(note ? '<br>'+esc(note) : '')+'</small></article>';
  }

  function solarCard(label,interval,data,offset,extra='') {
    const displayed = interval && interval.start === interval.end ? timeTextFromMs(interval.start,offset) : timeRange(interval,offset);
    return '<article class="tp-solar-card" data-kind="'+esc(data || '')+'"><span>'+esc(tr(label))+'</span><strong>'+esc(displayed)+'</strong>'+(extra?'<small>'+esc(extra)+'</small>':'')+'</article>';
  }

  function choghadiyaHTML(items,offset,label) {
    return '<div class="tp-chogh-row"><b>'+esc(tr(label))+'</b><div>'+items.map(item => '<span data-quality="'+item.quality+'"><strong>'+esc(item.name)+'</strong><small>'+esc(timeRange(item,offset))+'</small></span>').join('')+'</div></div>';
  }

  function chartOuterHTML(chart) {
    if (!chart?.element) return '<p class="tp-extension-note">'+esc(chart?.error || tr('The Transit Kundali could not be calculated.'))+'</p>';
    const clone = chart.element.cloneNode(true);
    for (const element of [clone,...clone.querySelectorAll('*')]) {
      element.removeAttribute('id');
      element.removeAttribute('tabindex');
      element.removeAttribute('contenteditable');
      for (const attribute of [...element.attributes]) if (/^on/i.test(attribute.name)) element.removeAttribute(attribute.name);
    }
    return clone.outerHTML;
  }

  function extensionHTML(day,includeChart=true) {
    const {config,panchang:p,solar,month,transitions,observances} = day;
    const offset = config.offset;
    const festivals = observances.items.length ? observances.items.map(item => '<li>'+esc(item)+'</li>').join('') : '<li>'+esc(tr('No major recurring vrata or festival is identified by the general sunrise rules for this date.'))+'</li>';
    const auspicious = [solar.abhijit ? {name:'Abhijit Muhurta',...solar.abhijit} : null,solar.brahma ? {name:'Brahma Muhurta',...solar.brahma} : null,...solar.dayChoghadiya.filter(item => item.quality === 'good')].filter(Boolean);
    return '<section class="tp-dinvisesh" data-tp-extension="true">'
      +'<header><div><h3>'+esc(tr('Dinvisesh · Daily Panchang'))+'</h3><p>'+esc(dateText(config.date)+' · '+WEEKDAYS[solar.weekday]+(config.place?' · '+config.place:''))+'</p></div><span class="tp-month-badge">'+esc((month.adhika?'Adhika ':'')+month.name+' · Vikram Samvat '+day.vikramSamvat)+'</span></header>'
      +'<div class="tp-transition-grid">'
      +transitionCard('Tithi',p.tithi,transitions?.tithi,offset,p.paksha+' paksha')
      +transitionCard('Nakshatra',p.nakshatra,transitions?.nakshatra,offset,'Pada '+p.pada+' · '+p.nakLord)
      +transitionCard('Yoga',p.yoga,transitions?.yoga,offset)
      +transitionCard('Karana',p.karana,transitions?.karana,offset)
      +'</div>'
      +'<div class="tp-solar-grid">'
      +solarCard('Sunrise',{start:solar.sunrise,end:solar.sunrise},'good',offset)
      +solarCard('Sunset',{start:solar.sunset,end:solar.sunset},'neutral',offset)
      +solarCard('Abhijit Muhurta',solar.abhijit,solar.abhijit?.recommended?'good':'neutral',offset,solar.abhijit&&!solar.abhijit.recommended?tr('Traditionally avoided on Wednesday'):'')
      +solarCard('Rahu Kaal',solar.rahu,'avoid',offset)
      +solarCard('Yamaganda',solar.yamaganda,'avoid',offset)
      +solarCard('Gulika Kaal',solar.gulika,'avoid',offset)
      +'</div>'
      +'<section class="tp-choghadiya"><h4>'+esc(tr('Choghadiya'))+'</h4>'
      +choghadiyaHTML(solar.dayChoghadiya,offset,'Day')+choghadiyaHTML(solar.nightChoghadiya,offset,'Night')+'</section>'
      +'<div class="tp-day-lists"><section><h4>'+esc(tr('Vrats / festivals'))+'</h4><ul>'+festivals+'</ul><small>'+esc(tr('General sunrise/sunset rules are shown; local sampradaya and regional calendars can differ.'))+'</small></section>'
      +'<section><h4>'+esc(tr('Auspicious periods'))+'</h4><ul>'+auspicious.map(item => '<li><b>'+esc(item.name)+'</b> '+esc(timeRange(item,offset))+'</li>').join('')+'</ul></section></div>'
      +(includeChart?'<section class="tp-chart-card"><h4>'+esc(tr('Same-day 05:30 AM Transit Kundali'))+'</h4><p>'+esc(tr('Calculated independently for this Panchang date, place and UTC offset.'))+'</p>'+chartOuterHTML(day.chart)+'</section>':'')
      +'</section>';
  }

  function render(day) {
    const mount = $('tp-daily-extension');
    if (!mount) return;
    state = {...day,signature:signature(day.config)};
    mount.innerHTML = extensionHTML(day,false);
    window.KPLanguage?.localize(mount);
    window.KPChartTypography?.refresh?.();
  }

  function clear(message='') {
    state = null;
    const mount = $('tp-daily-extension');
    if (mount) mount.innerHTML = message ? '<p class="tp-extension-note">'+esc(message)+'</p>' : '';
  }

  function calculateExtension() {
    if (working) return state;
    working = true;
    try {
      const config = settings();
      const day = calculateDay(config,{chart:false,transitions:true});
      render(day);
      return day;
    } catch (error) {
      clear(error.message || tr('Daily Panchang details could not be calculated.'));
      return null;
    } finally {
      working = false;
    }
  }

  function ensureCurrent() {
    try {
      const config = settings();
      if (!state || state.signature !== signature(config)) return calculateExtension();
      return state;
    } catch (_) {
      return null;
    }
  }

  function reportSnapshot() {
    const day = ensureCurrent();
    if (!day) return '<div class="tp-dinvisesh-report"><p>'+esc(tr('Calculate Transit Panchang to show Dinvisesh.'))+'</p></div>';
    return '<div class="tp-dinvisesh-report">'+extensionHTML(day,false)+'</div>';
  }

  function calendarDay(config) {
    const day = calculateDay(config,{time:'05:30:00',useSunrise:true,transitions:false,chart:false});
    return {date:config.date,weekday:day.solar.weekday,panchang:day.panchang,solar:day.solar,month:day.month,observances:day.observances};
  }

  function calendarShell(preview) {
    const doc = preview.document;
    doc.open();
    doc.write('<!doctype html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(tr('Transit Panchang Calendar'))+'</title><style>'+CALENDAR_CSS+'</style></head><body><nav class="tp-calendar-tools"><button id="cal-prev" type="button">‹ '+esc(tr('Previous month'))+'</button><button id="cal-print" type="button">'+esc(tr('Print / Save PDF'))+'</button><button id="cal-zoom-out" type="button">'+esc(tr('Zoom −'))+'</button><button id="cal-zoom-in" type="button">'+esc(tr('Zoom +'))+'</button><button id="cal-next" type="button">'+esc(tr('Next month'))+' ›</button><button id="cal-close" type="button">'+esc(tr('Close'))+'</button></nav><main id="calendar-root"><p class="tp-calendar-loading">'+esc(tr('Calculating monthly Panchang…'))+'</p></main></body></html>');
    doc.close();
  }

  function calendarHTML(anchor,config,days) {
    const year = Number(anchor.slice(0,4));
    const month = Number(anchor.slice(5,7));
    const firstWeekday = new Date(Date.UTC(year,month-1,1,12)).getUTCDay();
    const cells = Array(firstWeekday).fill('<div class="tp-calendar-empty"></div>');
    for (const day of days) {
      const selected = day.date === value('tp-date');
      const festival = day.observances.items[0] || '';
      cells.push('<article class="tp-calendar-day'+(selected?' is-selected':'')+'" data-weekday="'+day.weekday+'"><header><strong>'+Number(day.date.slice(8,10))+'</strong><span>'+esc(WEEKDAYS[day.weekday].slice(0,3))+'</span></header><p><b>'+esc(day.panchang.tithi)+'</b> · '+esc(day.panchang.paksha)+'</p><p>'+esc(day.panchang.nakshatra)+'</p><small>☀ '+esc(timeTextFromMs(day.solar.sunrise,config.offset))+' · Rahu '+esc(timeRange(day.solar.rahu,config.offset))+'</small>'+(festival?'<em>'+esc(festival)+'</em>':'')+'</article>');
    }
    while (cells.length % 7) cells.push('<div class="tp-calendar-empty"></div>');
    return '<section class="tp-calendar-sheet"><header class="tp-calendar-heading"><div><h1>'+esc(MONTHS[month-1]+' '+year)+'</h1><p>'+esc(tr('Transit Panchang Calendar')+(config.place?' · '+config.place:'')+' · UTC '+(config.offset>=0?'+':'')+config.offset)+'</p></div><div class="tp-calendar-legend"><span data-quality="good">'+esc(tr('Auspicious'))+'</span><span data-quality="avoid">'+esc(tr('Rahu / observance'))+'</span></div></header><div class="tp-calendar-week">'+WEEKDAYS.map(day => '<b>'+esc(day.slice(0,3))+'</b>').join('')+'</div><div class="tp-calendar-grid">'+cells.join('')+'</div><footer>'+esc(tr('Daily Tithi and Nakshatra are evaluated just after local sunrise; if sunrise is unavailable, 05:30 local time is used. Festival labels use general sunrise/sunset rules and may differ by region.'))+'</footer></section>';
  }

  async function fillCalendar(preview,anchor,baseConfig) {
    const token = ++calendarSerial;
    const doc = preview.document;
    const root = doc.getElementById('calendar-root');
    if (!root) return;
    root.innerHTML = '<p class="tp-calendar-loading">'+esc(tr('Calculating monthly Panchang…'))+'</p>';
    const year = Number(anchor.slice(0,4));
    const month = Number(anchor.slice(5,7));
    const count = new Date(Date.UTC(year,month,0)).getUTCDate();
    const days = [];
    try {
      for (let number=1; number<=count; number++) {
        if (token !== calendarSerial || preview.closed) return;
        const date = year+'-'+String(month).padStart(2,'0')+'-'+String(number).padStart(2,'0');
        days.push(calendarDay({...baseConfig,date}));
        if (number % 4 === 0) {
          root.innerHTML = '<p class="tp-calendar-loading">'+esc(tr('Calculating day')+' '+number+' / '+count+'…')+'</p>';
          await new Promise(resolve => setTimeout(resolve,0));
        }
      }
      if (token !== calendarSerial || preview.closed) return;
      root.innerHTML = calendarHTML(anchor,baseConfig,days);
      root.dataset.anchor = anchor;
    } catch (error) {
      root.innerHTML = '<p class="tp-calendar-error">'+esc(error.message || tr('Calendar Panchang could not be calculated.'))+'</p>';
    }
  }

  function shiftMonth(anchor,amount) {
    const date = new Date(anchor + 'T12:00:00Z');
    date.setUTCDate(1);
    date.setUTCMonth(date.getUTCMonth()+amount);
    return date.toISOString().slice(0,7)+'-01';
  }

  function openCalendarPreview() {
    let config;
    try { config = settings(); }
    catch (error) { clear(error.message); return null; }
    const preview = window.open('','_blank','width=1260,height=860');
    if (!preview) return null;
    calendarShell(preview);
    let anchor = config.date.slice(0,7)+'-01';
    let zoom = 1;
    const load = next => { anchor=next; fillCalendar(preview,anchor,config); };
    preview.document.getElementById('cal-prev').addEventListener('click',()=>load(shiftMonth(anchor,-1)));
    preview.document.getElementById('cal-next').addEventListener('click',()=>load(shiftMonth(anchor,1)));
    preview.document.getElementById('cal-print').addEventListener('click',()=>preview.print());
    preview.document.getElementById('cal-close').addEventListener('click',()=>preview.close());
    preview.document.getElementById('cal-zoom-in').addEventListener('click',()=>{zoom=Math.min(1.7,zoom+.1);preview.document.getElementById('calendar-root').style.zoom=zoom;});
    preview.document.getElementById('cal-zoom-out').addEventListener('click',()=>{zoom=Math.max(.6,zoom-.1);preview.document.getElementById('calendar-root').style.zoom=zoom;});
    load(anchor);
    return preview;
  }

  function installReportComposition() {
    if (reportInstalled || typeof window.renderReport !== 'function') return;
    reportInstalled = true;
    const renderReport = window.renderReport;
    window.renderReport = function (...args) {
      const result = renderReport.apply(this,args);
      const cover = document.querySelector('[data-report-section="transit-panchang"] .report-cover');
      if (cover && !cover.querySelector('[data-tp-dinvisesh-report]')) {
        const extension = document.createElement('div');
        extension.dataset.tpDinviseshReport = 'true';
        extension.innerHTML = reportSnapshot();
        cover.append(extension);
        window.KPLanguage?.localize(extension);
      }
      return result;
    };
  }

  function install() {
    const section = $('transit-panchang');
    const actions = section?.querySelector('.almanac-actions');
    const summary = $('tp-summary');
    if (!section || !actions || !summary || !window.KPTransitPanchang || !window.KPTransitPanchangDailyEngine) return false;
    if (!$('tp-calendar-preview')) {
      const button = document.createElement('button');
      button.type = 'button';
      button.id = 'tp-calendar-preview';
      button.className = 'tp-calendar-preview-button';
      button.textContent = tr('Calendar Preview');
      button.addEventListener('click',openCalendarPreview);
      actions.append(button);
    }
    if (!$('tp-daily-extension')) {
      const mount = document.createElement('div');
      mount.id = 'tp-daily-extension';
      mount.className = 'tp-daily-extension';
      summary.after(mount);
    }
    $('tp-calculate')?.addEventListener('click',()=>setTimeout(calculateExtension,0));
    $('tp-now')?.addEventListener('click',()=>setTimeout(calculateExtension,0));
    $('tp-copy-transit')?.addEventListener('click',()=>setTimeout(calculateExtension,0));
    const changed = event => {
      if (!event.target?.matches('#tp-date,#tp-time,#tp-timezone,#tp-place,#tp-latitude,#tp-longitude')) return;
      clear(tr('Settings changed. Calculate to update Dinvisesh.'));
    };
    section.addEventListener('input',changed);
    section.addEventListener('change',changed);
    installReportComposition();
    window.KPLanguage?.localize(section);
    return true;
  }

  function initialize() {
    if (install()) return;
    const section = $('transit-panchang');
    if (!section) return;
    const observer = new MutationObserver(()=>{if(install())observer.disconnect();});
    observer.observe(section,{childList:true,subtree:true});
    window.addEventListener('kp-transit-panchang-daily-engine-ready',()=>{if(install())observer.disconnect();},{once:true});
    setTimeout(()=>{if(install())observer.disconnect();},0);
  }

  const CALENDAR_CSS = `
@page{size:A4 landscape;margin:7mm}*{box-sizing:border-box}html,body{margin:0;background:#e8eef2;color:#183247;font-family:Arial,"Noto Sans Devanagari","Mangal",sans-serif}.tp-calendar-tools{position:sticky;top:0;z-index:10;display:flex;justify-content:center;gap:8px;padding:9px;background:#e8eef2;border-bottom:1px solid #bfd0dc}.tp-calendar-tools button{min-height:32px;padding:5px 11px;border:1px solid #9fb7c8;border-radius:6px;background:#fff;color:#173a52;cursor:pointer}.tp-calendar-tools #cal-print{background:#1f668d;color:#fff;border-color:#1f668d}#calendar-root{padding:10px;transform-origin:top center}.tp-calendar-sheet{width:277mm;min-height:190mm;margin:0 auto;padding:7mm;background:#fff;border:1px solid #bacbd6}.tp-calendar-heading{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid #2c6785;padding-bottom:3mm}.tp-calendar-heading h1{margin:0;font-size:22px}.tp-calendar-heading p{margin:3px 0 0;font-size:10px;color:#587083}.tp-calendar-legend{display:flex;gap:8px;font-size:9px}.tp-calendar-legend span{padding:3px 6px;border-radius:9px}.tp-calendar-legend [data-quality="good"]{background:#dff3e6;color:#0d6d3a}.tp-calendar-legend [data-quality="avoid"]{background:#fde5e9;color:#ae2940}.tp-calendar-week,.tp-calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))}.tp-calendar-week b{text-align:center;padding:2mm;background:#2c6785;color:#fff;border:1px solid #fff;font-size:10px}.tp-calendar-grid{border-left:1px solid #b9c8d2}.tp-calendar-day,.tp-calendar-empty{min-height:25mm;border-right:1px solid #b9c8d2;border-bottom:1px solid #b9c8d2;padding:2mm;overflow:hidden}.tp-calendar-empty{background:#f4f7f8}.tp-calendar-day header{display:flex;justify-content:space-between;align-items:center}.tp-calendar-day header strong{font-size:14px;color:#163e57}.tp-calendar-day header span{font-size:8px;color:#6c7d88}.tp-calendar-day p{margin:1.2mm 0 0;font-size:8.3px;line-height:1.2}.tp-calendar-day small{display:block;margin-top:1.2mm;font-size:7.2px;line-height:1.25;color:#587083}.tp-calendar-day em{display:block;margin-top:1.2mm;padding:1mm;background:#fff0f1;color:#a4293d;font-size:7.2px;font-style:normal;line-height:1.2}.tp-calendar-day[data-weekday="0"] header strong{color:#b7253d}.tp-calendar-day.is-selected{box-shadow:inset 0 0 0 2px #ef9f24;background:#fff9e7}.tp-calendar-sheet footer{margin-top:2mm;font-size:7.5px;line-height:1.3;color:#647785}.tp-calendar-loading,.tp-calendar-error{max-width:500px;margin:20vh auto;padding:20px;text-align:center;background:#fff;border:1px solid #bfd0dc;border-radius:8px}.tp-calendar-error{color:#a02a37}@media print{html,body{background:#fff}.tp-calendar-tools{display:none!important}#calendar-root{padding:0!important;zoom:1!important}.tp-calendar-sheet{width:277mm!important;min-height:190mm!important;margin:0!important;border:0!important;break-after:page;page-break-after:always}}
`;

  window.KPTransitPanchangDinvisesh = Object.freeze({
    calculate:calculateExtension,
    calendarPreview:openCalendarPreview,
    snapshot:reportSnapshot,
    getData:()=>state ? JSON.parse(JSON.stringify({...state,chart:state.chart?{moment:state.chart.moment,error:state.chart.error}:null})) : null,
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',initialize); else initialize();
})();
