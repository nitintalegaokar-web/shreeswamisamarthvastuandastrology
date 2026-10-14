/* User-supplied original KP Tables IV-A and IV-B. Direct integer-arcsecond lookup; no annual interpolation or intraday advance. */
(() => {
  'use strict';
  const source=JSON.parse(document.getElementById('kp-annual-ayanamsha-data').textContent);
  const rows=source.rows,byYear=new Map(rows.map(row=>[row.year,row]));
  const byId=id=>document.getElementById(id),value=id=>(byId(id)?.value||'').trim();
  let timer;
  function enabled(){return true;}
  function set(id,text){const field=byId(id);if(field)field.value=text;}
  function status(text,state='manual'){
    const target=byId('kp-ayanamsha-status');
    if(target){target.textContent=text;target.dataset.state=state;target.dataset.ready=String(state==='ready');}
  }
  function dms(arcSeconds){
    if(!Number.isFinite(arcSeconds))throw new Error('The annual ayanamsha is invalid.');
    const sign=arcSeconds<0?'-':'',total=Math.round(Math.abs(arcSeconds));
    return sign+String(Math.floor(total/3600)).padStart(2,'0')+':'+String(Math.floor(total%3600/60)).padStart(2,'0')+':'+String(total%60).padStart(2,'0');
  }
  function dateValue(value){
    const date=value instanceof Date?new Date(value.getTime()):new Date(value);
    if(!Number.isFinite(date.getTime()))throw new Error('Enter a valid date for the annual ayanamsha table.');
    return date;
  }
  function usable(year){
    const row=byYear.get(year);
    if(!row)throw new Error('The uploaded annual table covers 1861–2103. No value is available for '+year+'.');
    return row;
  }
  function details(value){
    const date=dateValue(value),year=date.getUTCFullYear(),row=usable(year);
    const month=date.getUTCMonth(),day=date.getUTCDate();
    const correction=source.dailyAdditions[day-1]?.[month];
    if(!Number.isInteger(correction))throw new Error('The original KP daily table has no value for this date.');
    return {date:date.toISOString(),year,month:month+1,day,baseline:row.dmsArcSeconds,correction,total:row.dmsArcSeconds+correction,anchor:source.anchor};
  }
  function at(value){return details(value).total/3600;}
  function prepare(){
    set('kp-ayanamsha-source','annual');
    for(const id of ['dayAyan','daySum','ayanValue'])if(byId(id))byId(id).readOnly=true;
    try{
      const birth=value('dob');
      if(!/^\d{4}-\d{2}-\d{2}$/.test(birth))throw new Error('Enter a valid birth date.');
      const date=dateValue(birth+'T00:00:00Z');
      if(date.toISOString().slice(0,10)!==birth)throw new Error('Enter a valid birth date.');
      const result=details(date),daily=result.correction;
      set('dayAyan',dms(result.baseline));set('daySum',dms(daily));set('ayanValue',dms(result.baseline+daily));
      status('Original KP Table IV-A · '+result.year+': '+dms(result.baseline)+' · Table IV-B '+result.day+'/'+result.month+': '+dms(daily)+' · total: '+dms(result.total)+'. Exact supplied values; no interpolation.','ready');
      return true;
    }catch(error){
      ['dayAyan','daySum','ayanValue'].forEach(id=>set(id,''));
      status('Annual ayanamsha unavailable: '+error.message,'error');
      return true;
    }
  }
  function renderReview(){
    const target=byId('kp-ayanamsha-table-source');if(!target)return;
    const heading=document.createElement('p');heading.textContent=source.title+' · '+source.fileName;
    const note=document.createElement('p');note.textContent='243 supplied annual rows, 1861–2103, and 31 × 12 daily additions from Table IV-B. Exact month/day lookup; no interpolation, extrapolation or intraday increment. February 29 uses its supplied cell in leap years. Invalid dates are rejected. Ephemeris instants use their UTC calendar date; the birth worksheet uses the entered birth date.';
    const wrap=document.createElement('div');wrap.className='annual-ayanamsha-table-wrap';wrap.tabIndex=0;wrap.setAttribute('aria-label','Uploaded annual table, scroll to review all years');
    const table=document.createElement('table');table.setAttribute('aria-label','Uploaded annual KP ayanamsha with source consistency');
    const thead=document.createElement('thead'),header=document.createElement('tr');
    ['Year','Uploaded DMS','Uploaded arcseconds','DMS arcseconds','Check'].forEach(text=>{const cell=document.createElement('th');cell.scope='col';cell.textContent=text;header.append(cell);});thead.append(header);table.append(thead);
    const tbody=document.createElement('tbody');
    rows.forEach(row=>{
      const tr=document.createElement('tr');tr.dataset.year=row.year;tr.dataset.conflict=String(!row.consistent);
      [row.year,row.dms,row.arcSeconds,row.dmsArcSeconds,row.consistent?'Agrees':'DMS used'].forEach(text=>{const cell=document.createElement('td');cell.textContent=text;tr.append(cell);});
      tbody.append(tr);
    });table.append(tbody);wrap.append(table);
    const provenance=document.createElement('p');provenance.textContent='Upload SHA-256: '+source.sha256;
    target.replaceChildren(heading,note,wrap,provenance);
  }
  function capture(event){
    if(['dayAyan','daySum','ayanValue','kp-ayanamsha-source'].includes(event.target?.id))prepare();
  }
  document.addEventListener('input',capture,true);document.addEventListener('change',capture,true);
  window.KPAnnualAyanamsha=Object.freeze({enabled,prepare,at,details,format:dms,getTable:()=>JSON.parse(JSON.stringify(source))});
  document.addEventListener('DOMContentLoaded',()=>{
    renderReview();prepare();
    const changed=event=>{
      if(!['dob','kp-ayanamsha-source','dayAyan','daySum'].includes(event.target?.id))return;
      prepare();clearTimeout(timer);timer=setTimeout(()=>window.calculateAll(),90);
    };
    document.addEventListener('input',changed);document.addEventListener('change',changed);
  });
})();
