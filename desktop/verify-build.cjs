'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const asar = require('@electron/asar');
const resedit = require('resedit');
const dist=path.join(__dirname,'dist');
const native=path.join(dist,'win-unpacked','KP Master.exe');
const versionNumber=require('./package.json').version;
const launcher=path.join(dist,`KP-Master-Offline-Windows-${versionNumber}-x64.exe`);
const archive=path.join(dist,'win-unpacked','resources','app.asar');
function machine(file) {
  const bytes=fs.readFileSync(file);assert.equal(bytes.toString('ascii',0,2),'MZ');
  const offset=bytes.readUInt32LE(0x3c);assert.equal(bytes.toString('ascii',offset,offset+4),'PE\0\0');
  return bytes.readUInt16LE(offset+4);
}
assert.equal(machine(native),0x8664); // AMD64 packaged runtime
assert.equal(machine(launcher),0x14c); // NSIS portable launcher, supports x64 payload
const nativeExecutable=resedit.NtExecutable.from(fs.readFileSync(native));
const resources=resedit.NtExecutableResource.from(nativeExecutable);
const version=resedit.Resource.VersionInfo.fromEntries(resources.entries)[0];
assert.equal(version.getStringValues(version.getAllLanguagesForStringValues()[0]).ProductName,'KP Master');
assert.ok(resources.entries.some(e=>e.type===14)); // icon group
for(const file of ['main.cjs','policy.cjs','preload.cjs','app/index.html','app/owner-public-key.pem','licensing/core.cjs','licensing/gate.cjs','licensing/system-id.cjs','licensing/activation.html','licensing/activation.js']) {
  assert.deepEqual(asar.extractFile(archive,file),fs.readFileSync(path.join(__dirname,file)));
}
const html=asar.extractFile(archive,'app/index.html').toString('utf8');
assert.ok(html.indexOf('<script id="kp-desktop-files">')>html.indexOf('id="kp-automatic-calculations"'));
assert.ok(html.includes('id="kp-uploaded-house-data"'));
assert.ok(html.includes('id="kp-worksheet-ephemeris') || html.includes('KPWorksheetEphemeris'));
assert.equal(asar.listPackage(archive).some(p=>p.startsWith('/owner/')),false);
const publicPem=asar.extractFile(archive,'app/owner-public-key.pem').toString('utf8');
assert.ok(publicPem.includes('BEGIN PUBLIC KEY'));assert.equal(publicPem.includes('PRIVATE KEY'),false);
const locales=fs.readdirSync(path.join(dist,'win-unpacked','locales')).sort();
assert.deepEqual(locales,['en-US.pak','mr.pak']);
const bytes=fs.readFileSync(launcher);
const sha=crypto.createHash('sha256').update(bytes).digest('hex');
fs.writeFileSync(path.join(dist,'SHA256SUMS.txt'),sha+'  '+path.basename(launcher)+'\n');
console.log(JSON.stringify({launcher:path.basename(launcher),bytes:bytes.length,sha256:sha,windowsRuntime:'x64',portableLauncher:'NSIS',offlineApplicationParity:true,locales},null,2));
