'use strict';
const fs=require('node:fs');
const path=require('node:path');
fs.copyFileSync(path.join(__dirname,'..','licensing','core.cjs'),path.join(__dirname,'license-core.cjs'));
console.log('Prepared the activation tool. No private key is generated or packaged.');
