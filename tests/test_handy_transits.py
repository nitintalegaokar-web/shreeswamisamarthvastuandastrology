"""Compact standalone transit UI must execute all three approved search tracks."""
import csv,io,unittest
from pathlib import Path
from playwright.sync_api import expect
import test_personal_predictions as personal

class HandyTransitTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def open(self):
  p=self.page;p.wait_for_function('typeof KPHandyTransits!=="undefined"&&document.getElementById("tr-handy-dates")')
  p.evaluate('''()=>{const values={'instant-prashna':'0','chart-kind':'natal','dob':'1950-12-20','birthTime':'05:02:00','lat':'13:00:00','lon':'80:15:00','birth-utc-offset':'5.5','birth-dst-minutes':'0','stdLon':'82:30:00'};for(const [id,v] of Object.entries(values))document.getElementById(id).value=v;calculateAll();}''')
  p.locator('#quick-transit').click();return p
 def test_compact_filters_planets_dates_and_mobile_without_changing_native(self):
  p=self.open();native=p.evaluate('JSON.stringify(currentKPModel)')
  expect(p.locator('[data-tr-search-mode]')).to_have_count(3);expect(p.locator('#tr-period')).to_be_hidden()
  expect(p.locator('#tr-search-date-start')).to_be_visible();expect(p.locator('#tr-search-date-end')).to_be_visible();expect(p.locator('#tr-date-dba-selection')).not_to_have_attribute('open','')
  expect(p.locator('#tr-match')).to_be_visible();expect(p.locator('#tr-planet-options input:checked')).to_have_count(9)
  p.locator('#tr-search-date-start').fill('2026-10-14T00:00');p.locator('#tr-search-date-end').fill('2026-10-15T00:00');expect(p.locator('#tr-date-range-source')).to_have_value('custom');expect(p.locator('#tr-search-date-start')).to_have_value('2026-10-14T00:00')
  p.locator('[data-tr-event-filter]').fill('no-such-event-12345');expect(p.locator('#tr-run')).to_be_disabled();expect(p.locator('#tr-event-match-count')).to_contain_text('0')
  p.locator('[data-tr-event-filter]').fill('career');expect(p.locator('#tr-run')).to_be_enabled()
  self.assertTrue(p.locator('#tr-event').evaluate('n=>[...n.options].filter(o=>!o.disabled).every(o=>o.textContent.toLowerCase().includes("career"))'))
  p.locator('[data-tr-event-filter]').fill('');p.locator('#tr-no-planets').click();expect(p.locator('#tr-planet-options input:checked')).to_have_count(0)
  p.locator('#tr-run').click();expect(p.locator('#tr-status')).to_contain_text('Select at least one');expect(p.locator('#transit .tr-result-mount')).to_be_hidden()
  p.locator('#tr-all-planets').click();expect(p.locator('#tr-planet-options input:checked')).to_have_count(9)
  for value in ['dasha','sun','event']:
   p.locator('[data-tr-search-mode="'+value+'"]').click();expect(p.locator('[data-tr-search-mode="'+value+'"]')).to_have_attribute('aria-pressed','true')
  self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),native)
  p.set_viewport_size({'width':390,'height':844});self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'),390)
  p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi",themeType:"dark"})');expect(p.locator('[data-tr-search-mode="event"]')).to_contain_text('कार्येश')
  p.screenshot(path='/tmp/KP-MASTER-compact-transit-mobile.png',full_page=True)
 def test_real_three_modes_return_bounded_valid_intervals_csv_and_preview(self):
  p=self.open();p.locator('#tr-main-cusp').select_option('10');p.locator('[data-tr-event-filter]').fill('change in career')
  p.locator('#tr-date-dba-selection>summary').click()
  saturn=p.locator('#tr-selected-md').evaluate('n=>[...n.options].find(o=>o.textContent.startsWith("Sa ·")).value');p.locator('#tr-selected-md').select_option(saturn);p.locator('#tr-selected-ad').select_option('0');p.locator('#tr-selected-pd').select_option('4')
  self.assertEqual(p.evaluate('KPTransit.selectedPeriods().periods.PD.id'),'Su')
  dates=p.evaluate('''()=>{const target=currentKPModel.planets.find(p=>p.id==='Sa'),zone=Number(document.getElementById('tr-timezone').value)*60000;for(let i=0;i<365;i++){const t=Date.UTC(2026,0,1,12)+i*86400000,d=KPDisplay.longitudeDetails(KPEphemeris.longitude(new Date(t),'Su')*3600);if(d.signIndex===target.signIndex&&d.nakIndex===target.nakIndex)return [t-86400000,t+86400000].map(v=>new Date(v+zone).toISOString().slice(0,16));}throw Error('No annual Sun crossing of the native Saturn sector');}''')
  p.locator('#tr-date-range-source').select_option('custom');p.locator('#tr-search-date-start').fill(dates[0]);p.locator('#tr-search-date-end').fill(dates[1]);p.locator('#tr-search-date-end').dispatch_event('change')
  natal=p.evaluate('JSON.stringify(currentKPModel)')
  for mode,count in [('event',9),('dasha',18),('sun',2)]:
   p.locator('[data-tr-search-mode="'+mode+'"]').click();self.assertEqual(p.evaluate('KPTransit.makeTracks(KPTransit.selectedPeriods()).length'),count)
   p.locator('#tr-run').click();p.wait_for_function('document.getElementById("tr-status").dataset.state!=="running"',timeout=120000)
   self.assertNotEqual(p.locator('#tr-status').get_attribute('data-state'),'error',p.locator('#tr-status').inner_text())
   self.assertTrue(p.evaluate('''()=>{const tracks=KPTransit.makeTracks(KPTransit.selectedPeriods()),r=KPTransit.currentRange();return KPTransit.getResults().every(row=>{const track=tracks.find(t=>t.id===row.trackId),mid=new Date((Date.parse(row.start)+Date.parse(row.end))/2),d=KPDisplay.longitudeDetails(KPEphemeris.longitude(mid,row.planet)*3600);return track.test(d)&&Date.parse(row.start)>=r.start&&Date.parse(row.end)<=r.end&&row.start<row.end;});}'''))
   rows=p.evaluate('KPTransit.getResults()');self.assertTrue(rows,mode+' must return actual matching intervals for this reference range')
   if mode=='event':
    self.assertTrue(rows);expect(p.locator('#tr-result-rows tr[data-track]')).to_have_count(len(rows));self.assertRegex(p.locator('#tr-result-rows tr[data-track]').first.locator('td').nth(1).inner_text(),r'\d\d:\d\d:\d\d')
    with p.expect_download() as item:p.locator('#tr-handy-csv').click()
    download=item.value;self.assertEqual(download.suggested_filename,'KP-MASTER-Transit-dates.csv');records=list(csv.DictReader(io.StringIO(Path(download.path()).read_text(encoding='utf-8-sig'))));self.assertEqual(len(records),len(rows));self.assertEqual(records[0]['Entry UTC'],rows[0]['start']);self.assertIn('change in career',records[0]['Event'].lower())
    with p.expect_popup() as item:p.locator('#transit-preview').click()
    preview=item.value;expect(preview.locator('.tr-result-table tbody tr[data-track]')).to_have_count(len(rows));preview.close()
   self.assertEqual(p.evaluate('JSON.stringify(currentKPModel)'),natal)
  p.screenshot(path='/tmp/KP-MASTER-compact-transits-desktop.png',full_page=True)

if __name__=='__main__':unittest.main()
