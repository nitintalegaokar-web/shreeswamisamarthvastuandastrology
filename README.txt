KP MASTER Customer Edition — Windows x64 Setup 1.1.4

Install on Windows 10/11 x64. Includes installation wizard, desktop/Start menu
shortcuts and an uninstaller. Keeps the existing customer application identity
and saved charts/licenses. No separate runtime installation is required.

Fixes Windows System ID lookup: reads the real Registry64 MachineGuid directly,
with PowerShell registry fallback and optional hardware UUID. Retry ID is on the
activation screen. A checked local identity record preserves the chosen scheme.
Healthy legacy UUID-based IDs remain compatible; an uncached legacy ID can
require license reissuance if its UUID is unavailable on first upgrade.

Bound to the existing owner public key FFD543E7AFCE69618D61325E. Private owner
keys are never included. Existing .kplicense signatures/formats are retained.

Accepts signed .kpcontrol Activate/Deactivate status files from Owner Activation
1.1.0. Import from the locked activation screen or active workspace's top-right
three-dot menu. Deactivation persists across restart and blocks reimport of the
old license. A newer activation file restores a still-valid license; it does not
extend expiry. Offline clients must import the file; this is not instant remote
revocation. Older/conflicting revisions, wrong keys/computers are rejected.

Includes the previously released Raphael latitude-minute policy: <=30 minutes
uses the current degree sheet; >30 minutes uses the next degree sheet. Physical
latitude, full-precision ST, birth-instant KP ayanamsha and A4 reports preserved.

Validation: 23 unit tests; isolated actual Electron owner/client activation,
Retry recovery, status persistence, stale file rejection, wrong-key checks;
original-public-key gate checks; ASAR/source parity and installer archive checks.
Native Windows installation/launch could not be run in this Linux environment.
Windows-specific identifier paths/failures were verified with unit fixtures.

Unsigned installer. SHA-256 is in SHA256SUMS.txt.

Installer source: 48b8bbf8b3f0e9c7c50858b5cb3cd570da5f5a92
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/48b8bbf8b3f0e9c7c50858b5cb3cd570da5f5a92
