"""Supplied workbook integrity, independent interpolation and native chart integration."""
import bisect
import hashlib
import json
import math
import subprocess
import unittest
from pathlib import Path
from openpyxl import load_workbook
from playwright.sync_api import expect
import test_personal_predictions as personal
import test_protected_server as protected

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'vendor/houses/tables.json').read_text())
HOUSES = [10, 11, 12, 1, 2, 3]


def mix(a, b, fraction):
    return (a + ((b-a+180) % 360-180)*fraction) % 360


def reference(latitude, time, ayan, columns="numeric"):
    pool=DATA["printedValues"] if columns=="printed" else DATA["values"]
    low = min(len(DATA['times'])-2, bisect.bisect_right(DATA['times'], time)-1)
    high = low+1
    f = (time-DATA['times'][low])/(DATA['times'][high]-DATA['times'][low])
    a, b = math.floor(latitude), math.ceil(latitude)
    values = [mix(mix(pool[a][low][i], pool[a][high][i], f), mix(pool[b][low][i], pool[b][high][i], f), latitude-a) for i in range(6)]
    cusps = [None]*12
    for h, x in zip(HOUSES, values):
        cusps[h-1] = (x-ayan) % 360
        cusps[(h+5) % 12] = (x-ayan+180) % 360
    return cusps


