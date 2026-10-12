## KP MASTER interface update · 12 October 2026

The visible software name is KP MASTER in the header, tab/window titles, About
and report branding. Planet/cusp hover uses one teal panel with separate DMS,
SGL, STL and SBL rows; native chart HTML/SVG tooltips are removed. Home mirrors
retain their elements until source content changes, keeping hovered labels stable.
Chart labels are localized by the chart formatter rather than competing with
the general text translator; Marathi names use the same translation dictionary.
The hover panel remains excluded from printing and closes on pointer movement.

Owner and customer editions use the same corrected chart data and interface.
The owner edition is unlocked and installs separately as KP MASTER Owner.
The locked customer installer needs the owner's exported public key; no private
key or temporary test key is packaged for production customers.

## Raphael table and ST update · 12 October 2026

All seven newly uploaded Raphel workbooks are embedded unchanged for automatic
Bhavsadhan (0°–60° north). The seven-column layout is validated, with all 22,021
unique rows preserved and file hashes recorded. X/XI/XII/II/III use their printed
whole degrees; the Ascendant uses degrees/minutes. The printed values match the
previous sheets; the new workbooks contain no hidden precise numeric columns.

Automatic native ST now advances the selected ephemeris reference at full
precision and applies the native longitude once. It avoids rounded intermediate
LMT corrections, preserves the supplied ST +1 second, and respects UTC offset,
DST and date rollover. Annual KP ayanamsha is evaluated at the actual birth UTC
instant and subtracted once; final cusp values are rounded to DMS. Source rounding
limits remain: these files do not establish arcsecond house accuracy. Existing
Date-specific Placidus and explicit administrator manual modes remain available.

# Offline Windows licensing update · 11 October 2026

Client version 1.1.0 adds a System-ID activation screen, signed per-computer
licenses, startup/periodic checks, and permanent or dated activation. The
separate Owner Activation tool creates a password-encrypted private signing key
on the owner's PC, exports its public key for the client build, and issues
client license files offline. A production client build requires that owner
public key; no private key is built into either executable. Existing unlocked
copies are unaffected. Licensing conventions and setup are documented in
`desktop/licensing/README.md`.

## Offline Windows update · 11 October 2026

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

The workspace toolbar now offers Open Kundali and Save Kundali for `.lkp` files. The Calculate toolbar button is removed; automatic calculation remains active. Ctrl/⌘ S uses the same file-save action.
