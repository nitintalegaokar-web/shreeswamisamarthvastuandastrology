/* Standalone prediction lookup. Astrology calculations are not accessed. */
(()=>{'use strict';
let data;const catalogue=()=>data||(data=JSON.parse(document.getElementById('kp-numerology-data').textContent));
function reduce(digits){let n=[...String(digits)].reduce((sum,d)=>sum+Number(d),0);while(n>9)n=[...String(n)].reduce((sum,d)=>sum+Number(d),0);return n;}
function numbers(text){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(text))throw Error('Enter a valid birth date for Numerology.');
 const date=new Date(text+'T00:00:00Z');if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==text)throw Error('Enter a valid birth date for Numerology.');
 return {date:text,birth:reduce(text.slice(8)),destiny:reduce(text.replaceAll('-',''))};
}
function plain(text){return String(text).replace(/^[ \t]*#{1,6}[ \t]*/gm,'').replace(/\*\*/g,'').replace(/\s*\((?:mul\d\w*|Bha\d)(?:[^)]*)\)/g,'').trim();}
function match(){
 try{
  const result=numbers(document.getElementById('dob').value),marathi=window.KPPreferences?.get?.().language==='marathi';
  const rows=catalogue().records.filter(r=>r.number===(r.kind==='birth'?result.birth:result.destiny)).map(r=>({id:'numerology-'+r.id,language:'marathi',key:r.id,title:(r.kind==='birth'?'मूलांक ':'भाग्यांक ')+r.number,proof:(r.kind==='birth'?'Birth day':'Complete birth date')+' · '+result.date+' → '+r.number,text:plain(r.text),status:'matched'}));
  return {ready:true,rows,numerology:result,context:(marathi?'मूलांक ':'Birth number ')+result.birth+' · '+(marathi?'भाग्यांक ':'Destiny number ')+result.destiny};
 }catch(error){return {ready:false,reason:error.message,rows:[]};}
}
window.KPNumerology=Object.freeze({numbers,match,sources:()=>JSON.parse(JSON.stringify(catalogue().sources))});
})();
