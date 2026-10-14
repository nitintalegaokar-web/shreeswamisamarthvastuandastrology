'use strict';

/* Compare approved calculation blocks and source files with the release
 * baseline. This tool is read-only and intentionally ignores interface,
 * reporting and licensing modules.
 */
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

const root = path.resolve(__dirname, '..');
const requestedBaseline = process.argv[2] || null;
const baseline = requestedBaseline || 'd15b677367dbc0d744ebb15adb378d5d7da566ba';
const approvedTenSixBaseline = 'b6208e6014134993abfd47a8c4644aa7ef9872ab';
const approvedIshtaBaseline = '1194c4d71f3388a3dabc6cc9c85d6027b90de618';
const approvedScriptBaselines = requestedBaseline ? {} : {
  'kp-legacy-native-calculation-script': approvedTenSixBaseline,
  'worksheet-automatic-ephemeris-script': approvedTenSixBaseline,
  'kp-ishta-rounding': approvedIshtaBaseline,
  'kp-legacy-raphael-calculation-script': approvedIshtaBaseline,
  'kp-uploaded-house-worksheet': approvedIshtaBaseline,
};
const approvedFileBaselines = requestedBaseline ? {} : {
  'vendor/houses/README.md': approvedIshtaBaseline,
  'vendor/houses/worksheet.js': approvedIshtaBaseline,
  'vendor/houses/ishta-rounding.js': approvedIshtaBaseline,
};
// User's latest 14 October reference image replaces only Ishta rounding:
// 45′19″ => 45′; 43′49″ => 44′ (half-minute, 30-second threshold).
const imageRoundingFiles = {
  'vendor/houses/ishta-rounding.js': '7d5e44bd8ca4e1dfb434305c75f69358452439b79e02423675a72c0a835d8125',
  'vendor/houses/worksheet.js': 'cf0d976b75f3bbb9e1b2f349b0c4491c8052c88c9d600343a70923b1a6aff818',
  'vendor/houses/README.md': '14cb2ce11aec0923664aa43d5ac22f7dbd98090a3805eb01f220710fac3dfe96',
};
const imageRoundingScripts = {'kp-ishta-rounding':'vendor/houses/ishta-rounding.js','kp-uploaded-house-worksheet':'vendor/houses/worksheet.js'};
const protectedScripts = [
  'kp-legacy-native-calculation-script',
  'kp-ishta-rounding',
  'kp-legacy-raphael-calculation-script',
  'kp-display-engine',
  'kp-ephemeris-api',
  'kp-annual-ayanamsha-script',
  'worksheet-automatic-ephemeris-script',
  'kp-transit-engine',
  'kp-transit-house-api',
  'kp-home-vimshottari-script',
  'kp-matchmaking-script',
  'kp-single-page-report-script',
  'kp-horary-script',
  'kp-uploaded-house-table',
  'kp-uploaded-house-worksheet',
  'kp-automatic-calculations',
  'kp-vedic-math',
  'kp-vedic-adapter',
  'kp-muhurta-script',
  'kp-hit-math',
];
const protectedPaths = [
  'vendor/houses',
  'vendor/houses/ishta-rounding.js',
  'vendor/vedic',
  'vendor/muhurta/engine.js',
  'vendor/hit/engine.js',
];

