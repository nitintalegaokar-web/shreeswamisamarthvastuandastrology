# KP MASTER Android · 1.2.3

Two offline APKs use the existing approved single-file calculator unchanged:

- **Owner**: unlocked, package `in.kpmaster.mobile.owner`.
- **Customer**: signed device-bound activation, package `in.kpmaster.mobile.customer`.

Requires Android 9 or later and an enabled, updated Android System WebView
(Chromium 110 or newer). No Node.js, Python or separate astrology installation
is needed on the phone. Calculations and bundled data work offline. External
contact/web links open the phone's browser or mail app when explicitly selected.

## Install and activate

Install Owner on your own phone. Install Customer on the customer's phone.
Android may ask you to allow APK installation from your downloading browser.

On Customer, select **Save System ID file**. Send that text file to the owner.
In the existing Windows **KP Master Owner Activation 1.2.3**, open your original
owner key, choose **Open customer System ID file**, enter the client name and
expiry/permanent option, then create the licence. Send the `.kplicense` file to
the phone. Select **Import activation licence** in the Customer app.

The mobile request uses the same `KP1-…` request format, licence claims and
Ed25519 signatures as the existing Windows owner tool. The original approved
public keys are bundled; no private owner key is included. Mobile identity is
based on Android's app-signing/user/device-scoped ID and the package identity.
Factory resets or changed app signing identities require a new activation.

Activate/Deactivate commands from the Windows tool remain offline files.
Import a signed `.kpcontrol` with **Import licence status** from the mobile menu,
or from the activation screen. An owner issuing a command does not remotely
change an offline phone. Activation does not extend an expired licence.

## Files and reports

- Existing **Open Kundali / Save Kundali** use Android's document picker.
- The native menu provides **Backup app data / Restore backup**, plus text zoom.
- Backups preserve the current chart, saved chart, preferences and Resources notes.
  Device activation is separate and cannot be moved to another phone by backup.
- Report windows open as full-screen dialogs. Use **Print / Save PDF** and choose
  **Save as PDF** in Android's print service. The existing A4 layouts are preserved.
- Use the native Close button or the report's Close action. Android Back closes
  the report before leaving the calculator. Long-press a chart/table to invoke
  its existing double-click enlargement.
- Keep exported files outside the app. Uninstalling removes its private saved data.

## Build

Use the Android SDK platform 35 and build-tools 35.0.0. Java 21's compiler module
is sufficient; the scripts use the SDK's Java 8 lambda stubs. No Gradle/npm
runtime dependency is added to the existing calculator project.

```
python android/tools/setup_sdk.py
python android/build.py
```

`ANDROID_SDK_ROOT` can select the installed SDK.
`KP_ANDROID_SIGNING_DIR` selects the private directory containing `release.p12`
and `store-password.txt`. The current build's signing files are retained outside
Git at `/workspace/kp-master-android-signing/`. Preserve these privately for all
future upgrades; do not generate a replacement signing identity for existing apps.
This Android signing key is separate from your PC's private activation key.
Signing passwords and private keys are never included in the APKs or repository.

The build copies root `index.html` byte-for-byte into each APK and adds an isolated
mobile bridge. The native layer handles local asset loading, licence verification,
Android documents and printing; it does not implement or change astrology math.

## Targeted checks

`android/tests/generate-fixtures.cjs` produces temporary test licences using a
fresh test-only key. `LicenseTest.java` tests the production verifier with JVM
framework stubs, including signature/device/expiry/status rejection and the
existing Windows request parser. `android/tests/mobile_bridge.py` checks the
mobile export/backup/PDF bridge and byte-identical calculator assets in both APKs.
The real device gate always reads Android's native ID; no fixture override ships.

The Bouncy Castle Ed25519 implementation is MIT licensed; its exact
upstream licence is retained in `vendor/LICENSE-bouncycastle.txt`. JSON-java is
used only by JVM tests and is not packaged into the Android runtime.
