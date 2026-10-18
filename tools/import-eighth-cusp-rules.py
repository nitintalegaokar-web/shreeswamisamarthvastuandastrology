"""Preserve the supplied bilingual rules; encode only explicit placement conditions."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];source=root/'data/eighth-cusp-2026-10-18/Pasted-text.txt'
# Houses below mean occupied KP bhava, not sign number or significator-house union.
conditions={1:{'houses':[1,5,9]},5:{'houses':[6]},6:{'houses':[1]},7:{'houses':[1]},8:{'planets':['Ma']},9:{'houses':[6,12]},10:{'planets':['Ve']},11:{'planets':['Ra','Ke']},12:{'houses':[4,10]},13:{'signs':[3,7,11]},14:{'houses':[5,8,9]},15:{'planets':['Su']},16:{'houses':[1]},17:{'houses':[2,4]},18:{'planets':['Su','Mo','Sa'],'houses':[2,7,12]},19:{'houses':[3,6]},20:{'planets':['Ve'],'houses':[4,8]},22:{'houses':[4,6]},23:{'planets':['Ma'],'houses':[4,6]},24:{'planets':['Mo','Sa'],'houses':[4,7,8]},25:{'planets':['Sa'],'houses':[5,7,9]},26:{'houses':[5,9,10]},27:{'houses':[5,8,9]},28:{'planets':['Ma'],'houses':[6,8,12]},29:{'planets':['Ra','Sa','Su'],'houses':[7]},30:{'houses':[12]},31:{'planets':['Mo','Sa'],'houses':[12]},36:{'planets':['Me'],'signs':[8,11]},37:{'planets':['Mo','Sa'],'signs':[1,6]},38:{'planets':['Ma']},39:{'planets':['Ma','Sa','Ra','Ke'],'houses':[1]},40:{'planets':['Ra'],'houses':[12]}}
extra={2:'good-aspect',3:'badhaka-maraka-connection',11:'house-connection-and-scope',15:'sun-saturn-house-scope',21:'fourth-and-eighth-lord-house-scope',22:'watery-sign-connection'}
named_aspects={4:(["Mo","Sa","Ma"],"any"),5:(["Sa"],"any"),6:(["Ma","Sa"],"any"),7:(["Ma","Sa"],"all"),8:(["Sa"],"any"),16:(["Mo","Sa"],"any"),26:(["Su","Mo","Ma"],"any"),27:(["Su","Mo","Sa"],"any"),32:(["Su","Ma"],"any"),33:(["Mo","Sa"],"all"),34:(["Me"],"any"),35:(["Su","Mo","Ma","Sa"],"any")}
entries=[]
for line,row in enumerate(source.read_text().splitlines(),1):
 if not row.strip():continue
 cols=[x.strip() for x in row.split('\t')]
 if len(cols)!=5:raise ValueError(f'Expected five columns at line {line}')
 n=len(entries)+1;review=[]
 if 'afflict' in cols[0].lower() or 'पीडित' in cols[4] or 'पीडा' in cols[4] or 'ग्रहपीडित' in cols[4]:review.append('affliction')
 if n in extra:review.append(extra[n])
 if n in named_aspects:conditions.setdefault(n,{})['namedAspects']={'planets':named_aspects[n][0],'mode':named_aspects[n][1]}
 if n==2:conditions.setdefault(n,{})['beneficAspect']=True
 if n==3:conditions.setdefault(n,{})['excludeBadhakaMaraka']=True
 if n==11:conditions.setdefault(n,{})['signifiesAll']=[8,12]
 entries.append({'id':'eighth-'+str(n),'number':n,'english':cols[0],'marathiTitle':cols[2],'marathi':cols[3]+(' · '+cols[4] if cols[4]!='-' else '')+' — '+cols[2],'category':cols[1],'condition':conditions.get(n,{}),'reviewConditions':review,'sourceLine':line})
assert len(entries)==40
out={'metadata':{'filename':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'count':len(entries),'policy':'Uses existing incoming whole-sign aspect lists and natural-benefic classification where applicable. Named aspects require the stated any/all planets. Generic affliction means a malefic incoming aspect under existing classification. Badhaka/maraka and explicit house connections use existing fourfold A-D significators. Undefined compound scopes remain review-only. Traditional source statements are not clinical or lifespan findings.'},'entries':entries}
(root/'data/eighth-cusp-2026-10-18/rules.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(root/'vendor/predictions/eighth-cusp-data.js').write_text('/* Exact supplied bilingual rule text and explicit placement predicates. */\nglobalThis.KPEighthCuspData='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n')
print('Imported 40 supplied bilingual eighth-cusp rules.')
