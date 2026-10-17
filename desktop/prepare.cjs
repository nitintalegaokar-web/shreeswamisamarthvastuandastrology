'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const target = path.join(__dirname, 'app');
const {publicKey}=require('./licensing/core.cjs');
const {parseAdditionalKeys}=require('./licensing/trust.cjs');
const keyFile=process.env.KP_LICENSE_PUBLIC_KEY_FILE||path.join(__dirname,'owner-public-key.pem');
if(!fs.existsSync(keyFile))throw Error('Export your public key from KP Master Activation, then set KP_LICENSE_PUBLIC_KEY_FILE to that file. A locked client build requires your owner public key.');
const publicText=fs.readFileSync(keyFile,'utf8');
if(!publicText.includes('-----BEGIN PUBLIC KEY-----')||publicText.includes('PRIVATE KEY'))throw Error('Use only the exported PUBLIC key file. Do not provide your private owner key.');
const ownerPublic=publicKey(publicText).export({format:'pem',type:'spki'});
const extraFile=process.env.KP_LICENSE_EXTRA_PUBLIC_KEYS_FILE||path.join(__dirname,'licensing','additional-owner-public-keys.json');
const additionalKeys=parseAdditionalKeys(fs.readFileSync(extraFile,'utf8'));
fs.mkdirSync(target, {recursive:true});
fs.writeFileSync(path.join(target,'owner-public-key.pem'),ownerPublic);
fs.writeFileSync(path.join(target,'additional-owner-public-keys.json'),JSON.stringify({version:1,publicKeys:additionalKeys},null,2)+'\n');
for (const filename of ['index.html', 'README.md', 'RELEASE_NOTES.md']) {
  fs.copyFileSync(path.join(root, filename), path.join(target, filename));
}
let html = fs.readFileSync(path.join(target,'index.html'),'utf8');
const matchEntry='function refresh(){if(!initialized)return null;try{data=calculate();';
if(!html.includes(matchEntry))throw Error('Customer matchmaking guard entry is missing.');
html=html.replace(matchEntry,'function refresh(){if(window.KPCustomerDemo&&!KPCustomerDemo.permitMatchRefresh())return null;if(!initialized)return null;try{data=calculate();');
const demo=fs.readFileSync(path.join(root,'customer','demo-ui.js'),'utf8');
const files = fs.readFileSync(path.join(__dirname,'files.js'),'utf8');
// Report templates contain closing body tags inside JavaScript strings.
// Append to the real document, after every application module has initialized.
const closingBody = html.lastIndexOf('</body>');
if (closingBody < 0) throw Error('Application closing body tag is missing.');
fs.writeFileSync(path.join(target,'index.html'), html.slice(0,closingBody)+'<script id="kp-desktop-files">'+files+'</script><script id="kp-customer-demo">'+demo+'</script>'+html.slice(closingBody));
function copyNotices(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
    const source = path.join(dir, entry.name);
    if (entry.isDirectory()) copyNotices(source);
    else if (/^(license|notice|readme)/i.test(entry.name)) {
      const relative = path.relative(root, source);
      const destination = path.join(target, 'notices', relative);
      fs.mkdirSync(path.dirname(destination), {recursive:true});
      fs.copyFileSync(source, destination);
    }
  }
}
copyNotices(path.join(root, 'vendor'));
console.log('Prepared the self-contained offline application and source notices.');
