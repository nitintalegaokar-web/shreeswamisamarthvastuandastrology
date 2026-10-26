# KP Master 1.3.1 — WhatsApp app sharing

Changed all three CRM share actions, Matrugaya confirmations and remedy sharing to `whatsapp://send` URLs. Recipient normalization and encoded message text remain intact. The desktop shell permits only the WhatsApp send action with valid recipient/text parameters and opens it through the operating system. Web links and other protocols/actions are rejected. A failed launch explains that WhatsApp must be installed and signed in; no web fallback is attempted.

Validated with:

- `node desktop/tests/check-whatsapp-app.cjs`: app link allowlist and malformed/unrelated URL rejection.
- `node desktop/tests/check-whatsapp-routing.cjs`: mocked Electron shell routing, navigation cancellation, blocked web URLs and missing-app error guidance.
- `node desktop/tests/check-whatsapp-renderer.cjs`: Chromium under desktop CSP; follow-up, appointment, visit, booking and remedy buttons prepare app URLs, correct recipients and schedule details; private CRM notes stay out of messages and unsaved customer changes block sharing.
- `node desktop/tests/check-billing-whatsapp.cjs`: existing CRM/invoice/payment workflows with the updated app link assertions.
- ASAR bytes for main process, URL validator and staged HTML match source; package version is 1.3.1.
- Installer archive integrity and production ZIP integrity checked; GitHub downloads fetched back and SHA-256 compared with local files.

Windows WhatsApp activation, installed protocol registration and native Windows installation still require testing on the target computer. Browser HTML may display an external-app permission prompt. This installer is unsigned. Existing data keys and the desktop data folder are preserved; export backups before upgrading.
