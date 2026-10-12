KP MASTER Customer edition - 1.1.3
Windows 10/11 x64 Setup.exe

Raphael latitude selection update, 12 October 2026:
Up to and including 30 latitude minutes uses the current whole-degree sheet. Strictly above 30 minutes uses the next whole-degree sheet. Examples: 18:29:59 -> 18 N; 18:30:00 -> 18 N; 18:30:01 -> 19 N; 18:59:59 -> 19 N. This is a minutes threshold, not decimal degrees .30. A geographical decimal coordinate 18.30 degrees is 18 degrees 18 minutes and selects 18 N.

The selected whole-latitude sheet is used in the actual cusp calculation, source rows and automatic native/Instant Prashna calculations. The birth latitude stays unchanged in data and reports. There is no blending across latitude sheets in automatic mode. Full-precision interpolation between supplied ST rows, KP ayanamsha and final DMS rounding remain. Houses 10/11/12/2/3 source rows show whole degrees; Ascendant source rows show D:M. The seven XLSX source hashes and all 22,021 source rows are unchanged. Source degree/minute precision does not establish arcsecond astronomical accuracy.

60:30:00 selects the available 60 N sheet. Above this, a 61 N sheet would be required; no such sheet is invented or clamped. The existing Placidus fallback uses the true geographical latitude, as do southern-latitude fallbacks. Explicit Date-specific Placidus and numbered horary retain their own methods.

Checks passed across final targeted runs: original source rows/hashes and exact lookup/wrap; actual selected-sheet cusps at the 30-minute boundary and one second above; preserved geographical latitude/planet positions; fallback and explicit computed mode; independent full-precision ST and birth-instant KP ayanamsha; source units; manual/horary preservation; offline saved source; private-worker import/hiding; current HTML/runtime ASAR parity; owner native .lkp Save/Open and restored degrees; Marathi labels and chart hover; real-public-key customer activation lock, wrong-owner signature rejection and stable System ID; NSIS metadata, archive CRC, uninstaller and exact native/application payload parity. Native Windows installation/execution was not tested on this Linux host. This installer is unsigned.

The setup includes the full offline runtime, desktop/Start menu shortcuts and an uninstaller. No separate Python, Node.js or browser installation is needed. SHA-256 is in SHA256SUMS.txt.

LOCKED customer calculator bound to the same real owner public-key ID FFD543E7AFCE69618D61325E. No private keys, test keys/licenses or owner tool are packaged. Existing valid matching-computer licenses remain compatible. Client sends the complete KP1 System ID; owner opens the existing key locally in Owner Activation, enters client name/System ID, creates the .kplicense, and sends that file to the client to import and activate offline. Keep the owner private key and password on the owner PC.

Installer source: e341baeb76afe5ca71e3380f5fbb3fcc1b377811
https://github.com/nitintalegaokar-web/shreeswamisamarthvastuandastrology/tree/e341baeb76afe5ca71e3380f5fbb3fcc1b377811
