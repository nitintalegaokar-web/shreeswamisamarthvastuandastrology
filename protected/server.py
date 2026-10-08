#!/usr/bin/env python3
"""Private calculation worker and thin browser UI. Never serves engine files."""
import argparse
import base64
import concurrent.futures
import json
import os
from pathlib import Path
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TABS = ['ayan', 'lmt', 'stcalc', 'raphael5', 'planet']
MAX_BODY = 5_000_000
BOOT = r"""() => {
 window.KPClientPresentation.setClient(true);
 for(const id of ['st-ephemeris-source','p6-ephemeris-source'])document.getElementById(id).value='automatic';
 document.getElementById('kp-ayanamsha-source').value='annual';
 document.querySelectorAll('.formula,.formula-text,.raphael5-formulas,.md-main,.md-subtitle,.md-rule,.md-formula-row,.md-calc-line').forEach(n=>n.dataset.privateCalculation='true');
 document.getElementById('settings-pane-calculation')?.setAttribute('data-private-calculation','true');
 document.getElementById('settings-tab-calculation')?.setAttribute('data-private-calculation','true');
 const original=window.calculateAll;
 window.calculateAll=function(){original();if(document.getElementById('chart-kind').value!=='horary'){
   try {const moment=KPHorary.nativeMoment();const house=KPTransitHouses.calculate(moment.date,moment.latitude,moment.longitude);
    for(const h of [10,11,12,1,2,3]){const t=Math.round(house.cusps[h-1]*3600);document.getElementById('r5_nirayan_'+h).value=`${Math.floor(t/3600)}:${String(Math.floor(t%3600/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;}
    window.syncKPWorksheetPositions();window.updateKaryeshTables();window.renderChart(true);window.renderReport();
   }catch(error){document.getElementById('dob').setCustomValidity(error.message);}
 }KPClientPresentation.refreshCoordinates();};
 window.calculateAll();
 window.__bridgeSerial=0;
 window.__bridgeAllowed=new Set();
 window.alert=message=>{window.__bridgeMessage=String(message);};
 window.confirm=()=>false;
 }"""
