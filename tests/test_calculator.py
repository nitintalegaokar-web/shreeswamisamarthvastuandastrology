"""Browser regression checks for the dependency-free calculator.

Run with: python3 -m unittest discover -s tests -v
Requires Python Playwright and a Chromium executable on PATH (or set
CALCULATOR_CHROMIUM to its path). No browser or package downloads occur here.
"""

import functools
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
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
        for index in range(9):
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

    def test_print_popup_has_nine_a4_pages_without_duplicate_ids(self):
        self.prepare_worksheets()
        self.go("report")
        expect(self.page.locator("#printReport > .report-page")).to_have_count(9)
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
        expect(popup.locator("body > .report-page")).to_have_count(9)
        expect(popup.locator("body > .report-page").first).to_contain_text("Regression chart · मीरा")
        for target, label in ((self.page, "calculator"), (popup, "print popup")):
            duplicates = target.evaluate("""() => {
                const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
                return [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
            }""")
            self.assertEqual(duplicates, [], f"Duplicate IDs in {label}: {duplicates}")
        popup.emulate_media(media="print")
        page_geometry = popup.locator("body > .report-page").evaluate_all("""pages => pages.map(page => {
            const style = getComputedStyle(page);
            return {width: parseFloat(style.width), height: parseFloat(style.height), display: style.display, breakAfter: style.breakAfter};
        })""")
        for index, geometry in enumerate(page_geometry):
            with self.subTest(print_page=index + 1):
                self.assertNotEqual(geometry["display"], "none", "Every report page must be visible when printing.")
                self.assertAlmostEqual(geometry["width"], 190 * 96 / 25.4, delta=1)
                self.assertAlmostEqual(geometry["height"], 277 * 96 / 25.4, delta=1)
                if index < 8:
                    self.assertEqual(geometry["breakAfter"], "page")
        paper_sizes = popup.evaluate("""() => [...document.styleSheets].flatMap(sheet => [...sheet.cssRules])
            .filter(rule => rule.constructor.name === 'CSSPageRule').map(rule => rule.style.size.toLowerCase())""")
        # Chromium normalizes explicit "A4 portrait" to "a4", whose default
        # orientation is portrait; the page dimensions above also enforce it.
        self.assertIn(paper_sizes[-1], ("a4", "a4 portrait"), "The print document must request A4 portrait paper.")


if __name__ == "__main__":
    unittest.main()
