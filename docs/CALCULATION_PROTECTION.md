# KP MASTER calculation protection

This release uses commit `d15b677367dbc0d744ebb15adb378d5d7da566ba`
as the approved calculation baseline. Before the interface work, the complete
checkout was backed up to branch
`backup/pre-ui-1.2.1-2026-10-12` at that commit.

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

The calculation audit compares named and anonymous legacy script bodies in
`index.html` with the baseline. New interface modules are appended under their
own script/style IDs. The Transit Panchang daily engine is also a separate,
pure API: it takes explicit date/place values and does not write natal fields.

The optional Swiss Krishnamurti ayanamsha is isolated under
`vendor/ephemeris`. `uploaded-kp` remains the default and delegates every call
directly to the original objects, without reconstruction or rounding. Uranus,
Neptune and Pluto are display-only and are excluded from the traditional
nine-graha KP model.

## Approved reference guard

`tests/test_calculation_protection.py` protects the supplied native chart:

- 20 December 1950, 05:02:00, latitude 10°46′ N, UTC +05:30;
- longitude 76°42′ E must produce sidereal time `10:30:46`;
- longitude 89°10′ E must produce sidereal time `11:20:38`;
- the Raphael latitude sheet must be 11° (30 minutes and above advance to the
  next latitude; 29 minutes remains on the current latitude);
- planets, cusps, KP lords, worksheet fields and all nine Vimshottari MD rows
  must remain exactly equal after repeated calculations, visual chart controls,
  save and reload.

`tests/test_ephemeris_sources.py` loads the optional source adapter after a real
native calculation and requires exact equality in the default mode before and
after recalculation and saved-chart restoration. It separately checks the
opt-in Swiss ayanamsha samples.

## Required release gate

Run from the repository root:

```sh
PYTHONPATH=tests python3 -m unittest -v \
  test_calculation_protection \
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
