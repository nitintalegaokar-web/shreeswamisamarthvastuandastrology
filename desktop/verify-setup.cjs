'use strict';
// Inspect the actual setup payload, rather than assuming build configuration was applied.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const asar = require('@electron/asar');
const resedit = require('resedit');
const {getPath7za} = require('app-builder-lib/out/toolsets/7zip');

async function main() {
  const [installerArg, unpackedArg] = process.argv.slice(2);
  if (!installerArg || !unpackedArg) throw new Error('Usage: node verify-setup.cjs <Setup.exe> <verified win-unpacked folder>');
  const installer = path.resolve(installerArg), unpacked = path.resolve(unpackedArg);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'kp-setup-verify-'));
  const seven = await getPath7za();
  const run = args => execFileSync(seven, args, {stdio:'pipe', maxBuffer:8*1024*1024});
  const manifest = JSON.parse(asar.extractFile(path.join(unpacked,'resources','app.asar'),'package.json'));
  const product = manifest.name === 'kp-master-activation' ? 'KP Master Activation' : 'KP Master';
  try {
    const exe = fs.readFileSync(installer);
    assert.equal(exe.toString('ascii',0,2),'MZ');
    const resources = resedit.NtExecutableResource.from(resedit.NtExecutable.from(exe));
    const version = resedit.Resource.VersionInfo.fromEntries(resources.entries)[0];
    const values = version.getStringValues(version.getAllLanguagesForStringValues()[0]);
    assert.equal(values.ProductName, product);
    assert.ok(values.ProductVersion.startsWith(manifest.version));
    run(['t',installer]);
    const uninstallFile = '$R0/Uninstall '+product+'.exe';
    run(['x','-y',installer,uninstallFile,'-o'+temp]);
    const uninstallExe = fs.readFileSync(path.join(temp,uninstallFile));
    assert.equal(uninstallExe.toString('ascii',0,2),'MZ');
    const uninstallResources = resedit.NtExecutableResource.from(resedit.NtExecutable.from(uninstallExe));
    const uninstallVersion = resedit.Resource.VersionInfo.fromEntries(uninstallResources.entries)[0];
    assert.equal(uninstallVersion.getStringValues(uninstallVersion.getAllLanguagesForStringValues()[0]).ProductName,product);
    run(['x','-y',installer,'$PLUGINSDIR/app-64.7z','-o'+temp]);
    const archive = path.join(temp,'$PLUGINSDIR','app-64.7z');
    assert.ok(fs.existsSync(archive));
    run(['t',archive]);
    run(['x','-y',archive,'resources/app.asar',product+'.exe','-o'+path.join(temp,'app')]);
    for (const file of ['resources/app.asar', product+'.exe']) {
      assert.deepEqual(fs.readFileSync(path.join(temp,'app',file)),fs.readFileSync(path.join(unpacked,file)));
    }
    const sha256 = crypto.createHash('sha256').update(exe).digest('hex');
    fs.writeFileSync(installer+'.sha256',sha256+'  '+path.basename(installer)+'\n');
    console.log(JSON.stringify({installer:path.basename(installer),product,version:manifest.version,bytes:exe.length,sha256,payloadParity:true,archiveCRC:true,uninstallerIncluded:true},null,2));
  } finally { fs.rmSync(temp,{recursive:true,force:true}); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
