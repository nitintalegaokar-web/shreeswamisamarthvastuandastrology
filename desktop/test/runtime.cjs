'use strict';
// Run on Linux with DISPLAY provided by Xvfb, or directly on Windows.
const {_electron} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const licensing = require('../licensing/core.cjs');
const {getSystemId} = require('../licensing/system-id.cjs');
const {execFileSync} = require('node:child_process');
(async () => {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(),'kp-desktop-test-'));
  const chartFile = path.join(temporary,'fixed-native.lkp');
  const pdfFile = path.join(temporary,'marathi-profession-a4.pdf');
  const keys=crypto.generateKeyPairSync('ed25519');
  const publicFile=path.join(temporary,'test-owner-public.pem');
  const licenseFile=path.join(temporary,'test-client.kplicense');
  await fs.writeFile(publicFile,keys.publicKey.export({format:'pem',type:'spki'}));
  await fs.writeFile(licenseFile,JSON.stringify(licensing.issue(keys.privateKey,{systemId:await getSystemId(),clientName:'Desktop runtime test'})));
  execFileSync(process.execPath,[path.join(__dirname,'..','prepare.cjs')],{env:{...process.env,KP_LICENSE_PUBLIC_KEY_FILE:publicFile}});
  const options = {
    executablePath:require('electron'),
    args:[path.resolve(__dirname,'..'), ...(process.platform==='linux'?['--no-sandbox','--disable-gpu']:[]), '--user-data-dir='+path.join(temporary,'profile')],
    env:{...process.env, XDG_CONFIG_HOME:path.join(temporary,'config')},
    timeout:60000
  };
  let desktop;
  try {
    desktop = await _electron.launch(options);
    const page = await desktop.firstWindow();
    await page.waitForFunction('document.getElementById("system-id")?.value.startsWith("KP1-")');
    await desktop.evaluate(({dialog},file)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[file]});},licenseFile);
    await page.locator('#activate').click();
    await page.waitForURL('**/app/index.html',{timeout:120000});
    await page.waitForFunction('document.readyState==="complete" && typeof KPAutomaticCalculations!=="undefined" && typeof KPDesktopFiles!=="undefined"',null,{timeout:120000});
    assert.equal(await page.evaluate('typeof require'), 'undefined');
    const preferences=await desktop.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences());
    assert.equal(preferences.sandbox,true);assert.equal(preferences.nodeIntegration,false);assert.equal(preferences.contextIsolation,true);
    console.log('Desktop opened; isolated renderer verified.');
    await page.evaluate(() => {
      for(const [id,value] of Object.entries({'instant-prashna':'0','name':'Fixed native','dob':'1986-07-15','birthTime':'13:11:00','lat':'18:48:00','lon':'74:13:00','birth-utc-offset':'5.5','stdLon':'82:30:00'})) document.getElementById(id).value=value;
      calculateAll();
    });
    const sample=()=>({ready:currentKPModel.ready,planets:currentKPModel.planets.map(p=>p.longitude),cusps:currentKPModel.houses.map(p=>p.longitude),source:KPBhavSadhan.getData().source});
    const original=await page.evaluate(sample);
    assert.equal(original.ready,true);assert.equal(original.source,'uploaded');
    for(let count=0;count<3;count++) {await page.evaluate('calculateAll()');assert.deepEqual(await page.evaluate(sample),original);}
    console.log('Automatic native chart and repeated degree calculations verified.');
    await desktop.evaluate(({dialog},file) => {
      dialog.showSaveDialog=async()=>({canceled:false,filePath:file});
      dialog.showOpenDialog=async()=>({canceled:false,filePaths:[file]});
    },chartFile);
    assert.equal(await page.evaluate('KPChartFiles.save(getChartData())'),'Saved fixed-native.lkp');
    const saved=JSON.parse(await fs.readFile(chartFile,'utf8'));
    assert.equal(saved.fields.dob.value,'1986-07-15');
    await page.evaluate('document.getElementById("birthTime").value="14:11:00";calculateAll()');
    assert.notDeepEqual(await page.evaluate(sample),original);
    await page.evaluate('KPChartFiles.open().then(async file=>restoreChartData(JSON.parse(await file.text())))');
    assert.deepEqual(await page.evaluate(sample),original);
    console.log('Native Save/Open and saved-chart degree restoration verified.');
    const blocked=await page.evaluate('fetch("https://example.com/").then(()=>false,()=>true)');assert.equal(blocked,true);
    await page.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})');
    await page.waitForSelector('#ed-category',{state:'attached'});
    await page.locator('#quick-education-profession').click();
    await page.locator('#ed-category').selectOption('10');
    const opened=page.waitForEvent('popup');
    await page.locator('#education-profession-preview').click();
    const preview=await opened;
    await preview.waitForSelector('[data-education-cusp="10"]');
    assert.equal(await preview.locator('html').getAttribute('lang'),'mr');
    assert.equal(await preview.locator('#kp-report-a4-contract').count(),1);
    assert.equal(await preview.evaluate('typeof require'),'undefined');
    const pdfBase64=await desktop.evaluate(async ({BrowserWindow}) => {
      const report=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().startsWith('about:blank'));
      if(!report)throw Error('Report popup is missing.');
      const bytes=await report.webContents.printToPDF({pageSize:'A4',preferCSSPageSize:true,printBackground:true});
      return bytes.toString('base64');
    });
    await fs.writeFile(pdfFile,Buffer.from(pdfBase64,'base64'));
    if(process.platform==='linux')execFileSync('python',['-c',
      'import fitz,sys; d=fitz.open(sys.argv[1]); assert len(d)>0; '+
      'assert all(abs(p.rect.width-595.28)<.5 and abs(p.rect.height-841.89)<.5 for p in d); '+
      'assert all(b[0]>=27 and b[2]<=568 for p in d for b in p.get_text("blocks")); print("A4 PDF dimensions and text borders passed")',pdfFile],{stdio:'inherit'});
    await preview.close();
    await desktop.close();desktop=null;
    desktop=await _electron.launch(options);
    const reopened=await desktop.firstWindow();
    await reopened.waitForFunction('document.readyState==="complete" && typeof KPAutomaticCalculations!=="undefined"',null,{timeout:120000});
    assert.equal(await reopened.evaluate('KPPreferences.get().language'),'marathi');
    await desktop.evaluate(({dialog},file)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[file]});},chartFile);
    await reopened.evaluate('KPChartFiles.open().then(async file=>restoreChartData(JSON.parse(await file.text())))');
    assert.deepEqual(await reopened.evaluate(sample),original);
    // Preview windows have no filesystem bridge and cannot invoke native chart dialogs.
    const popupPromise=reopened.waitForEvent('popup');await reopened.evaluate('window.open("","_blank")');
    const blank=await popupPromise;assert.equal(await blank.evaluate('typeof KPDesktopFiles'),'undefined');await blank.close();
    console.log('PASS: offline automatic ephemeris/houses; repeatable native chart; native save/open; restart persistence; Marathi A4 preview; sandboxed windows; network requests blocked.');
    console.log('Test artifacts: '+temporary);
  } finally {if(desktop)await desktop.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
