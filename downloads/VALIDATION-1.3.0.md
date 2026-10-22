# KP Master 1.3.0 validation

Checked on Linux using Chromium against the staged desktop HTML with its content security policy:

- Existing 209 remedies, supplied KP Master icon, Settings persistence and selective print branding, booking save/reload/JSON export and exact advance/balance calculation.
- CRM save/reload, Marathi names, birth details, history, follow-up completion, booking links, JSON backup and responsive layout.
- Saved appointment/visit dates, times and locations; WhatsApp recipient and URL-decoded text for all three buttons; no private notes in messages; unsaved edits blocked; unchanged saves do not duplicate schedule history. WhatsApp opening was intercepted for verification; no customer message was sent.
- Daily/monthly/yearly ledger totals and calendar boundaries using integer amounts; booking advances do not create income; voided receipts remain in backups and are excluded from totals.
- Quotations with quantity, discount and optional tax; conversion preserves amount and linked references; issued invoices lock editing. Payments entered from Invoices and Accounts use one ledger; overpayment rejected; voiding a receipt recalculates invoice balance.
- Document backup restore, invalid imports preserve previous data, issued seller snapshots survive business profile changes, and print switches omit seller contact details.
- Invalid database payloads, failed storage writes and unreadable storage do not overwrite the saved data. Cancelling navigation retains unsaved customer edits.
- Real booking and accounts XLSX downloads under the desktop policy; independent openpyxl checks of numeric totals and A5 landscape configuration.
- Sample invoices/quotations produce one A5 portrait PDF; sample daily/yearly account reports produce A5 landscape PDFs. Longer documents can span multiple sheets.
- No JavaScript page errors in tested flows; mobile screens have no outer horizontal overflow.

Packaging checks compare ASAR HTML bytes with staging and check version 1.3.0; installer archives and HTML ZIP are integrity-tested. Published downloads are fetched back from GitHub and compared with local SHA-256 hashes.

Native Windows setup, upgrades, shortcuts, uninstallation, actual WhatsApp delivery and physical printer/Excel dialogs require checks on the target Windows computer. This build is unsigned.
