/* Pure daily Panchang computation layer.
 *
 * Input is an explicit civil date, UTC offset and location. Output contains
 * only serializable values; this module does not read or change interface
 * controls, natal records, calculation settings, or report markup.
 */
(() => {
  'use strict';

  const DAY = 86400000;
  const HOUR = 3600000;
  const MINUTE = 60000;
  const LUNAR_MONTHS = ['Chaitra','Vaishakha','Jyeshtha','Ashadha','Shravana','Bhadrapada','Ashwin','Kartika','Margashirsha','Pausha','Magha','Phalguna'];
  const DAY_CYCLE = ['Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog'];
  const NIGHT_CYCLE = ['Shubh','Amrit','Char','Rog','Kaal','Labh','Udveg'];
  const DAY_START = [0,3,6,2,5,1,4];
  const NIGHT_START = [0,2,4,6,1,3,5];
  const RAHU_EIGHTH = [8,2,7,5,6,4,3];
  const YAMAGANDA_EIGHTH = [5,4,3,2,1,7,6];
  const GULIKA_EIGHTH = [7,6,5,4,3,2,1];
  const GOOD_CHOGHADIYA = new Set(['Amrit','Shubh','Labh']);
  const NEUTRAL_CHOGHADIYA = new Set(['Char']);
  const norm = angle => ((Number(angle) % 360) + 360) % 360;

  function dateOK(text) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(text || ''))) return false;
    const date = new Date(text + 'T00:00:00Z');
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0,10) === text && text >= '1900-01-01' && text <= '2100-12-31';
  }

  function validate(config) {
    const normalized = {
      date:String(config?.date || ''),
      offset:Number(config?.offset),
      latitude:Number(config?.latitude),
      longitude:Number(config?.longitude),
      place:String(config?.place || ''),
    };
    if (!dateOK(normalized.date)) throw new Error('Choose a valid date from 1900 through 2100.');
    if (!Number.isFinite(normalized.offset) || Math.abs(normalized.offset) > 14) throw new Error('Enter a UTC offset between −14 and +14 hours.');
    if (!Number.isFinite(normalized.latitude) || Math.abs(normalized.latitude) >= 89) throw new Error('Enter latitude between −89° and +89°, excluding these limits.');
    if (!Number.isFinite(normalized.longitude) || Math.abs(normalized.longitude) > 180) throw new Error('Enter longitude between −180° and +180°.');
    return normalized;
  }

  function addDays(date, amount) {
    return new Date(Date.parse(date + 'T00:00:00Z') + amount * DAY).toISOString().slice(0,10);
  }

  function localUTC(date, time, offset) {
    return window.KPEphemeris.dateValue(new Date(Date.parse(date + 'T' + time + 'Z') - offset * HOUR));
  }

  function positionPair(milliseconds, cache) {
    const key = Math.round(milliseconds);
    if (cache.has(key)) return cache.get(key);
    const moment = new Date(key);
    const result = {sun:window.KPEphemeris.longitude(moment,'Su'),moon:window.KPEphemeris.longitude(moment,'Mo')};
    cache.set(key,result);
    return result;
  }

  function panchangAt(milliseconds, date, cache) {
    const point = positionPair(milliseconds,cache);
    return window.KPSinglePageReport.panchang(point.sun * 3600,point.moon * 3600,date);
  }

  function transitionAngle(kind, milliseconds, cache) {
    const point = positionPair(milliseconds,cache);
    if (kind === 'nakshatra') return point.moon;
    if (kind === 'yoga') return norm(point.sun + point.moon);
    return norm(point.moon - point.sun);
  }

  function nextTransition(kind, start, date, cache) {
    const step = kind === 'tithi' ? 12 : kind === 'karana' ? 6 : 360 / 27;
    const startAngle = transitionAngle(kind,start,cache);
    const required = step - (((startAngle % step) + step) % step);
    let lower = start;
    let upper = start + 3 * HOUR;
    let progress = 0;
    let previous = startAngle;
    const limit = start + 4 * DAY;
    while (upper <= limit) {
      const angle = transitionAngle(kind,upper,cache);
      progress += norm(angle - previous);
      if (progress + 1e-9 >= required) break;
      lower = upper;
      upper += 3 * HOUR;
      previous = angle;
    }
    if (upper > limit) return null;
    for (let iteration=0; iteration<45 && upper-lower>500; iteration++) {
      const middle = (lower + upper) / 2;
      if (norm(transitionAngle(kind,middle,cache) - startAngle) >= required) upper = middle;
      else lower = middle;
    }
    const end = Math.round(upper);
    const after = panchangAt(end + 1000,date,cache);
    return {end,next:kind === 'tithi' ? after.tithi : kind === 'karana' ? after.karana : kind === 'nakshatra' ? after.nakshatra : after.yoga};
  }

  function searchSun(date, latitude, longitude, offset, direction) {
    try {
      const start = new Date(Date.parse(date + 'T00:00:00Z') - offset * HOUR);
      const observer = new Astronomy.Observer(latitude,longitude,0);
      const event = Astronomy.SearchRiseSet(Astronomy.Body.Sun,observer,direction,start,1.05);
      const milliseconds = event?.date?.getTime();
      return Number.isFinite(milliseconds) && milliseconds >= start.getTime() && milliseconds < start.getTime() + DAY ? milliseconds : NaN;
    } catch (_) {
      return NaN;
    }
  }

  function segment(name,start,end) {
    return {name,start,end,quality:GOOD_CHOGHADIYA.has(name) ? 'good' : NEUTRAL_CHOGHADIYA.has(name) ? 'neutral' : 'avoid'};
  }

  function choghadiya(start,end,weekday,night) {
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return [];
    const cycle = night ? NIGHT_CYCLE : DAY_CYCLE;
    const first = (night ? NIGHT_START : DAY_START)[weekday];
    const span = (end - start) / 8;
    return Array.from({length:8},(_,index)=>segment(cycle[(first+index)%7],start+index*span,start+(index+1)*span));
  }

  function eighth(start,end,number) {
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
    const span = (end - start) / 8;
    return {start:start+(number-1)*span,end:start+number*span};
  }

  function solarDay(config) {
    const weekday = new Date(config.date + 'T12:00:00Z').getUTCDay();
    const sunrise = searchSun(config.date,config.latitude,config.longitude,config.offset,1);
    const sunset = searchSun(config.date,config.latitude,config.longitude,config.offset,-1);
    const nextSunrise = searchSun(addDays(config.date,1),config.latitude,config.longitude,config.offset,1);
    const previousSunset = searchSun(addDays(config.date,-1),config.latitude,config.longitude,config.offset,-1);
    const dayLength = Number.isFinite(sunrise) && Number.isFinite(sunset) && sunset > sunrise ? sunset - sunrise : NaN;
    const solarNoon = Number.isFinite(dayLength) ? sunrise + dayLength / 2 : NaN;
    const abhijit = Number.isFinite(dayLength) ? {start:solarNoon-dayLength/30,end:solarNoon+dayLength/30,recommended:weekday !== 3} : null;
    const nightLength = Number.isFinite(previousSunset) && Number.isFinite(sunrise) && sunrise > previousSunset ? sunrise - previousSunset : NaN;
    const brahma = Number.isFinite(nightLength) ? {start:sunrise-2*nightLength/15,end:sunrise-nightLength/15} : null;
    return {
      weekday,sunrise,sunset,nextSunrise,previousSunset,dayLength,abhijit,brahma,
      rahu:eighth(sunrise,sunset,RAHU_EIGHTH[weekday]),
      yamaganda:eighth(sunrise,sunset,YAMAGANDA_EIGHTH[weekday]),
      gulika:eighth(sunrise,sunset,GULIKA_EIGHTH[weekday]),
      dayChoghadiya:choghadiya(sunrise,sunset,weekday,false),
      nightChoghadiya:choghadiya(sunset,nextSunrise,weekday,true),
    };
  }

  function lunarMonth(milliseconds) {
    try {
      let cursor = new Date(milliseconds - 35 * DAY);
      let previous = null;
      for (let iteration=0; iteration<3; iteration++) {
        const candidate = Astronomy.SearchMoonPhase(0,cursor,40)?.date;
        if (!candidate || candidate.getTime() > milliseconds) break;
        previous = candidate;
        cursor = new Date(candidate.getTime() + MINUTE);
      }
      const next = Astronomy.SearchMoonPhase(0,new Date(milliseconds + 1000),40)?.date;
      if (!previous || !next) throw new Error('New moon search unavailable.');
      const previousSign = Math.floor(norm(window.KPEphemeris.longitude(previous,'Su')) / 30);
      const nextSign = Math.floor(norm(window.KPEphemeris.longitude(next,'Su')) / 30);
      const index = (previousSign + 1) % 12;
      return {index,name:LUNAR_MONTHS[index],adhika:previousSign === nextSign,previous:previous.toISOString(),next:next.toISOString()};
    } catch (_) {
      return {index:null,name:'—',adhika:false,previous:null,next:null};
    }
  }

  function vikramSamvat(date,monthIndex) {
    const year = Number(date.slice(0,4));
    const civilMonth = Number(date.slice(5,7));
    if (civilMonth < 3) return year + 56;
    if (civilMonth > 3) return year + 57;
    return year + (monthIndex === 0 ? 57 : 56);
  }

  function festivalRules(config,solar,month,cache) {
    const sunriseMoment = Number.isFinite(solar.sunrise) ? solar.sunrise + MINUTE : localUTC(config.date,'05:30:00',config.offset).getTime();
    const sunsetMoment = Number.isFinite(solar.sunset) ? solar.sunset : localUTC(config.date,'18:00:00',config.offset).getTime();
    const dawn = panchangAt(sunriseMoment,config.date,cache);
    const dusk = panchangAt(sunsetMoment,config.date,cache);
    const festivals = [];
    if ([10,25].includes(dawn.tithiIndex)) festivals.push((dawn.tithiIndex < 15 ? 'Shukla' : 'Krishna') + ' Ekadashi vrata');
    if (dawn.tithiIndex === 14) festivals.push('Purnima vrata');
    if (dawn.tithiIndex === 29) festivals.push('Amavasya observance');
    if (dawn.tithiIndex === 18) festivals.push('Sankashti Chaturthi');
    if (dawn.tithiIndex === 3) festivals.push('Vinayaka Chaturthi');
    if ([12,27].includes(dusk.tithiIndex)) festivals.push('Pradosha vrata');
    if (dawn.tithiIndex === 28) festivals.push('Masik Shivaratri');
    if (month.index === 0 && dawn.tithiIndex === 8) festivals.push('Rama Navami');
    if (month.index === 4 && dawn.tithiIndex === 14) festivals.push('Raksha Bandhan / Shravana Purnima');
    if (month.index === 5 && dawn.tithiIndex === 3) festivals.push('Ganesh Chaturthi');
    if (month.index === 6 && dawn.tithiIndex === 9) festivals.push('Vijayadashami');
    if (month.index === 6 && dawn.tithiIndex === 14) festivals.push('Sharad Purnima');
    if (month.index === 7 && dawn.tithiIndex === 29) festivals.push('Deepavali Amavasya');
    const midnight = localUTC(config.date,'00:00:00',config.offset).getTime();
    const sunStart = positionPair(midnight,cache).sun;
    const sunEnd = positionPair(midnight + DAY,cache).sun;
    if (Math.floor(sunStart/30) !== Math.floor(sunEnd/30)) festivals.push('Sankranti (solar ingress occurs today)');
    return {dawn,dusk,items:[...new Set(festivals)]};
  }

  function calculate(source,options={}) {
    if (!window.KPEphemeris || !window.KPSinglePageReport?.panchang || !window.Astronomy) throw new Error('The offline Panchang calculation is unavailable.');
    const config = validate(source);
    const solar = solarDay(config);
    const selected = /^\d{2}:\d{2}$/.test(options.time || '') ? options.time + ':00' : options.time;
    const time = /^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$/.test(selected || '') ? selected : '12:00:00';
    const moment = options.useSunrise && Number.isFinite(solar.sunrise) ? solar.sunrise + MINUTE : localUTC(config.date,time,config.offset).getTime();
    const cache = new Map();
    const panchang = panchangAt(moment,config.date,cache);
    const month = lunarMonth(moment);
    const transitions = options.transitions === false ? null : {
      tithi:nextTransition('tithi',moment,config.date,cache),
      nakshatra:nextTransition('nakshatra',moment,config.date,cache),
      yoga:nextTransition('yoga',moment,config.date,cache),
      karana:nextTransition('karana',moment,config.date,cache),
    };
    const observances = festivalRules(config,solar,month,cache);
    return {config,moment:new Date(moment).toISOString(),panchang,solar,month,vikramSamvat:vikramSamvat(config.date,month.index),transitions,observances};
  }

  window.KPTransitPanchangDailyEngine = Object.freeze({calculate,solarDay,nextTransition,lunarMonth,localUTC,validate});
  window.dispatchEvent(new CustomEvent('kp-transit-panchang-daily-engine-ready'));
})();
