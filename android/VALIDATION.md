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
