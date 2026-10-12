"""One chart tooltip, correct public lords/DMS, both layouts and languages."""
import unittest
from playwright.sync_api import expect
import test_personal_predictions as personal

NAMES={'Su':'Sun','Mo':'Moon','Ma':'Mars','Me':'Mercury','Ju':'Jupiter','Ve':'Venus','Sa':'Saturn','Ra':'Rahu','Ke':'Ketu'}

class HoverDetailsTests(unittest.TestCase):
    setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
    tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
    setUp=personal.PersonalPredictionTests.setUp
    tearDown=personal.PersonalPredictionTests.tearDown

    def test_single_vertical_tooltip_for_planets_and_cusps(self):
        p=self.page
        p.wait_for_function('typeof KPHoverDetails!=="undefined"')
        p.locator('#quick-home').click()
        p.evaluate("document.getElementById('instant-prashna').value='0';calculateAll()")
        for style in ['north','south']:
            p.evaluate('style=>KPPreferences.save({...KPPreferences.get(),language:"english",chartStyle:style})',style)
            for selector,point in [('[data-planet="Su"]','currentKPModel.planets.find(p=>p.id==="Su")'),('[data-cusp="1"]','currentKPModel.houses[0]')]:
                label=p.locator('#home-kundali [data-hover-dms]'+selector+':visible').first
                label.hover()
                tip=p.locator('#kp-hover-detail')
                expect(tip).to_be_visible()
                self.assertEqual(p.locator('[role=tooltip]:visible').count(),1)
                self.assertEqual(tip.locator('[data-hover-row]').evaluate_all('rows=>rows.map(r=>r.dataset.hoverRow)'),['DMS','SGL','STL','SBL'])
                expected=p.evaluate(point)
                expect(tip.locator('[data-hover-row="DMS"]')).to_contain_text(expected['degree'].replace(' R',''))
                for key,field in [('SGL','sgl'),('STL','stl'),('SBL','sl')]:
                    expect(tip.locator('[data-hover-row="'+key+'"] b')).to_have_text(NAMES[expected[field]])
                self.assertFalse(label.evaluate('n=>n.hasAttribute("title")'))
                self.assertEqual(label.locator('title').count(),0)
                self.assertEqual(label.evaluate('n=>n.closest("svg")?.querySelectorAll(":scope>title").length||0'),0)
                p.wait_for_timeout(900)
                expect(tip).to_be_visible()
                p.mouse.move(1400,900)
                expect(tip).to_be_hidden()
        p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi",chartStyle:"south"})')
        p.locator('#home-kundali [data-hover-dms][data-planet="Su"]:visible').first.hover()
        tip=p.locator('#kp-hover-detail')
        expect(tip).to_be_visible()
        expect(tip.locator('.kp-hover-heading')).to_have_text('रवी')
        expect(tip.locator('[data-hover-row="SGL"] .kp-hover-label')).to_have_text('रा. स्वा.')
        self.assertNotIn('Mercury',tip.inner_text())
        tip.screenshot(path='/tmp/kp-single-colour-hover.png')
        p.emulate_media(media='print')
        expect(tip).to_be_hidden()

    def test_table_cusp_header_and_disabled_hover(self):
        p=self.page;p.wait_for_function('typeof KPHoverDetails!=="undefined"')
        p.locator('#quick-home').click()
        p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"english",chartStyle:"north"})')
        heading=p.locator('tr[data-house="1"] th[scope=row]:visible').first
        heading.hover()
        expect(p.locator('#kp-hover-detail')).to_be_visible()
        expect(p.locator('#kp-hover-detail [data-hover-row="SBL"]')).to_be_visible()
        p.mouse.move(1400,900)
        p.evaluate('KPPreferences.save({...KPPreferences.get(),tooltips:false})')
        p.locator('#home-kundali [data-hover-dms][data-planet="Su"]:visible').first.hover()
        p.wait_for_timeout(350)
        expect(p.locator('#kp-hover-detail')).to_be_hidden()

if __name__=='__main__':unittest.main()
