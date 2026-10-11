# Offline Windows update · 11 October 2026

The Windows x64 portable executable packages the current standalone software
with Electron. Calculations and data run offline. Native Save/Open dialogs
handle `.lkp` files; language and preferences persist per Windows user. Report
popups keep the existing A4 print/PDF and zoom controls. Desktop windows isolate
the renderer from Node.js, block network requests, and open optional account
links in the external browser. The build is unsigned; no signing certificate
was provided. Rebuilding is documented in `desktop/README.md`.

## Previous software update · 10 October 2026

Open `index.html` after extracting the complete ZIP. Keep the `vendor` folder beside it. The private server is optional; its setup is described in README.md.

This update includes compact Event Promise, Prediction, House Results, Matchmaking and Transit screens; Roman cusp selection; ruling-planet PD filtering; grouped report selection; transient chart/table hover details; Vedic Kundali and traditional calculation reports; PDF-based HIT analysis and symbolic remedies; and separate Vedic Parashari and native KP Muhurta methods. Preview controls include print/save PDF, zoom and close. The private report download exports the selected visible report pages.

Current boundaries: the exact Dasha-entry rule awaits the astrologer's supplied rule. Marathi/English interface and chart labels are covered, while long imported English prediction paragraphs still need a reviewed Marathi text pack. Muhurta is common-purpose screening with the applied rules documented; ceremony-specific exceptions and full Tajika annual interpretations are not claimed. Calculation conventions are documented in vendor/vedic/README.md and vendor/hit/README.md.

Vedic follow-up: right-click a Vedic chart to switch North/South Indian geometry; open Sade Sati for automatically calculated Saturn phases. Print Report automatically prepares selected annual/Saturn reports and includes newly generated pages. Preview opens promptly, Print waits for prepared content, and Export to PDF downloads the selected A4 reports. Manual Vedic calculation buttons have been removed.

Vedic chart report layout: the report owns its border with a 4 mm inner margin instead of a fixed decorative border over the content. Chart/table widths respect that margin, and crowded Marathi planet labels wrap in divisional charts. North and South Indian layouts are checked in screen preview and A4 printing.

Basic Information (BI) is beside Birth Details and prints under General information. A local administrator PIN groups the five calculation worksheets plus DBA calculations under ADM, with automatic relocking. These calculation icons and sidebar entries are hidden; the normal DBA analysis popup remains available. PIN credentials stay separate from chart files.

House-table update (11 October 2026): all seven supplied Swiss Placidus workbooks are included for automatic Bhavsadhan. Their precise numeric columns supply 22,021 unique entries from 0°–60° north; local sidereal time and latitude interpolate automatically, with correct 360°/midnight handling and one KP ayanamsha subtraction. The normal Calculate action updates native cusps, kundali and significators. The source selector remains inside ADM; numbered KP Horary retains its exact numbered Ascendant. Unsupported table latitudes use the existing date-specific solver without extrapolating the uploaded tables. Existing manual chart files retain their input method.
