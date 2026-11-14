# KP Panchang Studio 3.0

Download KP_Panchang_Studio_v3_Setup.zip, extract it, and run
KP_Panchang_Studio_v3_Setup.exe. Close the previous version before updating.

Changes:
- North Indian Kundali has non-filled grid lines and separate house labels.
- South Indian fixed-zodiac Kundali begins with Pisces at top left, clockwise.
- Working File, View, Report and About menus.
- Settings save/open; logo selection; searchable places; local Access MDB/ACCDB,
  CSV and JSON import with column mapping and persistent city storage.
- Modern and traditional Panchang reports, one month per page, 1900–2500.
- Print current view, whole year, or a standalone Kundali; HTML and SVG exports.
- KP EPHEMERIES branding; detailed notes moved out of the main workspace.

The exact uploaded logo and AllPlaces database are NOT preloaded in this build.
The database exceeded the chat transfer limit; the logo was supplied inline.
Use File > Choose logo and File > Import places to load them directly on your
computer. To ship them as defaults in a later build, provide the logo as an
image file and the database in a ZIP under 32 MB.

The source ZIP contains code, build instructions and validation scripts. The
large generated year files can be reproduced with generate.py or extracted from
the installer. See BUILD-v3.md for scientific generation provenance and tests.
All 613 installed files were verified against their inputs; browser/menu/import
checks, 601-year coverage, and PDF page tests passed. The installer is unsigned;
native Windows installation, shortcut and direct-file launch still need a
Windows verification run. Main repository files are unchanged by this branch.
