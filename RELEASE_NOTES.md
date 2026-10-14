## Original KP ayanamsha tables · 14 October 2026

Replaced the old annual interpolation with exact lookup of the user-supplied
Table IV-A annual DMS plus Table IV-B month/day addition. Imported 243 annual
values (1861–2103) and all 372 daily cells without generating or rounding them.
The supplied source text and SHA-256 are retained for review.

The approved regression is 10 October 1931: 22°47′40″ + 38″ = 22°48′18″.
Other references are 8 April 1949 (23°02′53″), 20 December 1950 (23°04′18″),
and 12 October 2026 (24°07′29″). The addition is constant during a calendar day;
ephemeris instants use their UTC date, and the birth worksheet uses the entered
birth date, preserving the existing date convention.

Removed the Swiss ayanamsha selector and its bundled calculation module. Old
saved Swiss/manual ayanamsha choices migrate to the supplied original table;
the annual/daily ayanamsha fields are read-only. Dates beyond the supplied table
are rejected instead of extrapolated. The wider ephemeris API retains its
existing 1900–2100 range.

Uploaded nirayan planetary rows remain authoritative and unchanged. They are
already sidereal; no second ayanamsha is subtracted. Raphael, LMT, ST, planetary
interpolation and Vimshottari formulas remain unchanged. Computed tropical
positions and Raphael tropical cusps use the newly approved table subtraction.

## Handy Transits and Panchang report cleanup · 14 October 2026

Transits now has three direct search buttons: Event significators, DBA through
each other, and Sun through DBA (MD/AD combinations). Start/end dates and time
zone are visible; event names can be searched, and all nine planets can be
selected together. DBA choices and advanced natal support remain available.
Editing a date switches to Custom dates before period defaults can overwrite
it. Results show entry/exit times with seconds; CSV export preserves UTC and
local times. Empty/error status appears once, and previews enable after a
completed search. Mobile/dark layouts have explicit readable colours.

The same-day 05:30 Transit Kundali is omitted from the Transit Panchang screen
and its print/report snapshot. Dinvisesh, festivals, auspicious periods and
calendar preview remain available. All approved calculation blocks are
unchanged; the compact interface delegates to the existing transit scanner.

## Standalone HTML transit finder fix · 13 October 2026

The career-change catalogue event can require source-condition review. The
finder previously stopped at that review before scanning any planetary transit.
Event search now offers `Transit intervals` (default), which scans the chosen
house significators and transit requirement within the selected date range,
and `Natal promise + DBA support`, which retains the existing source review,
natal-promise and supporting-DBA restrictions. Transit intervals are labelled as
transit conditions rather than confirmed event predictions. Search status and
results appear immediately below Find dates, ahead of advanced rules. The
Search period dropdown remains removed. Protected calculation formulas are
unchanged.

## Traditional 10/6 sidereal correction · 1.2.2 · 13 October 2026

Automatic Sidereal Time and Bhavsadhan now use the requested traditional KP
10/6 correction instead of the exact-GMST rotation introduced in 1.2.0. The
calculation uses complete elapsed hours × 10 seconds plus the remaining complete
minutes ÷ 6, retains the `57 ÷ 6 = 9.5` half, and performs one final half-up
rounding. Therefore `18:57:28` gives `00:03:10`, and the reported worksheet is
`21:20:52 + 18:57:28 + 00:03:10 = 40:21:30 − 24:00:00 = 16:21:30`.

The screen, preview, print/PDF worksheet, source badge and Raphael interpolation
all use that same result. The existing 05:30 reference-date boundary, LMT,
longitude correction, uploaded base ST, Raphael tables, planetary ephemeris,
KP ayanamsha and Vimshottari calculations are unchanged. The previous 1.2.0 and
1.2.1 notes below describe those historical releases; this rule supersedes their
exact-GMST wording.

## Protected interface, Transit Panchang and chart tools · 1.2.1 · 13 October 2026

### Sidereal-source state hotfix · 13 October 2026

Restoring a legacy chart while Administrator Calculations was unlocked could
leave the sidereal worksheet in Manual 10/6 mode even though no explicit manual
calculation record had been saved. Legacy and ordinary chart restores now return
planet positions, sidereal time and Raphael houses to Automatic, and ayanamsha to
the annual KP source. A manual source survives only when it was explicitly stored
with **Save manual entries**.

Administrator Calculations now displays a green Automatic or red Manual source
badge and provides **Use automatic calculations** to clear a persisted manual
override. The sidereal worksheet also identifies the unnormalised subtotal and
final value: for example, `40:21:30 − 24:00:00 = 16:21:30`. No sidereal,
Raphael, LMT, planetary or ayanamsha formula was changed.

