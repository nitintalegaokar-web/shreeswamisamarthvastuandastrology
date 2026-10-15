# KP Raphael — automatic edition of your uploaded software

Unzip the download and open **index.html** in Chrome, Edge, or Firefox. No installation, Internet connection, or companion files are needed for calculations.

1. Open **Birth details**.
2. Enter the birth date, local time, birthplace, latitude and longitude in D:M:S.
3. Enter the UTC offset (**India: +5.5**) and DST/war-time correction in minutes (**normally 0**).
4. The house cusps, planetary positions, kundali, dasha and significators update automatically. **Calculate** also refreshes everything.

Your uploaded screen layouts, Marathi worksheets, chart styles, settings, `.lkp` backups and print/report controls are retained. The new time-zone and DST fields appear beside the birth details. Generated worksheet values are read-only; no Raphael rows or daily planetary positions need to be entered.

## Calculation conventions

- Supported birth years: **1900–2100**. Adjacent ephemeris references at the year boundaries are supported internally.
- Twelve sidereal **Placidus** house cusps are solved from the birth instant and geographic location. Four-minute sidereal brackets and the existing worksheet rows are populated automatically. Final cusps use the direct solution instead of rounded linear interpolation.
- These are **computed Raphael-style worksheet values**, not transcriptions from an original printed Raphael Table of Houses. No claim of comparison with a particular printed edition is made.
- Sidereal time uses the embedded Astronomy Engine. LMT uses the full longitude conversion, including arcseconds and DST, with correct date rollover.
- The previously supplied annual **KP ayanamsha table** is embedded. Its DMS column is authoritative, interpolated between January 1 UTC anchors. Differences or decreases in that original table are preserved rather than silently corrected.
- The seven classical planets are evaluated at the actual birth instant with the embedded **Astronomy Engine 2.1.19**. Rahu uses its mean-node model; Ketu is exactly 180° opposite.
- The planetary worksheet also displays consecutive **local 05:30** reference rows. Before 05:30, the first reference is on the previous date. Signed daily motion, hourly correction and remaining-minute correction are shown. The final positions are evaluated at birth, rather than assumed to move uniformly throughout the day.
- Nakshatra/pada, sign/star/sub/sub-sub lords, occupancy, significators, MD/AD and reports use the resulting natal chart. The existing 360-day/30-day symbolic dasha convention is retained.
- Invalid dates or locations clear calculated results instead of leaving an old chart visible. Placidus is unavailable in the polar circles; the program reports this rather than substituting a different house system.

Saving or importing `.lkp` files keeps the birth details, UTC offset, DST and supported preferences. Generated values are recalculated; imported worksheet overrides cannot replace automatic results.

## Verification

Seven browser regression checks cover complete startup, independent planetary/house reference fixtures, midnight/05:30 and timezone/DST boundaries, changes after delayed callbacks, invalid-input clearing, `.lkp` restoration, report metadata, and offline standalone operation. Separately, 72 house cusps at six reference date/locations were compared against Swiss Ephemeris; this is validation only, and Swiss Ephemeris is not bundled or required.

The displayed arcsecond resolution is not a guarantee that the underlying astronomical model or the supplied ayanamsha agrees with every printed ephemeris to one arcsecond. Existing reference tolerances are 0.03° for planetary astronomy and 0.001° for house comparisons, separate from the 0.5″ rounding check between computed results and displayed values.

This self-contained developer HTML includes its calculation code. Formula confidentiality requires a private calculation service; HTML distributed to a customer cannot enforce that confidentiality.

The original embedded Astronomy Engine MIT license is retained in index.html.
