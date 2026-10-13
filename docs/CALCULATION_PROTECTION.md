# KP MASTER calculation protection

This release keeps commit `d15b677367dbc0d744ebb15adb378d5d7da566ba`
as the approved baseline for every unchanged calculation and data file. The
user-approved traditional 10/6 sidereal correction is separately pinned to
commit `b6208e6014134993abfd47a8c4644aa7ef9872ab` for only the two named native-ST
script blocks and their house-table documentation. The complete state before
that correction is backed up at branch
`backup/pre-10-6-correction-2026-10-13`.

The owner's later explicit Ishta Farak examples authorize a 50-arcsecond
threshold in final Raphael cusps: 45′19″ → 45′, 43′49″ → 43′,
45′50″ → 46′, 45′59″ → 46′. This intentional change is pinned to
`1194c4d71f3388a3dabc6cc9c85d6027b90de618` only for the shared rounding helper,
the manual Raphael block, the automatic house worksheet and its documentation.
The pre-change backup is `backup/pre-ishta-50seconds-2026-10-13`. The generic
table API and all source XLSX/data files retain the older protected baseline.
ST, LMT, ayanamsha, planetary positions and Vimshottari formulas are unchanged.

## Protected calculation boundary

Interface, report and licensing work must not edit the approved formula bodies
or their data. The protected boundary includes:

- native longitude, LMT, sidereal-time and Sampattik calculations;
- Raphael table selection/interpolation, Ishtbhav and final cusp calculations;
- annual KP ayanamsha and uploaded 05:30 planetary ephemeris calculations;
- KP sign, star, sub, sub-sub and significator calculations;
- Vimshottari MD, AD and PD dates and exact exclusive boundaries;
- transit, Horary, Ruling Planet, matchmaking, Vedic, Muhurta and HIT engines;
- the source files under `vendor/houses`, `vendor/vedic`, `vendor/muhurta`,
  `vendor/hit`, and the embedded table/ephemeris/dasha data.

The calculation audit compares named script bodies in `index.html` and protected
source files with their scoped approved commits. The formerly anonymous native
worksheet block now has the stable ID `kp-legacy-native-calculation-script`, so
both the shared 10/6 helper and the automatic caller are protected. All other
calculation blocks and data remain pinned to the earlier baseline. New interface
modules are appended under their own script/style IDs. The Transit Panchang
daily engine is also a separate, pure API: it takes explicit date/place values
and does not write natal fields.

The calculation-source guard is likewise additive. It does not implement a
formula: it prevents a legacy chart restored while ADM is unlocked from leaving
the application in Manual mode without an explicit `manualCalculations` record.
The **Use automatic calculations** action clears that saved record and selects
the existing automatic engines. The worksheet keeps its raw subtotal before the
separate 24-hour adjustment and labels the final sidereal value explicitly.

The optional Swiss Krishnamurti ayanamsha is isolated under
`vendor/ephemeris`. `uploaded-kp` remains the default and delegates every call
directly to the original objects, without reconstruction or rounding. Uranus,
Neptune and Pluto are display-only and are excluded from the traditional
nine-graha KP model.

## Approved reference guard

`tests/test_calculation_protection.py` protects the supplied native chart:

- 20 December 1950, 05:02:00, latitude 10°46′ N, UTC +05:30;
- longitude 76°42′ E must produce sidereal time `10:30:45`;
- longitude 89°10′ E must produce sidereal time `11:20:46`;
- the Raphael latitude sheet must be 11° (30 minutes and above advance to the
  next latitude; 29 minutes remains on the current latitude);
- planets, cusps, KP lords, worksheet fields and all nine Vimshottari MD rows
  must remain exactly equal after repeated calculations, visual chart controls,
  save and reload.

`tests/test_ephemeris_sources.py` loads the optional source adapter after a real
native calculation and requires exact equality in the default mode before and
after recalculation and saved-chart restoration. It separately checks the
opt-in Swiss ayanamsha samples.

`tests/test_native_worksheet_st.py` independently checks the traditional rule:
complete elapsed hours × 10 seconds plus remaining complete minutes ÷ 6,
with one final half-up rounding. It reproduces the reported automatic and manual
example `21:20:52 + 18:57:28 + 00:03:10 = 40:21:30 − 24:00:00 = 16:21:30`.
It verifies that a legacy restore while ADM is unlocked returns to Automatic,
while an explicitly saved manual record remains Manual until the user chooses
**Use automatic calculations**.

## Required release gate

Run from the repository root:

```sh
PYTHONPATH=tests python3 -m unittest -v \
  test_calculation_protection \
  test_ishta_rounding \
  test_ephemeris_sources \
  test_native_worksheet_st \
  test_house_tables \
  test_automatic_calculations \
  test_transit_selection \
  test_vedic_reports \
  test_muhurta \
  test_hit_theory
```

The result must be reported as PASS or FAIL. A failing approved numerical
assertion blocks the installer build. Do not change a formula merely to make a
test pass; diagnose the exact baseline difference first. A browser or test
harness failure must be reported separately and rerun in isolation.

For the compact Swiss reference validation, use a disposable environment with
`pyswisseph==2.10.3.2` and run (the explicit compilers avoid relying on a
machine-specific default):

```sh
python3 -m venv /tmp/kp-swiss-validation
CC=gcc CXX=g++ /tmp/kp-swiss-validation/bin/python -m pip install \
  --no-cache-dir pyswisseph==2.10.3.2
/tmp/kp-swiss-validation/bin/python \
  vendor/ephemeris/validate_swiss_krishnamurti.py
```

## UI-only release changes

Font/zoom controls, chart enlargement, tooltip styling, report layout,
navigation visibility, About content, calendar preview, printing and licensing
must operate outside the protected boundary. The hidden `KPDashaFal` engine is
retained for Prediction → Dasha Results and report composition, while its
duplicate standalone navigation icon/tab is intentionally absent.
