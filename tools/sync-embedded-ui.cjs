'use strict';

/* Keep the single-file application synchronized with reviewed vendor modules.
 * This is deliberately limited to presentation modules and new, isolated APIs.
 * Existing protected calculation script blocks are never selected here.
 */
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const target = path.join(root, 'index.html');
const assets = [
  ['style', 'kp-transit-dark-labels', 'vendor/interface/transit-colours.css'],
  ['style', 'kp-compact-transit-panchang', 'vendor/interface/transit-panchang-layout.css'],
  ['script', 'kp-compact-transit-panchang-script', 'vendor/interface/transit-panchang-layout.js'],
  ['script', 'kp-panchang-daily-engine', 'vendor/panchang/daily-engine.js'],
  ['style', 'kp-transit-panchang-dinvisesh', 'vendor/interface/transit-panchang-dinvisesh.css'],
  ['script', 'kp-transit-panchang-dinvisesh-script', 'vendor/interface/transit-panchang-dinvisesh.js'],
  ['style', 'kp-chart-interactions', 'vendor/interface/chart-interactions.css'],
  ['script', 'kp-chart-interactions-script', 'vendor/interface/chart-interactions.js'],
  ['style', 'kp-about-branding', 'vendor/interface/about-branding.css'],
  ['script', 'kp-about-branding-script', 'vendor/interface/about-branding.js'],
  // Calculation-source support is deliberately appended after all approved
  // engines. Uploaded-KP remains an exact delegation path; Swiss KP is opt-in.
  ['script', 'kp-swiss-krishnamurti', 'vendor/ephemeris/swiss-krishnamurti.js'],
  ['script', 'kp-ephemeris-source-adapter', 'vendor/ephemeris/source-adapter.js'],
  ['style', 'kp-calculation-sources-style', 'vendor/interface/calculation-sources.css'],
  ['script', 'kp-calculation-sources', 'vendor/interface/calculation-sources.js'],
  ['style', 'kp-calculation-source-guard-style', 'vendor/interface/calculation-source-guard.css'],
  ['script', 'kp-calculation-source-guard', 'vendor/interface/calculation-source-guard.js'],
];

let html = fs.readFileSync(target, 'utf8');
for (const [tag, id, relative] of assets) {
  const body = fs.readFileSync(path.join(root, relative), 'utf8').trimEnd();
  const closing = `</${tag}>`;
  if (body.includes(closing)) throw new Error(`${relative} contains ${closing} and cannot be embedded safely.`);
  const block = `<${tag} id="${id}">${body}\n${closing}`;
  const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const expression = new RegExp(`<${tag} id="${escaped}">[\\s\\S]*?<\\/${tag}>`);
  if (expression.test(html)) html = html.replace(expression, block);
  else {
    const at = html.lastIndexOf('</body>');
    if (at < 0) throw new Error('The real closing body tag is missing.');
    html = html.slice(0, at) + block + '\n' + html.slice(at);
  }
}
fs.writeFileSync(target, html);
console.log(`Synchronized ${assets.length} reviewed embedded modules.`);
