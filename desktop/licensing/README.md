# System-ID client activation

KP MASTER Customer 1.1.5 requires an Ed25519-signed license for the current computer.
Until verification succeeds, only the activation screen loads; the calculation
workspace, chart-file APIs and preview windows are blocked. Verification runs
at startup and every minute while the program stays open.

On Windows, the reader queries the real 64-bit Windows MachineGuid with `reg.exe`; an explicit Registry64 PowerShell API is a second read path. The SMBIOS UUID is optional: CIM is attempted with legacy WMI as a fallback, but unavailable WMI or blocked PowerShell no longer prevents an ID when the registry is readable. Healthy UUID-based IDs use the same hash as earlier releases. If no UUID is available on first successful setup, the hash uses the Windows installation ID only. No random value or environment-provided identity is used.

A local `system-identity.json` in the current user's application-data folder preserves the chosen scheme. GUID-only IDs stay GUID-only when WMI returns, and cached UUID-based IDs survive temporary WMI failures. Every launch first checks the live Windows MachineGuid; copying the cache to a different Windows installation does not copy its ID. A changed available hardware UUID or changed Windows MachineGuid produces a new ID. If an older UUID-based installation has no identity record yet and WMI cannot read that UUID on upgrade, its newly generated ID may require a newly issued license. Do not accept a signed license for another computer just to work around an unavailable identifier.

Raw identifiers are not sent to a server or included in licenses. The local identity record stays on the computer. A missing/invalid real MachineGuid gives a registry-access error, and an unwritable identity record gives a folder-access error. Use **Retry ID** after correcting either problem. The owner's signing key and the license format are unchanged.

## Owner setup

1. Run `KP-Master-Owner-Activation-1.1.1-x64.exe` on your own Windows PC.
   You can instead install `KP-Master-Owner-Activation-Setup-1.1.1-x64.exe`
   and open **KP Master Activation** from its desktop or Start menu shortcut.
2. Enter a password of at least 12 characters twice, click **Create owner key**,
   and save the encrypted private key. Back it up securely. The password is never
   saved; a forgotten password or lost private key cannot be recovered by the tool.
3. Click **Export public key** and send **only that public key** to the developer.
   The matching public key must be packaged in the client build before distribution.
4. Keep using the same private key for this client build. Opening a different owner
   key does not let it activate a build tied to the original public key.

The owner tool does not contain a built-in private key. It generates the key on
your computer, stores it as AES-256-CBC encrypted PKCS8, and decrypts it only when
you enter the password. Closing the program or clicking **Lock key** clears the
unlocked key from the tool's state. Do not distribute your private key or password.

## Activate a paying client

1. The client opens the locked software and uses **Copy ID** or **Save ID** to
   send you their System ID.
2. Open your owner key with its password. Enter the client name and System ID.
   Choose **Permanent license** or an expiry date in UTC.
3. Click **Create activation license** and send the resulting `.kplicense` file.
4. The client clicks **Import activation license**. The signed license unlocks
   that computer and persists across restarts without internet access.

The tool records recently issued licenses locally on your PC. The client only
receives their signed license; copying it to a different System ID fails.
Timed licenses use the client's computer clock. Offline activation cannot
provide immediate remote revocation or dependable protection against an
administrator deliberately rolling back the clock or modifying the program.
This is a per-computer activation check, not tamper-proof DRM. Previous unlocked
executables and the previously distributed standalone HTML stay unlocked; this
new check cannot retrospectively lock copies already shared.

## Activate / Deactivate an issued license

Owner Activation 1.1.0 adds green **Activate** and red **Deactivate** buttons to
Recently issued licenses. Open the same owner key that issued that row. These
buttons export a signed `.kpcontrol` status file; the table shows the **status
issued**, not a remotely confirmed client state. Cancellation leaves history
unchanged. An expired license must be renewed with a new `.kplicense`; Activate
does not extend its expiry.

