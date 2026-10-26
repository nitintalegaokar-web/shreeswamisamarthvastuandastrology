# KP Master Windows installer — 1.3.1

Packages the combined HTML software from `../downloads/Swami-Samarth-HTML/index.html`: 209 remedies across 49 subjects, Matrugaya bookings, business Settings, configurable print branding, A5 remedy printouts and receipts, Excel booking reports, offline CRM, appointment/visit WhatsApp sharing, collection/expense reports, quotations/invoices and the KP Master icon. The separate floor-plan studio is not included.

## Install and use

Run `KP-Master-Setup-1.3.1.exe` on 64-bit Windows 10 or 11. The setup wizard lets you choose an installation folder and creates desktop and Start menu shortcuts. The application includes its runtime and needs no browser, Node.js, Python, or web server installed separately.

Use Settings to edit the consultancy name, astrologer name, address and mobile. Save settings after choosing which details to print. The master switch toggles astrologer name, address and mobile; consultancy name can be selected independently. These choices affect both remedy and booking printing. WhatsApp signatures retain your saved business contact details.

For printing, choose A5 (148 × 210 mm), portrait, 100% scale and turn browser print headers/footers off if offered. Select Microsoft Print to PDF or Save as PDF for a PDF file. Longer content can continue onto more A5 sheets without clipping. Marathi text uses installed Windows fonts.

Everything except WhatsApp sharing works offline. Sharing opens a prepared WhatsApp message for you to send.

## Data and upgrades

The application retains `com.swamisamarth.remedies` as its app ID and `%APPDATA%\SwamiSamarthRemedies` as its data folder, matching version 1.0.0. Uninstall preserves the data folder. Export backups before upgrading or uninstalling; Windows upgrade behavior has not been tested on this Linux build machine.

The HTML/browser version stores data separately. Export remedies, bookings and settings in that version, then import each JSON backup in the corresponding desktop section. Imports replace their respective collections. Save backups regularly; do not delete the data folder without exporting first.

## Rebuild

Node.js 22.12+ and npm are required on the build machine. Dependencies are pinned independently of the floor-plan application.

```sh
cd /workspace/shreeswamisamarthvastuandastrology/desktop
npm ci --ignore-scripts --cache /tmp/vastu-npm-cache
XDG_CACHE_HOME=/tmp/vastu-cache ELECTRON_CACHE=/tmp/electron-cache ELECTRON_BUILDER_CACHE=/tmp/electron-builder-cache npm run dist:win
```

On Windows, run `npm run dist:win` after `npm ci --ignore-scripts`. `stage.cjs` reads the combined HTML and adds a desktop content security policy. On Linux, `build-win.cjs` uses the pinned builder's native `UninstallerReader` for exactly the expected NSIS uninstaller-generation call, avoiding Wine execution. No dependency files are patched. Runtime and tool downloads retain checksum and TLS verification. Build output is in `release/`.

The Windows runtime includes English, Hindi and Marathi locale packs. Application content and remedies remain intact. `signExecutable: false` skips signing while preserving Windows executable icon and product metadata. Publishing through electron-builder is disabled. Differential update packaging is disabled because this build has no automatic updater; normal solid compression keeps the full offline installer small enough for a direct GitHub download. The builder's supported BCJ2 executable compression filter preserves the installed bytes.

## Validation and limitations

The renderer has no Node.js integration, enables context isolation and sandboxing, denies permissions except sanitized clipboard writes, blocks navigation and webviews, and only permits validated WhatsApp app send links to open externally. Browser checks use the staged HTML and its desktop CSP. ASAR checks verify packaged bytes against staging, Windows metadata and icon resources are inspected, and NSIS archive checks verify the installer and embedded application archive.

This installer is unsigned and Windows may show an unknown publisher. Native Windows installation, shortcuts, updates, uninstallation and printer dialogs require a Windows machine for final testing. No signing credentials are included.

## Excel booking report

Open Matrugaya Bookings → Saved bookings / नोंदी → Export Excel / एक्सेल. The offline exporter creates a real `.xlsx` workbook with all saved booking rows, numeric payments, balance formulas and a totals row. It preserves text IDs and mobile numbers and supports Marathi text.

The worksheet is configured for A5 landscape, one page wide with as many pages tall as needed, and repeated column headings. Your Settings print choices control business details in the Excel heading. Open the workbook in Excel and use File → Print. Native Excel printing is not tested on this Linux machine; the workbook structure, formulas, cached results and page-setup metadata are validated with an independent reader.

The ExcelJS 4.4.0 browser bundle is included inline in the HTML, with third-party notices in the ZIP and installed application. Rebuild these assets by running `npm ci --ignore-scripts` in `previews/source/vendor` and copying `node_modules/exceljs/dist/exceljs.min.js` to the adjacent `exceljs.min.js` before running the preview/HTML package scripts.

## Update HTML modules

The standalone base library is `../Remedy.html`. Booking, Settings, CRM, Accounts and document modules live under `../previews/source/`. Generate the combined preview and production HTML/ZIP before rebuilding:

```sh
python3 previews/source/build-preview.py
python3 previews/source/package-html.py
npm run dist:win --prefix desktop
```

Run those commands from the repository root (with the cache environment variables above for this Linux build environment). See `tests/README.md` for browser checks and `../downloads/VALIDATION-1.3.1.md` for validation scope. Keep source edits out of generated `desktop/app/` and `desktop/release/`.

WhatsApp sharing opens the installed WhatsApp application using its app link. Install and sign in to WhatsApp on this computer before sharing. No WhatsApp Web fallback is used. Browsers may ask permission to open the installed app; the desktop installer opens it through Windows.
