const fs = require('node:fs');
const path = require('node:path');
const target = path.join(__dirname, 'app');
fs.mkdirSync(target, { recursive: true });
const source = fs.readFileSync(path.join(__dirname, '..', 'downloads', 'Swami-Samarth-HTML', 'index.html'), 'utf8');
for (const feature of ['profilePrintDetails', 'bkPrintCurrent', 'profileAstrologer', 'software']) {
  if (!source.includes(feature)) throw new Error('Combined software is missing a required feature: ' + feature);
}
const policy = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">`;
fs.writeFileSync(path.join(target, 'Remedy.html'), source.replace('<head>', '<head>' + policy));

fs.copyFileSync(path.join(__dirname, '..', 'downloads', 'Swami-Samarth-HTML', 'THIRD-PARTY-NOTICES.txt'), path.join(target, 'THIRD-PARTY-NOTICES.txt'));
