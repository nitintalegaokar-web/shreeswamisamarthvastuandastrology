KP MASTER Owner Activation Tool — Windows x64 Setup 1.1.1

Close the old Owner Activation tool, install this update, and open KP Master
Activation from its desktop/Start menu shortcut. Existing keys and issued-license
history retain the same application-data identity. Customer 1.1.5 and the full
unlocked Owner calculator 1.0.3 are unchanged.

Remove beside a history row archives that exact license ID locally, even while
the owner key is locked or belongs to a different row. It does not delete the
customer's .kplicense file or deactivate their software. Expand Removed entries
and click Restore to undo removal. Active and removed lists have Show more.
Original license ID, expiry and control revision survive removal/restart/restore.

Help opens step-by-step English/Marathi instructions in the same window, covering
correct owner keys, new-customer activation, offline status changes, expiry,
troubleshooting and record management. Save help as Text saves those instructions.
Save list as Text exports all retained entries, including later pages, and excludes
removed entries. UTF-8 .txt files contain no private key, password or signed
license payload. They are records/instructions; customer activation continues to
use signed .kplicense files, and status changes use .kpcontrol files.

History writes use atomic replacement, preserve the existing legacy array format,
and report malformed data instead of silently replacing it with an empty list.
Activate/Deactivate still require the same private owner key that issued the
license. Offline status changes take effect only after the client imports the
signed file. Continue using the same approved owner key for every customer.
Customer 1.1.5 accepts D5909EAD14FB2D4717E98A8C and original
FFD543E7AFCE69618D61325E. This installer contains no private key.

Validation: 30 unit tests; actual Electron duplicate-entry removal while locked,
Restore/restart, unchanged signed license, preserved revision 7 to 8 after restore,
all-page text export, English/Marathi Help and exports, cancellation and invalid
request checks; existing owner/client signed issuance, wrong-key/signature/computer
rejection, activation/deactivation/reactivation/restart checks; final ASAR source
parity and key/license/record exclusion; setup metadata/CRC/payload/uninstaller.
These tests used isolated temporary projects and ephemeral test keys only.
Native Windows installation/launch remains untested in this Linux environment.

Unsigned installer. SHA-256 is in SHA256SUMS.txt.

Installer source: 5960362bacbc375df02a5e224a9081ecbd4a777a
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/5960362bacbc375df02a5e224a9081ecbd4a777a
