"""Protect original-KP delegation, native results and legacy-source migration.

The optional display/settings modules must not alter the source engine's output.
Swiss choices from older saved charts migrate to the exact original KP tables.
"""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path
import re
import shutil
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    ROOT / "vendor/ephemeris/source-adapter.js",
    ROOT / "vendor/interface/calculation-sources.js",
)
def without_new_modules() -> bytes:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for element, identifier in (
        ("script", "kp-swiss-krishnamurti"),
        ("script", "kp-ephemeris-source-adapter"),
        ("script", "kp-calculation-sources"),
        ("style", "kp-calculation-sources-style"),
    ):
        html = re.sub(
            rf'<{element}\s+id=["\']{re.escape(identifier)}["\'][^>]*>.*?</{element}>',
            "",
            html,
            flags=re.DOTALL,
        )
    return html.encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    baseline = b""

    def do_GET(self):  # noqa: N802 - stdlib callback name
        if self.path.split("?", 1)[0] == "/ephemeris-source-baseline.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self.baseline)))
            self.end_headers()
            self.wfile.write(self.baseline)
            return
        super().do_GET()

    def log_message(self, _format, *_args):
        pass


class EphemerisSourceRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chromium = os.environ.get("CALCULATOR_CHROMIUM") or shutil.which("chromium") or shutil.which("chromium-browser")
        if not chromium:
            raise unittest.SkipTest("Chromium is required for browser regression checks.")
        Handler.baseline = without_new_modules()
        handler = functools.partial(Handler, directory=str(ROOT))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    @staticmethod
    def snapshot(page):
        return page.evaluate("""() => {
          window.KPHomeDasha?.refresh();
          const periods=(window.mdDashaPeriods||[]).map(row=>({
            key:row.key,lord:row.lord,years:row.years,y:row.y,m:row.m,d:row.d,
            start:row.start,end:row.end,isBirth:row.isBirth,
            birthRemainingDays:row.birthRemainingDays,birthElapsedDays:row.birthElapsedDays,
            fullStart:row.fullStart
          }));
          return JSON.parse(JSON.stringify({
            siderealTime:document.getElementById('birthPlaceSiderealTime').value,
            ayanamsha:document.getElementById('ayanValue').value,
            planets:Object.fromEntries(Object.entries(window.lastPlanetPositions||{}).sort()),
            cusps:(window.cuspResults||[]).map(row=>({i:row.i,nir:row.nir})),
            vimshottari:{birthLord:document.getElementById('mdBirthDasha').value,balance:document.getElementById('mdBhogyaDuration').value,periods}
          }));
        }""")

    def test_original_kp_source_is_exact_and_old_swiss_choices_migrate(self):
        context = self.browser.new_context(viewport={"width": 1280, "height": 900})
        self.addCleanup(context.close)
        context.add_init_script("localStorage.removeItem('kpCalculationSourcesV1')")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            f"http://127.0.0.1:{self.server.server_port}/ephemeris-source-baseline.html",
            wait_until="load",
            timeout=120_000,
        )
        page.wait_for_function("window.KPEphemeris && window.KPHomeDasha && window.KPWorksheetEphemeris")
        page.evaluate("""() => {
          const values={name:'Ephemeris regression',dob:'1950-12-20',birthTime:'05:02:00',birthPlace:'India',lat:'10:46:00',lon:'76:42:00',
            'birth-utc-offset':'5.5','birth-dst-minutes':'0',stdLon:'82:30:00','chart-kind':'natal','instant-prashna':'0',
            'kp-ayanamsha-source':'annual','p6-ephemeris-source':'automatic','st-ephemeris-source':'automatic','r5-house-source':'automatic'};
          for(const [id,value] of Object.entries(values)){const field=document.getElementById(id);if(field)field.value=value;}
          window.calculateAll();window.KPHomeDasha.refresh();
        }""")
        page.wait_for_function("""() =>
          document.getElementById('birthPlaceSiderealTime').value &&
          Object.keys(window.lastPlanetPositions||{}).length===9 &&
          (window.cuspResults||[]).length===12 &&
          (window.mdDashaPeriods||[]).length===9
        """, timeout=60_000)
        before = self.snapshot(page)
        self.assertEqual(before["siderealTime"], "10:30:45")
        self.assertEqual(len(before["planets"]), 9)
        self.assertEqual(len(before["cusps"]), 12)
        self.assertEqual(len(before["vimshottari"]["periods"]), 9)
        page.evaluate("""() => {window.__kpOriginalSources={ephemeris:window.KPEphemeris,annual:window.KPAnnualAyanamsha,uploaded:window.KPUploadedEphemeris};}""")

        for module in MODULES:
            page.add_script_tag(path=str(module))
        page.wait_for_function("window.KPCalculationSources && window.KPEphemerisSources?.getSource()==='uploaded-kp'")
        self.assertEqual(self.snapshot(page), before, "Loading the optional modules must not mutate an existing uploaded-KP chart.")

        delegation = page.evaluate("""() => {
          const original=window.__kpOriginalSources,date=new Date('2026-10-12T06:30:00Z');
          const originalRow=original.uploaded.get('2026-10-12'),adaptedRow=window.KPUploadedEphemeris.get('2026-10-12');
          return {
            source:window.KPEphemerisSources.getSource(),
            positions:JSON.stringify(original.ephemeris.positions(date))===JSON.stringify(window.KPEphemeris.positions(date)),
            longitude:original.ephemeris.longitude(date,'Mo')===window.KPEphemeris.longitude(date,'Mo'),
            ascendant:original.ephemeris.ascendant(date,18.52,73.85)===window.KPEphemeris.ascendant(date,18.52,73.85),
            annual:original.annual.at(date)===window.KPAnnualAyanamsha.at(date),
            uploadedData:JSON.stringify(originalRow)===JSON.stringify(adaptedRow),
            planetKeys:Object.keys(window.KPEphemeris.positions(date))
          };
        }""")
        self.assertEqual(delegation["source"], "uploaded-kp")
        delegated_keys=("positions", "longitude", "ascendant", "annual", "uploadedData")
        self.assertTrue(all(delegation[key] for key in delegated_keys), delegation)
        self.assertEqual(delegation["planetKeys"], ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"])

        page.evaluate("calculateAll(); KPHomeDasha.refresh()")
        page.wait_for_timeout(250)
        self.assertEqual(self.snapshot(page), before, "A full recalculation through the default adapter must be byte-for-byte stable.")

        saved = page.evaluate("getChartData()")
        self.assertEqual(saved["calculationSources"]["ayanamshaSource"], "uploaded-kp")
        page.evaluate("KPCalculationSources.set({ayanamshaSource:'swiss-kp',outerUranus:true,outerNeptune:true,outerPluto:true})")
        isolation = page.evaluate("""() => ({
          source:KPEphemerisSources.getSource(),planetKeys:Object.keys(KPEphemeris.positions('2026-10-12T06:30:00Z')),
          outerKeys:Object.keys(KPCalculationSources.outerPositions('2026-10-12T06:30:00Z')),
          uploaded:KPUploadedEphemeris.get('2026-10-12'),options:KPEphemerisSources.sources
        })""")
        self.assertEqual(isolation["source"], "uploaded-kp")
        self.assertEqual(isolation["options"], ["uploaded-kp"])
        self.assertEqual(isolation["planetKeys"], ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"])
        self.assertEqual(isolation["outerKeys"], ["Ur", "Ne", "Pl"])
        self.assertIsNotNone(isolation["uploaded"])

        page.evaluate("calculateAll(); KPHomeDasha.refresh()")
        page.wait_for_function(
            "window.currentKPModel?.ready "
            "&& Object.keys(window.lastPlanetPositions||{}).length===9 "
            "&& (window.cuspResults||[]).length===12 "
            "&& (window.mdDashaPeriods||[]).length===9",
            timeout=60_000,
        )
        swiss_chart = self.snapshot(page)
        self.assertTrue(swiss_chart["siderealTime"])
        self.assertEqual(len(swiss_chart["planets"]), 9)
        self.assertEqual(len(swiss_chart["cusps"]), 12)
        self.assertEqual(len(swiss_chart["vimshottari"]["periods"]), 9)

        page.evaluate("data => restoreChartData(data)", saved)
        page.wait_for_function("window.KPEphemerisSources.getSource()==='uploaded-kp'")
        page.wait_for_timeout(250)
        self.assertEqual(self.snapshot(page), before, "Restoring a saved default chart must restore the uploaded source and identical calculations.")
        self.assertFalse(errors, errors)


if __name__ == "__main__":
    unittest.main()