This update was made on backup branch
`backup/pre-ui-1.2.1-2026-10-12` from calculation baseline `d15b677`.
Seventeen protected calculation blocks plus the Raphael, Vedic, Muhurta and HIT
source files match that baseline. Approved Raphael selection/interpolation,
KP ayanamsha, LMT, sidereal time, planet positions and Vimshottari formulas were
not rewritten. The displayed Sidereal rotation correction, including values such
as 00:03:12, continues to come from the approved exact-GMST calculation.

Transit Panchang now has a compact layout, Dinvisesh daily details, Tithi,
Nakshatra, Yoga and Karana transitions, sunrise/sunset, Abhijit, Brahma Muhurta,
Rahu Kaal, Yamaganda, Gulika, day/night Choghadiya, general vrata/festival notes
and auspicious periods. It also shows an independent same-day 05:30 Transit
Kundali. Calendar Preview calculates the selected month and provides previous /
next month, Print / Save PDF, Zoom +, Zoom − and Close. These additions use a
separate API and do not write native birth fields or replace the original Transit
Panchang calculation.

South Indian charts have a separate colourful SGL/STL/SBL size control that also
follows the general chart font settings. Double-clicking a displayed chart or
table opens one read-only large viewer with zoom and Close. Home adds compact
birth-time rectification steps of ±15 seconds, ±1 minute, ±15 minutes and ±1 hour,
with Reset; calculations run only after an explicit step.

Astrologer Settings adds Uploaded KP (the unchanged default) and an opt-in Swiss
Ephemeris Krishnamurti ayanamsha reference. Loading the adapter in default mode
has exact delegation for all nine planets, all twelve cusps, sidereal time and
Vimshottari periods. Uranus, Neptune and Pluto are optional display-only values
and are excluded from traditional nine-graha KP significator logic.

About identifies Shri. Nitin R Talegaonkar — B.Sc-Maths/MCA and KP Advisor
Mr. Anil Deshmukh — KP astrologer. A local portrait chooser compresses and stores
one portrait offline. The duplicate standalone Dasha Fal navigation icon and tab
are removed; its current MD/AD/PD engine remains available through Prediction
and report composition.

## Ishtbhav displayed minutes and TC period labels · 1.2.1 · 12 October 2026

Only the readonly Ishtbhav Farak (min) column now shows whole minutes:
fractions below .50 stay at the lower minute, and .50 or above round up.
For example, 14.604006 → 15, 22.75949 → 23 and 11.379745 → 11.
Full-precision interpolation, raw Ishtbhav values, sidereal time, ayanamsha,
planet positions and final cusps are unchanged. All three installer versions
are 1.2.1; activation behaviour and existing licence compatibility are retained.

TC MD / AD / PD period labels and PD lord labels are dark navy on screen
and in the print report, including the highlighted current PD row.

Transit Panchang uses a compact blue/white card, tighter controls and summary
cards. Location filters and GeoNames attribution remain under an arrow; place
search results stay visible outside it. Original calculations and preview are retained.

## Unified 1.2.0 release and simpler activation · 12 October 2026

All three Windows installers share version 1.2.0. Customer Save System ID file
includes its System ID and accepted public Key IDs. Owner Activation can import
that text file to fill the ID automatically, rejects unapproved signing keys before
issuing a licence, and confirms a compatible key in green. New-key creation is
under a small arrow; Open owner key is the main action. Existing signed licences,
expiry rules and offline System ID binding are retained. Importing a valid licence
opens the customer calculator automatically.

## Native worksheets, visible TC labels and selectable transit searches · 12 October 2026

TC Transit Chart planet labels are dark navy and cusp/sign labels dark maroon
in North/South Indian Rashi and Bhav charts, on screen and in reports. Pale
custom planet palettes cannot hide these labels; values and font sizes are retained.

Find event transit dates adds a compact Select dates / DBA drawer. MD, AD and PD
choices come from the native timeline and update dependent choices. Current DBA,
DBA at the selected start date, or an explicitly selected DBA can be used. Custom
start/end dates and times use the selected display timezone, with exclusive end
times. Event dates under a selected DBA are restricted to that actual PD window.
All / I–XII cusp selection filters related events and selects that natal CSL chain.
All shows all 453 handbook events and 1,612 prediction records;
source conditions requiring review remain visible and cannot produce invented dates.
Choices and date ranges survive .lkp saving and import.

Owner calculator, Customer calculator and Owner Activation tool use version 1.2.0.
The calculators apply the latest explicit
latitude examples: 10°29′ → 10°; 10°30′ and 10°47′ → 11°. The original native
latitude is retained. A selected northern sheet above 60° uses the existing
physical-latitude Placidus fallback. Uploaded XLSX data and printed source units
are unchanged: X/XI/XII/II/III whole degrees; Ascendant degrees and minutes.

