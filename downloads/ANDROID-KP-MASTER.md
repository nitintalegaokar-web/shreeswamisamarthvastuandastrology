# KP Master for Android — 1.4.1

## Install

1. Download **KP-Master-Android-1.4.1.apk** on your Android phone.
2. Open the APK and allow **Install unknown apps** for the browser/file manager if Android asks. Install KP Master, then open it. You can turn that installation permission off afterward.
3. Requires Android 8.0 or newer and an updated Android System WebView/Chrome. The app shows an update notice if the installed WebView is too old.

This is a directly installed APK, not a Play Store listing. It includes the supplied KP Master / Shree Swami Samarth icon and all 209 remedies across 49 subjects. Approximate size: 7 MB. It works offline; WhatsApp sharing uses the installed WhatsApp app and its Internet connection.

## Use on your phone

- Bottom navigation: **Remedies**, **Customers**, **Bookings**, **Accounts**, **Quotes & invoices**. Tap **Menu → Settings** to change consultancy/astrologer details and print selections.
- Customers: add a customer, save follow-up/appointment/visit details, and tap the appropriate WhatsApp button. WhatsApp or WhatsApp Business opens for you to review and send the message.
- Bookings: save Matrugaya bookings and receipts, calculate advance/balance, and export Excel.
- Accounts: record collections and expenses. Choose daily/monthly/yearly reports and Print or Export Excel. Invoice payments use the same Accounts ledger.
- Quotations/invoices: itemised drafts, quote conversion, invoice payments, and **Preview & print**. Choose A5/A4 and top space; use **Actual size** to zoom the preview. **Print / Save PDF** opens Android printing. Choose Save as PDF or an available print service, confirm the paper size and save/print.
- Exports open Android's file saver. Choose Downloads or another folder, then Save. Imports open the phone's file picker. No broad file-access permission is needed.

## Bring existing PC data to the phone

Export each section's JSON backup on the PC, transfer the files to the phone and restore them in the matching sections. Restore Documents and the matching Accounts backup to retain invoice/payment links. Bookings, remedies, CRM, Accounts, Documents and Settings each have their own backup/restore controls. Imports replace that section, so export a copy first.

The Android app and Windows/browser software keep **separate offline copies**. They do not automatically sync. Export backups regularly. Uninstalling the app or clearing its storage removes phone data; keep backups outside the app before either action. Updating with a compatible APK signed by the same key should preserve storage; keep backups before updates.

## Build and checks

Signed release APK, package `com.swamisamarth.kpmaster.mobile`, version 1.4.1, minimum Android API 26, target API 35. No Internet, contacts, phone or broad storage permissions are requested by KP Master. Android owns the document picker and print dialog. The APK signature and embedded assets are verified; adjacent `.sha256` contains the download checksum.

Mobile Chromium checks cover all six workspaces, CRM persistence, booking links, privacy of WhatsApp text, JSON/Excel exports, A5/A4 print bridge calls, afterprint cleanup, settings persistence, older-engine compatibility and phone-width overflow. Excel output was independently read with openpyxl. Device/emulator and physical hardware validation limits are recorded with the delivered release.

### Validation limits for this build

The APK passed Android apksigner verification (v2/v3), ZIP/DEX/resource checks, minimum/target SDK checks, non-debuggable/no-permissions checks, and an exact comparison of embedded HTML to staging. Browser tests passed at phone width with native calls intercepted, including older-WebView compatibility. No WhatsApp messages were sent during testing.

An Android 11 x86_64 emulator was attempted without KVM hardware acceleration. Its first boot did not reach a usable system state in the available smoke-test window; an install attempted during partial boot failed in the emulator's unready package/storage services. This does **not** establish successful native installation. Native APK installation, file picker saves/imports, Android print/PDF dialogs, WhatsApp app launching and physical printers remain to be checked on an Android device. No physical-phone test is claimed.

Release signing certificate SHA-256: `995dc0871009110ac9f1fe69e2a60e7c0af366d69a1378be37ec332c513c4739`.

## 1.4.1 remedy screen correction

Search, Subject filter and Add remedy are now shown at the top of the Remedies workspace. They were inside a desktop header hidden by the original mobile layout. The controls now live in a dedicated mobile toolbar. New tests confirm that they are visible at 320/390/768 px, and that a newly saved Marathi remedy can be found by keyword after restarting the page. The package, signing certificate and offline storage keys are unchanged; install as an update and keep regular backups.
