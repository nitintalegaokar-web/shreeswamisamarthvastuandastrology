"""User-specified max-unique-house scoring, including ties and no-match cases."""
import unittest,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GemstoneRankingTests(unittest.TestCase):
 def test_unique_houses_ties_no_match_and_invalid_houses(self):
  script="""const {evaluate}=require('./vendor/predictions/gemstone-event-ranking.js');const model={ready:true,planets:[{id:'Su'},{id:'Mo'},{id:'Me'}],fourfold:{planets:[{id:'Su',A:[2,2,6],B:[6],C:[],D:[]},{id:'Mo',A:[2],B:[6],C:[11],D:[]},{id:'Me',A:[11],B:[6],C:[2],D:[]}]}};const rule={required:'2,6,11',stones:{Su:'Ruby',Mo:'Pearl',Me:'Emerald'}};const before=JSON.stringify(model),win=evaluate(model,rule),none=evaluate(model,{...rule,required:'12'});let invalid=0;for(const required of ['', '13','2,x'])try{evaluate(model,{...rule,required});}catch(e){invalid++;}process.stdout.write(JSON.stringify({win,none,invalid,unchanged:before===JSON.stringify(model)}));"""
  d=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT));self.assertEqual(d['win']['highest'],3);self.assertEqual({r['id'] for r in d['win']['results'] if r['qualifies']},{'Mo','Me'});self.assertEqual(next(r for r in d['win']['results'] if r['id']=='Su')['score'],2);self.assertFalse(any(r['qualifies'] for r in d['none']['results']));self.assertEqual(d['invalid'],3);self.assertTrue(d['unchanged'])
