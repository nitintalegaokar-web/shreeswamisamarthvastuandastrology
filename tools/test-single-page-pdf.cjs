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
 }finally{await browser?.close();await new Promise(resolve=>server?.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
