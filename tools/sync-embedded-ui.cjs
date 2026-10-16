'use strict';

/* Keep the single-file application synchronized with reviewed vendor modules.
 * This is deliberately limited to presentation modules and new, isolated APIs.
 * The original-KP block is synchronized only for the explicit Table IV-A/IV-B replacement approved by the user.
 */
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const target = path.join(root, 'index.html');
const assets = [
  ['style', 'kp-chart-workspace-style', 'vendor/interface/chart-workspace.css'],
  ['script', 'kp-feature-updates-script', 'vendor/predictions/dasha-gemstone-workspaces.js'],
  ['script', 'kp-gemstone-document', 'vendor/predictions/gemstone-document.js'],
  ['script', 'kp-horary-result-sheet', 'vendor/predictions/horary-result-sheet.js'],
  ['script', 'kp-additional-documents', 'vendor/resources/additional-documents.js'],
  ['script', 'kp-resources-notes-script', 'vendor/resources/resources-notes.js'],
  ['script', 'kp-personal-predictions-script', 'vendor/predictions/personal-predictions.js'],
  ['script', 'kp-ishta-rounding', 'vendor/houses/ishta-rounding.js'],
  ['script', 'kp-uploaded-house-worksheet', 'vendor/houses/worksheet.js'],
  ['script', 'kp-transit-selection', 'vendor/interface/transit-selection.js'],
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
  // engines. Original KP is mandatory; the other approved engines remain unchanged.
  ['script', 'kp-annual-ayanamsha-script', 'vendor/ephemeris/original-kp-ayanamsha.js'],
  ['script', 'kp-ephemeris-source-adapter', 'vendor/ephemeris/source-adapter.js'],
  ['style', 'kp-calculation-sources-style', 'vendor/interface/calculation-sources.css'],
  ['script', 'kp-calculation-sources', 'vendor/interface/calculation-sources.js'],
  ['style', 'kp-calculation-source-guard-style', 'vendor/interface/calculation-source-guard.css'],
  ['script', 'kp-calculation-source-guard', 'vendor/interface/calculation-source-guard.js'],
  ['style', 'kp-handy-transits-style', 'vendor/interface/handy-transits.css'],
  ['script', 'kp-handy-transits-script', 'vendor/interface/handy-transits.js'],
  ['script', 'kp-supplied-predictions', 'vendor/predictions/supplied-content.js'],
  ['script', 'kp-numerology', 'vendor/predictions/numerology.js'],
  ['script', 'kp-kaal-resources', 'vendor/resources/kaal-resources.js'],
  ['script', 'kp-chart-typography', 'vendor/interface/chart-typography.js'],
  ['script', 'kp-a4-report-contract', 'vendor/interface/a4-reports.js'],
  ['script', 'kp-chart-workspace-script', 'vendor/interface/chart-workspace.js'],
  ['script', 'kp-chart-workspace-extras', 'vendor/interface/chart-workspace-extras.js'],
  ['script', 'kp-transit-workspace', 'vendor/interface/transit-workspace.js'],
  ['script', 'kp-gemstone-event-ranking', 'vendor/predictions/gemstone-event-ranking.js'],
  ['script', 'kp-gemstone-panels', 'vendor/interface/gemstone-panels.js'],
  ['style', 'kp-rules-workspace-style', 'vendor/resources/rules-workspace.css'],
  ['script', 'kp-rules-workspace', 'vendor/resources/rules-workspace.js'],
  ['script', 'kp-developer-credit', 'vendor/interface/developer-credit.js'],
  ['style', 'kp-compact-navigation-style', 'vendor/interface/compact-navigation.css'],
  ['style', 'kp-compact-horary-sheet', 'vendor/interface/horary-sheet-layout.css'],
  ['style', 'kp-dark-readability', 'vendor/interface/dark-readability.css'],
  ['script', 'kp-compact-navigation-script', 'vendor/interface/compact-navigation.js'],
  ['script', 'kp-panchang-single-summary', 'vendor/interface/panchang-single-summary.js'],
];

let html = fs.readFileSync(target, 'utf8');
const predictionCatalogue = path.join(root,'vendor/predictions/supplied-content.json');
if (fs.existsSync(predictionCatalogue)) {
  const data = JSON.stringify(JSON.parse(fs.readFileSync(predictionCatalogue,'utf8'))).replaceAll('</','<\\/');
  const block = '<script id="kp-supplied-prediction-data" type="application/json">'+data+'</script>';
  const expression = /<script id="kp-supplied-prediction-data"[^>]*>[\s\S]*?<\/script>/;
  if (expression.test(html)) html=html.replace(expression,()=>block);
  else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+block+'\n'+html.slice(at);}
}

const numerologyDataPath=path.join(root,'vendor/predictions/numerology-data.json');
if(fs.existsSync(numerologyDataPath)) {
 const data=JSON.stringify(JSON.parse(fs.readFileSync(numerologyDataPath,'utf8'))).replaceAll('</','<\\/');
 const block='<script id="kp-numerology-data" type="application/json">'+data+'</script>';
 const expression=/<script id="kp-numerology-data"[^>]*>[\s\S]*?<\/script>/;
 if(expression.test(html))html=html.replace(expression,()=>block);
 else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+block+'\n'+html.slice(at);}
}
const kaalDataPath=path.join(root,'vendor/resources/kaal-topics.json');
if(fs.existsSync(kaalDataPath)) {
 const data=JSON.stringify(JSON.parse(fs.readFileSync(kaalDataPath,'utf8'))).replaceAll('</','<\\/');
 const block='<script id="kp-kaal-resource-data" type="application/json">'+data+'</script>';
 const expression=/<script id="kp-kaal-resource-data"[^>]*>[\s\S]*?<\/script>/;
 if(expression.test(html))html=html.replace(expression,()=>block);
 else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+block+'\n'+html.slice(at);}
}
const additionalPath=path.join(root,'vendor/resources/additional-documents.json');
const additional=JSON.stringify(JSON.parse(fs.readFileSync(additionalPath,'utf8'))).replaceAll('</','<\\/');
const additionalBlock='<script id="kp-additional-document-data" type="application/json">'+additional+'</script>';
if(/<script id="kp-additional-document-data"[^>]*>[\s\S]*?<\/script>/.test(html))html=html.replace(/<script id="kp-additional-document-data"[^>]*>[\s\S]*?<\/script>/,()=>additionalBlock);
else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+additionalBlock+'\n'+html.slice(at);}
const eventRules = fs.readFileSync(path.join(root,'vendor/resources/event-rules.json'),'utf8').trim().replaceAll('</','<\\/');
const eventBlock = '<script id="kp-event-rule-data" type="application/json">'+eventRules+'</script>';
const eventExpression = /<script id="kp-event-rule-data"[^>]*>[\s\S]*?<\/script>/;
if(eventExpression.test(html))html=html.replace(eventExpression,()=>eventBlock);
else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+eventBlock+'\n'+html.slice(at);}
// Apply the navigation guard before the first body paint, rather than at the end.
const navigationGuard = fs.readFileSync(path.join(root,'vendor/interface/navigation-startup.css'),'utf8').trimEnd();
html=html.replace(/<style id="kp-navigation-startup-guard">[\s\S]*?<\/style>\s*/g,'');
html=html.replace(/<\/head>/i,()=>'<style id="kp-navigation-startup-guard">'+navigationGuard+'\n</style>\n</head>');
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
