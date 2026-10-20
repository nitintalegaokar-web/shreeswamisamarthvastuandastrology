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
  ['script','kp-planet-notation','vendor/interface/planet-notation.js'],
  ['script', 'kp-interface-languages','vendor/interface/language-engine.js'],
  ['style','kp-pd-transit-refinement-style','vendor/predictions/pd-transit-refinement.css'],
  ['script','kp-pd-transit-refinement','vendor/predictions/pd-transit-refinement.js'],
  ['script','kp-dasha-promise-script','vendor/predictions/dasha-promise.js'],
  ['script','kp-muhurta-supplied-data','vendor/muhurta/supplied-data.js'],
  ['script','kp-muhurta-supplied-rules','vendor/muhurta/supplied-rules.js'],
  ['script','kp-muhurta-nirnay','vendor/muhurta/nirnay.js'],
  ['script','kp-muhurta-script','vendor/muhurta/engine.js'],
  ['script','kp-selected-report-window','vendor/interface/report-selection.js'],
  ['script','kp-higher-education-data','vendor/predictions/higher-education-data.js'],
  ['script','kp-education-profession-script','vendor/predictions/education-profession.js'],
  ['script','kp-cuspal-supplied-data','vendor/predictions/cuspal-supplied-data.js'],
  ['script','kp-cuspal-supplied','vendor/predictions/cuspal-supplied.js'],
  ['script','kp-disease-supplied-data','vendor/predictions/disease-supplied-data.js'],
  ['script','kp-disease-supplied','vendor/predictions/disease-supplied.js'],
  ['script','kp-hover-details','vendor/interface/hover-details.js'],
  ['script','kp-vedic-adapter','vendor/vedic/adapter.js'],
  ['script','kp-vedic-symbols','vendor/vedic/symbols.js'],
  ['script','kp-vedic-complete-report','vendor/vedic/complete-report.js'],
  ['script','kp-vedic-ui','vendor/vedic/ui.js'],
  ['style','kp-vedic-style','vendor/vedic/style.css'],
  ['style','kp-help-tutorial-style','vendor/interface/help-tutorial.css'],
  ['script','kp-help-tutorial','vendor/interface/help-tutorial.js'],
  ['script', 'kp-aspect-legend-language', 'vendor/interface/aspect-legend.js'],
  ['script', 'kp-personal-workspace', 'vendor/interface/personal-workspace.js'],
  ['script', 'kp-prediction-quick-language', 'vendor/interface/prediction-quick-language.js'],
  ['style', 'kp-settings-easy-style', 'vendor/interface/settings-easy.css'],
  ['script', 'kp-settings-easy', 'vendor/interface/settings-easy.js'],
  ['script', 'kp-table-karkatva', 'vendor/interface/table-karkatva.js'],
  ['script', 'kp-event-house-data', 'vendor/predictions/event-house-data.js'],
  ['script', 'kp-event-house-rules', 'vendor/predictions/event-house-rules.js'],
  ['script', 'kp-marriage-source-data', 'vendor/predictions/marriage-source-data.js'],
  ['script', 'kp-third-cusp-mindset-data', 'vendor/predictions/third-cusp-mindset-data.js'],
  ['script', 'kp-third-cusp-mindset', 'vendor/predictions/third-cusp-mindset.js'],
  ['script', 'kp-theft-profile', 'vendor/predictions/theft-profile.js'],
  ['script', 'kp-marriage-points', 'vendor/predictions/marriage-points.js'],
  ['script', 'kp-eighth-cusp-data', 'vendor/predictions/eighth-cusp-data.js'],
  ['script', 'kp-eighth-cusp-rules', 'vendor/predictions/eighth-cusp-rules.js'],
  ['script', 'kp-nakshatra-karkatva', 'vendor/interface/nakshatra-karkatva.js'],
  ['style', 'kp-fortuna-interpretation-style', 'vendor/interface/fortuna-interpretation.css'],
  ['script', 'kp-fortuna-interpretation', 'vendor/interface/fortuna-interpretation.js'],
  ['script', 'kp-child-gender-sheet', 'vendor/predictions/child-gender-sheet.js'],
  ['script', 'kp-childbirth-engine', 'vendor/predictions/childbirth.js'],
  ['script', 'kp-lifespan-reference', 'vendor/predictions/lifespan-reference.js'],
  ['script', 'kp-event-outcome-script', 'vendor/predictions/event-outcome.js'],
  ['script', 'kp-prediction-language-policy', 'vendor/predictions/prediction-language.js'],
  ['script', 'kp-rashi-karkatva-data', 'vendor/interface/rashi-karkatva-data.js'],
  ['script', 'kp-rashi-karkatva', 'vendor/interface/rashi-karkatva.js'],
  ['script', 'kp-planet-karkatva-data', 'vendor/interface/planet-karkatva-data.js'],
  ['style', 'kp-planet-karkatva-style', 'vendor/interface/planet-karkatva.css'],
  ['script', 'kp-planet-karkatva', 'vendor/interface/planet-karkatva.js'],
  ['script', 'kp-jyotish-source-data', 'vendor/predictions/jyotish-data.js'],
  ['script', 'kp-natal-panchang-predictions', 'vendor/predictions/natal-panchang.js'],
  ['script', 'kp-vedic-bhav-data', 'vendor/predictions/vedic-bhav-data.js'],
  ['script', 'kp-vedic-bhav', 'vendor/predictions/vedic-bhav.js'],
  ['script', 'kp-kalsarpa', 'vendor/predictions/kalsarpa.js'],
  ['script', 'kp-vedic-predictions-engine', 'vendor/predictions/vedic-predictions.js'],
  ['style', 'kp-vedic-predictions-style', 'vendor/predictions/vedic-predictions.css'],
  ['script', 'kp-preference-engine', 'vendor/interface/chart-preferences.js'],
  ['script', 'kp-transit-chart-ui', 'vendor/interface/transit-chart.js'],
  ['style', 'kp-bhava-karkatva-style', 'vendor/interface/bhava-karkatva.css'],
  ['script', 'kp-bhava-karkatva', 'vendor/interface/bhava-karkatva.js'],
  ['style', 'kp-matchmaking-compact', 'vendor/interface/matchmaking-compact.css'],
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
  ['script','kp-transit-event-chains','vendor/interface/transit-event-chains.js'],
  ['script', 'kp-transit-workspace', 'vendor/interface/transit-workspace.js'],
  ['script', 'kp-gemstone-event-ranking', 'vendor/predictions/gemstone-event-ranking.js'],
  ['script', 'kp-gemstone-panels', 'vendor/interface/gemstone-panels.js'],
  ['style', 'kp-rules-workspace-style', 'vendor/resources/rules-workspace.css'],
  ['script', 'kp-rules-workspace', 'vendor/resources/rules-workspace.js'],
  ['script', 'kp-developer-credit', 'vendor/interface/developer-credit.js'],
  ['style', 'kp-compact-navigation-style', 'vendor/interface/compact-navigation.css'],
  ['style', 'kp-compact-horary-sheet', 'vendor/interface/horary-sheet-layout.css'],
  ['script', 'kp-event-query-selection', 'vendor/interface/event-query-selection.js'],
  ['script', 'kp-horary-dba-selection', 'vendor/interface/horary-dba.js'],
  ['script', 'kp-coordinate-dms-inputs', 'vendor/interface/coordinate-dms.js'],
  ['style', 'kp-ruling-finder-style', 'vendor/interface/ruling-planet-finder.css'],
  ['script','kp-rp-reference-time','vendor/interface/rp-reference-time.js'],
  ['style','kp-rp-reference-time-style','vendor/interface/rp-reference-time.css'],
  ['script', 'kp-live-ruling-calculator', 'vendor/interface/live-ruling.js'],
  ['script', 'kp-ruling-finder-script', 'vendor/interface/ruling-planet-finder.js'],
  ['script', 'kp-dasha-current-selection', 'vendor/interface/dasha-current-selection.js'],
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
const guideData = JSON.stringify({file:'KP-MASTER-User-Tutorial-1.2.8.pdf',language:'english',base64:fs.readFileSync(path.join(root,'docs/KP-MASTER-User-Tutorial-1.2.8.pdf')).toString('base64')});
const guideBlock='<script id="kp-user-tutorial-pdf" type="application/json">'+guideData+'</script>';
if(/<script id="kp-user-tutorial-pdf"[^>]*>[\s\S]*?<\/script>/.test(html))html=html.replace(/<script id="kp-user-tutorial-pdf"[^>]*>[\s\S]*?<\/script>/,()=>guideBlock);else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+guideBlock+'\n'+html.slice(at);}
const featureCatalog = fs.readFileSync(path.join(root,'desktop/licensing/features.json'),'utf8').trim();
const featureBlock='<script id="kp-feature-catalog" type="application/json">'+featureCatalog+'</script>';
if(/<script id="kp-feature-catalog"[^>]*>[\s\S]*?<\/script>/.test(html))html=html.replace(/<script id="kp-feature-catalog"[^>]*>[\s\S]*?<\/script>/,()=>featureBlock);else {const at=html.lastIndexOf('</body>');html=html.slice(0,at)+featureBlock+'\n'+html.slice(at);}
fs.writeFileSync(target, html);
console.log(`Synchronized ${assets.length} reviewed embedded modules.`);
