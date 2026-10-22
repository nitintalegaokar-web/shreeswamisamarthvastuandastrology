# Browser workflow checks

Use the repository's Playwright dev dependency and system Chromium (`/usr/bin/chromium`). Build/stage the HTML first, start an HTTP server at the repository root on port 8084, and create `/tmp/remedy-design` for test output. Override the page URL with `KP_TEST_URL` if needed. Tests use new browser contexts and synthetic contacts, with no actual WhatsApp sending.

Run in order:

```sh
node desktop/tests/check-crm-finance.cjs
node desktop/tests/check-billing-whatsapp.cjs
node desktop/tests/check-data-safety.cjs
node desktop/tests/check-document-restore.cjs
```

The restore check uses the document backup produced by the billing check. Reports, backups and screenshots are written to `/tmp/remedy-design`. The date fixtures are in 2026; quote numbering assertions expect the current India calendar year to be 2026. These tests do not exercise native Windows setup or physical printing.
