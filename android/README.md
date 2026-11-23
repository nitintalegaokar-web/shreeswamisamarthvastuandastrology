# Remedy CRM Android 1.6.0

Native Android Activity with the complete offline consultancy HTML on an intercepted private HTTPS origin, `app.remedycrm.local`. No HTTP server runs on the phone. The installed app is `com.swamisamarth.remedycrm.mobile`, label **Remedy CRM**, with its own signing identity. It is separate from the previous KP Master APK; transfer records using per-section JSON backups. Neither product's data is automatically copied or replaced.

## Build

JDK 17+ (checked with JDK 21), SDK platform 35 and build-tools 35.0.0. No Gradle or third-party Android dependencies are needed. Prepare `downloads/Remedy-CRM-HTML/index.html` using the shared preview/package scripts, then:

```sh
KP_ANDROID_SDK=/path/to/android-sdk \
KP_ANDROID_KEYSTORE=/private/path/remedy-crm.jks \
KP_ANDROID_PASSWORD_FILE=/private/path/password.txt \
python3 android/build.py
```

The legacy build-variable prefix is retained for source compatibility; it does not select the installed app identity. The keystore alias is `remedy-crm`. Current private signing material is outside Git at `/workspace/.remedy-crm-signing/`. Keep it private and back it up securely: future updates to this new package must use the same key. Never commit keystore/password files. Output: `downloads/Remedy-CRM-Android-1.6.0.apk`. `KP_ANDROID_DEBUG=1` builds a separate debuggable test APK under ignored `android/build`; do not distribute that test build.

## Features and native boundaries

- Colourful compact navigation, saved themes, visible remedy search/Add, full-text expansion and page shortcuts. Saved theme choices remain selected. System mode reads Android configuration through the trusted bridge.
- Essential customer controls first; optional details, schedules, private notes and archive actions remain expandable. Reports follow selected filters and omit private CRM notes/birth details.
- Snapshot report preview, A5/A4 landscape and optional SVG bar diagrams for follow-ups or collections/expenses. Quotes/invoices use A5/A4 portrait. Remedy/booking A5 headings are compact, with saved top-space control (4–25 mm, default 5).
- Java opens only explicitly targeted WhatsApp/WhatsApp Business intents, with no web fallback or automatic sending.
- Exports use Android Create Document and imports use Open Document. No broad storage, contacts, phone or Internet permissions are requested. Export payloads are limited to 25 MB and written only to the selected URI.
- Android PrintDocumentAdapter uses selected report/document paper size/orientation; afterprint cleans up when the adapter finishes. Hardware/system service behavior needs device checks.
- Only bundled index content loads. Other navigation/requests are blocked, with restrictive CSP and no remote JavaScript. Web storage is private to this new package/origin. Cloud backup is disabled; export backups regularly. Uninstall/clear data removes local records.

## Checks

Serve the repository and set `KP_MOBILE_TEST_URL` (for example `http://127.0.0.1:8091/android/build/assets/index.html`) for `android/tests/mobile.cjs`, `compact.cjs`, `remedy-controls.cjs` and `themes.cjs`. Shared `desktop/tests/check-simple-reports.cjs` and `check-a5-heading.cjs` verify report/print output. Older-engine compatibility covers randomUUID, JSON-only structuredClone and dialog fallbacks; Android System WebView 80+ is required.

The release APK's signature, manifest identity, non-debuggable/no-permissions properties and exact embedded assets were checked. Browser tests intercept native calls; no WhatsApp messages are sent. No native-device installation, file-picker, print/WhatsApp launch or physical-printer test is claimed. See `downloads/REMEDY-CRM-START-HERE.md` for end-user use and migration.
