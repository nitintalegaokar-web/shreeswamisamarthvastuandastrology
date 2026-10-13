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
  const scope = requestedBaseline ? baseline : `${baseline}, approved 10/6 change ${approvedTenSixBaseline}, and approved Ishta change ${approvedIshtaBaseline}`;
  console.log(`PASS: ${protectedScripts.length} calculation blocks and protected source files match ${scope}.`);
}
