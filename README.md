# KP Master astrology workspace

A self-contained Krishnamurti Paddhati calculator with Marathi worksheets, South and North Indian kundalis, Traditional and KP matchmaking, and client PDF reports.

## Run locally

Extract the downloaded ZIP and open `index.html` in Chromium, Chrome or Edge. The standalone HTML includes its calculations, styling, data and offline India place search. Alternatively, from this directory:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/index.html`. The cloud workspace includes Python, Chromium and Python Playwright; no build step is required.

## Kundali and significators

Enter native birth details and place, then calculate the chart. Automatic KP ephemeris and Placidus cusps are available; the standalone developer worksheets also retain manual Raphael inputs. An original Raphael book has not been embedded. The uploaded annual KP ayanamsha table is interpolated at each calculation date, with anchors from January 1, 1861 to January 1, 2147. Automatic planetary calculations support 1900–2100.

Home shows the kundali, native details, planetary/cuspal positions and five-level Vimshottari timeline. Basic, four-fold, six-fold, four-step and Nadi significator views remain available. The South Indian Kundali window shows the detailed planetary and cuspal calculation tables in the Home style, with Basic, Four-fold, Six-fold, Four-step and Nadi buttons. It retains occupancy, ownership, all lord layers, received/given aspects and conjunction evidence. Auto Fill, Automatic calculation mode, Manual Edit and Time-slice comparison controls are removed from this window.

Four-step Theory follows planet → star lord → sub lord → sub lord’s star lord. Planet/sub levels remain Nil when their stars contain another planet, unless the planet is in its own star; star levels remain active. Direct ownership contributes empty houses. **Incoming whole-sign aspects now add the aspecting planet’s occupied and empty owned houses**, once, without recursive aspect inheritance. The original houses and `Aspd: [planet: houses]` evidence appear separately, while their union is used by four-step analyses. Aspects use the existing whole-sign rules: seventh for classical planets, Mars 4/7/8, Jupiter and Rahu 5/7/9, Saturn 3/7/10; Ketu follows the existing preference. These are separate from the Western longitude/orb matrix.

Home Nadi cards use white surfaces, dark planet labels and plain house numbers. Restrained green/amber/red text preserves house categories; underlining marks the selected event houses. Notepad typing, font selection, size and colour changes stay local to the notes and do not redraw or resize the kundali.

## Predictions and remedies

Prediction contains seven tabs: Kundali Analysis, House Results, General Predictions, Events, Dasha Results, Remedies and Gemstone Guidance. The duplicate Short Dasha tab is removed. Each shows only supported matches for the calculated native chart. All References, raw source browsing and reference-selection controls are removed. Incomplete charts show a reason instead of common predictions.

House Results requires every house in an unambiguous encoded source group to match the native cusp-significator evidence. General Predictions uses explicit planet sign/house and Moon nakshatra/pada placements. Kundali Analysis displays matched eligible supplied groups. Events defaults to the current native MD / AD / PD: every period lord must contribute to the matched event house group, and their union must cover it completely, in addition to the native cusp promise. **DBA selection** opens compact, dependent MD, AD and PD selectors; **Current DBA** restores automatic selection. Screen and preview retain the chosen chain and its exact native local PD interval. Conditional or ambiguous rules are not silently converted into predictions. House Results has a small I–XII cusp selector: screen and preview contain only that cusp’s matched results. Kundali Analysis keeps cusp/search controls visible, with calculation options under a closed arrow; its preview contains only the matched prediction text, without calculation or source columns.

Dasha Fal automatically uses the **currently running native MD / AD / PD**, the native UTC offset and exclusive period end boundaries. It shows only matching supplied short-result wording, with optional evidence. Dasha Results also uses the current period lords. Remedies selects the birth Moon nakshatra and the current MD–AD remedy line, rather than all remedy entries.

The seven original uploaded text files remain byte-for-byte in `data/` as source material. The standalone matching engine embeds only supported computable rules; it does not expose a general source library. Events.txt supplies names, not invented house criteria.

Gemstone Guidance stays under Prediction → Gemstone rule. Its consultation card uses a compact rule/preview row and tighter recommendation table; the GEM toolbar/sidebar entry is replaced by MUH. Gemstones has Rule and Purpose controls. **Vedic** selects whole-sign Lagnesh (1), Panchamesh (5) and Labhesh (11), merges duplicate owners and prioritizes them in that order. All these owners are shown, including retrograde/combust markers. **KP** scores unique purpose-house coverage using planet, star lord and sub lord; retrograde and combust candidates are excluded. Money/business uses 2,6,10,11; childbirth uses 2,5,11. Highest-scoring KP ties share priority. Zero eligible coverage gives no recommendation. The fitted single-page A4 report includes recommendations, original Ratna guidance, nine Navagraha verses and फलश्रुती.

## Simple analysis windows

Dasha Promise uses the requested centered MD/Bhukti selectors, exact local selected period and five white significator fields on a peach panel. It initially selects the active MD/AD and permits any subsequent selection. Supporting Antaras and Sun/Jupiter/Saturn searches remain. A small **Use RP for PD** toggle filters event-supporting Antaras by the current five KP Ruling Planet sources (Ascendant sign/star, Moon sign/star and day lord). The PD selector highlights a candidate; toggling RP preserves the MD/AD and transit results. Preview retains the captured RP location/time and selected PD. An unavailable RP calculation produces no filtered candidates, without changing the event verdict. Dasha-entry details explicitly retain the existing Moon-star-at-MD-start convention (birth for the partial MD); the user’s exact replacement rule is still pending.

Event Promise uses a compact two-column consultation card with favorable/neutral/opposed house colors, cusp selection and Auto/Manual house input. The selected native CSL/star/sub chain and combined houses appear beside event category, event and direct verdict/reason. Continuing chain options and native occupancy/aspect evidence are collapsed; that evidence is informational and does not silently change the source event criteria. Conditional rules remain flagged for review. Preview opens a single A4 report of the selected analysis.

Transits offers three searches: Event significators; mutual MD/AD/PD transits (six role directions × Rashi/star/sub); and both Sun MD/AD sign-star combinations. Current native DBA appears in a compact row, with MD/AD/PD scope selection and advanced rules under one arrow. Event mode defaults to all nine planets with star AND sub among event significators, intersected with supporting natal DBA windows. Mutual and Sun modes use natal target sectors by default and do not apply an unrelated event gate; ruled target sectors remain available in details. Current child periods are clipped to their parent/birth interval without changing subdivision anchors. Entries/exits are refined to one second and remain astrology-based matching windows.

Transit Panchang retains Now, Calculate and Preview. Ephemeris retains Generate and Preview, with Cancel during calculation; daily clock/offset options are collapsed. Western Aspects uses the supplied fixed angle/orb catalogue; on-screen aspect/orb/colour editors are removed. Planet-to-planet and planet-to-cusp matrices and their previews remain.

The old Ruling Planets tab and its legacy calculation APIs remain removed. A rebuilt **RP · Live** calculator now runs inside the workspace header between the left navigation and right action buttons on every tab. It updates every second from the saved consultation place and UTC offset, showing Ascendant and Moon sign/star/sub/sub-sub lords, traditional ruling planets, day and planetary-hour lords, with retrograde markers. Expand RP for positions, sunrise/sunset and hour boundaries; **Location settings** opens the existing consultation-place settings. Day changes at local sunrise, with day/night each divided into 12 unequal planetary hours. Polar locations without a complete sunrise/sunset cycle show an explicit unavailable reason for day/hour lords. The private interface polls a computation-only `/live-ruling-planets` endpoint without replacing the current chart. The obsolete `/ruling-clock` route remains removed.

## Muhurta

**MUH** provides 28 common purposes and two visible methods. **Vedic · Parashari** is the default, combining purpose-specific Panchang profiles with a conservative Parashari whole-sign Lagna screen. The Lagna lord and Moon must be outside 6/8/12, the Lagna lord must be uncombust, and an uncombust benefic must occupy a Kendra or Trikona. Mercury/Venus combustion limits distinguish direct/retrograde motion. Birth Tarabala and Chandrabala are required when a real natal chart is loaded. Searches retain daylight and exclude actual Rahu Kalam, Yamaganda, Gulika, Vishti and adverse yogas. Panchang, Moon and Lagna-screen state crossings are refined to one second and rounded inward.

**KP · Native Kundali** requires a real birth chart. Choose a purpose's mapped event or a supplied eligible event from the small KP event selector. It searches all 24 local hours and retains only complete natal cusp promise, supporting MD/AD/PD coverage by every lord, and transit Moon star **AND** sub among event significators. Conditional or unsupported results are excluded. A missing chart or event criterion gives an explicit reason. The native chart is not changed by either search.

Preview prints every window using the selected method, with Print / Save PDF, Zoom +/− and Close. Locations, UTC offset and applied rules stay in the closed **Place and rules** drawer. This is common-purpose screening: ceremony-specific months, ritual exceptions and family/regional conventions still require review. Refined astronomical boundaries do not guarantee real-world event dates.


## DBA/MAP and matchmaking

DBA navigation opens the popup directly and leaves the workspace tab in place. MD/AD worksheet details are behind a closed arrow; the popup exposes only computed birth-period facts. “Print current DBA/MAP” recalculates the running chain at the native local clock and prints the current MD, current AD and all Antaras in that AD with native significators. It preserves the manually selected period, view and screen zoom. The existing complete timeline and Overview print buttons remain available. Calculation details are excluded from DBA popup reports.

The former MD & AD tab is **DBA/MAP**. Its popup shows the complete native Mahadasha, Bhukti and Antara timeline in grouped tables. Every period includes the planet, star lord, sub lord and sub’s star lord, with each lord’s occupied and owned houses from the native kundali. Dasha/Bhukti buttons and clickable period names jump to a selection without hiding other periods; **Current DBA** selects the running chain. **Print all MD / AD / PD · Save PDF** prints every displayed period with repeated table headers on A4 landscape pages. **Overview** adds a three-column Dasha/Bhukti overview and expandable sidebar within the same popup, with the selected Bhukti’s Antaras below. **Significators** returns to the complete detailed timeline without losing the selection. Print follows the selected view. Zoom +/− and Close remain available. Exact local times, the native calendar convention, birth-balance clipping and exclusive end dates are preserved.

Matchmaking keeps **Traditional**, **KP** and **Both**. Traditional shows the total out of 36, percentage and Mangal screening, with technical details collapsed; its compact Marathi A4 report includes both kundalis and all eight koota scores. KP retains the six requested categories and shared marriage periods for both native DBA chains. The saved-chart Open/Delete control is removed; stored pairs are preserved. Birth records and result panels use compact styling; category house evidence is inside the common settings arrow. Birth coordinates/DST remain collapsed beside each record. **Matchmaking settings and details** is one closed arrow dropdown containing KP subtotal/adjustment evidence, scoring rules, joint marriage-period search, Mangal settings and scoring conventions. The main selected compatibility result stays visible. Joint search defaults to 13 years; every MD/AD/PD must contribute and jointly cover houses 2,7,11 for each person. Optional Moon refinement restricts existing overlapping periods. Empty results show each person’s supporting periods and reasons; no marriage dates are fabricated.

Significators uses a compact method/event toolbar with explanations and conjunction options under **Details**. Planet and house tables appear side by side on wide screens; Nadi and four-step cards use tighter spacing. Home chart and notepad fonts remain separate.

Education & Profession offers only **4th house · Basic education**, **9th house · Higher education**, and **10th house · Profession**. Screen and preview show the selected native cusp’s analysis; profession associations appear only for the 10th house. Workbook filenames, sheet names and row labels are omitted from education, profession and disease output.

## Notes, teaching and reports

TUT toggles drawing tools over any active tab: pointer, pen, highlighter, line, arrow, rectangle, ellipse, text, eraser, colour, size, undo/redo/clear and zoom/fit. Use Pointer to operate the software. Annotations stay separate for each tab and are omitted from reports.

Notepad supports font, size, colour and preview/print/PDF with zoom and close. KP Astrology Resources supports topic/subtopic edit/delete, note edit/delete, preview and UTF-8 text-file saving on the PC. Browser notes persist locally; download text files for portable copies. Name/place fields capitalize initial letters.

Preview windows provide Print / Save PDF, Zoom +, Zoom − and Close. Printing resets screen zoom. Nadi, selected significators, Event Promise, gemstones and Traditional matchmaking have fitted A4 layouts; longer result reports flow across pages. All CSV export buttons are removed. Dark theme uses contrasting surfaces and text; printed reports retain dark text on white paper. Popup permission may be needed in the browser.

Developer photo controls are not exposed to customers. The original portrait JPG and logo PNG attachments are still required to embed those supplied pictures; inline chat images have no downloadable file reference in this workspace.

## Private calculation server

```sh
python3 protected/server.py --port 8080
```

Python Playwright and Chromium are required; `CALCULATOR_CHROMIUM` overrides the executable. The server binds to loopback. Customer responses contain a script-free interface snapshot and interface code; original calculations run in a private Chromium worker. Hidden calculation controls and source files are rejected. Deploy behind authenticated HTTPS and keep the repository private if calculation-source confidentiality is required. The standalone developer HTML already contains calculation code.

Four isolated sessions are supported, expiring after 30 minutes without requests. Save/Load uses `.lkp` files; session storage is not a database. Imported chart user data is recalculated automatically in the worker. Restart the server after calculation-code changes.

## Verification

```sh
python3 -m unittest discover -s tests -p test_personal_predictions.py -v
PYTHONPATH=tests python3 -m unittest test_tutorial -v
PYTHONPATH=tests python3 -m unittest test_live_workspace -v
```

Focused checks cover personal-only predictions, ambiguous house-group rejection, current DBA boundaries, Vedic ownership, actual one-page PDFs, simple windows, Notepad/chart isolation, incoming aspect contributions, complete DBA table printing, Traditional/KP marriage intersections and private previews. The older full calculator suite contains fixtures for intentionally removed controls and is not claimed to pass without migration.

## India gazetteer provenance

Location data © [GeoNames](https://www.geonames.org/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The embedded populated-place subset comes from [Dibakar01/reverse-geocoding](https://github.com/Dibakar01/reverse-geocoding), pinned to commit `d80fb96ad43f3a9216dbd0cf2b9cdd38ffffd78d`; the mirror documents extraction from the official `IN.zip`. It retains source coordinates and administrative codes but supplies ASCII names without the original GeoNames aliases/IDs. The software adds a few disclosed search spelling variants, state/district labels, source-code fallbacks, and a compressed offline lookup. All 557,995 source records are retained, including 8,969 abandoned and two historical settlements. There are 37 records with unknown/obsolete state codes, 2,572 without a district code and 212 with unmapped district codes; those are not assigned a guessed district. The dataset loads only when lookup is first used. Metadata, source hashes, licensing and coverage are available in the picker.

Embedded India TSV SHA-256: `1bea1d79cd3fce326a2c1c7e2ac6af91c7311db712c96573ede8e05eeb2c0158`; source mirror TSV SHA-256: `2f16f9c4e94784d79b7a3db6392325b86cbc9a6c278ec543466465d21fd58949`. The mirror archive timestamp is August 28, 2026; the original GeoNames extraction date is unspecified.

Dasha Promise initially selects the running native MD and AD. Both dropdowns remain editable in Auto mode; Calculate preserves the chosen period. Its compact cards distinguish matched house criteria, missing criteria and additional conditions requiring review. Sun transit matching uses MD natal sign + AD natal nakshatra, or AD natal sign + MD natal nakshatra, and searches only inside the selected AD. Existing Moon-star-at-MD-start evidence is retained pending the astrologer’s exact Dasha-entry rule.

Marathi/English display switching now covers additional chart terminology, compact planet/sign codes, DBA headings and preview controls; Marathi buttons include English. Imported long English prediction paragraphs still require a reviewed Marathi text pack. This release does not claim fully translated prediction prose or guaranteed real-life event dates.

Disease screen and report omit the explanatory medical/source note, workbook filename and source row labels; native star/quarter matches and significator evidence are retained.

Education & Profession has a compact inline selector and two-column result cards on wide screens. Its A4 print layout uses dedicated page margins, fixed-width wrapping tables, repeated table headers and intact short prediction blocks; screen zoom does not change the print scale.

## Vedic reports, HIT and hover details

The small **VED** icon opens Vedic Kundali with native Rashi and sixteen Parashari divisions, strength tables, Ashtakavarga, solar-return and Saturn phase views. Print Report has grouped checkboxes, minimum page counts, Select all, Print, Preview, Export to PDF and Close. It includes Shadbala/Bhava Bala, Vimshopaka/Vaisheshikamsa, Bhinna/Sarva/Prastara Ashtakavarga, reductions/pindas, Sarvatobhadra chakra, relationships, full and current subperiod tables, native matched predictions/remedies, Manglik, Sade Sati and Varshaphal. Solar-return and Saturn reports prepare automatically when selected for preview. Detailed conventions and supported scope are in [vendor/vedic/README.md](vendor/vedic/README.md). In the standalone browser Export to PDF opens its print/save-PDF dialog; the private server downloads a generated PDF.

The small **HIT** icon uses the uploaded four-page HIT Theory PDF: all three native hit types, its exact six angle/orb rules, current native MD/AD/PD and their stars, direction-based symbolic remedies, deity/avatar and movable-item correspondences. Native planet/cusp values and the KP matrix remain unchanged. [vendor/hit/README.md](vendor/hit/README.md) records interpretation boundaries.

Hover on chart details or truncated table text reveals a small faint popup after the pointer pauses. Moving the pointer, leaving the data, clicking or scrolling hides it. It reads displayed text and existing full-text annotations without resizing the kundali or revealing private calculation code.

New focused verification:

```sh
PYTHONPATH=tests python3 -m unittest test_vedic_reports test_hit_theory -v
PYTHONPATH=tests python3 -m unittest test_muhurta.MuhurtaTests.test_vedic_lagna_and_kp_native_methods_filter_actual_intervals -v
```
