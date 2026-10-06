# KP Raphael astrology workspace

A browser-based Krishnamurti Paddhati calculator with Marathi worksheets, South Indian kundali, and printable client reports. It runs locally without an application server, build step, or external assets.

`index.html` is self-contained: its styling and JavaScript are embedded, so no companion files are needed. Open the HTML file in your browser, or start the development server from this directory:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

The cloud environment already includes Python, Chromium, and Python Playwright. Each cloud task is isolated; use the existing checkout unless a separate worktree is explicitly requested.

## Using the calculator

- Enter the birth details, then complete the Raphael houses and dated ephemeris worksheets. The included ephemeris sample covers 9–11 October 1931; enter your own dated rows for other births.
- **Tab 6 — Planet positions** calculates the hours and minutes automatically from daily angular motion and the birth-time difference from 05:30. The dated rows determine the motion's direction; births before 05:30 receive a signed correction. The correction components are angular degrees/minutes/seconds, not clock durations.
- Enter the seven classical planets and Rahu. Ketu has no independent calculation column: it is derived exactly 180° (six signs) opposite Rahu with identical degrees, minutes and seconds within its sign.
- Use the sidebar to move between all eleven sections. Dense worksheets and the kundali scroll sideways on small screens.
- **Calculate** refreshes the worksheet results and chart. The overview shows local mean time, ayanamsha, and longitude difference.
- **Tab 8 — Significators** shows four-fold and six-fold planet/house tables and four-step theory cards. Changes to completed worksheets refresh them automatically; incomplete or unordered cusp data clears the results. The column definitions appear beside each display.
- Each South Indian kundali cell places cusp numbers and degrees on the left, and planet names and degrees on the right. Crowded entries are spaced independently in each column, including in printed reports.
- Basic planet and house tables appear below the kundali, including nakshatra/pada, occupancy, ownership, sign/star/sub/sub-sub lords, cusp lords, aspects and cusp conjunctions. Aspects use Vedic sign rules; the default 3° cusp-conjunction range is editable in Tab 8. The software displays the nine traditional grahas.
- **Save chart** stores the editable worksheet data and manual kundali notes in the current browser. **Load** restores the saved chart and recalculates outputs.
- The toolbar's backup menu exports/imports a JSON chart file for moving work between browsers or devices. Imported charts must be saved separately to persist in the browser.
- **Manual Edit** allows plain-text notes in the kundali. They stay in place until **Auto Fill Kundali** returns to calculated chart values.
- **Print report** opens an eleven-page A4 report in a new window, with a page for each significator method and the basic calculation tables directly below the kundali. Use the browser print dialog to print or save a PDF. Allow the report window if your browser blocks popups.
- Set the astrologer's name, contact number, and address in **Astrologer settings**.

Keyboard shortcuts: **Ctrl/⌘ + S** to save, **Ctrl/⌘ + Enter** to calculate, **?** for help, and **Escape** to close mobile navigation or help.

## Browser regression checks

With Python Playwright and Chromium installed:

```sh
python3 -m unittest discover -s tests -v
```

The suite starts and stops its own temporary local servers. It checks calculations, automatic significators, crowded kundali cells on desktop/mobile/print, full worksheet persistence, portable backups, manual chart editing, mobile navigation, invalid data, report printing, and a standalone copy containing only `index.html`. These are software checks; they do not independently certify astrological accuracy.
