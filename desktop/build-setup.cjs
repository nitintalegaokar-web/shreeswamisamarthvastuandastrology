'use strict';
// Use electron-builder's standard NSIS wizard. Extract its generated uninstaller
// directly, using the bundled reader, so Linux builds need no Windows execution.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const asar = require('@electron/asar');
const {build, Platform, Arch} = require('electron-builder');
const {UninstallerReader} = require('app-builder-lib/out/targets/nsis/nsisUtil');
// Keep the offline reference data in one compression dictionary.
const archives=require('app-builder-lib/out/targets/archive'),archive=archives.archive;
archives.archive=(format,out,dir,options={})=>archive(format,out,dir,format==='7z'&&options.compression!=='store'?{...options,method:'LZMA2:fb=273',dictSize:256}:options);


async function main() {
  const args = process.argv.slice(2);
  const owner = args.includes('--owner');
  const ownerEdition=args.includes('--owner-edition');
  if(owner&&ownerEdition)throw new Error('Choose either the activation tool or the owner calculator.');
  const projectDir = owner ? path.join(__dirname,'owner') : ownerEdition ? path.join(__dirname,'owner-edition') : __dirname;
  const source = JSON.parse(fs.readFileSync(path.join(projectDir,'package.json')));
  const at = args.indexOf('--prepackaged');
  if (at >= 0 && !args[at+1]) throw new Error('--prepackaged requires a verified package folder');
  const unpacked = at >= 0 ? path.resolve(args[at+1]) : path.join(projectDir,'dist','win-unpacked');
  if (at < 0) {
    execFileSync(process.execPath,[path.join(projectDir,'prepare.cjs')],{cwd:__dirname,stdio:'inherit'});
    const cli = require.resolve('electron-builder/out/cli/cli.js');
    execFileSync(process.execPath,[cli,'--projectDir',projectDir,'--win','dir','--x64','--publish','never',...(process.env.KP_ELECTRON_DIST?['--config.electronDist='+process.env.KP_ELECTRON_DIST]:[])],{stdio:'inherit'});
  }
  assert.ok(fs.existsSync(path.join(unpacked,source.build.productName+'.exe')),
    'Prepackaged application must contain '+source.build.productName+'.exe so installed shortcuts have a valid target.');
  const manifest = JSON.parse(asar.extractFile(path.join(unpacked,'resources','app.asar'),'package.json'));
  assert.equal(manifest.name,source.name);
  const folder = fs.mkdtempSync(path.join(os.tmpdir(),'kp-nsis-build-'));
  const template = require.resolve('app-builder-lib/templates/nsis/installer.nsi');
  const escape = value => value.replace(/\$/g,()=>'$$').replace(/"/g,'$\\"');
  const uninstaller = path.join(folder,'uninstaller.exe');
  const stub = path.join(folder,'stub.nsi'), final = path.join(folder,'setup.nsi');
  const base = {...source.build,compression:'maximum',extraMetadata:{version:manifest.version}};
  const targets = Platform.WINDOWS.createTarget(['nsis'],Arch.x64);
  const options = {projectDir,prepackaged:unpacked,targets,publish:'never'};
  try {
    fs.writeFileSync(stub,'!define BUILD_UNINSTALLER\n!undef UNINSTALLER_OUT_FILE\n!define UNINSTALLER_OUT_FILE "'+escape(uninstaller)+'"\n!include "'+escape(template)+'"\n');
    await build({...options,config:{...base,compression:'store',directories:{output:folder},nsis:{...base.nsis,script:stub,artifactName:'uninstaller-stub.exe'}}});
    await UninstallerReader.exec(path.join(folder,'uninstaller-stub.exe'),uninstaller);
    assert.equal(fs.readFileSync(uninstaller).toString('ascii',0,2),'MZ');
    fs.writeFileSync(final,'!undef UNINSTALLER_OUT_FILE\n!define UNINSTALLER_OUT_FILE "'+escape(uninstaller)+'"\n!include "'+escape(template)+'"\n');
    await build({...options,config:{...base,directories:{output:path.join(projectDir,'dist','setup')},nsis:{...base.nsis,script:final}}});
    console.log('Setup includes the standard NSIS wizard and generated uninstaller for '+source.name+' '+manifest.version+'.');
  } finally { fs.rmSync(folder,{recursive:true,force:true}); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
