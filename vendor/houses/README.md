# Uploaded Bhavsadhan house tables

The seven supplied `Swiss_Placidus_User_ST_*.xlsx` workbooks are retained unchanged in `source/`. They supply tropical Placidus cusps for 61 whole northern latitudes, 0° through 60°, and local sidereal time from 00:00:00 through 24:00:00. They are user-supplied Swiss Placidus tables, not a verified transcription of a historical Raphael book.

`import_tables.py` validates sheet names, headers, clock fields, all numeric cusp values, chronological ordering and matching 00:00/24:00 endpoints. It removes 671 identical repeated boundary rows, retaining 22,021 unique latitude/time rows. `tables.json` keeps the original numeric columns **10H 360, 11H 360, 12H 360, Asc 360, 2H 360, 3H 360**, source filenames and SHA-256 hashes. Rounded text columns are not calculation inputs. Run `python vendor/houses/import_tables.py` with openpyxl to rebuild the packed data.

The standalone HTML embeds this data and both calculation modules, so tables work offline and in the private calculation worker without fetching files. Source XLSX files are not required at runtime.

Automatic Bhavsadhan interpolates circular ecliptic longitude first between actual tabulated sidereal times, then between the two adjacent integer latitudes. The table has unequal time intervals; it does not assume a four-minute grid. Exact grid inputs retain the numeric source values. At 360° and midnight, interpolation follows the short angular interval instead of averaging 359° and 0° across the zodiac. Six opposite cusps are derived at +180°. The currently selected KP ayanamsha is subtracted once; rounding happens only when writing the final worksheet fields to one arcsecond. Unlike manual legacy arithmetic, automatic interpolation does not round the correction to whole arcminutes.

For a native birth chart, the input is the existing worksheet's **birthPlaceSiderealTime**, including its selected ephemeris source and time corrections. Instant Prashna uses local apparent sidereal time at the exact entered UTC instant and longitude. Numbered KP Horary retains its existing exact numbered Ascendant and date-specific solver. The source workbooks have no dated obliquity metadata: this mode deliberately interpolates their reference values rather than claiming date-specific accuracy.

The compact source selector lives in **ADM → Raphael houses**. Uploaded tables are the default. Southern latitudes or latitudes above 60° use the existing date-specific Placidus solver at the same local sidereal orientation; source status identifies that fallback. No extrapolation or north/south mirroring is performed. Polar-circle locations remain unsupported and clear calculated cusp results. **Date-specific Placidus** explicitly uses that solver throughout. **Manual table entry** preserves the existing editable worksheet method. Editing a source cusp/time bracket switches to Manual. Existing saved charts without a source field load in Manual to preserve their entered tables; new saves retain the selected source.

Changing birth details or pressing the ordinary Calculate button refreshes the cusp worksheet, kundali, significators and dependent reports automatically. No separate table-import or house-calculation button is needed.

The private customer worker always restores automatic house/ephemeris sources and annual KP ayanamsha on calculation or chart import. Customer exports omit these administrator worksheet settings; importing such an export does not fall back to stale manual worksheet values.

Validation: `PYTHONPATH=tests python -m unittest test_house_tables -v`.
