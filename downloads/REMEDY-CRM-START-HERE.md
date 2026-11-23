# Remedy CRM 1.6.0

This software is **Remedy CRM**. It has its own icon, installer name and application identity so it can be installed separately from Advance KP Master.

## Install and transfer records

- **Windows:** run `Remedy-CRM-Setup-1.6.0.exe` on 64-bit Windows 10/11. Setup uses its dedicated folder and creates a **Remedy CRM** desktop/Start menu shortcut and uninstall entry. Open that new shortcut.
- **Android:** install `Remedy-CRM-Android-1.6.0.apk` on Android 8+ with an updated System WebView/Chrome. This is a **separate app** (`com.swamisamarth.remedycrm.mobile`), not an update over the old KP Master APK. It uses a Remedy CRM signing identity and icon. Android may ask permission to install from the browser/file manager.
- **HTML:** extract `Remedy-CRM-HTML.zip` and open `index.html` in Chrome/Edge.

Before transferring, export your remedies, bookings, CRM, Accounts, Documents and Settings JSON backups from the earlier remedy/CRM software. Restore each in the matching Remedy CRM section. Earlier remedy/CRM backup formats and record IDs remain accepted, including backups with older KP-Master filenames. Restore matching Documents and Accounts backups together so invoice payments remain linked. Imports replace the corresponding current collection; keep originals and verify the results before removing anything.

Windows data is in `%APPDATA%\RemedyCRM`; the new app does not automatically read or copy `%APPDATA%\SwamiSamarthRemedies`. Windows, HTML and Android each have independent offline storage and do not automatically sync. Uninstalling/clearing Android storage removes its data. Keep backups outside the app.

## Simple CRM

1. Choose Customers / Customer CRM and Add customer.
2. Enter name, mobile, service and next follow-up if needed.
3. Save customer. Use WhatsApp follow-up to prepare a message in the installed WhatsApp app.

More contact details, appointments, visits, birth details, private notes and archive/restore remain available in labelled expandable sections. Private notes and birth data are excluded from customer report printing. WhatsApp always requires you to review and send; no automatic messages are sent.

## Report printing and diagrams

- **Customer report:** choose search/stage/follow-up filters, then **Preview / Print customer report**. The report uses that filtered list. The CRM diagram section shows stages and follow-up status; the printed customer report includes the follow-up diagram when selected.
- **Accounts:** select Daily, Monthly or Yearly and the date/month/year. The bars compare the selected period's actual collections and expenses. Click **Preview / Print report**.
- In the preview, choose **A5 or A4 landscape**, keep or clear **Include bar diagram**, then **Print / Save PDF**. Long lists continue onto more pages. Select the matching paper size, 100% scale and headers/footers off in the printer dialog. Android opens the system print/PDF service.
- Use Export Excel for editable numeric tables. Quote/invoice previews continue to offer A5/A4 portrait.

Net movement is collections minus expenses for the selected period, not a bank balance. Booking package/advance fields do not automatically create collections. Invoice payment receipts are entered once in the shared Accounts ledger; voiding a receipt updates the invoice balance.

## Checks and limits

Verified: separate Windows package/appId/GUID/shortcut/profile, Android package/label/signature, embedded assets, installer and ZIP integrity, browser CRM/backup/accounts/invoice flows, exact chart values, private-data exclusions, report immutability, and PDF A5/A4 landscape dimensions. Sample one-customer and short accounts reports fit one A5 sheet. Long report pagination is also checked.

Built and tested on Linux/Chromium. Native Windows installation, real coexistence with Advance KP Master, the new Android package's installation/native file/print/WhatsApp dialogs, and physical printers still require target-device testing. The Windows installer is unsigned; the Android APK is signed. Adjacent SHA-256 files verify the downloads.

## A5 remedy and Matrugaya heading spacing

The A5 letterhead is compact and the default top margin is **5 mm**. In **Settings → A5 remedy & booking layout**, adjust Top space from **4–25 mm**, then Save settings. Choose A5 portrait and 100% scale with browser headers/footers off. Increase the value if you want space for preprinted letterhead. All enabled consultancy, astrologer, address and mobile details remain printed.

In a PDF comparison using the same full letterhead, the Matrugaya document title moved from about 37.6 mm down the page to 26.7 mm; the removed gap was about 11 mm. A sample receipt and remedy each fit one A5 page; a long remedy continued across four pages and retained its final line. The 12 mm setting moved content down by about 7 mm compared with 5 mm. Hidden letterhead details reserve no empty heading block. Printer drivers can apply their own minimum margins, so verify on your target printer.