class TableTests(unittest.TestCase):
    def test_printed_house_degree_columns_and_ascendant_dm(self):
        script="const fs=require('fs'),lib=require('./vendor/houses/table.js'),data=JSON.parse(fs.readFileSync('./vendor/houses/tables.json')),t=lib.create(data);console.log(JSON.stringify([t.lookup(0,0,0,'printed'),t.lookup(0,220,0,'printed'),t.lookup(0,110,24,'printed')]));"
        result=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT))
        self.assertEqual(DATA['metadata']['printedSourceColumns'],['10H','11H','12H','Asc DM','2H','3H'])
        self.assertEqual([result[0]['tropicalCusps'][h-1] for h in HOUSES],[0,32,62,90,118,148])
        self.assertEqual([result[1]['tropicalCusps'][h-1] for h in [10,11,12,2,3]],[1,33,63,119,149])
        self.assertAlmostEqual(result[1]['tropicalCusps'][0],90+50/60,places=10)
        self.assertAlmostEqual(result[2]['cusps'][0],90+25/60-24,places=10)
        self.assertAlmostEqual(result[2]['cusps'][9],336.5,places=10)
        self.assertEqual(result[2]['tableColumns'],'printed')

    def test_every_numeric_workbook_row_is_preserved_and_hashed(self):
        rows, duplicates = 0, 0
        for source in DATA['metadata']['sources']:
            path = ROOT / 'vendor/houses/source' / source['filename']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source['sha256'])
            workbook = load_workbook(path, read_only=True, data_only=True)
            self.assertEqual(workbook.sheetnames, source['sheets'])
            for sheet in workbook:
                lat = int(sheet.title[:-1]); last = None; packed = []
                for row in list(sheet.values)[1:]:
                    time = row[1]*3600+row[2]*60+row[3]
                    if time == last:
                        self.assertEqual(list(row[10:]), packed[-1][1]); duplicates += 1
                    else:
                        packed.append((time, list(row[10:]))); rows += 1
                    last = time
                self.assertEqual([r[0] for r in packed], DATA['times'])
                self.assertEqual([r[1] for r in packed], DATA['values'][lat])
            workbook.close()
        self.assertEqual(rows, 22021); self.assertEqual(duplicates, 671)

    def test_exact_rows_all_latitudes_interpolation_wrap_and_range_checks(self):
        cases = [[0, 0, 0], [60, 86400, 24], [18.8, 43201, 23.85], [59.99, 86399.9, 24.001], [0.01, 219, 0], [37.25, 21598.5, 23.7]]
        js = """const fs=require('fs');const data=JSON.parse(fs.readFileSync('vendor/houses/tables.json'));const api=require('./vendor/houses/table.js').create(data);let maximum=0;for(let lat=0;lat<=60;lat++)for(let row=0;row<data.times.length;row++){const result=api.lookup(lat,data.times[row]);for(let i=0;i<6;i++)maximum=Math.max(maximum,Math.abs(((result.tropicalCusps[[10,11,12,1,2,3][i]-1]-data.values[lat][row][i]+540)%360)-180));}const cases=JSON.parse(process.argv[1]);const invalid=[[-1,0],[60.01,0],[0,-1],[0,86401],[null,0],[0,null],[0,0,-1]].map(x=>{try{api.lookup(...x);return false;}catch(_){return true;}});console.log(JSON.stringify({maximum,results:cases.map(x=>api.lookup(...x)),invalid}));"""
        result = subprocess.run(['node', '-e', js, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, check=True)
        actual = json.loads(result.stdout)
        self.assertLess(actual['maximum'], 1e-10); self.assertTrue(all(actual['invalid']))
        for inputs, result in zip(cases, actual['results']):
            for a, b in zip(result['cusps'], reference(*inputs)):
                self.assertAlmostEqual(a, b, places=10)
            for i in range(6):
                self.assertAlmostEqual((result['cusps'][i+6]-result['cusps'][i]) % 360, 180)
        self.assertAlmostEqual(actual['results'][0]['tropicalCusps'][9], 0)
        self.assertLess(abs((actual['results'][3]['tropicalCusps'][9]+180) % 360-180), .01)


class BhavsadhanTests(unittest.TestCase):
    setUpClass = classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
    tearDownClass = classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
    setUp = personal.PersonalPredictionTests.setUp
    tearDown = personal.PersonalPredictionTests.tearDown

    def sample(self):
        self.page.wait_for_selector('#r5-house-source', state='attached')
        return self.page.evaluate('({data:KPBhavSadhan.getData(),cusps:currentKPModel.houses.map(h=>h.longitude),ready:currentKPModel.ready,source:document.getElementById("r5-house-source").value,st:document.getElementById("birthPlaceSiderealTime").value})')

    def verify(self, result):
        self.assertTrue(result['ready']); d = result['data']; self.assertEqual(d['source'], 'uploaded')
        expected = reference(d['latitude'], d['siderealSeconds'], d['ayanamsha'], columns=d.get('tableColumns','numeric'))
        self.assertEqual(result['cusps'], [math.floor(x*3600+.5) % 1296000 for x in expected])
        self.assertEqual(result['source'], 'automatic')

    def test_automatic_native_instant_edits_fallback_and_invalid_location(self):
        p = self.page; self.verify(self.sample())
        p.evaluate('''()=>{for(const [id,v] of Object.entries({'instant-prashna':'0','dob':'1986-07-15','birthTime':'13:11:00','lat':'18:48:00','lon':'74:13:00','stdLon':'82:30:00','birth-utc-offset':'5.5','p6-ephemeris-source':'automatic','st-ephemeris-source':'automatic'}))document.getElementById(id).value=v;calculateAll();}''')
        p.wait_for_timeout(250); before = self.sample(); self.verify(before)
        d = before['data']; b = d['brackets']
        self.assertEqual(p.locator('#stSmallTime').input_value(), f"{b['timeLow']//3600}:{b['timeLow']%3600//60:02}:{b['timeLow']%60:02}")
        original_planets = p.evaluate('currentKPModel.planets.map(x=>x.longitude)')
        # An explicit source override is an administrator worksheet operation.
        p.locator('#quick-admin-calculations').click();p.locator('[name="admin-pin"]').fill('684219');p.locator('[name="admin-confirm"]').fill('684219');p.locator('#admin-pin-submit').click();expect(p.locator('#admin-calculation-host')).to_be_visible()
        p.evaluate('document.getElementById("r5-house-source").value="computed";calculateAll()'); self.assertEqual(self.sample()['data']['source'], 'computed'); self.assertEqual(p.evaluate('currentKPModel.planets.map(x=>x.longitude)'), original_planets)
        p.evaluate('document.getElementById("r5-house-source").value="automatic";document.getElementById("birthTime").value="04:03:02";document.getElementById("birthTime").dispatchEvent(new Event("change",{bubbles:true}))')
        p.wait_for_timeout(500); changed = self.sample(); self.verify(changed); self.assertNotEqual(changed['cusps'], before['cusps'])
        for latitude, source in [('60:00:00','uploaded'), ('60:00:01','computed'), ('-18:48:00','computed')]:
            p.evaluate('lat=>{document.getElementById("lat").value=lat;calculateAll()}', latitude); self.assertEqual(self.sample()['data']['source'], source); self.assertTrue(self.sample()['ready'])
        p.evaluate('document.getElementById("lat").value="70:00:00";calculateAll()'); self.assertFalse(self.sample()['ready']); self.assertIsNone(self.sample()['data']); self.assertEqual(p.locator('#r5_nirayan_1').input_value(), '')
        self.assertEqual(p.evaluate('Array.from({length:3},()=>KPVedic.core().ready)'), [False]*3)
        p.evaluate('document.getElementById("lat").value="18:48:00";calculateAll()'); self.verify(self.sample()); self.assertTrue(p.evaluate('KPVedic.core().ready'))

    def test_manual_preservation_horary_and_administrator_source(self):
        p = self.page; self.sample(); p.locator('#quick-admin-calculations').click(); p.locator('[name="admin-pin"]').fill('684219'); p.locator('[name="admin-confirm"]').fill('684219'); p.locator('#admin-pin-submit').click(); expect(p.locator('#admin-calculation-host')).to_be_visible(); p.locator('[data-admin-worksheet="raphael5"]').click()
        expect(p.locator('#r5-house-source')).to_be_visible(); p.screenshot(path='/tmp/uploaded-bhav-tables.png')
        p.evaluate('document.getElementById("instant-prashna").value="0";calculateAll()')
        p.locator('#r5_small_1').fill('100:12:34'); self.assertEqual(p.locator('#r5-house-source').input_value(), 'manual'); self.assertEqual(p.locator('#r5_small_1').input_value(), '100:12:34')
        p.evaluate('calculateAll()'); self.assertEqual(p.locator('#r5_small_1').input_value(), '100:12:34')
        saved = p.evaluate('getChartData()'); self.assertEqual(saved['fields']['r5-house-source']['value'], 'manual')
        legacy = json.loads(json.dumps(saved)); del legacy['fields']['r5-house-source']
        p.evaluate('chart=>{document.getElementById("r5-house-source").value="automatic";restoreChartData(chart)}', legacy)
        self.assertEqual(p.locator('#r5-house-source').input_value(), 'manual'); self.assertEqual(p.locator('#r5_small_1').input_value(), '100:12:34')
        p.evaluate('document.getElementById("r5-house-source").value="automatic";document.getElementById("chart-kind").value="horary";document.getElementById("horary-number").value="123";calculateAll()')
        p.wait_for_timeout(250); result = p.evaluate('({native:currentKPModel.houses.map(h=>h.longitude),horary:KPHorary.getData().cusps.map(c=>c*3600),source:KPBhavSadhan.getData()})'); self.assertIsNone(result['source'])
        for a, b in zip(result['native'], result['horary']): self.assertAlmostEqual(a, b)
        p.evaluate('KPPreferences.save({...KPPreferences.get(),language:"marathi"})'); expect(p.locator('#r5-house-source option').first).to_have_text('अपलोड केलेल्या सारण्या · स्वयंचलित')

    def test_offline_embedded_tables_and_saved_automatic_source(self):
        p = self.page
        # The managed Chromium policy blocks file://. Start with a clean HTTP
        # origin, then disconnect networking before loading the standalone HTML.
        p.goto(self.url.rsplit('/',1)[0]+'/offline-check')
        self.context.set_offline(True)
        p.set_content((ROOT / 'index.html').read_text(), wait_until='load', timeout=60000)
        self.verify(self.sample())
        saved = p.evaluate('getChartData()'); self.assertEqual(saved['fields']['r5-house-source']['value'], 'automatic')
        original = self.sample()['cusps']
        p.evaluate('chart=>{document.getElementById("r5-house-source").value="computed";restoreChartData(chart)}', saved)
        self.verify(self.sample()); self.assertEqual(self.sample()['cusps'], original)


class HousePrivateTests(unittest.TestCase):
    setUpClass = classmethod(protected.ProtectedServerTests.setUpClass.__func__)
    tearDownClass = classmethod(protected.ProtectedServerTests.tearDownClass.__func__)
    setUp = protected.ProtectedServerTests.setUp
    tearDown = protected.ProtectedServerTests.tearDown
    private = protected.ProtectedServerTests.private
    post = protected.ProtectedServerTests.post

    def test_private_worker_embeds_tables_and_hides_house_controls(self):
        result = self.private('({data:KPBhavSadhan.getData(),cusps:currentKPModel.houses.map(h=>h.longitude),ready:currentKPModel.ready})')
        self.assertTrue(result['ready']); d = result['data']; self.assertEqual(d['source'], 'uploaded')
        self.assertEqual(result['cusps'], [math.floor(x*3600+.5) % 1296000 for x in reference(d['latitude'], d['siderealSeconds'], d['ayanamsha'], columns=d.get('tableColumns','numeric'))])
        self.assertEqual(self.page.evaluate('typeof KPBhavSadhan'), 'undefined')
        self.assertEqual(self.page.locator('#r5-house-source,#kp-uploaded-house-data').count(), 0)
        expect(self.page.locator('#quick-admin-calculations')).to_be_hidden()
        chart = self.page.request.get(self.url+'/export').json()
        self.assertNotIn('r5-house-source', chart['fields'])
        chart['fields']['instant-prashna']['value'] = '0'
        chart['fields']['dob']['value'] = '1986-07-15'
        chart['fields']['birthTime']['value'] = '13:11:00'
        chart['fields']['lat']['value'] = '18:48:00'
        chart['fields']['lon']['value'] = '74:13:00'
        self.assertEqual(self.post('/import', {'chart':chart}).status, 200)
        imported = self.private('({data:KPBhavSadhan.getData(),cusps:currentKPModel.houses.map(h=>h.longitude),ready:currentKPModel.ready,source:document.getElementById("r5-house-source").value})')
        self.assertTrue(imported['ready']); self.assertEqual(imported['source'], 'automatic')
        d = imported['data']; self.assertEqual(d['source'], 'uploaded')
        self.assertEqual(imported['cusps'], [math.floor(x*3600+.5) % 1296000 for x in reference(d['latitude'], d['siderealSeconds'], d['ayanamsha'], columns=d.get('tableColumns','numeric'))])
