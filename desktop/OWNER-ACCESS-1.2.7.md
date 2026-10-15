# KP MASTER · Fresh owner access · 1.2.7

The old Create/Open owner key settings are removed from the Activation screen.
You do not need any existing private-key file or its password.

1. Install Activation 1.2.7 on your Windows PC.
2. Enter the new owner access code supplied separately with this release, then click Continue.
3. Windows securely remembers your access on this PC. Keep the code private and backed up.
4. For each customer: enter System ID, name and period → Generate activation key → Copy key.
5. Install Customer 1.2.7 on their PC or Android phone. They paste the KP-A1 key and activate.

The owner access code unlocks the owner tool. Never give it to customers.
Customers receive only their own generated KP-A1 activation key or KP-S1 status key.
Green Activate, red Deactivate, expiry, Permanent, customer history, code copying,
Remove/Restore and text exports remain available. Offline status changes apply
when the customer pastes the status key; the list records issued status only.

All previous approved customer public keys remain accepted. Earlier licences
continue to work. The new owner identity is B88A1F9822575FBA49AFF5BC. New keys
from this owner tool require Customer 1.2.7. A PC and phone need separate keys.
Changes to earlier licences still require their original issuer identity; if
that identity is unavailable, generate a fresh licence using this new setup.

The Activation installer contains an AES-256-GCM encrypted owner credential,
protected by scrypt and a separately supplied random 144-bit access code.
No plaintext private key or owner access code is packaged or committed.
Only public verification keys are included in customer apps. The Windows
remembered copy is protected by Electron safeStorage / Windows DPAPI and is
separate from the original legacy key cache. Lock owner tool removes this new
remembered copy. Changing Windows accounts or PCs requires the access code again.

Calculation source, approved formulas, tables and data are unchanged. Tests use
temporary credentials: 40 unit tests, owner-access and history UI tests, full
Generate/Copy/Paste activation/status/expiry/restart workflow, and 18 Android
verifier assertions. Android calculator/layout/backup/PDF checks preserve the
original model and Dasha values. Native Windows DPAPI and phone UI behavior
still require testing on those devices.