Send the exported status file to the client. In an active customer workspace,
open the top-right **⋮** menu and choose **Import license status**. On the locked
activation screen, use **Import status file**. A Deactivate command closes the
workspace and persists across restart. Reimporting the old activation license
cannot undo the saved deactivation. A newer Activate status file restores access
if the signed license is still valid. Older/conflicting revisions and files for
another owner or computer are rejected. Clients need Customer 1.1.4 or later to
apply these files. An offline client must import the command: clicking the owner
button does not remotely contact or instantly disable that computer.

Customer 1.1.5 accepts the verified current owner key ID
**D5909EAD14FB2D4717E98A8C**, while retaining original key ID
**FFD543E7AFCE69618D61325E** for existing licenses. Continue using the same
issuing private key on your own PC. Installing the updated tool preserves
its existing history and application identity. The full unlocked Owner calculator
1.0.3 is a separate application and does not require these status files.

## Build and test

From `desktop/`, use `npm run build:owner` for the owner tool. No signing key is
generated during a build. For the client, set `KP_LICENSE_PUBLIC_KEY_FILE` to
the owner's exported public `.pem` file and run `npm run build:windows`.
Preparation fails if that public key is absent or is not Ed25519. The private
key is never an input to the client build.
For installation wizards with shortcuts, use `npm run build:owner:setup` and
`npm run build:setup` respectively. Installation does not issue or bypass a license.

`npm test` covers signatures, wrong computers, owner-key mismatch, altered or
malformed licenses, expiry, identifier stability and encrypted key reopening.
`node test/licensing-runtime.cjs` exercises the owner UI and real client gate
with ephemeral keys in isolated temporary copies, including Retry ID recovery, signed status changes, restart persistence and stale-command rejection. The production public-key package is never replaced with those test keys.
Windows-specific WMI reads and the executable launch need a native Windows check;
the Linux desktop test uses its actual `/etc/machine-id` without a licensing bypass.

## Additional approved owner key

Customer 1.1.5 retains the original public key and adds the owner's explicitly
provided public export after verifying a supplied license and its System ID.
`additional-owner-public-keys.json` is normalized during preparation and bundled
inside ASAR. Arbitrary keys in license files or user data are never imported into
this trust list. Signature validation selects the actual approved signer, then
keeps System ID, expiry and date validation intact. An expired license signed by
one approved key cannot fall through to another key to become valid.

The activation screen lists accepted owner Key IDs. A status file must have the
same signer and license ID as the installed signed license; an additional trusted
key cannot deactivate or reactivate a license issued by another key. Existing
owner .kplicense and .kpcontrol exports remain compatible, and the supplied
license is not changed, renewed, or embedded in any installer. No production
private key is opened, requested, generated or packaged by this update.

## History removal, Help and text files

Owner Activation 1.1.1 adds **Remove** to each license row. It archives the exact
entry on the owner's PC, without revoking the customer license or deleting its
`.kplicense` file. Removal works with the owner key locked, including entries
issued by older keys. Expand **Removed entries** and use **Restore** to undo it.
Both lists have **Show more**. The license ID, expiry and control revision are
retained so restoration does not reset status-command replay protection.

**Help** opens English/Marathi instructions in this same activation window.
**Save help as Text** saves these instructions. **Save list as Text** exports all
retained entries, including later displayed pages, but excludes removed entries.
The UTF-8 `.txt` file includes client details, System ID, license and owner Key IDs,
UTC dates, issued status and revision. It never exports private keys, passwords
or signed license payloads. Text reports are records; clients continue to import
`.kplicense` for activation or `.kpcontrol` for status changes.

Installing the updated tool preserves its existing application-data identity
and legacy history array. Atomic history writes retain archived rows across
restart. Invalid history data produces an error rather than an empty replacement.
With an X display, `node test/owner-history-runtime.cjs` checks exact removal among
duplicates while locked, Restore/restart/revision retention, list/help exports,
English/Marathi behavior and cancellation using isolated temporary fixtures.
