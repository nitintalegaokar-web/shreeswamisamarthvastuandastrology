# KP MASTER · Offline Windows

Run **KP-Master-Offline-Windows-1.1.4-x64.exe** on Windows 10 or Windows 11 (64-bit).
This client version requires a signed activation license for its System ID.
Use the separate Owner Activation tool on your own PC to issue licenses; see
[licensing/README.md](licensing/README.md) for first-time key setup and activation.
The client build must contain your exported public key. Your encrypted private
key stays on your PC and is never packaged with the client.
The portable executable includes Chromium, the calculation engine, house tables,
place lookup, and prediction data. Python, Node.js, Chrome, and an internet
connection are not required on the user's computer. Keep the executable in a
permanent folder and double-click it. The first launch extracts its bundled
runtime to a temporary folder; allow a few seconds for this to finish.

Alternatively, use **KP-Master-Setup-1.1.4-x64.exe** for a normal installation.
Its wizard lets you choose the installation folder and creates desktop and Start
menu shortcuts. It includes an uninstaller registered in Windows Installed Apps.
Installation defaults to the current user and does not require administrator
access. All runtime files are included; no separate Python, Node.js or browser
installation is needed. Uninstalling preserves saved charts, preferences and
activation data. A setup installer for the previously released 1.0.0 calculator
repackages that exact unlocked application; it does not add activation or data
encryption. Use the owner-bound 1.1.4 edition for client licensing.

Save kundalis as `.lkp` files using the application's Save controls. Open existing
`.lkp` charts with Open Kundali; degrees are recalculated using the packaged automatic
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

From `desktop/`, run `npm ci`, set `KP_LICENSE_PUBLIC_KEY_FILE` to your exported
public key file, then run `npm run build:windows`. The Electron and
electron-builder versions are pinned in the lockfile. Output is in `desktop/dist/`.
`npm run prepare-app` packages the current root `index.html` and source notices,
then adds the desktop chart-file bridge and public verification key. Generated files are ignored by Git.
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

`npm run build:owner` builds the independent Windows Owner Activation tool.
Use `npm run build:setup` for the client installation wizard, or
`npm run build:owner:setup` for the Owner Activation installation wizard. The
client setup still requires your exported public key, just like the portable
client. Both formats use the same application-data folder and signed licenses.
Installer builds use electron-builder’s standard NSIS wizard and its bundled
uninstaller reader; Linux builds do not need Wine. Inspect the final installer with
`node verify-setup.cjs <Setup.exe> <win-unpacked folder>`; this checks executable
metadata, archive CRCs, and the embedded application against the verified package.
No private key is generated during the build. `npm test` checks licensing, link and download policies. With Playwright installed and an
X display available, `node test/runtime.cjs` exercises the actual Electron app,
offline calculations, save/load, preferences across restart, and Marathi A4
printing. Linux tests use `--no-sandbox` solely for the restricted test container;
this switch is not part of the Windows launcher.

The unlocked full calculator for the owner is **KP-Master-Owner-Setup-1.0.3-x64.exe** (KP MASTER Owner). It installs separately from the locked customer application. This edition includes the new Raphael tables, full-precision ST, birth-instant KP ayanamsha, single chart hover popup and KP MASTER branding. The Owner Activation tool is a separate program for key generation and signed client license files. The owner-bound customer version 1.1.4 requires the exported public key before it can be built.

Build the full unlocked owner calculator with `npm run build:owner-edition:setup`. With an X display, `npm run test:owner-runtime` verifies this edition without keys, its Open/Save Kundali buttons, saved chart degrees, Marathi labels and single hover panel.

Customer 1.1.4 reads the 64-bit Windows installation ID directly from the registry, falls back to the explicit Registry64 PowerShell API, and treats WMI as optional. The activation screen includes Retry ID. A local identity record preserves the selected ID through WMI outages and recovery, checking the actual Windows MachineGuid on each launch. The owner calculator remains 1.0.3.

Owner Activation **1.1.0** adds green Activate and red Deactivate buttons to the
recent-license table, with English/Marathi labels. Each exports a signed
`.kpcontrol` file for the client to import. Issued status is shown separately
from actual offline client state. Customer 1.1.4 includes Import status file on
the activation screen and Import license status in the workspace's ⋮ menu.
Open the original key that issued a row to change its status; old commands are
rejected after a newer revision. Activation does not renew an expired license.