SNAPSHOT = r"""() => {
 KPClientPresentation.refreshCoordinates();
 const forbidden=n=>!!n.closest('[data-private-calculation],#ayan,#lmt,#stcalc,#raphael5,#planet,[data-report-section="ayan"],[data-report-section="lmt"],[data-report-section="stcalc"],[data-report-section="raphael5"],[data-report-section="planet"]');
 window.__bridgeKeyIds ||= new Map();
 document.querySelectorAll('#home-kundali [data-bridge-id]').forEach(n=>delete n.dataset.bridgeId);
 function bridgeKey(node){if(node.id)return 'id:'+node.id;const parts=[];while(node&&node!==document.body){if(node.id){parts.unshift('#'+node.id);break;}const siblings=[...node.parentElement.children];parts.unshift(node.tagName+':'+siblings.indexOf(node));node=node.parentElement;}return parts.join('/');}
 document.querySelectorAll('button,input,select,textarea,details,tbody tr,#kundali .v38-cell,#kundali .v38-center,#kundali,#kundali-north,#home-kundali').forEach(n=>{const key=bridgeKey(n);if(!window.__bridgeKeyIds.has(key))window.__bridgeKeyIds.set(key,'b'+(++window.__bridgeSerial));n.dataset.bridgeId=window.__bridgeKeyIds.get(key);});
 const clone=document.body.cloneNode(true);
 for(const live of document.querySelectorAll('input,textarea,select,details')){const n=clone.querySelector('[data-bridge-id="'+live.dataset.bridgeId+'"]');if(!n)continue;if(live.matches('input')){n.setAttribute('value',live.value);if(live.checked)n.setAttribute('checked','');else n.removeAttribute('checked');}if(live.matches('textarea'))n.textContent=live.value;if(live.matches('select'))[...n.options].forEach((o,i)=>o.toggleAttribute('selected',live.options[i].selected));if(live.matches('details')){n.toggleAttribute('open',live.open);n.dataset.bridgeOpen=String(live.open);}}
 clone.querySelectorAll('script,style,[data-private-calculation],.formula,.formula-text,.md-main,.md-subtitle,.md-rule,.md-formula-row,.md-calc-line,#ayan,#lmt,#stcalc,#raphael5,#planet').forEach(n=>n.remove());
 clone.querySelectorAll('[data-report-section]').forEach(n=>{if(['ayan','lmt','stcalc','raphael5','planet'].includes(n.dataset.reportSection))n.remove();});
 clone.querySelectorAll('[data-report-page-key]').forEach(n=>{if(['ayan','lmt','stcalc','raphael5','planet'].includes(n.dataset.reportPageKey))n.closest('label')?.remove();});
 clone.querySelectorAll('details').forEach(n=>{if(/calculation details|formula|worksheet/i.test(n.querySelector(':scope > summary')?.textContent||''))n.remove();});
 const comments=document.createTreeWalker(clone,NodeFilter.SHOW_COMMENT),removeComments=[];while(comments.nextNode())removeComments.push(comments.currentNode);removeComments.forEach(n=>n.remove());
 clone.querySelectorAll('*').forEach(n=>{for(const a of [...n.attributes])if(/^on/i.test(a.name)||a.name==='srcdoc'||a.name==='contenteditable')n.removeAttribute(a.name);});
 const actions={save:'export',load:'import',export:'export',import:'import'};
 clone.querySelectorAll('button').forEach(n=>{const live=document.querySelector('[data-bridge-id="'+n.dataset.bridgeId+'"]');const code=live?.getAttribute('onclick')||'';if(actions[n.dataset.action])n.dataset.clientAction=actions[n.dataset.action];if(n.id==='choose-report-cover-photo')n.dataset.clientAction='photo';if(/exportChart|downloadBackup|exportBackup/i.test(code)||/export.*lkp|download.*lkp/i.test(n.textContent))n.dataset.clientAction='export';if(/importChart|loadBackup|importBackup/i.test(code)||/import.*lkp|open.*lkp/i.test(n.textContent))n.dataset.clientAction='import';if(/printReport|window.print/i.test(code)||n.id==='print-selected-report')n.dataset.clientAction='print';if(/download.*software/i.test(n.textContent))n.remove();});
 window.__bridgeAllowed=new Set([...clone.querySelectorAll('[data-bridge-id]')].map(n=>n.dataset.bridgeId));
 const bodyData={...document.body.dataset};
 return {html:clone.innerHTML,css:[...document.querySelectorAll('style')].map(n=>n.textContent).join('\n'),bodyClass:document.body.className,bodyData,busy:!!document.querySelector('[aria-busy="true"]'),message:window.__bridgeMessage||''};
 }"""
EVENT = r"""data => {
 if(!/^b\d+$/.test(data.id)||!window.__bridgeAllowed.has(data.id))throw Error('This control is not available.');
 const el=document.querySelector('[data-bridge-id="'+data.id+'"]');
 if(!el||el.disabled||el.readOnly||el.closest('[data-private-calculation]'))throw Error('This control is protected.');
 const visible=el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden';
 if(!visible&&!(el.type==='radio'&&el.closest('.kp-reference-radios')))throw Error('This control is not visible.');
 if(data.kind==='change'){
  if(!el.matches('input,textarea,select')||el.type==='hidden'||el.type==='file'||el.classList.contains('kp-coordinate-source'))throw Error('This field is protected.');
  if(typeof data.value!=='string'||data.value.length>10000)throw Error('Invalid field value.');
  if(el.tagName==='SELECT'&&![...el.options].some(o=>o.value===data.value))throw Error('Invalid selection.');
  el.value=data.value;if(el.type==='checkbox'||el.type==='radio')el.checked=!!data.checked;
  el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
 }else if(data.kind==='toggle'&&el.tagName==='DETAILS'){el.open=!!data.open;
 }else if(data.kind==='click'&&el.matches('button,[role="menuitem"]')){window.confirm=()=>!!data.confirmed;el.click();window.confirm=()=>false;
 }else if(data.kind==='dblclick'){el.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));
 }else if(data.kind==='contextmenu'){el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:Number(data.x)||0,clientY:Number(data.y)||0}));
 }else throw Error('Unsupported action.');
 }"""

