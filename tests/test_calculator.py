"""Browser regression checks for the dependency-free calculator.

Run with: python3 -m unittest discover -s tests -v
Requires Python Playwright and a Chromium executable on PATH (or set
CALCULATOR_CHROMIUM to its path). No browser or package downloads occur here.
"""

import base64
import csv
from datetime import datetime
import functools
import io
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
    "karyesh", "prediction", "event-promise", "nadi-astrology", "ruling-planets", "matchmaking", "aspects", "transit", "transit-chart", "transit-panchang", "ephemeris", "south9", "report", "astrosettings",
)
OUTPUT_IDS = (
    "ayanValue", "lonDifference", "lmtFinal", "birthPlaceSiderealTime",
    "r5_nirayan_1", "r5_rashi_1", "p6_motion_0", "p6_final_0",
    "mdBirthDasha", "mdBhogyaDuration",
)
REPORT_PAGE_SECTIONS = (
    "cover", "single-page", "basic", "ayan", "lmt", "stcalc", "raphael5", "planet",
    "mdcalc", "adcalc", "kp-fourfold", "kp-sixfold", "kp-fourstep-section",
    "prediction", "aspects", "transit", "transit-chart", "transit-panchang", "ephemeris",
    "event-promise", "nadi-astrology", "ruling-planets", "matchmaking", "south9",
)
# Angles and short codes transcribed from the requested aspect reference.
# Keep this fixture independent of the application's catalog.
WESTERN_ASPECT_REFERENCE = (
    (0, "कंज."), (22.5, "से.ऑक्ट"), (30, "से.सेक"),
    (36, "सेक्यूटी"), (40, "नोवा"), (45, "से.स्क"),
    (60, "सेक."), (67.5, "सेस.ऑ."), (72, "क्यूटी"),
    (80, "बिनोवा"), (90, "स्क्वा"), (120, "ट्राइन"),
    (135, "सेसक्व"), (144, "बाइक्यू"), (150, "क्युनि"),
    (160, "क्वाड्रा"), (180, "अपो."),
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
# Independent Swiss Ephemeris 2.10.03 swe.houses (Placidus) fixtures in UTC.
# Tropical values let us check the house geometry separately from the
# calculator's explicit worksheet ayanamsha convention.
PLACIDUS_REFERENCE = (
    {"date": "1900-01-01T00:00:00Z", "latitude": 19.9975, "longitude": 73.7898,
     "cuspsTropical": [256.37367485, 286.81140335, 319.70738122, 353.44040898, 24.62683757, 51.81127149,
                       76.37367485, 106.81140335, 139.70738122, 173.44040898, 204.62683757, 231.81127149]},
    {"date": "2000-01-01T12:00:00Z", "latitude": 51.5074, "longitude": -0.1278,
     "cuspsTropical": [24.01459044, 61.01297153, 81.91142157, 99.49322530, 118.91353522, 147.48548731,
                       204.01459044, 241.01297153, 261.91142157, 279.49322530, 298.91353522, 327.48548731]},
    {"date": "2000-01-01T12:00:00Z", "latitude": -33.8688, "longitude": 151.2093,
     "cuspsTropical": [152.48890914, 195.67756727, 228.13154940, 253.08918682, 275.56340853, 299.97943816,
                       332.48890914, 15.67756727, 48.13154940, 73.08918682, 95.56340853, 119.97943816]},
    {"date": "2026-10-06T14:00:00Z", "latitude": 65, "longitude": 25,
     "cuspsTropical": [271.78200112, 28.75485959, 59.64171701, 71.76556716, 79.31803403, 85.42519881,
                       91.78200112, 208.75485959, 239.64171701, 251.76556716, 259.31803403, 265.42519881]},
    {"date": "2026-10-06T14:00:00Z", "latitude": -65, "longitude": -80,
     "cuspsTropical": [291.88256923, 298.53641564, 307.88660326, 322.90458686, 352.50259610, 64.05316990,
                       111.88256923, 118.53641564, 127.88660326, 142.90458686, 172.50259610, 244.05316990]},
    {"date": "2100-12-31T23:00:00Z", "latitude": 0, "longitude": 0,
     "cuspsTropical": [175.05416547, 207.42480604, 237.72506989, 265.83301906, 293.59905392, 323.12463212,
                       355.05416547, 27.42480604, 57.72506989, 85.83301906, 113.59905392, 143.12463212]},
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

    def show_astrologer_fields(self):
        # The settings workspace keeps the existing contact fields in its
        # Astrologer category; older standalone files showed them immediately.
        tab = self.page.locator("#settings-tab-astrologer")
        if tab.count():
            tab.click()

    def change_software_draft(self, **changes):
        self.go("astrosettings")
        for key, value in changes.items():
            control = self.page.locator(f"#setting-{key}")
            category = control.evaluate("element=>element.closest('[role=tabpanel]').id.replace('settings-pane-','')")
            self.page.locator(f"#settings-tab-{category}").click()
            tag = control.evaluate("element=>element.tagName")
            if tag == "SELECT":
                control.select_option(str(value))
            elif control.get_attribute("type") == "checkbox":
                control.set_checked(bool(value))
            else:
                control.fill(str(value))

    def save_software_preferences(self, **changes):
        self.change_software_draft(**changes)
        self.page.locator("#settings-save").click()
        self.page.wait_for_function("changes=>Object.entries(changes).every(([key,value])=>String(window.KPPreferences.get()[key])===String(value))", arg=changes)
        return self.page.evaluate("window.KPPreferences.get()")

    def outputs(self):
        return self.page.evaluate("ids => Object.fromEntries(ids.map(id => [id, document.getElementById(id).value]))", OUTPUT_IDS)

    def editable_values(self):
        # Read the worksheet DOM independently of the application's save helper.
        return self.page.evaluate("""() => Object.fromEntries(
            [...document.querySelectorAll('main > section:not(#report) input[id],main > section:not(#report) select[id],main > section:not(#report) textarea[id]')]
            .filter(el => !el.readOnly && !el.disabled && el.dataset.calculationLocked !== 'true')
            .map(el => [el.id, el.value]))""")

    @staticmethod
    def worksheet_arcseconds(value):
        """Read a worksheet angle independently of the calculator's parser."""
        text = str(value).strip().removesuffix(" R")
        sign = -1 if text.startswith("-") else 1
        degrees, minutes, seconds = map(int, text.lstrip("-").split(":"))
        return sign * (degrees * 3600 + minutes * 60 + seconds)

    def configure_automatic_0530_worksheets(self, date="2026-10-06", time="05:30:00"):
        self.page.locator("#dob").fill(date)
        self.page.locator("#birthTime").fill(time)
        self.page.locator("#dayAyan").fill("23:34:14")
        self.page.locator("#daySum").fill("00:00:00")
        self.go("planet")
        self.page.locator("#p6-ephemeris-source").select_option("automatic")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.page.wait_for_function("window.KPWorksheetEphemeris?.getData()?.ready===true")
        return self.page.evaluate("window.KPWorksheetEphemeris.getData()")

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
        self.show_astrologer_fields()
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
        expect(self.page.locator("#p6_final_1")).to_have_value(f"{int(degrees) % 30}:{minutes}:{seconds}")
        self.go("mdcalc")

    def dasha_rows(self, selector="#adDashaRows"):
        return self.page.locator(selector).evaluate("""body => [...body.rows].map(row =>
            [...row.cells].map(cell => {
                const value = cell.cloneNode(true);
                value.querySelectorAll('.ad-birth-marker').forEach(marker => marker.remove());
                return value.textContent.trim();
            }))""")

    def selected_report_popup(self, sections):
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        for section in sections:
            self.page.locator(f'#report-page-options [data-report-page-key="{section}"]').check()
        self.page.evaluate("""() => {const original=window.open;window.open=function(...args){
            const popup=original.apply(window,args);if(popup)popup.print=()=>{popup.testPrintCalled=true;};return popup;};}""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Selected report: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        return popup

    def assert_single_page_geometry(self, popup):
        # Page count alone can pass when overflow:hidden clips later tables.
        # Check every printed table cell and footer against the actual A4 page.
        errors = popup.locator(".report-single-page").evaluate("""page=>{
            const bounds=page.getBoundingClientRect(),errors=[];
            for(const element of page.querySelectorAll('.sp-chart,.sp-native-table,.sp-table,.sp-table tr,.sp-table td,.sp-table th,.sp-footer')){
                const rect=element.getBoundingClientRect(),style=getComputedStyle(element);
                if(style.display==='none'||rect.width<=0||rect.height<=0)errors.push('Hidden '+element.className);
                else if(rect.left<bounds.left-1||rect.right>bounds.right+1||rect.top<bounds.top-1||rect.bottom>bounds.bottom+1)
                    errors.push('Outside A4: '+element.tagName+' '+element.className+' '+element.textContent.slice(0,45));
                if(/^(TD|TH)$/.test(element.tagName)&&(element.scrollWidth>element.clientWidth+1||element.scrollHeight>element.clientHeight+1))
                    errors.push('Clipped cell: '+element.textContent);
            }
            for(const cell of page.querySelectorAll('.v38-cell'))for(const pseudo of ['::before','::after']){
                const style=getComputedStyle(cell,pseudo);
                if(style.display!=='none'&&style.content!=='none'&&style.content!=='normal')errors.push('Visible kundali divider '+pseudo);
            }
            for(const element of page.querySelectorAll('.sp-table td,.sp-table th,.v38-cell')){
                const style=getComputedStyle(element);
                for(const side of ['Top','Right','Bottom','Left'])if(['dotted','dashed'].includes(style['border'+side+'Style']))
                    errors.push('Dotted/dashed printed border');
            }
            for(const element of page.querySelectorAll('svg path,svg line,svg polygon,svg rect')){
                if(getComputedStyle(element).strokeDasharray!=='none')errors.push('Dashed SVG rule');
            }
            return errors;
        }""")
        self.assertEqual(errors, [], "All single-page rows, chart and footer must remain visible inside one A4 sheet.")

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
        expect(self.page.locator("#home-vimshottari")).to_be_visible()
        data = self.page.evaluate("window.KPHomeDasha.getData()")
        source_rows = self.dasha_rows("#mdDashaRows")
        self.assertTrue(data["ready"])
        self.assertEqual(len(data["levels"][0]["rows"]), 9)
        for period, source in zip(data["levels"][0]["rows"], source_rows):
            self.assertEqual(period["lord"], source[0])
            self.assertEqual(period["sourceStart"], datetime.strptime(source[4], "%d/%m/%Y").strftime("%Y-%m-%d"))
            self.assertEqual(period["sourceEnd"], datetime.strptime(source[5], "%d/%m/%Y").strftime("%Y-%m-%d"))
            self.assertGreater(period["endMs"], period["startMs"])
        expect(self.page.locator("#home-md")).to_be_hidden()
        expect(self.page.locator("#home-ad")).to_be_hidden()

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
        expect(self.page.locator('#printReport > [data-report-section="aspects"]')).to_have_count(1)
        expect(self.page.locator('#printReport > [data-report-section="transit"]')).to_have_count(1)

    def test_reference_western_catalog_calculates_all_seventeen_angles_and_inclusive_orbs(self):
        catalog = self.page.evaluate("window.KPWesternAspects.getCatalog()")
        self.assertEqual([(row["angle"], row["code"]) for row in catalog], list(WESTERN_ASPECT_REFERENCE))
        fixtures = []
        for angle, code in WESTERN_ASPECT_REFERENCE:
            for direction in (-1, 1):
                fixtures.append({"angle": angle, "code": code, "a": 350 + 720,
                                 "b": (350 + direction * angle) % 360 - 720})
        exact = self.page.evaluate("""fixtures => fixtures.map(({angle,a,b}) =>
            window.KPWesternAspects.calculate([{id:'Su',longitude:a},{id:'Mo',longitude:b}],
                [{id:1,longitude:b}], {aspects:[{angle,orb:0}]}))""", fixtures)
        for fixture, result in zip(fixtures, exact):
            with self.subTest(angle=fixture["angle"], target=fixture["b"]):
                for family in ("planetToPlanet", "planetToCusp"):
                    rows = [row for row in result[family] if row["source"] == "Su"]
                    self.assertEqual(len(rows), 1, "Exact listed angles must match in either direction across zodiac zero.")
                    self.assertEqual(rows[0]["code"], fixture["code"])
                    self.assertAlmostEqual(rows[0]["separation"], fixture["angle"], places=8)
                    self.assertAlmostEqual(rows[0]["orb"], 0, places=8)
        boundaries = [{"angle": angle, "separation": angle - 1.25 if angle == 180 else angle + 1.25}
                      for angle, _ in WESTERN_ASPECT_REFERENCE]
        edge = self.page.evaluate("""fixtures => fixtures.map(({angle,separation}) => {
            const calculate = value => window.KPWesternAspects.calculate(
                [{id:'Su',longitude:350},{id:'Mo',longitude:350+value}],
                [{id:1,longitude:350+value}], {aspects:[{angle,orb:1.25}]});
            return {inside:calculate(separation), outside:calculate(separation+(angle===180?-0.00001:0.00001))};
        })""", boundaries)
        for fixture, result in zip(boundaries, edge):
            with self.subTest(orb_boundary=fixture["angle"]):
                self.assertEqual(len(result["inside"]["planetToPlanet"]), 1)
                self.assertEqual(result["outside"]["planetToPlanet"], [])
                self.assertEqual(len([row for row in result["inside"]["planetToCusp"] if row["source"] == "Su"]), 1)
                self.assertEqual([row for row in result["outside"]["planetToCusp"] if row["source"] == "Su"], [])
        failures = self.page.evaluate("""() => [37,181].map(angle => {
            try { window.KPWesternAspects.calculate([{id:'Su',longitude:0}],[],{aspects:[{angle,orb:3}]}); return false; }
            catch { return true; }
        })""")
        self.assertEqual(failures, [True, True], "Unlisted angles must not silently become named aspects.")

    def test_aspect_catalog_color_choices_survive_lkp_and_print_without_changing_geometry(self):
        self.prepare_exact_kp_worksheets()
        self.page.locator("#p6_d_1").fill("41:00:00")
        self.page.locator("#p6_t_1").fill("41:00:00")
        self.action("calculate")
        self.go("aspects")
        self.page.locator("#western-select-all").click()
        self.assertEqual(self.page.evaluate("window.KPWesternAspects.getSettings().aspects.map(aspect=>aspect.angle)"),
                         [angle for angle, _ in WESTERN_ASPECT_REFERENCE])
        expect(self.page.locator('.western-angle-options input[type="checkbox"]:checked')).to_have_count(17)
        for angle, code in WESTERN_ASPECT_REFERENCE:
            expect(self.page.locator(f'[id="western-angle-{angle}"]')).to_be_checked()
            expect(self.page.locator(f'[id="western-angle-{angle}"]').locator("xpath=ancestor::div[contains(@class,'western-angle-option')]").first).to_contain_text(code)
        self.page.locator("#western-orb-36").fill("0.75")
        self.page.locator("#western-quality-36").select_option("very-bad")
        selected = self.page.locator('#western-planet-aspects tr[data-source="Su"][data-target="Mo"][data-angle="36"]')
        expect(selected).to_have_count(1)
        expect(selected).to_have_attribute("data-quality", "very-bad")
        expect(selected.locator(".western-aspect-code")).to_have_text("सेक्यूटी")
        self.assertEqual(selected.locator(".western-aspect-code").evaluate("element=>getComputedStyle(element).color"), "rgb(217, 36, 36)")
        geometric_rows = self.page.evaluate("""() => Object.keys(window.KPWesternAspects.getPalette()).map(quality => {
            const result=window.KPWesternAspects.calculate([{id:'Su',longitude:350},{id:'Mo',longitude:26}], [],
                {aspects:[{angle:36,orb:0,quality}]}).planetToPlanet[0];
            return {quality:result.quality,separation:result.separation,orb:result.orb,color:result.color};
        })""")
        self.assertEqual({row["quality"] for row in geometric_rows}, {"very-good", "good", "bad", "very-bad", "conjunction"})
        self.assertTrue(all(row["separation"] == 36 and row["orb"] == 0 for row in geometric_rows))
        self.assertEqual(len({row["color"] for row in geometric_rows}), 5)
        before = self.page.evaluate("window.KPWesternAspects.getSettings()")
        backup = self.page.evaluate("window.getChartData()")
        self.assertEqual(backup["fields"]["western-quality-36"]["value"], "very-bad")
        self.page.locator("#western-select-major").click()
        expect(self.page.locator('.western-angle-options input[type="checkbox"]:checked')).to_have_count(5)
        self.page.locator("#western-quality-36").select_option("good")
        self.page.locator("#western-orb-36").fill("4")
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="aspect-reference.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported")
        self.go("aspects")
        self.assertEqual(self.page.evaluate("window.KPWesternAspects.getSettings()"), before)
        expect(selected).to_have_attribute("data-quality", "very-bad")
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        self.page.locator('#report-page-options [data-report-page-key="aspects"]').check()
        self.page.evaluate("""() => { const original=window.open; window.open=function(...args) {
            const popup=original.apply(window,args); if(popup)popup.print=()=>{popup.testPrintCalled=true;}; return popup;
        }; }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Catalog print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        report = popup.locator('body > [data-report-section="aspects"]')
        expect(popup.locator("body > .report-page")).to_have_count(1)
        expect(report).to_contain_text("Semi-quintile · 36°")
        expect(report).to_contain_text("orb 0.75°")
        expect(report).to_contain_text("Very bad")
        printed = report.locator('[data-report-id="western-planet-aspects"] tr[data-source="Su"][data-target="Mo"][data-angle="36"]')
        expect(printed).to_have_attribute("data-quality", "very-bad")
        expect(printed.locator(".western-aspect-code")).to_have_text("सेक्यूटी")
        popup.emulate_media(media="print")
        self.assertEqual(printed.locator(".western-aspect-code").evaluate("element=>getComputedStyle(element).color"), "rgb(217, 36, 36)")
        expect(report.locator("input,select,button,textarea")).to_have_count(0)
        popup.close()

    def test_planet_notation_conditions_count_self_and_nodes_but_exclude_fortuna(self):
        expected = {
            "Su": ["[+]", "[*]"], "Mo": [], "Ma": ["[#]"],
            "Me": ["[*]", "[R]"], "Ju": ["[+]"], "Ve": ["[+]"],
            "Sa": ["[#]", "[*]"], "Ra": ["[+]", "[R]"], "Ke": ["[*]"],
        }
        result = self.page.evaluate("""() => {
            const ids=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
            const stars=['Ke','Ma','Ma','Sa','Ke','Ke','Sa','Me','Mo'];
            const subs=['Su','Ve','Ra','Me','Sa','Ju','Sa','Mo','Ke'];
            const model={ready:true,planets:ids.map((id,i)=>({id,longitude:i*40*3600,stl:stars[i],sl:subs[i]})),
                houses:[{id:1,occ:['Su']},{id:2,occ:[]},{id:3,occ:['Fo']},{id:4,occ:['Ra']}]};
            model.planets.push({id:'Fo',longitude:0,stl:'Ju',sl:'Fo'});
            const before=JSON.stringify(model),options={retrograde:new Set(['Me','Ra']),combustionRule:'planet-specific'};
            return {markers:Object.fromEntries(ids.map(id=>[id,window.KPDisplay.getNotations(id,model,options)])),
                text:Object.fromEntries(ids.map(id=>[id,window.KPDisplay.notationText(id,model,options)])),
                houses:[1,2,3,4,5].map(id=>window.KPDisplay.getHouseNotations(id,model)),
                marathi:window.KPDisplay.getNotations('मंगळ',model,options),
                fortuna:window.KPDisplay.getNotations('Fo',model,options),
                notReady:window.KPDisplay.getNotations('Su',{...model,ready:false},options),
                unchanged:JSON.stringify(model)===before};
        }""")
        self.assertEqual(result["markers"], expected,
                         "Own-star planets count themselves; Rahu supplies Mercury's star occupant and Fortuna supplies none.")
        self.assertEqual(result["text"], {id: "".join(markers) for id, markers in expected.items()})
        self.assertEqual(result["houses"], [[], ["[e]"], ["[e]"], [], []],
                         "An optional Fortuna point cannot make an otherwise empty natal house occupied.")
        self.assertEqual(result["marathi"], ["[#]"])
        self.assertEqual(result["fortuna"], [])
        self.assertEqual(result["notReady"], [])
        self.assertTrue(result["unchanged"], "Notation calculation must leave numeric and significator data untouched.")

    def test_combustion_markers_match_user_limits_retrograde_and_inclusive_zodiac_wrap(self):
        # Limits supplied by the user, independent of the application's constants.
        limits = (("Mo",4,False), ("Ma",8,False), ("Me",5,False), ("Me",3,True),
                  ("Ve",6,False), ("Ve",4,True), ("Ju",5,False), ("Sa",8,False))
        cases = []
        for id, orb, retrograde in limits:
            for rule, limit in (("planet-specific", orb), ("uniform", 8.5)):
                for direction in (-1, 1):
                    for delta in (-1, 0, 1):
                        cases.append({"id":id, "orb":limit, "retrograde":retrograde, "rule":rule,
                                      "direction":direction, "delta":delta, "expected":delta <= 0})
        result = self.page.evaluate("""cases=>cases.map(test=>{
            const ids=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'],sun=test.direction>0?359:1;
            const model={ready:true,houses:[],planets:ids.map((id,i)=>({id,longitude:(sun+(id===test.id
                ?test.direction*(test.orb+test.delta/3600):id==='Su'?0:90+i*10)+360)%360*3600,stl:'Ke',sl:'Ke'}))};
            const before=JSON.stringify(model),markers=window.KPDisplay.getNotations(test.id,model,
                {retrograde:test.retrograde?[test.id]:[],combustionRule:test.rule});
            return {combust:markers.includes('[C]'),retrograde:markers.includes('[R]'),unchanged:before===JSON.stringify(model)};
        })""", cases)
        for test, actual in zip(cases, result):
            with self.subTest(**test):
                self.assertEqual(actual["combust"], test["expected"],
                                 "The orb boundary is inclusive; one arcsecond beyond it must be excluded.")
                self.assertEqual(actual["retrograde"], test["retrograde"])
                self.assertTrue(actual["unchanged"])
        excluded = self.page.evaluate("""() => {
            const model={ready:true,houses:[],planets:['Su','Ra','Ke','Fo'].map(id=>({id,longitude:359*3600,stl:'Ke',sl:'Ke'}))};
            return ['Su','Ra','Ke','Fo'].map(id=>window.KPDisplay.getNotations(id,model,{retrograde:[]}));
        }""")
        self.assertTrue(all("[C]" not in markers for markers in excluded),
                        "The Sun, lunar nodes and optional Fortuna never receive combustion markers.")

    def test_planet_notations_update_live_and_survive_home_print_settings_and_lkp(self):
        self.prepare_exact_dasha()
        self.go("basic")
        self.page.locator("#birthTime").fill("05:30:00")
        self.go("planet")
        positions = ("359:00:00", "05:00:00", "53:30:00", "02:00:00",
                     "125:00:00", "03:00:00", "214:00:00", "300:00:00")
        for index, longitude in enumerate(positions):
            self.page.locator(f"#p6_d_{index}").fill(longitude)
            self.page.locator(f"#p6_t_{index}").fill("01:00:00" if index == 3 else longitude)
        self.action("calculate")
        expect(self.page.locator("#p6_final_3")).to_have_value(re.compile(r".*\bR$"))
        expected = {
            "Su": ["[+]"], "Mo": ["[+]"], "Ma": ["[#]", "[*]"],
            "Me": ["[R]", "[C]"], "Ju": ["[+]"], "Ve": ["[+]", "[C]"],
            "Sa": ["[#]", "[*]"], "Ra": ["[+]"], "Ke": ["[#]", "[*]"],
        }
        empty_houses = {3,4,6,7,9,10}
        native = self.outputs()
        model = self.page.evaluate("JSON.stringify(window.currentKPModel)")
        # At 05:30 the base longitude stays 2° while changing tomorrow's
        # longitude reverses Mercury's motion. Markers must follow that edit
        # automatically, without pressing Calculate or changing any position.
        self.page.locator("#p6_t_3").fill("03:00:00")
        expect(self.page.locator('#kp-basic-planet tr[data-planet="Me"] th [data-marker="[R]"]')).to_have_count(0)
        expect(self.page.locator('#kp-basic-planet tr[data-planet="Me"] th [data-marker="[C]"]')).to_have_count(1)
        self.page.locator("#p6_t_3").fill("01:00:00")
        expect(self.page.locator('#kp-basic-planet tr[data-planet="Me"] th [data-marker="[R]"]')).to_have_count(1)
        self.assertEqual(self.page.evaluate("JSON.stringify(window.currentKPModel)"), model)

        def assert_references(root, expectations=expected):
            refs = root.locator("[data-planet-ref]").evaluate_all("""refs=>refs.map(ref=>({id:ref.dataset.planetRef,
                markers:[...ref.querySelectorAll('.kp-notation-marker')].map(marker=>marker.dataset.marker)}))""")
            self.assertTrue(refs, "The source and mirrored calculations must expose planet references.")
            for reference in refs:
                self.assertEqual(reference["markers"], expectations[reference["id"]], reference)

        for table in ("kp-basic-planet", "kp-fourfold-planet", "kp-sixfold-planet"):
            assert_references(self.page.locator(f"#{table}"))
            for id, markers in expected.items():
                row = self.page.locator(f'#{table} tr[data-planet="{id}"]')
                expect(row.locator("th .kp-planet-label")).to_have_text(id)
                self.assertEqual(row.locator("th .kp-notation-marker").evaluate_all(
                    "markers=>markers.map(marker=>marker.dataset.marker)"), markers)
        for table in ("kp-basic-house", "kp-fourfold-house", "kp-sixfold-house"):
            assert_references(self.page.locator(f"#{table}"))
            for house in range(1,13):
                markers = self.page.locator(f'#{table} tr[data-house="{house}"] th .kp-notation-marker').evaluate_all(
                    "markers=>markers.map(marker=>marker.dataset.marker)")
                self.assertEqual(markers, ["[e]"] if house in empty_houses else [])
        assert_references(self.page.locator("#kp-fourstep"))
        for section in ("kp-basic-calculations", "kp-fourfold", "kp-sixfold", "kp-fourstep-section"):
            self.assertEqual(self.page.locator(f"#{section} > .kp-notation-legend b").all_text_contents(),
                             ["[+]", "[#]", "[*]", "[R]", "[C]", "[e]"])
        self.go("home")
        expect(self.page.locator("#home-notations-legend")).to_be_visible()
        self.assertEqual(self.page.locator("#home-notations-legend b").all_text_contents(),
                         ["[+]", "[#]", "[*]", "[R]", "[C]", "[e]"])
        assert_references(self.home_source("kp-basic-planet"))
        for view, table in (("fourfold", "kp-fourfold-planet"), ("sixfold", "kp-sixfold-planet"), ("fourstep", "kp-fourstep")):
            self.page.locator(f'#home [data-home-view="{view}"]').click()
            assert_references(self.home_source(table))
        self.go("report")
        for section in ("south9", "kp-fourfold", "kp-sixfold", "kp-fourstep-section"):
            assert_references(self.page.locator(f'[data-report-section="{section}"]'))
        self.page.locator("#report-clear-pages").click()
        for section in ("south9", "kp-fourfold", "kp-sixfold", "kp-fourstep-section"):
            self.page.locator(f'#report-page-options [data-report-page-key="{section}"]').check()
        self.page.evaluate("""() => {const original=window.open;window.open=function(...args){
            const popup=original.apply(window,args);if(popup)popup.print=()=>{popup.testPrintCalled=true;};return popup;};}""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Notation print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        popup.emulate_media(media="print")
        for section in ("south9", "kp-fourfold", "kp-sixfold", "kp-fourstep-section"):
            printed = popup.locator(f'body > [data-report-section="{section}"]')
            assert_references(printed)
            self.assertEqual(printed.locator(".kp-notation-legend b").all_text_contents(),
                             ["[+]", "[#]", "[*]", "[R]", "[C]", "[e]"])
            expect(printed.locator("input,select,button,textarea")).to_have_count(0)
        popup.close()
        self.save_software_preferences(notationMarkers=False, combustionRule="uniform")
        expect(self.page.locator("#kp-basic-planet .kp-notation-marker,#kp-basic-house .kp-notation-marker,#kp-fourstep .kp-notation-marker")).to_have_count(0)
        self.go("home")
        expect(self.page.locator("#home-notations-legend")).not_to_be_visible()
        self.assertEqual(self.page.evaluate("window.KPDisplay.getNotations('Mo')"), ["[+]", "[C]"],
                         "Hiding markers must not disable their calculation or change the selected combustion rule.")
        self.assertEqual(self.outputs(), native)
        self.assertEqual(self.page.evaluate("JSON.stringify(window.currentKPModel)"), model)
        self.action("save")
        saved = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        preferences = json.loads(saved["fields"]["kp-software-settings"]["value"])
        self.assertFalse(preferences["notationMarkers"])
        self.assertEqual(preferences["combustionRule"], "uniform")
        self.save_software_preferences(notationMarkers=True, combustionRule="planet-specific")
        self.import_file(json.dumps(saved, ensure_ascii=False))
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.assertFalse(self.page.evaluate("window.KPPreferences.get().notationMarkers"))
        expect(self.page.locator("#kp-basic-planet .kp-notation-marker")).to_have_count(0)
        self.save_software_preferences(notationMarkers=True)
        uniform_expected = {**expected, "Mo":["[+]", "[C]"]}
        assert_references(self.page.locator("#kp-basic-planet"), uniform_expected)
        self.assertEqual(self.outputs(), native)
        self.assertEqual(self.page.evaluate("JSON.stringify(window.currentKPModel)"), model)

    def test_fortuna_uses_day_night_cusp_boundaries_and_absolute_zodiac_wrap(self):
        # These expected values use Asc + Moon - Sun for day and
        # Asc + Sun - Moon for night; they do not read the displayed result.
        fixtures = [
            {"asc":350,"sun":200,"moon":40,"formula":"sect","expected":190,"sect":"day","house":8,"used":"day"},
            {"asc":350,"sun":10,"moon":40,"formula":"sect","expected":320,"sect":"night","house":1,"used":"night"},
            {"asc":350,"sun":10,"moon":40,"formula":"day","expected":20,"sect":"night","house":1,"used":"day"},
            {"asc":350,"sun":200,"moon":40,"formula":"night","expected":150,"sect":"day","house":8,"used":"night"},
            {"asc":350,"sun":170,"moon":10,"formula":"sect","expected":190,"sect":"day","house":7,"used":"day"},
            {"asc":350,"sun":350,"moon":10,"formula":"sect","expected":330,"sect":"night","house":1,"used":"night"},
            {"asc":350,"sun":170,"moon":10,"formula":"sect","expected":190,"sect":"day","house":7,"used":"day",
             "cusps":[350,10,40,75,100,140,170,190,220,255,280,310]},
            {"asc":350,"sun":169.99,"moon":10,"formula":"sect","expected":149.99,"sect":"night","house":6,"used":"night",
             "cusps":[350,10,40,75,100,140,170,190,220,255,280,310]},
        ]
        results = self.page.evaluate("""fixtures=>fixtures.map(fixture=>{
            const model={ready:true,houses:(fixture.cusps||Array.from({length:12},(_,i)=>(fixture.asc+i*30)%360))
                .map((longitude,i)=>({id:i+1,longitude})),planets:[{id:'Su',longitude:fixture.sun},{id:'Mo',longitude:fixture.moon}]};
            const before=JSON.stringify(model),point=window.KPFortuna.calculate(model,{unit:'degrees',formula:fixture.formula});
            const arcseconds={ready:true,houses:model.houses.map(cusp=>({...cusp,longitude:cusp.longitude*3600})),
                planets:model.planets.map(planet=>({...planet,longitude:planet.longitude*3600}))};
            return {point,unchanged:before===JSON.stringify(model),native:window.KPFortuna.calculate(arcseconds,{formula:fixture.formula})};
        })""", fixtures)
        for fixture, result in zip(fixtures, results):
            with self.subTest(sun=fixture["sun"], formula=fixture["formula"], unequal="cusps" in fixture):
                self.assertTrue(result["unchanged"], "Deriving Fortuna must not mutate the nine-graha model or house cusps.")
                for point in (result["point"], result["native"]):
                    self.assertEqual(point["id"], "Fo")
                    self.assertEqual(point["unit"], "arcseconds")
                    self.assertAlmostEqual(point["longitude"], fixture["expected"] * 3600, places=6)
                    self.assertEqual(point["sect"], fixture["sect"])
                    self.assertEqual(point["formulaUsed"], fixture["used"])
                    self.assertEqual(point["sunHouse"], fixture["house"])
        invalid = self.page.evaluate("""() => {
            const model={ready:true,cusps:Array.from({length:12},(_,i)=>({id:i+1,longitude:i*30})),
                planets:[{id:'Su',longitude:200},{id:'Mo',longitude:40}]};
            return [window.KPFortuna.calculate(model),window.KPFortuna.calculate({...model,cusps:model.cusps.slice(1)},{unit:'degrees'}),
                window.KPFortuna.calculate({...model,cusps:Array(12).fill({longitude:0})},{unit:'degrees'}),
                window.KPFortuna.calculate({...model,planets:[{id:'Su',longitude:200}]},{unit:'degrees'})];
        }""")
        self.assertEqual(invalid, [None,None,None,None], "Missing units, cusps or Moon must not yield an invented point.")
        self.assertIsNone(self.page.evaluate("window.KPFortuna.getNatal()"), "Fortuna display must remain optional by default.")

    def test_optional_fortuna_appears_on_selected_charts_and_print_without_changing_graha_calculations(self):
        self.prepare_exact_dasha()
        native_outputs = self.outputs()
        native_positions = self.page.evaluate("""() => ({planets:window.currentKPModel.planets.map(point=>[point.id,point.longitude]),
            cusps:window.currentKPModel.houses.map(point=>point.longitude)})""")
        transit = self.configure_transit_chart()
        self.assertIsNone(self.page.evaluate("window.KPFortuna.getNatal()"))
        expect(self.page.locator('#kundali [data-planet="Fo"]')).to_have_count(0)
        self.save_software_preferences(showFortuna=True, fortunaFormula="sect")
        fortuna = self.page.evaluate("window.KPFortuna.getNatal()")
        self.assertEqual(fortuna["longitude"], 5 * 3600, "Asc0 + Sun5 - Moon0 must give night Fortuna5°.")
        self.assertEqual(fortuna["formulaUsed"], "night")
        self.go("south9")
        point = self.page.locator('#kundali [data-planet="Fo"]')
        expect(point).to_have_count(1)
        self.assertAlmostEqual(float(point.get_attribute("data-longitude")), fortuna["longitude"], places=7)
        expect(point.locator(".v38-lords")).to_have_text(f'({fortuna["sgl"]}-{fortuna["stl"]}-{fortuna["sl"]})')
        expect(self.page.locator("#kundali-fortuna-info")).to_contain_text("Asc + Sun − Moon")
        self.go("home")
        expect(self.home_source("kundali").locator('[data-planet="Fo"]')).to_have_count(1)
        self.save_software_preferences(chartStyle="north")
        self.go("home")
        north = self.home_source("kundali-north").locator('svg [data-planet="Fo"]')
        expect(north).to_have_count(1)
        self.assertAlmostEqual(float(north.get_attribute("data-longitude")), fortuna["longitude"], places=7)
        self.go("transit-chart")
        tc_fortuna = self.page.evaluate("window.KPFortuna.getTransit(window.KPTransitChart.getData())")
        for chart in ("tc-rashi-chart", "tc-bhav-chart"):
            fo = self.page.locator(f'#{chart} svg [data-planet="Fo"]')
            expect(fo).to_have_count(1)
            self.assertAlmostEqual(float(fo.get_attribute("data-longitude")), tc_fortuna["longitude"] / 3600, places=7)
        self.assertEqual(len(self.page.evaluate("window.KPTransitChart.getData().planets")), 9)
        expect(self.page.locator("#tc-planets tbody tr[data-planet]")).to_have_count(9)
        self.assertEqual(self.page.evaluate("window.KPTransitChart.getData().utc"), transit["utc"])
        self.assertEqual(self.outputs(), native_outputs)
        self.assertEqual(self.page.evaluate("""() => ({planets:window.currentKPModel.planets.map(point=>[point.id,point.longitude]),
            cusps:window.currentKPModel.houses.map(point=>point.longitude)})"""), native_positions,
                         "Fortuna visibility must preserve all nine planet longitudes and twelve native cusps.")
        expect(self.page.locator('#kp-basic-planet tbody tr')).to_have_count(9)
        expect(self.page.locator('input[id^="p6_d_"]:not([readonly])')).to_have_count(8)
        backup = self.page.evaluate("window.getChartData()")
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        for section in ("south9", "transit-chart"):
            self.page.locator(f'#report-page-options [data-report-page-key="{section}"]').check()
        self.page.evaluate("""() => { const original=window.open; window.open=function(...args) {
            const popup=original.apply(window,args); if(popup)popup.print=()=>{popup.testPrintCalled=true;}; return popup;
        }; }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Fortuna print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator('[data-report-section="south9"] svg [data-planet="Fo"]')).to_have_count(1)
        expect(popup.locator('[data-report-section="transit-chart"] svg [data-planet="Fo"]')).to_have_count(2)
        expect(popup.locator('[data-report-section="transit-chart"]')).to_contain_text("Fortuna")
        popup.close()
        self.save_software_preferences(showFortuna=False)
        expect(self.page.locator('#kundali [data-planet="Fo"],#kundali-north svg [data-planet="Fo"],#tc-rashi-chart svg [data-planet="Fo"]')).to_have_count(0)
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="fortuna-display.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported")
        self.assertTrue(self.page.evaluate("window.KPPreferences.get().showFortuna"))
        self.assertEqual(self.page.evaluate("window.KPFortuna.getNatal().longitude"), fortuna["longitude"])

    def test_all_settings_categories_keep_drafts_isolated_and_save_cancel_presets_work(self):
        self.prepare_exact_dasha()
        self.save_software_preferences(degreeSize="medium")
        self.show_astrologer_fields()
        self.page.locator("#astroName").fill("Saved settings astrologer")
        self.page.locator("#settings-save").click()
        saved = self.page.evaluate("window.KPPreferences.get()")
        before_font = self.page.locator("#kundali .v38-degree").first.evaluate("element=>getComputedStyle(element).fontSize")
        before_hidden = self.page.locator("#kp-software-settings").input_value()
        self.change_software_draft(degreeSize="large", chartStyle="north", theme="classic")
        self.show_astrologer_fields()
        self.page.locator("#astroName").fill("Unsaved settings astrologer")
        self.assertEqual(self.page.evaluate("window.KPPreferences.get()"), saved,
                         "Changing settings controls must remain a draft until Save.")
        self.assertEqual(self.page.locator("#kundali .v38-degree").first.evaluate("element=>getComputedStyle(element).fontSize"), before_font)
        self.assertEqual(self.page.locator("#kp-software-settings").input_value(), before_hidden)
        backup = self.page.evaluate("window.getChartData()")
        self.assertFalse(any(key.startswith("setting-") for key in backup["fields"]),
                         "Portable backups must not accidentally apply an unsaved settings draft.")
        self.page.locator("#settings-cancel").click()
        self.assertEqual(self.page.evaluate("window.KPSettings.getDraft()"), saved)
        expect(self.page.locator("#astroName")).to_have_value("Saved settings astrologer")
        self.page.locator("#settings-tab-presets").click()
        self.page.locator("#settings-preset-compact").click()
        draft = self.page.evaluate("window.KPSettings.getDraft()")
        self.assertEqual(draft["tableSize"], "small")
        self.assertEqual(draft["resolution"], "compact")
        self.assertEqual(self.page.evaluate("window.KPPreferences.get()"), saved,
                         "Choosing a preset must wait for Save before changing the software.")
        self.page.locator("#settings-save").click()
        self.page.wait_for_function("window.KPPreferences.get().resolution === 'compact'")
        expect(self.page.locator("body")).to_have_attribute("data-kp-resolution", "compact")
        compact = self.page.evaluate("window.KPPreferences.get()")
        self.assertEqual(json.loads(self.page.locator("#kp-software-settings").input_value()), compact)
        stored = self.page.evaluate("JSON.parse(localStorage.getItem(window.KPPreferences.storageKey))")
        self.assertEqual(stored, compact)
        self.page.reload(wait_until="load")
        self.page.wait_for_function("window.KPPreferences?.get().resolution === 'compact'")
        self.go("astrosettings")
        self.assertEqual(self.page.evaluate("window.KPSettings.getDraft()"), compact)
        categories = ("display", "calculation", "notations", "ruling", "significators", "aspects",
                      "language", "presets", "themes", "astrologer")
        expect(self.page.locator("#kp-settings-shell [role=tab]")).to_have_count(10)
        for width in (1280, 390):
            self.page.set_viewport_size({"width":width,"height":900})
            for category in categories:
                tab = self.page.locator(f"#settings-tab-{category}")
                tab.click()
                expect(tab).to_have_attribute("aria-selected", "true")
                expect(self.page.locator(f"#settings-pane-{category}")).to_be_visible()
                expect(self.page.locator("#kp-settings-shell [role=tabpanel]:visible")).to_have_count(1)
                self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width + 1,
                                     f"The {category} settings category must fit its screen.")
        self.page.locator("#settings-tab-display").focus()
        self.page.keyboard.press("ArrowDown")
        expect(self.page.locator("#settings-tab-calculation")).to_be_focused()
        expect(self.page.locator("#settings-pane-calculation")).to_be_visible()
        self.page.keyboard.press("End")
        expect(self.page.locator("#settings-tab-astrologer")).to_be_focused()
        self.page.keyboard.press("Home")
        expect(self.page.locator("#settings-tab-display")).to_be_focused()

    def test_settings_change_real_aspects_and_significators_and_round_trip_without_losing_natal_data(self):
        self.prepare_exact_dasha()
        before = self.outputs()
        self.assertFalse(self.page.evaluate("window.currentKPModel.options.ketuAspects"))
        self.save_software_preferences(ketuAspects=True, conjunctionOrb=5, aspectSet="all", aspectOrb=1.25,
                                       homeView="sixfold", rpOrb=0.5, rpRefresh="manual")
        actual = self.page.evaluate("window.currentKPModel")
        self.assertTrue(actual["options"]["ketuAspects"])
        self.assertEqual(actual["options"]["conjunctionOrb"], 5)
        ketu = next(planet for planet in actual["planets"] if planet["id"] == "Ke")
        self.assertGreater(len(ketu["aspg"]["houses"]), 0, "The Ketu option must change actual aspect relationships.")
        self.assertTrue(any(planet["conj"] for planet in actual["planets"]), "The selected5° cusp conjunction orb must include the exact5° fixture.")
        settings = self.page.evaluate("window.KPWesternAspects.getSettings()")
        self.assertEqual([aspect["angle"] for aspect in settings["aspects"]], [angle for angle, _ in WESTERN_ASPECT_REFERENCE])
        self.assertTrue(all(aspect["orb"] == 1.25 for aspect in settings["aspects"]))
        self.go("home")
        expect(self.home_source("kp-sixfold-planet")).to_be_visible()
        expect(self.page.locator("#home-current-ruling-planets")).to_contain_text("0.5° orb")
        saved = self.page.evaluate("window.KPPreferences.get()")
        backup = self.page.evaluate("window.getChartData()")
        self.assertEqual(json.loads(backup["fields"]["kp-software-settings"]["value"]), saved)
        self.save_software_preferences(ketuAspects=False, conjunctionOrb=0, aspectSet="major", aspectOrb=3,
                                       homeView="basic")
        self.assertFalse(self.page.evaluate("window.currentKPModel.options.ketuAspects"))
        planets = self.page.evaluate("window.currentKPModel.planets")
        self.assertEqual(next(planet for planet in planets if planet["id"] == "Su")["conj"], [])
        self.assertEqual(next(planet for planet in planets if planet["id"] == "Mo")["conj"], [1],
                         "A zero orb must retain an exact cusp conjunction and exclude the Sun5° away.")
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="software-settings.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported")
        self.assertEqual(self.page.evaluate("window.KPPreferences.get()"), saved)
        self.assertTrue(self.page.evaluate("window.currentKPModel.options.ketuAspects"))
        self.assertEqual(self.page.evaluate("window.currentKPModel.options.conjunctionOrb"), 5)
        self.assertEqual(self.outputs(), before, "Settings must preserve every numeric worksheet calculation and native date.")
        invalid = json.loads(json.dumps(backup))
        invalid["fields"]["name"] = {"value":"Must not replace native data"}
        invalid["fields"]["kp-software-settings"]["value"] = "{broken preferences"
        self.import_file(json.dumps(invalid), filename="broken-preferences.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Unable to import")
        self.assertEqual(self.page.evaluate("window.KPPreferences.get()"), saved)
        self.assertEqual(self.outputs(), before)
        expect(self.page.locator("#name")).not_to_have_value("Must not replace native data")

    def test_display_preferences_change_live_labels_sizes_dates_and_print_while_preserving_raw_values(self):
        self.prepare_exact_dasha(dob="2000-06-15")
        self.go("basic")
        self.page.locator("#birthTime").fill("14:30:00")
        self.action("calculate")
        self.configure_transit_chart()
        before = self.outputs()
        self.go("south9")
        degree_font = self.page.evaluate("parseFloat(getComputedStyle(document.querySelector('#kundali .v38-degree')).fontSize)")
        table_font = self.page.evaluate("parseFloat(getComputedStyle(document.querySelector('#kp-basic-planet tbody td')).fontSize)")
        self.save_software_preferences(degreeSize="large", tableSize="small", planetNotation="short", houseNotation="numeric",
                                       degreePrecision="minutes", dateFormat="MM/DD/YYYY", timeFormat="12", birthInfo=False,
                                       tooltips=False, language="english", theme="classic")
        self.go("south9")
        sun = self.page.locator('#kundali .v38-planet[data-planet="Su"]')
        expect(sun).to_have_count(1)
        expect(sun.locator(".v38-name")).to_have_text("Su")
        expect(sun.locator(".v38-degree")).to_have_text("5°00′")
        expect(self.page.locator("#kundali .v38-cusp .v38-name")).not_to_contain_text(["I", "II", "III"])
        self.assertEqual(set(self.page.locator("#kundali .v38-cusp .v38-name").all_text_contents()), {str(i) for i in range(1,13)})
        # A legacy recalculation replaces the chart DOM. Preferences must be
        # present immediately in the replacement, before any observer/RAF runs.
        redraw = self.page.evaluate("""() => {
            window.renderChart(true);
            const sun=document.querySelector('#kundali .v38-planet[data-planet="Su"]');
            return {name:sun.querySelector('.v38-name').textContent,
                degree:sun.querySelector('.v38-degree').textContent,
                font:parseFloat(getComputedStyle(sun.querySelector('.v38-degree')).fontSize),
                cusps:[...document.querySelectorAll('#kundali .v38-cusp .v38-name')].map(label=>label.textContent)};
        }""")
        self.assertEqual((redraw["name"], redraw["degree"]), ("Su", "5°00′"),
                         "Configured planet names and precision must survive a synchronous chart redraw.")
        self.assertEqual(set(redraw["cusps"]), {str(i) for i in range(1,13)})
        shown_degree_font = redraw["font"]
        shown_table_font = self.page.evaluate("parseFloat(getComputedStyle(document.querySelector('#kp-basic-planet tbody td')).fontSize)")
        self.assertGreater(shown_degree_font, degree_font)
        self.assertLess(shown_table_font, table_font)
        expect(self.page.locator("#kundali .v38-data")).not_to_be_visible()
        expect(self.page.locator("#kundali .v38-item[title]")).to_have_count(0)
        expect(self.page.locator("body")).to_have_attribute("data-kp-theme", "classic")
        expect(self.page.locator("html")).to_have_attribute("lang", "en")
        self.assertEqual(self.page.locator(".app-sidebar").evaluate("element=>getComputedStyle(element).backgroundColor"), "rgb(38, 58, 33)")
        dates = self.page.evaluate("""() => ({leap:window.KPPreferences.formatDate('2024-02-29'),
            invalid:window.KPPreferences.formatDate('2024-02-30'), midnight:window.KPPreferences.formatTime('00:00:00'),
            noon:window.KPPreferences.formatTime('12:00:00'),evening:window.KPPreferences.formatTime('23:59:00')})""")
        self.assertEqual(dates, {"leap":"02/29/2024", "invalid":"2024-02-30", "midnight":"12:00:00 AM",
                                 "noon":"12:00:00 PM", "evening":"11:59:00 PM"})
        self.go("home")
        expect(self.page.locator('#home-native [data-home-field="dob"]')).to_contain_text("06/15/2000")
        expect(self.page.locator('#home-native [data-home-field="birthTime"]')).to_have_text("2:30:00 PM")
        self.assertTrue(all("″" not in text for text in self.home_source("kundali").locator(".v38-degree").all_text_contents()))
        self.go("mdcalc")
        expect(self.page.locator("#mdDashaRows tr").first).to_contain_text("06/15/2000")
        self.go("transit-chart")
        expect(self.page.locator("#tc-status")).to_contain_text("10/06/2026")
        expect(self.page.locator("#tc-status")).to_contain_text("5:30:00 AM")
        self.assertEqual(self.outputs(), before)
        expect(self.page.locator("#dob")).to_have_value("2000-06-15")
        expect(self.page.locator("#birthTime")).to_have_value("14:30:00")
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        for section in ("cover", "south9", "transit-chart"):
            self.page.locator(f'#report-page-options [data-report-page-key="{section}"]').check()
        self.page.evaluate("""() => { const original=window.open; window.open=function(...args) {
            const popup=original.apply(window,args); if(popup)popup.print=()=>{popup.testPrintCalled=true;}; return popup;
        }; }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Preferences print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator('[data-report-section="cover"] [data-cover-field="dob"]')).to_have_text("06/15/2000")
        expect(popup.locator('[data-report-section="cover"] [data-cover-field="birthTime"]')).to_have_text("2:30:00 PM")
        chart = popup.locator('[data-report-section="south9"] [data-report-id="kundali"]')
        self.assertTrue(all("″" not in text for text in chart.locator(".v38-degree").all_text_contents()))
        self.assertEqual(set(chart.locator(".v38-cusp .v38-name").all_text_contents()), {str(i) for i in range(1,13)})
        expect(popup.locator('[data-report-section="transit-chart"]')).to_contain_text("10/06/2026 5:30:00 AM")
        popup.emulate_media(media="print")
        expect(chart.locator(".v38-data")).not_to_be_visible()
        popup.close()
        self.save_software_preferences(planetSymbols=True, tooltips=True, birthInfo=True)
        self.go("south9")
        expect(self.page.locator("#kundali .v38-name", has_text="☉")).to_have_count(1)
        expect(self.page.locator("#kundali .v38-item[title]")).to_have_count(21)
        expect(self.page.locator("#kundali .v38-data")).to_be_visible()

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

    def test_transit_placidus_houses_match_independent_references_and_reject_invalid_locations(self):
        actual = self.page.evaluate("""fixtures => fixtures.map(fixture => ({
            ...window.KPTransitHouses.calculate(fixture.date, fixture.latitude, fixture.longitude),
            ayanamsha:window.KPEphemeris.ayanamsha(fixture.date),
            horizonAscendant:window.KPEphemeris.ascendant(fixture.date, fixture.latitude, fixture.longitude),
        }))""", PLACIDUS_REFERENCE)
        for fixture, values in zip(PLACIDUS_REFERENCE, actual):
            with self.subTest(date=fixture["date"], latitude=fixture["latitude"]):
                self.assertEqual(values["system"], "Placidus")
                self.assertEqual(values["units"], "degrees")
                self.assertEqual(len(values["cusps"]), 12)
                self.assertTrue(all(0 <= longitude < 360 for longitude in values["cusps"]))
                self.assertAlmostEqual(values["ascendant"], values["cusps"][0], places=7)
                self.assertAlmostEqual(values["mc"], values["cusps"][9], places=7)
                self.assertLess(abs((values["ascendant"] - values["horizonAscendant"] + 180) % 360 - 180), 0.001)
                for index, (longitude, expected) in enumerate(zip(values["cusps"], fixture["cuspsTropical"])):
                    tropical = (longitude + values["ayanamsha"]) % 360
                    delta = abs((tropical - expected + 180) % 360 - 180)
                    self.assertLess(delta, 0.001, f"House {index+1} differs from independent Placidus reference by {delta}°.")
                for index in range(6):
                    self.assertAlmostEqual((values["cusps"][index+6] - values["cusps"][index]) % 360, 180, places=7)
                gaps = [(values["cusps"][(index+1) % 12] - values["cusps"][index]) % 360 for index in range(12)]
                self.assertTrue(all(gap > 0 for gap in gaps), "Cusps must follow the zodiac without duplicates.")
                self.assertAlmostEqual(sum(gaps), 360, places=7)
        failures = self.page.evaluate("""() => [
            ['2026-10-06T00:00:00Z',85,0], ['2026-10-06T00:00:00Z',95,0],
            ['2026-10-06T00:00:00Z',18.52,181], ['2101-01-01T00:00:00Z',18.52,73.85]
        ].map(args => { try { window.KPTransitHouses.calculate(...args); return null; }
                         catch (error) { return error.message; } })""")
        self.assertTrue(all(isinstance(message, str) and message for message in failures),
                        "Polar geometry, invalid coordinates and unsupported dates must produce explicit errors instead of fabricated cusps.")

    def configure_transit_chart(self, date="2026-10-06", time="05:30:00", source="transit", place="Pune, Maharashtra"):
        self.go("transit-chart")
        for field, value in {"date": date, "time": time, "latitude": "18.52", "longitude": "73.85",
                             "timezone": "5.5", "place": place}.items():
            self.page.locator(f"#tc-{field}").fill(value)
        self.page.locator("#tc-cusp-source").select_option(source)
        self.page.locator("#tc-calculate").click()
        expect(self.page.locator("#tc-status")).to_have_attribute("data-state", "ready")
        return self.page.evaluate("window.KPTransitChart.getData()")

    def test_transit_chart_uses_selected_moment_and_cusp_source_without_editing_natal_data(self):
        self.prepare_exact_dasha()
        natal_fields = {key: value for key, value in self.editable_values().items() if not key.startswith("tc-")}
        natal_outputs = self.outputs()
        natal_cusps = self.page.evaluate("window.currentKPModel.houses.map(house=>house.longitude/3600)")
        transit = self.configure_transit_chart()
        self.assertEqual(transit["utc"], "2026-10-06T00:00:00.000Z", "The entered local time must use its selected UTC offset.")
        self.assertEqual(transit["cuspSource"], "transit")
        self.assertEqual(transit["cuspSystem"], "Placidus")
        self.assertEqual(len(transit["planets"]), 9)
        self.assertEqual(len(transit["cusps"]), 12)
        expected = self.page.evaluate("""stamp => ({planets:window.KPEphemeris.positions(stamp),
            cusps:window.KPTransitHouses.calculate(stamp,18.52,73.85).cusps})""", transit["utc"])
        for planet in transit["planets"]:
            self.assertAlmostEqual(planet["longitude"], expected["planets"][planet["id"]], places=7)
            self.assertEqual(planet["retrograde"], planet["motionDegreesPerDay"] < 0)
            row = self.page.locator(f'#tc-planets tbody tr[data-planet="{planet["id"]}"]')
            expect(row).to_have_count(1)
            self.assertAlmostEqual(float(row.get_attribute("data-longitude")), planet["longitude"], places=7)
            expect(row.locator("td").nth(2)).to_have_text("R" if planet["retrograde"] else "D")
        for cusp, longitude in zip(transit["cusps"], expected["cusps"]):
            self.assertAlmostEqual(cusp["longitude"], longitude, places=7)
        self.assertNotEqual([cusp["longitude"] for cusp in transit["cusps"]], natal_cusps,
                            "Transit houses must be calculated for this moment rather than copying natal houses.")
        for chart in ("tc-rashi-chart", "tc-bhav-chart"):
            expect(self.page.locator(f"#{chart} svg g[data-house]")).to_have_count(12)
            expect(self.page.locator(f"#{chart} svg tspan[data-planet]")).to_have_count(9)
            plotted = self.page.locator(f"#{chart} svg tspan[data-planet]").evaluate_all("""planets => Object.fromEntries(
                planets.map(planet=>[planet.dataset.planet,Number(planet.dataset.longitude)]))""")
            self.assertEqual(plotted, expected["planets"], "Both charts must plot the same real transit longitudes as their table.")
        self.assertTrue(transit["dasha"]["ready"])
        self.assertEqual(transit["dasha"]["md"]["lord"], "शुक्र")
        expect(self.page.locator('#tc-dasha tbody tr[data-role="MD"]')).to_contain_text("Ve")
        expect(self.page.locator("#tc-pd-periods tbody tr")).to_have_count(9)

        self.page.locator("#tc-cusp-source").select_option("natal")
        expect(self.page.locator("#tc-status")).to_have_attribute("data-state", "ready")
        natal = self.page.evaluate("window.KPTransitChart.getData()")
        self.assertEqual([cusp["longitude"] for cusp in natal["cusps"]], natal_cusps)
        self.assertEqual([planet["longitude"] for planet in natal["planets"]],
                         [planet["longitude"] for planet in transit["planets"]],
                         "Changing cusp source must retain the selected moment's planetary positions.")
        self.page.locator("#tc-date").fill("2026-10-07")
        self.page.locator("#tc-calculate").click()
        changed = self.page.evaluate("window.KPTransitChart.getData()")
        self.assertEqual(changed["utc"], "2026-10-07T00:00:00.000Z")
        self.assertEqual([cusp["longitude"] for cusp in changed["cusps"]], natal_cusps)
        first_moon = next(planet["longitude"] for planet in natal["planets"] if planet["id"] == "Mo")
        next_moon = next(planet["longitude"] for planet in changed["planets"] if planet["id"] == "Mo")
        self.assertGreater(abs((next_moon - first_moon + 180) % 360 - 180), 10,
                           "Advancing one day must move the Moon rather than showing fixed natal positions.")
        self.assertEqual({key: value for key, value in self.editable_values().items() if not key.startswith("tc-")}, natal_fields)
        self.assertEqual(self.outputs(), natal_outputs, "Transit exploration must leave all birth worksheet results intact.")

    def test_transit_chart_calendar_steps_lkp_restore_and_mobile_charts_preserve_selected_data(self):
        self.prepare_exact_dasha()
        self.configure_transit_chart(date="2026-01-31", time="23:45:00")
        self.page.locator("#tc-step-size").select_option("month")
        self.page.locator("#tc-forward").click()
        expect(self.page.locator("#tc-date")).to_have_value("2026-02-28")
        expect(self.page.locator("#tc-time")).to_have_value("23:45:00")
        self.assertEqual(self.page.evaluate("window.KPTransitChart.getData().localDate"), "2026-02-28")
        self.page.locator("#tc-step-size").select_option("hour")
        self.page.locator("#tc-forward").click()
        expect(self.page.locator("#tc-date")).to_have_value("2026-03-01")
        expect(self.page.locator("#tc-time")).to_have_value("00:45:00")
        self.page.locator("#tc-backward").click()
        expect(self.page.locator("#tc-date")).to_have_value("2026-02-28")
        saved = self.page.evaluate("window.KPTransitChart.getData()")
        self.action("save")
        backup = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        self.configure_transit_chart(date="2026-04-01", time="12:00:00", source="natal", place="Other location")
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="transit-chart.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.go("transit-chart")
        for field, value in (("date", "2026-02-28"), ("time", "23:45:00"), ("cusp-source", "transit"),
                             ("latitude", "18.52"), ("longitude", "73.85"), ("timezone", "5.5"), ("place", "Pune, Maharashtra")):
            expect(self.page.locator(f"#tc-{field}")).to_have_value(value)
        self.page.locator("#tc-calculate").click()
        restored = self.page.evaluate("window.KPTransitChart.getData()")
        self.assertEqual(restored["utc"], saved["utc"])
        self.assertEqual(restored["planets"], saved["planets"])
        self.assertEqual(restored["cusps"], saved["cusps"])
        for width, height in ((1920, 1080), (1280, 900), (390, 844)):
            self.page.set_viewport_size({"width": width, "height": height})
            for chart in ("tc-rashi-chart", "tc-bhav-chart"):
                with self.subTest(width=width, chart=chart):
                    dimensions = self.page.locator(f"#{chart}").evaluate("""mount => {
                        const bounds=mount.getBoundingClientRect(),svg=mount.querySelector('svg'),box=svg.getBoundingClientRect();
                        const glyphs=[...svg.querySelectorAll('text')].map(text=>text.getBoundingClientRect());
                        return {left:bounds.left,right:bounds.right,top:bounds.top,bottom:bounds.bottom,
                                svgLeft:box.left,svgRight:box.right,svgTop:box.top,svgBottom:box.bottom,
                                clientWidth:mount.clientWidth,scrollWidth:mount.scrollWidth,
                                clippedGlyphs:glyphs.filter(rect=>rect.left<box.left-1||rect.right>box.right+1||rect.top<box.top-1||rect.bottom>box.bottom+1).length};
                    }""")
                    self.assertLessEqual(dimensions["scrollWidth"], dimensions["clientWidth"] + 1, dimensions)
                    self.assertGreaterEqual(dimensions["svgLeft"], dimensions["left"] - 1, dimensions)
                    self.assertLessEqual(dimensions["svgRight"], dimensions["right"] + 1, dimensions)
                    self.assertGreaterEqual(dimensions["svgTop"], dimensions["top"] - 1, dimensions)
                    self.assertLessEqual(dimensions["svgBottom"], dimensions["bottom"] + 1, dimensions)
                    self.assertEqual(dimensions["clippedGlyphs"], 0, "Both North Indian charts must show their labels within their fitted SVG.")
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width + 1)
        self.page.locator("#tc-latitude").fill("85")
        self.page.locator("#tc-calculate").click()
        expect(self.page.locator("#tc-status")).to_have_attribute("data-state", "error")
        expect(self.page.locator("#tc-planets tbody tr[data-planet]")).to_have_count(0)
        expect(self.page.locator("#tc-rashi-chart svg")).to_have_count(0)
        self.assertIsNone(self.page.evaluate("window.KPTransitChart.getData()"),
                          "Invalid geometry must clear the old chart rather than leaving stale values visible.")

    def test_transit_chart_print_selection_uses_current_date_and_static_chart_data(self):
        self.prepare_exact_dasha()
        place = '<img src=x onerror="window.tcInjected=true"> · Pune'
        data = self.configure_transit_chart(place=place)
        source_tables = {table_id: self.table_rows(self.page.locator(f"#{table_id}"))
                         for table_id in ("tc-planets", "tc-cusps", "tc-dasha", "tc-pd-periods")}
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        self.go("transit-chart")
        self.page.locator("#tc-print").click()
        expect(self.page.locator("main > #report")).to_be_visible()
        option = self.page.locator("#report-page-options [data-report-page-key='transit-chart']")
        expect(option).to_be_checked()
        self.assertEqual(self.page.locator("#report-page-options input:checked").evaluate_all(
            "options => options.map(option => option.dataset.reportPageKey)"), ["transit-chart"])
        self.page.locator("#report-clear-pages").click()
        option.check()
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
        popup.on("pageerror", lambda error: self.errors.append("Transit Chart print popup: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(1)
        report = popup.locator('body > [data-report-section="transit-chart"]')
        expect(report).to_contain_text("06/10/2026")
        expect(report).to_contain_text("05:30:00")
        expect(report).to_contain_text("UTC +5.5")
        expect(report).to_contain_text(place)
        expect(report).to_contain_text("Transit Placidus cusps")
        expect(report.locator("input,select,textarea,button,img")).to_have_count(0)
        self.assertFalse(popup.evaluate("Boolean(window.tcInjected)"))
        self.assertFalse(self.page.evaluate("Boolean(window.tcInjected)"))
        for table_id, expected_rows in source_tables.items():
            self.assertEqual(self.table_rows(report.locator(f'[data-report-id="{table_id}"]')), expected_rows,
                             "The printed transit chart must match the current selected moment's calculations.")
        for chart in ("tc-rashi-chart", "tc-bhav-chart"):
            expect(report.locator(f'[data-report-id="{chart}"] svg g[data-house]')).to_have_count(12)
            expect(report.locator(f'[data-report-id="{chart}"] svg tspan[data-planet]')).to_have_count(9)
        self.assertEqual(self.page.evaluate("window.KPTransitChart.getData().utc"), data["utc"])
        popup.emulate_media(media="print")
        expect(report).to_be_visible()
        clipped = report.evaluate("""page => {
            const bounds=page.getBoundingClientRect();
            return [...page.querySelectorAll('table,svg,.tc-report-summary')].filter(element=>{
                const box=element.getBoundingClientRect();
                return box.width<=0||box.height<=0||box.left<bounds.left-1||box.right>bounds.right+1||box.top<bounds.top-1||box.bottom>bounds.bottom+1;
            }).map(element=>element.dataset.reportId||element.className);
        }""")
        self.assertEqual(clipped, [], "Selected charts, native dasha and position tables must remain visible inside their printed section.")
        popup.close()

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
                expect(rp.locator(f'[data-field="{field}"]')).to_have_text(source.locator(f'[data-field="{field}"] .kp-planet-label').text_content())
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
        self.page.locator('#home-dasha-table [data-dasha-depth="0"]').click()
        expect(self.page.locator('#home-dasha-table tr[data-dasha-row]')).to_have_count(9)
        self.page.locator('#home-dasha-table tr[data-dasha-row="0"]').click()
        data = self.page.evaluate("window.KPHomeDasha.getData()")
        self.assertEqual((data["level"], data["levels"][0]["rows"][data["path"][0]]["lord"]), ("AD", "केतू"))
        self.assertEqual(data["rows"][0]["lord"], "केतू")
        self.assertAlmostEqual(sum(row["durationDays"] for row in data["rows"]), 7 * 360)
        for expected_level in ("PD", "SD", "PrD"):
            self.page.locator('#home-dasha-table tr[data-dasha-row="0"]').click()
            self.assertEqual(self.page.evaluate("window.KPHomeDasha.getData().level"), expected_level)
            expect(self.page.locator('#home-dasha-table tr[data-dasha-row]')).to_have_count(9)
        self.page.locator('#home-dasha-table thead [data-dasha-depth="0"]').click()
        self.assertEqual(self.page.evaluate("window.KPHomeDasha.getData().depth"), 0)
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

    def test_kundali_context_menu_switches_source_and_home_without_changing_transit_chart(self):
        self.prepare_exact_dasha()
        transit = self.configure_transit_chart()
        native = self.outputs()
        expected = self.page.evaluate("""() => ({planets:Object.fromEntries(window.currentKPModel.planets.map(point=>[point.id,point.longitude])),
            cusps:Object.fromEntries(window.currentKPModel.houses.map(point=>[point.id,point.longitude]))})""")
        self.go("south9")
        expect(self.page.locator("#kundali")).to_be_visible()
        self.page.locator("#kundali").click(button="right")
        menu = self.page.locator("#kundali-style-menu")
        expect(menu).to_be_visible()
        expect(menu).to_have_attribute("role", "menu")
        expect(self.page.locator("#kundali-style-south")).to_have_attribute("aria-checked", "true")
        expect(self.page.locator("#kundali-style-north")).to_have_attribute("role", "menuitemradio")
        self.page.locator("#kundali-style-north").click()
        expect(menu).not_to_be_visible()
        expect(self.page.locator("#kundali")).not_to_be_visible()
        expect(self.page.locator("#kundali-north")).to_be_visible()
        expect(self.page.locator('#south9 [data-kundali-style-control]')).to_have_value("north")
        expect(self.page.locator('#south9 button[onclick="enableKundaliEdit()"]')).to_be_disabled()
        self.assertEqual(self.page.evaluate("window.KPChartStyle.getStyle()"), "north")
        self.assertEqual(self.page.locator('#kundali-north [data-planet]').evaluate_all(
            "points=>Object.fromEntries(points.map(point=>[point.dataset.planet,Number(point.dataset.longitude)]))"), expected["planets"])
        self.assertEqual(self.page.locator('#kundali-north [data-cusp]').evaluate_all(
            "points=>Object.fromEntries(points.map(point=>[point.dataset.cusp,Number(point.dataset.longitude)]))"), expected["cusps"])
        self.assertEqual(self.page.locator('#kundali-north g[data-rashi-house="1"]').get_attribute("data-sign"), "1")
        self.go("home")
        expect(self.page.locator("#home-kundali-title")).to_have_text("North Indian kundali")
        mirror = self.home_source("kundali-north")
        expect(mirror).to_be_visible()
        expect(mirror.locator("svg [data-planet]")).to_have_count(9)
        expect(mirror.locator("svg [data-cusp]")).to_have_count(12)
        self.assertEqual(mirror.locator("svg").inner_html(), self.page.locator("#kundali-north svg").inner_html())
        self.page.locator("#home-kundali").click(button="right")
        expect(menu).to_be_visible()
        expect(self.page.locator("#kundali-style-north")).to_have_attribute("aria-checked", "true")
        self.page.keyboard.press("Escape")
        expect(menu).not_to_be_visible()
        expect(self.page.locator("#home-kundali")).to_be_focused()
        self.page.keyboard.press("Shift+F10")
        expect(menu).to_be_visible()
        self.page.keyboard.press("ArrowDown")
        expect(self.page.locator("#kundali-style-south")).to_be_focused()
        self.page.keyboard.press("Enter")
        expect(menu).not_to_be_visible()
        expect(self.home_source("kundali")).to_be_visible()
        expect(self.page.locator('#home [data-kundali-style-control]')).to_have_value("south")
        self.assertEqual(self.outputs(), native, "Changing display layout must retain natal calculations.")
        self.assertEqual(self.page.evaluate("window.KPTransitChart.getData()"), transit,
                         "The natal layout menu must not change the separate Transit Chart's selected moment or calculations.")
        self.page.set_viewport_size({"width":390,"height":844})
        self.page.locator('#home [data-kundali-style-control]').select_option("north")
        expect(self.home_source("kundali-north")).to_be_visible()
        size = self.page.locator("#home-kundali").evaluate("""mount=>({width:mount.clientWidth,height:mount.clientHeight,
            scrollWidth:mount.scrollWidth,scrollHeight:mount.scrollHeight})""")
        self.assertLessEqual(size["scrollWidth"], size["width"] + 1, "North Indian Home chart must fit without a horizontal moving bar.")
        self.assertLessEqual(size["scrollHeight"], size["height"] + 1, "North Indian Home chart must fit without a vertical moving bar.")
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 391)
        # Context-menu gestures on the independent transit chart retain normal
        # browser behavior and must not open the natal chart layout menu.
        self.go("transit-chart")
        self.page.locator("#tc-rashi-chart").dispatch_event("contextmenu", {"clientX":100,"clientY":100})
        expect(menu).not_to_be_visible()

    def test_kundali_layout_backup_print_and_south_manual_notes_survive_north_selection(self):
        self.prepare_exact_dasha()
        self.go("south9")
        self.page.locator('button[onclick="enableKundaliEdit()"]').click()
        note = '<img src=x onerror="window.noteInjected=true"> · South notes'
        cell = self.page.locator('#kundali .v38-cell[data-sign-index="0"]')
        center = self.page.locator("#kundali .v38-center")
        cell.fill(note)
        center.fill("Original manual center · मीरा")
        self.page.locator("#kundali").click(button="right")
        self.page.locator("#kundali-style-north").click()
        backup = self.page.evaluate("window.getChartData()")
        self.assertEqual(backup["fields"]["kundali-chart-style"]["value"], "north")
        self.assertTrue(backup["kundali"]["manual"])
        self.assertEqual(next(row["text"] for row in backup["kundali"]["cells"] if row["signIndex"] == 0), note)
        self.page.locator('#south9 [data-kundali-style-control]').select_option("south")
        center.fill("Unsaved manual edit")
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="north-and-south-notes.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported")
        self.go("south9")
        expect(self.page.locator("#kundali-north")).to_be_visible()
        expect(cell).to_have_text(note)
        expect(center).to_have_text("Original manual center · मीरा")
        self.action("save")
        self.page.locator('#south9 [data-kundali-style-control]').select_option("south")
        self.action("load")
        expect(self.page.locator("#kundali-north")).to_be_visible()
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        self.page.locator('#report-page-options [data-report-page-key="south9"]').check()
        preview = self.page.locator('#printReport > [data-report-section="south9"]')
        expect(preview).to_contain_text("North Indian kundali and basic calculations")
        expect(preview.locator("span").filter(has_text=re.compile(r"^(north|south)$"))).to_have_count(0)
        expect(preview.locator('[data-report-id="kundali-north"] svg [data-planet]')).to_have_count(9)
        expect(preview.locator('[data-report-id="kundali"]')).to_have_count(0)
        self.page.evaluate("""() => { const original=window.open; window.open=function(...args) {
            const popup=original.apply(window,args); if(popup)popup.print=()=>{popup.testPrintCalled=true;}; return popup;
        }; }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Kundali layout print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        report = popup.locator('body > [data-report-section="south9"]')
        expect(popup.locator("body > .report-page")).to_have_count(1)
        expect(report.locator('[data-report-id="kundali-north"]')).to_be_visible()
        expect(report.locator('[data-report-id="kundali"]')).to_have_count(0)
        expect(report.locator('[data-report-id="kundali-north"] svg [data-planet]')).to_have_count(9)
        expect(report.locator('[data-report-id="kundali-north"] svg [data-cusp]')).to_have_count(12)
        expect(report.locator("button,select,input,textarea,#kundali-style-menu")).to_have_count(0)
        expect(report.locator("span").filter(has_text=re.compile(r"^(north|south)$"))).to_have_count(0)
        popup.emulate_media(media="print")
        clipping = report.evaluate("""page=>{ const bounds=page.getBoundingClientRect(); return [...page.querySelectorAll('svg,.kp-table,.report-developer-footer')].filter(element=>{
                const box=element.getBoundingClientRect();return box.width<=0||box.height<=0||box.left<bounds.left-1||
                    box.right>bounds.right+1||box.top<bounds.top-1||box.bottom>bounds.bottom+1;
            }).map(element=>element.dataset.reportId||element.className); }""")
        self.assertEqual(clipping, [], "The selected North Indian chart and both basic tables must fit their printed page.")
        popup.close()
        self.go("home")
        self.page.locator('#home [data-kundali-style-control]').select_option("south")
        expect(self.home_source("kundali").locator('.v38-cell[data-sign-index="0"]')).to_have_text(note)
        expect(self.home_source("kundali").locator(".v38-center")).to_have_text("Original manual center · मीरा")
        self.assertFalse(self.page.evaluate("Boolean(window.noteInjected)"))
        expect(self.page.locator("#kundali img")).to_have_count(0)

    def test_south_kundali_displays_each_sign_star_and_sub_lord_on_home_and_print(self):
        self.prepare_exact_dasha()
        self.go("south9")
        expected = self.page.evaluate("""() => [
            ...window.currentKPModel.houses.map(point=>({kind:'cusp',name:point.name,sgl:point.sgl,stl:point.stl,sbl:point.sl})),
            ...window.currentKPModel.planets.map(point=>({kind:'planet',name:point.name,sgl:point.sgl,stl:point.stl,sbl:point.sl}))
        ].sort((a,b)=>(a.kind+':'+a.name).localeCompare(b.kind+':'+b.name))""")
        metadata = """chart => [...chart.querySelectorAll('.v38-item')].map(entry=>{
            const lords=entry.querySelector('.v38-lords');
            return {kind:entry.dataset.kind,name:entry.querySelector('.v38-name').textContent,
                sgl:lords?.dataset.sgl,stl:lords?.dataset.stl,sbl:lords?.dataset.sbl,text:lords?.textContent};
        }).sort((a,b)=>(a.kind+':'+a.name).localeCompare(b.kind+':'+b.name))"""
        def assert_labels(chart):
            expect(chart.locator(".v38-lords")).to_have_count(21)
            actual = chart.evaluate(metadata)
            self.assertEqual([{key:value for key,value in row.items() if key != "text"} for row in actual], expected)
            for row in actual:
                self.assertEqual(row["text"], f'({row["sgl"]}-{row["stl"]}-{row["sbl"]})',
                                 "Each small line must list sign, star and sub lord in the requested order.")
            self.assertEqual(next(row["text"] for row in actual if row["kind"] == "cusp" and row["name"] == "I"), "(Ma-Ke-Ke)")
            self.assertEqual(next(row["text"] for row in actual if row["kind"] == "planet" and row["name"] == "रवी"), "(Ma-Ke-Ma)")
        assert_labels(self.page.locator("#kundali"))
        self.go("home")
        assert_labels(self.home_source("kundali"))
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        self.page.locator('#report-page-options [data-report-page-key="south9"]').check()
        preview = self.page.locator('#printReport > [data-report-section="south9"]')
        expect(preview.locator("span").filter(has_text=re.compile(r"^(north|south)$"))).to_have_count(0)
        assert_labels(preview.locator('[data-report-id="kundali"]'))
        self.page.evaluate("""() => { const original=window.open; window.open=function(...args) {
            const popup=original.apply(window,args); if(popup)popup.print=()=>{popup.testPrintCalled=true;}; return popup;
        }; }""")
        with self.page.expect_popup() as popup_info:
            self.page.locator("#print-selected-report").click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Lord labels print: " + str(error)))
        popup.wait_for_function("window.testPrintCalled === true")
        popup.emulate_media(media="print")
        report = popup.locator('body > [data-report-section="south9"]')
        expect(report.locator("span").filter(has_text=re.compile(r"^(north|south)$"))).to_have_count(0)
        assert_labels(report.locator('[data-report-id="kundali"]'))
        popup.close()

    def test_home_dashboard_fits_desktop_and_mobile_with_separate_chart_lanes(self):
        self.prepare_exact_dasha()
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.go("home")
        viewports = ((1920, 1080), (1536, 960), (1280, 900), (390, 844))

        def assert_chart_fits_mount(width, height):
            self.page.set_viewport_size({"width": width, "height": height})
            # Let responsive layout and any ResizeObserver fitting settle.
            self.page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            dimensions = self.page.locator("#home-kundali").evaluate("""mount => {
                const chart = mount.querySelector('[data-home-source-id="kundali"]');
                const box = element => {
                    const rect = element.getBoundingClientRect();
                    return {left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom,width:rect.width,height:rect.height};
                };
                return {clientWidth:mount.clientWidth,scrollWidth:mount.scrollWidth,clientHeight:mount.clientHeight,
                        scrollHeight:mount.scrollHeight,mount:box(mount),chart:box(chart)};
            }""")
            self.assertGreater(dimensions["chart"]["width"], 0, "The fitted kundali must remain visible.")
            self.assertGreater(dimensions["chart"]["height"], 0, "The fitted kundali must remain visible.")
            self.assertLessEqual(dimensions["scrollWidth"], dimensions["clientWidth"] + 1,
                                 f"Home kundali must fit its panel without a horizontal scrollbar: {dimensions}")
            self.assertLessEqual(dimensions["scrollHeight"], dimensions["clientHeight"] + 1,
                                 f"Home kundali must fit its panel without a vertical scrollbar: {dimensions}")
            for near, far in (("left", "right"), ("top", "bottom")):
                self.assertGreaterEqual(dimensions["chart"][near], dimensions["mount"][near] - 1, dimensions)
                self.assertLessEqual(dimensions["chart"][far], dimensions["mount"][far] + 1, dimensions)
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width + 1,
                                 "Fitting the chart must not introduce horizontal page scrolling.")

        for width, height in viewports:
            with self.subTest(width=width, chart="regular", expanded=False):
                assert_chart_fits_mount(width, height)
        self.page.set_viewport_size({"width": 1920, "height": 1080})
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
        for width, height in viewports:
            with self.subTest(width=width, chart="regular", expanded=True):
                assert_chart_fits_mount(width, height)

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
                        for(const selector of ['.v38-name','.v38-degree',...(entry.querySelector('.v38-lords')?['.v38-lords']:[])]) {
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
            for expanded in (True, False):
                if toggle.get_attribute("aria-pressed") != str(expanded).lower():
                    self.page.set_viewport_size({"width": 1920, "height": 1080})
                    toggle.click()
                for width, height in viewports:
                    with self.subTest(width=width, cusps=cusp_count, planets=planet_count, expanded=expanded):
                        assert_chart_fits_mount(width, height)
                        geometry_errors = crowded.evaluate(geometry_script)
                        self.assertEqual(geometry_errors, [], "\n".join(geometry_errors))
                        self.assertTrue(all(text == "29°59′59″" for text in crowded.locator(".v38-degree").all_text_contents()))
        if toggle.get_attribute("aria-pressed") != "true":
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            toggle.click()
        self.page.set_viewport_size({"width": 390, "height": 844})
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
            cell = sun.locator(f'[data-field="{column}"]')
            expect(cell.locator(".kp-planet-label") if column in ("stl", "sl", "ssl") else cell).to_have_text(value)
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
        expect(printed_planets.locator('tr[data-planet="Su"] [data-field="ssl"] .kp-planet-label')).to_have_text("Ju")
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
                    for (const selector of ['.v38-name', '.v38-degree', ...(entry.querySelector('.v38-lords') ? ['.v38-lords'] : [])]) {
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
                    for (let i=0; i<textRects.length; i++) for (let j=i+1; j<textRects.length; j++)
                        if (overlaps(textRects[i],textRects[j])) errors.push(`Entry labels overlap: ${description}`);
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

    def test_single_page_report_contains_current_native_model_fourfold_and_all_md_ad_starts(self):
        self.prepare_exact_dasha("186:37:11", dob="1986-07-15")
        self.go("basic")
        for id, text in {"name":"Single-page native · मीरा", "birthTime":"15:45:00", "birthPlace":"Nashik",
                         "lat":"19:59:50", "lon":"73:47:27"}.items():
            self.page.locator(f"#{id}").fill(text)
        self.go("astrosettings")
        self.show_astrologer_fields()
        for id, text in {"astroName":"Current single-page astrologer", "astroMobile":"9876543210",
                         "astroAddress":"Current office · Nashik"}.items():
            self.page.locator(f"#{id}").fill(text)
        self.action("calculate")
        model = self.page.evaluate("window.currentKPModel")
        timeline = self.page.evaluate("""() => window.mdDashaPeriods.map(period=>({key:period.key,
            lord:window.KPDisplay.idByName[period.lord],end:period.end,
            ads:window.calculateAntardashas(period).map(ad=>({lord:window.KPDisplay.idByName[ad.lord],
                start:ad.start,end:ad.end,birthActive:ad.birthActive}))}))""")
        selected_ad = self.page.locator("#adMDSelect").input_value()
        self.go("report")
        report = self.page.locator('#printReport > [data-report-section="single-page"]')
        expect(report).to_have_attribute("data-ready", "true")
        expect(report.locator(".sp-chart")).to_have_attribute("data-source-chart", "kundali")
        expect(report.locator(".sp-chart .v38-center")).to_have_text("ॐ")
        expect(report.locator(".sp-chart .v38-center")).not_to_contain_text("Single-page native")
        columns = report.locator(".sp-column").evaluate_all("elements=>elements.map(element=>element.getBoundingClientRect().width)")
        self.assertEqual(len(columns), 2)
        self.assertAlmostEqual(columns[0], columns[1], delta=1)
        native = {"name":"Single-page native · मीरा", "dob":"15/07/1986", "time":"03:45:00 PM",
                  "place":"Nashik", "latitude":"19° 59′ 50″ N", "longitude":"73° 47′ 27″ E",
                  "timezone":"+05:30", "dst":"0", "weekday":"Tuesday", "nakshatra":"Chitra",
                  "star-lord":"Mars", "pada":"4", "rashi":"Libra", "tithi":"Pratipada",
                  "paksha":"Krishna", "yoga":"Vajra", "karana":"Balava"}
        for field, expected in native.items():
            expect(report.locator(f'[data-native-field="{field}"]')).to_have_attribute("data-value", expected)
            expect(report.locator(f'[data-native-field="{field}"]')).to_contain_text(expected)
        for field, expected in {"name":"Current single-page astrologer", "mobile":"9876543210", "address":"Current office · Nashik"}.items():
            expect(report.locator(f'[data-astrologer-field="{field}"]')).to_contain_text(expected)
        for credits in ("Light of KP Astrology", "Andrew Dutta", "TSRh.ws"):
            expect(report).not_to_contain_text(credits)

        for key, rows, fields, identity in (
            ("basic-planet", model["planets"], ("signCode","degree","occ","own","sgl","stl","sl","ssl"), "planet"),
            ("basic-house", model["houses"], ("signCode","degree","occ","sgl","stl","sl","ssl"), "house"),
            ("fourfold-planet", model["fourfold"]["planets"], ("A","B","C","D"), "planet"),
            ("fourfold-house", model["fourfold"]["houses"], ("A","B","C","D"), "house"),
        ):
            table = report.locator(f'[data-single-table="{key}"]')
            expect(table.locator("tbody tr")).to_have_count(len(rows))
            for row in rows:
                printed = table.locator(f'tr[data-{identity}="{row["id"]}"]')
                for field in fields:
                    cell = printed.locator(f'[data-field="{field}"]')
                    expected = row[field]
                    encoded = cell.get_attribute("data-value")
                    self.assertEqual(json.loads(encoded) if isinstance(expected,list) else encoded,
                                     expected if isinstance(expected,list) else str(expected), (key,row["id"],field))
                    text = cell.evaluate(r"""cell=>{const copy=cell.cloneNode(true);copy.querySelectorAll('.sp-marker').forEach(marker=>marker.remove());
                        return copy.textContent.replace(/\s/g,'');}""")
                    wanted = ",".join(str(item) for item in expected) if isinstance(expected,list) else re.sub(r"\s", "", str(expected))
                    self.assertIn(text, (wanted, "—") if wanted == "" else (wanted,), (key,row["id"],field))
                if key.startswith("basic"):
                    expect(printed.locator('[data-field="nak"]')).to_have_text(f'{row["nakCode"]} ({row["pada"]})')
        cards = report.locator("[data-single-md-key]")
        expect(cards).to_have_count(9)
        expect(cards.locator("tbody tr[data-ad-lord]")).to_have_count(81)
        for index, period in enumerate(timeline):
            card = cards.nth(index)
            expect(card).to_have_attribute("data-single-md-key", period["key"])
            expect(card).to_have_attribute("data-md-lord", period["lord"])
            expect(card).to_have_attribute("data-md-end", period["end"])
            expect(card).to_have_attribute("data-md-full-start", period["ads"][0]["start"])
            rows = card.locator("tbody tr")
            for ordinal, ad in enumerate(period["ads"]):
                row = rows.nth(ordinal)
                expect(row).to_have_attribute("data-ad-lord", ad["lord"])
                expect(row).to_have_attribute("data-period-start", ad["start"])
                expect(row).to_have_attribute("data-period-end", ad["end"])
                expect(row).to_have_attribute("data-birth-active", str(ad["birthActive"]).lower())
                expect(row.locator("td")).to_have_text(datetime.strptime(ad["start"],"%Y-%m-%d").strftime("%d/%m/%Y"))
        expect(cards.first).to_have_attribute("data-md-lord", "Ma")
        expect(cards.first).to_have_attribute("data-md-full-start", "1979-07-25")
        expect(cards.first).to_have_attribute("data-md-end", "1986-07-24")
        expect(cards.first.locator('tr[data-birth-active="true"]')).to_have_attribute("data-ad-lord", "Mo")
        self.assertEqual(self.page.evaluate("window.currentKPModel"), model)
        expect(self.page.locator("#adMDSelect")).to_have_value(selected_ad)

    def test_single_page_panchang_matches_independent_sample_and_exact_lunar_boundaries(self):
        sample = self.page.evaluate("window.KPSinglePageReport.panchang(320649,671729,'1986-07-15')")
        for key, expected in {"tithi":"Navami","paksha":"Shukla","yoga":"Siddha","karana":"Balava",
                              "nakshatra":"Chitra","nakLord":"Mars","pada":4,"rashi":"Libra","weekday":"Tuesday"}.items():
            self.assertEqual(sample[key], expected)
        # Independent 12° tithi, 6° karana and 13°20′ yoga/nakshatra boundaries.
        fixtures = (
            (21599,{"tithi":"Pratipada","karana":"Kimstughna"}),
            (21600,{"tithi":"Pratipada","karana":"Bava"}),
            (43199,{"tithi":"Pratipada","karana":"Bava"}),
            (43200,{"tithi":"Dwitiya","karana":"Balava"}),
            (647999,{"tithi":"Purnima","paksha":"Shukla","karana":"Bava"}),
            (648000,{"tithi":"Pratipada","paksha":"Krishna","karana":"Balava"}),
            (1231199,{"karana":"Vishti"}), (1231200,{"karana":"Shakuni"}),
            (1252800,{"tithi":"Amavasya","karana":"Chatushpada"}), (1274400,{"karana":"Naga"}),
            (47999,{"yoga":"Vishkambha","nakshatra":"Ashwini","pada":4}),
            (48000,{"yoga":"Priti","nakshatra":"Bharani","pada":1}),
            (959999,{"yoga":"Shiva"}), (960000,{"yoga":"Siddha"}),
            (1008000,{"yoga":"Sadhya"}), (1248000,{"yoga":"Vaidhriti"}),
            (1296000,{"tithi":"Pratipada","paksha":"Shukla","karana":"Kimstughna","yoga":"Vishkambha","rashi":"Aries"}),
            (11999,{"pada":1}), (12000,{"pada":2}),
            (107999,{"rashi":"Aries"}), (108000,{"rashi":"Taurus"}),
        )
        actual = self.page.evaluate("fixtures=>fixtures.map(([moon])=>window.KPSinglePageReport.panchang(0,moon,'2000-01-01'))", fixtures)
        for (moon, expected), result in zip(fixtures, actual):
            with self.subTest(moon_arcseconds=moon):
                for field, wanted in expected.items():
                    self.assertEqual(result[field], wanted)
                self.assertEqual(result["weekday"], "Saturday")
        invalid = self.page.evaluate("""() => [window.KPSinglePageReport.panchang(null,0,'2000-01-01'),
            window.KPSinglePageReport.panchang(0,NaN,'2000-01-01'),window.KPSinglePageReport.panchang(0,Infinity,'2000-01-01'),
            window.KPSinglePageReport.panchang(0,0,'2024-02-30').weekday]""")
        self.assertEqual(invalid, [None,None,None,"—"])

    def test_single_page_selected_print_is_one_complete_a4_pdf_in_both_styles_with_large_preferences(self):
        self.prepare_exact_dasha("186:37:11", dob="1986-07-15")
        model = self.page.evaluate("window.currentKPModel")
        self.go("report")
        self.page.emulate_media(media="print")
        self.page.wait_for_function("""() => {
            const cell=document.querySelector('.report-single-page [data-single-table="basic-planet"] tbody td');
            return cell?.isConnected&&parseFloat(getComputedStyle(cell).fontSize)>0;
        }""")
        original_font = self.page.evaluate("""() => getComputedStyle(document.querySelector(
            '.report-single-page [data-single-table="basic-planet"] tbody td')).fontSize""")
        self.page.emulate_media(media="screen")
        for style, source in (("south","kundali"),("north","kundali-north")):
            with self.subTest(chart_style=style):
                self.save_software_preferences(chartStyle=style,showFortuna=True,notationMarkers=True,
                                               interpretiveSize="large",planetSize="large",degreeSize="large",tableSize="large")
                popup = self.selected_report_popup(["single-page"])
                try:
                    expect(popup.locator("body > .report-page")).to_have_count(1)
                    report = popup.locator('body > [data-report-section="single-page"]')
                    expect(report).to_have_attribute("data-ready", "true")
                    expect(report.locator(".sp-chart")).to_have_attribute("data-source-chart", source)
                    expect(report.locator('[data-single-table="basic-planet"] tbody tr')).to_have_count(9)
                    expect(report.locator('[data-single-table="basic-house"] tbody tr')).to_have_count(12)
                    expect(report.locator(".sp-md-card tbody tr")).to_have_count(81)
                    expect(report.locator("input,select,textarea,button,[id]")).to_have_count(0)
                    expect(report.locator('.sp-chart [data-planet="Fo"]')).to_have_count(1)
                    for id in ("Su","Mo","Ma","Me","Ju","Ve","Sa","Ra","Ke"):
                        marker = report.locator(f'[data-single-table="basic-planet"] tr[data-planet="{id}"] th .sp-marker').evaluate_all(
                            "elements=>elements.map(element=>element.dataset.marker)")
                        self.assertEqual(marker,self.page.evaluate("id=>window.KPDisplay.getNotations(id)",id))
                    popup.emulate_media(media="print")
                    self.assertEqual(report.locator('[data-single-table="basic-planet"] tbody td').first.evaluate(
                        "element=>getComputedStyle(element).fontSize"), original_font,
                        "Global large fonts must leave the single-page report's compact metrics intact.")
                    self.assert_single_page_geometry(popup)
                    pdf = popup.pdf(format="A4",print_background=True,prefer_css_page_size=True)
                    self.assertEqual(len(re.findall(rb"/Type\s*/Page\b",pdf)),1,
                                     "The selected compact report must generate one physical PDF sheet.")
                    media = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]",pdf)
                    self.assertIsNotNone(media, "Chromium's PDF must declare its paper size.")
                    self.assertAlmostEqual(float(media.group(1)),595.28,delta=1)
                    self.assertAlmostEqual(float(media.group(2)),841.89,delta=1)
                finally:
                    popup.close()
        self.assertEqual(self.page.evaluate("window.currentKPModel"), model)

    def test_single_page_report_clears_incomplete_data_and_preserves_escaped_long_details_on_mobile(self):
        self.prepare_exact_dasha("186:37:11",dob="1986-07-15")
        native = 'मीरा <img src=x onerror="window.singleInjected=true"> & extended native name'
        astrologer = 'Astrologer <script>window.singleInjected=true</script> & current consultation'
        address = "Current consultation office, "+"long address details · "*7
        self.go("basic")
        self.page.locator("#name").fill(native)
        self.go("astrosettings")
        self.show_astrologer_fields()
        self.page.locator("#astroName").fill(astrologer)
        self.page.locator("#astroAddress").fill(address)
        self.action("calculate")
        self.go("report")
        report = self.page.locator('.report-single-page')
        expect(report.locator('[data-native-field="name"]')).to_have_attribute("data-value", native)
        expect(report.locator('[data-native-field="name"]')).to_contain_text(native)
        expect(report.locator('[data-astrologer-field="name"]')).to_contain_text(astrologer)
        expect(report.locator('[data-astrologer-field="address"]')).to_contain_text(address.strip())
        expect(report.locator("script,img[src='x']")).to_have_count(0)
        self.assertFalse(self.page.evaluate("window.singleInjected===true"))
        popup = self.selected_report_popup(["single-page"])
        try:
            popup.emulate_media(media="print")
            self.assert_single_page_geometry(popup)
            expect(popup.locator('[data-native-field="name"]')).to_contain_text(native)
            expect(popup.locator('[data-astrologer-field="name"]')).to_contain_text(astrologer)
            expect(popup.locator("script,img[src='x']")).to_have_count(0)
        finally:
            popup.close()
        self.page.set_viewport_size({"width":390,"height":844})
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"),391)
        self.assertLessEqual(self.page.evaluate("document.body.scrollWidth"),391)
        expect(report.locator(".sp-md-card tbody tr")).to_have_count(81)
        self.page.set_viewport_size({"width":1280,"height":900})
        self.go("planet")
        self.page.locator("#p6_d_1").fill("")
        self.page.locator("#p6_t_1").fill("")
        self.action("calculate")
        self.go("report")
        expect(report).to_have_attribute("data-ready","false")
        expect(report.locator(".sp-status").first).to_be_visible()
        expect(report.locator("[data-single-md-key]")).to_have_count(0)
        expect(report.locator("tr[data-period-start]")).to_have_count(0)
        for field in ("tithi","nakshatra","yoga","karana"):
            expect(report.locator(f'[data-native-field="{field}"]')).to_have_attribute("data-value","")
        values = report.locator('[data-single-table] td[data-value]').evaluate_all("elements=>elements.map(element=>element.dataset.value)")
        self.assertTrue(values and all(value=="" for value in values), "Incomplete input must clear all stale calculated table values.")
        self.go("planet")
        self.page.locator("#p6_d_1").fill("186:37:11")
        self.page.locator("#p6_t_1").fill("186:37:11")
        self.action("calculate")
        self.go("report")
        expect(report).to_have_attribute("data-ready","true")
        expect(report.locator(".sp-md-card tbody tr")).to_have_count(81)

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
        self.show_astrologer_fields()
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
        expect(self.page.locator("#printReport > .report-page").nth(1)).to_have_attribute("data-report-section", "single-page")
        expect(self.page.locator("#printReport > .report-page").nth(2)).to_have_attribute("data-report-section", "basic")
        expect(self.page.locator("#printReport > .report-page").last).to_have_attribute("data-report-section", "south9")

        self.go("basic")
        self.page.locator("#name").fill("")
        self.go("astrosettings")
        self.show_astrologer_fields()
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

    def test_print_popup_has_selectable_a4_sections_without_duplicate_ids(self):
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
            return {section: page.dataset.reportSection, width: parseFloat(style.width), height: parseFloat(style.height),
                    maxHeight: style.maxHeight, overflow: style.overflow, display: style.display, breakAfter: style.breakAfter};
        })""")
        for index, geometry in enumerate(page_geometry):
            with self.subTest(print_page=index + 1):
                self.assertNotEqual(geometry["display"], "none", "Every report page must be visible when printing.")
                self.assertAlmostEqual(geometry["width"], 190 * 96 / 25.4, delta=1)
                if geometry["section"] in ("prediction", "aspects", "transit", "transit-chart", "transit-panchang", "ephemeris", "event-promise", "nadi-astrology", "ruling-planets", "matchmaking"):
                    self.assertGreaterEqual(geometry["height"], 277 * 96 / 25.4 - 1)
                    self.assertEqual(geometry["maxHeight"], "none", "Variable-length results must continue onto later sheets.")
                    self.assertEqual(geometry["overflow"], "visible", "Aspect and transit results must not be clipped at A4 height.")
                else:
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

    def test_selected_aspect_and_transit_reports_preserve_current_results_without_controls(self):
        self.prepare_exact_dasha()
        self.go("aspects")
        self.page.locator("#western-angle-30").check()
        self.page.locator("#western-orb-30").fill("1.5")
        self.go("transit")
        self.page.locator("#tr-mode").select_option("sun")
        self.page.locator("#tr-dasha-source").select_option("manual")
        self.page.locator("#tr-md").select_option("Ju")
        self.page.locator("#tr-ad").select_option("Sa")
        self.page.locator("#tr-timezone").select_option("0")
        self.page.locator("#tr-start").fill("2026-01-01")
        self.page.locator("#tr-end").fill("2026-12-31")
        results = self.run_transit_search()
        self.assertEqual(len(results), 2, "This Sun fixture must have both simultaneous MD / AD combinations.")
        transit_rows = self.page.locator("#tr-result-rows").evaluate("""body => [...body.rows].map(row =>
            [...row.cells].map(cell => cell.textContent.trim()))""")

        self.go("aspects")
        self.page.locator("#western-angle-90").uncheck()
        self.page.locator("#western-orb-30").fill("2.25")
        self.assertEqual(self.page.evaluate("window.KPTransit.getResults()"), results,
                         "Changing aspect choices or orbs must preserve an independently completed transit search.")
        expect(self.page.locator("#tr-result-rows tr[data-entry]")).to_have_count(len(results))
        aspect_rows = {table_id: self.table_rows(self.page.locator(f"#{table_id}"))
                       for table_id in ("western-planet-aspects", "western-cusp-aspects")}

        self.page.locator(".backup-menu > summary").click()
        self.page.locator(".global-actions [data-action='print']").click()
        expect(self.page.locator("main > #report")).to_be_visible()
        self.assertEqual(self.page.evaluate("window.KPTransit.getResults()"), results,
                         "Opening Print must preserve a completed search when natal calculations have not changed.")
        self.page.locator("#report-clear-pages").click()
        for section in ("transit", "aspects"):
            option = self.page.locator(f"#report-page-options [data-report-page-key='{section}']")
            expect(option).to_be_visible()
            option.check()
        self.page.evaluate("window.renderReport()")
        self.assertEqual(self.page.locator("#report-page-options input:checked").evaluate_all(
            "options => options.map(option => option.dataset.reportPageKey)"), ["aspects", "transit"])

        def assert_snapshot(target, prefix):
            aspects = target.locator(f'{prefix}[data-report-section="aspects"]')
            expect(aspects).to_contain_text("orb 2.25°")
            expect(aspects).not_to_contain_text("Square · 90°")
            for table_id, expected_rows in aspect_rows.items():
                self.assertEqual(self.table_rows(target.locator(f'{prefix}[data-report-section="aspects"] [data-report-id="{table_id}"]')),
                                 expected_rows, "The aspect report must retain the currently selected angles, orbs and results.")
            transit = target.locator(f'{prefix}[data-report-section="transit"] [data-report-id="tr-result-rows"]')
            self.assertEqual(transit.evaluate("""body => [...body.rows].map(row =>
                [...row.cells].map(cell => cell.textContent.trim()))"""), transit_rows,
                             "The transit report must retain the computed entry and exit dates without requiring another search.")
            self.assertEqual(transit.locator("tr[data-entry]").evaluate_all("rows => rows.map(row => row.dataset.entry)"),
                             [row["start"] for row in results])
            for section in ("aspects", "transit"):
                expect(target.locator(f'{prefix}[data-report-section="{section}"] input, '
                                      f'{prefix}[data-report-section="{section}"] select, '
                                      f'{prefix}[data-report-section="{section}"] textarea, '
                                      f'{prefix}[data-report-section="{section}"] button')).to_have_count(0)

        assert_snapshot(self.page, "#printReport > ")
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
        popup.on("pageerror", lambda error: self.errors.append("Aspect / transit print popup: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(2)
        self.assertEqual(popup.locator("body > .report-page").evaluate_all("pages => pages.map(page => page.dataset.reportSection)"),
                         ["aspects", "transit"], "Selected sections must print in report order, regardless of click order.")
        popup.emulate_media(media="print")
        assert_snapshot(popup, "body > ")
        for section in ("aspects", "transit"):
            expect(popup.locator(f'body > [data-report-section="{section}"]')).to_be_visible()
        self.assertEqual(self.page.evaluate("window.KPTransit.getResults()"), results,
                         "The final Print action must preserve the source search results as well as the printed snapshot.")
        popup.close()

        self.go("planet")
        self.page.locator("#p6_d_0").fill("10:00:00")
        self.page.locator("#p6_t_0").fill("10:00:00")
        expect(self.page.locator("#tr-result-rows tr[data-entry]")).to_have_count(0)
        self.go("report")
        expect(self.page.locator('[data-report-section="transit"] [data-report-id="tr-result-rows"] tr[data-entry]')).to_have_count(0)
        self.assertEqual(self.page.evaluate("window.KPTransit.getResults()"), [],
                         "Changing a natal calculation must invalidate old transit dates before they can be printed.")

    def test_long_aspect_and_transit_reports_flow_beyond_a4_without_clipping_rows(self):
        self.prepare_exact_dasha()
        self.go("aspects")
        for angle in (0, 30, 45, 60, 90, 120, 135, 150, 180):
            self.page.locator(f"#western-angle-{angle}").check()
        self.page.locator("#western-orb").fill("15")
        aspect_counts = {table_id: self.page.locator(f"#{table_id} tbody tr[data-source]").count()
                         for table_id in ("western-planet-aspects", "western-cusp-aspects")}
        self.assertGreaterEqual(sum(aspect_counts.values()), 144,
                                "The fixture must exercise a long list of planet and cusp aspect rows.")
        self.go("transit")
        self.page.locator("#tr-mode").select_option("dasha")
        self.page.locator("#tr-dasha-source").select_option("manual")
        for role, planet in (("md", "Mo"), ("ad", "Sa"), ("pd", "Me")):
            self.page.locator(f"#tr-{role}").select_option(planet)
        self.page.locator("#tr-direction").select_option("MD>AD")
        self.page.locator("#tr-level").select_option("sub")
        self.page.locator("#tr-timezone").select_option("0")
        self.page.locator("#tr-start").fill("2026-01-01")
        self.page.locator("#tr-end").fill("2026-03-31")
        results = self.run_transit_search()
        self.assertGreater(len(results), 60, "A quarter-year Moon sub-lord search must exercise multiple printed sheets.")
        self.go("report")
        self.page.locator("#report-clear-pages").click()
        for section in ("aspects", "transit"):
            self.page.locator(f"#report-page-options [data-report-page-key='{section}']").check()
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
        popup.on("pageerror", lambda error: self.errors.append("Long results print popup: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        popup.emulate_media(media="print")
        for table_id, count in aspect_counts.items():
            expect(popup.locator(f'[data-report-id="{table_id}"] tbody tr[data-source]')).to_have_count(count)
        expect(popup.locator('[data-report-id="tr-result-rows"] tr[data-entry]')).to_have_count(len(results))
        layouts = popup.locator("body > .report-page").evaluate_all("""pages => pages.map(page => {
            const style = getComputedStyle(page), bounds = page.getBoundingClientRect();
            const errors = [];
            for (const row of page.querySelectorAll('tbody tr[data-source],tbody tr[data-entry]')) {
                const rect = row.getBoundingClientRect();
                if (rect.height <= 0 || rect.left < bounds.left - 1 || rect.right > bounds.right + 1 || rect.bottom > bounds.bottom + 1)
                    errors.push('Hidden or out-of-bounds result row');
                for (let parent = row.parentElement; parent && parent !== page.parentElement; parent = parent.parentElement) {
                    const css = getComputedStyle(parent), outer = parent.getBoundingClientRect();
                    if (['hidden','clip','auto','scroll'].includes(css.overflowY) && rect.bottom > outer.bottom + 1)
                        errors.push('Result row clipped by ' + parent.className);
                }
            }
            return {section: page.dataset.reportSection, width: bounds.width, height: bounds.height,
                    maxHeight: style.maxHeight, overflow: style.overflow, errors};
        })""")
        self.assertEqual([layout["section"] for layout in layouts], ["aspects", "transit"])
        for layout in layouts:
            with self.subTest(section=layout["section"]):
                self.assertAlmostEqual(layout["width"], 190 * 96 / 25.4, delta=1)
                self.assertGreater(layout["height"], 277 * 96 / 25.4,
                                   "A long results section must expand onto additional A4 sheets.")
                self.assertEqual(layout["maxHeight"], "none")
                self.assertEqual(layout["overflow"], "visible")
                self.assertEqual(layout["errors"], [], "Every current result row must remain visible within the flow layout.")
        popup.close()

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
        expect(self.page.locator("#report-page-options label:has([data-report-page-key='mdcalc'])")).to_contain_text("Mahadasha (MD)")
        expect(self.page.locator("#report-page-options label:has([data-report-page-key='adcalc'])")).to_contain_text("Antardasha (AD)")
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
        selected_md = self.page.locator("#adMDSelect").input_value()
        self.page.locator('.md-workspace-nav a[href="#adcalc"]').click()
        self.page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        ad_bounds = self.page.locator("#adcalc").bounding_box()
        self.assertGreaterEqual(ad_bounds["y"], -1, "The AD shortcut must bring its table into view.")
        self.assertLess(ad_bounds["y"], self.page.viewport_size["height"] - 30,
                        "The AD shortcut must bring its table into view.")
        expect(self.page.locator("main > #mdcalc")).to_be_visible()
        expect(self.page.locator("#adMDSelect")).to_have_value(selected_md)
        self.assertEqual(self.dasha_rows(), venus_rows,
                         "Using the AD shortcut must preserve the selected MD and its calculated AD table.")
        self.go("report")
        report_ad = self.page.locator('#printReport > [data-report-section="adcalc"]')
        expect(report_ad).to_have_count(1)
        self.assertEqual(report_ad.locator('[data-report-id="adDashaRows"]').evaluate("""body => [...body.rows].map(row =>
            [...row.cells].map(cell => cell.textContent.trim()))"""), venus_rows,
                         "The AD report page must print the currently chosen MD's recalculated table.")
        expect(self.page.locator('#printReport > [data-report-section="mdcalc"] [data-report-id="adDashaRows"]')).to_have_count(0)

    def test_md_reconstructs_absolute_moon_from_all_twelve_signs(self):
        # Independent zodiac/nakshatra reference at 0° of each sign. The in-sign
        # Moon degree is identical in every case; its sign must change the MD.
        fixtures = (
            (0, "मेष", "अश्विनी", "केतू", "7 वर्ष 0 महिने 0 दिवस", "01/01/2007"),
            (30, "वृषभ", "कृत्तिका", "रवी", "4 वर्ष 6 महिने 0 दिवस", "01/07/2004"),
            (60, "मिथुन", "मृगशीर्ष", "मंगळ", "3 वर्ष 6 महिने 0 दिवस", "01/07/2003"),
            (90, "कर्क", "पुनर्वसू", "गुरु", "4 वर्ष 0 महिने 0 दिवस", "01/01/2004"),
            (120, "सिंह", "मघा", "केतू", "7 वर्ष 0 महिने 0 दिवस", "01/01/2007"),
            (150, "कन्या", "उत्तराफाल्गुनी", "रवी", "4 वर्ष 6 महिने 0 दिवस", "01/07/2004"),
            (180, "तुळ", "चित्रा", "मंगळ", "3 वर्ष 6 महिने 0 दिवस", "01/07/2003"),
            (210, "वृश्चिक", "विशाखा", "गुरु", "4 वर्ष 0 महिने 0 दिवस", "01/01/2004"),
            (240, "धनु", "मूळ", "केतू", "7 वर्ष 0 महिने 0 दिवस", "01/01/2007"),
            (270, "मकर", "उत्तराषाढा", "रवी", "4 वर्ष 6 महिने 0 दिवस", "01/07/2004"),
            (300, "कुंभ", "धनिष्ठा", "मंगळ", "3 वर्ष 6 महिने 0 दिवस", "01/07/2003"),
            (330, "मीन", "पूर्वाभाद्रपदा", "गुरु", "4 वर्ष 0 महिने 0 दिवस", "01/01/2004"),
        )
        self.prepare_exact_dasha()
        for absolute, sign, star, lord, balance, end in fixtures:
            with self.subTest(sign=sign, absolute=absolute):
                self.go("planet")
                for suffix in ("d", "t"):
                    self.page.locator(f"#p6_{suffix}_1").fill(f"{absolute:02d}:00:00")
                self.action("calculate")
                expect(self.page.locator("#p6_final_1")).to_have_value("0:00:00")
                expect(self.page.locator("#p6_rashi_1")).to_have_value("तुला" if sign == "तुळ" else sign)
                self.go("mdcalc")
                expect(self.page.locator("#mdMoonInfo")).to_have_value(f"{sign} — {star} — {lord}")
                expect(self.page.locator("#mdBirthDasha")).to_have_value(lord)
                expect(self.page.locator("#mdBhogyaDuration")).to_have_value(balance)
                expect(self.page.locator("#mdDashaEnd")).to_have_value(end)
                self.assertEqual(self.dasha_rows("#mdDashaRows")[0][0], lord)
                self.assertAlmostEqual(self.page.evaluate("window.currentKPModel.planets.find(p=>p.id==='Mo').longitude"), absolute*3600)

    def test_libra_chitra_user_fixture_keeps_exact_md_ad_pd_in_home_transit_and_report(self):
        # Moon 186°37′11″ is 169 arcseconds before Chitra's end. Mars's
        # remaining balance is 169/48000 × 7 × 360 = 8.8725 symbolic days.
        # Its elapsed 2511.1275 days fall in Moon AD (2310..2520) and Sun
        # PD (2509.5..2520). Display dates round the balance to nine days.
        self.prepare_exact_dasha("186:37:11", dob="1986-07-15")
        self.go("basic")
        self.page.locator("#birthTime").fill("15:45:00")
        self.action("calculate")
        self.go("mdcalc")
        expect(self.page.locator("#p6_rashi_1")).to_have_value("तुला")
        expect(self.page.locator("#mdMoonInfo")).to_have_value("तुळ — चित्रा — मंगळ")
        expect(self.page.locator("#mdBirthDasha")).to_have_value("मंगळ")
        expect(self.page.locator("#mdBhogyaDuration")).to_have_value("0 वर्ष 0 महिने 9 दिवस")
        expect(self.page.locator("#mdDashaEnd")).to_have_value("24/07/1986")
        expect(self.page.locator("#adBirthLord")).to_have_value("चंद्र")
        expect(self.page.locator("#adBirthBalance")).to_have_value("0 वर्ष 0 महिने 9 दिवस")
        self.assertEqual(self.dasha_rows("#mdDashaRows")[0], ["मंगळ", "0", "0", "9", "15/07/1986", "24/07/1986"])
        self.assertEqual(self.dasha_rows()[-1], ["चंद्र", "0", "7", "0", "25/12/1985", "24/07/1986"])
        period = self.page.evaluate("window.mdDashaPeriods[0]")
        self.assertAlmostEqual(period["birthRemainingDays"], 8.8725, places=8)
        self.assertAlmostEqual(period["birthElapsedDays"], 2511.1275, places=8)

        self.go("home")
        self.page.locator("#home-dasha-date").fill("1986-07-15")
        self.page.locator("#home-dasha-time").fill("15:45:00")
        self.page.locator("#home-dasha-time").dispatch_event("change")
        expect(self.page.locator('#home-dasha-table tr[data-dasha-row]').first).to_contain_text("Ma")
        expect(self.page.locator('#home-dasha-table tr[data-dasha-row]').first).to_contain_text("24/07/1986")
        home = self.page.evaluate("window.KPHomeDasha.getData()")
        self.assertEqual(home["levels"][1]["rows"][home["path"][1]]["lord"], "चंद्र")
        self.assertEqual(home["levels"][2]["rows"][home["path"][2]]["lord"], "रवी")
        self.go("transit")
        self.page.locator("#tr-mode").select_option("dasha")
        self.page.locator("#tr-reference").fill("1986-07-15")
        self.page.locator("#tr-reference").dispatch_event("change")
        automatic = self.page.evaluate("window.KPTransit.autoDasha()")
        self.assertEqual(tuple(automatic[key] for key in ("MD", "AD", "PD")), ("Ma", "Mo", "Su"))
        self.assertEqual((automatic["pd"]["start"], automatic["pd"]["end"]), ("1986-07-13", "1986-07-24"))
        chart = self.configure_transit_chart(date="1986-07-15", time="15:45:00", source="natal")
        self.assertTrue(chart["dasha"]["ready"])
        self.assertEqual(tuple(chart["dasha"][key]["lord"] for key in ("md", "ad", "pd")), ("मंगळ", "चंद्र", "रवी"))
        for role, lord in (("MD", "Ma"), ("AD", "Mo"), ("PD", "Su")):
            expect(self.page.locator(f'#tc-dasha tr[data-role="{role}"] td').first).to_have_text(lord)
        self.go("report")
        md = self.page.locator('[data-report-section="mdcalc"] [data-report-id="mdDashaRows"] tr').first
        expect(md).to_contain_text("मंगळ")
        expect(md).to_contain_text("24/07/1986")
        expect(self.page.locator('[data-report-section="adcalc"] tr[data-birth-active="true"]')).to_contain_text("चंद्र")
        expect(self.page.locator('[data-report-section="transit-chart"] [data-report-id="tc-dasha"]')).to_contain_text("Su")

    def test_fractional_birth_dasha_boundaries_keep_exact_lords_before_date_rounding(self):
        # 3°40′ begins Moon AD at Ketu elapsed day 693 exactly. One arcsecond
        # before it is Sun AD/Venus PD; at it the new Moon AD/Moon PD starts.
        # At 13°19′59″, 0.0525 day remains in Ketu MD despite its displayed
        # zero-day end. The birth moment still has Mercury AD/Saturn PD.
        fixtures = (
            ("03:39:59", "रवी", ("Ke", "Su", "Ve"), 692.9475, "28/01/2005"),
            ("03:40:00", "चंद्र", ("Ke", "Mo", "Mo"), 693, "28/01/2005"),
            ("13:19:59", "बुध", ("Ke", "Me", "Sa"), 2519.9475, "01/01/2000"),
        )
        self.prepare_exact_dasha()
        for moon, ad_lord, expected_codes, elapsed, end in fixtures:
            with self.subTest(moon=moon):
                self.go("planet")
                self.page.locator("#p6_d_1").fill(moon)
                self.page.locator("#p6_t_1").fill(moon)
                self.action("calculate")
                self.go("mdcalc")
                expect(self.page.locator("#mdBirthDasha")).to_have_value("केतू")
                expect(self.page.locator("#adBirthLord")).to_have_value(ad_lord)
                expect(self.page.locator('#adDashaRows tr[data-birth-active="true"]')).to_have_attribute("data-ad-lord", ad_lord)
                expect(self.page.locator("#mdDashaEnd")).to_have_value(end)
                self.assertAlmostEqual(self.page.evaluate("window.mdDashaPeriods[0].birthElapsedDays"), elapsed, places=8)
                self.go("transit")
                self.page.locator("#tr-mode").select_option("dasha")
                self.page.locator("#tr-reference").fill("2000-01-01")
                self.page.locator("#tr-reference").dispatch_event("change")
                automatic = self.page.evaluate("window.KPTransit.autoDasha()")
                self.assertEqual(tuple(automatic[key] for key in ("MD", "AD", "PD")), expected_codes)
                chart = self.configure_transit_chart(date="2000-01-01", time="12:00:00", source="natal")
                self.assertTrue(chart["dasha"]["ready"])
                actual_codes = self.page.locator('#tc-dasha tr[data-role] td:first-of-type').all_text_contents()
                self.assertEqual(tuple(actual_codes), expected_codes)
                if moon == "13:19:59":
                    expect(self.page.locator("#mdBhogyaDuration")).to_have_value("0 वर्ष 0 महिने 0 दिवस")
                    expect(self.page.locator("#adBirthBalance")).to_have_value("0 वर्ष 0 महिने 0 दिवस")
                    expect(self.page.locator("#tc-dasha-status")).to_contain_text("at birth")

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
                            document.getElementById('p6_rashi_1').value = 'मेष';
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


    def configure_transit_panchang(self, date="2026-10-06", time="05:30:00", offset="5.5", latitude="0", longitude="0"):
        self.go("transit-panchang")
        for field, value in {"date": date, "time": time, "timezone": offset,
                             "latitude": latitude, "longitude": longitude, "place": "Selected transit place"}.items():
            self.page.locator(f"#tp-{field}").fill(value)
        self.page.locator("#tp-calculate").click()
        expect(self.page.locator("#tp-status")).to_have_attribute("data-state", "ready")
        return self.page.evaluate("window.KPTransitPanchang.getData()")

    def configure_daily_ephemeris(self, start="2026-10-06", end="2026-10-07", time="05:30:00", offset="5.5"):
        self.go("ephemeris")
        for field, value in {"start": start, "end": end, "time": time, "timezone": offset}.items():
            self.page.locator(f"#eph-{field}").fill(value)
        self.page.locator("#eph-run").click()
        expect(self.page.locator("#eph-status")).to_have_attribute("data-state", "ready")
        return self.page.evaluate("window.KPDailyEphemeris.getData()")

    def test_transit_panchang_uses_real_positions_local_weekday_zero_coordinates_and_polar_sunrise(self):
        self.prepare_exact_dasha()
        natal = self.outputs()
        values = self.configure_transit_panchang()
        self.assertEqual(values["utc"], "2026-10-06T00:00:00.000Z")
        self.assertEqual(values["latitude"], 0)
        self.assertEqual(values["longitude"], 0)
        expect(self.page.locator("#tp-summary > div")).to_have_count(9)
        expect(self.page.locator("#tp-positions tbody tr[data-planet]")).to_have_count(10)
        fixture = EPHEMERIS_REFERENCE[1]
        for id, tropical in fixture["tropical"].items():
            expected = (tropical - values["ayanamsha"]) % 360
            delta = abs((values["positions"][id] - expected + 180) % 360 - 180)
            self.assertLess(delta, 0.03, f"Panchang {id} must use an independently checked transit position.")
        panchang = values["panchang"]
        # Sun 192.76015°, Moon 134.56756° gives a 301.8074° elongation.
        # The worksheet ayanamsha shifts both equally, preserving tithi/karana.
        self.assertEqual({key: panchang[key] for key in ("tithi", "tithiNumber", "paksha", "karana", "weekday")},
                         {"tithi": "Ekadashi", "tithiNumber": 26, "paksha": "Krishna", "karana": "Bava", "weekday": "Tuesday"})
        self.assertEqual({key: panchang[key] for key in ("nakshatra", "nakLord", "pada", "rashi", "yoga")},
                         {"nakshatra": "P.Phalguni", "nakLord": "Venus", "pada": 1, "rashi": "Leo", "yoga": "Brahma"})
        for field, hour_range in (("sunrise", (5, 6.5)), ("sunset", (17, 18.5))):
            stamp = datetime.fromisoformat(values[field].replace("Z", "+00:00"))
            self.assertEqual(stamp.strftime("%Y-%m-%d"), "2026-10-06")
            self.assertGreater(stamp.hour + stamp.minute / 60, hour_range[0])
            self.assertLess(stamp.hour + stamp.minute / 60, hour_range[1])
        shifted = self.configure_transit_panchang(date="2026-10-05", time="19:00:00", offset="-5")
        self.assertEqual(shifted["utc"], values["utc"])
        self.assertEqual(shifted["positions"], values["positions"])
        self.assertEqual(shifted["panchang"]["weekday"], "Monday",
                         "Civil weekday must use the entered local date rather than UTC.")
        polar = self.configure_transit_panchang(date="2026-06-21", time="12:00:00", offset="0", latitude="78")
        self.assertIsNone(polar["sunrise"])
        self.assertIsNone(polar["sunset"])
        expect(self.page.locator("#tp-summary")).to_contain_text("No event on this date")
        self.page.locator("#tp-latitude").fill("89")
        self.page.locator("#tp-calculate").click()
        expect(self.page.locator("#tp-status")).to_have_attribute("data-state", "error")
        self.assertIsNone(self.page.evaluate("window.KPTransitPanchang.getData()"))
        expect(self.page.locator("#tp-positions tbody tr[data-planet]")).to_have_count(0)
        self.assertEqual(self.outputs(), natal)

    def test_daily_ephemeris_checks_two_days_derived_motion_custom_combustion_csv_and_invalid_ranges(self):
        self.prepare_exact_dasha()
        natal = self.outputs()
        data = self.configure_daily_ephemeris()
        self.assertEqual(data["days"], 2)
        self.assertEqual([row["date"] for row in data["rows"]], ["2026-10-06", "2026-10-07"])
        self.assertEqual(data["rows"][0]["utc"], "2026-10-06T00:00:00.000Z")
        expect(self.page.locator("#eph-table tbody tr[data-planet]")).to_have_count(18)
        limits = {"Mo": 4, "Ma": 8, "Me": 5, "Ve": 6, "Ju": 5, "Sa": 8}
        for index, day in enumerate(data["rows"]):
            planets = {planet["id"]: planet for planet in day["planets"]}
            self.assertEqual(set(planets), {"Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"})
            self.assertAlmostEqual((planets["Ke"]["longitude"] - planets["Ra"]["longitude"]) % 360, 180, places=7)
            self.assertEqual(planets["Ke"]["details"]["degree"], planets["Ra"]["details"]["degree"])
            self.assertTrue(planets["Sa"]["retrograde"])
            self.assertTrue(planets["Ve"]["retrograde"])
            for id, planet in planets.items():
                if index == 0 and id in EPHEMERIS_REFERENCE[1]["tropical"]:
                    expected = (EPHEMERIS_REFERENCE[1]["tropical"][id] - day["ayanamsha"]) % 360
                    delta = abs((planet["longitude"] - expected + 180) % 360 - 180)
                    self.assertLess(delta, 0.03)
                self.assertEqual(planet["retrograde"], planet["motionDegreesPerDay"] < 0)
                threshold = limits.get(id, 0)
                if id == "Me" and planet["retrograde"]: threshold = 3
                if id == "Ve" and planet["retrograde"]: threshold = 4
                separation = abs((planet["longitude"] - planets["Su"]["longitude"] + 180) % 360 - 180)
                self.assertEqual(planet["combust"], id in limits and separation <= threshold)
                self.assertEqual("[R]" in planet["markers"], planet["retrograde"])
                self.assertEqual("[C]" in planet["markers"], planet["combust"])
        with self.page.expect_download() as download_info:
            self.page.locator("#eph-csv").click()
        exported = list(csv.reader(io.StringIO(Path(download_info.value.path()).read_text(encoding="utf-8-sig"))))
        self.assertEqual(len(exported), 19)
        self.assertEqual(exported[-1][0:4], ["2026-10-07", "05:30:00", "5.5", "Ke"])
        self.assertAlmostEqual(float(exported[1][-1]), data["rows"][0]["planets"][0]["longitude"], places=7)

        # Mercury at J2000 is 8.48° from the Sun: outside the user's 5°
        # threshold, inside the optional uniform 8.5° threshold.
        j2000 = self.configure_daily_ephemeris(start="2000-01-01", end="2000-01-01", time="12:00:00", offset="0")
        self.assertFalse(next(p for p in j2000["rows"][0]["planets"] if p["id"] == "Me")["combust"])
        self.save_software_preferences(combustionRule="uniform")
        uniform = self.configure_daily_ephemeris(start="2000-01-01", end="2000-01-01", time="12:00:00", offset="0")
        self.assertTrue(next(p for p in uniform["rows"][0]["planets"] if p["id"] == "Me")["combust"])
        for start, end, expected in (("2026-10-07", "2026-10-06", "on or after"),
                                     ("2026-01-01", "2027-01-02", "366")):
            self.page.locator("#eph-start").fill(start)
            self.page.locator("#eph-end").fill(end)
            self.page.locator("#eph-run").click()
            expect(self.page.locator("#eph-status")).to_have_attribute("data-state", "error")
            expect(self.page.locator("#eph-status")).to_contain_text(expected)
            expect(self.page.locator("#eph-table tbody tr[data-planet]")).to_have_count(0)
            self.assertIsNone(self.page.evaluate("window.KPDailyEphemeris.getData()"))
            expect(self.page.locator("#eph-csv")).to_be_disabled()
        self.page.locator("#eph-end").fill("2026-12-31")
        self.page.evaluate("()=>{window.KPDailyEphemeris.run();window.KPDailyEphemeris.cancel();}")
        expect(self.page.locator("#eph-status")).to_contain_text("cancelled")
        self.assertIsNone(self.page.evaluate("window.KPDailyEphemeris.getData()"))
        expect(self.page.locator("#eph-run")).to_be_enabled()
        self.assertEqual(self.outputs(), natal)

    def test_new_prediction_almanac_tabs_restore_lkp_and_print_all_rows_in_mobile_navigation(self):
        self.prepare_exact_dasha()
        self.configure_transit_panchang(date="2026-10-05", time="19:00:00", offset="-5")
        self.configure_daily_ephemeris()
        self.go("prediction")
        settings = {"pred-language": "marathi", "pred-method": "sixfold", "pred-chain-mode": "cusp-lords",
                    "pred-match-filter": "all", "pred-main-house": "0"}
        for id, value in settings.items():
            self.page.locator(f"#{id}").select_option(value)
        self.page.locator("#pred-layer-STL").uncheck()
        self.page.locator("#pred-require-main").check()
        self.action("save")
        backup = self.page.evaluate("JSON.parse(localStorage.getItem('kpRaphaelData'))")
        for id, value in settings.items():
            self.assertEqual(backup["fields"][id]["value"], value)
        self.assertFalse(backup["fields"]["pred-layer-STL"]["checked"])
        self.assertTrue(backup["fields"]["pred-require-main"]["checked"])
        self.assertEqual(backup["fields"]["tp-timezone"]["value"], "-5")
        self.assertEqual(backup["fields"]["eph-start"]["value"], "2026-10-06")
        self.assertFalse(any(key.startswith(("pred-event", "tp-summary", "eph-table")) for key in backup["fields"]),
                         "Only chosen settings belong in .lkp; calculated sheets are rebuilt from current data.")
        self.page.locator("#pred-language").select_option("english")
        self.page.locator("#pred-method").select_option("fourfold")
        self.page.locator("#pred-layer-STL").check()
        self.import_file(json.dumps(backup, ensure_ascii=False), filename="prediction-panchang-ephemeris.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        for id, value in settings.items():
            expect(self.page.locator(f"#{id}")).to_have_value(value)
        expect(self.page.locator("#pred-layer-STL")).not_to_be_checked()
        expect(self.page.locator("#pred-require-main")).to_be_checked()
        self.assertEqual(self.page.evaluate("window.KPPrediction.getData().options"),
                         {"method": "sixfold", "chainMode": "cusp-lords", "layers": ["CSL", "SBL"],
                          "requireMain": True, "language": "marathi"})
        self.assertEqual(self.page.evaluate("window.KPTransitPanchang.getData().utc"), "2026-10-06T00:00:00.000Z")
        self.assertIsNone(self.page.evaluate("window.KPDailyEphemeris.getData()"),
                          "Import must clear an old generated ephemeris until it is recalculated.")
        self.configure_daily_ephemeris()
        self.go("prediction")
        self.page.locator("#pred-print").click()
        expect(self.page.locator("main > #report")).to_be_visible()
        checked = self.page.locator('#report-page-options input:checked').evaluate_all("items=>items.map(item=>item.dataset.reportPageKey)")
        self.assertEqual(checked, ["prediction"])

        popup = self.selected_report_popup(["prediction", "transit-panchang", "ephemeris"])
        try:
            self.assertEqual(popup.locator("body > .report-page").evaluate_all("pages=>pages.map(page=>page.dataset.reportSection)"),
                             ["prediction", "transit-panchang", "ephemeris"])
            expect(popup.locator('[data-report-section="prediction"] [data-pred-event]')).to_have_count(1612)
            expect(popup.locator('[data-report-section="prediction"] [data-pred-cusp]')).to_have_count(12)
            expect(popup.locator('[data-report-section="transit-panchang"] tr[data-planet]')).to_have_count(10)
            expect(popup.locator('[data-report-section="ephemeris"] tr[data-planet]')).to_have_count(18)
            expect(popup.locator("input,select,button,textarea")).to_have_count(0)
            popup.emulate_media(media="print")
            geometry = popup.locator('body > .report-page').evaluate_all("""pages=>pages.map(page=>{
                const bounds=page.getBoundingClientRect(),style=getComputedStyle(page);
                const rows=[...page.querySelectorAll('tr')];
                const clipped=rows.filter(row=>{const rect=row.getBoundingClientRect();return rect.left<bounds.left-1||rect.right>bounds.right+1||rect.bottom>bounds.bottom+1;});
                return {section:page.dataset.reportSection,maxHeight:style.maxHeight,overflow:style.overflow,clipped:clipped.length};
            })""")
            for page in geometry:
                self.assertEqual(page["maxHeight"], "none")
                self.assertEqual(page["overflow"], "visible")
                self.assertEqual(page["clipped"], 0, page)
        finally:
            popup.close()

        self.page.set_viewport_size({"width": 390, "height": 844})
        for section in ("prediction", "transit-panchang", "ephemeris"):
            self.go(section)
            expect(self.page.locator("#menu-toggle")).to_have_attribute("aria-expanded", "false")
            self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 391,
                                 "Dense tables may scroll inside their containers while mobile navigation stays within the viewport.")
        self.page.locator("#menu-toggle").click()
        expect(self.page.locator(".app-sidebar [data-tab]")).to_have_count(len(SECTIONS))

    def test_prediction_chain_analysis_proves_house_groups_and_selected_layers_independently(self):
        # This synthetic chart deliberately gives every main cusp CSL Su,
        # whose own star and sub lords differ from the cusp's star lord Sa.
        # The expected evidence is authored here, independent of KPDisplay.
        ids = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
        planets = [{"id": id, "stl": "Mo", "sl": "Ma"} for id in ids]
        four = [{"id": id, "A": [], "B": [], "C": [], "D": []} for id in ids]
        for row in four:
            if row["id"] == "Su": row["A"] = [2]
            if row["id"] == "Mo": row["B"] = [3]
            if row["id"] == "Ma": row["C"] = [4]
            if row["id"] == "Sa": row["D"] = [8]
        six = [{**row, "E": [5] if row["id"] == "Su" else [], "F": []} for row in four]
        model = {"ready": True, "planets": planets,
                 "houses": [{"id": i, "sl": "Su", "stl": "Sa"} for i in range(1, 13)],
                 "fourfold": {"planets": four}, "sixfold": {"planets": six}}
        groups = ([2, 3, 4], [2, 11], [11], [2], [2, 5])
        events = [{"id": i, "event": {"en": f"Evidence {i}"}, "mainHouses": [1],
                   "supportingHouses": list(group), "supportingGroups": [list(group)],
                   "automaticEligible": True} for i, group in enumerate(groups, 1)]
        events.append({"id": 6, "event": {"en": "Conditional rule"}, "mainHouses": [1],
                       "supportingHouses": [2], "supportingGroups": [], "automaticEligible": False})
        catalogue = {"events": events}
        actual = self.page.evaluate("""({model,catalogue})=>Object.fromEntries([
            ['all',{}],['cslOnly',{layers:['CSL']}],['cuspLords',{chainMode:'cusp-lords'}],
            ['mainRequired',{requireMain:true}],['sixfold',{method:'sixfold'}],
            ['missing',{model:{...model,ready:false,reason:'Missing natal planets'}}]
        ].map(([key,options])=>[key,window.KPPrediction.analyze(options.model||model,{...options,catalogue})]))""",
                                    {"model": model, "catalogue": catalogue})
        self.assertEqual([row["status"] for row in actual["all"]["results"]],
                         ["matched", "partial", "unmatched", "matched", "partial", "review"])
        proof = actual["all"]["results"][0]["proof"]
        self.assertEqual(proof["chain"], {"CSL": "Su", "STL": "Mo", "SBL": "Ma"})
        self.assertEqual(proof["signifiedHouses"], [2, 3, 4])
        self.assertEqual(proof["matchedHouses"], [2, 3, 4])
        self.assertEqual(proof["missingHouses"], [])
        self.assertEqual(proof["contributions"], [
            {"house": 2, "sources": [{"role": "CSL", "planet": "Su", "level": "A"}]},
            {"house": 3, "sources": [{"role": "STL", "planet": "Mo", "level": "B"}]},
            {"house": 4, "sources": [{"role": "SBL", "planet": "Ma", "level": "C"}]},
        ])
        self.assertEqual(actual["cslOnly"]["results"][0]["proof"]["missingHouses"], [3, 4])
        self.assertEqual(actual["cslOnly"]["results"][0]["status"], "partial")
        self.assertEqual(actual["cuspLords"]["chains"][0]["houses"], [2, 8])
        self.assertEqual(actual["cuspLords"]["results"][0]["proof"]["chain"],
                         {"CSL": "Su", "STL": "Sa", "SBL": "Su"})
        self.assertEqual(actual["mainRequired"]["results"][3]["proof"]["requiredHouses"], [1, 2])
        self.assertEqual(actual["mainRequired"]["results"][3]["status"], "partial")
        self.assertEqual(actual["sixfold"]["results"][4]["status"], "matched")
        self.assertEqual(actual["sixfold"]["fields"], list("ABCDEF"))
        self.assertFalse(actual["missing"]["ready"])
        self.assertEqual(actual["missing"]["counts"]["incomplete"], 6)

    def test_prediction_workbook_provenance_live_chains_filters_and_csv_include_all_rows(self):
        self.prepare_exact_dasha()
        self.go("prediction")
        expect(self.page.locator("#pred-status")).to_have_attribute("data-ready", "true")
        data = self.page.evaluate("window.KPPrediction.getData()")
        catalogue = self.page.evaluate("window.KPPrediction.getCatalogue()")
        self.assertEqual(len(catalogue["events"]), 1612)
        self.assertEqual(sum(event["automaticEligible"] for event in catalogue["events"]), 1398)
        self.assertEqual(data["counts"]["review"], 214)
        expect(self.page.locator("#pred-chain-table tbody tr")).to_have_count(12)
        self.page.locator("#pred-match-filter").select_option("all")
        expect(self.page.locator("#pred-event-rows tr")).to_have_count(60)
        actual_chains = self.page.evaluate("""()=>window.currentKPModel.houses.map(cusp=>{
            const csl=window.currentKPModel.planets.find(planet=>planet.id===cusp.sl);
            return {cusp:cusp.id,CSL:cusp.sl,STL:csl.stl,SBL:csl.sl};
        })""")
        self.assertEqual([{key: chain[key] for key in ("cusp", "CSL", "STL", "SBL")}
                          for chain in data["chains"]], actual_chains)
        indexed = {event["id"]: event for event in catalogue["events"]}
        self.assertEqual(indexed[1300]["event"], {"en": None, "mr": "कार्यक्षेत्रात निराशा"})
        self.assertEqual(indexed[1301]["sources"]["en"]["row"], 1301)
        self.assertEqual(indexed[1301]["sources"]["mr"]["row"], 1302)
        self.assertEqual(indexed[700]["sources"]["en"]["supporting"], "11,1")
        self.assertEqual(indexed[700]["sources"]["mr"]["supporting"], "1, 4, 11")
        by_id = {row["id"]: row for row in data["results"]}
        self.assertEqual(by_id[700]["status"], "review")
        self.assertEqual(by_id[1300]["status"], "review")

        # Screen pagination must not truncate the export or printed sheet.
        csv_rows = list(csv.reader(io.StringIO(self.page.evaluate("window.KPPrediction.csv()").lstrip("\ufeff"))))
        self.assertEqual(len(csv_rows), 1613)
        self.assertEqual(csv_rows[-1][0], "1612")
        snapshot_rows = self.page.evaluate("""()=>{
            const root=document.createElement('div');root.innerHTML=window.KPPrediction.snapshot();
            return {events:root.querySelectorAll('[data-pred-event]').length,
                    cusps:root.querySelectorAll('[data-pred-cusp]').length,
                    controls:root.querySelectorAll('input,select,button,textarea').length};
        }""")
        self.assertEqual(snapshot_rows, {"events": 1612, "cusps": 12, "controls": 0})
        self.page.locator("#pred-match-filter").select_option("review")
        expect(self.page.locator("#pred-print-count")).to_contain_text("214")
        self.page.locator("#pred-search").fill("कार्यक्षेत्रात निराशा")
        expect(self.page.locator('#pred-event-rows [data-pred-event="1300"]')).to_have_count(1)
        self.page.locator("#pred-language").select_option("marathi")
        expect(self.page.locator('#pred-event-rows [data-pred-event="1300"]')).to_contain_text("कार्यक्षेत्रात निराशा")
        self.page.locator('#pred-event-rows [data-pred-detail="1300"]').click()
        expect(self.page.locator("#pred-event-detail")).to_contain_text("Marathi Prediction")
        expect(self.page.locator("#pred-event-detail")).to_contain_text("1301")
        self.page.locator("#pred-method").select_option("sixfold")
        self.page.locator('#pred-layers input[value="STL"]').uncheck()
        self.assertEqual(self.page.evaluate("window.KPPrediction.getData().options.layers"), ["CSL", "SBL"])
        self.assertEqual(self.page.evaluate("window.KPPrediction.getData().fields"), list("ABCDEF"))
        self.go("planet")
        self.page.locator("#p6_d_1").fill("")
        self.page.locator("#p6_t_1").fill("")
        self.action("calculate")
        self.go("prediction")
        expect(self.page.locator("#pred-status")).to_have_attribute("data-ready", "false")
        expect(self.page.locator("#pred-chain-table")).to_have_count(0)
        self.assertEqual(self.page.evaluate("window.KPPrediction.getData().counts.incomplete"), 1612,
                         "An incomplete natal chart must replace prior house matches.")

    def test_automatic_0530_worksheet_ephemeris_matches_independent_reference_without_double_ayanamsha(self):
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("manual")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("manual")
        data = self.configure_automatic_0530_worksheets()
        self.assertEqual(data["dates"], ["2026-10-06", "2026-10-07"])
        self.assertEqual(data["offset"], 5.5)
        self.assertEqual(data["time"], "05:30:00")
        self.assertEqual(data["rows"][0]["utc"], "2026-10-06T00:00:00.000Z")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("automatic")
        expect(self.page.locator("#st-ephemeris-status")).to_have_attribute("data-ready", "true")
        ayanamsha = self.worksheet_arcseconds("23:34:14") / 3600
        ids = ("Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")
        for index, id in enumerate(ids):
            with self.subTest(planet=id):
                first = data["rows"][0]["positions"][id]
                if id in EPHEMERIS_REFERENCE[1]["tropical"]:
                    expected = (EPHEMERIS_REFERENCE[1]["tropical"][id] - ayanamsha) % 360
                    error = abs((first - expected + 180) % 360 - 180)
                    self.assertLess(error, 0.03, "The worksheet must receive the independently checked KP sidereal longitude.")
                row = self.worksheet_arcseconds(self.page.locator(f"#p6_d_{index}").input_value()) / 3600
                final = self.worksheet_arcseconds(self.page.locator(f"#p6_add_{index}").input_value()) / 3600
                self.assertLessEqual(abs((row - first + 180) % 360 - 180), 0.51 / 3600)
                self.assertEqual(final, row, "At 05:30, interpolation is zero and must not subtract ayanamsha a second time.")
                expect(self.page.locator(f"#p6_total_{index}")).to_have_value("0:00:00")
        self.assertAlmostEqual((data["rows"][0]["positions"]["Ke"] - data["rows"][0]["positions"]["Ra"]) % 360, 180, places=7)
        self.assertEqual(self.page.locator("#p6_final_7").input_value(), self.page.locator("#p6_final_8").input_value())
        expect(self.page.locator("#p6_motion_5")).to_have_value(re.compile(r".* R$"))
        expect(self.page.locator("#p6_motion_6")).to_have_value(re.compile(r".* R$"))

        # Meeus' GMST polynomial is independent of Astronomy Engine. Its mean
        # sidereal angle differs from apparent sidereal time by only nutation.
        instant = datetime(2026, 10, 6)
        days = (instant - datetime(2000, 1, 1, 12)).total_seconds() / 86400
        centuries = days / 36525
        gmst = (280.46061837 + 360.98564736629 * days + 0.000387933 * centuries ** 2
                - centuries ** 3 / 38710000) % 360
        expected_standard_seconds = ((gmst + 82.5) % 360) * 240
        self.go("stcalc")
        actual_standard_seconds = self.worksheet_arcseconds(self.page.locator("#baseSidereal0530").input_value())
        st_error = abs((actual_standard_seconds - expected_standard_seconds + 43200) % 86400 - 43200)
        self.assertLess(st_error, 4, "05:30 IST is 00:00 UTC; ST must include the standard meridian exactly once.")

    def test_automatic_0530_rows_interpolate_before_dawn_honor_dates_and_refresh_ayanamsha_offset(self):
        data = self.configure_automatic_0530_worksheets(time="04:00:00")
        self.assertEqual(data["dates"], ["2026-10-05", "2026-10-06"])
        expect(self.page.locator("#p6_row_date_1")).to_have_value("2026-10-05")
        expect(self.page.locator("#p6_row_date_2")).to_have_value("2026-10-06")

        def assert_before_dawn(interval):
            for index in (0, 1, 5, 6, 7):
                first = self.worksheet_arcseconds(self.page.locator(f"#p6_d_{index}").input_value())
                second = self.worksheet_arcseconds(self.page.locator(f"#p6_t_{index}").input_value())
                daily = ((second - first + 648000) % 1296000 - 648000) / interval
                correction = daily * (-1.5 / 24)
                expected = (second + (1 if correction >= 0 else -1) * int(abs(correction) + 0.5)) % 1296000
                actual = self.worksheet_arcseconds(self.page.locator(f"#p6_add_{index}").input_value())
                self.assertEqual(actual, expected, "The correction is signed from the DOB's 05:30 row, using the actual row-date span.")
                expect(self.page.locator(f"#p6_birth_{index}")).to_have_value(self.page.locator(f"#p6_t_{index}").input_value())
            expect(self.page.locator("#p6_final_5")).to_have_value(re.compile(r".* R$"))

        assert_before_dawn(1)
        self.page.locator("#p6_row_date_1").fill("2026-10-04")
        self.page.wait_for_function("window.KPWorksheetEphemeris.getData()?.dates?.[0]==='2026-10-04'")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("automatic")
        assert_before_dawn(2)
        before = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        self.go("basic")
        self.page.locator("#dayAyan").fill("24:34:14")
        self.page.wait_for_function("previous=>Math.abs((previous-window.KPWorksheetEphemeris.getData().rows[1].positions.Su+360)%360-1)<0.00001", arg=before["rows"][1]["positions"]["Su"])
        after = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        for old, new in zip(before["rows"], after["rows"]):
            self.assertEqual(old["date"], new["date"])
            for id in ("Su", "Mo", "Ve", "Ra", "Ke"):
                self.assertAlmostEqual((old["positions"][id] - new["positions"][id]) % 360, 1, places=7)
        self.go("ayan")
        self.page.locator("#stdLon").fill("00:00:00")
        self.page.wait_for_function("window.KPWorksheetEphemeris.getData()?.offset===0")
        zero_offset = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        self.assertEqual(zero_offset["rows"][0]["utc"], "2026-10-04T05:30:00.000Z")
        self.assertEqual(zero_offset["rows"][1]["utc"], "2026-10-06T05:30:00.000Z")
        self.assertNotEqual(zero_offset["rows"][1]["positions"]["Mo"], after["rows"][1]["positions"]["Mo"])
        self.go("planet")
        assert_before_dawn(2)
        self.go("basic")
        self.page.locator("#birthTime").fill("15:45:00")
        expect(self.page.locator("#p6_row_date_1")).to_have_value("2026-10-06")
        expect(self.page.locator("#p6_row_date_2")).to_have_value("2026-10-07")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.assertEqual(self.page.evaluate("window.KPWorksheetEphemeris.getData().dates"), ["2026-10-06", "2026-10-07"],
                         "Changing birth time resets the dated rows to its new chronological DOB pair.")
        self.go("planet")
        first = self.worksheet_arcseconds(self.page.locator("#p6_d_1").input_value())
        second = self.worksheet_arcseconds(self.page.locator("#p6_t_1").input_value())
        daily = (second - first + 648000) % 1296000 - 648000
        expected = (first + int(daily * 10.25 / 24 + 0.5)) % 1296000
        self.assertEqual(self.worksheet_arcseconds(self.page.locator("#p6_add_1").input_value()), expected)
        self.go("basic")
        self.page.locator("#dob").fill("2026-10-07")
        self.page.wait_for_function("window.KPWorksheetEphemeris.getData()?.dates?.[0]==='2026-10-07'")
        updated = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        self.assertEqual(updated["dates"], ["2026-10-07", "2026-10-08"])
        self.assertEqual(updated["rows"][0]["utc"], "2026-10-07T05:30:00.000Z")

    def test_automatic_0530_modes_roundtrip_lkp_and_manual_edits_preserve_legacy_data(self):
        original = self.configure_automatic_0530_worksheets()
        expected_rows = self.page.evaluate("()=>Object.fromEntries([...document.querySelectorAll('#planet input[id^=p6_d_],#planet input[id^=p6_t_]')].map(input=>[input.id,input.value]))")
        with self.page.expect_download() as download_info:
            self.action("export")
        download = download_info.value
        self.assertTrue(download.suggested_filename.endswith(".lkp"))
        backup = json.loads(Path(download.path()).read_text(encoding="utf-8"))
        self.assertEqual(backup["fields"]["p6-ephemeris-source"]["value"], "automatic")
        self.assertEqual(backup["fields"]["st-ephemeris-source"]["value"], "automatic")
        self.page.locator("#p6_d_0").fill("11:00:00")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("manual")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("automatic")
        self.assertIsNone(self.page.evaluate("window.KPWorksheetEphemeris.getData()"))
        self.go("stcalc")
        self.page.locator("#baseSidereal0530").fill("06:00:00")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("manual")
        self.action("calculate")
        expect(self.page.locator("#baseSidereal0530")).to_have_value("06:00:00")
        expect(self.page.locator("#p6_d_0")).to_have_value("11:00:00")
        self.import_file(json.dumps(backup), filename="automatic-0530.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("automatic")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("automatic")
        self.assertEqual(self.page.evaluate("window.KPWorksheetEphemeris.getData()"), original)
        actual_rows = self.page.evaluate("()=>Object.fromEntries([...document.querySelectorAll('#planet input[id^=p6_d_],#planet input[id^=p6_t_]')].map(input=>[input.id,input.value]))")
        self.assertEqual(actual_rows, expected_rows)
        self.page.locator("#baseSidereal0530").fill("06:00:00")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("manual")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("automatic")
        independent_modes = self.page.evaluate("window.getChartData()")
        self.page.locator("#st-ephemeris-source").select_option("automatic")
        self.import_file(json.dumps(independent_modes), filename="automatic-planets-manual-st.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#st-ephemeris-source")).to_have_value("manual")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("automatic")
        expect(self.page.locator("#baseSidereal0530")).to_have_value("06:00:00")
        self.assertEqual(self.page.evaluate("window.KPWorksheetEphemeris.getData()"), original,
                         "Planet and sidereal sources must retain their independent choices through .lkp import.")

        # Old chart files did not have source-mode fields. Importing one while
        # automatic mode is active must preserve its own manually entered rows.
        legacy = json.loads(json.dumps(backup))
        legacy["version"] = 2
        legacy.pop("format", None)
        for id in ("p6-ephemeris-source", "st-ephemeris-source"):
            legacy["fields"].pop(id)
        legacy["fields"]["p6_d_0"]["value"] = "11:00:00"
        legacy["fields"]["p6_t_0"]["value"] = "12:00:00"
        legacy["fields"]["baseSidereal0530"]["value"] = "06:00:00"
        self.import_file(json.dumps(legacy), filename="legacy-manual-rows.json")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        for id in ("p6-ephemeris-source", "st-ephemeris-source"):
            expect(self.page.locator(f"#{id}")).to_have_value("manual")
        expect(self.page.locator("#p6_d_0")).to_have_value("11:00:00")
        expect(self.page.locator("#p6_t_0")).to_have_value("12:00:00")
        expect(self.page.locator("#p6_add_0")).to_have_value("11:00:00")
        expect(self.page.locator("#baseSidereal0530")).to_have_value("06:00:00")
        self.assertIsNone(self.page.evaluate("window.KPWorksheetEphemeris.getData()"))
        self.go("basic")
        self.page.locator("#birthTime").fill("06:30:00")
        expect(self.page.locator("#p6_d_0")).to_have_value("11:00:00")
        expect(self.page.locator("#p6_t_0")).to_have_value("12:00:00")
        expect(self.page.locator("#p6_add_0")).to_have_value("11:02:30")
        expect(self.page.locator("#baseSidereal0530")).to_have_value("06:00:00")

    def test_automatic_0530_rejects_missing_or_out_of_range_dates_without_stale_positions(self):
        self.configure_automatic_0530_worksheets()

        def assert_no_generated_positions():
            expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "false")
            self.assertIsNone(self.page.evaluate("window.KPWorksheetEphemeris.getData()"))
            for index in range(9):
                for prefix in ("d", "t", "hours", "minutes", "total", "final", "rashi"):
                    expect(self.page.locator(f"#p6_{prefix}_{index}")).to_have_value("")
            self.assertEqual(self.page.evaluate("window.lastPlanetPositions"), {})

        def assert_no_generated_sidereal():
            expect(self.page.locator("#st-ephemeris-status")).to_have_attribute("data-ready", "false")
            for id in ("baseSidereal0530", "stGrandTotal", "birthPlaceSiderealTime", "stBirthTimeAgain"):
                expect(self.page.locator(f"#{id}")).to_have_value("")

        self.go("basic")
        self.page.locator("#dob").fill("")
        assert_no_generated_positions()
        assert_no_generated_sidereal()
        self.page.locator("#dob").fill("2100-12-31")
        self.page.locator("#birthTime").fill("12:00:00")
        assert_no_generated_positions()
        self.page.locator("#dob").fill("1900-01-01")
        self.page.locator("#birthTime").fill("04:00:00")
        assert_no_generated_positions()
        self.page.locator("#dob").fill("2026-10-06")
        self.page.locator("#birthTime").fill("05:30:00")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.go("planet")
        self.page.locator("#p6_row_date_1").fill("2026-10-07")
        expect(self.page.locator("#p6_row_date_2")).to_have_value("2026-10-07")
        assert_no_generated_positions()
        self.page.locator("#p6_row_date_1").fill("2026-10-06")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.page.locator("#p6_row_date_2").fill("2026-10-20")
        assert_no_generated_positions()
        self.page.locator("#p6_row_date_2").fill("2026-10-07")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.go("ayan")
        self.page.locator("#stdLon").fill("")
        assert_no_generated_positions()
        assert_no_generated_sidereal()

    def test_annual_kp_ayanamsha_uses_supplied_years_calendar_fractions_and_future_ephemeris(self):
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("manual")
        expect(self.page.locator("#kp-ayanamsha-table-source tbody tr")).to_have_count(287)
        expect(self.page.locator("#kp-ayanamsha-table-source tbody tr[data-conflict=true]")).to_have_count(44)
        self.page.locator("#dob").fill("1986-07-15")
        self.page.locator("#birthTime").fill("15:45:00")
        self.page.locator("#kp-ayanamsha-source").select_option("annual")
        expect(self.page.locator("#kp-ayanamsha-status")).to_have_attribute("data-ready", "true")
        expect(self.page.locator("#dayAyan")).to_have_value("23:33:30")
        expect(self.page.locator("#daySum")).to_have_value("00:00:27")
        expect(self.page.locator("#ayanValue")).to_have_value("23:33:57")

        # Independent anchors transcribed from the supplied annual table. Its
        # epoch is treated as January 1, with the actual calendar year's length.
        fixtures = (
            ("1986-01-01", "23:33:30", "00:00:00", "23:33:30"),
            ("1986-07-01", "23:33:30", "00:00:25", "23:33:55"),
            ("2000-02-29", "23:45:10", "00:00:08", "23:45:18"),
            ("2001-01-01", "23:46:00", "00:00:00", "23:46:00"),
            ("2026-01-01", "24:06:50", "00:00:00", "24:06:50"),
        )
        for dob, base, increment, total in fixtures:
            with self.subTest(date=dob):
                self.page.locator("#dob").fill(dob)
                expect(self.page.locator("#kp-ayanamsha-status")).to_have_attribute("data-ready", "true")
                expect(self.page.locator("#dayAyan")).to_have_value(base)
                expect(self.page.locator("#daySum")).to_have_value(increment)
                expect(self.page.locator("#ayanValue")).to_have_value(total)

        exact = self.page.evaluate("""() => {
            const dates=['2000-01-01T00:00:00Z','2000-02-29T00:00:00Z',
                '2000-12-31T12:00:00Z','2001-01-01T00:00:00Z','2026-01-01T00:00:00Z',
                '2103-07-02T00:00:00Z','2104-01-01T00:00:00Z','2147-01-01T00:00:00Z'];
            return dates.map(date=>window.KPAnnualAyanamsha.at(new Date(date)));
        }""")
        expected = (85510, 85510 + 50 * 59 / 366,
                    85510 + 50 * 365.5 / 366, 85560, 86810,
                    90660 - 100 * 182 / 365, 90560, 90560)
        for actual, arcseconds in zip(exact, expected):
            self.assertAlmostEqual(actual * 3600, arcseconds, places=7,
                                   msg="Annual interpolation must retain fractional seconds for ephemeris calculations.")
        # Future rows deliberately check the user's authoritative DMS choice;
        # their conflicting raw arc-second column must not replace the DMS.

        self.page.locator("#dob").fill("1986-07-15")
        future_before = self.page.evaluate("window.KPEphemeris.ayanamsha('2026-01-01T00:00:00Z')")
        self.assertAlmostEqual(future_before * 3600, 86810, places=7)
        self.page.locator("#dob").fill("2000-02-29")
        future_after = self.page.evaluate("window.KPEphemeris.ayanamsha('2026-01-01T00:00:00Z')")
        self.assertEqual(future_before, future_after,
                         "Transit and daily ephemeris use the requested date's annual value, independent of the native's DOB.")
        longitudes = self.page.evaluate("""() => {
            const date=new Date('2026-01-01T00:00:00Z');
            return {tropical:window.KPEphemeris.tropical(date,'Su'),
                    sidereal:window.KPEphemeris.longitude(date,'Su')};
        }""")
        self.assertAlmostEqual((longitudes["tropical"] - longitudes["sidereal"]) % 360,
                               86810 / 3600, places=7)

    def test_annual_kp_ayanamsha_manual_edits_and_lkp_restore_preserve_source_choices(self):
        self.page.locator("#dob").fill("1986-07-15")
        self.page.locator("#birthTime").fill("05:30:00")
        self.page.locator("#kp-ayanamsha-source").select_option("annual")
        expect(self.page.locator("#ayanValue")).to_have_value("23:33:57")
        self.go("planet")
        self.page.locator("#p6-ephemeris-source").select_option("automatic")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        generated = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        with self.page.expect_download() as download_info:
            self.action("export")
        download = download_info.value
        self.assertTrue(download.suggested_filename.endswith(".lkp"))
        backup = json.loads(Path(download.path()).read_text(encoding="utf-8"))
        self.assertEqual(backup["fields"]["kp-ayanamsha-source"]["value"], "annual")

        self.go("basic")
        self.page.locator("#dayAyan").fill("24:00:00")
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("manual")
        self.page.locator("#daySum").fill("00:00:10")
        self.action("calculate")
        expect(self.page.locator("#ayanValue")).to_have_value("24:00:10")
        expect(self.page.locator("#dayAyan")).to_have_value("24:00:00")
        expect(self.page.locator("#p6-ephemeris-source")).to_have_value("automatic")
        manual = self.page.evaluate("window.KPWorksheetEphemeris.getData()")
        self.assertNotEqual(manual["rows"][0]["positions"]["Su"], generated["rows"][0]["positions"]["Su"])

        self.import_file(json.dumps(backup), filename="annual-ayanamsha.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("annual")
        expect(self.page.locator("#kp-ayanamsha-status")).to_have_attribute("data-ready", "true")
        expect(self.page.locator("#ayanValue")).to_have_value("23:33:57")
        self.assertEqual(self.page.evaluate("window.KPWorksheetEphemeris.getData()"), generated)

        # A chart created before the annual-source option must preserve its
        # supplied values even when imported over a currently automatic chart.
        legacy = json.loads(json.dumps(backup))
        legacy["fields"].pop("kp-ayanamsha-source")
        legacy["fields"]["dayAyan"]["value"] = "24:00:00"
        legacy["fields"]["daySum"]["value"] = "00:00:10"
        self.import_file(json.dumps(legacy), filename="legacy-manual-ayanamsha.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("manual")
        expect(self.page.locator("#ayanValue")).to_have_value("24:00:10")
        expect(self.page.locator("#dayAyan")).to_have_value("24:00:00")
        expect(self.page.locator("#daySum")).to_have_value("00:00:10")
        self.assertEqual(self.page.evaluate("window.KPWorksheetEphemeris.getData()"), manual)
        self.page.locator("#kp-ayanamsha-source").select_option("annual")
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("annual")
        self.page.locator("#daySum").fill("00:00:12")
        expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("manual")
        expect(self.page.locator("#ayanValue")).to_have_value("23:33:42")

    def test_annual_kp_ayanamsha_invalid_birth_dates_clear_generated_values_and_recover(self):
        self.page.locator("#dob").fill("1986-07-15")
        self.page.locator("#birthTime").fill("05:30:00")
        self.page.locator("#kp-ayanamsha-source").select_option("annual")
        expect(self.page.locator("#ayanValue")).to_have_value("23:33:57")
        self.go("planet")
        self.page.locator("#p6-ephemeris-source").select_option("automatic")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.go("basic")
        for date in ("", "1860-01-01"):
            with self.subTest(date=date):
                self.page.locator("#dob").fill(date)
                expect(self.page.locator("#kp-ayanamsha-source")).to_have_value("annual")
                expect(self.page.locator("#kp-ayanamsha-status")).to_have_attribute("data-ready", "false")
                expect(self.page.locator("#ayanValue")).to_have_value("")
                expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "false")
                self.assertIsNone(self.page.evaluate("window.KPWorksheetEphemeris.getData()"))
                self.assertEqual(self.page.evaluate("window.lastPlanetPositions"), {})
                for index in range(9):
                    for prefix in ("d", "t", "final", "rashi"):
                        expect(self.page.locator(f"#p6_{prefix}_{index}")).to_have_value("")
                self.action("calculate")
                expect(self.page.locator("#ayanValue")).to_have_value("")
        self.page.locator("#dob").fill("2026-01-01")
        expect(self.page.locator("#kp-ayanamsha-status")).to_have_attribute("data-ready", "true")
        expect(self.page.locator("#ayanValue")).to_have_value("24:06:50")
        expect(self.page.locator("#p6-ephemeris-status")).to_have_attribute("data-ready", "true")
        self.assertTrue(self.page.evaluate("window.KPWorksheetEphemeris.getData().ready"))

    def test_prediction_reference_library_preserves_all_seven_sources_duplicates_and_original_text(self):
        catalogue = self.page.evaluate("window.KPPredictionLibrary.getCatalogue()")
        entries = catalogue["entries"]
        self.assertEqual(len(entries), 6213)
        self.assertEqual(len({entry["id"] for entry in entries}), 6213)
        expected = {"Ratna.txt": 18, "Bhavfal.txt": 2869, "Prediction.txt": 824,
                    "Events.txt": 1046, "Dahs Fal Short.txt": 391,
                    "dashafal.txt": 1017, "Mahadasha.txt": 48}
        self.assertEqual({source["file"]: source["entries"] for source in catalogue["sources"]}, expected)
        self.assertEqual({file: sum(entry["file"] == file for entry in entries) for file in expected}, expected)
        import hashlib
        projection = [[entry["file"], entry["line"], entry["key"], entry["value"], entry["rawValue"], entry.get("continuationLines", [])] for entry in entries]
        digest = hashlib.sha256(json.dumps(projection, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(digest, "c62d1db97896174b09d550d4ca319cdbd53bea4a3a6ac5cb846057acca6cdc2c")
        self.assertEqual(len(catalogue["categories"]), 7)
        repeated = [entry for entry in entries if entry["file"] == "Bhavfal.txt" and entry["key"] == "Bh9R35912"]
        self.assertEqual([entry["line"] for entry in repeated], [1630, 1748])
        self.assertEqual([entry["duplicateCount"] for entry in repeated], [2, 2])
        self.assertNotEqual(repeated[0]["value"], repeated[1]["value"], "A repeated key must not overwrite its other source paragraph.")
        remedy = next(entry for entry in entries if entry["file"] == "Ratna.txt" and entry["key"] == "RatnaH")
        self.assertTrue(remedy["rawValue"].startswith(" To get full auspicious result"))
        self.assertIn("\\n At the time", remedy["rawValue"], "Literal newline markers remain source data.")
        malformed = next(entry for entry in entries if entry["file"] == "dashafal.txt" and entry["key"] == "DasaC34511HN")
        self.assertEqual(malformed["value"], "3,4,511")
        self.assertEqual(malformed["mappingStatus"], "review")
        self.assertNotIn(511, malformed["houses"], "The invalid source number must not become an inferred house rule.")
        self.go("prediction")
        expect(self.page.locator("#pred-reference-view")).to_have_value("analysis")
        expect(self.page.locator("#pred-analysis-panel")).to_be_visible()
        self.page.locator("#pred-reference-view").select_option("library")
        self.page.locator("#pred-library-category").select_option("house-results")
        self.page.locator("#pred-library-search").fill("Bh9R35912")
        expect(self.page.locator("#pred-library-records [data-reference-entry]")).to_have_count(2)
        self.assertEqual(self.page.evaluate("window.KPPredictionLibrary.getData().count"), 2)

    def test_prediction_reference_csv_and_print_include_every_filtered_record_beyond_screen_pagination(self):
        self.go("prediction")
        self.page.locator("#pred-reference-view").select_option("library")
        self.page.locator("#pred-library-category").select_option("events")
        expect(self.page.locator("#pred-library-records [data-reference-entry]")).to_have_count(30)
        expect(self.page.locator("#pred-library-page")).to_contain_text("1–30 of 1046")
        self.page.locator("#pred-library-next").click()
        expect(self.page.locator("#pred-library-page")).to_contain_text("31–60 of 1046")
        self.assertEqual(self.page.evaluate("window.KPPredictionLibrary.getData().rows.length"), 1046)
        with self.page.expect_download() as download_info:
            self.page.locator("#pred-library-csv").click()
        download = download_info.value
        self.assertTrue(download.suggested_filename.endswith(".csv"))
        exported = list(csv.reader(io.StringIO(Path(download.path()).read_text(encoding="utf-8-sig"))))
        self.assertEqual(len(exported), 1047, "CSV includes all matching entries, not only the current thirty.")
        self.assertTrue(all(len(row) == 16 for row in exported))
        partnership = [row for row in exported[1:] if row[6] == "Profit from partnership"]
        self.assertEqual(len(partnership), 3, "Source duplicates must remain separate CSV records.")
        snapshot = self.page.evaluate("""() => {
            const root = document.createElement('div'); root.innerHTML = window.KPPredictionLibrary.snapshot();
            return {records:root.querySelectorAll('[data-reference-entry]').length,
                    controls:root.querySelectorAll('input,select,button,textarea').length};
        }""")
        self.assertEqual(snapshot, {"records": 1046, "controls": 0})
        self.page.locator("#pred-library-print").click()
        expect(self.page.locator("main > #report")).to_be_visible()
        expect(self.page.locator('#printReport > [data-report-section="prediction"] [data-reference-entry]')).to_have_count(1046)
        selected = self.page.evaluate("[...document.querySelectorAll('#report-page-options input:checked')].map(input=>input.dataset.reportPageKey)")
        self.assertEqual(selected, ["prediction"])

    def test_prediction_reference_filters_restore_across_categories_and_legacy_files_keep_analysis_available(self):
        self.go("prediction")
        self.page.locator("#pred-reference-view").select_option("library")
        self.page.locator("#pred-library-category").select_option("mahadasha-remedies")
        self.page.locator("#pred-library-subgroup").select_option("MD/AD remedies")
        self.assertEqual(self.page.evaluate("window.KPPredictionLibrary.getData().count"), 9)
        backup = self.page.evaluate("window.getChartData()")
        for field, expected in (("pred-reference-view", "library"), ("pred-library-category", "mahadasha-remedies"),
                                ("pred-library-subgroup", "MD/AD remedies"), ("pred-library-search", "")):
            self.assertEqual(backup["fields"][field]["value"], expected)
        self.page.locator("#pred-library-category").select_option("house-results")
        self.page.locator("#pred-library-search").fill("changed")
        self.import_file(json.dumps(backup), filename="reference-filters.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#pred-library-category")).to_have_value("mahadasha-remedies")
        expect(self.page.locator("#pred-library-subgroup")).to_have_value("MD/AD remedies")
        expect(self.page.locator("#pred-library-search")).to_have_value("")
        self.assertEqual(self.page.evaluate("window.KPPredictionLibrary.getData().count"), 9)
        self.page.set_viewport_size({"width": 390, "height": 844})
        widths = self.page.evaluate("({viewport:innerWidth,document:document.documentElement.scrollWidth})")
        self.assertLessEqual(widths["document"], widths["viewport"], "Reference paragraphs and controls must fit the mobile screen.")
        legacy = json.loads(json.dumps(backup))
        for field in ("pred-reference-view", "pred-library-category", "pred-library-subgroup", "pred-library-search"):
            legacy["fields"].pop(field)
        self.import_file(json.dumps(legacy), filename="legacy-before-reference-library.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        self.go("prediction")
        expect(self.page.locator("#pred-reference-view")).to_have_value("analysis")
        expect(self.page.locator("#pred-analysis-panel")).to_be_visible()
        expect(self.page.locator("#pred-library-category")).to_have_value("all")
        expect(self.page.locator("#pred-library-subgroup")).to_have_value("all")

    def test_horary_249_and_2193_boundaries_exact_planets_dst_and_legacy_import(self):
        # Independent Vimshottari proportions: Revati's last sub is Saturn
        # (19/120 of 13°20′); its last sub-sub is Jupiter (16/120 of that).
        tables = self.page.evaluate("""() => ({
            coarse:KPHorary.catalogue(249), fine:KPHorary.catalogue(2193)
        })""")
        self.assertEqual(len(tables["coarse"]), 249)
        self.assertEqual(len(tables["fine"]), 2193)
        self.assertEqual(tables["coarse"][0]["start"], 0)
        self.assertAlmostEqual(tables["coarse"][-1]["start"], 360 - 7600 / 3600, places=9)
        self.assertAlmostEqual(tables["fine"][1]["start"], 48000 * 7 / 120 * 7 / 120 / 3600, places=9)
        self.assertAlmostEqual(tables["fine"][-1]["start"], 360 - 7600 * 16 / 120 / 3600, places=9)
        # Krittika's Rahu sub crosses the Aries/Taurus seam. Splitting that
        # physical interval gives 249 number 23 and 2193 number 193 at 30°.
        self.assertEqual(tables["coarse"][22]["start"], 30)
        self.assertEqual(tables["fine"][192]["start"], 30)
        self.page.locator("#dob").fill("2000-01-01")
        self.page.locator("#birthTime").fill("12:00:00")
        self.page.locator("#dayAyan").fill("00:00:00")
        self.page.locator("#daySum").fill("00:00:00")
        self.page.locator("#birth-utc-offset").fill("0")
        self.page.locator("#chart-kind").select_option("horary")
        self.page.locator("#horary-number").fill("1")
        self.action("calculate")
        self.page.wait_for_function("KPHorary.getData()?.number===1 && currentKPModel?.ready")
        first = self.page.evaluate("""() => ({data:KPHorary.getData(),
            moon:currentKPModel.planets.find(p=>p.id==='Mo').longitude/3600,
            cusp:currentKPModel.houses.find(h=>h.id===1).longitude/3600,
            lords:['sgl','stl','sl','ssl'].map(key=>currentKPModel.houses.find(h=>h.id===1)[key])})""")
        self.assertEqual(first["data"]["utc"], "2000-01-01T12:00:00.000Z")
        self.assertAlmostEqual(first["cusp"], 0, places=7)
        self.assertEqual(first["lords"], ["Ma","Ke","Ke","Ke"],
                         "A zero-degree Ascendant must be Aries/Ashwini, not a previous-sign float at 360°.")
        self.assertLess(abs(first["moon"] - EPHEMERIS_REFERENCE[0]["tropical"]["Mo"]), .03,
                        "Horary planets must use the exact query instant, not a fake date implied by the chosen Ascendant.")
        self.page.locator("#birthTime").fill("13:00:00")
        self.page.locator("#birth-dst-minutes").fill("60")
        self.page.locator("#horary-system").select_option("2193")
        self.page.locator("#horary-number").fill("193")
        self.action("calculate")
        self.page.wait_for_function("KPHorary.getData()?.horarySystem===2193 && KPHorary.getData()?.number===193")
        second = self.page.evaluate("""() => ({data:KPHorary.getData(),
            moon:currentKPModel.planets.find(p=>p.id==='Mo').longitude/3600,
            cusp:currentKPModel.houses.find(h=>h.id===1).longitude/3600})""")
        self.assertEqual(second["data"]["utc"], first["data"]["utc"])
        self.assertAlmostEqual(second["moon"], first["moon"], places=7)
        self.assertAlmostEqual(second["cusp"], 30, places=7)
        saved = self.page.evaluate("getChartData()")
        self.assertEqual(saved["fields"]["horary-system"]["value"], "2193")
        self.assertEqual(saved["fields"]["birth-dst-minutes"]["value"], "60")
        self.import_file(json.dumps({"version":2,"basic":{"dob":"2001-02-03",
            "birthTime":"12:00:00","dayAyan":"23:00:00","daySum":"00:00:00",
            "lat":"13:04:00","lon":"80:15:00"}}), "legacy-natal.lkp")
        expect(self.page.locator("#chart-kind")).to_have_value("natal")
        expect(self.page.locator("#horary-system")).to_have_value("249")
        expect(self.page.locator("#birth-dst-minutes")).to_have_value("0")
        expect(self.page.locator("#birth-dst-minutes")).to_be_disabled()

    def test_matchmaking_hand_scores_timezone_dst_and_validated_notebook_lkp_roundtrip(self):
        fixtures = self.page.evaluate("""() => {
            const score=(b,g)=>KPMatchmaking.score(b,g),part=(s,n)=>s.kootas.find(k=>k.name===n).score;
            return {same:score(1,1),taraGood:part(score(.1,40/3+.1),'Tara'),
                taraBad:part(score(.1,2*40/3+.1),'Tara'),
                badBhakoot:part(score(1,31),'Bhakoot'),goodBhakoot:part(score(1,91),'Bhakoot'),
                sameNadi:part(score(.1,5*40/3+.1),'Nadi'),differentNadi:part(score(.1,40/3+.1),'Nadi')};
        }""")
        self.assertEqual(fixtures["same"]["total"], 28)
        self.assertEqual(next(k["score"] for k in fixtures["same"]["kootas"] if k["name"]=="Nadi"), 0)
        self.assertEqual(fixtures["taraGood"], 3)
        self.assertEqual(fixtures["taraBad"], 1.5,
                         "Inclusive Tara category 3 is unfavorable; the reverse category 8 supplies only 1.5 points.")
        self.assertEqual([fixtures["badBhakoot"],fixtures["goodBhakoot"]], [0,7])
        self.assertEqual([fixtures["sameNadi"],fixtures["differentNadi"]], [0,8])
        self.go("matchmaking")
        records = {
            "boy":{"name":"Person A","date":"2026-10-06","time":"05:30:00","timezone":"5.5","dst":"0",
                   "place":"Nashik","latitude":"19.9975","longitude":"73.7898"},
            "girl":{"name":"Person B","date":"2026-10-05","time":"18:00:00","timezone":"-7","dst":"60",
                    "place":"Nashik","latitude":"19.9975","longitude":"73.7898"},
        }
        natal = self.page.evaluate("""() => Object.fromEntries(['dob','birthTime','lat','lon','dayAyan','daySum']
            .map(id=>[id,document.getElementById(id).value]))""")
        for kind, record in records.items():
            for key, value in record.items():
                self.page.locator(f"#mm-{kind}-{key}").fill(value)
        self.page.locator("#mm-calculate").click()
        expect(self.page.locator("#mm-status")).to_have_attribute("data-state", "ready")
        data = self.page.evaluate("KPMatchmaking.getData()")
        self.assertEqual(data["boy"]["utc"], "2026-10-06T00:00:00.000Z")
        self.assertEqual(data["girl"]["utc"], data["boy"]["utc"])
        self.assertEqual(data["girl"]["effectiveOffset"], -6)
        self.assertEqual(data["ashtakoota"]["total"], 28)
        self.assertAlmostEqual(data["boy"]["positions"]["Mo"], data["girl"]["positions"]["Mo"], places=9)
        self.page.locator("#mm-save-memo").click()
        # A notebook beyond the old 10 KB generic field limit must still load.
        saved = self.page.evaluate("""() => {
            const first=KPMatchmaking.getMemos()[0],memos=Array.from({length:16},(_,i)=>({...first,
                id:'permanent-pair-'+i,boy:{...first.boy,name:'Boy '+i+' '+('A'.repeat(100))},
                girl:{...first.girl,name:'Girl '+i+' '+('B'.repeat(100))}}));
            if(!KPMatchmaking.restore(JSON.stringify(memos)))throw Error('Invalid test notebook');
            return getChartData();
        }""")
        self.assertGreater(len(saved["fields"]["mm-memos"]["value"]), 10000)
        self.page.locator("#mm-girl-time").fill("22:00:00")
        self.page.evaluate("KPMatchmaking.restore('[]')")
        self.import_file(json.dumps(saved), "match-pair.lkp")
        expect(self.page.locator("#mm-girl-time")).to_have_value("18:00:00")
        self.assertEqual(len(self.page.evaluate("KPMatchmaking.getMemos()")), 16)
        self.assertEqual(self.page.evaluate("KPMatchmaking.getData().ashtakoota.total"), 28)
        self.assertEqual(self.page.evaluate("""() => Object.fromEntries(['dob','birthTime','lat','lon','dayAyan','daySum']
            .map(id=>[id,document.getElementById(id).value]))"""), natal)
        malformed = self.page.evaluate("""saved => {
            const bad=JSON.parse(JSON.stringify(saved));bad.fields.dob.value='2000-01-01';
            bad.fields['mm-memos'].value='{bad JSON';let rejected=false;
            try{restoreChartData(bad);}catch(error){rejected=true;}
            return {rejected,dob:document.getElementById('dob').value,memos:KPMatchmaking.getMemos().length};
        }""", saved)
        self.assertTrue(malformed["rejected"])
        self.assertEqual(malformed["dob"], natal["dob"])
        self.assertEqual(malformed["memos"], 16)

    def test_event_nadi_and_ruling_workspaces_keep_native_chart_and_print_selected_sections(self):
        self.prepare_exact_kp_worksheets()
        self.action("calculate")
        natal = self.page.evaluate("""() => ({inputs:Object.fromEntries(['dob','birthTime','lat','lon','dayAyan','daySum']
            .map(id=>[id,document.getElementById(id).value])),planets:currentKPModel.planets.map(p=>[p.id,p.longitude]),
            houses:currentKPModel.houses.map(h=>[h.id,h.longitude])})""")
        self.go("event-promise")
        self.page.locator("#ep-event").select_option("custom")
        self.page.locator("#ep-custom-houses").fill("2,7,11")
        self.page.locator("#ep-input-mode").select_option("manual")
        for role, houses in {"CSL":"2","STL":"7","SBL":"11"}.items():
            self.page.locator(f"#ep-houses-{role}").fill(houses)
        self.page.locator("#ep-calculate").click()
        promise = self.page.evaluate("KPEventPromise.getData()")
        self.assertTrue(promise["ready"])
        self.assertEqual(promise["status"], "matched")
        self.assertEqual(promise["best"]["missing"], [])
        self.page.locator("#ep-houses-SBL").fill("10")
        self.page.locator("#ep-calculate").click()
        partial = self.page.evaluate("KPEventPromise.getData()")
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(partial["best"]["missing"], [11])
        self.go("nadi-astrology")
        self.page.locator("#na-source").select_option("moment")
        self.page.locator("#na-cusp-source").select_option("transit")
        for key,value in {"date":"2026-10-06","time":"05:30:00","timezone":"5.5",
                          "latitude":"0","longitude":"0","place":"Query location"}.items():
            self.page.locator(f"#na-{key}").fill(value)
        self.page.locator("#na-update").click()
        nadi = self.page.evaluate("KPNadiAstrology.getData()")
        self.assertTrue(nadi["ready"])
        self.assertEqual(nadi["moment"]["utc"], "2026-10-06T00:00:00.000Z")
        expect(self.page.locator("#na-grid [data-nadi-planet]")).to_have_count(9)
        expected_ayan = (datetime(2026,10,6)-datetime(1990,6,15)).total_seconds() / (365.2425*86400) * 50.29/3600
        expected_moon = EPHEMERIS_REFERENCE[1]["tropical"]["Mo"] - expected_ayan
        moon = next(card["planet"]["longitude"] / 3600 for card in nadi["cards"] if card["id"]=="Mo")
        self.assertLess(abs(moon-expected_moon), .03)
        self.go("ruling-planets")
        for key,value in {"date":"2026-10-06","time":"05:30:00","offset":"5.5","place":"Query location",
                          "latitude":"0","longitude":"0"}.items():
            self.page.locator(f"#rpw-{key}").fill(value)
        self.page.locator("#rpw-calculate").click()
        ruling = self.page.evaluate("KPRulingWorkspace.getData()")
        self.assertEqual(ruling["utc"], "2026-10-06T00:00:00.000Z")
        self.assertLess(abs(next(row["longitude"] for row in ruling["rows"] if row["id"]=="Mo")-expected_moon), .03)
        expect(self.page.locator("#rpw-table [data-rpw-planet]")).to_have_count(4)
        retained = self.page.evaluate("""() => ({inputs:Object.fromEntries(['dob','birthTime','lat','lon','dayAyan','daySum']
            .map(id=>[id,document.getElementById(id).value])),planets:currentKPModel.planets.map(p=>[p.id,p.longitude]),
            houses:currentKPModel.houses.map(h=>[h.id,h.longitude])})""")
        self.assertEqual(retained, natal, "Separate query workspaces must preserve the native inputs and computed chart.")
        popup = self.selected_report_popup(["event-promise","nadi-astrology","ruling-planets"])
        sections = popup.locator("body > .report-page").evaluate_all("pages=>pages.map(p=>p.dataset.reportSection)")
        self.assertEqual(sections, ["event-promise","nadi-astrology","ruling-planets"])
        self.assertEqual(self.page.locator("#report-page-options [data-report-page-key]").count(), 24)
        expect(popup.locator('[data-report-section="nadi-astrology"] [data-nadi-planet]')).to_have_count(9)
        expect(popup.locator('[data-report-section="ruling-planets"] [data-rpw-planet]')).to_have_count(4)
        popup.close()

    def test_india_offline_gazetteer_keeps_all_populated_rows_and_source_codes(self):
        import hashlib
        from collections import Counter
        self.assertFalse(self.page.evaluate("window.KPIndiaPlaces.getData().ready"), "The large index must remain lazy until a place lookup is requested.")
        document = (REPOSITORY / "index.html").read_text()
        metadata = json.loads(re.search(r'<script id="kp-india-places-metadata"[^>]*>(.*?)</script>', document, re.S).group(1))
        packed = base64.b64decode(re.search(r'<script id="kp-india-places-packed"[^>]*>(.*?)</script>', document, re.S).group(1))
        self.assertEqual(hashlib.sha256(packed).hexdigest(), metadata["embeddedSHA256"])
        raw = zlib.decompress(packed, 31)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["embeddedTSVSHA256"])
        rows = raw.decode().splitlines()
        self.assertEqual(len(rows), 557995)
        states, features = Counter(), Counter()
        for line in rows:
            name, latitude, longitude, state, district, population, feature = line.split("\t")
            state, district, feature = int(state), int(district), int(feature)
            self.assertTrue(name)
            self.assertTrue(-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180)
            self.assertEqual(metadata["districts"][district]["state"], metadata["states"][state]["code"])
            states[state] += 1
            features[metadata["featureCodes"][feature]] += 1
        self.assertEqual(dict(features), metadata["features"])
        self.assertEqual(sum(state["known"] for state in metadata["states"]), 36)
        self.assertEqual(sum(states[i] for i, state in enumerate(metadata["states"]) if not state["known"]), 37)
        self.assertTrue(all(states[i] == state["count"] for i, state in enumerate(metadata["states"])))
        self.assertEqual(features["PPLQ"], 8969)
        self.assertEqual(features["PPLH"], 2)
        self.assertEqual(metadata["mirrorCommit"], "d80fb96ad43f3a9216dbd0cf2b9cdd38ffffd78d")
        self.assertEqual(metadata["license"], "CC BY 4.0")
        self.assertIn("not a complete Census", metadata["coverage"])
        ready = self.page.evaluate("window.KPIndiaPlaces.ready()")
        self.assertTrue(ready["ready"])
        for query, expected in (
            ("Delhi", ("Delhi", 28.65195, 77.23149, "07")),
            ("Mumbai", ("Mumbai", 19.07283, 72.88261, "16")),
            ("Nashik", ("Nashik", 19.99727, 73.79096, "16")),
            ("Uruli Kanchan", ("Uruli Kanchan", 18.48982, 74.13376, "16")),
        ):
            result = self.page.evaluate("query=>window.KPIndiaPlaces.search(query)", query)
            self.assertLessEqual(len(result), 30)
            self.assertEqual(tuple(result[0][key] for key in ("name", "latitude", "longitude", "stateCode")), expected)
        self.assertEqual(self.page.evaluate("window.KPIndiaPlaces.search('mu')"), [])
        district_results = self.page.evaluate("window.KPIndiaPlaces.search('Uruli',{state:'16',district:'521'})")
        self.assertTrue(district_results)
        self.assertTrue(all(row["stateCode"] == "16" and row["districtCode"] == "521" for row in district_results))
        self.assertEqual(self.page.evaluate("window.KPIndiaPlaces.search('Uruli Kanchan',{state:'07'})"), [])
        delhi = self.page.evaluate("window.KPIndiaPlaces.search('Delhi')")[0]
        self.assertEqual(delhi["districtCode"], "")
        self.assertFalse(delhi["districtKnown"], "A missing source district must not be guessed from proximity.")

    def test_india_place_picker_fills_coordinates_offline_and_round_trips_lkp(self):
        blocked_requests = []
        def block_network(route):
            blocked_requests.append(route.request.url)
            route.abort()
        # The complete application is already loaded. Every later lookup must
        # work even when all subsequent network requests are rejected.
        self.page.route("**/*", block_network)
        birth_date = self.page.locator("#dob").input_value()
        birth_time = self.page.locator("#birthTime").input_value()
        panel = self.page.locator('[data-place-for="birthPlace"]')
        panel.locator("select").nth(0).select_option("16")
        panel.locator("select").nth(1).select_option("521")
        self.page.locator("#birthPlace").fill("Uruli Kanchan")
        expect(panel.locator(".kp-india-picker-result").first).to_be_visible(timeout=15000)
        panel.locator(".kp-india-picker-result").first.click()
        expect(self.page.locator("#lat")).to_have_value("18:29:23")
        expect(self.page.locator("#lon")).to_have_value("74:08:02")
        expect(self.page.locator("#birth-utc-offset")).to_have_value("5.5")
        expect(self.page.locator("#birthPlace")).to_have_value(re.compile(r"^Uruli Kanchan.*India$"))
        expect(panel.locator(".kp-india-picker-status")).to_have_attribute("data-state", "selected")
        expect(panel.locator(".kp-india-picker-results")).to_be_hidden()
        self.assertEqual(self.page.locator("#dob").input_value(), birth_date)
        self.assertEqual(self.page.locator("#birthTime").input_value(), birth_time)
        selected_native = self.page.locator("#birthPlace").input_value()
        for prefix in ("tc", "tp", "na"):
            local_date = self.page.locator("#" + prefix + "-date").input_value()
            local_time = self.page.locator("#" + prefix + "-time").input_value()
            self.page.evaluate("""async prefix=>{
                const [place]=await window.KPIndiaPlaces.search('Nashik');
                return window.KPIndiaPlaces.choose(place.id,prefix+'-place');
            }""", prefix)
            expect(self.page.locator("#" + prefix + "-latitude")).to_have_value("19.99727")
            expect(self.page.locator("#" + prefix + "-longitude")).to_have_value("73.79096")
            self.assertEqual(self.page.locator("#" + prefix + "-date").input_value(), local_date)
            self.assertEqual(self.page.locator("#" + prefix + "-time").input_value(), local_time)
            self.assertEqual(self.page.locator("#birthPlace").input_value(), selected_native)
        self.assertEqual(blocked_requests, [], "Place searches and selections must make no external requests.")
        with self.page.expect_download() as download:
            self.action("export")
        self.assertTrue(download.value.suggested_filename.endswith(".lkp"))
        backup_text = Path(download.value.path()).read_text()
        backup = json.loads(backup_text)
        self.assertEqual(backup["fields"]["birthPlace"]["value"], selected_native)
        self.assertEqual(backup["fields"]["lat"]["value"], "18:29:23")
        self.assertEqual(backup["fields"]["lon"]["value"], "74:08:02")
        self.assertFalse(any(key.startswith("india-") for key in backup["fields"]), "Transient filters must not become chart data.")
        self.assertNotIn("kp-india-places-packed", backup_text)
        self.assertLess(len(backup_text), 1000000, "The embedded gazetteer must never be copied into chart backups.")
        self.page.locator("#birthPlace").fill("Changed place")
        self.page.locator("#lat").fill("00:00:00")
        self.import_file(backup_text, filename="india-place-round-trip.lkp")
        expect(self.page.locator("#workspace-toast")).to_contain_text("Chart imported.")
        expect(self.page.locator("#birthPlace")).to_have_value(selected_native)
        expect(self.page.locator("#lat")).to_have_value("18:29:23")
        expect(self.page.locator("#lon")).to_have_value("74:08:02")
        self.assertTrue(self.page.evaluate("window.KPIndiaPlaces.getData().ready"))
        self.page.set_viewport_size({"width": 390, "height": 844})
        width = self.page.evaluate("({document:document.documentElement.scrollWidth,viewport:innerWidth})")
        self.assertLessEqual(width["document"], width["viewport"])

if __name__ == "__main__":
    unittest.main()
