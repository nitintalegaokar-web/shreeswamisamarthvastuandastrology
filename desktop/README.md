# Remedy CRM — Windows 1.6.0

Remedy CRM is a separate product from Advance KP Master. The installer uses:

| Identity | Value |
| --- | --- |
| Product / shortcut / uninstall entry | Remedy CRM |
| Electron package | remedy-crm |
| Windows app ID / AppUserModelID | com.swamisamarth.remedycrm |
| NSIS GUID | 38a6638f-04d2-5d6c-acf9-32cab91581b7 |
| User data | `%APPDATA%\RemedyCRM` |
| Windows executable | Remedy CRM.exe |
| Installer | Remedy-CRM-Setup-1.6.0.exe |

Setup uses a dedicated default folder; the installation-directory selection step is disabled. No old-product profile, registry install path or data folder is automatically copied/opened. This intentionally starts a separate Remedy CRM profile. Existing backup formats and record IDs remain compatible: transfer records using per-section JSON backups. Do not delete old data before verifying the transfer. Uninstall preserves Remedy CRM user data.

## Features

209 remedies, customer CRM and follow-ups, appointment/visit WhatsApp sharing, Matrugaya booking, collections/expenses, daily/monthly/yearly reports, quotations/invoices, Excel exports, and A5/A4 document previews. Simplified CRM puts required contact fields, follow-up, Save and WhatsApp first; optional contact details, schedules, private notes and archive controls are clearly expandable.

Customer reports follow the current search/stage/follow-up filters and exclude private notes and birth data. Customer-stage/follow-up bar diagrams appear in the CRM summary. Accounts diagrams compare actual collections and expenses for the selected period. Report preview offers A5/A4 landscape, optional bar diagrams and Print / Save PDF. Charts read validated records without changing them. Booking advances are not automatically ledger receipts; invoice payments share the Accounts ledger.

## Rebuild

Node.js 22.12+, pinned Electron 44.9.0 / electron-builder 26.15.3:

```sh
npm ci --ignore-scripts --prefix desktop
python3 previews/source/build-preview.py
python3 previews/source/package-html.py
XDG_CACHE_HOME=/tmp/remedy-cache ELECTRON_CACHE=/tmp/remedy-electron-cache ELECTRON_BUILDER_CACHE=/tmp/remedy-electron-builder-cache npm run dist:win --prefix desktop
```

The base library is `Remedy.html`; shared modules are in `previews/source`. The HTML output is `downloads/Remedy-CRM-HTML/index.html`. `stage.cjs` adds desktop CSP. `build-win.cjs` uses electron-builder's native NSIS uninstaller reader on Linux and BCJ2 solid compression; differential update packaging is disabled to keep the full installer below GitHub's file limit. Do not edit generated app/release files.

The renderer disables Node integration, enables context isolation and sandboxing, blocks other navigation and permits only validated WhatsApp app send links externally. It opens the installed WhatsApp app; no web fallback or automatic sending.

## Verification and limits

Run `check-product-isolation.cjs`, `check-simple-reports.cjs` and the browser workflow checks under `desktop/tests`. Serve the repository on port 8090 or override `KP_TEST_URL`. The checks cover product boundaries, backup compatibility, CRM/accounts/invoices, chart values and A5/A4 output. The release's ASAR and installer archives are checked before publishing. Independent `pdfinfo` checks confirm the paper dimensions.

Cross-built on Linux. Native Windows install/uninstall, coexistence with the user's actual Advance KP Master installation and physical printing have not been exercised here. The installer is unsigned and may show an unknown publisher warning.

A5 remedy/booking letterhead spacing uses a named `remedyA5` page and compact heading CSS. Settings stores `a5TopMargin` (4–25 mm, default 5) in the business profile; earlier settings backups default to 5. `check-a5-heading.cjs` verifies persistence, enabled/hidden heading details and full body text; independent PDF checks cover dimensions, position shifts and long-content pagination. Other document page rules remain separate.
