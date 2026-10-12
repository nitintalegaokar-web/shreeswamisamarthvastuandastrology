'use strict';
const {_electron}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process'),core=require('../licensing/core.cjs');
(async()=>{
 const root=path.resolve(__dirname,'..');execFileSync(process.execPath,[path.join(root,'owner','prepare.cjs')]);
 const temp=await fs.mkdtemp(path.join(os.tmpdir(),'kp-easy-activation-')),project=path.join(temp,'owner');await fs.mkdir(project);
 for(const file of ['main.cjs','preload.cjs','index.html','ui.js','license-core.cjs','history.cjs','help.json','package.json','client-request.cjs','client-keys.json'])await fs.copyFile(path.join(root,'owner',file),path.join(project,file));
 const good=crypto.generateKeyPairSync('ed25519'),wrong=crypto.generateKeyPairSync('ed25519'),goodId=core.keyId(good.publicKey),wrongId=core.keyId(wrong.publicKey),pass='Ephemeral-activation-test-123',id=core.systemId({machineGuid:'00112233445566778899aabbccddeeff'});
 await fs.writeFile(path.join(project,'client-keys.json'),JSON.stringify({version:1,ownerKeyIds:[goodId]}));
 for(const [name,pair]of [['good',good],['wrong',wrong]])await fs.writeFile(path.join(temp,name+'.pem'),pair.privateKey.export({format:'pem',type:'pkcs8',cipher:'aes-256-cbc',passphrase:pass}));
 const request=path.join(temp,'request.txt'),badRequest=path.join(temp,'old-customer.txt'),license=path.join(temp,'client.kplicense');await fs.writeFile(request,'KP MASTER · Activation request · 1.2.0\nSystem ID: '+id+'\nAccepted owner Key IDs: '+goodId+'\n');await fs.writeFile(badRequest,'System ID: '+id+'\nAccepted owner Key IDs: '+wrongId+'\n');
 let app;try{
  app=await _electron.launch({executablePath:require('electron'),args:[project,...(process.platform==='linux'?['--no-sandbox','--disable-gpu']:[]),'--user-data-dir='+path.join(temp,'profile')],env:{...process.env,XDG_CONFIG_HOME:path.join(temp,'config')},timeout:60000});const page=await app.firstWindow();await page.waitForFunction('!document.getElementById("open").disabled');
  assert.equal(await page.locator('#create').isVisible(),false);
  const choose=async file=>app.evaluate(({dialog},file)=>{dialog.showOpenDialog=async()=>({canceled:false,filePaths:[file]});},file);
  await choose(path.join(temp,'wrong.pem'));await page.locator('#password').fill(pass);await page.locator('#open').click();await page.waitForFunction('document.getElementById("key-status").classList.contains("key-error")');assert.equal(await page.locator('#issue').isDisabled(),true);await assert.rejects(()=>page.evaluate(id=>KPOwner.issue({clientName:'Test customer',systemId:id,expiryDate:null}),id),/does not match Customer/);
  await choose(path.join(temp,'good.pem'));await page.locator('#password').fill(pass);await page.locator('#open').click();await page.waitForFunction('!document.getElementById("issue").disabled');assert.match(await page.locator('#key-status').innerText(),/Key matches customer software/);
  await choose(badRequest);await page.locator('#import-request').click();await page.waitForFunction('document.getElementById("system").value.startsWith("KP1-")');await page.waitForFunction('document.getElementById("issue").disabled');await assert.rejects(()=>page.evaluate(id=>KPOwner.issue({clientName:'Test customer',systemId:id,expiryDate:null}),id),/different owner key/);
  await choose(request);await page.locator('#import-request').click();await page.waitForFunction('!document.getElementById("issue").disabled');assert.equal(await page.locator('#system').inputValue(),id);await page.locator('#client').fill('Test customer');
  await app.evaluate(({dialog},file)=>{dialog.showSaveDialog=async()=>({canceled:false,filePath:file});},license);await page.locator('#issue').click();await page.waitForFunction('document.getElementById("status").textContent.includes("Licence created:")');const claims=core.verify(await fs.readFile(license,'utf8'),good.publicKey,id);assert.equal(claims.clientName,'Test customer');assert.equal(claims.expiresAt,null);assert.equal((await page.evaluate('KPOwner.history()'))[0].systemId,id);
  await page.locator('#language').selectOption('mr');assert.equal(await page.locator('#import-request').innerText(),'ग्राहकाची System ID फाइल उघडा');assert.match(await page.locator('#key-status').innerText(),/किल्ली जुळली/);
  console.log('PASS easy activation: wrong owner key blocked in UI and backend; request-key mismatch blocked; exact ID imported; matching signed licence and history; English/Marathi compatibility status; new-key creation collapsed. Test keys only.');
 }finally{if(app)await app.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
