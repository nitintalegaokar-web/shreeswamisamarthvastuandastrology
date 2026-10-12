KP MASTER Owner Activation Tool — Windows x64 Setup 1.1.0

Separate from the full unlocked owner calculator (which remains 1.0.3).
Installs KP Master Activation with desktop/Start menu shortcuts and uninstaller.
The application identity and recently-issued license history are preserved.

Adds green Activate and red Deactivate buttons to each recently-issued license
row, with an issued-status badge and English/Marathi labels. Open the owner key
that issued that row. Each action exports a signed .kpcontrol file; cancellation
leaves history unchanged. Send it to the client to import in Customer 1.1.4.
The table records issued status, not an online-confirmed client state.

For the existing customer build, use the original owner key with Key ID
FFD543E7AFCE69618D61325E. Your private key stays on your own PC. No private key,
production signing key or fixture key is included in this installer.

Offline changes take effect only when the client imports the signed file.
Deactivation persists across restart; old activation-license reimport does not
undo it. A newer Activate command restores a still-valid license. Activate does
not extend expiry; renew expired licenses with a new .kplicense.

Validation: actual Electron encrypted-key opening, issuance and key lock;
green/red status actions, cancellation, wrong-key rejection, persisted history,
Marathi labels, client deactivation/reactivation/restart and stale-file rejection;
ASAR/source parity and installer archive checks. Native Windows execution remains
untested in this Linux build environment.

Unsigned installer. SHA-256 is in SHA256SUMS.txt.

Installer source: 48b8bbf8b3f0e9c7c50858b5cb3cd570da5f5a92
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/48b8bbf8b3f0e9c7c50858b5cb3cd570da5f5a92