Automatic ST now uses one shared full-precision sidereal rotation, applying the
native UTC instant and longitude once. The worksheet and Bhavsadhan agree;
subtotal hours no longer wrap before the displayed 24-hour adjustment. Manual ST
retains the legacy 10/6 method. The uploaded ephemeris ST +1-second adjustment
is retained. For 20 December 1950, 05:02 IST, ST is 10:30:46 at 76°42′ E and
11:20:38 at 89°10′ E. The differing longitude changes ST by 49 minutes 52 seconds.

Automatic planetary dates always follow the requested 05:30 boundary: previous
date/birth date before 05:30, birth date/next date from 05:30 onward. Birth-date
05:30 positions receive a signed daily-motion correction; pre-dawn corrections
are negative. Wrap-around and retrograde motion retain signed interpolation.
Automatic mode repairs stale dates; obsolete loaders cannot replace manual rows.

ADM adds Save manual entries, visible only with a manual source selected. Saving
creates a .lkp chart with explicit manual overrides bound to those native inputs.
They survive locking ADM, recalculation and reopening the saved chart. With ADM
locked, changed birth inputs use automatic calculations instead. Cancelling or failing Save
restores the prior saved override; PINs are excluded from chart files.

Customer licensing keeps both approved owner public keys and existing license
compatibility. Owner Activation 1.1.1 retains Remove/Restore, Help, Text exports
and signed Activate/Deactivate controls. No owner private key or client identity
is included in these installers. Builds are inspected on Linux; installation
and execution on native Windows still require a Windows computer.

## Owner Activation history and Help · 12 October 2026

Owner Activation tool 1.1.1 adds Remove beside each issued license, available even
when the signing key is locked or differs from the row's issuing key. Removal
archives that exact license ID locally and keeps the customer license unchanged.
Removed entries has Restore; original metadata and status revisions survive
restart and restoration. Active and removed lists include Show more.

Help opens in the same window in English or Marathi, covering initial activation,
correct owner keys, offline status-file delivery, expiry and troubleshooting.
Save help as Text exports those instructions. Save list as Text exports all
retained entries, including later pages, with client/System ID, license/owner
Key IDs, UTC dates, issued status and revision. Removed entries are excluded.
UTF-8 text exports contain no private keys, passwords or signed license payloads.

History updates use atomic file replacement; malformed existing history is
reported instead of silently overwritten. Existing issued-history arrays,
application identity, key files and signed license/control formats are retained.
The Customer edition remains 1.1.5 and the full unlocked Owner calculator remains
1.0.3. Existing Activate/Deactivate actions still require the original issuing key
and client import of a signed .kpcontrol file.

## Verified owner-key compatibility · 12 October 2026

Customer 1.1.5 accepts licenses signed by the newly supplied and verified owner
public key D5909EAD14FB2D4717E98A8C. The previously packaged original owner key
FFD543E7AFCE69618D61325E remains accepted for existing licenses. The supplied
license's signature and System ID were valid; Customer 1.1.4 rejected it because
it contained only the original owner's public key.

Approved public keys are explicitly bundled at build time. Keys inside license
files, renderer input and user-data files never become trusted. Each license
still requires a valid signature, matching native System ID, valid dates and
unexpired term. Activate/Deactivate controls must come from the same approved
key that issued the installed license and target that exact license. Existing
signed license/control formats and application-data identity are retained.
The activation screen shows accepted owner Key IDs in English/Marathi.

The Owner Activation tool remains 1.1.0, and the full unlocked Owner calculator
remains 1.0.3. Mathematical calculations, Raphael tables, the latitude-minute
rule, KP ayanamsha, System ID reader and report layouts are unchanged. No private
owner key, customer license or client identity override is included in the build.

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
## Owner-approved 50-second Ishta Farak rule · 13 October 2026

The explicit examples define a 50-arcsecond threshold, rather than ordinary
half-minute rounding: 45′19″ → 45′, 43′49″ → 43′, 45′50″ → 46′,
45′59″ → 46′. Automatic Raphael and manual worksheet calculations use the
same rule before adding Ishta Farak to the smaller cusp and subtracting KP
ayanamsha. Both DMS and minute worksheets show that applied difference. The
13° N / ST 14:13:47 reference gives 45′ for houses X, XI, XII, II, III and
43′ for the Ascendant. The source Excel values, ST, latitude selection,
planetary ephemeris and Vimshottari formulas are unchanged. This intentionally
supersedes the earlier display-only Ishta rounding notes.
