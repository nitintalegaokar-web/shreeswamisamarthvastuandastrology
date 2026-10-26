from pathlib import Path
import re,zipfile
root=Path(__file__).resolve().parents[2]
target=root/'downloads'/'Swami-Samarth-HTML'
target.mkdir(parents=True,exist_ok=True)
s=(root/'previews'/'consultancy-preview.html').read_text()
s=s.replace('astroRemedies_a5_design_preview_v1','astroRemedies_v10_bw_dualprint').replace('swami_matrugaya_design_preview_v1','swami_matrugaya_bookings_v1').replace('swami_consultancy_profile_preview_v1','swami_consultancy_profile_v1').replace('swami_crm_design_preview_v1','swami_crm_v1').replace('swami_finance_design_preview_v1','swami_finance_v1').replace('swami_documents_design_preview_v1','swami_documents_v1')
s=s.replace('DESIGN PREVIEW · SAMPLE DATA','HTML REVIEW VERSION').replace('Design preview · Sample customer data · Remedy and booking printouts use A5 paper','Your data stays on this device · Remedy and booking printouts use A5 paper')
s=s.replace('It will replace bookings in this preview.','It will replace the currently saved bookings.')
s,count=re.subn(r"^bkSet\(\{bookingId:'SWAMI-SAMPLE-001'.*?\}\);$",'bkNew();',s,flags=re.M)
assert count==1,'Expected sample startup not found'
(target/'index.html').write_text(s)
for icon_name in ['software-logo.svg','software-logo.png','software-icon.ico']:
 (target/icon_name).write_bytes((root/'previews/source/branding'/icon_name).read_bytes())
(target/'THIRD-PARTY-NOTICES.txt').write_bytes((root/'previews/source/vendor/THIRD-PARTY-NOTICES.txt').read_bytes())
(target/'READ-ME.txt').write_text('''SWAMI SAMARTH — REMEDY & MATRUGAYA BOOKING SOFTWARE
HTML version 1.3.2 — 26 October 2026

GET STARTED
1. Extract this ZIP to a folder on your computer.
2. Open index.html with Microsoft Edge or Google Chrome.
3. Open Settings and enter the consultancy name, astrologer name,
   address and mobile. Click Save settings.

INCLUDED
- Quotations, itemised invoices, quote conversion, A5 print/PDF and linked payments.
- Offline customer CRM, consultation history and on-screen follow-up reminders.
- Daily collections and expenses with daily/monthly/yearly A5 reports and Excel.
- Saved appointment and site visit schedules, with WhatsApp sharing buttons.
- Separate CRM, accounts and quotation/invoice JSON backup/restore.
- All 209 remedies in 49 subjects, with search and editing.
- Saved bookings Export Excel button creates a real .xlsx workbook with
  payment totals, repeated headings and A5 landscape print settings.
- Matrugaya booking form, automatic remaining balance, saved bookings,
  booking JSON export/restore and prepared WhatsApp confirmations.
- Editable business profile, live letterhead preview and settings backup.
- A5 portrait remedy printouts and booking receipts.

PRINT SELECTION
Settings > Print astrologer details turns the astrologer name, address
and mobile on or off together. Use the individual checkboxes to choose
consultancy name, astrologer name, address and mobile separately.
Click Save settings after making changes. These choices affect remedy
printouts, booking receipts, accounts reports and quotations/invoices.
WhatsApp signatures retain saved contact
information; print selections do not remove details from messages.

A5 PRINTING
Use a remedy's Print button or Print A5 receipt in the booking form.
In the print dialog choose A5 paper (148 x 210 mm), Portrait, scale 100%,
and turn browser headers/footers off. Select Save as PDF to download a PDF.
Long remedies or unusually long booking details continue onto more A5
pages. No content is deliberately clipped to force a one-page receipt.

DATA AND BACKUPS
Data is kept in this browser on this device. Export remedies, bookings,
settings, CRM, accounts and documents regularly using each section's separate
JSON backup button. Keep matching Accounts and Documents backups together:
invoice payments are ledger entries, not stored inside document backups.
Browser storage and the Windows desktop app store data separately.
To transfer existing notes, export a backup in the old software and import
it here. Keep a copy before importing: remedy and booking imports replace
the respective current collections. Moving or renaming index.html can
change the browser storage location, so export first.

CRM AND WHATSAPP
Save the customer, follow-up date/purpose, appointment date/time/location,
and visit date/time/address/details in Customer CRM. Use WhatsApp follow-up,
appointment or visit buttons below the form. Review the prepared message
and press Send in the installed WhatsApp app. WhatsApp must be installed
and signed in on this computer; browser versions may ask permission to open it. Only the shareable schedule fields are included;
private consultation notes and birth details are excluded. Use +country code
for international mobile numbers. Indian 10-digit mobiles use +91.
Follow-up reminders appear inside the app; no background alerts are sent.

ACCOUNTS AND DOCUMENTS
In Collections & Expenses, record money actually received or spent. Select
Daily, Monthly or Yearly, choose a date/month/year, then Print or Export Excel.
Reports use A5 landscape. Net movement is collections minus expenses, not
an opening/closing bank balance. Booking advance fields do not automatically
create collection entries. Record each actual receipt once.
In Quotations & Invoices, save an itemised draft, finalise it or convert a quote
to an invoice. Issue the invoice, then Record payment in Accounts. This creates
one collection entry; do not enter the same payment again in Accounts.
Invoice balances use active linked ledger entries. To correct a receipt, void
it with a reason in Accounts, then record the correct receipt. Issued documents
are locked; void and create a replacement if needed. Quotation and invoice
Preview & print lets you choose A5 or A4 portrait and top space (4-40 mm).
Review the document, then Print / Save PDF. Select the matching paper in the
printer dialog, scale 100%, headers/footers off. Long documents span pages.

No server or installation is needed for this HTML version. It works offline,
except WhatsApp sharing. Marathi rendering requires a suitable installed
font (standard Windows Marathi fonts are supported).

This ZIP does not update the previous Windows installer. It includes a square KP Master icon prepared from your supplied artwork,
embedded as the browser icon and sidebar logo. PNG, SVG and Windows ICO
versions are included for future packaging.
''')
zip_path=root/'downloads'/'Swami-Samarth-HTML.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(target.iterdir()):z.write(p,'Swami-Samarth-HTML/'+p.name)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert z.read('Swami-Samarth-HTML/index.html')==(target/'index.html').read_bytes()
print('ZIP verified:',zip_path,'('+str(zip_path.stat().st_size)+' bytes)')
