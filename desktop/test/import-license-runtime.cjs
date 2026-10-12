'use strict';
// Exercise a supplied signed license in a copied project. The System ID fixture
// exists only in that temporary copy; the released native reader is unchanged.
const {_electron}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os');
const {normalizedId,keyId}=require('../licensing/core.cjs');
const {approvedKeys,parseAdditionalKeys,verifyTrustedLicense}=require('../licensing/trust.cjs');
(async()=>{
 const [licenseFile,inputId]=process.argv.slice(2);if(!licenseFile||!inputId)throw Error('Usage: node test/import-license-runtime.cjs <signed .kplicense> <client System ID>');
 const id=normalizedId(inputId),root=path.resolve(__dirname,'..'),temporary=await fs.mkdtemp(path.join(os.tmpdir(),'kp-supplied-license-')),project=path.join(temporary,'customer');await fs.mkdir(project);
 const keys=approvedKeys(await fs.readFile(path.join(root,'app','owner-public-key.pem'),'utf8'),parseAdditionalKeys(await fs.readFile(path.join(root,'app','additional-owner-public-keys.json'),'utf8')));
 const text=await fs.readFile(licenseFile,'utf8'),verified=verifyTrustedLicense(text,keys,id);
 for(const f of ['main.cjs','policy.cjs','preload.cjs','package.json'])await fs.copyFile(path.join(root,f),path.join(project,f));
 await fs.cp(path.join(root,'licensing'),path.join(project,'licensing'),{recursive:true});await fs.cp(path.join(root,'app'),path.join(project,'app'),{recursive:true});
 const reader=path.join(project,'licensing','system-id.cjs');await fs.writeFile(reader,'// TEST COPY ONLY\nexports.getSystemId=async()=>'+JSON.stringify(id)+';\n');
 const options={executablePath:require('electron'),args:[project,...(process.platform==='linux'?['--no-sandbox','--disable-gpu']:[]),'--user-data-dir='+path.join(temporary,'profile')],env:{...process.env,XDG_CONFIG_HOME:path.join(temporary,'config')},timeout:60000};let app;
 try{
  app=await _electron.launch(options);let page=await app.firstWindow();await page.waitForFunction('document.getElementById("system-id")?.value.startsWith("KP1-")');
  const requestFile=path.join(temporary,'KP-System-ID.txt');await app.evaluate(({dialog},f)=>{dialog.showSaveDialog=async()=>({canceled:false,filePath:f});},requestFile);await page.locator('#export').click();await page.waitForFunction('document.getElementById("status").textContent.includes("saved")');const requestText=await fs.readFile(requestFile,'utf8');assert(requestText.includes('System ID: '+id));for(const key of keys)assert(requestText.includes(keyId(key)));assert(requestText.includes('Activation request · 1.2.0'));
  const status=await page.evaluate('KPLicensing.status()');assert.equal(status.systemId,id);assert.equal(status.active,false);assert.deepEqual(status.ownerKeyIds,keys.map(keyId));assert.equal(await page.evaluate('typeof KPAutomaticCalculations'),'undefined');
  await page.locator('#language').selectOption('mr');assert.equal(await page.locator('#owner-keys-label').innerText(),'स्वीकृत मालक किल्ली ID');await page.locator('#language').selectOption('en');
  const altered=JSON.parse(text),claims=JSON.parse(Buffer.from(altered.payload,'base64url'));claims.expiresAt=null;altered.payload=Buffer.from(JSON.stringify(claims)).toString('base64url');const alteredFile=path.join(temporary,'altered.kplicense');await fs.writeFile(alteredFile,JSON.stringify(altered));
  await app.evaluate(({dialog},f)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[f]});},alteredFile);await page.locator('#activate').click();await page.waitForFunction('document.getElementById("status").textContent.includes("has been changed")');assert.equal((await page.evaluate('KPLicensing.status()')).active,false);
  await app.evaluate(({dialog},f)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[f]});},path.resolve(licenseFile));await page.locator('#activate').click();await page.waitForURL('**/app/index.html',{timeout:120000});await page.waitForFunction('currentKPModel?.ready',null,{timeout:120000});assert.equal(await page.locator('#system-id').count(),0);
  const data=await app.evaluate(({app})=>app.getPath('userData'));assert.equal((await fs.readFile(path.join(data,'system-license.json'),'utf8')),text);assert.equal(verifyTrustedLicense(text,keys,id).ownerKeyId,verified.ownerKeyId);
  await app.close();app=null;app=await _electron.launch(options);page=await app.firstWindow();await page.waitForURL('**/app/index.html',{timeout:120000});await page.waitForFunction('currentKPModel?.ready',null,{timeout:120000});
  console.log('PASS supplied license: approved owner signature and exact System ID; actual UI import opens offline engine; unchanged expiry; activation persists across restart; altered file rejected.');
  await app.close();app=null;await fs.copyFile(path.join(root,'licensing','system-id.cjs'),reader);
  assert.notEqual(await require('../licensing/system-id.cjs').getSystemId(),id,'The native test computer must differ from the supplied client.');
  app=await _electron.launch(options);page=await app.firstWindow();await page.waitForSelector('#system-id');await page.waitForFunction('document.getElementById("status").textContent.includes("different computer")');assert.equal((await page.evaluate('KPLicensing.status()')).active,false);assert.equal(await page.evaluate('typeof KPAutomaticCalculations'),'undefined');
  console.log('PASS restored native reader: copied supplied license is rejected on this actual different computer; no shipping System ID override or production private key used.');
  console.log('Artifacts: '+temporary+' (customer license remains outside release files).');
 }finally{if(app)await app.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
