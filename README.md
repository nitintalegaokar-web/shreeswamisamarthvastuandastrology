# KP Raphael astrology workspace

A browser-based Krishnamurti Paddhati calculator with Marathi worksheets, South Indian kundali, and printable client reports. It runs locally without an application server, build step, or external assets.

`index.html` is self-contained: its styling and JavaScript are embedded, so no companion files are needed. Open the HTML file in your browser, or start the development server from this directory:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

The cloud environment already includes Python, Chromium, and Python Playwright. Each cloud task is isolated; use the existing checkout unless a separate worktree is explicitly requested.

## Using the calculator

- **Home** opens with the South Indian kundali, planet and house tables, birth and current ruling planets, MD/AD periods, and native details together. Switch the center tables between basic calculations, four-fold, six-fold and four-step views. **Expand workspace** gives the dashboard more room on desktop; compact screens stack the panels and allow table scrolling. Home reflects the current worksheet data and saved chart.
- The ruling-planet tables show Ascendant, Moon, Rahu and Ketu with sign, star, sub and sub-sub lords. Use each table's pencil to edit its date, time, location and UTC offset, with optional sidereal longitude overrides. When following the current clock, the table refreshes every minute while Home is open; its refresh button updates to the present time and clears longitude overrides. Reset returns to native birth data or the current clock. Hour and day lords follow local sunrise and sunset; unavailable sunrise is indicated. Retrograde lords appear in red. RP aspect columns use Western major aspects with a 3° orb, with the Ascendant representing cusp aspects in ephemeris tables.
- Enter the birth details, then complete the Raphael houses and dated ephemeris worksheets. The included ephemeris sample covers 9–11 October 1931; enter your own dated rows for other births.
- **Tab 6 — Planet positions** calculates the hours and minutes automatically from daily angular motion and the birth-time difference from 05:30. The dated rows determine the motion's direction; births before 05:30 receive a signed correction. The correction components are angular degrees/minutes/seconds, not clock durations.
- Enter the seven classical planets and Rahu. Ketu has no independent calculation column: it is derived exactly 180° (six signs) opposite Rahu with identical degrees, minutes and seconds within its sign.
- Use the sidebar to move between Home, the worksheets, Western Aspects, Transit and Report. Dense worksheets and the kundali scroll sideways on small screens.
- **Calculate** refreshes the worksheet results and chart. The overview shows local mean time, ayanamsha, and longitude difference.
- **Tab 7 — MD & AD** calculates Mahadasha and Antardasha together. Choose a Mahadasha to view its nine Antardashas in the same planet, years, months, days, start-date and end-date format. The birth Antardasha is marked with its remaining balance; the full birth Mahadasha includes periods before birth. Durations follow the worksheet's 12-month year and 30-day month convention.
- **Tab 8 — Significators** shows four-fold and six-fold planet/house tables and four-step theory cards. Changes to completed worksheets refresh them automatically; incomplete or unordered cusp data clears the results. The column definitions appear beside each display.
- Each South Indian kundali cell places cusp numbers and degrees on the left, and planet names and degrees on the right. Crowded entries are spaced independently in each column, including in printed reports.
- Basic planet and house tables appear below the kundali, including nakshatra/pada, occupancy, ownership, sign/star/sub/sub-sub lords, cusp lords, aspects and cusp conjunctions. Aspects use Vedic sign rules; the default 3° cusp-conjunction range is editable in Tab 8. The software displays the nine traditional grahas.
- **Western Aspects** separately calculates planet-to-planet and planet-to-cusp aspects from the natal worksheet longitudes. Major aspects are selected initially; optional minor aspects and individual orbs are editable. Each result shows the aspect, shortest zodiac separation and actual orb. Planet pairs appear once.
- **Transit** searches a selected date range and returns entry/exit date-times in India time or UTC. Event mode selects significators automatically from the relevant houses using four-fold, six-fold or four-step calculations. Event house presets are editable; choose transiting planets and whether their star/sub lords must match together or separately.
- Mutual transit mode uses MD, AD and PD lords from the calculated timeline at a reference date, or manually selected lords. Choose a direction and Rashi, Nakshatra or Sub level. Sun mode checks both simultaneous combinations: MD Rashi with AD Nakshatra, and MD Nakshatra with AD Rashi. Targets can be sectors ruled by the lord or sectors occupied by the target natal planet; the selected lords stay fixed throughout the search. Results include retrograde reentries and mark intervals clipped by the requested range.
- **Save chart** stores the editable worksheet data and manual kundali notes in the current browser. **Load** restores the saved chart and recalculates outputs.
- The toolbar's backup menu exports/imports **`.lkp` chart files**, including worksheets, aspect/transit settings, ruling-planet overrides, manual notes and the cover photo. These files contain the calculator's JSON backup format; earlier `.json` backups can still be imported. Imported charts must be saved separately to persist in the browser.
- **Manual Edit** allows plain-text notes in the kundali. They stay in place until **Auto Fill Kundali** returns to calculated chart values.
- **Print report** opens the report controls. Select individual pages or use **Select all**, then click **Print selected pages** to print or save a PDF. The complete report has thirteen A4 pages, with MD and AD on separate pages. Its front page includes Ucchishta Mahaganpati, the native's name, birth details and birthplace, and the astrologer's name, phone and address. The remaining pages include each significator method and the basic calculation tables directly below the kundali. Allow the report window if your browser blocks popups.
- In **Report**, use **Choose cover photo** to select the original JPG, PNG or WebP from your device. The full image appears on the front page without cropping. It is saved in this browser and included in `.lkp` chart backups; use **Export chart** to move the chart and photo to another device.
- Set the astrologer's name, contact number, and address in **Astrologer settings**.

Keyboard shortcuts: **Ctrl/⌘ + S** to save, **Ctrl/⌘ + Enter** to calculate, **?** for help, and **Escape** to close mobile navigation or help.

## Transit and current-position calculations

The HTML embeds [Astronomy Engine 2.1.19](https://github.com/cosinekitty/astronomy/tree/v2.1.19), including its MIT license, for offline geocentric planetary positions and sunrise/sunset. The embedded minified source has SHA-256 `f41139a87941ea017ab902b954c9389fa27ea72083d7fab4971756d7769d14e6`.

Sidereal longitudes use the worksheet's birth ayanamsha, advanced by 50.29 arcseconds per year. Rahu uses the mean lunar-node polynomial, and Ketu stays 180° opposite. Searches cover 1900–2100 with a maximum ten-year range. Crossings are numerically refined to one second; that refinement is distinct from the underlying astronomical and ayanamsha model accuracy. Automatic AD/PD boundaries retain the existing worksheet's 360-day duration and calendar-offset convention. Event results are matching transit intervals for the displayed criteria.

## Browser regression checks

With Python Playwright and Chromium installed:

```sh
python3 -m unittest discover -s tests -v
```

The suite starts and stops its own temporary local servers. It checks calculations, MD/AD balances and date boundaries across time zones, automatic significators, crowded kundali cells on desktop/mobile/print, full worksheet persistence, `.lkp` and legacy backups, Home synchronization, editable ruling planets, Western aspect geometry, independent planetary/Ascendant reference fixtures, transit boundaries and retrograde reentries, manual chart editing, mobile navigation, invalid data, selected report pages, and a standalone copy containing only `index.html`.
