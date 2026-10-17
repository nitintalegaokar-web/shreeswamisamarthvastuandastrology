'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const LIMITS=Object.freeze({kundali:15,matchmaking:10});
class DemoStore{
 constructor(file,systemId,{seal=s=>Buffer.from(s),open=b=>b.toString()}={}){this.file=file;this.systemId=systemId;this.seal=seal;this.open=open;}
 read(){let d;try{d=JSON.parse(this.open(fs.readFileSync(this.file)));}catch(e){if(e.code==='ENOENT')return {version:1,systemId:this.systemId,kundali:[],matchmaking:[]};throw Error('Demo usage data could not be verified. Register the software to continue.');}if(d?.version!==1||d.systemId!==this.systemId||Object.keys(LIMITS).some(k=>!Array.isArray(d[k])||d[k].length>LIMITS[k]||new Set(d[k]).size!==d[k].length||d[k].some(v=>!/^[a-f0-9]{64}$/.test(v))))throw Error('Invalid demo usage data. Register the software to continue.');return d;}
 status(){const d=this.read();return {demo:true,limits:LIMITS,used:{kundali:d.kundali.length,matchmaking:d.matchmaking.length},remaining:{kundali:15-d.kundali.length,matchmaking:10-d.matchmaking.length}};}
 use(kind,signature,consume=true){if(!Object.hasOwn(LIMITS,kind)||typeof signature!=='string'||signature.length<3||signature.length>16384)throw Error('Invalid demo request.');const d=this.read(),id=crypto.createHash('sha256').update(signature).digest('hex');if(d[kind].includes(id))return {allowed:true,known:true,...this.status()};if(!consume||d[kind].length>=LIMITS[kind])return {allowed:false,...this.status()};d[kind].push(id);fs.mkdirSync(path.dirname(this.file),{recursive:true});fs.writeFileSync(this.file+'.tmp',this.seal(JSON.stringify(d)),{mode:0o600});fs.renameSync(this.file+'.tmp',this.file);return {allowed:true,known:false,...this.status()};}
}
module.exports={DemoStore,LIMITS};
