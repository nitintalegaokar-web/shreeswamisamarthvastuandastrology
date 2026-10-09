"""Functional regression checks for recovered references and new analysis views."""
import functools
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import Error as PlaywrightError, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROMIUM = os.environ.get('CALCULATOR_CHROMIUM') or shutil.which('chromium')
FIXTURE_MODEL = """() => {
  const codes=['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'];
  const positions=Object.fromEntries(codes.map((id,i)=>[id,(5+i*30)*3600]));
  positions.Ke=(positions.Ra+180*3600)%(360*3600);
  const model=KPDisplay.build(Array.from({length:12},(_,i)=>i*30*3600),positions);
  const sets={Su:[2,6,10,11],Mo:[2,5,11],Ma:[2,6,10,11],Me:[2],Ju:[5,11],Ve:[7],Sa:[8],Ra:[12],Ke:[3]};
  for(const method of ['fourfold','sixfold'])for(const row of model[method].planets){
    row.A=sets[row.id];for(const key of ['B','C','D','E','F'])row[key]=[];
  }
  return model;
}"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def close_preview(preview):
    """Assert the Close control closes its window, including early click completion."""
    with preview.expect_event('close'):
        try:
            preview.get_by_role('button',name='Close preview',exact=True).click(no_wait_after=True)
        except PlaywrightError:
            if not preview.is_closed():
                raise


class FeatureUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=CHROMIUM, headless=True, args=['--no-sandbox'])
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/index.html'

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, timeout=60000)
        self.page.wait_for_function('window.KPGemstones && window.KPNadiAstrology && currentKPModel?.ready && document.getElementById("gem-results")', timeout=60000)
        self.page.wait_for_timeout(450)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def test_transit_current_periods_use_exact_native_boundaries_and_refresh_lords(self):
        self.page.locator('nav [data-tab="transit"]').click()
        expect(self.page.locator('#tr-period')).to_have_value('PD')
        expect(self.page.locator('#tr-start')).not_to_be_visible()
        expect(self.page.locator('#tr-end')).not_to_be_visible()
        expect(self.page.locator('#tr-reference')).to_have_count(0)
        expect(self.page.locator('[data-current-period]')).to_have_count(3)
        result = self.page.evaluate("""() => {
          const now=KPTransit.currentPeriods(),home=KPHomeDasha.getData();
          const nativeCivil=Date.parse(now.instant)+home.timeZoneHours*3600000;
          let rows=home.levels[0].rows;const checks=[];
          for(const level of ['MD','AD','PD']){
            const expected=rows.find(p=>p.startMs<=nativeCivil&&nativeCivil<p.endMs),p=now.periods[level];
            checks.push(p.startMs===expected.startMs&&p.endMs===expected.endMs&&Date.parse(p.startUTC)===p.startMs-home.timeZoneHours*3600000&&Date.parse(p.endUTC)===p.endMs-home.timeZoneHours*3600000);
            rows=KPHomeDasha.subdivide(expected);
          }
          const next=KPTransit.currentPeriods(new Date(now.periods.PD.endUTC));
          let outside=false;try{KPTransit.currentPeriods(new Date('2300-01-01T00:00:00Z'));}catch(_){outside=true;}
          return {checks,outside,nextStart:next.periods.PD.startUTC,previousEnd:now.periods.PD.endUTC};
        }""")
        self.assertTrue(all(result['checks']))
        self.assertTrue(result['outside'])
        self.assertEqual(result['nextStart'], result['previousEnd'])
        self.page.locator('#tr-mode').select_option('dasha')
        for level in ['MD', 'AD', 'PD']:
            self.page.locator('#tr-period').select_option(level)
            data = self.page.evaluate("""() => {
              const p=KPTransit.currentPeriods(),r=KPTransit.currentRange(p),summary=document.getElementById('tr-period-summary');
              return {start:r.start.toISOString(),end:r.end.toISOString(),summaryStart:summary.dataset.start,summaryEnd:summary.dataset.end,lords:KPTransit.autoDasha(p),selected:['tr-md','tr-ad','tr-pd'].map(id=>document.getElementById(id).value)};
            }""")
            self.assertEqual(data['start'],data['summaryStart'])
            self.assertEqual(data['end'],data['summaryEnd'])
            self.assertEqual(data['selected'],[data['lords'][level] for level in ['MD','AD','PD']])
        self.page.locator('#tr-timezone').select_option('0')
        utc = self.page.evaluate('KPTransit.currentRange().start.toISOString()')
        self.assertEqual(utc,data['start'])
        expect(self.page.locator('#tr-period-summary')).to_contain_text('UTC')

    def test_transit_search_uses_current_pd_and_accepts_complete_twenty_year_md(self):
        self.page.locator('nav [data-tab="transit"]').click()
        self.page.locator('#tr-mode').select_option('sun')
        self.page.locator('#tr-run').click()
        expect(self.page.locator('#tr-status')).to_contain_text('matching transit interval',timeout=60000)
        result = self.page.evaluate("""async () => {
          const range=KPTransit.currentRange(),found=KPTransit.getResults();
          const start=new Date('2000-01-01T12:34:56Z'),end=new Date('2020-01-01T12:34:56Z');
          const long=await KPTransit.scan({start,end,tracks:[{id:'whole',planet:'Su',label:'whole range',levels:[],test:()=>true}]});
          return {within:found.every(row=>Date.parse(row.start)>=range.start.getTime()&&Date.parse(row.end)<=range.end.getTime()),long};
        }""")
        self.assertTrue(result['within'])
        self.assertEqual(len(result['long']),1)
        self.assertEqual(result['long'][0]['start'],'2000-01-01T12:34:56.000Z')
        self.assertEqual(result['long'][0]['end'],'2020-01-01T12:34:56.000Z')
        self.page.locator('#tr-period').select_option('AD')
        self.assertEqual(self.page.evaluate('KPTransit.getResults().length'),0)

    def test_removed_prediction_controls_capitalization_and_preview_toolbar(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        expect(self.page.locator('#pred-export')).to_have_count(0)
        self.page.locator('#pred-tab-gemstones').click()
        expect(self.page.locator('#pred-library-csv')).to_have_count(0)
        with self.page.expect_popup() as opened:
            self.page.locator('#pred-library-print').click()
        preview=opened.value
        self.assertNotIn('Choose Save as PDF in the print dialog.',preview.locator('body').inner_text())
        close_preview(preview)
        self.page.locator('nav [data-tab="matchmaking"]').click()
        self.page.locator('#mm-boy-name').fill('nitin talegaokar')
        expect(self.page.locator('#mm-boy-name')).to_have_value('Nitin Talegaokar')
        self.page.locator('#mm-boy-place').fill("new delhi")
        expect(self.page.locator('#mm-boy-place')).to_have_value('New Delhi')

    def test_gemstone_priorities_preserve_ties_and_highlight_recommendations(self):
        result=self.page.evaluate("""() => {
          const model=("""+FIXTURE_MODEL+""")(),base={excluded:'',method:'fourfold',roles:['planet'],stones:{Su:'Ruby',Ma:'Coral',Sa:'Sapphire'}};
          const vedic=KPGemstones.evaluate(model,{...base,mode:'vedic'}),kp=KPGemstones.evaluate(model,{...base,mode:'kp',required:'2,6,10,11'});
          return {vedic:vedic.results.filter(r=>r.qualifies).map(r=>[r.id,r.priority]),kp:kp.results.filter(r=>r.qualifies).map(r=>[r.id,r.priority])};
        }""")
        self.assertEqual(result['vedic'],[['Ma',1],['Su',2],['Sa',3]])
        self.assertEqual(result['kp'],[['Su',1],['Ma',1]])
        self.page.locator('nav [data-tab="gemstones"]').click()
        self.page.locator('#gem-mode').select_option('vedic')
        row=self.page.locator('#gem-results tr[data-gem-priority="1"]')
        expect(row).to_have_count(1)
        expect(row.locator('.gem-priority-badge')).to_have_text('1')
        self.assertNotEqual(row.evaluate('(e)=>getComputedStyle(e).backgroundColor'),'rgba(0, 0, 0, 0)')

    def test_event_timing_ranges_calendar_clamps_and_native_dba_coverage(self):
        result=self.page.evaluate("""async()=>{
          const model=("""+FIXTURE_MODEL+""")();for(const method of ['fourfold','sixfold'])for(const r of model[method].planets){r.A=[2,7,11];for(const f of ['B','C','D','E','F'])r[f]=[];}
          const data=KPEventPromise.analyze(model,{customHouses:'2,7,11',cusp:7}),nativeBefore=JSON.stringify({d:document.getElementById('dob').value,p:currentKPModel.planets,h:currentKPModel.houses});
          const base={startDate:'2028-01-31',startTime:'12:34:56',offset:-4,latitude:20,longitude:74,place:'Test place',required:'2,7,11',useRuling:false};
          const runs=[];for(const range of ['day','month','year','13years']){const r=await KPEventOutcome.find({...base,range},data,model);runs.push({range,trigger:r.trigger,count:r.rows.length,start:r.start,end:r.end,first:r.rows[0]?.start,last:r.rows.at(-1)?.end,allCovered:r.rows.every(row=>[2,7,11].every(h=>row.lords.some(p=>p.houses.includes(h)))&&row.lords.every(p=>p.houses.some(h=>[2,7,11].includes(h)))),continuous:r.rows.every((row,i)=>!i||r.rows[i-1].end===row.start)});}
          const leap=KPEventOutcome.calendarRange({...base,startDate:'2028-02-29',range:'year'}).end.toISOString();
          const invalid=[{startDate:'2028-02-30'},{offset:NaN},{required:'2,7,111'},{range:'bad'},{latitude:70,range:'day'}].map(change=>{try{KPEventOutcome.validate({...base,range:'day',...change});return false;}catch(_){return true;}});
          return {runs,leap,invalid,unchanged:nativeBefore===JSON.stringify({d:document.getElementById('dob').value,p:currentKPModel.planets,h:currentKPModel.houses})};
        }""")
        self.assertEqual([r['trigger'] for r in result['runs']],['As','Mo','Su','Ju'])
        for row in result['runs']:
            self.assertGreater(row['count'],0)
            self.assertEqual(row['first'],row['start'])
            self.assertEqual(row['last'],row['end'])
            self.assertTrue(row['allCovered'])
            self.assertTrue(row['continuous'])
        self.assertEqual(result['runs'][1]['end'],'2028-02-29T16:34:56.000Z')
        self.assertEqual(result['leap'],'2029-02-28T16:34:56.000Z')
        self.assertTrue(all(result['invalid']))
        self.assertTrue(result['unchanged'])

    def test_ascendant_transit_roots_geometry_and_half_open_intersections(self):
        result=self.page.evaluate("""async()=>{
          const start=new Date('2028-01-31T00:00:00Z'),end=new Date('2028-02-01T00:00:00Z'),location={latitude:20,longitude:74};
          const lon=KPTransitHouses.ascendant(start,20,74),geometry=KPTransitHouses.calculate(start,20,74).cusps[0];
          const first=KPDisplay.longitudeDetails(lon*3600),test=p=>p.stl===first.stl&&p.sl===first.sl;
          const rows=await KPTransit.scan({start,end,location,tracks:[{id:'asc',planet:'As',label:'Asc',levels:['star','sub'],test}]});
          const at=t=>KPDisplay.longitudeDetails(KPTransitHouses.ascendant(new Date(t),20,74)*3600);
          const boundaries=rows.every(r=>(r.startClipped||!test(at(Date.parse(r.start)-2000))&&test(at(Date.parse(r.start)+2000)))&&(r.endClipped||test(at(Date.parse(r.end)-2000))&&!test(at(Date.parse(r.end)+2000))));
          const cut=KPEventOutcome.intersect([{start:'2028-01-01T00:00:00Z',end:'2028-01-01T01:00:00Z',planet:'Su'}],[{start:'2028-01-01T01:00:00Z',end:'2028-01-01T02:00:00Z',lords:[]}]);
          const overlap=KPMatchmaking.jointPeriods([{start:'2028-01-01T00:00:00Z',end:'2028-01-01T02:00:00Z',lords:[{id:'Su'}]}],[{start:'2028-01-01T01:00:00Z',end:'2028-01-01T03:00:00Z',lords:[{id:'Mo'}]}]);
          const controller=new AbortController();controller.abort();let cancelled=false;try{await KPTransit.scan({start,end,location,signal:controller.signal,tracks:[{id:'x',planet:'As',test:()=>true}]});}catch(e){cancelled=e.message==='Search cancelled.';}
          return {lon,geometry,count:rows.length,boundaries,cut,overlap,cancelled};
        }""")
        self.assertAlmostEqual(result['lon'],result['geometry'],places=8)
        self.assertGreater(result['count'],0)
        self.assertTrue(result['boundaries'])
        self.assertEqual(result['cut'],[])
        self.assertEqual(result['overlap'][0]['start'],'2028-01-01T01:00:00.000Z')
        self.assertEqual(result['overlap'][0]['end'],'2028-01-01T02:00:00.000Z')
        self.assertTrue(result['cancelled'])

    def test_ruling_planets_accept_minutes_refresh_and_search_selected_event(self):
        self.page.locator('nav [data-tab="ruling-planets"]').click()
        before=self.page.evaluate("JSON.stringify({d:document.getElementById('dob').value,p:currentKPModel.planets,h:currentKPModel.houses})")
        self.page.locator('#rpw-date').fill('2028-01-31')
        self.page.locator('#rpw-time').fill('13:15')
        self.page.locator('#rpw-calculate').click()
        expect(self.page.locator('#rpw-table tbody tr')).to_have_count(4)
        data=self.page.evaluate('KPRulingWorkspace.getData()')
        self.assertEqual(data['utc'],'2028-01-31T07:45:00.000Z')
        self.page.locator('#rpw-time').fill('15:15')
        self.page.locator('#rpw-calculate').click()
        later=self.page.evaluate('KPRulingWorkspace.getData()')
        self.assertNotEqual(data['rows'][0]['longitude'],later['rows'][0]['longitude'])
        self.assertEqual(before,self.page.evaluate("JSON.stringify({d:document.getElementById('dob').value,p:currentKPModel.planets,h:currentKPModel.houses})"))
        self.page.locator('#rp-time-event').select_option('11')
        expect(self.page.locator('#rp-time-houses')).to_have_value('1,11')
        self.page.locator('#rp-time-find').click()
        expect(self.page.locator('#rp-time-panel')).not_to_have_attribute('aria-busy','true',timeout=60000)
        self.assertTrue(self.page.evaluate('KPEventOutcome.getRulingData().ready'))
        self.assertGreater(len(self.page.locator('#rp-time-results').inner_text()),30)

    def test_kp_matchmaking_scores_independent_timelines_and_joint_marriage_periods(self):
        self.page.locator('nav [data-tab="matchmaking"]').click()
        expect(self.page.get_by_text('Copy native birth details',exact=True)).to_have_count(0)
        expect(self.page.locator('.mm-birth-chart-details')).to_have_count(0)
        expect(self.page.locator('#mm-traditional-charts svg')).to_have_count(2)
        self.page.locator('[data-mm-method="kp"]').click()
        result=self.page.evaluate("""async()=>{
          const d=KPMatchmaking.getData(),native=JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,md:mdDashaPeriods});
          const shifted=KPMatchmaking.profile({...d.girl.record,time:'15:11'}),other=KPMatchmaking.kpCompatibility(d.boy,shifted,{boy:d.manglik.boy,girl:KPMatchmaking.manglik(shifted,d.settings)});
          const report=KPMatchmaking.snapshot(),timeline=KPMatchmaking.timeline(d.boy),periods=await KPMatchmaking.findMarriage({startDate:'2026-10-09',startTime:'00:00:00',offset:5.5,range:'13years',refine:false},d);
          return {kp:d.kp,other,timelineStart:timeline.levels[0].rows[0].start,rows:periods.rows,profileChanged:shifted.ascendant!==d.girl.ascendant,hasSvg:report.includes('<svg'),reportHasKP:report.includes('KP matchmaking'),unchanged:native===JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses,md:mdDashaPeriods})};
        }""")
        kp=result['kp']
        self.assertEqual(sum(c['weight'] for c in kp['categories']),100)
        self.assertEqual(len(kp['categories']),6)
        self.assertAlmostEqual(kp['total'],max(0,kp['base']-kp['mangalPenalty']),places=2)
        self.assertTrue(0<=kp['total']<=100)
        self.assertTrue(result['profileChanged'])
        self.assertGreater(len(result['rows']),0)
        for row in result['rows']:
            self.assertEqual(len(row['boy']),3)
            self.assertEqual(len(row['girl']),3)
            for side in ['boy','girl']:
                self.assertTrue(all(any(h in p['houses'] for h in [2,7,11]) for p in row[side]))
                self.assertTrue(all(any(h in p['houses'] for p in row[side]) for h in [2,7,11]))
        self.assertFalse(result['hasSvg'])
        self.assertTrue(result['reportHasKP'])
        self.assertTrue(result['unchanged'])

    def test_western_aspect_table_colours_marathi_and_chart_backup(self):
        self.page.locator('nav [data-tab="aspects"]').click()
        expect(self.page.locator('#am-mode')).to_contain_text('ग्रहांमधील दृष्टी संबंध')
        self.page.locator('#am-mode').select_option('cusp')
        expect(self.page.locator('#aspects .am-matrix caption')).to_have_text('ग्रहांपासून भावांवर दृष्टी संबंध')
        self.page.evaluate("""()=>{for(const [id,v] of [['am-header-colour','#112233'],['am-column-colour','#ddeeff']]){const e=document.getElementById(id);e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}));}}""")
        expect(self.page.locator('#aspects .am-matrix thead th').first).to_have_css('background-color','rgb(17, 34, 51)')
        expect(self.page.locator('#aspects .am-matrix tbody th').first).to_have_css('background-color','rgb(221, 238, 255)')
        chart=self.page.evaluate('getChartData()')
        self.assertEqual(chart['fields']['am-header-colour']['value'],'#112233')
        self.page.evaluate('(c)=>restoreChartData(c)',chart)
        expect(self.page.locator('#am-header-colour')).to_have_value('#112233')

    def test_nadi_selected_kundali_and_all_positions_fit_one_a4_page(self):
        before=self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})')
        self.page.locator('nav [data-tab="nadi-astrology"]').click()
        self.page.evaluate("""()=>{for(const [id,value] of [['na-source','moment'],['na-date','2000-01-01'],['na-time','12:10:00'],['na-latitude','51.5074'],['na-longitude','-0.1278'],['na-timezone','0']]){const n=document.getElementById(id);n.value=value;}KPNadiAstrology.calculate();}""")
        selected=self.page.evaluate('KPNadiAstrology.getData().model.planets.map(p=>({id:p.id,longitude:String(p.longitude)}))')
        for style in ['south','north']:
            self.page.evaluate('(s)=>KPChartStyle.setStyle(s)',style)
            with self.page.expect_popup() as opened:
                self.page.evaluate('KPReportPreview.open("nadi-astrology")')
            preview=opened.value
            expect(preview.locator('.na-report-kundali')).to_have_attribute('data-chart-style',style)
            expect(preview.locator('[data-nadi-cusp]')).to_have_count(12)
            expect(preview.locator('[data-nadi-chart-planet]')).to_have_count(9)
            expect(preview.locator('[data-nadi-report-cusp]')).to_have_count(12)
            expect(preview.locator('[data-nadi-report-planet]')).to_have_count(9)
            for planet in selected:
                expect(preview.locator('[data-nadi-chart-planet="'+planet['id']+'"]')).to_have_attribute('data-longitude',planet['longitude'])
            preview.get_by_role('button',name='Zoom +',exact=True).click()
            preview.emulate_media(media='print')
            preview.wait_for_timeout(150)
            output=Path('/tmp/kp-nadi-'+style+'.pdf')
            pdf=preview.pdf(path=str(output),format='A4',prefer_css_page_size=True,print_background=True)
            self.assertEqual(len(re.findall(rb'/Type\s*/Page\b',pdf)),1)
            bounds=preview.locator('.report-page').evaluate("""n=>{const p=n.getBoundingClientRect(),i=n.querySelector('.kp-a4-body').getBoundingClientRect(),c=n.querySelector('.na-report-kundali').getBoundingClientRect();return {complete:i.bottom<=p.bottom+1,chart:c.bottom<=p.bottom,scale:Number(n.dataset.a4Scale)};}""")
            self.assertTrue(bounds['complete'])
            self.assertTrue(bounds['chart'])
            self.assertGreater(bounds['scale'],0.7)
            preview.emulate_media(media='screen')
            close_preview(preview)
        self.assertEqual(before,self.page.evaluate('JSON.stringify({p:currentKPModel.planets,h:currentKPModel.houses})'))

    def test_notepad_formats_persist_and_removed_time_slice_stays_absent(self):
        self.page.evaluate("localStorage.setItem('kpRaphaelNotepadV1','Existing notes · जुनी नोंद')")
        self.page.locator('#quick-notepad').click()
        expect(self.page.locator('#notepad-text')).to_have_value('Existing notes · जुनी नोंद')
        self.page.locator('#notepad-font').select_option('mangal')
        self.page.locator('#notepad-size').fill('20')
        self.page.locator('#notepad-size').dispatch_event('change')
        self.page.locator('#notepad-larger').click()
        expect(self.page.locator('#notepad-text')).to_have_css('font-size','21px')
        self.page.evaluate("""()=>{const n=document.getElementById('notepad-colour');n.value='#553399';n.dispatchEvent(new Event('input',{bubbles:true}));}""")
        expect(self.page.locator('#notepad-text')).to_have_css('color','rgb(85, 51, 153)')
        self.page.locator('#notepad-text').fill('Updated notes · नवीन नोंद')
        self.page.locator('#notepad-close').click()
        self.page.reload(timeout=60000)
        self.page.wait_for_function('window.KPNotepad && document.getElementById("quick-notepad")')
        self.page.locator('#quick-notepad').click()
        expect(self.page.locator('#notepad-text')).to_have_value('Updated notes · नवीन नोंद')
        expect(self.page.locator('#notepad-font')).to_have_value('mangal')
        expect(self.page.locator('#notepad-text')).to_have_css('font-size','21px')
        expect(self.page.locator('#notepad-text')).to_have_css('color','rgb(85, 51, 153)')
        self.page.locator('#notepad-size').fill('100')
        self.page.locator('#notepad-size').dispatch_event('change')
        expect(self.page.locator('#notepad-size')).to_have_value('48')
        self.page.locator('#notepad-smaller').click()
        expect(self.page.locator('#notepad-text')).to_have_css('font-size','47px')
        self.page.locator('#notepad-close').click()
        self.page.locator('nav [data-tab="south9"]').click()
        expect(self.page.locator('#south9 button',has_text='Manual Edit')).to_have_count(0)
        expect(self.page.locator('#time-slices,.kundali-time-slices-link')).to_have_count(0)

    def test_notepad_preview_preserves_fonts_safe_text_zoom_and_complete_pdf(self):
        self.page.locator('#quick-notepad').click()
        self.page.locator('#notepad-font').select_option('serif')
        self.page.locator('#notepad-size').fill('18')
        self.page.locator('#notepad-size').dispatch_event('change')
        self.page.evaluate("""()=>{const n=document.getElementById('notepad-colour');n.value='#662244';n.dispatchEvent(new Event('change',{bubbles:true}));}""")
        notes='<img src=x onerror="window.noteInjection=true"> & literal notes\n'+'\n'.join('Note line '+str(i) for i in range(160))+'\nEND OF PERSONAL NOTES'
        self.page.locator('#notepad-text').fill(notes)
        with self.page.expect_popup() as opened:
            self.page.locator('#notepad-preview').click()
        preview=opened.value
        self.assertEqual(preview.locator('#notepad-preview-text').text_content(),notes)
        expect(preview.locator('#notepad-preview-text')).to_have_css('font-size','18px')
        expect(preview.locator('#notepad-preview-text')).to_have_css('color','rgb(102, 34, 68)')
        expect(preview.locator('#notepad-preview-text img')).to_have_count(0)
        self.assertFalse(preview.evaluate('Boolean(window.noteInjection)'))
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertEqual(preview.locator('.notepad-preview-page').evaluate('n=>n.style.zoom'),'1.1')
        preview.get_by_role('button',name='Zoom −',exact=True).click()
        self.assertEqual(preview.locator('.notepad-preview-page').evaluate('n=>n.style.zoom'),'1')
        preview.evaluate('window.print=()=>window.notePrintRequested=true')
        preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
        self.assertTrue(preview.evaluate('window.notePrintRequested'))
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        preview.emulate_media(media='print')
        expect(preview.locator('.notepad-preview-page')).to_have_css('zoom','1')
        pdf=preview.pdf(path='/tmp/kp-notepad-preview.pdf',format='A4',prefer_css_page_size=True,print_background=True)
        self.assertGreater(len(re.findall(rb'/Type\s*/Page\b',pdf)),1)
        if shutil.which('pdftotext'):
            import subprocess
            printed=subprocess.check_output(['pdftotext','/tmp/kp-notepad-preview.pdf','-']).decode()
            self.assertIn('Note line 0',printed)
            self.assertIn('END OF PERSONAL NOTES',printed)
        preview.emulate_media(media='screen')
        close_preview(preview)
        expect(self.page.locator('#kp-notepad')).to_be_visible()
        self.page.locator('#notepad-close').click()

    def test_resource_topics_notes_preview_text_file_and_deletion_persist(self):
        self.page.locator('nav [data-tab="resources"]').click()
        self.page.locator('#resource-new-topic').fill('My KP notes')
        self.page.locator('#resource-add').click()
        expect(self.page.locator('#resource-topic')).to_have_value('My KP notes')
        self.page.locator('#resource-notes').fill('मराठी संदर्भ\n<script>window.resourceInjection=true</script>')
        self.page.locator('#resource-save').click()
        expect(self.page.locator('#resource-notes')).to_have_attribute('readonly','')
        self.page.locator('#resource-edit-topic').click()
        self.page.locator('#resource-new-topic').fill('Updated KP notes')
        self.page.locator('#resource-add').click()
        expect(self.page.locator('#resource-topic')).to_have_value('Updated KP notes')
        with self.page.expect_popup() as opened:
            self.page.locator('#resource-preview').click()
        preview=opened.value
        expect(preview.locator('#notepad-preview-text')).to_contain_text('मराठी संदर्भ')
        expect(preview.locator('#notepad-preview-text')).to_contain_text('<script>window.resourceInjection=true</script>')
        self.assertFalse(preview.evaluate('Boolean(window.resourceInjection)'))
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertEqual(preview.locator('.notepad-preview-page').evaluate('n=>n.style.zoom'),'1.1')
        close_preview(preview)
        self.page.evaluate('window.showSaveFilePicker=undefined')
        with self.page.expect_download() as downloaded:
            self.page.locator('#resource-download').click()
        file=downloaded.value
        self.assertTrue(file.suggested_filename.endswith('.txt'))
        file.save_as('/tmp/kp-resource-notes.txt')
        content=Path('/tmp/kp-resource-notes.txt').read_text(encoding='utf-8-sig')
        self.assertIn('Topic / subtopic: Updated KP notes',content)
        self.assertIn('मराठी संदर्भ',content)
        self.page.reload(timeout=60000)
        self.page.wait_for_function('window.KPResources && document.getElementById("resource-topic")')
        self.page.locator('nav [data-tab="resources"]').click()
        self.page.locator('#resource-topic').select_option('Updated KP notes')
        expect(self.page.locator('#resource-notes')).to_have_value('मराठी संदर्भ\n<script>window.resourceInjection=true</script>')
        self.page.on('dialog',lambda d:d.accept())
        self.page.locator('#resource-delete-note').click()
        expect(self.page.locator('#resource-notes')).to_have_value('')
        self.page.locator('#resource-delete-topic').click()
        expect(self.page.locator('#resource-topic option',has_text='Updated KP notes')).to_have_count(0)
        self.page.locator('#resource-topic').select_option('KP Fundamentals')
        self.page.locator('#resource-delete-topic').click()
        self.page.reload(timeout=60000)
        self.page.wait_for_function('window.KPResources && document.getElementById("resource-topic")')
        expect(self.page.locator('#resource-topic option',has_text='KP Fundamentals')).to_have_count(0)
        expect(self.page.locator('#resource-topic option',has_text='Updated KP notes')).to_have_count(0)

    def test_dba_popup_cascades_exact_periods_boundary_selection_and_print_controls(self):
        self.page.locator('nav [data-tab="mdcalc"]').click()
        before=self.page.evaluate('JSON.stringify(KPHomeDasha.getData())')
        roots=self.page.evaluate('KPDbaPopup.data().roots')
        with self.page.expect_popup() as opened:
            self.page.locator('#dba-preview').click()
        preview=opened.value
        preview.wait_for_function('window.KPDBASelection')
        expect(preview.locator('.dba-card')).to_have_count(len(roots))
        preview.locator('#dba-md').select_option('1')
        preview.locator('#dba-ad').select_option('2')
        preview.locator('#dba-pd').select_option('4')
        chosen=preview.evaluate('KPDBASelection.getData()')
        self.assertEqual([p['startMs'] for p in chosen['periods']],[roots[1]['startMs'],roots[1]['children'][2]['startMs'],roots[1]['children'][2]['children'][4]['startMs']])
        preview.evaluate("""()=>{const end=KPDBASelection.getData().periods[2].endMs,t=new Date(Math.ceil(end/1000)*1000).toISOString();document.getElementById('dba-reference-date').value=t.slice(0,10);document.getElementById('dba-reference-time').value=t.slice(11,19);}""")
        preview.locator('#dba-find').click()
        self.assertEqual(preview.evaluate('KPDBASelection.getData().pd'),5)
        preview.locator('#dba-zoom-in').click()
        self.assertEqual(preview.locator('#dba-report').evaluate('n=>n.style.zoom'),'1.1')
        preview.locator('#dba-zoom-out').click()
        preview.evaluate('window.print=()=>window.dbaPrintRequested=true')
        preview.locator('#dba-print-selected').click()
        self.assertTrue(preview.evaluate('window.dbaPrintRequested'))
        preview.emulate_media(media='print')
        expect(preview.locator('#dba-grid')).not_to_be_visible()
        expect(preview.locator('#dba-print-selection')).to_be_visible()
        pdf=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True)
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b',pdf)),1)
        preview.emulate_media(media='screen')
        preview.locator('#dba-print-all').click()
        preview.emulate_media(media='print')
        expect(preview.locator('#dba-grid')).to_be_visible()
        preview.emulate_media(media='screen')
        close_preview(preview)
        self.assertEqual(before,self.page.evaluate('JSON.stringify(KPHomeDasha.getData())'))

    def test_all_significator_methods_print_complete_tables_on_one_dark_a4_page(self):
        self.page.locator('nav [data-tab="karyesh"]').click()
        for method in ['kp-fourfold','kp-sixfold','kp-fourstep-section']:
            self.page.locator('#sig-method').select_option(method)
            with self.page.expect_popup() as opened:
                self.page.locator('#significators-preview').click()
            preview=opened.value
            if method!='kp-fourstep-section':
                expect(preview.locator('[data-report-id="'+method+'-planet"] tbody tr')).to_have_count(9)
                expect(preview.locator('[data-report-id="'+method+'-house"] tbody tr')).to_have_count(12)
                self.assertTrue(preview.locator('.kp-table-scroll').evaluate_all('rows=>rows.every(n=>getComputedStyle(n).overflowX==="visible"&&n.scrollWidth<=n.clientWidth+1)'))
            else:
                expect(preview.locator('.kp-step-card')).to_have_count(9)
            preview.emulate_media(media='print')
            pdf=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True)
            self.assertEqual(len(re.findall(rb'/Type\s*/Page\b',pdf)),1)
            bounds=preview.locator('.report-page').evaluate('n=>{const p=n.getBoundingClientRect(),i=n.querySelector(".kp-a4-body").getBoundingClientRect();return i.bottom<=p.bottom+1&&i.right<=p.right+1;}')
            self.assertTrue(bounds)
            expect(preview.locator('.report-page-title')).to_have_css('color','rgb(18, 44, 66)')
            preview.emulate_media(media='screen')
            close_preview(preview)

    def test_settings_presets_apply_restore_classic_and_dark_theme_has_readable_surfaces(self):
        self.page.locator('nav [data-tab="astrosettings"]').click()
        expect(self.page.locator('[data-settings-theme="lavender"],[data-settings-theme="light"],[data-settings-theme="classic"]')).to_have_count(0)
        self.page.locator('#settings-tab-presets').click()
        self.page.locator('#settings-preset-presentation').click()
        expect(self.page.locator('#settings-preset-presentation')).to_have_attribute('aria-pressed','true')
        self.page.locator('#settings-save').click()
        values=self.page.evaluate('KPPreferences.get()')
        self.assertEqual(values['fontSize'],16)
        self.assertEqual(values['resolution'],'wide')
        self.page.locator('#settings-preset-classic').click()
        self.page.locator('#settings-save').click()
        values=self.page.evaluate('KPPreferences.get()')
        self.assertEqual(values['fontSize'],12)
        self.assertEqual(values['resolution'],'auto')
        self.assertEqual(values['tableSize'],'medium')
        self.page.locator('#settings-tab-themes').click()
        self.page.locator('#setting-themeType').select_option('dark')
        self.page.locator('#settings-save').click()
        expect(self.page.locator('body')).to_have_attribute('data-kp-theme-type','dark')
        self.page.locator('nav [data-tab="karyesh"]').click()
        expect(self.page.locator('#kp-fourfold-planet thead th').first).to_have_css('background-color','rgb(45, 72, 100)')
        expect(self.page.locator('#kp-fourfold-planet thead th').first).to_have_css('color','rgb(241, 245, 251)')
        expect(self.page.locator('#kp-fourfold-planet tbody td').first).to_have_css('color','rgb(232, 238, 246)')
        self.page.locator('nav [data-tab="resources"]').click()
        expect(self.page.locator('#resource-notes')).to_have_css('background-color','rgb(24, 38, 55)')
        expect(self.page.locator('#resource-notes')).to_have_css('color','rgb(241, 245, 251)')
        self.page.reload(timeout=60000)
        self.page.wait_for_function('window.KPPreferences && document.body.dataset.kpThemeType==="dark"')
        self.assertEqual(self.page.evaluate('KPPreferences.get().themeType'),'dark')

    def test_single_page_south_chart_separates_crowded_planet_labels(self):
        self.page.evaluate("""()=>{KPChartStyle.setStyle('south');const source=document.getElementById('kundali'),lane=source.querySelector('[data-sign-index="7"] .v38-planet-lane');for(const id of ['Sa','Mo']){const n=source.querySelector('.v38-planet[data-planet="'+id+'"]');lane.append(n);n.style.top=id==='Sa'?'70%':'80%';n.style.height='20%';}document.querySelector('#printReport').replaceChildren(KPSinglePageReport.render());}""")
        html=self.page.evaluate('KPSinglePageReport.render().outerHTML')
        # Preview the exact compact chart without triggering another native render.
        preview=self.context.new_page()
        styles=self.page.evaluate('[...document.querySelectorAll("style")].map(n=>"<style>"+n.textContent+"</style>").join("")')
        preview.set_content('<!doctype html><html><head>'+styles+'</head><body>'+html+'</body></html>')
        for media in ['screen','print']:
            preview.emulate_media(media=media)
            bounds=preview.locator('.sp-chart [data-sign-index="7"] .v38-planet-lane').evaluate("""lane=>{const groups=[...lane.querySelectorAll('.v38-item')].map(n=>{const r=[...n.querySelectorAll('.v38-name,.v38-degree,.v38-lords')].map(x=>x.getBoundingClientRect());return {top:Math.min(...r.map(x=>x.top)),bottom:Math.max(...r.map(x=>x.bottom))};}).sort((a,b)=>a.top-b.top);const box=lane.getBoundingClientRect();return {separated:groups.every((r,i)=>!i||r.top>=groups[i-1].bottom-.5),contained:groups.every(r=>r.top>=box.top-.5&&r.bottom<=box.bottom+.5)};}""")
            self.assertTrue(bounds['separated'],bounds)
            self.assertTrue(bounds['contained'],bounds)
        expect(preview.locator('.sp-chart .v38-planet')).to_have_count(9)
        expect(preview.locator('.sp-chart .v38-cusp')).to_have_count(12)
        preview.close()

    def test_original_prediction_catalogues_preserve_counts_conditions_and_duplicate_texts(self):
        data = self.page.evaluate("""() => {
          const pred=KPPrediction.getCatalogue(),ref=KPPredictionLibrary.getCatalogue();
          return {count:pred.events.length,eligible:pred.events.filter(r=>r.automaticEligible).length,
            references:ref.entries.length,short:ref.entries.filter(r=>r.categoryId==='dasha-short').length,
            malformed:ref.entries.find(r=>r.key==='DasaC34511H'&&r.categoryId==='dasha-short'),
            duplicates:ref.entries.filter(r=>r.categoryId==='dasha-short'&&r.duplicateCount>1),
            review:KPPrediction.getData().counts.review};
        }""")
        self.assertEqual((data['count'], data['eligible'], data['references'], data['short']), (1612, 1398, 6213, 391))
        self.assertEqual(data['review'], 214)
        self.assertNotEqual(data['malformed']['mappingStatus'], 'clear')
        self.assertIn('511', data['malformed']['houseMappingRaw'])
        self.assertTrue(data['duplicates'])
        self.assertEqual(len({r['id'] for r in data['duplicates']}), len(data['duplicates']))
        self.page.locator('nav [data-tab="prediction"]').click()
        expect(self.page.locator('#page-title')).to_have_text('Prediction')
        self.page.locator('#pred-tab-dasha-short').click()
        expect(self.page.locator('#pred-library-status')).to_contain_text('391 matching reference entries')

    def test_prediction_subtabs_chart_matches_and_selected_preview_controls(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        for category,count in [('house-results',2869),('general-predictions',824),('events',1046),('dasha-short',391),('dasha-results',1017),('mahadasha-remedies',48),('gemstones',18)]:
            self.page.locator('#pred-tab-'+category).click()
            expect(self.page.locator('#pred-tab-'+category)).to_have_attribute('aria-selected','true')
            expect(self.page.locator('#pred-library-status')).to_contain_text(str(count)+' matching reference entries')
        self.page.locator('#pred-open-gems').click()
        expect(self.page.locator('#page-title')).to_have_text('Gemstone guidance')
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-tab-general-predictions').click()
        self.page.locator('#pred-library-chart').select_option('matched')
        result=self.page.evaluate("""() => ({keys:KPPredictionLibrary.getData().rows.map(r=>r.key),
          expected:currentKPModel.planets.flatMap(p=>[p.id+'InH'+p.occ,p.id+'In'+p.signCode]),
          moon:currentKPModel.planets.find(p=>p.id==='Mo')})""")
        self.assertTrue(set(result['expected']).issubset(result['keys']))
        self.assertIn('Nak'+str(result['moon']['nakIndex']+1)+'C'+str(result['moon']['pada']),result['keys'])
        self.assertFalse(any(key.startswith('Y') for key in result['keys']))
        self.page.locator('#pred-library-search').fill('SuInH')
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-preview').click()
        preview=opened.value
        expect(preview.locator('[data-report-section="prediction"]')).to_be_visible()
        expect(preview.locator('[data-reference-entry]')).to_have_count(1)
        expect(preview.locator('.pred-library-chart-proof')).to_contain_text('Su occupies Bhav')
        preview.evaluate('() => {window.printInvocations=0;window.print=()=>{window.printInvocations++};}')
        preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
        self.assertEqual(preview.evaluate('window.printInvocations'),1)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
        preview.get_by_role('button',name='Zoom −',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1)
        close_preview(preview)
        preview.wait_for_event('close') if not preview.is_closed() else None

    def test_long_reference_preview_prints_every_filtered_record_across_pdf_pages(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-tab-dasha-short').click()
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-preview').click()
        preview=opened.value
        expect(preview.locator('[data-reference-entry]')).to_have_count(391)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        preview.emulate_media(media='print')
        self.assertEqual(preview.locator('.report-page').evaluate('n=>getComputedStyle(n).zoom'),'1')
        output=Path('/tmp/kp-short-dasha-preview.pdf')
        preview.pdf(path=str(output),format='A4',prefer_css_page_size=True,print_background=True)
        self.assertGreater(output.stat().st_size,10000)
        if shutil.which('pdftotext'):
            import subprocess
            text=subprocess.check_output(['pdftotext',str(output),'-']).decode()
            self.assertIn('DasaC1911H',text)
            last=self.page.evaluate('KPPredictionLibrary.getData().rows.at(-1).key')
            self.assertIn(last,text)
            self.assertGreater(text.count('\f'),1)
        preview.close()

    def test_dasha_house_lists_are_explicit_and_conditional_or_invalid_rules_never_match(self):
        result = self.page.evaluate("""() => {
          const model=(""" + FIXTURE_MODEL + """)();
          const records=[
            {id:'clear',key:'ambiguous111',houses:[2,6,10,11],mappingStatus:'clear'},
            {id:'condition',key:'conditional',houses:[2,6],mappingStatus:'conditional'},
            {id:'invalid',key:'34511',houses:[3,4,511],mappingStatus:'clear'},
            {id:'partial',key:'partial',houses:[2,5,11],mappingStatus:'clear'}];
          return KPDashaFal.analyze(model,{lords:['Su'],method:'fourfold',records}).results;
        }""")
        self.assertEqual([r['status'] for r in result], ['matched', 'review', 'review', 'partial'])
        self.assertEqual(result[0]['required'], [2, 6, 10, 11])
        self.assertEqual(result[3]['missing'], [5])

    def test_user_gemstone_rules_choose_1_5_11_owners_and_highest_kp_coverage_with_ties(self):
        result = self.page.evaluate("""() => {
          const model=(""" + FIXTURE_MODEL + """)();
          const base={excluded:'',method:'fourfold',roles:['planet'],stones:{Su:'Ruby',Ma:'Coral',Mo:'Pearl'}};
          const select=rule=>KPGemstones.evaluate(model,{...base,...rule}).results.filter(r=>r.qualifies).map(r=>r.id);
          const unequal=(""" + FIXTURE_MODEL + """)();unequal.houses[4].sgl='Ju';unequal.houses[10].sgl='Mo';
          return {vedic:select({mode:'vedic'}),money:select({mode:'kp',required:'2,6,10,11'}),
            child:select({mode:'kp',required:'2,5,11'}),excluded:select({mode:'kp',required:'2,5,11',excluded:'6'}),
            none:select({mode:'kp',required:'4'}),
            unequalVedic:KPGemstones.evaluate(unequal,{...base,mode:'vedic'}).results.filter(r=>r.qualifies).map(r=>r.id)};
        }""")
        self.assertEqual(result['vedic'], ['Ma', 'Su', 'Sa'])  # Aries/Leo/Aquarius lords, not house 9's Jupiter.
        self.assertEqual(result['unequalVedic'], ['Ma', 'Su', 'Sa'])
        self.assertEqual(result['money'], ['Su', 'Ma'])
        self.assertEqual(result['child'], ['Mo'])
        self.assertEqual(result['excluded'], ['Mo'])
        self.assertEqual(result['none'], [])

    def test_gemstone_modes_and_custom_mapping_survive_chart_backup(self):
        self.page.locator('nav [data-tab="gemstones"]').click()
        self.page.locator('#gem-event').select_option('childbirth')
        expect(self.page.locator('#gem-required')).to_have_value('2,5,11')
        self.page.locator('#gem-mode').select_option('vedic')
        expect(self.page.locator('#gem-status')).to_contain_text('Labhesh')
        expect(self.page.locator('#gem-event')).to_be_disabled()
        # Older saved chart mappings remain compatible without an editable mapping form.
        self.page.evaluate("document.getElementById('gem-stone-Su').value='My ruby reference'")
        chart = self.page.evaluate('getChartData()')
        self.assertEqual(chart['fields']['gem-stone-Su']['value'], 'My ruby reference')
        self.assertEqual(chart['fields']['gem-mode']['value'], 'vedic')
        self.page.evaluate('(chart)=>restoreChartData(chart)', chart)
        expect(self.page.locator('#gem-stone-Su')).to_have_value('My ruby reference')
        expect(self.page.locator('#gem-mode')).to_have_value('vedic')

    def test_one_year_dasha_uses_real_periods_and_clamps_leap_anniversary(self):
        result = self.page.evaluate("""() => {
          const data=KPDashaFal.year('2028-02-29','12:00:00',2,{records:[{id:'one',houses:[1],mappingStatus:'clear'}]});
          return {end:data.end,periods:data.periodCount,rows:data.results.map(r=>({start:r.periodStart,end:r.periodEnd,lords:r.lords}))};
        }""")
        self.assertEqual(result['end'], '2029-02-28T12:00:00')
        self.assertGreater(result['periods'], 0)
        self.assertEqual(result['rows'][0]['start'], '2028-02-29T12:00:00')
        self.assertEqual(result['rows'][-1]['end'], result['end'])
        for previous, current in zip(result['rows'], result['rows'][1:]):
            self.assertEqual(previous['end'], current['start'])
        self.assertTrue(all(len(row['lords']) == 2 for row in result['rows']))
        self.page.locator('nav [data-tab="dasha-fal"]').click()
        self.page.locator('#df-depth').select_option('2')
        expect(self.page.locator('#df-pd')).not_to_be_visible()
        self.page.locator('#df-filter').select_option('all')
        expect(self.page.locator('#dasha-fal-preview')).to_be_enabled()

    def test_south_kundali_retains_chart_without_time_slice_controls(self):
        self.page.locator('nav [data-tab="south9"]').click()
        expect(self.page.locator('#time-slices,.kundali-time-slices-link')).to_have_count(0)
        expect(self.page.locator('nav [data-tab="time-slices"]')).to_have_count(0)
        expect(self.page.locator('#kundali')).to_be_visible()
        self.assertFalse(self.page.evaluate('KPReportPages.sections().some(s=>s.id==="time-slices")') if self.page.evaluate('typeof KPReportPages.sections==="function"') else self.page.locator('[data-report-page-key="time-slices"]').count())
        expect(self.page.locator('#mm-csv,#ts-csv,#gem-csv,#df-csv')).to_have_count(0)

    def test_gemstone_catalogue_groups_simple_controls_and_original_ratna_printing(self):
        self.page.locator('nav [data-tab="gemstones"]').click()
        self.page.locator('#gem-event').select_option('kp:1354:0')
        expect(self.page.locator('#gem-required')).to_have_value('2,6,10,11')
        expect(self.page.locator('#gem-event-proof')).to_contain_text('Prediction catalogue #1354')
        self.assertEqual(self.page.locator('#gemstones select:visible').count(),2)
        self.assertEqual(self.page.locator('#gemstones input:visible').count(),0)
        # Name-only Events.txt records have no supplied house rules and cannot become automatic choices.
        self.assertEqual(self.page.locator('#gem-event option[value^="named:"]').count(),0)
        self.assertLessEqual(self.page.locator('#gemstones-preview').bounding_box()['height'],30)
        original=self.page.evaluate('KPPredictionLibrary.getCatalogue().entries.find(r=>r.categoryId==="gemstones"&&r.key==="RatnaH").value').replace(r'\n','\n')
        with self.page.expect_popup() as opened:self.page.locator('#gemstones-preview').click()
        preview=opened.value;self.assertEqual(preview.locator('[data-ratna-key="RatnaH"] p').inner_text(),original);expect(preview.locator('[data-navagraha]')).to_have_count(9);preview.close()
        chart=self.page.evaluate('getChartData()');self.assertEqual(chart['fields']['gem-event']['value'],'kp:1354:0')

    def test_dasha_report_contains_only_original_filtered_result_text(self):
        self.page.locator('nav [data-tab="dasha-fal"]').click()
        self.page.locator('#df-source').select_option('manual')
        self.page.locator('#df-md').select_option('Su')
        self.page.locator('#df-ad').select_option('')
        self.page.locator('#df-pd').select_option('')
        self.page.locator('#df-filter').select_option('all')
        expected=[text.replace(r'\n','\n') for text in self.page.evaluate('KPDashaFal.getData().results.filter(r=>r.record.categoryId==="dasha-short").map(r=>r.record.value)')]
        with self.page.expect_popup() as opened:
            self.page.locator('#dasha-fal-preview').click()
        preview=opened.value
        expect(preview.locator('.df-text-report table')).to_have_count(0)
        expect(preview.locator('[data-df-result-text]')).to_have_count(391)
        self.assertEqual(preview.locator('[data-df-result-text] p').all_text_contents(),expected)
        text=preview.locator('.df-text-report').inner_text()
        self.assertNotIn('Dahs Fal Short.txt',text)
        self.assertNotIn('Mapping source line',text)
        self.assertNotIn('House group matched',text)
        preview.close()

    def test_prediction_reports_scope_to_selected_cusp_and_chain_preview_is_separate(self):
        self.page.locator('nav [data-tab="prediction"]').click()
        self.page.locator('#pred-main-house').select_option('7')
        self.page.locator('#pred-match-filter').select_option('all')
        expect(self.page.locator('#pred-status')).to_contain_text('Cusp 7')
        with self.page.expect_popup() as opened:
            self.page.locator('#pred-print').click()
        preview=opened.value
        expect(preview.locator('[data-pred-print-chains]')).to_have_count(0)
        expect(preview.locator('.pred-report')).to_have_attribute('data-main-cusp','7')
        mains=preview.locator('[data-pred-event]>td:nth-child(3)').all_text_contents()
        self.assertTrue(mains and all(main=='7' for main in mains))
        self.assertFalse(self.page.locator('#printReport [data-report-section="prediction-chains"]').count())
        preview.close()
        self.page.locator('#prediction-chains-preview').locator('..').locator('summary').click()
        with self.page.expect_popup() as opened:
            self.page.locator('#prediction-chains-preview').click()
        preview=opened.value
        expect(preview.locator('[data-pred-cusp]')).to_have_count(1)
        expect(preview.locator('[data-pred-cusp]')).to_have_attribute('data-pred-cusp','7')
        preview.evaluate('() => {window.calls=0;window.print=()=>{window.calls++};}')
        preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
        self.assertEqual(preview.evaluate('window.calls'),1)
        preview.get_by_role('button',name='Zoom +',exact=True).click()
        self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
        preview.get_by_role('button',name='Zoom −',exact=True).click()
        close_preview(preview)
        self.page.locator('#pred-main-house').select_option('0')
        expect(self.page.locator('#pred-print')).to_be_disabled()
        expect(self.page.locator('#prediction-preview')).to_be_disabled()


class FeatureProtectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('feature_private_server', ROOT / 'protected/server.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.engine = cls.module.Engine()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), cls.module.Handler)
        cls.server.engine = cls.engine
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=CHROMIUM, headless=True, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.engine.close()

    def tearDown(self):
        # Closed test browsers no longer need private worker sessions. Keep the
        # six independent tests within the production limit of four live users.
        def close_sessions():
            for session in self.engine.sessions.values():
                session['context'].close()
            self.engine.sessions.clear()
        self.engine.executor.submit(close_sessions).result()

    def test_private_ruling_fix_kp_matching_colours_capitalization_and_removed_controls(self):
        context=self.browser.new_context()
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('#quick-notepad').click()
            page.locator('#notepad-font').select_option('serif')
            page.locator('#notepad-larger').click()
            expect(page.locator('#notepad-text')).to_have_css('font-size','15px')
            page.locator('#notepad-text').fill('Private personal notes')
            with page.expect_popup() as note_popup:
                page.locator('#notepad-preview').click()
            note_preview=note_popup.value
            expect(note_preview.locator('#notepad-preview-text')).to_have_text('Private personal notes')
            note_preview.get_by_role('button',name='Zoom +',exact=True).click()
            self.assertEqual(note_preview.locator('.notepad-preview-page').evaluate('n=>n.style.zoom'),'1.1')
            close_preview(note_preview)
            page.locator('#notepad-close').click()
            page.locator('nav [data-tab="south9"]').click()
            expect(page.locator('#south9 button',has_text='Manual Edit')).to_have_count(0)
            expect(page.locator('#time-slices')).to_have_count(0)
            page.locator('nav [data-tab="ruling-planets"]').click()
            expect(page.locator('#rpw-date')).to_be_visible(timeout=30000)
            page.locator('#rpw-date').fill('2028-01-31')
            page.locator('#rpw-time').fill('13:15')
            page.locator('#rpw-calculate').click()
            expect(page.locator('#rpw-status')).to_contain_text('13:15:00',timeout=30000)
            expect(page.locator('#rpw-table tbody tr')).to_have_count(4)
            page.locator('#rp-time-event').select_option('11')
            expect(page.locator('#rp-time-houses')).to_have_value('1,11',timeout=30000)
            page.locator('nav [data-tab="matchmaking"]').click()
            expect(page.locator('#mm-kp-analysis')).to_contain_text('/ 100',timeout=30000)
            expect(page.locator('#mm-kp-analysis [data-kp-category]')).to_have_count(6)
            expect(page.get_by_text('Copy native birth details',exact=True)).to_have_count(0)
            page.locator('#mm-boy-name').fill('nitin talegaokar')
            page.locator('#mm-girl-name').click()
            expect(page.locator('#mm-boy-name')).to_have_value('Nitin Talegaokar',timeout=30000)
            page.locator('nav [data-tab="prediction"]').click()
            expect(page.locator('#pred-export')).to_have_count(0)
            page.locator('#pred-tab-gemstones').click()
            expect(page.locator('#pred-library-csv')).to_have_count(0)
            with page.expect_popup() as opened:
                page.locator('#pred-library-print').click()
            preview=opened.value
            expect(preview.locator('#preview-save-pdf')).to_be_visible(timeout=30000)
            self.assertNotIn('Choose Save as PDF in the print dialog.',preview.locator('body').inner_text())
            preview.close()
            page.locator('nav [data-tab="aspects"]').click()
            expect(page.locator('#am-mode')).to_contain_text('ग्रहांपासून भावांवर दृष्टी संबंध',timeout=30000)
            page.locator('#aspects .am-advanced > summary').click()
            page.locator('#am-header-colour').evaluate("e=>{e.value='#112233';e.dispatchEvent(new Event('change',{bubbles:true}));}")
            expect(page.locator('#aspects .am-matrix thead th').first).to_have_css('background-color','rgb(17, 34, 51)',timeout=30000)
            self.assertEqual(errors,[])
        finally:
            context.close()

    def test_private_resource_notes_stay_local_survive_reload_and_export_text(self):
        context=self.browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('nav [data-tab="resources"]').click()
            expect(page.locator('#resources')).to_have_class('tab active',timeout=30000)
            page.locator('#resource-new-topic').fill('Private notes')
            page.locator('#resource-add').click()
            page.locator('#resource-notes').fill('संदर्भ · saved on my PC')
            page.locator('#resource-save').click()
            page.locator('nav [data-tab="south9"]').click()
            expect(page.locator('#south9')).to_have_class('tab active',timeout=30000)
            page.locator('nav [data-tab="resources"]').click()
            expect(page.locator('#resources')).to_have_class('tab active',timeout=30000)
            expect(page.locator('#resource-notes')).to_have_value('संदर्भ · saved on my PC')
            page.reload()
            expect(page.locator('#resources')).to_have_class('tab active',timeout=60000)
            page.locator('nav [data-tab="resources"]').click()
            expect(page.locator('#resources')).to_have_class('tab active',timeout=30000)
            page.locator('#resource-topic').select_option('Private notes')
            expect(page.locator('#resource-notes')).to_have_value('संदर्भ · saved on my PC')
            with page.expect_popup() as opened:
                page.locator('#resource-preview').click()
            preview=opened.value
            expect(preview.locator('#notepad-preview-text')).to_contain_text('संदर्भ · saved on my PC')
            close_preview(preview)
            page.evaluate('window.showSaveFilePicker=undefined')
            page.locator('#resource-export-scope').select_option('all')
            with page.expect_download() as downloaded:
                page.locator('#resource-download').click()
            downloaded.value.save_as('/tmp/kp-private-resources.txt')
            text=Path('/tmp/kp-private-resources.txt').read_text(encoding='utf-8-sig')
            self.assertIn('Private notes',text)
            self.assertIn('KP Fundamentals',text)
            self.assertIn('संदर्भ · saved on my PC',text)
            self.assertEqual(errors,[])
        finally:context.close()

    def test_private_dba_popup_and_significator_pdf_use_computed_data(self):
        context=self.browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('nav [data-tab="mdcalc"]').click()
            expect(page.locator('#mdcalc')).to_have_class('tab md-locked active',timeout=30000)
            before=page.request.get(self.url+'/export').json()['fields']
            with page.expect_popup() as opened:
                page.locator('#dba-preview').click()
            preview=opened.value
            expect(preview.locator('.dba-card')).to_have_count(9,timeout=60000)
            preview.locator('#dba-md').select_option('1')
            preview.locator('#dba-ad').select_option('2')
            preview.locator('#dba-pd').select_option('3')
            self.assertEqual(preview.evaluate('KPDBASelection.getData().pd'),3)
            body=preview.content()
            self.assertNotIn('KPEphemeris',body)
            self.assertNotIn('durationDays',body)
            close_preview(preview)
            after=page.request.get(self.url+'/export').json()['fields']
            for id in ['name','dob','birthTime']:
                self.assertEqual(before.get(id),after.get(id))
            page.locator('nav [data-tab="karyesh"]').click()
            expect(page.locator('#karyesh')).to_have_class('tab active',timeout=30000)
            page.locator('#sig-method').select_option('kp-sixfold')
            with page.expect_popup() as opened:
                page.locator('#significators-preview').click()
            preview=opened.value
            expect(preview.locator('[data-report-id="kp-sixfold-planet"] tbody tr')).to_have_count(9,timeout=60000)
            expect(preview.locator('[data-report-id="kp-sixfold-house"] tbody tr')).to_have_count(12)
            preview.emulate_media(media='print')
            pdf=preview.pdf(format='A4',prefer_css_page_size=True,print_background=True)
            self.assertEqual(len(re.findall(rb'/Type\s*/Page\b',pdf)),1)
            preview.close()
            self.assertEqual(errors,[])
        finally:context.close()

    def test_private_presets_and_dark_theme_save_readable_values(self):
        context=self.browser.new_context(viewport={'width':1280,'height':900})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('nav [data-tab="astrosettings"]').click()
            expect(page.locator('#astrosettings')).to_have_class('tab active',timeout=30000)
            page.locator('#settings-tab-presets').click()
            expect(page.locator('#settings-pane-presets')).to_be_visible(timeout=30000)
            page.locator('#settings-preset-compact').click()
            expect(page.locator('#settings-preset-compact')).to_have_attribute('aria-pressed','true',timeout=30000)
            page.locator('#settings-save').click()
            expect(page.locator('body')).to_have_attribute('data-kp-resolution','compact',timeout=30000)
            page.locator('#settings-tab-themes').click()
            page.locator('#setting-themeType').select_option('dark')
            page.locator('#settings-save').click()
            expect(page.locator('body')).to_have_attribute('data-kp-theme-type','dark',timeout=30000)
            page.locator('nav [data-tab="resources"]').click()
            expect(page.locator('#resources')).to_have_class('tab active',timeout=30000)
            expect(page.locator('#resource-notes')).to_have_css('color','rgb(241, 245, 251)')
            expect(page.locator('#resource-notes')).to_have_css('background-color','rgb(24, 38, 55)')
            self.assertEqual(errors,[])
        finally:context.close()

    def test_customer_feature_controls_previews_and_source_isolation(self):
        context = self.browser.new_context()
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home', timeout=60000)
            page.locator('nav [data-tab="transit"]').click()
            expect(page.locator('#tr-period')).to_have_value('PD',timeout=30000)
            expect(page.locator('[data-current-period]')).to_have_count(3)
            expect(page.locator('#tr-start')).not_to_be_visible()
            page.locator('#tr-period').select_option('AD')
            expect(page.locator('#tr-period-summary')).to_contain_text('Current AD',timeout=30000)
            for tab in ['prediction', 'dasha-fal', 'gemstones', 'south9']:
                page.locator('nav [data-tab="'+tab+'"]').click()
                expect(page.locator('#'+tab)).to_be_visible(timeout=30000)
            expect(page.locator('#south9 #time-slices')).to_have_count(0)
            expect(page.locator('nav [data-tab="time-slices"]')).to_have_count(0)
            page.locator('nav [data-tab="gemstones"]').click()
            page.locator('#gem-mode').select_option('vedic')
            expect(page.locator('#gem-status')).to_contain_text('Labhesh', timeout=30000)
            exported = page.request.get(self.url+'/export').json()
            self.assertEqual(exported['fields']['gem-mode']['value'], 'vedic')
            page.locator('nav [data-tab="prediction"]').click()
            page.locator('#pred-tab-events').click()
            expect(page.locator('#pred-library-status')).to_contain_text('1046 matching reference entries',timeout=30000)
            page.locator('#pred-library-search').fill('Success in business')
            expect(page.locator('#pred-library-status')).to_contain_text('4 matching reference entries',timeout=30000)
            with page.expect_popup() as opened:
                page.locator('#prediction-preview').click()
            preview=opened.value
            expect(preview.locator('[data-reference-entry]')).to_have_count(4,timeout=90000)
            self.assertLess(preview.get_by_role('button',name='Print / Save PDF',exact=True).bounding_box()['y'],100)
            preview.evaluate('() => {window.printInvocations=0;window.print=()=>{window.printInvocations++};}')
            preview.get_by_role('button',name='Print / Save PDF',exact=True).click()
            self.assertEqual(preview.evaluate('window.printInvocations'),1)
            preview.get_by_role('button',name='Zoom +',exact=True).click()
            self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1.1)
            preview.get_by_role('button',name='Zoom −',exact=True).click()
            self.assertAlmostEqual(preview.locator('.report-page').evaluate('n=>parseFloat(n.style.zoom)'),1)
            close_preview(preview)
            for section in ['prediction', 'dasha-fal', 'gemstones']:
                response = page.request.get(self.url+'/'+section+'-preview', timeout=90000)
                self.assertEqual(response.status, 200, response.text()[:200])
                self.assertIn('data-report-section="'+section+'"', response.text())
            snapshot = page.request.get(self.url+'/snapshot').json()
            self.assertNotIn('<script', snapshot['html'])
            self.assertEqual(page.request.get(self.url+'/index.html').status, 404)
            self.assertEqual(errors, [])
        finally:
            context.close()

    def test_private_removed_time_slice_chain_preview_and_restricted_reports(self):
        context=self.browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        try:
            page.goto(self.url)
            expect(page.locator('#page-title')).to_have_text('Home',timeout=60000)
            page.locator('nav [data-tab="south9"]').click()
            expect(page.locator('#south9')).to_have_class('tab active',timeout=30000)
            snapshot=page.request.get(self.url+'/snapshot').json()
            token=snapshot['token']
            before=page.request.get(self.url+'/export').json()['fields']
            expect(page.locator('#time-slices')).to_have_count(0)
            page.locator('nav [data-tab="prediction"]').click()
            expect(page.locator('#prediction')).to_have_class('tab active',timeout=30000)
            page.locator('#pred-main-house').select_option('7')
            expect(page.locator('#pred-status')).to_contain_text('Cusp 7',timeout=30000)
            response=page.request.get(self.url+'/prediction-preview')
            self.assertEqual(response.status,200)
            self.assertNotIn('data-pred-print-chains',response.text())
            self.assertIn('data-main-cusp="7"',response.text())
            page.locator('#prediction-chains-preview').locator('..').locator('summary').click()
            expect(page.locator('#prediction-chains-preview')).to_be_visible(timeout=30000)
            with page.expect_popup() as opened:
                page.locator('#prediction-chains-preview').click()
            preview=opened.value
            expect(preview.locator('[data-pred-cusp]')).to_have_count(1,timeout=60000)
            expect(preview.locator('[data-pred-cusp]')).to_have_attribute('data-pred-cusp','7')
            preview.close()
            response=page.request.get(self.url+'/dasha-fal-preview')
            self.assertEqual(response.status,200)
            self.assertIn('df-text-report',response.text())
            self.assertNotIn('data-df-record',response.text())
            response=page.request.get(self.url+'/gemstones-preview')
            self.assertEqual(response.status,200)
            self.assertIn('data-ratna-key="RatnaH"',response.text())
            self.assertEqual(errors,[])
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main()
