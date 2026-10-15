'use strict';
const fs=require('node:fs');
const path=require('node:path');
fs.copyFileSync(path.join(__dirname,'..','licensing','core.cjs'),path.join(__dirname,'license-core.cjs'));
fs.copyFileSync(path.join(__dirname,'..','licensing','activation-code.cjs'),path.join(__dirname,'activation-code.cjs'));
console.log('Prepared the activation tool. No private key is generated or packaged.');
