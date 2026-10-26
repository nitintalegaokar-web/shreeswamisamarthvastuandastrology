'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const methods=['kp-fourfold','kp-sixfold','kp-fourstep-section','nadi-astrology'];
(async()=>{let browser,server;try{
 server=http.createServer((_req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(path.join(root,'index.html')));});
 await new Promise(resolve=>server.listen(18830,'127.0.0.1',resolve));
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:1440,height:900}});page.setDefaultTimeout(30000);
 await page.goto('http://127.0.0.1:18830/',{waitUntil:'load',timeout:120000});
 await page.waitForFunction(()=>document.body.classList.contains('app-ready')&&window.KPReportPreview&&window.KPSinglePageReport,null,{timeout:90000});
 for(const style of ['south','north'])for(const method of methods){
  await page.evaluate(({style,method})=>{KPChartStyle.setStyle(style);const select=document.getElementById('sig-method');select.value=method;select.dispatchEvent(new Event('change',{bubbles:true}));},{style,method});
  const popupPromise=page.waitForEvent('popup');await page.evaluate(()=>KPReportPreview.open('single-page'));const popup=await popupPromise;
  await popup.waitForLoadState('domcontentloaded');await popup.evaluate(()=>document.fonts.ready);await popup.waitForTimeout(250);
  const file='/tmp/kp-single-'+style+'-'+method+'.pdf';await popup.pdf({path:file,format:'A4',printBackground:true,preferCSSPageSize:true});
  const info=execFileSync('pdfinfo',[file],{encoding:'utf8'}),pages=Number(/^Pages:\s+(\d+)/m.exec(info)?.[1]);
  assert.equal(pages,1,style+' '+method+' must print exactly one PDF page');
  const text=execFileSync('pdftotext',['-f','1','-l','1',file,'-'],{encoding:'utf8'}).replace(/\s+/g,' ').trim();
  assert.ok(text.length>80,style+' '+method+' first page must contain report data, not a blank sheet');
  await popup.close();console.log(style,method,'PASS',text.length+' chars');
 }
 for(const style of ['south','north']){
  await page.evaluate(style=>{KPChartStyle.setStyle(style);document.querySelector('[data-tab="nadi-astrology"]')?.click();window.KPNadiAstrology?.calculate();},style);
  const popupPromise=page.waitForEvent('popup');await page.evaluate(()=>KPReportPreview.open('nadi-astrology'));const popup=await popupPromise;
  await popup.waitForLoadState('domcontentloaded');await popup.evaluate(()=>document.fonts.ready);await popup.waitForTimeout(500);
  const layout=await popup.locator('.na-one-page').evaluate(node=>({overflow:node.scrollHeight-node.clientHeight,chart:node.querySelector('.na-report-kundali')?.getBoundingClientRect().height||0,font:parseFloat(getComputedStyle(node).fontSize)}));
  assert.ok(layout.overflow<=2,style+' Nadi report content must remain inside one A4 sheet');assert.ok(layout.chart>=250,style+' Nadi chart must use the available page space');assert.ok(layout.font>=9,style+' Nadi report body must remain readable');
  if(style==='south'&&process.env.NADI_PREVIEW_SCREENSHOT)await popup.locator('.report-page[data-report-section="nadi-astrology"]').screenshot({path:process.env.NADI_PREVIEW_SCREENSHOT});
  const file='/tmp/kp-nadi-report-'+style+'.pdf';await popup.pdf({path:file,format:'A4',printBackground:true,preferCSSPageSize:true});
  const info=execFileSync('pdfinfo',[file],{encoding:'utf8'}),pages=Number(/^Pages:\s+(\d+)/m.exec(info)?.[1]);assert.equal(pages,1,style+' Nadi report must print exactly one PDF page');
  const text=execFileSync('pdftotext',[file,'-'],{encoding:'utf8'}).replace(/\s+/g,' ').trim();assert.ok(text.length>200,style+' Nadi report PDF must contain its report data');
  await popup.close();console.log(style,'Nadi A4 PASS',layout,text.length+' chars');
 }
 {
  const popupPromise=page.waitForEvent('popup');await page.evaluate(()=>KPReportPreview.open('aspects'));const popup=await popupPromise;
  await popup.waitForLoadState('domcontentloaded');await popup.waitForTimeout(300);
  assert.equal(await popup.locator('[data-report-section="aspects"]').count(),2,'Western aspects preview must contain two report pages');
  assert.equal(await popup.locator('[data-aspect-page="planet"] [data-aspect-chart]').getAttribute('data-aspect-chart'),'planet');
  assert.equal(await popup.locator('[data-aspect-page="cusp"] [data-aspect-chart]').getAttribute('data-aspect-chart'),'cusp');
  const file='/tmp/kp-western-aspects.pdf';await popup.pdf({path:file,format:'A4',printBackground:true,preferCSSPageSize:true});
  const info=execFileSync('pdfinfo',[file],{encoding:'utf8'}),pages=Number(/^Pages:\s+(\d+)/m.exec(info)?.[1]);assert.equal(pages,2,'Western aspect charts must print on two separate pages');
  await popup.close();console.log('Western aspects two-page PASS');
 }
 await page.evaluate(()=>KPPreferences.save({...KPPreferences.get(),language:'marathi'}));
 for(const style of ['south','north']){
  await page.evaluate(style=>{KPChartStyle.setStyle(style);const select=document.getElementById('sig-method');select.value='kp-fourfold';select.dispatchEvent(new Event('change',{bubbles:true}));},style);
  const popupPromise=page.waitForEvent('popup');await page.evaluate(()=>KPReportPreview.open('single-page'));const popup=await popupPromise;
  await popup.waitForLoadState('domcontentloaded');await popup.evaluate(()=>document.fonts.ready);await popup.waitForTimeout(900);
  const scale=Number(await popup.locator('.sp-page-inner').getAttribute('data-localized-print-scale'));assert.ok(scale>0&&scale<=1,style+' Marathi report must calculate a valid localized A4 scale');
  const file='/tmp/kp-single-'+style+'-marathi.pdf';await popup.pdf({path:file,format:'A4',printBackground:true,preferCSSPageSize:true});
  const info=execFileSync('pdfinfo',[file],{encoding:'utf8'}),pages=Number(/^Pages:\s+(\d+)/m.exec(info)?.[1]);assert.equal(pages,1,style+' Marathi report must print exactly one PDF page');
  const text=execFileSync('pdftotext',[file,'-'],{encoding:'utf8'}).replace(/\s+/g,' ').trim();assert.match(text,/KP MASTER/,style+' Marathi report footer must remain inside the printed page');
  await popup.close();console.log(style,'Marathi PASS',scale,text.length+' chars');
 }
 }finally{await browser?.close();await new Promise(resolve=>server?.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
