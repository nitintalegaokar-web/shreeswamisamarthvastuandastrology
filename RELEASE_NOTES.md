## Issued-license controls · 12 October 2026

Owner Activation tool 1.1.0 adds green Activate and red Deactivate buttons to
Recently issued licenses, with English/Marathi labels and an issued-status badge.
The issuing owner key must be unlocked. Each action exports a signed `.kpcontrol`
file; the offline client must import it before the change takes effect.

Customer 1.1.4 imports these files from the activation screen or the workspace
⋮ menu. Deactivation survives restart and blocks old-license reimport; a newer
activation command restores a still-valid license. Altered signatures, wrong
computers, wrong owner keys and stale/conflicting revisions are rejected.
Activate does not extend license expiry. The original owner public key
FFD543E7AFCE69618D61325E is retained. The full owner calculator remains 1.0.3.

## Windows activation reader fix · 12 October 2026

Customer 1.1.4 fixes the unavailable System ID shown in the Windows activation
screen. The earlier PowerShell registry path was over-escaped, and the combined
registry/WMI command failed whenever WMI was unavailable. MachineGuid is now
read directly from the 64-bit registry, with an explicit Registry64 fallback;
CIM/legacy WMI supply an optional hardware UUID. A checked local identity
record keeps the selected ID stable through WMI failure and recovery, while
requiring the actual Windows installation ID on every launch. Healthy legacy
UUID-based IDs remain compatible; an older uncached ID can require reissuance
if its UUID is unavailable on upgrade. There is no random-ID or licensing bypass.

Retry ID is available in English and Marathi. Signed owner licenses are still
required, and the existing owner public key, calculator and Raphael rules are
unchanged. The unlocked owner calculator remains 1.0.3.

## Raphael latitude-minute rule · 12 October 2026

Automatic Raphael calculations now select one latitude sheet: minutes up to
and including 30′ use the current degree; minutes strictly above 30′ use the
next degree. 18°30′00″ uses 18° N; 18°30′01″ uses 19° N. The selected sheet is
used for the actual cusp calculation and displayed Excel values, with ST
interpolation retained and no interpolation across latitude sheets. The
original geographical latitude remains unchanged in birth details and reports.
The source status shows both the original and selected table latitude.

60°30′00″ uses 60° N; above that the requested 61° sheet is unavailable, so
the existing Placidus fallback uses true geographical latitude. Explicit
Date-specific Placidus and numbered horary continue to use their own methods.
The source values still show whole degrees for X/XI/XII/II/III and D:M for the
Ascendant. ST, KP ayanamsha and final DMS rounding remain unchanged.

Owner 1.0.3 and customer 1.1.3 include this rule. Customer licensing retains
the same public-key ID FFD543E7AFCE69618D61325E and existing license format.

## Raphael source units · 12 October 2026

The Raphael worksheet source rows now display the original Excel entries: whole
degrees for X, XI, XII, II and III; D:M for the Ascendant. They show the lower
latitude bracket explicitly, with the adjacent latitude source rows available
under a compact arrow. Previously latitude-interpolated source values could
appear as long decimals, such as 86.78333333. Latitude interpolation now appears
in clearly labelled derived D:M:S rows, while full-precision final cusp
calculations, ST, KP ayanamsha and source workbooks remain unchanged.

Owner installer 1.0.2 and customer installer 1.1.2 include this correction.
The locked customer remains bound to owner public-key ID
FFD543E7AFCE69618D61325E; no private key is needed for building either edition.

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