class Engine:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.sessions = {}
        self.executor.submit(self.start).result()

    def start(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(executable_path=os.environ.get('CALCULATOR_CHROMIUM', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])

    def close(self):
        def shutdown():
            self.browser.close()
            self.pw.stop()
        self.executor.submit(shutdown).result()
        self.executor.shutdown()

    def call(self, token, action, data=None):
        return self.executor.submit(self.run, token, action, data).result(timeout=90)

    def run(self, token, action, data):
        now = time.monotonic()
        for old, session in list(self.sessions.items()):
            if now-session['used'] > 1800:
                session['context'].close(); del self.sessions[old]
        if token not in self.sessions:
            if action != 'snapshot':
                raise ValueError('Session expired. Reload the application.')
            if len(self.sessions) >= 4:
                raise ValueError('The server is busy. Try again shortly.')
            token = secrets.token_urlsafe(32)
            context = self.browser.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True)
            page = context.new_page()
            downloads=[]
            page.on('download',lambda download:downloads.append(download))
            # No network or filesystem routes are available to customer input.
            page.route('**/*', lambda route: route.abort())
            page.set_content((ROOT/'index.html').read_text(), wait_until='load')
            page.wait_for_timeout(1800)
            page.evaluate(BOOT)
            self.sessions[token] = {'context':context, 'page':page, 'used':now, 'downloads':downloads}
        session=self.sessions[token]; session['used']=now; page=session['page']
        if action=='event':
            page.evaluate(EVENT, data); page.wait_for_timeout(250)
        elif action=='import':
            if not isinstance(data, dict) or not isinstance(data.get('fields'), dict):
                raise ValueError('Select a valid .lkp chart.')
            allowed=page.evaluate("() => [...document.querySelectorAll('input[id],select[id],textarea[id]')].filter(n=>!n.closest('[data-private-calculation]')&&!n.readOnly&&(n.type!=='hidden'||['kp-software-settings','rpw-memos','mm-memos','chart-categories'].includes(n.id))).map(n=>n.id)")
            data={**data, 'fields':{k:v for k,v in data['fields'].items() if k in allowed}, 'eph':[], 'kundali':{'manual':False}}
            page.evaluate('(data)=>{restoreChartData(data);calculateAll();}',data)
            page.wait_for_timeout(350)
        elif action=='photo':
            if not isinstance(data,str) or len(data)>4_100_000 or not data.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):
                raise ValueError('Select a PNG, JPEG or WebP photo under 3 MB.')
            page.evaluate("(photo)=>{if(!KPReportPhoto.isValid(photo))throw Error('Invalid photo');KPReportPhoto.apply(photo);renderReport();}",data)
        elif action=='export':
            chart=page.evaluate("() => {const d=getChartData();for(const id of Object.keys(d.fields)){const n=document.getElementById(id);if(!n||n.closest('[data-private-calculation]')||n.readOnly||(n.type==='hidden'&&!['kp-software-settings','rpw-memos','mm-memos','chart-categories'].includes(n.id)))delete d.fields[id];}d.eph=[];d.kundali={manual:false};return d;}")
            return token, chart
        elif action=='print':
            page.evaluate('()=>renderReport()')
            result=page.evaluate("() => {const blocked=KPClientPresentation.privateTabs;const pages=KPReportPages.selected().filter(n=>!blocked.includes(n.dataset.reportSection));return {html:pages.map(n=>{const copy=n.cloneNode(true);copy.querySelectorAll('[data-private-calculation],.formula,.formula-text,.md-main,.md-subtitle,.md-rule,.md-formula-row,.md-calc-line').forEach(c=>c.remove());return copy.outerHTML;}).join(''),css:[...document.querySelectorAll('style')].map(n=>n.textContent.replace(/#kundali\\b/g,'[data-report-id=\"kundali\"]')).join('\\n')};}")
            if not result['html']: raise ValueError('Select at least one report page in Print.')
            return token, result
        snapshot=page.evaluate(SNAPSHOT); snapshot['token']=token
        if session['downloads']:
            download=session['downloads'].pop(0)
            content=Path(download.path()).read_bytes()
            if len(content)>20_000_000:raise ValueError('Download is too large.')
            snapshot['download']={'name':download.suggested_filename,'base64':base64.b64encode(content).decode()}
            download.delete()
        return token,snapshot

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def token(self):
        cookie=self.headers.get('Cookie','')
        return next((v.strip()[3:] for v in cookie.split(';') if v.strip().startswith('kp=')), '')
    def respond(self, body, content='application/json', status=200, token=None, extra=None):
        if isinstance(body,dict): body=json.dumps(body,ensure_ascii=False)
        body=body.encode() if isinstance(body,str) else body
        self.send_response(status)
        self.send_header('Content-Type',content+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('X-Frame-Options','DENY')
        if token:self.send_header('Set-Cookie',f'kp={token}; HttpOnly; SameSite=Strict; Path=/')
        for k,v in (extra or {}).items():self.send_header(k,v)
        try:
            self.end_headers(); self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def do_GET(self):
        path=urlsplit(self.path).path
        try:
            if path=='/':
                self.respond('<!doctype html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KP Astrology</title><style id="application-style"></style></head><body><div id="application">Loading your chart…</div><script src="/client.js"></script></body></html>','text/html');return
            if path=='/client.js':self.respond((ROOT/'protected/client.js').read_bytes(),'text/javascript');return
            if path not in ('/snapshot','/export','/print'):
                self.respond({'error':'Not found'},status=404);return
            token,result=self.server.engine.call(self.token(),path[1:])
            if path=='/export':self.respond(result,token=token,extra={'Content-Disposition':'attachment; filename="chart.lkp"'});return
            if path=='/print':
                safe=result['html']
                # Report snapshots already remove active controls and handlers.
                doc='<!doctype html><html><head><meta charset="UTF-8"><title>KP Report</title><style>'+result['css']+'</style><style>html,body{margin:0;background:white}body>.report-page{display:block!important;margin:0 auto!important}@media print{body>.report-page{display:block!important}}@page{size:A4;margin:10mm}</style></head><body>'+safe+'<script>window.onload=()=>setTimeout(()=>window.print(),500)</script></body></html>'
                self.respond(doc,'text/html',token=token);return
            self.respond(result,token=token)
        except Exception as error:self.respond({'error':str(error).split('\n')[0]},status=400)
    def do_POST(self):
        path=urlsplit(self.path).path
        if path not in ('/event','/import','/photo'):
            self.respond({'error':'Not found'},status=404);return
        token=self.token()
        if not token or not secrets.compare_digest(self.headers.get('X-KP-Session',''),token):
            self.respond({'error':'Invalid session'},status=403);return
        if self.headers.get('Origin') and urlsplit(self.headers['Origin']).netloc!=self.headers.get('Host'):
            self.respond({'error':'Invalid origin'},status=403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<=0 or size>MAX_BODY or self.headers.get('Content-Type')!='application/json':raise ValueError('Invalid request')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError('Invalid request')
            _,result=self.server.engine.call(token,path[1:],data.get('chart') if path=='/import' else data.get('photo') if path=='/photo' else data)
            self.respond(result)
        except Exception as error:self.respond({'error':str(error).split('\n')[0]},status=400)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8080)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.engine=Engine()
    print(f'Private calculation server ready on port {args.port}',flush=True)
    try:server.serve_forever()
    finally:server.server_close();server.engine.close()
