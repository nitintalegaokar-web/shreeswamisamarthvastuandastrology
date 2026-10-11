'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const target = path.join(__dirname, 'app');
fs.mkdirSync(target, {recursive:true});
for (const filename of ['index.html', 'README.md', 'RELEASE_NOTES.md']) {
  fs.copyFileSync(path.join(root, filename), path.join(target, filename));
}
const html = fs.readFileSync(path.join(target,'index.html'),'utf8');
const files = fs.readFileSync(path.join(__dirname,'files.js'),'utf8');
// Report templates contain closing body tags inside JavaScript strings.
// Append to the real document, after every application module has initialized.
const closingBody = html.lastIndexOf('</body>');
if (closingBody < 0) throw Error('Application closing body tag is missing.');
fs.writeFileSync(path.join(target,'index.html'), html.slice(0,closingBody)+'<script id="kp-desktop-files">'+files+'</script>'+html.slice(closingBody));
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
