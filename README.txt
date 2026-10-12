KP MASTER Customer - System-ID-locked edition
Version 1.1.1 - Windows 10/11 x64 setup installer
Owner public-key ID: FFD543E7AFCE69618D61325E

This is the full locked customer calculator, bound to the actual owner-exported Ed25519 public key provided for this release. The unlocked owner edition is a separate installer. Only the public verification key is packaged here. No production private key was loaded, created or packaged, and no test keys or test licenses are included.

Installation: run KP-Master-Setup-1.1.1-x64.exe. The wizard creates desktop and Start menu shortcuts and registers the uninstaller. Runtime files are bundled; Python, Node.js, a browser installation and internet are not needed for calculations.

Activation: the client sends the displayed complete KP1-... System ID to the owner. In KP Master Activation on the owner's PC, open the existing owner key whose Key ID is FFD543E7AFCE69618D61325E, enter the client name and System ID, then create an activation license. Send only the resulting .kplicense file to that client. In the customer app, click Select license file to import it. Activation is verified against this build's public key and matching computer. Keep the owner's encrypted private key and password on the owner's PC.

Includes the current KP MASTER update, all seven uploaded Raphel workbooks, full-precision native sidereal time, birth-instant annual KP ayanamsha, one coloured vertical DMS/SGL/STL/SBL hover panel, repeatable saved charts, and Open Kundali/Save Kundali toolbar buttons. Calculate is removed from that toolbar; automatic calculations remain. The source tables have whole degrees for X/XI/XII/II/III and whole minutes for the Ascendant; displayed DMS retains these source precision limits.

Verified: packaged owner key matches the uploaded key and supplied Key ID; application and licensing code match current source; x64 Windows runtime; no private/test licenses/owner tool in package; real-public-key Linux Electron activation screen; unlicensed workspace and file-dialog access blocked; a license signed by another key rejected; Marathi activation controls and stable System ID across restart; licensing/policy unit checks; NSIS installer metadata, embedded uninstaller, archive CRC and exact payload parity. Earlier signed-fixture Electron workflows verified successful activation, wrong-computer rejection, persistence and tamper rejection; production-owner-signed activation cannot be exercised here because the owner's private key remains on their PC. Native Windows installation/execution was not tested on this Linux host. This installer is unsigned.

Installer SHA-256 is in SHA256SUMS.txt.

Installer source: c50ed747eb5362464c87b7ac97ad8bcb5090a095
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/c50ed747eb5362464c87b7ac97ad8bcb5090a095
