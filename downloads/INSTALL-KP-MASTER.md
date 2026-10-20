# KP Master 1.2.0 — Windows installer

Download **KP-Master-Setup-1.2.0.exe** from this folder using GitHub's **Download raw file** button. Run it on **64-bit Windows 10 or 11**, choose the installation folder, and open **KP Master** from the desktop or Start menu.

Includes:

- All 209 remedies in 49 subjects.
- Matrugaya booking form, saved bookings, advance and balance calculation.
- Settings for consultancy name, astrologer name, address and mobile.
- Print switches for business details on both remedy and booking printouts.
- A5 portrait remedy printouts and booking receipts.
- Excel booking reports with totals, repeated headings and A5 landscape print settings.
- KP Master icon and uninstall support.

The runtime is included; Python, Node.js and a browser do not need to be installed separately. Local features work offline; WhatsApp sharing requires Internet access and opens a prepared message for you to send.

Before updating, export remedy, booking and settings JSON backups. The application uses the same app identity and `%APPDATA%\SwamiSamarthRemedies` data folder as version 1.0.0. Browser/HTML data is separate; export it there before importing it in the installed app. Imports replace their respective collections. Uninstall preserves application data.

Choose A5 paper (148 × 210 mm), Portrait and 100% scale when printing. Long content may continue onto additional A5 pages. Choose Microsoft Print to PDF or Save as PDF to generate a PDF.

This is an unsigned build; Windows may display an unknown publisher. It was cross-built on Linux: packaged application contents, icon metadata, browser workflows, A5 output and installer archive integrity were checked. Native Windows installation, upgrades, shortcuts, uninstallation and printer dialogs have not been tested here.

`KP-Master-Setup-1.2.0.exe.sha256` contains the SHA-256 checksum for verifying the installer download.

## Print a saved-bookings Excel report

Open **Matrugaya Bookings → Saved bookings / नोंदी → Export Excel / एक्सेल**. Save the `.xlsx` file, open it in Microsoft Excel and choose **File → Print**. A5 landscape and fit-to-one-page-wide are preconfigured; rows continue onto more pages as needed. The report includes booking ID, customer, mobile, departure, persons, total, advance and balance, plus totals. Settings print preferences control the business details in the heading.

The report is generated locally and works offline. Phone numbers and booking IDs are preserved as text; amounts remain numeric and balance/totals formulas are included. Native Excel print dialogs were not tested on this Linux build machine.
