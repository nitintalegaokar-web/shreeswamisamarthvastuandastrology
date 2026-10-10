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

Prediction contains eight tabs: Kundali Analysis, House Results, General Predictions, Events, Short Dasha, Dasha Results, Remedies and Gemstone Guidance. Each shows only supported matches for the calculated native chart. All References, raw source browsing and reference-selection controls are removed. Incomplete charts show a reason instead of common predictions.

House Results requires every house in an unambiguous encoded source group to match the native cusp-significator evidence. General Predictions uses explicit planet sign/house and Moon nakshatra/pada placements. Events and Kundali Analysis display matched eligible supplied groups. Conditional or ambiguous rules are not silently converted into predictions. Reports respect the selected main cusp; the separate cusp-chain preview prints that cusp’s chain.

Dasha Fal automatically uses the **currently running native MD / AD / PD**, the native UTC offset and exclusive period end boundaries. It shows only matching supplied short-result wording, with optional evidence. Short/Detailed Dasha prediction tabs also use the current period lords. Remedies selects the birth Moon nakshatra and the current MD–AD remedy line, rather than all remedy entries.

The seven original uploaded text files remain byte-for-byte in `data/` as source material. The standalone matching engine embeds only supported computable rules; it does not expose a general source library. Events.txt supplies names, not invented house criteria.

Gemstones has Rule and Purpose controls. **Vedic** selects whole-sign Lagnesh (1), Panchamesh (5) and Labhesh (11), merges duplicate owners and prioritizes them in that order. All these owners are shown, including retrograde/combust markers. **KP** scores unique purpose-house coverage using planet, star lord and sub lord; retrograde and combust candidates are excluded. Money/business uses 2,6,10,11; childbirth uses 2,5,11. Highest-scoring KP ties share priority. Zero eligible coverage gives no recommendation. The fitted single-page A4 report includes recommendations, original Ratna guidance, nine Navagraha verses and फलश्रुती.

## Simple analysis windows

Event Promise has one event dropdown. Changing it immediately displays whether the native CSL chain promises the event and explains matched/missing houses. Rules with additional conditions remain explicitly flagged for review. Preview opens a simple A4 report.

Transits offers an event and the current MD, AD or PD period. Find dates searches Moon, Sun, Jupiter and Saturn star/sub transits inside supporting native DBA periods, using the event’s natal promise and timing houses. Returned entry/exit boundaries are refined to one second; they are astrology-based matching windows, not guaranteed real-life event dates. Missing natal promise or supporting periods is explained rather than fabricated.

Transit Panchang retains Now, Calculate and Preview. Ephemeris retains Generate and Preview, with Cancel during calculation; daily clock/offset options are collapsed. Western Aspects uses the supplied fixed angle/orb catalogue; on-screen aspect/orb/colour editors are removed. Planet-to-planet and planet-to-cusp matrices and their previews remain.

The old Ruling Planets tab and its legacy calculation APIs remain removed. A rebuilt **RP · Live** calculator now runs inside the workspace header between the left navigation and right action buttons on every tab. It updates every second from the saved consultation place and UTC offset, showing Ascendant and Moon sign/star/sub/sub-sub lords, traditional ruling planets, day and planetary-hour lords, with retrograde markers. Expand RP for positions, sunrise/sunset and hour boundaries; **Location settings** opens the existing consultation-place settings. Day changes at local sunrise, with day/night each divided into 12 unequal planetary hours. Polar locations without a complete sunrise/sunset cycle show an explicit unavailable reason for day/hour lords. The private interface polls a computation-only `/live-ruling-planets` endpoint without replacing the current chart. The obsolete `/ruling-clock` route remains removed.

## DBA/MAP and matchmaking

The former MD & AD tab is **DBA/MAP**. Its popup shows the complete native Mahadasha, Bhukti and Antara timeline in grouped tables. Every period includes the planet, star lord, sub lord and sub’s star lord, with each lord’s occupied and owned houses from the native kundali. Dasha/Bhukti buttons and clickable period names jump to a selection without hiding other periods; **Current DBA** selects the running chain. **Print all MD / AD / PD · Save PDF** prints every displayed period with repeated table headers on A4 landscape pages. **Overview** adds a three-column Dasha/Bhukti overview and expandable sidebar within the same popup, with the selected Bhukti’s Antaras below. **Significators** returns to the complete detailed timeline without losing the selection. Print follows the selected view. Zoom +/− and Close remain available. Exact local times, the native calendar convention, birth-balance clipping and exclusive end dates are preserved.

Matchmaking keeps **Traditional**, **KP** and **Both**. Traditional shows the total out of 36, percentage and Mangal screening, with technical details collapsed; its compact Marathi A4 report includes both kundalis and all eight koota scores. KP retains the six requested categories and shared marriage periods for both native DBA chains. Birth coordinates/DST, Mangal options and marriage-search options are collapsed. Joint search defaults to 13 years; every MD/AD/PD must contribute and jointly cover houses 2,7,11 for each person. Optional Moon refinement restricts existing overlapping periods. Empty results show each person’s supporting periods and reasons; no marriage dates are fabricated.

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
