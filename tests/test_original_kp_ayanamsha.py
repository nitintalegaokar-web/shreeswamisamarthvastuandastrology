"""Independent regression references for the user's supplied KP Tables IV-A/B."""
import calendar,json,re,subprocess,unittest
from pathlib import Path
import test_personal_predictions as personal
ROOT=Path(__file__).resolve().parents[1]

class OriginalKPTableTests(unittest.TestCase):
 def test_all_supplied_annual_and_daily_cells_are_exact(self):
  annual={};daily={}
  for line in (ROOT/'vendor/ephemeris/source/Original-KP-Tables-IV-A-IV-B.txt').read_text().splitlines():
   c=line.split('\t')
   for i in range(0,min(8,len(c)),2):
    if re.fullmatch(r'\d{4}',c[i].strip()):
     d,m,s=map(int,c[i+1].split(':'));annual[int(c[i])]=3600*d+60*m+s
   if len(c)>=21 and re.fullmatch(r'\d{1,2}',c[8].strip()):daily[int(c[8])]=[int(v.split(':')[-1]) for v in c[9:21]]
  runner="""const fs=require('fs'),vm=require('vm');const table=JSON.parse(fs.readFileSync('vendor/ephemeris/original-kp-tables.json','utf8'));const context={Date,Map,Number,String,JSON,Error,window:{},document:{getElementById:id=>id==='kp-annual-ayanamsha-data'?{textContent:JSON.stringify(table)}:null,addEventListener(){}}};vm.runInNewContext(fs.readFileSync('vendor/ephemeris/original-kp-ayanamsha.js','utf8'),context);const api=context.window.KPAnnualAyanamsha,answers=JSON.parse(fs.readFileSync(0,'utf8')).map(date=>api.details(date));process.stdout.write(JSON.stringify(answers));"""
  dates=[];expected=[]
  for year,base in sorted(annual.items()):
   for month in range(1,13):
    for day in range(1,calendar.monthrange(year,month)[1]+1):
     dates.append(f'{year:04}-{month:02}-{day:02}T00:00:00Z');expected.append(base+daily[day][month-1])
  result=subprocess.run(['node','-e',runner],cwd=ROOT,input=json.dumps(dates),text=True,capture_output=True,check=True)
  answers=json.loads(result.stdout)
  self.assertEqual(len(answers),len(expected))
  for date,answer,total in zip(dates,answers,expected):self.assertEqual(answer['total'],total,date)
  self.assertEqual(len(annual),243);self.assertEqual(len(daily),31)

class OriginalKPBrowserTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_references_strict_source_and_saved_chart_migration(self):
  p=self.page
  p.wait_for_function('window.KPCalculationSources')
  for date,expected in [('1931-10-10','22:48:18'),('1949-04-08','23:02:53'),('1950-12-20','23:04:18'),('2026-10-12','24:07:29')]:
   result=p.evaluate("date=>{document.getElementById('dob').value=date;calculateAll();return {field:document.getElementById('ayanValue').value,api:KPAnnualAyanamsha.format(KPEphemeris.ayanamsha(date+'T12:00:00Z')*3600),native:currentKPModel.ready};}",date)
   self.assertEqual(result['field'],expected,date);self.assertEqual(result['api'],expected,date);self.assertTrue(result['native'])
  saved=p.evaluate('getChartData()');saved['calculationSources']['ayanamshaSource']='swiss-kp';saved['fields']['kp-ayanamsha-source']['value']='manual'
  saved['fields']['dayAyan']['value']='01:00:00';saved['fields']['daySum']['value']='00:00:00';saved['fields']['ayanValue']['value']='01:00:00'
  p.evaluate('data=>restoreChartData(data)',saved)
  p.wait_for_function("document.getElementById('ayanValue').value==='24:07:29'")
  self.assertEqual(p.evaluate('KPEphemerisSources.sources'),['uploaded-kp']);self.assertEqual(p.evaluate('KPCalculationSources.get().ayanamshaSource'),'uploaded-kp')
  self.assertEqual(p.locator('#setting-ayanamshaCalculation option').count(),1)
  self.assertEqual(p.evaluate('typeof KPSwissKrishnamurti'),'undefined')
  self.assertTrue(p.locator('#dayAyan').evaluate('(e)=>e.readOnly'))
  p.evaluate('calculateAll()');self.assertEqual(p.locator('#ayanValue').input_value(),'24:07:29')
