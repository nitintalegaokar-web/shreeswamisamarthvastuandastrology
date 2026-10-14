"""User-supplied prediction/reference rules; original astrology remains immutable."""
import unittest,json,hashlib
from pathlib import Path
import fitz
import test_personal_predictions as personal
ROOT=Path(__file__).resolve().parents[1]
class DocumentSourceTests(unittest.TestCase):
 def test_reference_sources_and_249_numbers(self):
  d=json.loads((ROOT/'vendor/resources/additional-documents.json').read_text())
  self.assertEqual([int(r[0]) for r in d['numbers']],list(range(1,250)))
  for s in d['sources']:self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
  d=json.loads((ROOT/'vendor/resources/kaal-topics.json').read_text());self.assertEqual(d['topicCount'],len(d['topics']));self.assertGreater(d['topicCount'],20)
class DocumentBrowserTests(unittest.TestCase):
 setUpClass=classmethod(personal.PersonalPredictionTests.setUpClass.__func__)
 tearDownClass=classmethod(personal.PersonalPredictionTests.tearDownClass.__func__)
 setUp=personal.PersonalPredictionTests.setUp
 tearDown=personal.PersonalPredictionTests.tearDown
 def test_gemstones_horary_single_page_and_resources(self):
  p=self.page;p.wait_for_function('window.KPDocumentReferences&&document.getElementById("hq-panel")')
  before=p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})')
  cases=p.evaluate('''()=>{const m=structuredClone(currentKPModel);m.houses.find(h=>h.id===11).sl='Me';m.planets.find(p=>p.id==='Me').stl='Ju';m.fourfold.planets.forEach(p=>['A','B','C','D'].forEach(f=>p[f]=[]));m.fourfold.planets.find(p=>p.id==='Ju').A=[2];m.fourfold.planets.find(p=>p.id==='Su').A=[1,2,11];const yes=KPGemstoneDocument.evaluate(m,{stones:{Ju:'Yellow sapphire'}});m.fourfold.planets.find(p=>p.id==='Ju').A=[6];const no=KPGemstoneDocument.evaluate(m,{});return {yes:yes.results.filter(r=>r.qualifies),no:no.results.filter(r=>r.qualifies)};}''')
  self.assertEqual([r['id'] for r in cases['yes']],['Ju']);self.assertEqual(cases['yes'][0]['stone'],'Yellow sapphire');self.assertEqual(cases['no'],[])
  actual=p.evaluate('KPGemstones.getData()');self.assertTrue(actual['documentRule']);self.assertIn('XI CSL',actual['proof'])
  p.locator('#quick-event-promise').click();p.locator('#hq-opinion').fill('Reviewed with the client.');p.locator('#hq-question').fill('Will this event occur?')
  for method in ['fourfold','sixfold']:
   p.locator('#hq-method').select_option(method);d=p.evaluate('KPHoraryResults.getData()');self.assertTrue(d['ready']);self.assertEqual(d['method'],method)
   m=p.evaluate('currentKPModel')
   for row in d['levels']:
    source=next(r for r in m[method]['houses'] if r['id']==row['id'])
    for field in d['fields']:self.assertEqual(row[field],source[field])
   with p.expect_popup() as opened:p.locator('#hq-preview').click()
   preview=opened.value;preview.wait_for_function('document.querySelector(".sheet")?.dataset.fitted')
   pdf=fitz.open(stream=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True),filetype='pdf');self.assertEqual(len(pdf),1);text=pdf[0].get_text();self.assertIn('Reviewed with the client.',text);self.assertIn('Combined significators',text);self.assertIn('Joint period',text);pdf.close();preview.close()
  self.assertEqual(p.locator('#report-horary-sheet').count(),1)
  self.assertEqual(p.evaluate('KPDocumentReferences.numbers.length'),249)
  topics=p.locator('#resource-topic option').all_text_contents();self.assertTrue(any('काल ·' in t or 'Kala ·' in t for t in topics));self.assertTrue(any('226–249' in t for t in topics))
  p.evaluate("document.getElementById('resource-topic').value=[...document.getElementById('resource-topic').options].find(o=>o.textContent.includes('226–249')).value;document.getElementById('resource-topic').dispatchEvent(new Event('change'))")
  self.assertIn('249 | Pisces',p.locator('#resource-notes').input_value())
  self.assertEqual(p.evaluate('JSON.stringify({model:currentKPModel,periods:mdDashaPeriods})'),before)

  p.locator('nav [data-tab="resources"]').click();p.locator('#resource-edit-note').click();p.locator('#resource-notes').fill('My saved reference note');p.locator('#resource-save').click()
  p.reload();p.wait_for_function('window.KPDocumentReferences&&document.getElementById("hq-panel")')
  self.assertEqual(p.evaluate("JSON.parse(localStorage.getItem('kpResourcesV1'))['KP Numbers · 226–249 · Sub-lord reference']"),'My saved reference note')
  # Run the embedded HTML with networking disabled. This cloud browser blocks file: URLs.
  self.context.set_offline(True);p.goto('about:blank');p.set_content((ROOT/'index.html').read_text(),wait_until='domcontentloaded',timeout=60000);p.wait_for_function('window.KPDocumentReferences&&document.getElementById("hq-panel")',timeout=60000)
  self.assertTrue(p.evaluate('currentKPModel.ready'));self.assertTrue(p.evaluate('KPHoraryResults.getData().ready'));self.assertEqual(p.evaluate('KPDocumentReferences.numbers.length'),249)
