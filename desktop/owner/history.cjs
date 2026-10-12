'use strict';
const fs=require('node:fs/promises'),path=require('node:path');
function validate(rows){if(!Array.isArray(rows)||rows.some(row=>!row||typeof row!=='object'||typeof row.licenseId!=='string'||!row.licenseId))throw Error('The saved license history is invalid. Restore a valid history backup before changing entries.');return rows;}
async function readHistory(file){try{return validate(JSON.parse(await fs.readFile(file,'utf8')));}catch(error){if(error.code==='ENOENT')return [];if(error instanceof SyntaxError)throw Error('The saved license history is invalid. Restore a valid history backup before changing entries.');throw error;}}
async function writeHistory(file,rows){validate(rows);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file+'.tmp',JSON.stringify(rows.slice(0,5000),null,2),{encoding:'utf8',mode:0o600});await fs.rename(file+'.tmp',file);}
function changeRemoval(rows,id,removed,now=new Date()){
 if(typeof id!=='string'||!rows.some(row=>row.licenseId===id))throw Error('The issued license was not found.');
 return rows.map(row=>{if(row.licenseId!==id)return row;const updated={...row};if(removed)updated.removedAt=updated.removedAt||now.toISOString();else delete updated.removedAt;return updated;});
}
const line=value=>String(value??'').replace(/[\r\n\t]/g,' ');
function historyText(rows,language='en',now=new Date()){
 const mr=language==='mr',labels=mr?{title:'KP MASTER · मालक सक्रियकरण · परवाना नोंदी',date:'निर्यात वेळ (UTC)',count:'एकूण नोंदी',note:'दिलेली स्थिती फाइल तयार झाल्याची नोंद आहे. ती ग्राहकाच्या ऑफलाइन संगणकावरील सक्रियतेची पुष्टी नाही.',client:'ग्राहक',system:'System ID',license:'परवाना ID',key:'मालक किल्ली ID',expiry:'अंतिम वेळ (UTC)',issued:'दिल्याची वेळ (UTC)',status:'दिलेली स्थिती',revision:'स्थिती आवृत्ती',changed:'स्थिती दिल्याची वेळ (UTC)',permanent:'कायमस्वरूपी',active:'सक्रियता दिली',inactive:'निष्क्रियता दिली'}:{title:'KP MASTER · Owner Activation · License history',date:'Exported (UTC)',count:'Entries',note:'Issued status records generated files. It does not confirm activation on an offline customer computer.',client:'Client',system:'System ID',license:'License ID',key:'Owner Key ID',expiry:'Expiry (UTC)',issued:'Issued (UTC)',status:'Status issued',revision:'Status revision',changed:'Status issued (UTC)',permanent:'Permanent',active:'Activation issued',inactive:'Deactivation issued'};
 const visible=rows.filter(row=>!row.removedAt),text=[labels.title,labels.date+': '+now.toISOString(),labels.count+': '+visible.length,labels.note,''];
 for(const [index,row]of visible.entries()){
  text.push('['+(index+1)+']');for(const [label,value]of [[labels.client,row.clientName],[labels.system,row.systemId],[labels.license,row.licenseId],[labels.key,row.ownerKeyId],[labels.expiry,row.expiresAt||labels.permanent],[labels.issued,row.issuedAt],[labels.status,row.status==='deactivate'?labels.inactive:labels.active],[labels.revision,row.controlRevision||0],[labels.changed,row.statusIssuedAt||'—']])text.push(label+': '+line(value));text.push('');
 }
 return '\uFEFF'+text.join('\r\n')+'\r\n';
}
module.exports={readHistory,writeHistory,changeRemoval,historyText};