function git(...args) {
  return execFileSync('git', args, {cwd:root, encoding:'utf8', maxBuffer:64 * 1024 * 1024});
}
function atCommit(commit, relative) {
  return git('show', `${commit}:${relative}`);
}
function scriptBody(html, id) {
  const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = html.match(new RegExp(`<script\\s+id=["']${escaped}["'][^>]*>([\\s\\S]*?)<\\/script>`));
  if (!match) throw new Error(`Missing protected script: ${id}`);
  return match[1];
}
function digest(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

const htmlAtCommit = new Map();
function committedHtml(commit) {
  if (!htmlAtCommit.has(commit)) htmlAtCommit.set(commit, atCommit(commit, 'index.html'));
  return htmlAtCommit.get(commit);
}
const currentHtml = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const failures = [];
for (const id of protectedScripts) {
  // User explicitly replaced only this source on 14 October 2026 with the
  // supplied original Tables IV-A/B (1931-10-10 => 22:48:18).
  if (!requestedBaseline && id === 'kp-annual-ayanamsha-script') {
    const expected = fs.readFileSync(path.join(root,'vendor/ephemeris/original-kp-ayanamsha.js'),'utf8');
    if (digest(expected) !== '217909ed5c32e29be92105eff365d08b87d305383a551a24c6af5350a605aecc') failures.push('Original KP source differs from reviewed implementation.');
    if (scriptBody(currentHtml,id).trim() !== expected.trim()) failures.push('Original KP embedded implementation is out of sync.');
    const data = currentHtml.match(/<script id="kp-annual-ayanamsha-data"[^>]*>([\s\S]*?)<\/script>/);
    const approvedData = fs.readFileSync(path.join(root,'vendor/ephemeris/original-kp-tables.json'),'utf8');
    if (!data || JSON.stringify(JSON.parse(data[1])) !== JSON.stringify(JSON.parse(approvedData))) failures.push('Original KP embedded table differs from source data.');
    const upload = fs.readFileSync(path.join(root,'vendor/ephemeris/source/Original-KP-Tables-IV-A-IV-B.txt'));
    if (digest(upload) !== '95e0c79979bb67f06d8f31382190e024ee8b67796650fefdd6bd43ebc4be4782') failures.push('Original KP upload differs from approved source.');
    continue;
  }
  if (!requestedBaseline && imageRoundingScripts[id]) {
    const relative = imageRoundingScripts[id], expected = fs.readFileSync(path.join(root,relative),'utf8');
    if (digest(expected) !== imageRoundingFiles[relative]) failures.push(`${relative}: differs from approved reference-image rounding.`);
    if (scriptBody(currentHtml,id).trim() !== expected.trim()) failures.push(`${id}: embedded rounding module is out of sync.`);
    continue;
  }
  const expectedCommit = approvedScriptBaselines[id] || baseline;
  const expected = scriptBody(committedHtml(expectedCommit), id);
  const actual = scriptBody(currentHtml, id);
  if (actual !== expected) failures.push(`index.html#${id} (${expectedCommit}): ${digest(expected)} -> ${digest(actual)}`);
}

for (const protectedPath of protectedPaths) {
  const treeBaseline = approvedFileBaselines[protectedPath] || baseline;
  const entries = git('ls-tree', '-r', '--name-only', treeBaseline, '--', protectedPath).trim().split('\n').filter(Boolean);
  if (!entries.length) failures.push(`${protectedPath}: missing from baseline`);
  for (const relative of entries) {
    if (!requestedBaseline && imageRoundingFiles[relative]) {
      if (digest(fs.readFileSync(path.join(root,relative),'utf8')) !== imageRoundingFiles[relative]) failures.push(`${relative}: differs from approved reference-image rounding.`);
      continue;
    }
    const expectedCommit = approvedFileBaselines[relative] || baseline;
    const expected = atCommit(expectedCommit, relative);
    const current = path.join(root, relative);
    if (!fs.existsSync(current)) {
      failures.push(`${relative}: missing from working tree`);
      continue;
    }
    const actual = fs.readFileSync(current, 'utf8');
    if (actual !== expected) failures.push(`${relative} (${expectedCommit}): ${digest(expected)} -> ${digest(actual)}`);
  }
}

if (failures.length) {
  console.error(`FAIL: ${failures.length} protected calculation difference(s) from approved scoped baselines.`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exitCode = 1;
} else {
  const scope = requestedBaseline ? baseline : `${baseline}, approved 10/6 change ${approvedTenSixBaseline}, approved Ishta change ${approvedIshtaBaseline}, user-supplied original KP Tables IV-A/IV-B, and latest Raphael reference-image half-minute rounding (14 October 2026)`;
  console.log(`PASS: ${protectedScripts.length} calculation blocks and protected source files match ${scope}.`);
}
