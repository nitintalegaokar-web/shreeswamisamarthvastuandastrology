"""Functional checks for the self-contained automatic version of the uploaded HTML."""
import ast
import functools
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
# Independent Swiss Ephemeris fixtures, already documented in the repository.
fixtures={}
for node in ast.parse((ROOT/'tests/test_calculator.py').read_text()).body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in ('EPHEMERIS_REFERENCE','PLACIDUS_REFERENCE'):
                fixtures[target.id]=ast.literal_eval(node.value)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

class UploadedAutomaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/automatic/index.html'
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.p.stop();cls.server.shutdown();cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000},timezone_id='America/Los_Angeles')
        self.page=self.context.new_page();self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto(self.url);self.page.wait_for_timeout(1600)
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def set_birth(self,**values):
        self.page.evaluate("values=>{for(const [id,value] of Object.entries(values))document.getElementById(id).value=value;calculateAll();}",values)
    def compare(self):
        result=self.page.evaluate("""()=>{const moment=KPAutoCalculator.getData();if(!moment)throw Error(document.getElementById('auto-calculation-status').textContent);const utc=new Date(moment.utc),positions=KPEphemeris.positions(utc),cusps=KPTransitHouses.calculate(utc,moment.latitude,moment.longitude).cusps,m=currentKPModel;return {ready:m.ready,houses:m.houses.map(h=>h.longitude/3600),expectedCusps:cusps,worksheet:[10,11,12,1,2,3].map(h=>({house:h,small:document.getElementById('r5_small_'+h).value,large:document.getElementById('r5_large_'+h).value,farak1:document.getElementById('r5_calc_diff1_'+h).value,farak2:document.getElementById('r5_calc_diff2_'+h).value,ishta:Number(document.getElementById('r5_calc_ishta_'+h).value),ishtaDms:document.getElementById('r5_ishta_'+h).value,smallPlus:document.getElementById('r5_smallplus_'+h).value,ayan:document.getElementById('r5_geoayan_'+h).value,nirayan:document.getElementById('r5_nirayan_'+h).value})),planets:m.planets.map(p=>[p.id,p.longitude/3600]),positions,nodes:m.planets.filter(p=>['Ra','Ke'].includes(p.id)).map(p=>p.longitude),first:document.getElementById('p6_date_1').value,second:document.getElementById('p6_date_2').value,moment};}""")
        self.assertTrue(result['ready']);self.assertEqual(len(result['houses']),12);self.assertEqual(len(result['planets']),9)
        def seconds(text):
            parts=[int(x) for x in text.split(':')];return parts[0]*3600+parts[1]*60+parts[2]
        for row in result['worksheet']:
            first=seconds(row['farak1']);second=seconds(row['farak2']);difference=seconds(row['large'])-seconds(row['small'])
            minutes=(second*difference+first*30)//(first*60)
            self.assertEqual(row['ishta'],minutes)
            self.assertEqual(seconds(row['ishtaDms']),minutes*60)
            self.assertEqual(seconds(row['smallPlus']),seconds(row['small'])+minutes*60)
            expected=(seconds(row['smallPlus'])-seconds(row['ayan']))%1296000
            self.assertEqual(seconds(row['nirayan']),expected)
            self.assertAlmostEqual(result['houses'][row['house']-1]*3600,expected,places=5)
        for i in range(6):self.assertAlmostEqual((result['houses'][i+6]-result['houses'][i])%360,180,places=8)
        for planet,actual in result['planets']:self.assertLessEqual(abs((actual-result['positions'][planet]+180)%360-180)*3600,.501)
        self.assertEqual((result['nodes'][1]-result['nodes'][0])%1296000,648000)
        return result
    def test_rounding_boundaries_and_midnight_carry(self):
        result=self.page.evaluate("""()=>({
            cutoff:[7199,7200].map(large=>KPAutoHouses.roundedRow(0,large,240,1,0).ishtaMinutes),
            degree:[7199,7200].map(large=>KPAutoHouses.roundedRow(0,large,240,119,0).ishtaMinutes),
            seconds:[.49,.5,239.49,239.5].map(t=>KPAutoHouses.roundedRow(0,14400,240,t,0).farak2),
            wrap:KPAutoHouses.roundedRow(1295970,1296030,240,120,0),
            longitude:(((-Astronomy.SiderealTime(new Date('2000-01-01T12:00:00Z'))*15-.4/240+180)%360+360)%360)-180
        })""")
        self.assertEqual(result['cutoff'],[0,1]);self.assertEqual(result['degree'],[59,60]);self.assertEqual(result['seconds'],[0,1,239,240]);self.assertEqual(result['wrap']['nirayanSeconds'],30)
        self.set_birth(dob='2000-01-01',birthTime='12:00:00',lat='0',lon=str(result['longitude']),**{'birth-utc-offset':'0'})
        self.compare();self.assertEqual(self.page.locator('#birthPlaceSiderealTime').input_value(),'00:00:00');self.assertEqual(self.page.locator('#stDiff2Seconds').input_value(),'240')
        self.assertEqual(self.page.locator('#stDiffSeconds').input_value(),'240')
        self.assertNotIn('.',self.page.locator('#r5_calc_ishta_1').input_value())

    def test_initial_chart_is_complete_without_manual_worksheets(self):
        self.compare();expect(self.page.locator('#auto-calculation-status')).to_contain_text('Automatic')
        self.assertTrue(self.page.locator('#mdBirthDasha').input_value())
        self.assertEqual(self.page.locator('#kp-basic-house tbody tr').count(),12)
        self.assertEqual(self.page.locator('#kp-basic-planet tbody tr').count(),9)
    def test_independent_planets_and_cusps_match_reference(self):
        for f in fixtures['EPHEMERIS_REFERENCE']:
            result=self.page.evaluate("f=>({tropical:Object.fromEntries(Object.keys(f.tropical).map(id=>[id,KPEphemeris.tropical(f.date,id)]))})",f)
            for planet,expected in f['tropical'].items():self.assertLess(abs((result['tropical'][planet]-expected+180)%360-180),.03)
        # 0.001 degree (3.6 arcsec) is the underlying astronomy engine's
        # established house-reference tolerance, separate from UI rounding.
        for f in fixtures['PLACIDUS_REFERENCE']:
            d=f['date'];self.set_birth(dob=d[:10],birthTime=d[11:19],**{'birth-utc-offset':'0','lat':str(f['latitude']),'lon':str(f['longitude'])})
            r=self.compare();ayan=r['moment']['ayanamsha']
            for cusp,expected in zip(r['expectedCusps'],f['cuspsTropical']):self.assertLess(abs((cusp+ayan-expected+180)%360-180),.001,(f['date'],f['latitude'],f['longitude'],r['expectedCusps'].index(cusp)+1,cusp+ayan,expected))
    def test_timezone_dst_midnight_and_0530_references(self):
        cases=[('2000-01-01','00:00:00','5.5','0','1999-12-31T18:30:00.000Z','1999-12-31'),('2026-10-06','05:29:59','5.75','0','2026-10-05T23:44:59.000Z','2026-10-05'),('2026-10-06','05:30:00','5.5','0','2026-10-06T00:00:00.000Z','2026-10-06'),('2026-10-06','23:45:00','-5','60','2026-10-07T03:45:00.000Z','2026-10-06')]
        for date,time,offset,dst,utc,reference in cases:
            self.set_birth(dob=date,birthTime=time,**{'birth-utc-offset':offset,'birth-dst-minutes':dst})
            r=self.compare();self.assertEqual(r['moment']['utc'],utc);self.assertEqual(r['first'],reference)
    def test_edits_survive_old_timers_and_recalculate_all_dependents(self):
        self.page.locator('.app-sidebar [data-tab="basic"]').click();self.page.locator('#dob').fill('1986-07-15');self.page.locator('#birthTime').fill('15:45:00');self.page.wait_for_timeout(1800)
        r=self.compare();self.assertEqual(r['moment']['localDate'],'1986-07-15');before=r['houses'][0]
        self.page.locator('#birthTime').fill('18:45:00');self.page.wait_for_timeout(1800);r=self.compare();self.assertNotEqual(before,r['houses'][0])
        self.page.locator('.app-sidebar [data-tab="south9"]').click();expect(self.page.locator('#kundali')).to_be_visible()
    def test_invalid_polar_missing_coordinates_clear_previous_chart(self):
        for value in ['85','', '18:90:00']:
            self.set_birth(lat=value)
            expect(self.page.locator('#auto-calculation-status')).to_have_attribute('data-state','error')
            self.assertFalse(self.page.evaluate('currentKPModel.ready'))
            self.assertEqual(self.page.locator('#p6_final_1').input_value(),'');self.assertEqual(self.page.locator('#r5_nirayan_1').input_value(),'')
        self.set_birth(lat='18:30:00');self.compare()
    def test_persistence_recomputes_calculated_fields_and_report_metadata(self):
        self.set_birth(dob='2026-10-06',birthTime='23:45:00',**{'birth-utc-offset':'-5','birth-dst-minutes':'60','lat':'-33:52:08','lon':'151:12:33'})
        before=self.compare();chart=self.page.evaluate('getChartData()')
        chart['fields']['r5_nirayan_1']={'value':'0:00:00'}
        self.set_birth(dob='2000-01-01',**{'birth-utc-offset':'5.5','birth-dst-minutes':'0'})
        self.page.evaluate('data=>restoreChartData(data)',chart);after=self.compare();self.assertEqual(before['houses'],after['houses']);self.assertEqual(after['moment']['offset'],-4)
        report=self.page.locator('#printReport [data-report-section="single-page"]')
        expect(report).to_contain_text('Computed Placidus');expect(report).to_contain_text('Mean lunar node');expect(report).to_contain_text('DST / war time applied')
    def test_standalone_html_needs_no_external_assets(self):
        html=(ROOT/'automatic/index.html').read_text();self.assertNotIn('<script src=',html)
        self.page.route('https://**/*',lambda route:route.abort())
        self.page.reload();self.page.wait_for_timeout(1500);self.compare()

if __name__=='__main__':unittest.main()
