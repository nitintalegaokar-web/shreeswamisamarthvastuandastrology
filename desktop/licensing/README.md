# System-ID client activation

KP Master 1.1.0 requires an Ed25519-signed license for the current computer.
Until verification succeeds, only the activation screen loads; the calculation
workspace, chart-file APIs and preview windows are blocked. Verification runs
at startup and every minute while the program stays open.

On Windows, the System ID hashes the Windows MachineGuid and SMBIOS system UUID.
Raw identifiers are never sent to a server or included in the license. Ordinary
restarts, username changes and network-card changes do not change this ID.
Reinstalling Windows, replacing the motherboard, or changing a virtual machine's
UUID can change it; issue a new license when that happens. Missing WMI/registry
information produces an explicit error rather than a random or changing ID.

## Owner setup

1. Run `KP-Master-Owner-Activation-1.0.0-x64.exe` on your own Windows PC.
   You can instead install `KP-Master-Owner-Activation-Setup-1.0.0-x64.exe`
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
with ephemeral test keys. Do not distribute a client configured with those keys.
Windows-specific WMI reads and the executable launch need a native Windows check;
the Linux desktop test uses its actual `/etc/machine-id` without a licensing bypass.
