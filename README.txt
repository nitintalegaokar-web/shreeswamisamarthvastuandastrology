KP MASTER Customer Edition — Windows x64 Setup 1.1.5

Install this update on the customer PC, close the old KP MASTER before installing,
and open KP MASTER afterward. Import the existing signed .kplicense file using
Import activation license. An activation-status .kpcontrol file does not replace
the initial license. No separate runtime or internet connection is required.

This installer accepts the verified current owner key
D5909EAD14FB2D4717E98A8C and retains original owner key
FFD543E7AFCE69618D61325E. The provided license was correctly signed and matched
the provided client System ID, but Customer 1.1.4 lacked its issuing public key.
No new license is required while the existing signed license is still valid.

Use the same issuing owner key for future licenses. A new owner key requires an
explicitly approved customer-build update. Accepted Key IDs appear in the
activation window in English/Marathi. Only explicitly bundled approved keys are
trusted; keys in license files, renderer requests and user-data files are not
added. Native System ID binding, signature verification, expiry and date checks
remain enforced. Activate/Deactivate commands require the same signer and exact
license ID as the installed license, with existing replay protection retained.

This update does not renew a timed license or change its expiry. The Owner
Activation tool stays 1.1.0 and the full unlocked Owner calculator stays 1.0.3.
The customer application identity is preserved to retain charts/preferences and
activation data. All existing Raphael, ST, KP ayanamsha and A4 reporting rules
are unchanged. No private key, customer license or System ID override is bundled.

Validation: 27 unit tests; actual Electron multi-key license import, restart,
wrong-key/wrong-computer checks and signed status controls; exact supplied signed
license UI import/restart under a matching-ID fixture in an isolated test copy;
restoring the native reader proves copied-license rejection on another machine;
final ASAR approved-key/source parity and license/key exclusion checks; native
installer metadata, CRC, embedded uninstaller and exact payload parity checks.
No production private key was used. Windows-specific ID failure paths have unit
coverage; native Windows installation/launch remains untested in this Linux cloud.

Unsigned installer. SHA-256 is in SHA256SUMS.txt.

Installer source: 296b76b2fffd26b7fe71485aee0dd8b7161ba4da
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/296b76b2fffd26b7fe71485aee0dd8b7161ba4da
