# KP Master 1.3.2 — document preview and A4 printing

Quotations and invoices open an in-app preview before printing. The preview offers A5/A4 portrait and adjustable top space (4–40 mm; default 6 mm). Both preview and print use the same document markup. A named billing page rule applies paper/margins to document printing without changing remedy, booking or account report paper sizes. No quotation/invoice data schema or storage keys changed.

Checked staged desktop HTML with Chromium:

- `check-billing-preview.cjs`: quotations and issued invoices preview before opening print; preview alone does not call print; preview and printable markup match; A5/A4 changes sheet width; top margin validation; unsaved edits blocked; Close/Escape; mobile layout; long document output; no browser page errors.
- PDFs independently checked for A5 (148 × 210 mm) and A4 (210 × 297 mm) dimensions. Default first printed text starts near the top (about 5 mm), rather than reserving a large blank header. Increasing top space from 6 to 12 mm moves content down accordingly.
- `check-billing-whatsapp.cjs`: existing CRM/WhatsApp, quote conversion, issued document locking, payments, overpayment rejection, void balances and persistence pass with the preview step.
- Long quotations retain final item lines and totals on additional pages.
- ASAR bytes and version 1.3.2 verified; HTML ZIP and installer archive integrity checked. GitHub downloads fetched back and compared with local SHA-256 checksums.

The in-app preview shows wrapping and spacing on the selected paper width; native print preview is authoritative for final page breaks. Windows printer drivers and physical printers are not available on this Linux build machine. The installer is unsigned. Back up all software sections before upgrading.
