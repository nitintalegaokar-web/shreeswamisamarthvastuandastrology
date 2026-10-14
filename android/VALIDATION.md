# Android first-build validation · 1.2.3

- Owner and Customer APKs: built with Android SDK 35, minimum API 28.
- APK v3 signatures: verified by Android's official apksigner.
- Approved calculator HTML: byte-identical in both APKs to root index.html.
- Windows-generated signed licences/status commands: production mobile verifier
  passed 14 JVM assertions with temporary test-only credentials and framework stubs.
  Tests include altered signatures, foreign keys/devices, expiry, deactivation,
  reactivation and older/mismatched control rejection. No real owner private key
  was read or used to generate test licences.
- Mobile backup, Blob export and native print bridge: passed in Chromium at a
  mobile viewport with the native bridge mocked. Native calculator model and
  Dasha period data remained unchanged through these operations.
- Public-key bundle: retains the same approved Windows keys.
- Android signing identity: retained privately; pinned public certificate hash.

Android emulator launch could not be completed in this cloud environment.
Real-phone installation, WebView startup, Android document-picker/PDF interaction
and end-to-end phone activation therefore remain pending. Treat these APKs as
first Android builds; try the Owner APK on a phone before distributing Customer.
