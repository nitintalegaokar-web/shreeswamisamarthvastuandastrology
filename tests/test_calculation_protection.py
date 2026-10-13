"""Small end-to-end guard for the approved KP native-chart reference.

This intentionally complements (rather than repeats) the detailed worksheet
tests.  It protects the one user-approved birth fixture across recalculation,
calculation-neutral chart controls, and chart save/reload.
"""

import unittest

import test_personal_predictions as personal


class CalculationProtectionTests(unittest.TestCase):
    setUpClass = classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
    tearDownClass = classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
    setUp = personal.PersonalPredictionTests.setUp
    tearDown = personal.PersonalPredictionTests.tearDown

    FIELDS = {
        "instant-prashna": "0",
        "chart-kind": "natal",
        "dob": "1950-12-20",
        "birthTime": "05:02:00",
        "lat": "10:46:00",
        "birth-utc-offset": "5.5",
        "birth-dst-minutes": "0",
        "stdLon": "82:30:00",
    }

    SNAPSHOT = """() => JSON.parse(JSON.stringify({
      siderealTime: document.getElementById('birthPlaceSiderealTime').value,
      siderealSeconds: KPBhavSadhan.getData().siderealSeconds,
      tableLatitude: KPBhavSadhan.getData().tableLatitude,
      siderealWorksheet: Object.fromEntries([
        'baseSidereal0530','stLmtDifference','stTenSixCorrection',
        'stGrandTotal','st24Adjustment'
      ].map(id => [id, document.getElementById(id).value])),
      ayanamsha: document.getElementById('ayanValue').value,
      planets: currentKPModel.planets.map(row => ({
        id:row.id, longitude:row.longitude, signIndex:row.signIndex,
        stl:row.stl, sl:row.sl, occ:row.occ, own:row.own
      })),
      houses: currentKPModel.houses.map(row => ({
        id:row.id, longitude:row.longitude, signIndex:row.signIndex,
        stl:row.stl, sl:row.sl
      })),
      ephemeris: KPWorksheetEphemeris.getData(),
      vimshottari: {
        birthLord: document.getElementById('mdBirthDasha').value,
        balance: document.getElementById('mdBhogyaDuration').value,
        periods: (window.mdDashaPeriods || []).map(row => ({
          key:row.key, lord:row.lord, years:row.years,
          y:row.y, m:row.m, d:row.d, start:row.start, end:row.end,
          isBirth:row.isBirth, birthRemainingDays:row.birthRemainingDays,
          birthElapsedDays:row.birthElapsedDays, fullStart:row.fullStart
        }))
      }
    }))"""

    def configure(self, longitude):
        fields = {**self.FIELDS, "lon": longitude}
        self.page.wait_for_function(
            "typeof KPWorksheetEphemeris?.siderealCalculation === 'function' "
            "&& typeof KPBhavSadhan?.getData === 'function'"
        )
        self.page.evaluate(
            """fields => {
              for (const [id, value] of Object.entries(fields)) {
                document.getElementById(id).value = value;
              }
              calculateAll();
            }""",
            fields,
        )
        self.page.wait_for_function(
            "window.currentKPModel?.ready "
            "&& (window.mdDashaPeriods || []).length === 9"
        )

    def snapshot(self):
        return self.page.evaluate(self.SNAPSHOT)

    def assert_restores_exactly(self, original, expected_st):
        saved = self.page.evaluate("getChartData()")
        self.page.reload(timeout=120_000)
        self.page.wait_for_function(
            "typeof KPWorksheetEphemeris?.siderealCalculation === 'function' "
            "&& typeof restoreChartData === 'function'"
        )
        self.page.evaluate("data => restoreChartData(data)", saved)
        self.page.wait_for_function(
            "expected => document.getElementById('birthPlaceSiderealTime').value === expected "
            "&& window.currentKPModel?.ready "
            "&& (window.mdDashaPeriods || []).length === 9",
            arg=expected_st,
        )
        self.assertEqual(self.snapshot(), original)

    def test_approved_reference_is_stable_across_ui_recalculate_and_reload(self):
        for longitude, expected_st in (
            ("76:42:00", "10:30:46"),
            ("89:10:00", "11:20:38"),
        ):
            with self.subTest(longitude=longitude):
                self.configure(longitude)
                original = self.snapshot()
                self.assertEqual(original["siderealTime"], expected_st)
                self.assertEqual(original["tableLatitude"], 11)

                # These controls are visual only.  They must never alter any
                # protected calculation or the generated Vimshottari periods.
                ui_result = self.page.evaluate(
                    """() => {
                      KPLordLabelSize.set(1.3);
                      const source = document.querySelector('#home-kundali .v38-chart')
                        || document.querySelector('#home-kundali [data-home-chart]');
                      const opened = source ? KPChartEnlarger.open(source) : false;
                      if (opened) {
                        document.querySelector('#kp-enlarge-dialog [data-enlarge-action="in"]')?.click();
                        KPChartEnlarger.close();
                      }
                      return {opened, scale:KPLordLabelSize.get()};
                    }"""
                )
                self.assertTrue(ui_result["opened"])
                self.assertEqual(ui_result["scale"], 1.3)
                self.assertEqual(self.snapshot(), original)

                for command in (
                    "updateSiderealTimeCalculation()",
                    "calculateAll()",
                    "updateTab4SampattikKaal(); updateRaphaelTable5()",
                ):
                    self.page.evaluate(command)
                    self.assertEqual(self.snapshot(), original)

                self.assert_restores_exactly(original, expected_st)


if __name__ == "__main__":
    unittest.main()
