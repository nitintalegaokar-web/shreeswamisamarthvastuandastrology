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
const baseline = process.argv[2] || 'd15b677367dbc0d744ebb15adb378d5d7da566ba';
const protectedScripts = [
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
  'vendor/vedic',
  'vendor/muhurta/engine.js',
  'vendor/hit/engine.js',
];

function git(...args) {
  return execFileSync('git', args, {cwd:root, encoding:'utf8', maxBuffer:64 * 1024 * 1024});
}
function atBaseline(relative) {
  return git('show', `${baseline}:${relative}`);
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

const baselineHtml = atBaseline('index.html');
const currentHtml = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const failures = [];
for (const id of protectedScripts) {
  const expected = scriptBody(baselineHtml, id);
  const actual = scriptBody(currentHtml, id);
  if (actual !== expected) failures.push(`index.html#${id}: ${digest(expected)} -> ${digest(actual)}`);
}

for (const protectedPath of protectedPaths) {
  const entries = git('ls-tree', '-r', '--name-only', baseline, '--', protectedPath).trim().split('\n').filter(Boolean);
  if (!entries.length) failures.push(`${protectedPath}: missing from baseline`);
  for (const relative of entries) {
    const expected = atBaseline(relative);
    const current = path.join(root, relative);
    if (!fs.existsSync(current)) {
      failures.push(`${relative}: missing from working tree`);
      continue;
    }
    const actual = fs.readFileSync(current, 'utf8');
    if (actual !== expected) failures.push(`${relative}: ${digest(expected)} -> ${digest(actual)}`);
  }
}

if (failures.length) {
  console.error(`FAIL: ${failures.length} protected calculation difference(s) from ${baseline}`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exitCode = 1;
} else {
  console.log(`PASS: ${protectedScripts.length} calculation blocks and protected source files match ${baseline}.`);
}
