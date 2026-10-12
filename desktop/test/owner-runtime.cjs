'use strict';
// Full owner calculator, without keys or licenses. Run under Xvfb on Linux.
const {_electron} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
(async () => {
  const project = path.resolve(__dirname,'../owner-edition');
  execFileSync(process.execPath,[path.join(project,'prepare.cjs')],{stdio:'inherit'});
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(),'kp-owner-runtime-'));
  const file = path.join(temporary,'native.lkp');
  let desktop;
  try {
    desktop = await _electron.launch({executablePath:require('electron'),
      args:[project,...(process.platform==='linux'?['--no-sandbox','--disable-gpu']:[]),'--user-data-dir='+path.join(temporary,'profile')],
      env:{...process.env,XDG_CONFIG_HOME:path.join(temporary,'config')},timeout:60000});
    const page = await desktop.firstWindow();
    await page.waitForFunction('document.readyState==="complete" && typeof KPDesktopFiles!=="undefined" && typeof KPHoverDetails!=="undefined"',null,{timeout:120000});
    assert.equal(await page.locator('#system-id').count(),0);
    assert.match(await page.title(),/KP MASTER/);
    assert.equal(await page.evaluate('typeof require'),'undefined');
    assert.equal(await page.locator('.global-actions [data-action="calculate"]').count(),0);
    await page.evaluate(() => {
      KPPreferences.save({...KPPreferences.get(),language:'english',chartStyle:'south'});
      for(const [id,value] of Object.entries({'instant-prashna':'0',name:'Owner test',dob:'1986-07-15',birthTime:'13:11:00',lat:'18:48:00',lon:'74:13:00','birth-utc-offset':'5.5',stdLon:'82:30:00'}))document.getElementById(id).value=value;
      calculateAll();
    });
    const sample=()=>({planets:currentKPModel.planets.map(p=>p.longitude),cusps:currentKPModel.houses.map(p=>p.longitude),source:KPBhavSadhan.getData().source});
    const original = await page.evaluate(sample);
    assert.equal(original.source,'uploaded');
    const save=page.locator('.global-actions [data-action="save-kundali"]');
    const open=page.locator('.global-actions [data-action="open-kundali"]');
    assert.equal((await save.innerText()).trim(),'Save kundali');
    assert.equal((await open.innerText()).trim(),'Open kundali');
    await desktop.evaluate(({dialog},file)=>{
      dialog.showSaveDialog=async()=>({canceled:false,filePath:file});
      dialog.showOpenDialog=async()=>({canceled:false,filePaths:[file]});
    },file);
    await save.click();
    await page.waitForFunction('document.getElementById("save-state").textContent.includes("Saved native.lkp")');
    assert.equal(JSON.parse(await fs.readFile(file,'utf8')).fields.dob.value,'1986-07-15');
    await page.evaluate('document.getElementById("birthTime").value="14:11:00";calculateAll()');
    assert.notDeepEqual(await page.evaluate(sample),original);
    await open.click();
    await page.waitForFunction('document.getElementById("save-state").textContent.includes("Opened native.lkp")');
    assert.deepEqual(await page.evaluate(sample),original);
    await desktop.evaluate(({dialog})=>{dialog.showOpenDialog=async()=>({canceled:true,filePaths:[]});dialog.showSaveDialog=async()=>({canceled:true});});
    await open.click();await save.click();
    assert.deepEqual(await page.evaluate(sample),original);
    await page.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})');
    await page.waitForFunction('document.querySelector("[data-action=save-kundali]").textContent.includes("कुंडली जतन करा")');
    assert.match(await save.innerText(),/Save kundali/);
    assert.match(await open.innerText(),/कुंडली उघडा/);
    const planet=page.locator('#home-kundali [data-hover-dms][data-planet="Su"]:visible').first();
    await planet.hover();await page.waitForSelector('#kp-hover-detail',{state:'visible'});
    assert.equal(await page.locator('[role="tooltip"]:visible').count(),1);
    assert.equal(await page.locator('#kp-hover-detail [data-hover-row]').count(),4);
    await page.mouse.move(1400,900);await page.waitForSelector('#kp-hover-detail',{state:'hidden'});
    console.log('PASS: unlocked owner opens without keys; KP MASTER brand; Open/Save Kundali toolbar and cancellation; saved degree restoration; Marathi bilingual buttons; single vertical tooltip.');
  } finally {if(desktop)await desktop.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
