# KP MASTER · Simple activation · 1.2.6

Install the updated Owner Activation tool on your Windows PC. Install Customer
1.2.6 on the customer's Windows PC or Android phone (over its existing version).
The Owner calculator remains unlocked and requires no activation.

## One-time owner setup

1. Enter the original password for your encrypted owner key.
2. Keep **Remember securely on this Windows PC** checked and click **Open owner key**.
3. Choose your recovered key. Its ID should be **77F4455FF0BD330B82760384**.
4. The green Ready message means setup is complete. Keep the original encrypted
   key and password in a separate backup. Never send them to a customer.

Windows protects the remembered copy for your Windows account on this PC.
The password is not saved. After restarting the Activation tool, the key opens
automatically. Anyone using your Windows account can issue licences; use
**Lock and forget this PC** when you no longer want that convenience.

## For every customer — no files needed

1. Customer copies the System ID from Customer 1.2.6 and sends it to you.
2. Paste it into Customer System ID. Enter their name and choose Permanent or an expiry date.
3. Click **Generate activation key**, then **Copy key to send to customer**.
4. Send the complete **KP-A1…** key as text.
5. Customer pastes it into **Activation key** and presses **Activate / Apply key**.
   Android: **Enter activation key → Paste → Activate / Apply**.

The customer list retains name, System ID, period/expiry and issued status.
**Copy key** lets you resend a generated key. Green **Activate** and red
**Deactivate** generate a **KP-S1…** status key to copy and send. Customers paste
it in the same key screen; running apps provide **Enter Activate / Deactivate key**
in the menu. An offline change applies when the customer pastes the status key.
The list shows issued status, not remote confirmation from an offline device.

Customer 1.2.6 is required for text codes and recovered key
77F4455FF0BD330B82760384. Older approved keys remain accepted. A phone and PC
have different System IDs and need separate codes. Existing signed file licences
and status files continue to work through the optional file controls.

## Validation

- 38 licensing, identity, history, trust and key-vault unit tests passed.
- Electron activation workflow and history UI tests passed using temporary test keys.
- Android signature/control verifier: 18 JVM assertions passed.
- Mobile layout/export/backup/A4 tests passed; calculator and Dasha model unchanged.
- Both Windows calculator archives reproduce the original index.html after removing
  the existing desktop file bridge; the Android calculator assets are byte-identical.
- No private owner key or password is included in any download or Git commit.

Native Windows DPAPI and installer execution cannot be exercised on this Linux
host. Real Windows secure remembering and Android picker/printing remain device checks.
