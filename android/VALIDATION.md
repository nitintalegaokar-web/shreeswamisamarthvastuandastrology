# Mobile follow-up · visible version 1.2.8 · 17 October 2026

Removed the duplicate menu/shortcut block from Android only. The existing Home
hamburger opens the left navigation drawer; its Ruling Planet entry remains
available. No replacement toolbar was added. Windows and root HTML are unchanged.

Single-page Kundali PDF now uses the existing chart renderer and PDF library to
save one A4 page directly. Home/single-page print actions route to that export;
other reports retain Android printing with zero additional native margins.

Visible version stays 1.2.8 as requested. Android versionCode is 10209 so the
corrected APK can update the previously installed 10208 release. Package IDs,
original signing certificate, stored charts and activation trust are preserved.

Java compilation, APK packaging, signatures and asset parity were checked.
The browser/phone UI and PDF checks for this follow-up were not completed:
Chromium requires sandbox approval, and those attempts were interrupted.
Verify the new PDF export on a phone before client distribution.
# Android icon toolbar update · 1.2.5

Added a persistent Hide icons / Show icons arrow above the shortcut toolbar.
The preference is included in mobile data backups; the arrow is hidden in print.
Calculator HTML, native code, signing identity and activation are unchanged.

# Android readability update · 1.2.4

Home tables use readable text and horizontal scrolling; North Indian charts have
an enlarged scrollable diagram and a readable list of the existing planet values.
Report windows include native zoom controls and phone insets. Printing waits for
fonts and two layout frames before opening Android Print / Save PDF.

The approved index.html calculation source is unchanged. Both APKs contain the
same original calculator bytes and retain the original app IDs, signing certificate,
public owner keys, licence verifier and data storage.

Validation: mobile Chromium layout, nine North planet entries, backup/export,
unchanged calculation model and Dasha data, one-page A4 report with text inside
page bounds; production licence verifier 14 assertions; official APK signatures.
Native Android PDF dialog and the updated layout still require real-phone testing.
