"""Focused checks for the additive 1.2.2 interface modules."""

import unittest

from playwright.sync_api import expect

import test_personal_predictions as personal


class ReleaseUIRegressionTests(unittest.TestCase):
    setUpClass = classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
    tearDownClass = classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
    setUp = personal.PersonalPredictionTests.setUp
    tearDown = personal.PersonalPredictionTests.tearDown

    def test_duplicate_dasha_route_and_additive_tools(self):
        expect(self.page.locator('nav [data-tab="dasha-fal"],#quick-dasha-fal')).to_have_count(0)
        expect(self.page.locator('#dasha-fal')).to_be_hidden()
        dasha = self.page.evaluate(
            "() => ({ready:KPDashaFal.current().ready, "
            "levels:KPDashaFal.current().periods.length, "
            "predictionTab:Boolean(document.getElementById('pred-tab-dasha-results'))})"
        )
        self.assertTrue(dasha["ready"])
        self.assertEqual(dasha["levels"], 3)
        self.assertTrue(dasha["predictionTab"])

        native = self.page.evaluate("JSON.stringify(currentKPModel)")
        self.page.locator('#quick-transit-panchang').click()
        expect(self.page.locator('#tp-calendar-preview')).to_be_visible()
        self.page.evaluate(
            """() => {
              const values={
                'tp-date':'2026-10-12','tp-time':'16:59:59',
                'tp-timezone':'5.5','tp-place':'Chennai',
                'tp-latitude':'13:04:00','tp-longitude':'80:15:00'
              };
              for (const [id,value] of Object.entries(values)) {
                const field=document.getElementById(id);field.value=value;
                field.dispatchEvent(new Event('change',{bubbles:true}));
              }
              document.getElementById('tp-calculate').click();
            }"""
        )
        self.page.wait_for_function(
            "window.KPTransitPanchangDinvisesh?.getData()?.config?.date === '2026-10-12'",
            timeout=60_000,
        )
        live = self.page.locator('#tp-daily-extension')
        expect(live.locator('.tp-transition-card')).to_have_count(4)
        expect(live.locator('.tp-solar-card')).to_have_count(6)
        expect(live.locator('.tp-chogh-row [data-quality]')).to_have_count(16)
        expect(live.locator('[data-transit-panchang-chart="0530"]')).to_have_count(1)
        daily = self.page.evaluate("KPTransitPanchangDinvisesh.getData()")
        self.assertEqual(daily["chart"]["moment"], "2026-10-12T00:00:00.000Z")
        self.assertEqual(self.page.evaluate("JSON.stringify(currentKPModel)"), native)

        with self.page.expect_popup() as opened:
            self.page.locator('#tp-calendar-preview').click()
        calendar = opened.value
        calendar.wait_for_function(
            "document.getElementById('calendar-root')?.dataset.anchor === '2026-10-01'",
            timeout=120_000,
        )
        expect(calendar.locator('.tp-calendar-day')).to_have_count(31)
        for button in ('cal-prev', 'cal-next', 'cal-print', 'cal-zoom-in', 'cal-zoom-out', 'cal-close'):
            expect(calendar.locator('#' + button)).to_be_visible()
        calendar.close()

        self.page.locator('#quick-about').click()
        expect(self.page.locator('#about .developer-profile h2')).to_have_text(
            'Shri. Nitin R Talegaonkar — B.Sc-Maths/MCA'
        )
        expect(self.page.locator('#about .about-advisor')).to_contain_text(
            'Mr. Anil Deshmukh'
        )
        expect(self.page.locator('#choose-about-photo')).to_be_visible()

        self.page.locator('#quick-astrosettings').click()
        expect(self.page.locator('#setting-ayanamshaCalculation')).to_have_value('uploaded-kp')
        expect(self.page.locator('#setting-outerUranus,#setting-outerNeptune,#setting-outerPluto')).to_have_count(3)

        self.page.locator('#quick-south9').click()
        expect(self.page.locator('.kp-lord-size-control[data-lord-control="chart"]')).to_be_visible()
        self.assertTrue(self.page.evaluate("KPChartEnlarger.open(document.getElementById('kundali'))"))
        expect(self.page.locator('#kp-enlarge-dialog')).to_be_visible()
        expect(self.page.locator('#kp-enlarge-dialog [data-enlarge-action="in"]')).to_be_visible()
        self.page.evaluate("KPChartEnlarger.close()")


if __name__ == '__main__':
    unittest.main()
