"""Browser regression checks for the dependency-free calculator.

Run with: python3 -m unittest discover -s tests -v
Requires Python Playwright and a Chromium executable on PATH (or set
CALCULATOR_CHROMIUM to its path). No browser or package downloads occur here.
"""

import base64
import functools
import json
import os
from pathlib import Path
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
    "basic", "ayan", "lmt", "stcalc", "raphael5", "planet", "mdcalc",
    "karyesh", "south9", "report", "astrosettings",
)
OUTPUT_IDS = (
    "ayanValue", "lonDifference", "lmtFinal", "birthPlaceSiderealTime",
    "r5_nirayan_1", "r5_rashi_1", "p6_motion_0", "p6_final_0",
    "mdBirthDasha", "mdBhogyaDuration",
)
# A tiny local fixture tests the cover's image binding and print readiness.
# It deliberately does not stand in for the user's requested devotional photo.
COVER_IMAGE_FIXTURE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aCfoAAAAASUVORK5CYII="


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

    def import_file(self, contents):
        self.action("import")
        self.page.locator("#import-chart-file").set_input_files({
            "name": "chart.json", "mimeType": "application/json", "buffer": contents.encode("utf-8"),
        })

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
                page.on("requestfailed", lambda request: failed_resources.append(f"{request.url}: {request.failure}"))
                page.on("response", lambda response: failed_resources.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
                page.on("pageerror", lambda error: self.errors.append("Standalone HTML: " + str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/index.html", wait_until="load")
                page.wait_for_timeout(1700)
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
                self.assertTrue(download.suggested_filename.endswith(".json"))
                exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
                self.assertEqual(exported["fields"]["name"]["value"], "Portable chart · अनया")
                self.assertEqual(exported["fields"]["birthTime"]["value"], "10:30:00")
                self.assertEqual(failed_resources, [], "The standalone workflow must complete without failed resource loads.")
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

    def test_json_download_and_file_import_restore_the_chart(self):
        self.prepare_worksheets()
        expected_fields, expected_outputs = self.editable_values(), self.outputs()
        with self.page.expect_download() as download_info:
            self.action("export")
        download = download_info.value
        self.assertTrue(download.suggested_filename.endswith(".json"))
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
        expect(self.page.locator("#printReport > .report-page")).to_have_count(12)
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

    def test_selected_cover_photo_survives_backups_printing_and_standalone_software_download(self):
        self.prepare_worksheets()
        self.go("report")
        photo_input = self.page.locator("#report-cover-photo-input")
        status = self.page.locator("#report-cover-photo-status")
        self.assertEqual(photo_input.locator("xpath=ancestor::main").count(), 0,
                         "The image picker must not enter the chart's generic field serialization.")
        expect(self.page.locator("#choose-report-cover-photo")).to_be_visible()
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
        expect(self.page.locator("#printReport > .report-page")).to_have_count(12)
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
            self.page.get_by_role("button", name="Print Report", exact=True).click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Selected-photo print: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(12)
        printed_photo = popup.locator(".report-front-page .report-cover-image")
        expect(printed_photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
        printed_photo.evaluate("image => image.decode()")
        popup.close()

        with self.page.expect_download() as software_info:
            self.page.locator("#download-cover-software").click()
        software = software_info.value
        self.assertTrue(software.suggested_filename.endswith(".html"))
        with tempfile.TemporaryDirectory(prefix="kp-photo-standalone-test-") as directory:
            standalone = Path(directory) / "index.html"
            software.save_as(standalone)
            self.assertEqual(list(Path(directory).iterdir()), [standalone])
            self.assertIn('id="report-cover-photo-data"', standalone.read_text(encoding="utf-8"),
                          "The downloaded software must carry its cover photo in the single HTML file.")
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
                page.on("pageerror", lambda error: self.errors.append("Downloaded photo software: " + str(error)))
                page.goto(isolated_url, wait_until="load")
                page.wait_for_timeout(1700)
                embedded_photo = page.locator("#report-cover-photo-data").text_content()
                self.assertIn(json.dumps(COVER_IMAGE_FIXTURE), embedded_photo)
                context.set_offline(True)
                page.locator(".app-sidebar [data-tab='report']").click()
                expect(page.locator("#printReport > .report-page")).to_have_count(12)
                offline_photo = page.locator(".report-front-page .report-cover-image")
                expect(offline_photo).to_have_attribute("src", COVER_IMAGE_FIXTURE)
                offline_photo.evaluate("image => image.decode()")
                self.assertGreater(offline_photo.evaluate("image => image.naturalWidth"), 0)
                for field, expected in (
                    ("name", "Regression chart · मीरा"), ("dob", "1990-06-15"),
                    ("astroName", "Test Astrologer"), ("astroMobile", "1234567890"),
                    ("astroAddress", "Pune\nClient report office"),
                ):
                    with self.subTest(downloaded_cover_field=field):
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
                expect(page.locator("#printReport > .report-page")).to_have_count(12)
                expect(page.locator('.report-front-page [data-cover-field="birthTime"]')).to_have_text("13:30:00")
                expect(page.locator(".report-front-page .report-cover-image")).to_have_attribute("src", COVER_IMAGE_FIXTURE)
                self.assertEqual(unexpected_requests, [],
                                 "The copied software and cover photo must work without sibling files or network assets.")
            finally:
                context.close()
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

    def test_print_popup_has_twelve_a4_pages_without_duplicate_ids(self):
        self.prepare_worksheets()
        self.page.evaluate("source => { window.KP_REPORT_COVER_IMAGE = source; }", COVER_IMAGE_FIXTURE)
        self.go("report")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(12)
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
            self.page.get_by_role("button", name="Print Report", exact=True).click()
        popup = popup_info.value
        popup.on("pageerror", lambda error: self.errors.append("Print popup: " + str(error)))
        popup.wait_for_load_state("domcontentloaded")
        popup.wait_for_function("window.testPrintCalled === true")
        expect(popup.locator("body > .report-page")).to_have_count(12)
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
                if index < 11:
                    self.assertEqual(geometry["breakAfter"], "page")
        content_errors = popup.locator("body > .report-page").evaluate_all("""pages => pages.flatMap((page, index) => {
            const bounds = page.getBoundingClientRect(), errors = [];
            for (const element of page.querySelectorAll('.report-developer-footer,.kp-key,.kp-table,[data-cover-field],.report-cover-image,.report-front-heading,.report-front-footnote')) {
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


if __name__ == "__main__":
    unittest.main()
