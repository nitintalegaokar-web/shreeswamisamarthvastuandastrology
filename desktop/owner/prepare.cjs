'use strict';
const fs=require('node:fs');
const path=require('node:path');
fs.copyFileSync(path.join(__dirname,'..','licensing','core.cjs'),path.join(__dirname,'license-core.cjs'));
fs.copyFileSync(path.join(__dirname,'..','licensing','activation-code.cjs'),path.join(__dirname,'activation-code.cjs'));
for(const name of ['feature-policy.cjs','features.json'])fs.copyFileSync(path.join(__dirname,'..','licensing',name),path.join(__dirname,name));
fs.writeFileSync(path.join(__dirname,'feature-catalog.js'),'window.KPFeatureCatalog='+fs.readFileSync(path.join(__dirname,'features.json'),'utf8').trim()+';\n');
console.log('Prepared the activation tool with an encrypted owner credential. No plaintext private key or owner access code is packaged.');
