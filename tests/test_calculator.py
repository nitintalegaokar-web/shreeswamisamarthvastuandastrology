"""Browser regression checks for the dependency-free calculator.

Run with: python3 -m unittest discover -s tests -v
Requires Python Playwright and a Chromium executable on PATH (or set
CALCULATOR_CHROMIUM to its path). No browser or package downloads occur here.
"""

import base64
from datetime import datetime
import functools
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import threading
import unittest
import zlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright


REPOSITORY = Path(__file__).resolve().parents[1]
SECTIONS = (
    "home", "basic", "ayan", "lmt", "stcalc", "raphael5", "planet", "mdcalc",
    "karyesh", "aspects", "transit", "south9", "report", "astrosettings",
)
OUTPUT_IDS = (
    "ayanValue", "lonDifference", "lmtFinal", "birthPlaceSiderealTime",
    "r5_nirayan_1", "r5_rashi_1", "p6_motion_0", "p6_final_0",
    "mdBirthDasha", "mdBhogyaDuration",
)
REPORT_PAGE_SECTIONS = (
    "cover", "basic", "ayan", "lmt", "stcalc", "raphael5", "planet",
    "mdcalc", "adcalc", "kp-fourfold", "kp-sixfold", "kp-fourstep-section", "south9",
)
# A tiny local fixture tests the cover's image binding and print readiness.
# It deliberately does not stand in for the user's requested devotional photo.
COVER_IMAGE_FIXTURE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aCfoAAAAASUVORK5CYII="
# Independent reference fixtures from Swiss Ephemeris 2.10.03 (Moshier,
# geocentric apparent longitude, UTC). Swiss Ephemeris is not a test dependency.
EPHEMERIS_REFERENCE = (
    {
        "date": "2000-01-01T12:00:00Z",
        "tropical": {"Su": 280.36891968, "Mo": 223.32377544, "Ma": 327.96331332,
                     "Me": 271.88927501, "Ju": 25.25303031, "Ve": 241.56579833,
                     "Sa": 40.39563896, "Ra": 125.04064606},
        "ascendantTropical": 92.42999875,
    },
    {
        "date": "2026-10-06T00:00:00Z",
        "tropical": {"Su": 192.76015388, "Mo": 134.56755767, "Ma": 124.57725047,
                     "Me": 217.02069024, "Ju": 140.46883192, "Ve": 218.34872422,
                     "Sa": 11.18566288, "Ra": 327.45047901},
        "ascendantTropical": 178.59436249,
    },
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


class CalculatorBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chromium = os.environ.get("CALCULATOR_CHROMIUM") or shutil.which("chromium") or shutil.which("chromium-browser")
        if not chromium:
            raise RuntimeError("Install Chromium or set CALCULATOR_CHROMIUM to its executable path.")
        handler = functools.partial(QuietHandler, directory=str(REPOSITORY))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.addClassCleanup(cls.server.server_close)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.addClassCleanup(cls.stop_server)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/index.html"
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch(
            executable_path=chromium, headless=True, args=["--no-sandbox"],
        )
        cls.addClassCleanup(cls.browser.close)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        self.addCleanup(self.context.close)
        self.errors = []
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, wait_until="load")
        expect(self.page.locator("#page-title")).to_have_text("Home")
        expect(self.page.locator("main > #home")).to_be_visible()
        self.go("basic")
        expect(self.page.locator("#page-title")).to_have_text("Birth details")
        # The original calculator initializes several legacy worksheets on timers.
        self.page.wait_for_timeout(1700)

    def tearDown(self):
        self.assertEqual(self.errors, [], "Unexpected JavaScript errors: " + "\n".join(self.errors))

    def go(self, section):
        if self.page.viewport_size["width"] <= 800:
            self.page.locator("#menu-toggle").click()
        self.page.locator(f".app-sidebar [data-tab='{section}']").click()
        expect(self.page.locator(f"main > #{section}")).to_be_visible()

    def action(self, action):
        if action in ("export", "import"):
            self.page.locator(".backup-menu > summary").click()
        self.page.locator(f".global-actions [data-action='{action}']").click()

    def outputs(self):
        return self.page.evaluate("ids => Object.fromEntries(ids.map(id => [id, document.getElementById(id).value]))", OUTPUT_IDS)

    def editable_values(self):
        # Read the worksheet DOM independently of the application's save helper.
        return self.page.evaluate("""() => Object.fromEntries(
            [...document.querySelectorAll('main > section:not(#report) input[id],main > section:not(#report) select[id],main > section:not(#report) textarea[id]')]
            .filter(el => !el.readOnly && !el.disabled && el.dataset.calculationLocked !== 'true')
            .map(el => [el.id, el.value]))""")

    def prepare_worksheets(self):
        self.page.locator("#name").fill("Regression chart · मीरा")
        self.page.locator("#dob").fill("1990-06-15")
        self.page.locator("#birthTime").fill("12:30:00")
        self.page.locator("#birthPlace").fill("Pune, Maharashtra")
        self.page.locator("#lat").fill("18:31:00")
        self.page.locator("#lon").fill("73:51:00")
        self.page.locator("#dayAyan").fill("23:40:00")
        self.page.locator("#daySum").fill("00:00:30")
        self.go("ayan")
        self.page.locator("#stdLon").fill("82:30:00")
        self.go("stcalc")
        self.page.locator("#baseSidereal0530").fill("06:00:00")
        self.page.locator("#stLargeTime").fill("14:00:00")
        self.page.locator("#stSmallTime").fill("12:00:00")
        self.go("raphael5")
        for index, house in enumerate((10, 11, 12, 1, 2, 3)):
            self.page.locator(f"#r5_large_{house}").fill(f"{40 + index * 30}:00:00")
            self.page.locator(f"#r5_small_{house}").fill(f"{38 + index * 30}:00:00")
        self.go("planet")
        for index in range(8):
            self.page.locator(f"#p6_d_{index}").fill(f"{20 + index * 30}:00:00")
            self.page.locator(f"#p6_t_{index}").fill(f"{21 + index * 30}:00:00")
        self.go("astrosettings")
        self.page.locator("#astroName").fill("Test Astrologer")
        self.page.locator("#astroMobile").fill("1234567890")
        self.page.locator("#astroAddress").fill("Pune\nClient report office")
        self.action("calculate")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart calculations updated.")
        self.page.wait_for_timeout(650)
        self.assertTrue(all(self.outputs().values()), "Completed worksheets should produce nonempty outputs.")

    def prepare_exact_kp_worksheets(self):
        """Zero motion and equal interpolation endpoints give exact positions."""
        self.page.locator("#dob").fill("1990-06-15")
        self.page.locator("#birthTime").fill("12:00:00")
        self.page.locator("#dayAyan").fill("00:00:00")
        self.page.locator("#daySum").fill("00:00:00")
        self.go("stcalc")
        self.page.locator("#baseSidereal0530").fill("06:00:00")
        self.page.locator("#stLargeTime").fill("14:00:00")
        self.page.locator("#stSmallTime").fill("12:00:00")
        self.go("raphael5")
        for house, degree in ((1, 0), (2, 30), (3, 60), (10, 270), (11, 300), (12, 330)):
            self.page.locator(f"#r5_large_{house}").fill(f"{degree:02d}:00:00")
            self.page.locator(f"#r5_small_{house}").fill(f"{degree:02d}:00:00")
        self.go("planet")
        for index in range(8):
            degree = 5 + index * 30
            self.page.locator(f"#p6_d_{index}").fill(f"{degree:02d}:00:00")
            self.page.locator(f"#p6_t_{index}").fill(f"{degree:02d}:00:00")

    def prepare_exact_dasha(self, moon="00:00:00", dob="2000-01-01"):
        self.prepare_exact_kp_worksheets()
        self.go("basic")
        self.page.locator("#dob").fill(dob)
        self.go("planet")
        self.page.locator("#p6_d_1").fill(moon)
        self.page.locator("#p6_t_1").fill(moon)
        self.action("calculate")
        degrees, minutes, seconds = moon.split(":")
        expect(self.page.locator("#p6_final_1")).to_have_value(f"{int(degrees)}:{minutes}:{seconds}")
        self.go("mdcalc")

    def dasha_rows(self, selector="#adDashaRows"):
        return self.page.locator(selector).evaluate("""body => [...body.rows].map(row =>
            [...row.cells].map(cell => {
                const value = cell.cloneNode(true);
                value.querySelectorAll('.ad-birth-marker').forEach(marker => marker.remove());
                return value.textContent.trim();
            }))""")

    def import_file(self, contents, filename="chart.lkp"):
        self.action("import")
        self.page.locator("#import-chart-file").set_input_files({
            "name": filename, "mimeType": "application/json", "buffer": contents.encode("utf-8"),
        })

    def home_source(self, source_id):
        return self.page.locator(f'#home [data-home-source-id="{source_id}"]')

    def table_rows(self, table):
        return table.evaluate("""table => [...table.rows].map(row => [...row.cells].map(cell => {
            const value = cell.cloneNode(true);
            value.querySelectorAll('.ad-birth-marker').forEach(marker => marker.remove());
            return value.textContent.trim();
        }))""")

    def assert_home_calculation_tables_match(self, mode="basic"):
        prefix = {"basic": "kp-basic", "fourfold": "kp-fourfold", "sixfold": "kp-sixfold"}[mode]
        for suffix in ("planet", "house"):
            source_id = f"{prefix}-{suffix}"
            mirror = self.home_source(source_id)
            expect(mirror).to_be_visible()
            self.assertEqual(self.table_rows(mirror), self.table_rows(self.page.locator(f"#{source_id}")),
                             f"Home must show the current {source_id} calculation rather than example data.")

    def assert_home_dasha_dates_match(self):
        for source_id in ("mdDashaRows", "adDashaRows"):
            source_rows = self.dasha_rows(f"#{source_id}")
            source_dates = [[row[0], row[4], row[5]] for row in source_rows]
            mirror = self.home_source(source_id)
            expect(mirror).to_be_visible()
            actual_dates = mirror.locator("tbody tr").evaluate_all("""rows => [...rows].map(row =>
                [...row.cells].map(cell => cell.textContent.trim()))""")
            self.assertEqual(actual_dates, source_dates,
                             f"Home's compact {source_id} table must retain the worksheet's lord and dates.")

    def test_western_aspects_use_shortest_angle_inclusive_orbs_and_unique_pairs(self):
        # These fixtures have known geometric angles independent of the KP
        # whole-sign aspect renderer and of any ephemeris calculations.
        fixtures = [
            (359, 1, 0, 2, 2),
            (350, 20, 30, 0, 30),
            (350, 35, 45, 0, 45),
            (350, 50, 60, 0, 60),
            (350, 80, 90, 0, 90),
            (350, 110, 120, 0, 120),
            (350, 125, 135, 0, 135),
            (350, 140, 150, 0, 150),
            (359, 179, 180, 0, 180),
        ]
        results = self.page.evaluate("""fixtures => fixtures.map(([a,b,angle,orb]) =>
            window.KPWesternAspects.calculate([{id:'Su',longitude:a},{id:'Mo',longitude:b}], [], {aspects:[{angle,orb}]}))""", fixtures)
        for fixture, result in zip(fixtures, results):
            with self.subTest(angle=fixture[2]):
                self.assertEqual(len(result["planetToPlanet"]), 1)
                row = result["planetToPlanet"][0]
                self.assertEqual({row["source"], row["target"]}, {"Su", "Mo"})
                self.assertEqual(row["angle"], fixture[2])
                self.assertAlmostEqual(row["separation"], fixture[4], places=6)
        rejected = self.page.evaluate("""() => window.KPWesternAspects.calculate(
            [{id:'Su',longitude:359},{id:'Mo',longitude:1.0001}], [], {aspects:[{angle:0,orb:2}]})""")
        self.assertEqual(rejected["planetToPlanet"], [], "A separation just outside the orb must be excluded.")
        units = self.page.evaluate("""() => window.KPWesternAspects.calculate(
            [{id:'Su',longitude:359*3600},{id:'Mo',longitude:3600}],
            [{id:1,longitude:359*3600},{id:2,longitude:3600},{id:3,longitude:179*3600}],
            {unit:'arcseconds',aspects:[{angle:0,orb:2},{angle:180,orb:0}]})""")
        self.assertEqual(len(units["planetToPlanet"]), 1)
        self.assertEqual(len(units["planetToCusp"]), 5,
                         "Each supplied cusp must be checked independently, including the zodiac wrap.")
        complete = self.page.evaluate("""() => window.KPWesternAspects.calculate(
            ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'].map(id=>({id,longitude:0})),
            Array.from({length:12},(_,i)=>({id:i+1,longitude:0})), {aspects:[{angle:0,orb:0}]})""")
        pairs = [frozenset((row["source"], row["target"])) for row in complete["planetToPlanet"]]
        self.assertEqual(len(pairs), 36, "Nine planets must yield 36 unordered, non-self pairs.")
        self.assertEqual(len(set(pairs)), 36, "Reverse-direction duplicates must not appear.")
        self.assertEqual(len(complete["planetToCusp"]), 108)

    def test_western_aspect_tab_follows_natal_inputs_and_keeps_minor_aspects_optional(self):
        self.prepare_exact_kp_worksheets()
        self.action("calculate")
        self.go("aspects")
        expect(self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Ma"][data-angle="60"]')).to_have_count(1)
        expect(self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Me"][data-angle="90"]')).to_have_count(1)
        expect(self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Ju"][data-angle="120"]')).to_have_count(1)
        expect(self.page.locator('#western-planet-aspects tr[data-angle="30"]')).to_have_count(0)
        self.page.locator("#western-angle-30").check()
        self.page.locator("#western-orb-30").fill("0")
        expect(self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Mo"][data-angle="30"]')).to_have_count(1)
        self.page.locator("#western-angle-60").uncheck()
        expect(self.page.locator('#western-planet-aspects tr[data-angle="60"]')).to_have_count(0)
        self.go("planet")
        self.page.locator("#p6_d_0").fill("06:00:00")
        self.page.locator("#p6_t_0").fill("06:00:00")
        self.go("aspects")
        expect(self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Mo"][data-angle="30"]')).to_have_count(0)
        self.action("save")
        self.page.locator("#western-angle-60").check()
        self.page.locator("#western-angle-30").uncheck()
        self.action("load")
        expect(self.page.locator("#western-angle-60")).not_to_be_checked()
        expect(self.page.locator("#western-angle-30")).to_be_checked()
        expect(self.page.locator("#western-orb-30")).to_have_value("0")
        self.go("report")
        expect(self.page.locator('#printReport > [data-report-section="aspects"]')).to_have_count(0)
        expect(self.page.locator('#printReport > [data-report-section="transit"]')).to_have_count(0)

    def edit_ruling_planets(self, kind, date, time, ascendant="", moon="", rahu=""):
        self.page.locator(f'#home [data-ruling-edit="{kind}"]').click()
        expect(self.page.locator("#ruling-editor")).to_be_visible()
        for field, value in {
            "date": date, "time": time, "latitude": "18.52", "longitude": "73.85", "timezone": "5.5",
            "ascendant": ascendant, "moon": moon, "rahu": rahu,
        }.items():
            self.page.locator(f"#ruling-{field}").fill(value)
        self.page.locator("#ruling-apply").click()
        expect(self.page.locator("#ruling-editor")).not_to_be_visible()

    def test_both_ruling_tables_allow_manual_positions_and_round_trip_lkp_without_changing_native(self):
        self.prepare_exact_dasha()
        native, outputs = self.editable_values(), self.outputs()
        self.go("home")
        self.edit_ruling_planets("birth", "2024-09-20", "10:23:27", "359", "1", "89")
        self.edit_ruling_planets("current", "2026-10-06", "19:57:19", "89", "1", "359")
        expect(self.page.locator('#home-ruling-planets [data-home-day-lord]')).to_have_attribute("data-home-day-lord", "Ve")
        expect(self.page.locator('#home-current-ruling-planets [data-home-day-lord]')).to_have_attribute("data-home-day-lord", "Ma")
        for mount in ("home-ruling-planets", "home-current-ruling-planets"):
            table = self.page.locator(f"#{mount} table")
            self.assertEqual(table.locator("thead th").all_text_contents(), ["RP", "SgL", "StL", "SL", "SSL", "Aspd", "Aspg", "Conj"])
            moon = table.locator('tr[data-home-rp="Mo"]')
            for field, lord in {"sgl": "Ma", "stl": "Ke", "sl": "Ve", "ssl": "Ve"}.items():
                expect(moon.locator(f'[data-field="{field}"]')).to_have_text(lord)
            expect(table.locator('tr[data-home-rp="Ke"]')).to_have_count(1)
        expect(self.page.locator('#home-ruling-planets tr[data-home-rp="As"] [data-field="sgl"]')).to_have_text("Ju")
        expect(self.page.locator('#home-current-ruling-planets tr[data-home-rp="As"] [data-field="sgl"]')).to_have_text("Me")
        self.assertEqual(self.editable_values(), native, "Ruling-planet edits must not overwrite the native's chart inputs.")
        self.assertEqual(self.outputs(), outputs)
        birth_rows = self.table_rows(self.page.locator("#home-ruling-planets table"))
        current_rows = self.table_rows(self.page.locator("#home-current-ruling-planets table"))
        self.action("save")
        saved = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        self.assertEqual(saved["rulingSettings"]["birth"]["moon"], 1)
        self.assertEqual(saved["rulingSettings"]["current"]["ascendant"], 89)
        self.assertFalse(any(key.startswith("ruling-") or key.startswith("home") for key in saved["fields"]),
                         "Ruling dialog and Home controls belong in separate settings, not native chart fields.")
        with self.page.expect_download() as download_info:
            self.action("export")
        exported = json.loads(Path(download_info.value.path()).read_text(encoding="utf-8"))
        self.assertEqual(exported["format"], "KP-RAPHAEL-LKP")
        self.assertEqual(exported["version"], 3)
        self.assertEqual(exported["rulingSettings"], saved["rulingSettings"])
        self.edit_ruling_planets("birth", "2024-09-21", "12:00:00", "0", "15", "180")
        self.edit_ruling_planets("current", "2026-10-07", "12:00:00", "0", "15", "180")
        self.import_file(json.dumps(exported, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.assertEqual(self.table_rows(self.page.locator("#home-ruling-planets table")), birth_rows)
        self.assertEqual(self.table_rows(self.page.locator("#home-current-ruling-planets table")), current_rows)
        broken = json.loads(json.dumps(exported))
        broken["rulingSettings"]["current"]["latitude"] = 100
        broken["fields"]["name"]["value"] = "Must not partially replace native"
        self.import_file(json.dumps(broken))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Unable to import:")
        self.assertEqual(self.editable_values(), native, "Invalid ruling settings must reject the entire backup atomically.")
        self.assertEqual(self.table_rows(self.page.locator("#home-current-ruling-planets table")), current_rows)
        legacy = json.loads(json.dumps(exported))
        legacy["version"] = 2
        legacy.pop("format")
        legacy.pop("rulingSettings")
        self.import_file(json.dumps(legacy), filename="older-chart.json")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        for mount in ("home-ruling-planets", "home-current-ruling-planets"):
            expect(self.page.locator(f"#{mount}")).to_have_attribute("data-ruling-edited", "false")
        self.assertEqual(self.page.evaluate("window.KPRulingPlanets.getSettings()"), {"birth": None, "current": None},
                         "An older chart must not inherit ruling overrides from a previously open chart.")

    def test_ruling_time_edits_recalculate_current_positions_and_leave_birth_table_unchanged(self):
        self.prepare_exact_dasha()
        self.go("home")
        birth = self.table_rows(self.page.locator("#home-ruling-planets table"))
        native = self.editable_values()
        self.edit_ruling_planets("current", "2026-10-06", "06:00:00")
        morning = self.table_rows(self.page.locator("#home-current-ruling-planets table"))
        self.edit_ruling_planets("current", "2026-10-06", "12:00:00")
        noon = self.table_rows(self.page.locator("#home-current-ruling-planets table"))
        self.assertNotEqual(morning, noon, "Time edits must calculate actual Ascendant and Moon positions.")
        self.assertEqual(self.table_rows(self.page.locator("#home-ruling-planets table")), birth)
        self.assertEqual(self.editable_values(), native)
        settings = self.page.evaluate("window.KPRulingPlanets.getSettings()")
        self.assertIsNone(settings["current"]["ascendant"])
        self.assertIsNone(settings["current"]["moon"])
        self.assertIsNone(settings["current"]["rahu"])

    def test_offline_ephemeris_matches_independent_planet_and_ascendant_fixtures(self):
        actual = self.page.evaluate("""fixtures => fixtures.map(fixture => {
            const engine = window.KPEphemeris;
            return {
                tropical:Object.fromEntries(Object.keys(fixture.tropical).map(id=>[id,engine.tropical(fixture.date,id)])),
                sidereal:engine.positions(fixture.date), ayanamsha:engine.ayanamsha(fixture.date),
                ascendantTropical:(engine.ascendant(fixture.date,18.52,73.85)+engine.ayanamsha(fixture.date))%360,
            };
        })""", EPHEMERIS_REFERENCE)
        for fixture, values in zip(EPHEMERIS_REFERENCE, actual):
            with self.subTest(date=fixture["date"]):
                for planet, expected in fixture["tropical"].items():
                    delta = abs((values["tropical"][planet] - expected + 180) % 360 - 180)
                    self.assertLess(delta, 0.03, f"{planet}: independent tropical reference differs by {delta}°.")
                    sidereal = (values["tropical"][planet] - values["ayanamsha"]) % 360
                    self.assertAlmostEqual(values["sidereal"][planet], sidereal, places=7)
                asc_delta = abs((values["ascendantTropical"] - fixture["ascendantTropical"] + 180) % 360 - 180)
                self.assertLess(asc_delta, 0.01, "Ascendant must use the eastern horizon, including geographic longitude.")
                self.assertAlmostEqual((values["sidereal"]["Ke"] - values["sidereal"]["Ra"]) % 360, 180, places=7)

    def test_transit_scan_refines_sun_boundaries_and_preserves_mercury_reentries(self):
        self.prepare_exact_dasha()
        intervals = self.page.evaluate("""async () => {
            const sun = await window.KPTransit.scan({start:new Date('2026-03-01T00:00:00Z'),end:new Date('2026-05-01T00:00:00Z'),
                tracks:[{id:'sun-aries',planet:'Su',label:'Aries',levels:['sign'],test:d=>d.signIndex===0}]});
            const mercury = await window.KPTransit.scan({start:new Date('2026-06-01T00:00:00Z'),end:new Date('2026-08-20T00:00:00Z'),
                tracks:[{id:'mercury-ashlesha',planet:'Me',label:'Ashlesha',levels:['star'],test:d=>d.nakIndex===8}]});
            return {sun,mercury};
        }""")
        self.assertEqual(len(intervals["sun"]), 1)
        self.assertEqual(len(intervals["mercury"]), 2, "A retrograde exit and direct reentry must remain separate intervals.")
        # Independent Swiss Ephemeris roots use the same explicit worksheet
        # ayanamsha convention: zero at 2000-01-01, then 50.29 arcseconds/year.
        reference = {
            "sun": [("2026-03-20T23:36:37Z", "2026-04-20T10:40:42Z")],
            "mercury": [("2026-06-13T16:34:17Z", "2026-07-19T22:25:55Z"),
                        ("2026-07-27T19:14:46Z", "2026-08-09T22:06:38Z")],
        }
        for planet, rows in intervals.items():
            for row, expected in zip(rows, reference[planet]):
                with self.subTest(planet=planet, entry=expected[0]):
                    for key, stamp in zip(("start", "end"), expected):
                        delta = abs((datetime.fromisoformat(row[key].replace("Z", "+00:00")) -
                                     datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds())
                        self.assertLess(delta, 45 * 60, "Crossing date must agree with the independent astronomical reference.")
                    self.assertFalse(row["startClipped"])
                    self.assertFalse(row["endClipped"])
        boundary_checks = self.page.evaluate("""intervals => {
            const longitude=(stamp,seconds,planet)=>window.KPEphemeris.longitude(new Date(new Date(stamp).getTime()+seconds*1000),planet);
            return {
                sun:intervals.sun.map(row=>[longitude(row.start,-2,'Su'),longitude(row.start,2,'Su'),longitude(row.end,-2,'Su'),longitude(row.end,2,'Su')]),
                mercury:intervals.mercury.map(row=>[longitude(row.start,-2,'Me'),longitude(row.start,2,'Me'),longitude(row.end,-2,'Me'),longitude(row.end,2,'Me')]),
            };
        }""", intervals)
        for before_entry, after_entry, before_exit, after_exit in boundary_checks["sun"]:
            self.assertGreater(before_entry, 359)
            self.assertLess(after_entry, 1)
            self.assertLess(before_exit, 30)
            self.assertGreater(after_exit, 30)
        for before_entry, after_entry, before_exit, after_exit in boundary_checks["mercury"]:
            self.assertFalse(106 + 2 / 3 <= before_entry < 120)
            self.assertTrue(106 + 2 / 3 <= after_entry < 120)
            self.assertTrue(106 + 2 / 3 <= before_exit < 120)
            self.assertFalse(106 + 2 / 3 <= after_exit < 120)

    def run_transit_search(self):
        self.page.locator("#tr-run").click()
        expect(self.page.locator("#tr-run")).to_be_enabled(timeout=30000)
        expect(self.page.locator("#tr-status")).not_to_have_attribute("data-state", "running")
        return self.page.evaluate("window.KPTransit.getResults()")

    def test_event_transits_select_relevant_house_significators_and_require_all_requested_lords(self):
        self.prepare_exact_dasha()
        self.go("transit")
        expect(self.page.locator("#tr-houses")).to_have_value("2, 7, 11")
        selected = self.page.evaluate("window.KPTransit.significators().map(row=>row.id)")
        self.assertEqual(set(selected), {"Su", "Mo", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"},
                         "The exact natal fixture has no Mars membership in marriage houses 2, 7 or 11.")
        self.page.locator("#tr-event").select_option("career")
        expect(self.page.locator("#tr-houses")).to_have_value("2, 6, 10, 11")
        self.page.locator("#tr-event").select_option("custom")
        self.page.locator("#tr-houses").fill("1")
        self.page.locator("#tr-houses").dispatch_event("change")
        selected = self.page.evaluate("window.KPTransit.significators().map(row=>row.id)")
        self.assertEqual(set(selected), {"Su", "Mo", "Ma", "Ve", "Sa", "Ke"})
        for planet in ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"):
            self.page.locator(f"#tr-planet-{planet}").set_checked(planet == "Su")
        self.page.locator("#tr-match").select_option("all")
        self.page.locator("#tr-timezone").select_option("0")
        self.page.locator("#tr-start").fill("2026-01-01")
        self.page.locator("#tr-end").fill("2026-03-31")
        found = self.run_transit_search()
        self.assertTrue(found, "The custom-house Sun search must return dated intervals.")
        self.assertTrue(all(row["planet"] == "Su" for row in found))
        checks = self.page.evaluate("""rows => rows.map(row=>window.KPDisplay.longitudeDetails(
            window.KPEphemeris.longitude(new Date((new Date(row.start).getTime()+new Date(row.end).getTime())/2),'Su')*3600))""", found)
        for detail in checks:
            self.assertTrue(all(detail[field] in selected for field in ("sgl", "stl", "sl")),
                            "Sign, star and sub must all satisfy the selected event rule at the same time.")
        rows = self.page.locator("#tr-result-rows tr[data-entry]")
        expect(rows).to_have_count(len(found))
        expect(rows.first.locator("td").nth(1)).to_contain_text(found[0]["start"][:10])
        self.action("save")
        self.page.locator("#tr-houses").fill("4, 9")
        self.page.locator("#tr-planet-Sa").check()
        self.action("load")
        expect(self.page.locator("#tr-houses")).to_have_value("1")
        expect(self.page.locator("#tr-planet-Su")).to_be_checked()
        expect(self.page.locator("#tr-planet-Sa")).not_to_be_checked()
        self.page.locator("#tr-houses").fill("13")
        self.page.locator("#tr-houses").dispatch_event("change")
        self.assertEqual(self.run_transit_search(), [])
        expect(self.page.locator("#tr-status")).to_have_attribute("data-state", "error")
        expect(self.page.locator("#tr-status")).to_contain_text("between 1 and 12")
        expect(self.page.locator("#tr-result-rows tr[data-entry]")).to_have_count(0)

    def test_mutual_dasha_transits_cover_six_directions_three_levels_and_restore_manual_selection(self):
        self.prepare_exact_dasha()
        self.go("transit")
        self.page.locator("#tr-mode").select_option("dasha")
        self.page.locator("#tr-reference").fill("2000-01-01")
        self.page.locator("#tr-reference").dispatch_event("change")
        for role in ("md", "ad", "pd"):
            expect(self.page.locator(f"#tr-{role}")).to_have_value("Ke")
        periods = self.page.evaluate("""() => {
            const md=window.mdDashaPeriods[0],ad=window.calculateAntardashas(md)[0];
            return window.KPTransit.calculatePratyantardashas(md,ad);
        }""")
        self.assertEqual([row["lord"] for row in periods], ["केतू", "शुक्र", "रवी", "चंद्र", "मंगळ", "राहू", "गुरु", "शनि", "बुध"])
        self.assertAlmostEqual(sum(row["durationDays"] for row in periods), 147)
        self.assertEqual(periods[0]["start"], "2000-01-01")
        self.assertEqual(periods[0]["end"], "2000-01-10")
        self.assertEqual(periods[-1]["end"], "2000-05-28")
        self.assertTrue(all(periods[index]["end"] == periods[index + 1]["start"] for index in range(8)))
        self.page.locator("#tr-reference").fill("2000-01-10")
        self.page.locator("#tr-reference").dispatch_event("change")
        expect(self.page.locator("#tr-pd")).to_have_value("Ve")
        self.page.locator("#tr-dasha-source").select_option("manual")
        for role, planet in (("md", "Ju"), ("ad", "Sa"), ("pd", "Me")):
            self.page.locator(f"#tr-{role}").select_option(planet)
        actual = self.page.evaluate("""() => window.KPTransit.makeTracks().map(track=>({
            id:track.id,planet:track.planet,levels:track.levels,
            matches: ['Ju','Sa','Me'].map(lord=>track.test({sgl:lord,stl:lord,sl:lord}))
        }))""")
        roles = {"MD": "Ju", "AD": "Sa", "PD": "Me"}
        expected_ids = {f"{moving}>{target}:{level}" for moving in roles for target in roles if moving != target
                        for level in ("sign", "star", "sub")}
        self.assertEqual({track["id"] for track in actual}, expected_ids)
        for track in actual:
            moving, target = track["id"].split(":")[0].split(">")
            self.assertEqual(track["planet"], roles[moving])
            self.assertEqual(track["matches"], [roles[target] == planet for planet in ("Ju", "Sa", "Me")])
        self.page.locator("#tr-zone").select_option("natal")
        natal = self.page.evaluate("""() => window.KPTransit.makeTracks().filter(track=>track.id.startsWith('MD>AD:')).map(track=>({
            id:track.id,
            matches: [{signIndex:6,nakIndex:13,sl:'Su'},{signIndex:6,nakIndex:12,sl:'Su'}].map(detail=>track.test(detail))
        }))""")
        self.assertEqual({row["id"]: row["matches"] for row in natal}, {
            "MD>AD:sign": [True, True], "MD>AD:star": [True, False], "MD>AD:sub": [True, False],
        }, "Saturn at 185° requires its actual natal nakshatra and sub, not the same sub lord in another nakshatra.")
        self.page.locator("#tr-zone").select_option("lord")
        self.page.locator("#tr-direction").select_option("PD>AD")
        self.page.locator("#tr-level").select_option("sub")
        self.page.locator("#tr-timezone").select_option("0")
        self.page.locator("#tr-start").fill("2026-01-01")
        self.page.locator("#tr-end").fill("2026-01-31")
        found = self.run_transit_search()
        self.assertTrue(found)
        self.assertTrue(all(row["trackId"] == "PD>AD:sub" and row["planet"] == "Me" for row in found))
        lords = self.page.evaluate("""rows => rows.map(row=>window.KPDisplay.longitudeDetails(
            window.KPEphemeris.longitude(new Date((new Date(row.start).getTime()+new Date(row.end).getTime())/2),'Me')*3600).sl)""", found)
        self.assertEqual(set(lords), {"Sa"})
        self.action("save")
        saved = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        self.page.locator("#tr-dasha-source").select_option("auto")
        expect(self.page.locator("#tr-md")).to_be_disabled()
        self.page.reload(wait_until="load")
        self.page.wait_for_timeout(1700)
        self.import_file(json.dumps(saved, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.go("transit")
        expect(self.page.locator("#tr-dasha-source")).to_have_value("manual")
        for role, planet in (("md", "Ju"), ("ad", "Sa"), ("pd", "Me")):
            expect(self.page.locator(f"#tr-{role}")).to_be_enabled()
            expect(self.page.locator(f"#tr-{role}")).to_have_value(planet)
        expect(self.page.locator("#tr-direction")).to_have_value("PD>AD")
        expect(self.page.locator("#tr-level")).to_have_value("sub")

    def test_sun_transit_combinations_match_both_lords_simultaneously_and_show_dates(self):
        self.prepare_exact_dasha()
        self.go("transit")
        self.page.locator("#tr-mode").select_option("sun")
        self.page.locator("#tr-dasha-source").select_option("manual")
        self.page.locator("#tr-md").select_option("Ju")
        self.page.locator("#tr-ad").select_option("Sa")
        self.page.locator("#tr-timezone").select_option("0")
        self.page.locator("#tr-start").fill("2026-01-01")
        self.page.locator("#tr-end").fill("2026-12-31")
        found = self.run_transit_search()
        self.assertEqual({row["trackId"] for row in found}, {"sun:MD-sign-AD-star", "sun:MD-star-AD-sign"})
        self.assertEqual(len(found), 2, "Each fixed lord combination has one Sun passage per year in this fixture.")
        checks = self.page.evaluate("""rows => rows.map(row=>({id:row.trackId,detail:window.KPDisplay.longitudeDetails(
            window.KPEphemeris.longitude(new Date((new Date(row.start).getTime()+new Date(row.end).getTime())/2),'Su')*3600)}))""", found)
        for check in checks:
            detail = check["detail"]
            if check["id"] == "sun:MD-sign-AD-star":
                self.assertEqual((detail["sgl"], detail["stl"]), ("Ju", "Sa"))
                self.assertTrue(333 + 1 / 3 <= detail["longitude"] / 3600 < 346 + 2 / 3)
            else:
                self.assertEqual((detail["stl"], detail["sgl"]), ("Ju", "Sa"))
                self.assertTrue(320 <= detail["longitude"] / 3600 < 330)
        expect(self.page.locator("#tr-result-rows tr[data-entry]")).to_have_count(2)
        self.page.locator("#tr-start").fill("2026-12-31")
        self.page.locator("#tr-end").fill("2026-01-01")
        self.assertEqual(self.run_transit_search(), [])
        expect(self.page.locator("#tr-status")).to_have_attribute("data-state", "error")
        expect(self.page.locator("#tr-status")).to_contain_text("end date on or after the start")

    def test_transit_scan_detects_a_short_station_crossing_between_equal_outside_endpoints(self):
        result = self.page.evaluate("""async () => {
            const original=window.KPEphemeris,origin=new Date('2026-10-01T00:00:00Z').getTime(),day=86400000;
            try {
                window.KPEphemeris={...original,longitude:date=>30.0001-((date.getTime()-origin)/day-.25)**2};
                return await window.KPTransit.scan({start:new Date(origin),end:new Date(origin+day),
                    tracks:[{id:'station',planet:'Me',label:'Station crossing',levels:['sign'],test:d=>d.signIndex===1}]});
            } finally { window.KPEphemeris=original; }
        }""")
        self.assertEqual(len(result), 1, "A short passage around a station must survive a bracket with both endpoints outside.")
        for key, expected in (("start", "2026-10-01T05:45:36Z"), ("end", "2026-10-01T06:14:24Z")):
            delta = abs((datetime.fromisoformat(result[0][key].replace("Z", "+00:00")) -
                         datetime.fromisoformat(expected.replace("Z", "+00:00"))).total_seconds())
            self.assertLess(delta, 1, "The analytic parabola gives independent station crossing times.")

    def test_home_shows_current_native_kundali_calculations_and_dasha_together(self):
        self.prepare_worksheets()
        self.go("home")
        expect(self.page.locator("#home-status")).to_have_attribute("data-ready", "true")
        for field in ("name", "dob", "birthTime", "birthPlace", "lat", "lon", "ayanValue", "lmtFinal"):
            expect(self.page.locator(f'#home-native [data-home-field="{field}"]')).to_have_attribute(
                "data-home-value", self.page.locator(f"#{field}").input_value())
        chart = self.home_source("kundali")
        expect(chart).to_be_visible()
        self.assertEqual(chart.locator(".v38-cell").all_text_contents(),
                         self.page.locator("#kundali .v38-cell").all_text_contents())
        self.assertEqual(chart.locator(".v38-center").text_content(),
                         self.page.locator("#kundali .v38-center").text_content())
        expect(chart.locator(".v38-cusp")).to_have_count(12)
        expect(chart.locator(".v38-planet")).to_have_count(9)
        self.assert_home_calculation_tables_match()
        self.assert_home_dasha_dates_match()
        expect(self.page.locator('#home-ruling-planets [data-home-day-lord]')).to_have_attribute("data-home-day-lord", "Ve")
        for rp_id in ("As", "Mo", "Ra", "Ke"):
            rp = self.page.locator(f'#home-ruling-planets tr[data-home-rp="{rp_id}"]')
            source = self.page.locator('#kp-basic-house tr[data-house="1"]') if rp_id == "As" else self.page.locator(f'#kp-basic-planet tr[data-planet="{rp_id}"]')
            for field in ("sgl", "stl", "sl", "ssl"):
                expect(rp.locator(f'[data-field="{field}"]')).to_have_text(source.locator(f'[data-field="{field}"]').text_content())
        duplicates = self.page.evaluate("""() => {
            const seen = new Set();
            return [...document.querySelectorAll('[id]')].map(element => element.id)
                .filter(id => seen.has(id) || !seen.add(id));
        }""")
        self.assertEqual(duplicates, [], "Home clones must not duplicate worksheet IDs.")
        expect(self.page.locator('#home [contenteditable="true"]')).to_have_count(0)
        self.go("report")
        self.assertEqual(self.page.locator("#printReport > .report-page").count(), len(REPORT_PAGE_SECTIONS))
        expect(self.page.locator('#printReport > [data-report-section="home"]')).to_have_count(0)

    def test_home_refreshes_after_edits_save_load_and_json_import(self):
        self.prepare_exact_dasha()
        self.go("basic")
        self.page.locator("#name").fill("Home chart · मीरा")
        self.page.locator("#birthPlace").fill("Pune")
        self.go("home")
        expect(self.page.locator('#home-native [data-home-field="name"]')).to_have_text("Home chart · मीरा")
        self.assert_home_calculation_tables_match()
        self.assert_home_dasha_dates_match()
        self.action("save")
        saved = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        self.assertFalse(any(field.startswith("home") for field in saved["fields"]),
                         "Home display controls must not become chart inputs in backups.")
        self.go("basic")
        self.page.locator("#name").fill("Unsaved replacement")
        self.go("planet")
        self.page.locator("#p6_d_0").fill("09:00:00")
        self.page.locator("#p6_t_0").fill("09:00:00")
        self.go("home")
        expect(self.page.locator('#home-native [data-home-field="name"]')).to_have_text("Unsaved replacement")
        expect(self.home_source("kp-basic-planet").locator('tr[data-planet="Su"] [data-field="degree"]')).to_have_text("9°00′00″")
        self.action("load")
        expect(self.page.locator("#workspace-toast")).to_have_text("Saved chart loaded and recalculated.")
        expect(self.page.locator('#home-native [data-home-field="name"]')).to_have_text("Home chart · मीरा")
        expect(self.home_source("kp-basic-planet").locator('tr[data-planet="Su"] [data-field="degree"]')).to_have_text("5°00′00″")
        self.assert_home_dasha_dates_match()
        saved["fields"]["name"]["value"] = "Imported <b>literal</b> chart"
        saved["fields"]["birthPlace"]["value"] = "Nashik"
        saved["fields"]["p6_d_1"]["value"] = "06:40:00"
        saved["fields"]["p6_t_1"]["value"] = "06:40:00"
        self.import_file(json.dumps(saved, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator('#home-native [data-home-field="name"]')).to_have_text("Imported <b>literal</b> chart")
        expect(self.page.locator('#home-native [data-home-field="birthPlace"]')).to_have_text("Nashik")
        expect(self.page.locator("#home-native b")).to_have_count(0)
        expect(self.page.locator("#mdBhogyaDuration")).to_have_value("3 वर्ष 6 महिने 0 दिवस")
        self.assert_home_calculation_tables_match()
        self.assert_home_dasha_dates_match()
        self.action("calculate")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart calculations updated.")
        self.assert_home_calculation_tables_match()

    def test_home_view_buttons_and_md_selection_show_real_synchronized_results(self):
        self.prepare_exact_dasha()
        self.go("home")
        for mode in ("basic", "fourfold", "sixfold"):
            self.page.locator(f'#home [data-home-view="{mode}"]').click()
            expect(self.page.locator(f'#home [data-home-view="{mode}"]')).to_have_attribute("aria-pressed", "true")
            self.assert_home_calculation_tables_match(mode)
        self.page.locator('#home [data-home-view="fourstep"]').click()
        mirror = self.home_source("kp-fourstep")
        expect(mirror).to_be_visible()
        self.assertEqual(mirror.text_content(), self.page.locator("#kp-fourstep").text_content())
        self.page.locator('#home [data-home-view="basic"]').click()
        home_select = self.page.locator("#home .home-ad-select")
        expect(home_select.locator("option")).to_have_count(9)
        source_values = self.page.locator("#adMDSelect option").evaluate_all("options => [...options].map(option => option.value)")
        home_select.select_option(source_values[1])
        expect(self.page.locator("#adMDSelect")).to_have_value(source_values[1])
        expect(self.page.locator("#adBirthLord")).to_have_value("केतू")
        self.assert_home_dasha_dates_match()
        self.page.locator(f'#home-md button[data-home-md-key="{source_values[0]}"]').click()
        expect(self.page.locator("#adMDSelect")).to_have_value(source_values[0])
        expect(home_select).to_have_value(source_values[0])
        self.assert_home_dasha_dates_match()
        self.go("mdcalc")
        self.page.locator("#adMDSelect").select_option(source_values[2])
        self.go("home")
        expect(home_select).to_have_value(source_values[2])
        self.assert_home_dasha_dates_match()

    def test_home_preserves_manual_notes_without_exposing_editable_copies(self):
        self.go("south9")
        self.page.get_by_role("button", name="Manual Edit").click()
        note = '<img src=x onerror="window.homeExecuted=true"> · manual कुंडली'
        source = self.page.locator("#kundali .v38-cell[data-sign-index='0']")
        source.fill(note)
        self.page.locator("#kundali .v38-center").fill("Manual center")
        self.go("home")
        mirror = self.home_source("kundali")
        expect(mirror.locator(".v38-cell[data-sign-index='0']")).to_have_text(note)
        expect(mirror.locator(".v38-center")).to_have_text("Manual center")
        expect(mirror.locator("img")).to_have_count(0)
        expect(mirror.locator('[contenteditable="true"]')).to_have_count(0)
        self.assertFalse(self.page.evaluate("Boolean(window.homeExecuted)"))
        self.assertTrue(source.evaluate("element => element.isContentEditable"),
                        "Read-only Home mirroring must not disable the source worksheet's manual editor.")
        self.action("save")
        self.action("load")
        expect(mirror.locator(".v38-cell[data-sign-index='0']")).to_have_text(note)

    def test_home_dashboard_fits_desktop_and_mobile_with_separate_chart_lanes(self):
        self.prepare_exact_dasha()
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.go("home")
        for mount in ("home-ruling-planets", "home-current-ruling-planets"):
            expect(self.page.locator(f"#{mount}")).to_have_attribute("data-ready", "true")
            expect(self.page.locator(f"#{mount} tbody tr[data-home-rp]")).to_have_count(4)
            bounds = self.page.locator(f"#{mount}").evaluate("""mount => {
                const box=mount.getBoundingClientRect(),table=mount.querySelector('table').getBoundingClientRect();
                return {mountBottom:box.bottom,tableBottom:table.bottom,mountRight:box.right,tableRight:table.right};
            }""")
            self.assertLessEqual(bounds["tableBottom"], bounds["mountBottom"] + 1, "All four ruling rows must fit their table panel.")
            self.assertLessEqual(bounds["tableRight"], bounds["mountRight"] + 1, "All eight ruling columns must fit their table panel.")
            self.assertLessEqual(bounds["mountBottom"], 1081, "Both CT and RT tables must fit the initial desktop screen.")
        toggle = self.page.locator("#home-expand-workspace")
        toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "true")
        expect(self.page.locator("body")).to_have_class(re.compile(r".*\bhome-expanded\b.*"))
        columns = self.page.locator("#home .home-dashboard").evaluate("""dashboard => {
            const box = element => { const r = element.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width}; };
            return ['.home-chart-column','.home-data-column','.home-summary-column'].map(selector => box(dashboard.querySelector(selector)));
        }""")
        self.assertLessEqual(columns[0]["right"], columns[1]["left"] + 1, columns)
        self.assertLessEqual(columns[1]["right"], columns[2]["left"] + 1, columns)
        for column in columns:
            self.assertGreater(column["width"], 150, columns)
            self.assertLessEqual(column["bottom"], 1081, "Expanded Home should show all three columns in one desktop screen.")
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 1921)

        # Exercise both the normal two-line layout's five-entry threshold and
        # the dense layout using the real source renderer.
        fixture_script = """({cusps, planets}) => {
            window.calculateAll = () => {};
            window.updateKaryeshTables = () => {};
            const longitude = 11 * 108000 + 107999;
            window.cuspResults = Array.from({length:12}, (_, i) => ({i:i+1,nir:i<cusps?longitude:(i-cusps)*108000}));
            window.lastPlanetPositions = Object.fromEntries(
                ['रवी','चंद्र','मंगळ','बुध','गुरु','शुक्र','शनि','राहू','केतू'].map((planet,i) => [planet,i<planets?longitude:(i-planets)*108000]));
            window.kundaliManual = false;
            window.renderChart(true);
        }"""
        geometry_script = """cell => {
                    const errors = [], bounds = cell.getBoundingClientRect(), middle = (bounds.left+bounds.right)/2, tolerance=.7;
                    const entries = [...cell.querySelectorAll('.v38-item')], glyphs=[];
                    const overlap = (a,b) => Math.min(a.right,b.right)-Math.max(a.left,b.left)>tolerance &&
                        Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>tolerance;
                    for (const entry of entries) {
                        const rect=entry.getBoundingClientRect(), cusp=entry.dataset.kind==='cusp';
                        if(rect.left<bounds.left-tolerance || rect.right>bounds.right+tolerance || rect.top<bounds.top-tolerance || rect.bottom>bounds.bottom+tolerance)
                            errors.push('Entry outside sign: '+entry.textContent);
                        if(cusp ? rect.right>middle+tolerance : rect.left<middle-tolerance)
                            errors.push('Entry outside assigned lane: '+entry.textContent);
                        for(const selector of ['.v38-name','.v38-degree']) {
                            const label=entry.querySelector(selector), range=document.createRange();
                            range.selectNodeContents(label); const text=range.getBoundingClientRect();
                            if(text.width<=0 || text.height<=0 || text.left<rect.left-tolerance || text.right>rect.right+tolerance ||
                                text.top<bounds.top-tolerance || text.bottom>bounds.bottom+tolerance)
                                errors.push('Clipped label: '+label.textContent);
                            glyphs.push({rect:text,entry});
                        }
                    }
                    for(let i=0;i<glyphs.length;i++) for(let j=i+1;j<glyphs.length;j++)
                        if(overlap(glyphs[i].rect,glyphs[j].rect)) errors.push('Overlapping chart labels');
                    return errors;
                }"""
        for cusp_count, planet_count in ((12, 9), (5, 5)):
            self.page.evaluate(fixture_script, {"cusps": cusp_count, "planets": planet_count})
            crowded = self.home_source("kundali").locator('.v38-cell[data-sign-index="11"]')
            expect(crowded.locator(".v38-cusp")).to_have_count(cusp_count)
            expect(crowded.locator(".v38-planet")).to_have_count(planet_count)
            for width, height in ((1920, 1080), (390, 844)):
                with self.subTest(width=width, cusps=cusp_count, planets=planet_count):
                    self.page.set_viewport_size({"width": width, "height": height})
                    self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width + 1)
                    geometry_errors = crowded.evaluate(geometry_script)
                    self.assertEqual(geometry_errors, [], "\n".join(geometry_errors))
                    self.assertTrue(all(text == "29°59′59″" for text in crowded.locator(".v38-degree").all_text_contents()))
        for mode in ("basic", "fourfold", "sixfold", "fourstep"):
            self.page.locator(f'#home [data-home-view="{mode}"]').click()
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 391,
                                 f"The {mode} Home view must scroll within its mobile panel.")
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "false")
        self.go("basic")
        self.assertFalse(self.page.locator("body").evaluate("element => element.classList.contains('home-expanded')"))

    def test_birth_inputs_recalculate_and_validate_with_live_summary(self):
        self.page.locator("#name").fill("अनया Patil")
        self.page.locator("#birthTime").fill("10:30:00")
        self.page.locator("#lon").fill("81:00:00")
        self.page.locator("#dayAyan").fill("23:40:00")
        self.page.locator("#daySum").fill("00:00:30")
        expect(self.page.locator("#overview-name")).to_have_text("अनया Patil")
        expect(self.page.locator("#ayanValue")).to_have_value("23:40:30")
        expect(self.page.locator("#overview-ayan")).to_have_text("23:40:30")
        expect(self.page.locator("#overview-longitude")).to_have_text("01:30:00")
        expect(self.page.locator("#overview-lmt")).to_have_text("10:24:00")
        self.page.locator("#lon").fill("181:00:00")
        self.action("calculate")
        expect(self.page.locator("#lon")).to_be_focused()
        expect(self.page.locator("#lon")).to_have_attribute("aria-invalid", "true")
        expect(self.page.locator("#lon-error")).to_contain_text("Longitude must be between")
        self.page.locator("#lon").fill("81:00:00")
        self.action("calculate")
        expect(self.page.locator("#lon-error")).to_have_count(0)
        self.go("south9")
        expect(self.page.locator("#kundali .v38-center")).to_contain_text("अनया Patil")

    def test_index_is_self_contained_without_sibling_files(self):
        with tempfile.TemporaryDirectory(prefix="kp-standalone-test-") as directory:
            standalone = Path(directory) / "index.html"
            shutil.copyfile(REPOSITORY / "index.html", standalone)
            self.assertEqual(list(Path(directory).iterdir()), [standalone], "The standalone fixture must contain only index.html.")
            handler = functools.partial(QuietHandler, directory=directory)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            context = self.browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
            try:
                page = context.new_page()
                failed_resources = []
                requested_resources = []
                page.on("request", lambda request: requested_resources.append(request.url))
                page.on("requestfailed", lambda request: failed_resources.append(f"{request.url}: {request.failure}"))
                page.on("response", lambda response: failed_resources.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
                page.on("pageerror", lambda error: self.errors.append("Standalone HTML: " + str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/index.html", wait_until="load")
                page.wait_for_timeout(1700)
                expect(page.locator("#page-title")).to_have_text("Home")
                expect(page.locator("main > #home")).to_be_visible()
                page.locator(".app-sidebar [data-tab='basic']").click()
                self.assertEqual(failed_resources, [], "Opening index.html alone must not require missing sibling assets.")
                layout = page.evaluate("""() => ({
                    sidebarPosition: getComputedStyle(document.getElementById('app-sidebar')).position,
                    mainMargin: parseFloat(getComputedStyle(document.getElementById('workspace-main')).marginLeft),
                    birthLayout: getComputedStyle(document.querySelector('.birth-layout')).display,
                })""")
                self.assertEqual(layout["sidebarPosition"], "fixed", "The professional sidebar styling must load from the HTML file.")
                self.assertGreaterEqual(layout["mainMargin"], 240, "The desktop workspace must leave room for its sidebar.")
                self.assertEqual(layout["birthLayout"], "grid")
                expect(page.locator("#overview-lmt")).to_have_text(page.locator("#lmtFinal").input_value())

                page.set_viewport_size({"width": 390, "height": 844})
                menu = page.locator("#menu-toggle")
                menu.click()
                expect(menu).to_have_attribute("aria-expanded", "true")
                page.locator(".app-sidebar [data-tab='stcalc']").click()
                expect(page.locator("#page-title")).to_have_text("Sidereal time")
                expect(page.locator("#stcalc")).to_be_visible()
                expect(menu).to_have_attribute("aria-expanded", "false")
                menu.click()
                page.locator(".app-sidebar [data-tab='basic']").click()

                calculate = page.locator(".global-actions [data-action='calculate']")
                page.locator("#lon").fill("181:00:00")
                calculate.click()
                expect(page.locator("#lon")).to_have_attribute("aria-invalid", "true")
                expect(page.locator("#lon-error")).to_contain_text("Longitude must be between")
                page.locator("#lon").fill("81:00:00")
                page.locator("#birthTime").fill("10:30:00")
                page.locator("#name").fill("Portable chart · अनया")
                calculate.click()
                expect(page.locator("#lon-error")).to_have_count(0)
                expect(page.locator("#overview-longitude")).to_have_text("01:30:00")
                expect(page.locator("#overview-lmt")).to_have_text("10:24:00")
                page.locator(".global-actions [data-action='save']").click()
                expect(page.locator("#workspace-toast")).to_have_text("Chart and worksheet data saved in this browser.")
                page.locator("#name").fill("Unsaved edit")
                page.locator("#birthTime").fill("12:30:00")
                page.locator("#lon").fill("80:00:00")
                expect(page.locator("#overview-lmt")).to_have_text("12:20:00")
                page.locator(".global-actions [data-action='load']").click()
                expect(page.locator("#workspace-toast")).to_have_text("Saved chart loaded and recalculated.")
                expect(page.locator("#name")).to_have_value("Portable chart · अनया")
                expect(page.locator("#birthTime")).to_have_value("10:30:00")
                expect(page.locator("#lon")).to_have_value("81:00:00")
                expect(page.locator("#overview-lmt")).to_have_text("10:24:00")
                page.locator(".backup-menu > summary").click()
                with page.expect_download() as download_info:
                    page.locator(".global-actions [data-action='export']").click()
                download = download_info.value
                self.assertTrue(download.suggested_filename.endswith(".lkp"))
                exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
                self.assertEqual(exported["fields"]["name"]["value"], "Portable chart · अनया")
                self.assertEqual(exported["fields"]["birthTime"]["value"], "10:30:00")
                menu.click()
                page.locator(".app-sidebar [data-tab='home']").click()
                expect(page.locator("#page-title")).to_have_text("Home")
                expect(page.locator('#home-native [data-home-field="name"]')).to_have_text("Portable chart · अनया")
                expect(page.locator('#home-native [data-home-field="lmtFinal"]')).to_have_attribute("data-home-value", "10:24:00")
                expect(page.locator('#home [data-home-source-id="kundali"]')).to_be_visible()
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 391)
                offline = page.evaluate("""async () => {
                    const planets=window.KPEphemeris.positions('2026-10-06T00:00:00Z');
                    const intervals=await window.KPTransit.scan({start:new Date('2026-04-01T00:00:00Z'),end:new Date('2026-05-01T00:00:00Z'),
                        tracks:[{id:'offline-sun',planet:'Su',label:'Aries',levels:['sign'],test:d=>d.signIndex===0}]});
                    return {sun:window.KPEphemeris.tropical('2026-10-06T00:00:00Z','Su'),planets,intervals};
                }""")
                self.assertAlmostEqual(offline["sun"], 192.76015388, delta=0.03)
                self.assertAlmostEqual((offline["planets"]["Ke"] - offline["planets"]["Ra"]) % 360, 180, places=7)
                self.assertEqual(len(offline["intervals"]), 1, "A standalone index.html must calculate dated transits offline.")
                self.assertEqual(failed_resources, [], "The standalone workflow must complete without failed resource loads.")
                self.assertTrue(all(url.startswith((f"http://127.0.0.1:{server.server_port}/", "data:", "blob:"))
                                    for url in requested_resources),
                                "Planet and transit calculations must not request online ephemeris services or assets.")
            finally:
                context.close()
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

    def test_save_and_load_restore_all_worksheet_fields_and_recalculate(self):
        self.prepare_worksheets()
        expected_fields = self.editable_values()
        expected_outputs = self.outputs()
        self.action("save")
        expect(self.page.locator("#save-state")).to_have_text("Saved in this browser")
        self.go("basic")
        self.page.locator("#name").fill("Temporary edit")
        self.page.locator("#lon").fill("80:00:00")
        self.go("stcalc")
        self.page.locator("#baseSidereal0530").fill("08:00:00")
        self.go("raphael5")
        self.page.locator("#r5_small_1").fill("145:00:00")
        self.go("planet")
        self.page.locator("#p6_d_0").fill("10:00:00")
        self.assertNotEqual(self.outputs(), expected_outputs, "Editing worksheet inputs should alter calculated results.")
        self.action("load")
        expect(self.page.locator("#workspace-toast")).to_have_text("Saved chart loaded and recalculated.")
        self.page.wait_for_timeout(650)
        self.assertEqual(self.editable_values(), expected_fields, "Load should restore every editable worksheet field.")
        self.assertEqual(self.outputs(), expected_outputs, "Load should recompute the saved chart's results.")
        self.page.reload(wait_until="load")
        self.page.wait_for_timeout(1700)
        expect(self.page.locator("#save-state")).to_have_text("Saved chart available")
        self.action("load")
        self.page.wait_for_timeout(650)
        self.assertEqual(self.editable_values(), expected_fields, "The saved chart should survive a browser reload.")
        self.assertEqual(self.outputs(), expected_outputs)

    def test_lkp_download_and_file_import_restore_the_chart_and_accept_legacy_json(self):
        self.prepare_worksheets()
        expected_fields, expected_outputs = self.editable_values(), self.outputs()
        with self.page.expect_download() as download_info:
            self.action("export")
        download = download_info.value
        self.assertTrue(download.suggested_filename.endswith(".lkp"))
        accept = self.page.locator("#import-chart-file").get_attribute("accept").split(",")
        self.assertIn(".lkp", accept)
        self.assertIn(".json", accept, "Previously exported JSON charts must remain importable.")
        with tempfile.TemporaryDirectory(prefix="kp-chart-test-") as directory:
            backup = Path(directory) / download.suggested_filename
            download.save_as(backup)
            exported = json.loads(backup.read_text(encoding="utf-8"))
            self.assertEqual(exported["fields"]["astroAddress"]["value"], "Pune\nClient report office")
            self.assertEqual(exported["fields"]["r5_small_1"]["value"], expected_fields["r5_small_1"])
            self.go("basic")
            self.page.locator("#name").fill("Changed after export")
            self.page.locator("#birthTime").fill("15:00:00")
            self.action("import")
            self.page.locator("#import-chart-file").set_input_files(backup)
            expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
            self.page.wait_for_timeout(650)
        self.assertEqual(self.editable_values(), expected_fields, "File import should restore all worksheet inputs.")
        self.assertEqual(self.outputs(), expected_outputs, "File import should recalculate chart results.")
        expect(self.page.locator("#save-state")).to_have_text("Imported · not saved")
        self.go("basic")
        self.page.locator("#name").fill("Changed before legacy import")
        legacy = json.loads(json.dumps(exported))
        legacy["version"] = 2
        legacy.pop("format")
        legacy.pop("rulingSettings")
        self.import_file(json.dumps(legacy, ensure_ascii=False), filename="older-chart.json")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.assertEqual(self.editable_values(), expected_fields,
                         "Changing the default file extension must preserve older JSON backups.")

    def test_manual_chart_text_survives_navigation_save_load_and_literal_import(self):
        self.go("south9")
        self.page.get_by_role("button", name="Manual Edit").click()
        cell = self.page.locator("#kundali .v38-cell[data-sign-index='0']")
        center = self.page.locator("#kundali .v38-center")
        cell.fill("मेष · personal note\nSecond line")
        center.fill("Manual center · अनया")
        self.action("save")
        expect(self.page.locator("#save-state")).to_have_text("Saved in this browser")
        self.go("basic")
        self.page.locator("#name").fill("Different birth name")
        self.go("south9")
        expect(cell).to_have_text("मेष · personal note\nSecond line", use_inner_text=True)
        expect(center).to_have_text("Manual center · अनया")
        cell.fill("Unsaved manual edit")
        expect(self.page.locator("#save-state")).to_have_text("Unsaved changes")
        self.action("load")
        expect(cell).to_have_text("मेष · personal note\nSecond line", use_inner_text=True)
        expect(center).to_have_text("Manual center · अनया")
        data = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        literal = '<img src=x onerror="window.importExecuted=true"> & <b>literal text</b>'
        data["kundali"]["cells"][0]["text"] = literal
        data["kundali"]["center"] = literal
        self.import_file(json.dumps(data, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(cell).to_have_text(literal)
        expect(center).to_have_text(literal)
        expect(self.page.locator("#kundali img, #kundali b")).to_have_count(0)
        self.assertFalse(self.page.evaluate("Boolean(window.importExecuted)"), "Imported notes must remain literal text.")

    def test_mobile_navigation_escape_focus_and_all_sections_fit_viewport(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        menu = self.page.locator("#menu-toggle")
        menu.click()
        expect(menu).to_have_attribute("aria-expanded", "true")
        expect(self.page.locator(".sidebar-close")).to_be_focused()
        self.page.keyboard.press("Shift+Tab")
        expect(self.page.locator("#help-open")).to_be_focused()
        self.page.keyboard.press("Tab")
        expect(self.page.locator(".sidebar-close")).to_be_focused()
        self.page.keyboard.press("Escape")
        expect(menu).to_have_attribute("aria-expanded", "false")
        expect(menu).to_be_focused()
        self.assertTrue(self.page.locator("#app-sidebar").evaluate("el => el.inert"))
        for section in SECTIONS:
            with self.subTest(section=section):
                self.go(section)
                self.page.wait_for_timeout(100)
                dimensions = self.page.evaluate("""() => ({
                    viewport: document.documentElement.clientWidth,
                    document: document.documentElement.scrollWidth,
                    body: document.body.scrollWidth,
                })""")
                self.assertLessEqual(dimensions["document"], dimensions["viewport"] + 1, f"{section} causes viewport horizontal overflow: {dimensions}")
                self.assertLessEqual(dimensions["body"], dimensions["viewport"] + 1, f"{section} causes body horizontal overflow: {dimensions}")
                expect(menu).to_have_attribute("aria-expanded", "false")
                expect(self.page.locator(f"[data-tab='{section}']")).to_have_attribute("aria-current", "page")

    def test_missing_or_corrupt_saves_and_imports_leave_current_chart_intact(self):
        self.action("load")
        expect(self.page.locator("#workspace-toast")).to_have_text("No saved chart in this browser yet.")
        self.page.locator("#name").fill("Keep this chart")
        baseline = self.editable_values()
        for saved in ("{broken", json.dumps({"fields": {"name": {"value": "Must not replace"}}, "kundali": {"manual": True, "cells": []}})):
            with self.subTest(saved=saved):
                self.page.evaluate("value => localStorage.setItem('kpRaphaelData', value)", saved)
                self.action("load")
                expect(self.page.locator("#workspace-toast")).to_contain_text("Unable to load saved chart.")
                self.assertEqual(self.editable_values(), baseline, "Rejected save must not partially overwrite current inputs.")
        for invalid_file in ("not json", "{}", json.dumps({"fields": {"name": {"value": "Must not replace"}}, "eph": [["bad row"]]})):
            with self.subTest(invalid_file=invalid_file):
                self.import_file(invalid_file)
                expect(self.page.locator("#workspace-toast")).to_contain_text("Unable to import:")
                self.assertEqual(self.editable_values(), baseline, "Rejected import must leave current inputs unchanged.")
                expect(self.page.locator("#import-chart-file")).to_have_value("")

    def test_fourfold_sixfold_and_fourstep_significators_update_from_hidden_worksheets(self):
        expect(self.page.locator("#kp-status")).to_have_attribute("data-ready", "false")
        self.prepare_exact_kp_worksheets()
        expect(self.page.locator("main > #karyesh")).to_be_hidden()
        expect(self.page.locator("#kp-status")).to_have_attribute("data-ready", "true")
        for table in ("kp-fourfold-planet", "kp-sixfold-planet"):
            expect(self.page.locator(f"#{table} tbody tr[data-planet]")).to_have_count(9)
        for table in ("kp-fourfold-house", "kp-sixfold-house"):
            expect(self.page.locator(f"#{table} tbody tr[data-house]")).to_have_count(12)
        expect(self.page.locator("#kp-fourstep [data-planet]")).to_have_count(9)

        def field(table, planet, column):
            return self.page.locator(f'#{table} tbody tr[data-planet="{planet}"] [data-field="{column}"]')

        # Independent KP oracle: exact cusps at 0°,30°,...330°. Sun5°
        # occupies1, owns5, starKe occupies2 and ownsnone; subMa occupies3
        # and owns1,8. Rahu215° occupies8, its star/subSa occupies7 and
        # owns10,11. Ketu is derived35°, not a ninth ephemeris input.
        for table, planet, values in (
            ("kp-fourfold-planet", "Su", {"A": "2", "B": "1", "C": "—", "D": "5"}),
            ("kp-sixfold-planet", "Su", {"A": "3", "B": "2", "C": "1", "D": "1, 8", "E": "—", "F": "5"}),
            ("kp-fourfold-planet", "Ra", {"A": "7", "B": "8", "C": "10, 11", "D": "—"}),
            ("kp-sixfold-planet", "Ra", {"A": "7", "B": "7", "C": "8", "D": "10, 11", "E": "10, 11", "F": "—"}),
        ):
            for column, value in values.items():
                expect(field(table, planet, column)).to_have_text(value)
        expect(field("kp-fourfold-planet", "Ra", "CSL")).to_have_text("2, 6, 10")
        for step, lord in (("planet", "Su"), ("star", "Ke"), ("sub", "Ma"), ("sub-star", "Ma")):
            expect(self.page.locator(f'#kp-fourstep [data-planet="Su"] [data-step="{step}"]')).to_contain_text(lord)
        expect(self.page.locator('#kp-fourstep [data-planet="Su"] [data-step="planet"]')).to_contain_text("Nil")
        expect(self.page.locator('#kp-fourstep [data-planet="Su"] [data-step="sub"]')).to_contain_text("Own Star")

        # New source positions propagate while Tab8 is hidden, without the
        # Calculate button. Sun65° now occupies3; its starMa also occupies3
        # and owns1,8. A subsequent cusp edit moves Saturn from7 to6.
        self.page.locator("#p6_d_0").fill("65:00:00")
        self.page.locator("#p6_t_0").fill("65:00:00")
        for column, value in {"A": "3", "B": "3", "C": "1, 8", "D": "5"}.items():
            expect(field("kp-fourfold-planet", "Su", column)).to_have_text(value)
        self.go("raphael5")
        self.page.locator("#r5_large_1").fill("10:00:00")
        self.page.locator("#r5_small_1").fill("10:00:00")
        expect(field("kp-fourfold-planet", "Me", "A")).to_have_text("6")
        expect(self.page.locator("main > #karyesh")).to_be_hidden()
        snapshot_selector = "#kp-fourfold-planet,#kp-fourfold-house,#kp-sixfold-planet,#kp-sixfold-house,#kp-fourstep"
        expected_tables = self.page.locator(snapshot_selector).all_text_contents()
        self.action("save")
        self.go("planet")
        self.page.locator("#p6_d_0").fill("")
        expect(self.page.locator("#kp-status")).to_have_attribute("data-ready", "false")
        expect(field("kp-fourfold-planet", "Su", "A")).to_have_text("—")
        for table in ("kp-fourfold-planet", "kp-fourfold-house", "kp-sixfold-planet", "kp-sixfold-house"):
            values = self.page.locator(f"#{table} tbody [data-field]").all_text_contents()
            self.assertTrue(values and all(value.strip() == "—" for value in values),
                            "Incomplete worksheets must clear every stale significator value.")
        self.action("load")
        expect(self.page.locator("#workspace-toast")).to_have_text("Saved chart loaded and recalculated.")
        expect(self.page.locator("#kp-status")).to_have_attribute("data-ready", "true")
        expect(field("kp-fourfold-planet", "Su", "C")).to_have_text("1, 8")
        expect(field("kp-fourfold-planet", "Me", "A")).to_have_text("6")
        self.assertEqual(self.page.locator(snapshot_selector).all_text_contents(), expected_tables)
        self.go("karyesh")
        self.assertEqual(self.page.locator(snapshot_selector).all_text_contents(), expected_tables,
                         "Opening Tab8 must retain its already-calculated values.")

    def test_planetary_hour_minute_corrections_and_opposite_ketu_are_automatic(self):
        self.page.locator("#dob").fill("1990-06-15")
        self.page.locator("#birthTime").fill("13:11:00")
        self.go("planet")
        expect(self.page.locator("#p6_d_8:visible, #p6_t_8:visible")).to_have_count(0)
        expect(self.page.locator("#planet .planet6-table thead th")).to_have_count(9)
        self.page.locator("#p6_d_0").fill("20:00:00")
        self.page.locator("#p6_t_0").fill("21:00:00")
        # Independent angular oracle: 1 degree per day times 7 hours =
        # 17'30", plus 41 minutes = 1'42.5". Outputs round to arcseconds.
        expected = {
            "p6_motion_0": "1:00:00", "p6_hours_0": "0:17:30",
            "p6_minutes_0": "0:01:43", "p6_total_0": "0:19:13",
            "p6_birth_0": "20:00:00", "p6_add_0": "20:19:13",
            "p6_final_0": "20:19:13", "p6_rashi_0": "मेष",
        }
        for field, value in expected.items():
            expect(self.page.locator(f"#{field}")).to_have_value(value)
        for prefix in ("hours", "minutes"):
            self.assertTrue(self.page.locator(f"#p6_{prefix}_0").evaluate("field => field.readOnly"),
                            "Hourly and minute corrections are calculated outputs.")
        expect(self.page.locator("#p6-hours-label")).to_contain_text("7")
        expect(self.page.locator("#p6-minutes-label")).to_contain_text("41")

        # Rahu crosses 360 degrees without acquiring a spurious retrograde
        # daily motion. Ketu must always lie exactly 180 degrees opposite.
        self.page.locator("#p6_d_7").fill("359:50:00")
        self.page.locator("#p6_t_7").fill("0:50:00")
        expect(self.page.locator("#p6_motion_7")).to_have_value("1:00:00")
        expect(self.page.locator("#p6_final_7")).to_have_value("0:09:13")
        expect(self.page.locator("#p6_rashi_7")).to_have_value("मेष")
        expect(self.page.locator("#p6_final_8")).to_have_value("0:09:13")
        expect(self.page.locator("#p6_rashi_8")).to_have_value("तुला")
        self.go("south9")
        rahu = self.page.locator("#kundali .v38-planet").filter(has=self.page.locator(".v38-name", has_text="राहू"))
        ketu = self.page.locator("#kundali .v38-planet").filter(has=self.page.locator(".v38-name", has_text="केतू"))
        expect(rahu.locator(".v38-degree")).to_have_text("0°09′13″")
        expect(ketu.locator(".v38-degree")).to_have_text("0°09′13″")
        self.assertEqual(rahu.evaluate("row => Number(row.closest('[data-sign-index]').dataset.signIndex)"), 0)
        self.assertEqual(ketu.evaluate("row => Number(row.closest('[data-sign-index]').dataset.signIndex)"), 6)

        self.go("planet")
        self.page.locator("#p6_d_0").fill("21:00:00")
        self.page.locator("#p6_t_0").fill("20:00:00")
        expect(self.page.locator("#p6_motion_0")).to_have_value("1:00:00 R")
        expect(self.page.locator("#p6_total_0")).to_have_value("-0:19:13")
        expect(self.page.locator("#p6_final_0")).to_have_value("20:40:47 R")
        # At 04:00 the worksheet dates become preceding day, then DOB.
        # Enter 20° for that preceding day and 21° for DOB. A direct 1° daily
        # motion gives a negative 1h30 correction from the DOB 05:30 base.
        self.page.locator("#birthTime").evaluate("field => { field.value = '04:00:00'; field.dispatchEvent(new Event('input', {bubbles: true})); }")
        expect(self.page.locator("#p6_row_date_1")).to_have_value("1990-06-14")
        expect(self.page.locator("#p6_row_date_2")).to_have_value("1990-06-15")
        self.page.locator("#p6_d_0").fill("20:00:00")
        self.page.locator("#p6_t_0").fill("21:00:00")
        for field, value in {
            "p6_motion_0": "1:00:00", "p6_hours_0": "-0:02:30",
            "p6_minutes_0": "-0:01:15", "p6_total_0": "-0:03:45",
            "p6_birth_0": "21:00:00", "p6_final_0": "20:56:15",
        }.items():
            expect(self.page.locator(f"#{field}")).to_have_value(value)
        self.page.locator("#birthTime").evaluate("field => { field.value = '05:30:00'; field.dispatchEvent(new Event('input', {bubbles: true})); }")
        for prefix in ("hours", "minutes", "total"):
            expect(self.page.locator(f"#p6_{prefix}_0")).to_have_value("0:00:00")
        self.page.locator("#p6_d_7").fill("")
        for prefix in ("hours", "minutes", "total", "final", "rashi"):
            expect(self.page.locator(f"#p6_{prefix}_7")).to_have_value("")
            expect(self.page.locator(f"#p6_{prefix}_8")).to_have_value("")
        self.go("south9")
        expect(self.page.locator("#kundali .v38-name", has_text="केतू")).to_have_count(0)

    def test_basic_planet_and_house_calculations_appear_below_kundali_on_screen_and_report(self):
        self.prepare_exact_kp_worksheets()
        self.go("south9")
        planet_table = self.page.locator("#kp-basic-planet")
        house_table = self.page.locator("#kp-basic-house")
        expect(planet_table).to_be_visible()
        expect(house_table).to_be_visible()
        expect(planet_table.locator("tbody tr[data-planet]")).to_have_count(9)
        expect(house_table.locator("tbody tr[data-house]")).to_have_count(12)
        sun = planet_table.locator('tr[data-planet="Su"]')
        for column, value in {"signCode": "Ar", "degree": "5°00′00″", "nak": "Asw (2)", "occ": "1", "own": "5", "stl": "Ke", "sl": "Ma", "ssl": "Ju", "cstl": "2, 6, 10"}.items():
            expect(sun.locator(f'[data-field="{column}"]')).to_have_text(value)
        ketu = planet_table.locator('tr[data-planet="Ke"]')
        expect(ketu.locator('[data-field="occ"]')).to_have_text("2")
        expect(ketu.locator('[data-field="own"]')).to_have_text("—")

        def assert_placement(target, chart_selector, planet_selector, house_selector, printed=False):
            positions = target.evaluate("""({chartSelector, planetSelector, houseSelector, printed}) => {
                const chart = document.querySelector(chartSelector), planet = document.querySelector(planetSelector), house = document.querySelector(houseSelector);
                const box = element => { const r = element.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:r.width,height:r.height}; };
                const page = printed ? chart.closest('.report-page') : null;
                return {chart:box(chart),planet:box(planet),house:box(house),page:page?box(page):null,
                    visible:[chart,planet,house].every(element => getComputedStyle(element).display !== 'none' && element.getBoundingClientRect().height > 0)};
            }""", {"chartSelector": chart_selector, "planetSelector": planet_selector, "houseSelector": house_selector, "printed": printed})
            self.assertTrue(positions["visible"], "The chart and both calculation tables must be visible.")
            self.assertGreaterEqual(positions["planet"]["top"], positions["chart"]["bottom"] - 1, positions)
            self.assertGreaterEqual(positions["house"]["top"], positions["planet"]["bottom"] - 1, positions)
            if printed:
                for key in ("chart", "planet", "house"):
                    self.assertLessEqual(positions[key]["bottom"], positions["page"]["bottom"] + 1,
                                         f"{key} is clipped outside its printable A4 page: {positions}")
                    self.assertGreaterEqual(positions[key]["left"], positions["page"]["left"] - 1)
                    self.assertLessEqual(positions[key]["right"], positions["page"]["right"] + 1)

        assert_placement(self.page, "#kundali", "#kp-basic-planet", "#kp-basic-house")
        self.page.set_viewport_size({"width": 390, "height": 844})
        assert_placement(self.page, "#kundali", "#kp-basic-planet", "#kp-basic-house")
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 391,
                             "Wide calculation tables must scroll inside their mobile container.")
        self.page.set_viewport_size({"width": 1280, "height": 900})
        self.page.evaluate("""() => {
            const original = window.open;
            window.open = function (...args) {
                const popup = original.apply(window, args);
                if (popup) popup.print = () => { popup.testPrintCalled = true; };
                return popup;
            };
        }""")
        with self.page.expect_popup() as popup_info:
            self.page.evaluate("window.printReport()")
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Basic calculation report: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        popup.emulate_media(media="print")
        printed_planets = popup.locator('[data-report-id="kp-basic-planet"]')
        printed_houses = popup.locator('[data-report-id="kp-basic-house"]')
        expect(printed_planets.locator("tbody tr[data-planet]")).to_have_count(9)
        expect(printed_houses.locator("tbody tr[data-house]")).to_have_count(12)
        expect(printed_planets.locator('tr[data-planet="Su"] [data-field="ssl"]')).to_have_text("Ju")
        assert_placement(popup, '[data-report-id="kundali"]', '[data-report-id="kp-basic-planet"]', '[data-report-id="kp-basic-house"]', printed=True)
        popup.close()

    def test_dense_kundali_lanes_keep_labels_and_degrees_visible_on_screen_and_print(self):
        self.go("south9")
        self.page.wait_for_timeout(500)
        # Isolate rendering from worksheet recomputation: stress fixtures place
        # all 12 cusps and all 9 planets at the same degree in one sign. Keep
        # the real chart renderer, report snapshot, popup and print styles.
        self.page.evaluate("""() => {
            window.calculateAll = () => {};
            window.updateKaryeshTables = () => {};
            const originalOpen = window.open;
            window.open = function (...args) {
                const popup = originalOpen.apply(window, args);
                if (popup) popup.print = () => { popup.testPrintCalled = true; };
                return popup;
            };
        }""")

        def assert_geometry(target, chart_selector, sign, degree_text):
            cell = target.locator(f"{chart_selector} .v38-cell[data-sign-index='{sign}']")
            expect(cell.locator(".v38-cusp")).to_have_count(12)
            expect(cell.locator(".v38-planet")).to_have_count(9)
            geometry_errors = cell.evaluate("""cell => {
                const errors = [], bounds = cell.getBoundingClientRect();
                const midpoint = (bounds.left + bounds.right) / 2, tolerance = 0.6;
                const entries = [...cell.querySelectorAll('.v38-item')], allTextRects = [];
                const overlaps = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > tolerance &&
                    Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > tolerance;
                const inside = (inner, outer) => inner.left >= outer.left - tolerance && inner.right <= outer.right + tolerance &&
                    inner.top >= outer.top - tolerance && inner.bottom <= outer.bottom + tolerance;
                for (const entry of entries) {
                    const rect = entry.getBoundingClientRect(), kind = entry.dataset.kind;
                    const description = `${kind}: ${entry.textContent}`;
                    if (kind !== 'cusp' && kind !== 'planet') errors.push(`Missing kind: ${description}`);
                    if (!inside(rect, bounds) || rect.width <= 0 || rect.height <= 0) errors.push(`Entry outside cell: ${description}`);
                    if (kind === 'cusp' && rect.right > midpoint + tolerance) errors.push(`Cusp outside left lane: ${description}`);
                    if (kind === 'planet' && rect.left < midpoint - tolerance) errors.push(`Planet outside right lane: ${description}`);
                    const textRects = [];
                    for (const selector of ['.v38-name', '.v38-degree']) {
                        const label = entry.querySelector(selector);
                        if (!label || !label.textContent.trim()) { errors.push(`Missing ${selector}: ${description}`); continue; }
                        const range = document.createRange(); range.selectNodeContents(label);
                        const labelRect = range.getBoundingClientRect();
                        const style = getComputedStyle(label);
                        // Font ascenders can extend outside a short line box
                        // when overflow is visible. Check their actual painted
                        // range against the cell and their horizontal lane.
                        if (!inside(labelRect, bounds) || labelRect.left < rect.left - tolerance || labelRect.right > rect.right + tolerance ||
                            labelRect.width <= 0 || labelRect.height <= 0 || style.visibility === 'hidden' || style.display === 'none' ||
                            (getComputedStyle(entry).overflow !== 'visible' && !inside(labelRect, rect)))
                            errors.push(`Clipped ${selector}: ${description}`);
                        textRects.push(labelRect);
                        allTextRects.push({rect: labelRect, entry, description});
                    }
                    if (textRects.length === 2 && overlaps(...textRects)) errors.push(`Name overlaps degree: ${description}`);
                }
                for (let i = 0; i < entries.length; i++) for (let j = i + 1; j < entries.length; j++)
                    if (overlaps(entries[i].getBoundingClientRect(), entries[j].getBoundingClientRect()))
                        errors.push(`Overlapping entries: ${entries[i].textContent} / ${entries[j].textContent}`);
                for (let i = 0; i < allTextRects.length; i++) for (let j = i + 1; j < allTextRects.length; j++)
                    if (allTextRects[i].entry !== allTextRects[j].entry && overlaps(allTextRects[i].rect, allTextRects[j].rect))
                        errors.push(`Overlapping glyphs: ${allTextRects[i].description} / ${allTextRects[j].description}`);
                return errors;
            }""")
            self.assertEqual(geometry_errors, [], "\n".join(geometry_errors))
            degrees = cell.locator(".v38-degree").all_text_contents()
            self.assertEqual(len(degrees), 21)
            self.assertTrue(all(value.startswith(degree_text) for value in degrees), degrees)
            self.assertEqual(cell.locator(".v38-planet .v38-name").all_text_contents(),
                             ["रवी", "चंद्र", "मंगळ", "बुध", "गुरु", "शुक्र", "शनि", "राहू", "केतू"])

        # Both ends of each degree direction exercise the previous collision
        # and bottom-clamping bug, including the opposite Pisces orientation.
        for sign, local_seconds in ((0, 0), (0, 107999), (11, 0), (11, 107999)):
            degree_text = "0°00′00″" if local_seconds == 0 else "29°59′59″"
            with self.subTest(sign=sign, degree=degree_text):
                self.page.set_viewport_size({"width": 1280, "height": 900})
                self.page.evaluate("""({sign, localSeconds}) => {
                    const longitude = sign * 108000 + localSeconds;
                    const planets = ['रवी', 'चंद्र', 'मंगळ', 'बुध', 'गुरु', 'शुक्र', 'शनि', 'राहू', 'केतू'];
                    window.cuspResults = Array.from({length: 12}, (_, i) => ({i: i + 1, nir: longitude}));
                    window.lastPlanetPositions = Object.fromEntries(planets.map(planet => [planet, longitude]));
                    window.kundaliManual = false;
                    window.renderChart(true);
                }""", {"sign": sign, "localSeconds": local_seconds})
                assert_geometry(self.page, "#kundali", sign, degree_text)
                self.page.set_viewport_size({"width": 390, "height": 844})
                assert_geometry(self.page, "#kundali", sign, degree_text)
                self.page.set_viewport_size({"width": 1280, "height": 900})
                with self.page.expect_popup() as popup_info:
                    self.page.evaluate("window.printReport()")
                popup = popup_info.value
                popup.on("pageerror", lambda error: self.errors.append("Dense chart print popup: " + str(error)))
                popup.wait_for_load_state("domcontentloaded")
                popup.wait_for_function("window.testPrintCalled === true")
                popup.emulate_media(media="print")
                assert_geometry(popup, '[data-report-id="kundali"]', sign, degree_text)
                popup.close()

    def test_report_front_page_shows_native_and_astrologer_details_as_literal_text(self):
        self.prepare_worksheets()
        self.page.evaluate("source => { window.KP_REPORT_COVER_IMAGE = source; }", COVER_IMAGE_FIXTURE)
        native_name = 'मीरा <img src=x onerror="window.coverInjected=true">'
        astrologer_name = 'Astrologer <script>window.coverInjected=true</script>'
        astrologer_address = 'Pune office\nSecond floor <b>Address</b>\nMaharashtra'
        self.go("basic")
        self.page.locator("#name").fill(native_name)
        self.page.locator("#birthPlace").fill("Pune <b>India</b>")
        self.go("astrosettings")
        self.page.locator("#astroName").fill(astrologer_name)
        self.page.locator("#astroAddress").fill(astrologer_address)
        self.go("report")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
        cover = self.page.locator("#printReport > .report-page").first
        expect(cover).to_have_attribute("data-report-section", "cover")
        expect(cover).to_contain_text("Ucchishta Mahaganpati")
        photo = cover.locator('.report-cover-image[data-report-image="ganpati"]')
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        photo.evaluate("image => image.decode()")
        self.assertGreater(photo.evaluate("image => image.naturalWidth"), 0)
        self.assertEqual(photo.evaluate("image => getComputedStyle(image).objectFit"), "contain")
        for field, expected in (
            ("name", native_name), ("birthTime", "12:30:00"), ("birthPlace", "Pune <b>India</b>"),
            ("lat", "18:31:00"), ("lon", "73:51:00"),
            ("astroName", astrologer_name), ("astroMobile", "1234567890"),
            ("astroAddress", astrologer_address),
        ):
            with self.subTest(cover_field=field):
                expect(cover.locator(f'[data-cover-field="{field}"]')).to_have_text(expected)
        expect(cover.locator('[data-cover-field="dob"]')).to_have_text("1990-06-15")
        self.assertEqual(cover.locator("script, img[src='x'], [data-cover-field] b").count(), 0)
        self.assertFalse(self.page.evaluate("window.coverInjected === true"))
        self.assertEqual(cover.locator('[data-cover-field="astroAddress"]').evaluate(
            "element => getComputedStyle(element).whiteSpace"), "pre-wrap")
        expect(self.page.locator("#printReport > .report-page").nth(1)).to_have_attribute("data-report-section", "basic")
        expect(self.page.locator("#printReport > .report-page").last).to_have_attribute("data-report-section", "south9")

        self.go("basic")
        self.page.locator("#name").fill("")
        self.go("astrosettings")
        self.page.locator("#astroAddress").fill("")
        self.go("report")
        cover = self.page.locator(".report-front-page")
        expect(cover.locator('[data-cover-field="name"]')).to_have_text("—")
        expect(cover.locator('[data-cover-field="astroAddress"]')).to_have_text("—")

    def test_selected_cover_photo_survives_backups_printing_and_offline_single_file_use(self):
        self.prepare_worksheets()
        self.go("report")
        photo_input = self.page.locator("#report-cover-photo-input")
        status = self.page.locator("#report-cover-photo-status")
        self.assertEqual(photo_input.locator("xpath=ancestor::main").count(), 0,
                         "The image picker must not enter the chart's generic field serialization.")
        expect(self.page.locator("#choose-report-cover-photo")).to_be_visible()
        expect(self.page.locator("#download-cover-software")).to_have_count(0)
        expect(self.page.get_by_role("button", name="Download software with photo")).to_have_count(0)
        self.assertFalse(self.page.evaluate("Boolean(window.KPReportPhoto?.download)"),
                         "The removed software-download option must not remain available through its old API.")
        original_bytes = base64.b64decode(COVER_IMAGE_FIXTURE.split(",", 1)[1])
        photo_input.set_input_files({
            "name": "ganpati-test.png", "mimeType": "image/png", "buffer": original_bytes,
        })
        expect(status).to_have_attribute("data-ready", "true")
        photo = self.page.locator(".report-front-page .report-cover-image")
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        photo.evaluate("image => image.decode()")
        self.assertEqual(base64.b64decode(photo.get_attribute("src").split(",", 1)[1]), original_bytes,
                         "The selected photo must retain its original bytes rather than be redrawn or regenerated.")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
        self.assertEqual(self.page.evaluate("localStorage.getItem('kpReportCoverPhoto')"), COVER_IMAGE_FIXTURE)
        self.action("save")

        self.page.reload(wait_until="load")
        self.page.wait_for_timeout(1700)
        self.go("report")
        photo = self.page.locator(".report-front-page .report-cover-image")
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        self.action("load")
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        expect(self.page.locator('[data-cover-field="name"]')).to_have_text("Regression chart · मीरा")

        with self.page.expect_download() as backup_info:
            self.action("export")
        exported = json.loads(Path(backup_info.value.path()).read_text(encoding="utf-8"))
        self.assertEqual(exported["coverPhoto"], COVER_IMAGE_FIXTURE,
                         "A portable chart backup must include the selected cover photograph.")
        self.assertNotIn("report-cover-photo-input", exported["fields"])
        baseline_fields = self.editable_values()
        invalid_backup = json.loads(json.dumps(exported))
        invalid_backup["fields"]["name"]["value"] = "Rejected replacement"
        invalid_backup["coverPhoto"] = '<img src=x onerror="window.photoInjected=true">'
        self.import_file(json.dumps(invalid_backup))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Unable to import:")
        self.assertEqual(self.editable_values(), baseline_fields,
                         "An invalid cover image must reject the complete import before changing native data.")
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        self.assertFalse(self.page.evaluate("window.photoInjected === true"))

        # A standards-compliant ancillary PNG text chunk makes a valid local
        # photo large enough to exercise the backup import's previous 1 MiB cap.
        metadata = b"Comment\x00" + b"A" * 900_000
        chunk = b"tEXt" + metadata
        large_bytes = (original_bytes[:-12] + struct.pack(">I", len(metadata)) + chunk
                       + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF) + original_bytes[-12:])
        large_photo = "data:image/png;base64," + base64.b64encode(large_bytes).decode("ascii")
        large_backup = json.loads(json.dumps(exported))
        large_backup["coverPhoto"] = large_photo
        large_json = json.dumps(large_backup)
        self.assertGreater(len(large_json.encode("utf-8")), 1024 * 1024)
        self.import_file(large_json)
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(photo).to_have_attribute("src", large_photo)
        photo.evaluate("image => image.decode()")

        cleared_backup = json.loads(json.dumps(exported))
        cleared_backup["coverPhoto"] = ""
        self.import_file(json.dumps(cleared_backup))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(photo).to_be_hidden()
        self.import_file(json.dumps(exported))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        expect(photo).to_be_visible()

        for file_name, mime_type, bad_bytes, error in (
            ("not-a-photo.jpg", "image/jpeg", b"This file is not a JPEG image.",
             "This file is not a valid PNG, JPG or WebP photo."),
            ("unreadable.jpg", "image/jpeg", b"\xff\xd8This JPEG header has no real image.\xff\xd9",
             "This image cannot be read. Choose a valid PNG, JPG or WebP photo."),
            ("notes.txt", "text/plain", b"These are notes, not a cover photo.",
             "Choose a PNG, JPG or WebP cover photo."),
        ):
            with self.subTest(rejected_photo=file_name):
                photo_input.set_input_files({"name": file_name, "mimeType": mime_type, "buffer": bad_bytes})
                expect(self.page.locator("#workspace-toast")).to_have_text(error)
                expect(self.page.locator("#workspace-toast")).to_have_attribute("data-type", "error")
                expect(photo_input).to_have_value("")
                expect(photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
                expect(photo).to_be_visible()
                self.assertEqual(self.page.evaluate("localStorage.getItem('kpReportCoverPhoto')"), COVER_IMAGE_FIXTURE)

        self.page.evaluate("""() => {
            const original = window.open;
            window.open = function (...args) {
                const popup = original.apply(window, args);
                if (popup) popup.print = () => { popup.testPrintCalled = true; };
                return popup;
            };
        }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Selected-photo print: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
        printed_photo = popup.locator(".report-front-page .report-cover-image")
        expect(printed_photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        printed_photo.evaluate("image => image.decode()")
        popup.close()

        with tempfile.TemporaryDirectory(prefix="kp-photo-standalone-test-") as directory:
            standalone = Path(directory) / "index.html"
            shutil.copyfile(REPOSITORY / "index.html", standalone)
            self.assertEqual(list(Path(directory).iterdir()), [standalone])
            handler = functools.partial(QuietHandler, directory=directory)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            context = self.browser.new_context(viewport={"width": 1280, "height": 900})
            isolated_url = f"http://127.0.0.1:{server.server_port}/index.html"
            unexpected_requests = []

            def allow_only_html(route):
                if route.request.url == isolated_url:
                    route.continue_()
                else:
                    unexpected_requests.append(route.request.url)
                    route.abort()

            context.route("**/*", allow_only_html)
            try:
                page = context.new_page()
                page.on("pageerror", lambda error: self.errors.append("Offline photo software: " + str(error)))
                page.goto(isolated_url, wait_until="load")
                page.wait_for_timeout(1700)
                context.set_offline(True)
                page.locator(".backup-menu > summary").click()
                page.locator(".global-actions [data-action='import']").click()
                page.locator("#import-chart-file").set_input_files({
                    "name": "chart-with-photo.json", "mimeType": "application/json",
                    "buffer": json.dumps(exported, ensure_ascii=False).encode("utf-8"),
                })
                expect(page.locator("#workspace-toast")).to_contain_text("Chart imported.")
                page.locator(".app-sidebar [data-tab='report']").click()
                expect(page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
                offline_photo = page.locator(".report-front-page .report-cover-image")
                expect(offline_photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
                offline_photo.evaluate("image => image.decode()")
                self.assertGreater(offline_photo.evaluate("image => image.naturalWidth"), 0)
                for field, expected in (
                    ("name", "Regression chart · मीरा"), ("dob", "1990-06-15"),
                    ("astroName", "Test Astrologer"), ("astroMobile", "1234567890"),
                    ("astroAddress", "Pune\nClient report office"),
                ):
                    with self.subTest(offline_cover_field=field):
                        expect(page.locator(f'[data-cover-field="{field}"]')).to_have_text(expected)
                page.locator(".app-sidebar [data-tab='basic']").click()
                page.locator("#birthTime").fill("13:30:00")
                page.locator(".global-actions [data-action='calculate']").click()
                expect(page.locator("#workspace-toast")).to_contain_text("Chart calculations updated.")
                page.locator(".global-actions [data-action='save']").click()
                expect(page.locator("#save-state")).to_have_text("Saved in this browser")
                page.locator("#name").fill("Temporary offline edit")
                page.locator(".global-actions [data-action='load']").click()
                expect(page.locator("#name")).to_have_value("Regression chart · मीरा")
                expect(page.locator("#birthTime")).to_have_value("13:30:00")
                page.set_viewport_size({"width": 390, "height": 844})
                menu = page.locator("#menu-toggle")
                menu.click()
                expect(menu).to_have_attribute("aria-expanded", "true")
                page.locator(".app-sidebar [data-tab='report']").click()
                expect(menu).to_have_attribute("aria-expanded", "false")
                expect(page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
                expect(page.locator('.report-front-page [data-cover-field="birthTime"]')).to_have_text("13:30:00")
                expect(page.locator(".report-front-page .report-cover-image")).to_have_attribute("src", COVER_IMAGE_FIXTURE)
                self.assertEqual(unexpected_requests, [],
                                 "The copied software and cover photo must work without sibling files or network assets.")
            finally:
                context.close()
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

    def test_print_popup_has_thirteen_a4_pages_without_duplicate_ids(self):
        self.prepare_worksheets()
        self.page.evaluate("source => { window.KP_REPORT_COVER_IMAGE = source; }", COVER_IMAGE_FIXTURE)
        self.go("report")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
        # Stub the print dialog on the actual newly opened window, before the
        # app's deferred print call; still exercise popup creation and rendering.
        self.page.evaluate("""() => {
            const original = window.open;
            window.open = function (...args) {
                const popup = original.apply(window, args);
                if (popup) popup.print = () => { popup.testPrintCalled = true; };
                return popup;
            };
        }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Print popup: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))
        expect(popup.locator("body > .report-page").first).to_have_attribute("data-report-section", "cover")
        expect(popup.locator("body > .report-page").first).to_contain_text("Regression chart · मीरा")
        expect(popup.locator("body > .report-page").first).to_contain_text("Test Astrologer")
        expect(popup.locator("body > .report-page").first).to_contain_text("Client report office")
        for target, label in ((self.page, "calculator"), (popup, "print popup")):
            duplicates = target.evaluate("""() => {
                const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
                return [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
            }""")
            self.assertEqual(duplicates, [], f"Duplicate IDs in {label}: {duplicates}")
        popup.emulate_media(media="print")
        expect(popup.locator(".report-front-heading")).to_be_visible()
        expect(popup.locator(".report-front-heading h1")).to_be_visible()
        expect(popup.locator(".report-front-heading")).to_contain_text("Ucchishta Mahaganpati")
        printed_photo = popup.locator('.report-front-page .report-cover-image[data-report-image="ganpati"]')
        expect(printed_photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        printed_photo.evaluate("image => image.decode()")
        self.assertEqual(printed_photo.evaluate("image => getComputedStyle(image).objectFit"), "contain")
        image_height = printed_photo.bounding_box()["height"]
        self.assertGreaterEqual(image_height, 100 * 96 / 25.4, "The devotional image should remain prominent on the cover.")
        self.assertLessEqual(image_height, 132 * 96 / 25.4 + 1, "The image must leave room for the native and astrologer details.")
        cover_overflow = popup.locator(".report-front-page").evaluate("""page => ({
            width: page.scrollWidth - page.clientWidth,
            height: page.scrollHeight - page.clientHeight
        })""")
        self.assertLessEqual(cover_overflow["width"], 1, "The cover must not overflow the printable page horizontally.")
        self.assertLessEqual(cover_overflow["height"], 1, "The cover must not overflow the printable page vertically.")
        page_geometry = popup.locator("body > .report-page").evaluate_all("""pages => pages.map(page => {
            const style = getComputedStyle(page);
            return {width: parseFloat(style.width), height: parseFloat(style.height), display: style.display, breakAfter: style.breakAfter};
        })""")
        for index, geometry in enumerate(page_geometry):
            with self.subTest(print_page=index + 1):
                self.assertNotEqual(geometry["display"], "none", "Every report page must be visible when printing.")
                self.assertAlmostEqual(geometry["width"], 190 * 96 / 25.4, delta=1)
                self.assertAlmostEqual(geometry["height"], 277 * 96 / 25.4, delta=1)
                if index < len(REPORT_PAGE_SECTIONS) - 1:
                    self.assertEqual(geometry["breakAfter"], "page")
        content_errors = popup.locator("body > .report-page").evaluate_all("""pages => pages.flatMap((page, index) => {
            const bounds = page.getBoundingClientRect(), errors = [];
            for (const element of page.querySelectorAll('.report-developer-footer,.kp-key,.kp-table,[data-cover-field],.report-cover-image,.report-front-heading,.report-front-footnote,.md-dasha-table,.ad-sheet table,.ad-sheet [data-report-id]')) {
                const rect = element.getBoundingClientRect();
                if (getComputedStyle(element).display === 'none' || rect.width <= 0 || rect.height <= 0)
                    errors.push(`Page ${index+1}: hidden ${element.className}`);
                else if (rect.top < bounds.top-1 || rect.bottom > bounds.bottom+1 || rect.left < bounds.left-1 || rect.right > bounds.right+1)
                    errors.push(`Page ${index+1}: clipped ${element.className} (${rect.top},${rect.bottom}) outside (${bounds.top},${bounds.bottom})`);
            }
            return errors;
        })""")
        self.assertEqual(content_errors, [], "Cover details, report tables, legends and developer footers must fit their printed A4 pages.")
        paper_sizes = popup.evaluate("""() => [...document.styleSheets].flatMap(sheet => [...sheet.cssRules])
            .filter(rule => rule.constructor.name === 'CSSPageRule').map(rule => rule.style.size.toLowerCase())""")
        # Chromium normalizes explicit "A4 portrait" to "a4", whose default
        # orientation is portrait; the page dimensions above also enforce it.
        self.assertIn(paper_sizes[-1], ("a4", "a4 portrait"), "The print document must request A4 portrait paper.")

    def test_report_page_selection_prints_only_checked_pages_and_preserves_report_order(self):
        self.prepare_worksheets()
        self.page.locator(".backup-menu > summary").click()
        self.page.locator(".global-actions [data-action='print']").click()
        expect(self.page.locator("main > #report")).to_be_visible()
        expect(self.page.locator("#report-page-options")).to_be_focused()
        self.assertEqual(len(self.context.pages), 1,
                         "The global print action must let the user choose pages before it opens a print window.")
        options = self.page.locator("#report-page-options input[type='checkbox'][data-report-page-key]")
        expect(options).to_have_count(len(REPORT_PAGE_SECTIONS))
        actual_sections = options.evaluate_all("options => options.map(option => option.dataset.reportPageKey)")
        self.assertEqual(actual_sections, list(REPORT_PAGE_SECTIONS),
                         "The page choices must include the current MD and AD report pages in preview order.")
        self.assertTrue(options.evaluate_all("options => options.every(option => option.checked)"),
                        "Printing the full report must remain the default.")
        self.page.locator("#report-clear-pages").click()
        selected_sections = ["cover", "mdcalc", "adcalc", "south9"]
        for section in reversed(selected_sections):
            self.page.locator(f"#report-page-options [data-report-page-key='{section}']").check()
        self.page.evaluate("window.renderReport()")
        expect(options).to_have_count(len(REPORT_PAGE_SECTIONS))
        self.assertEqual(options.evaluate_all("options => options.filter(option => option.checked).map(option => option.dataset.reportPageKey)"),
                         selected_sections, "Refreshing report data must preserve the selected pages.")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(len(REPORT_PAGE_SECTIONS))

        self.page.evaluate("""() => {
            const original = window.open;
            window.testPopupCalls = 0;
            window.open = function (...args) {
                window.testPopupCalls++;
                const popup = original.apply(window, args);
                if (popup) popup.print = () => { popup.testPrintCalled = true; };
                return popup;
            };
        }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Selected-pages print: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        pages = popup.locator("body > .report-page")
        expect(pages).to_have_count(len(selected_sections))
        self.assertEqual(pages.evaluate_all("pages => pages.map(page => page.dataset.reportSection)"),
                         selected_sections, "Click order must not reorder printed report pages.")
        popup.emulate_media(media="print")
        for page in pages.all():
            expect(page).to_be_visible()
        self.assertIn(pages.last.evaluate("page => getComputedStyle(page).breakAfter"), ("auto", "avoid"),
                      "The last selected page must not force an extra blank sheet.")
        expect(popup.locator('[data-report-section="adcalc"] [data-report-id="adDashaRows"] tr')).to_have_count(9)
        popup.close()
        self.assertEqual(self.page.evaluate("window.testPopupCalls"), 1)

        self.page.locator("#report-clear-pages").click()
        self.page.locator("#print-selected-report").click()
        expect(self.page.locator("#report-page-selection-status")).to_have_text("Select at least one page to print.")
        self.assertEqual(self.page.evaluate("window.testPopupCalls"), 1,
                         "An empty page selection must not open or print a blank document.")
        self.page.locator("#report-select-all").click()
        self.assertTrue(options.evaluate_all("options => options.every(option => option.checked)"))
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.locator("#report-clear-pages").click()
        self.page.locator("#report-page-options [data-report-page-key='adcalc']").check()
        expect(self.page.locator("#report-page-selection-status")).to_contain_text("1")
        dimensions = self.page.evaluate("""() => ({
            viewport: document.documentElement.clientWidth,
            document: document.documentElement.scrollWidth,
            body: document.body.scrollWidth,
        })""")
        self.assertLessEqual(dimensions["document"], dimensions["viewport"] + 1)
        self.assertLessEqual(dimensions["body"], dimensions["viewport"] + 1)

    def test_antardasha_matches_known_ketu_sequence_and_full_md_duration(self):
        self.prepare_exact_dasha()
        expect(self.page.locator("#mdBirthDasha")).to_have_value("केतू")
        expect(self.page.locator("#mdBhogyaDuration")).to_have_value("7 वर्ष 0 महिने 0 दिवस")
        expect(self.page.locator("#adMDSelect")).to_have_count(1)
        expect(self.page.locator("#adMDSelect option")).to_have_count(9)
        expect(self.page.locator("#adBirthLord")).to_have_value("केतू")
        expect(self.page.locator("#adBirthBalance")).to_have_value("0 वर्ष 4 महिने 27 दिवस")
        expected = [
            ["केतू", "0", "4", "27", "01/01/2000", "28/05/2000"],
            ["शुक्र", "1", "2", "0", "28/05/2000", "28/07/2001"],
            ["रवी", "0", "4", "6", "28/07/2001", "04/12/2001"],
            ["चंद्र", "0", "7", "0", "04/12/2001", "04/07/2002"],
            ["मंगळ", "0", "4", "27", "04/07/2002", "01/12/2002"],
            ["राहू", "1", "0", "18", "01/12/2002", "19/12/2003"],
            ["गुरु", "0", "11", "6", "19/12/2003", "25/11/2004"],
            ["शनि", "1", "1", "9", "25/11/2004", "04/01/2006"],
            ["बुध", "0", "11", "27", "04/01/2006", "01/01/2007"],
        ]
        self.assertEqual(self.dasha_rows(), expected,
                         "AD must use the Vimshottari sequence and MD × AD years ÷ 120, with cumulative calendar boundaries.")
        durations = [int(row[1]) * 360 + int(row[2]) * 30 + int(row[3]) for row in self.dasha_rows()]
        self.assertEqual(durations, [147, 420, 126, 210, 147, 378, 336, 399, 357])
        self.assertEqual(sum(durations), 7 * 360, "The nine AD durations must cover exactly their complete Ketu MD.")
        md_table = self.page.locator("#mdDashaRows").locator("xpath=ancestor::table")
        ad_table = self.page.locator("#adDashaRows").locator("xpath=ancestor::table")
        self.assertIn("md-dasha-table", ad_table.get_attribute("class").split())
        self.assertEqual(ad_table.locator("thead th").all_text_contents(), md_table.locator("thead th").all_text_contents(),
                         "The AD worksheet must retain the MD table's six-column format.")

        self.page.locator("#adMDSelect").select_option(index=1)
        venus_rows = self.dasha_rows()
        self.assertEqual([row[0] for row in venus_rows], ["शुक्र", "रवी", "चंद्र", "मंगळ", "राहू", "गुरु", "शनि", "बुध", "केतू"])
        self.assertEqual(venus_rows[0][1:4], ["3", "4", "0"])
        self.assertEqual(venus_rows[0][4], "01/01/2007")
        self.assertEqual(venus_rows[-1][5], "01/01/2027")
        self.assertEqual(sum(int(row[1]) * 360 + int(row[2]) * 30 + int(row[3]) for row in venus_rows), 20 * 360)
        self.go("report")
        report_ad = self.page.locator('#printReport > [data-report-section="adcalc"]')
        expect(report_ad).to_have_count(1)
        self.assertEqual(report_ad.locator('[data-report-id="adDashaRows"]').evaluate("""body => [...body.rows].map(row =>
            [...row.cells].map(cell => cell.textContent.trim()))"""), venus_rows,
                         "The AD report page must print the currently chosen MD's recalculated table.")
        expect(self.page.locator('#printReport > [data-report-section="mdcalc"] [data-report-id="adDashaRows"]')).to_have_count(0)

    def test_birth_antardasha_uses_elapsed_md_and_changes_at_exact_nakshatra_boundaries(self):
        self.prepare_exact_dasha("06:40:00")
        expect(self.page.locator("#mdBhogyaDuration")).to_have_value("3 वर्ष 6 महिने 0 दिवस")
        expect(self.page.locator("#adBirthLord")).to_have_value("राहू")
        expect(self.page.locator("#adBirthBalance")).to_have_value("0 वर्ष 5 महिने 18 दिवस")
        active = self.page.locator('#adDashaRows tr[data-birth-active="true"]')
        expect(active).to_have_count(1)
        expect(active).to_have_attribute("data-ad-lord", "राहू")
        expect(active.locator(".ad-birth-marker")).to_have_text("जन्मतः / At birth")
        rows = self.dasha_rows()
        self.assertEqual(rows[0][4], "01/07/1996", "A partly elapsed birth MD must begin before the native's birth.")
        self.assertEqual(rows[5][4:6], ["01/06/1999", "19/06/2000"])
        self.assertEqual(rows[-1][5], "01/07/2003")
        self.assertEqual(rows[-1][5], self.page.locator("#mdDashaEnd").input_value())
        periods = self.page.evaluate("window.calculateAntardashas(window.mdDashaPeriods[0])")
        self.assertTrue(all(periods[index]["end"] == periods[index + 1]["start"] for index in range(8)),
                        "Adjacent AD periods must meet without a gap or overlap.")

        # 3°40′ of Ashwini is exactly 693 of 2520 Ketu-MD days:
        # Ketu 147 + Venus 420 + Sun 126. The new Moon AD begins at birth.
        self.go("planet")
        self.page.locator("#p6_d_1").fill("03:40:00")
        self.page.locator("#p6_t_1").fill("03:40:00")
        self.action("calculate")
        self.go("mdcalc")
        expect(self.page.locator("#adBirthLord")).to_have_value("चंद्र")
        expect(self.page.locator("#adBirthBalance")).to_have_value("0 वर्ष 7 महिने 0 दिवस")
        self.assertEqual(self.dasha_rows()[3][4], "01/01/2000",
                         "At an exact AD boundary, the new period must start on the birth date.")
        self.go("planet")
        self.page.locator("#p6_d_1").fill("13:20:00")
        self.page.locator("#p6_t_1").fill("13:20:00")
        self.action("calculate")
        self.go("mdcalc")
        expect(self.page.locator("#mdBirthDasha")).to_have_value("शुक्र")
        expect(self.page.locator("#mdBhogyaDuration")).to_have_value("20 वर्ष 0 महिने 0 दिवस")
        expect(self.page.locator("#adBirthLord")).to_have_value("शुक्र")
        expect(self.page.locator("#adBirthBalance")).to_have_value("3 वर्ष 4 महिने 0 दिवस")
        self.assertEqual(self.dasha_rows()[0][4], "01/01/2000")
        self.page.set_viewport_size({"width": 390, "height": 844})
        dimensions = self.page.evaluate("""() => ({
            viewport: document.documentElement.clientWidth,
            document: document.documentElement.scrollWidth,
            body: document.body.scrollWidth,
        })""")
        self.assertLessEqual(dimensions["document"], dimensions["viewport"] + 1)
        self.assertLessEqual(dimensions["body"], dimensions["viewport"] + 1)

    def test_antardasha_clears_incomplete_inputs_and_keeps_calendar_dates_across_timezones(self):
        self.prepare_exact_dasha()
        baseline = self.dasha_rows()
        self.go("basic")
        self.page.locator("#dob").fill("")
        self.go("mdcalc")
        expect(self.page.locator("#ad-status")).to_have_attribute("data-ready", "false")
        expect(self.page.locator("#adMDSelect")).to_be_disabled()
        expect(self.page.locator("#adBirthLord")).to_have_value("")
        expect(self.page.locator("#adBirthBalance")).to_have_value("")
        self.assertNotEqual(self.dasha_rows(), baseline, "Incomplete inputs must not leave an earlier valid AD table visible.")
        self.assertEqual(self.page.evaluate("window.mdDashaPeriods"), [])
        self.go("basic")
        self.page.locator("#dob").fill("2000-01-01")
        self.go("mdcalc")
        expect(self.page.locator("#ad-status")).to_have_attribute("data-ready", "true")
        expect(self.page.locator("#adMDSelect")).to_be_enabled()
        self.assertEqual(self.dasha_rows(), baseline, "Restoring the birth date must recalculate the same periods.")
        self.go("planet")
        self.page.locator("#p6_d_1").fill("")
        self.page.locator("#p6_t_1").fill("")
        self.go("mdcalc")
        expect(self.page.locator("#ad-status")).to_have_attribute("data-ready", "false")
        expect(self.page.locator("#adMDSelect")).to_be_disabled()
        expect(self.page.locator("#adBirthLord")).to_have_value("")
        self.assertNotEqual(self.dasha_rows(), baseline)

        timezone_results = []
        for timezone in ("Etc/UTC", "Asia/Kolkata"):
            with self.subTest(timezone=timezone):
                context = self.browser.new_context(viewport={"width": 1280, "height": 900}, timezone_id=timezone)
                try:
                    page = context.new_page()
                    page.on("pageerror", lambda error: self.errors.append("Timezone AD: " + str(error)))
                    page.goto(self.url, wait_until="load")
                    page.wait_for_timeout(1700)
                    # Supply exact already-calculated Moon positions directly
                    # to isolate calendar calculation from the ephemeris inputs.
                    result = page.evaluate("""() => {
                        const collect = (moon, dob) => {
                            document.getElementById('p6_final_1').value = moon;
                            document.getElementById('dob').value = dob;
                            window.updateMDCalculation();
                            return {
                                mdEnd: document.getElementById('mdDashaEnd').value,
                                rows: [...document.getElementById('adDashaRows').rows].map(row => [...row.cells].map(cell => cell.textContent.trim())),
                                birthLord: document.getElementById('adBirthLord').value,
                                balance: document.getElementById('adBirthBalance').value,
                            };
                        };
                        return [collect('00:00:00', '2000-02-29'), collect('03:40:00', '2000-01-31')];
                    }""")
                    self.assertEqual(result[0]["mdEnd"], "28/02/2007", "A leap-day birth must clamp the non-leap end date.")
                    self.assertEqual(result[0]["rows"][0][4], "29/02/2000")
                    self.assertEqual(result[1]["birthLord"], "चंद्र")
                    self.assertEqual(result[1]["balance"], "0 वर्ष 7 महिने 0 दिवस")
                    self.assertEqual(result[1]["rows"][3][4], "31/01/2000",
                                     "The exact birth AD boundary must remain the birth date at a month end.")
                    timezone_results.append(result)
                finally:
                    context.close()
        self.assertEqual(timezone_results[0], timezone_results[1],
                         "Logical report dates must not shift by one day when the browser uses India time.")

    def test_saved_future_antardasha_selection_restores_after_incomplete_or_different_moon(self):
        self.prepare_exact_dasha()
        select = self.page.locator("#adMDSelect")
        select.select_option(index=1)
        expected_key = select.input_value()
        expected_rows = self.dasha_rows()
        self.assertEqual(expected_rows[0][0], "शुक्र")
        self.action("save")
        saved = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        self.assertEqual(saved["fields"]["adMDSelect"]["value"], expected_key)

        self.go("planet")
        self.page.locator("#p6_d_1").fill("")
        self.page.locator("#p6_t_1").fill("")
        expect(select).to_be_disabled()
        self.action("load")
        expect(select).to_be_enabled()
        expect(select).to_have_value(expected_key)
        self.assertEqual(self.dasha_rows(), expected_rows,
                         "Loading a chart must restore its chosen future MD even when the current AD selector was disabled.")
        self.page.locator("#p6_d_1").fill("13:20:00")
        self.page.locator("#p6_t_1").fill("13:20:00")
        self.action("calculate")
        self.assertNotEqual(select.input_value(), expected_key)
        self.import_file(json.dumps(saved, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(select).to_have_value(expected_key)
        self.assertEqual(self.dasha_rows(), expected_rows,
                         "JSON import must recreate options before restoring a key absent from the previous Moon's MD sequence.")
        self.page.reload(wait_until="load")
        self.page.wait_for_timeout(1700)
        self.action("load")
        expect(self.page.locator("#adMDSelect")).to_have_value(expected_key)
        self.assertEqual(self.dasha_rows(), expected_rows)
        self.go("report")
        report_rows = self.page.locator('[data-report-section="adcalc"] [data-report-id="adDashaRows"]').evaluate("""body =>
            [...body.rows].map(row => [...row.cells].map(cell => cell.textContent.trim()))""")
        self.assertEqual(report_rows, expected_rows,
                         "The report must keep the restored future MD's AD table after reloading the browser.")


if __name__ == "__main__":
    unittest.main()
