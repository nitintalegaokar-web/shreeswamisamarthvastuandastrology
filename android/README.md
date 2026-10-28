# KP Master Android 1.4.0

A native Android Activity hosts the complete offline consultancy HTML on a private, intercepted HTTPS origin (`app.kpmaster.local`). No HTTP server runs on the phone. Java/Android SDK APIs handle installed WhatsApp, the Storage Access Framework, clipboard and Android printing. The APK does not request Internet, contacts, phone or broad storage permissions. It is universal Java bytecode, with no ABI-specific native libraries.

## Build

Requires JDK 17+ (validated with JDK 21), SDK platform 35 and build-tools 35.0.0. No Gradle, npm or third-party Android libraries are needed. Existing combined HTML must be present at `downloads/Swami-Samarth-HTML/index.html` (build it using the preview/package scripts if needed).

```sh
KP_ANDROID_SDK=/path/to/android-sdk \
KP_ANDROID_KEYSTORE=/private/path/kp-master.jks \
KP_ANDROID_PASSWORD_FILE=/private/path/password.txt \
python3 android/build.py
```

The keystore alias is `kp-master`. Use the same private signing key for future updates. A distribution keystore was created outside Git at `/workspace/.kp-master-android-signing/`; it and its password must be kept private and backed up securely. No signing secrets are committed. Output: `downloads/KP-Master-Android-1.4.0.apk`. The manifest is the version source. The production manifest is not debuggable. `KP_ANDROID_DEBUG=1` builds a separate, debuggable `android/build/KP-Master-test.apk` for local emulator checks; do not distribute it.

The build uses aapt2, javac, d8, zipalign and apksigner. For the cloud's manual SDK downloads, official Google repository checksums were verified. The builder accepts normal SDK directory layouts and the temporary zip extraction layout used here. Use SDK tools under their applicable licenses.

## Phone design

Persistent bottom navigation: Remedies, Customers, Bookings, Accounts, Quotes & invoices. The Menu contains all workspaces, including Settings. Touch controls are larger, forms use one column on phones, customer/document selection scrolls to the editor, and document previews fit the screen with an Actual size toggle. A5/A4 print dimensions remain unchanged. Compatibility helpers cover randomUUID, JSON-only structuredClone and dialog fallback on older engines. Android System WebView 80+ is required; update System WebView/Chrome if prompted.

## Native boundaries

- Only the bundled index can load in the WebView. Remote content/navigation is blocked. Inline HTML has a restrictive response CSP. The bridge is exposed only to this bundled content.
- WhatsApp intents explicitly target WhatsApp or WhatsApp Business; no web fallback or automatic sending.
- Blob exports become base64 with a 25 MB limit and open Android's Create Document picker. Export bytes are written only to the selected URI. User cancellation does not delete saved app data.
- Imports use Android's Open Document picker and existing per-section validation/confirmation.
- Printing delegates to WebView's PrintDocumentAdapter. The native media size defaults to selected A5/A4; Accounts uses A5 landscape. afterprint cleanup runs when the print adapter finishes, including cancellation.
- Web storage uses a stable package/origin. Cloud backups are disabled; export each module regularly. Uninstalling or clearing app storage removes local data.

## Verification

Serve the repository on localhost:8086; create `/tmp/kp-mobile-tests`, then run:

```sh
python3 android/stage.py
node android/tests/mobile.cjs
KP_TEST_LEGACY=1 node android/tests/mobile.cjs
```

Tests use synthetic contacts and a mocked native bridge; no WhatsApp messages are sent. Native emulator checks and their limits are documented in `downloads/ANDROID-KP-MASTER.md`. A physical phone, installed WhatsApp and a real printer are required for final hardware verification.
