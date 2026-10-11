# KP Master · Offline Windows

Run **KP-Master-Offline-Windows-1.0.0-x64.exe** on Windows 10 or Windows 11 (64-bit).
The portable executable includes Chromium, the calculation engine, house tables,
place lookup, and prediction data. Python, Node.js, Chrome, and an internet
connection are not required on the user's computer. Keep the executable in a
permanent folder and double-click it. The first launch extracts its bundled
runtime to a temporary folder; allow a few seconds for this to finish.

Save kundalis as `.lkp` files using the application's Save controls. Open existing
`.lkp` charts with Load/Open; degrees are recalculated using the packaged automatic
sources. Application preferences, language, notes, and administrator PIN persist
in the current Windows user's application-data folder. Keep separate backups of
important chart files. Selecting a location and saved birth details determines
the chart; Instant Prashna uses the current time.

Use each report's Preview to select Print/Save PDF, Zoom +/−, and Close. Reports
retain their A4 layouts (dense DBA uses A4 landscape). Optional online account
registration/sign-in opens the configured hosted server in the default browser
and requires internet access.

This build is unsigned because no Windows code-signing certificate was supplied.
Windows may display an unknown-publisher warning. Verify the accompanying SHA-256
checksum against the downloaded executable before running it.

## Rebuild

From `desktop/`, run `npm ci`, then `npm run build:windows`. The Electron and
electron-builder versions are pinned in the lockfile. Output is in `desktop/dist/`.
`npm run prepare-app` packages the current root `index.html` and source notices,
then adds only the desktop chart-file bridge. Generated files are ignored by Git.
Windows resource editing uses electron-builder's JavaScript resource editor;
Wine is not required. The portable executable does not request administrator
privileges. To run the desktop locally: `npm start`.

For this restricted Linux cloud workspace, use writable package/cache locations:

```sh
export XDG_CACHE_HOME=/tmp/kp-cache
export ELECTRON_BUILDER_CACHE=/tmp/kp-builder-cache
export electron_config_cache=/tmp/kp-electron-cache
export NODE_USE_ENV_PROXY=1
npm --cache /tmp/kp-npm-cache ci
node node_modules/electron/install.js
npm --cache /tmp/kp-npm-cache run build:windows
```

`npm test` checks link and download policies. With Playwright installed and an
X display available, `node test/runtime.cjs` exercises the actual Electron app,
offline calculations, save/load, preferences across restart, and Marathi A4
printing. Linux tests use `--no-sandbox` solely for the restricted test container;
this switch is not part of the Windows launcher.
