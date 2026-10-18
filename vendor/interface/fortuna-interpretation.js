/* Supplied Fortuna house interpretations. Derived display only; calculations unchanged. */
(function(root){'use strict';
const en=[
'The person will be fortunate, gain in his enterprises, industry etc. He will be successful in his efforts. He works with confidence and will have a brilliant and successful career.',
'The person will be a very lucky person. He will gain through property, business etc. and enjoy a satisfactory bank balance. He will have a happy domestic life and improvement in his status.',
'The person will gain through brothers, short journeys, agency and publication business. He will work as an advisor or a Secretary and earn. He will earn easily. He maintains good relationship with neighbours.',
'The person will get a decent patrimony, saves much of his earnings, invests in landed property or business. He will get a hidden treasure. Mines, Minerals and Metals will make him rich. He will become suddenly rich.',
'The person will earn his fortune in Sports, Opera, Cinema, music etc. He will have lucky children and they contribute much for his financial improvement. He gains by investments and speculations, share market etc.',
'The person gains by poultry, cattle etc. Uncles and Aunts will contribute to his gains. He gains through his pet animals. He will gain through small banking business and get over draft facilities from the Bank.',
'The Person gains through his partners and other sex. He gains through contracts, election, competition, litigation, associations, clubs and public organisations etc.',
'The person gains a huge property through will or transfer. Partner or other sex gives a lump sum money. He gains through Insurance, Business, Gratuity, Bonus etc. and his life-partner will be an employee.',
'The person gains through long journeys as a Travelling Agent. Gains by foreign contract and by publication or a new discovery. Gains through service in educational, legal, spiritual, yogic, social service or religious institutions and by import and export trade.',
'Gains in service. Reaches a very high status quickly, even overlooking his seniors. All his efforts will bring him large money.',
'Gains through friends, brothers. Does a very profitable business. Friends from high society will contribute to his gains. His desires are easily fulfilled.',
'He gains from unknown sources. Gains by smuggling. Very lucky in purchases and sales. Investments will bring good fortune. Inimical activities will end in the gain of this person.'
];
const mr=[
'व्यक्ती भाग्यवान असेल. उद्योग, व्यवसाय व उपक्रमांत लाभ होईल. प्रयत्नांना यश मिळेल. आत्मविश्वासाने काम करून उज्ज्वल व यशस्वी कारकीर्द घडवेल.',
'व्यक्ती अत्यंत भाग्यवान असेल. मालमत्ता, व्यवसाय इत्यादींतून लाभ होईल व समाधानकारक बँक शिल्लक राहील. कौटुंबिक जीवन आनंदी असेल व प्रतिष्ठेत वाढ होईल.',
'भावंडे, लहान प्रवास, एजन्सी व प्रकाशन व्यवसायातून लाभ होईल. सल्लागार किंवा सचिव म्हणून उत्पन्न मिळेल. सहज कमाई होईल. शेजाऱ्यांशी चांगले संबंध राहतील.',
'चांगली वडिलोपार्जित मालमत्ता मिळेल. उत्पन्नातील मोठा भाग बचत करून जमीन-जुमला किंवा व्यवसायात गुंतवेल. गुप्तधन मिळेल. खाणी, खनिजे व धातू यातून संपत्ती प्राप्त होऊन अचानक श्रीमंती येईल.',
'क्रीडा, नाट्यसंगीत, चित्रपट व संगीत यातून भाग्योदय होईल. भाग्यवान संतती आर्थिक प्रगतीत मोठे योगदान देईल. गुंतवणूक, सट्टा व शेअर बाजारातून लाभ होईल.',
'कुक्कुटपालन, गुरेढोरे इत्यादींतून लाभ होईल. मामा-मावशी किंवा काका-आत्या लाभास हातभार लावतील. पाळीव प्राण्यांपासून लाभ होईल. लहान बँकिंग व्यवसायातून लाभ व बँकेकडून अधिकर्ष सुविधा मिळेल.',
'भागीदार व विरुद्ध लिंगी व्यक्तींमुळे लाभ होईल. करार, निवडणूक, स्पर्धा, न्यायालयीन प्रकरणे, संघटना, मंडळे व सार्वजनिक संस्थांतून लाभ होईल.',
'मृत्युपत्र किंवा हस्तांतरणातून मोठी मालमत्ता मिळेल. जोडीदार किंवा विरुद्ध लिंगी व्यक्तीकडून एकरकमी धन मिळेल. विमा, व्यवसाय, उपदान व अतिरिक्त लाभ यातून लाभ होईल. जीवनसाथी नोकरी करणारा असेल.',
'प्रवासी प्रतिनिधी म्हणून लांबच्या प्रवासातून लाभ होईल. परदेशी करार, प्रकाशन किंवा नवीन शोधातून लाभ होईल. शैक्षणिक, कायदेविषयक, आध्यात्मिक, योग, समाजसेवा किंवा धार्मिक संस्थांतील सेवेतून तसेच आयात-निर्यात व्यापारातून लाभ होईल.',
'नोकरीत लाभ होईल. वरिष्ठांनाही मागे टाकून लवकर उच्च पद प्राप्त होईल. सर्व प्रयत्नांतून मोठी धनप्राप्ती होईल.',
'मित्र व भावंडांमुळे लाभ होईल. अत्यंत फायदेशीर व्यवसाय करेल. उच्च समाजातील मित्र लाभास हातभार लावतील. इच्छा सहज पूर्ण होतील.',
'अज्ञात मार्गांनी लाभ होईल. तस्करीतून लाभ होईल. खरेदी-विक्रीत विशेष भाग्य लाभेल. गुंतवणुकीतून भाग्योदय होईल. शत्रुत्वाच्या कृतींचा शेवटही या व्यक्तीच्या लाभात होईल.'
];
const CIRCLE=1296000,norm=n=>((n%CIRCLE)+CIRCLE)%CIRCLE;
function occupiedHouse(longitude,cusps,unit='arcseconds'){
 if(!Number.isFinite(longitude)||!Array.isArray(cusps)||cusps.length!==12||!['degrees','arcseconds'].includes(unit))return null;
 const scale=unit==='degrees'?3600:1,values=cusps.map(c=>Number(typeof c==='object'?c.longitude:c)*scale);if(values.some(v=>!Number.isFinite(v)))return null;
 const spans=values.map((v,i)=>norm(values[(i+1)%12]-v));if(spans.some(v=>v<=0)||Math.abs(spans.reduce((a,b)=>a+b,0)-CIRCLE)>.0001)return null;
 const lon=norm(longitude*scale),i=values.findIndex((v,i)=>norm(lon-v)<spans[i]);return i<0?null:i+1;
}
function get(house,lang='english'){if(!Number.isInteger(house)||house<1||house>12)return null;return {house,language:lang,text:lang==='marathi'?mr[house-1]:lang==='bilingual'?en[house-1]+'\n\n'+mr[house-1]:lang==='english'?en[house-1]:null};}
let dialog,focusBack,selected,queued=false;
const language=()=>root.KPPreferences?.get?.().language||'english';
function context(target){
 const transit=Boolean(target?.closest?.('#transit-chart,[data-kp-source-id="tc-rashi-chart"],[data-kp-source-id="tc-bhav-chart"]')),model=transit?root.KPTransitChart?.getData?.():root.currentKPModel,point=transit?root.KPFortuna?.getTransit?.(model):root.KPFortuna?.getNatal?.();
 if(!model?.ready||!point)return null;
 const house=occupiedHouse(transit?point.longitudeDegrees:point.longitude,transit?model.cusps:model.houses,transit?'degrees':'arcseconds');if(!house)return null;return {house,point,transit};
}
function render(){
 if(!dialog||!selected)return;const lang=language(),isMr=lang==='marathi',both=lang==='bilingual',d=get(selected.house,lang);dialog.lang=isMr?'mr':'en';
 dialog.querySelector('h2').textContent=isMr?'फॉर्च्युना · भाव '+selected.house:both?'Fortuna · फॉर्च्युना · '+selected.house:'Fortuna · House '+selected.house;
 dialog.querySelector('.kp-fortuna-kicker').textContent=isMr?'भाग्यबिंदूचे भावफल':both?'Part of Fortune · भाग्यबिंदू':'Part of Fortune';
 dialog.querySelector('.kp-fortuna-badge').textContent=(isMr?'भाव ':'House ')+selected.house;
 dialog.querySelector('.kp-fortuna-position').textContent=(selected.transit?(isMr?'गोचर कुंडली':'Transit chart'):(isMr?'जन्मकुंडली':'Natal chart'))+' · '+selected.point.degree;
 const text=dialog.querySelector('.kp-fortuna-text');text.textContent=d.text||(root.KPPredictionLanguage?.message('unavailable',lang)||'—');
 dialog.querySelector('.kp-fortuna-basis').textContent=isMr?'भावचलित कुंडलीतील भावसीमांनुसार स्थान. राशी क्रमांक किंवा फिरवलेल्या दृश्यावरून भाव ठरवलेला नाही.':'House determined from the chart’s cusp boundaries, independently of sign number or chart rotation.';
 const close=dialog.querySelector('button');close.textContent=isMr?'बंद करा':both?'Close · बंद करा':'Close';
}
function ensure(){if(dialog)return;dialog=document.createElement('dialog');dialog.id='kp-fortuna-dialog';dialog.className='no-print';dialog.setAttribute('data-no-localize','');dialog.setAttribute('aria-labelledby','kp-fortuna-title');dialog.innerHTML='<header><span class="kp-fortuna-symbol" aria-hidden="true">⊗</span><div><span class="kp-fortuna-kicker"></span><h2 id="kp-fortuna-title"></h2></div><button type="button"></button></header><div class="kp-fortuna-content"><span class="kp-fortuna-badge"></span><p class="kp-fortuna-position"></p><p class="kp-fortuna-text"></p><p class="kp-fortuna-basis"></p></div>';document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});dialog.addEventListener('close',()=>focusBack?.focus?.({preventScroll:true}));}
function open(target){const d=context(target);if(!d)return false;selected=d;focusBack=target||document.activeElement;ensure();render();if(!dialog.open)dialog.showModal();dialog.querySelector('button').focus();return true;}
function mark(e){if(!e)return;e.dataset.fortunaInterpretation='true';e.setAttribute('role','button');e.setAttribute('tabindex','0');e.setAttribute('aria-haspopup','dialog');e.setAttribute('aria-label',language()==='marathi'?'फॉर्च्युना · भावफल पाहा':'Fortuna · View house interpretation');}
function decorate(){queued=false;document.querySelectorAll('.v38-planet[data-planet="Fo"] .v38-name,svg [data-planet="Fo"],#kundali-fortuna-info,#tc-fortuna-info,#home .kp-fortuna-info').forEach(mark);}
function schedule(){if(!queued){queued=true;requestAnimationFrame(decorate);}}
function init(){decorate();const o=new MutationObserver(schedule);for(const id of ['kundali','kundali-north','home-kundali','tc-rashi-chart','tc-bhav-chart','kundali-fortuna-info','tc-fortuna-info']){const n=document.getElementById(id);if(n)o.observe(n,{childList:true,subtree:true});}document.addEventListener('click',e=>{const t=e.target.closest?.('[data-fortuna-interpretation]');if(t){e.preventDefault();e.stopPropagation();open(t);}},true);document.addEventListener('keydown',e=>{if(!['Enter',' '].includes(e.key))return;const t=e.target.closest?.('[data-fortuna-interpretation]');if(t){e.preventDefault();e.stopPropagation();open(t);}},true);root.addEventListener('kp-preferences-changed',()=>{decorate();if(dialog?.open)render();});}
root.KPFortunaInterpretation=Object.freeze({get,occupiedHouse,open,refresh:decorate,source:()=>({english:[...en],marathi:[...mr]})});
if(typeof module!=='undefined'&&module.exports)module.exports=root.KPFortunaInterpretation;
if(root.document){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();}
})(typeof window==='undefined'?globalThis:window);
