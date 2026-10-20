"""Build the bundled English A4 tutorial from reviewed application workflows."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
for name,file in [('Guide','DejaVuSans.ttf'),('GuideBold','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='GuideBody',fontName='Guide',fontSize=10,leading=15,spaceAfter=9,textColor=colors.HexColor('#23374a')))
styles.add(ParagraphStyle(name='GuideTitle',fontName='GuideBold',fontSize=23,leading=29,spaceAfter=18,textColor=colors.HexColor('#173e63')))
styles.add(ParagraphStyle(name='GuideSub',fontName='GuideBold',fontSize=12,leading=17,spaceBefore=9,spaceAfter=7,textColor=colors.HexColor('#17675e')))
styles.add(ParagraphStyle(name='GuideCell',fontName='Guide',fontSize=9,leading=13,textColor=colors.HexColor('#23374a')))
P=lambda s:Paragraph(s,styles['GuideBody'])
def grid(rows,widths=None):
 t=Table([[Paragraph(str(v),styles['GuideCell']) for v in row] for row in rows],colWidths=widths or [83*mm,83*mm],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf5')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#a4b7c7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));return t
pages=[]
def page(title,paragraphs,rows=None):
 items=[Paragraph(title,styles['GuideTitle'])]
 for text in paragraphs:
  if text.startswith('## '):items.append(Paragraph(text[3:],styles['GuideSub']))
  else:items.append(P(text))
 if rows:items.extend([Spacer(1,5*mm),grid(rows)])
 pages.append(items)
page('KP MASTER\nUser tutorial'.replace('\n','<br/>'),[
 '<b>Version 1.2.10 · English guide · 20 October 2026</b>',
 'Use this guide alongside the software. It explains the main controls, the latest RP settings and the complete report workflow.',
 '## Your first session',
 '<b>1.</b> Extract the ZIP completely and open <b>index.html</b> in Chrome or Edge. The startup logo leads to Home.',
 '<b>2.</b> Open <b>Astrologer settings</b>, choose a language and enter your consultation location. Save your settings.',
 '<b>3.</b> Create or open a kundali. Check the name, date, time, latitude, longitude and UTC offset before reading results.',
 '<b>4.</b> Review the chart and significators, then open Prediction or the RP timing tool.',
 '<b>5.</b> Save a chart file, select report pages, preview them and print or export a PDF.',
 '## Guide map',
 '2 Chart entry and saving · 3 Chart reading and popups · 4 Vedic Kundali · 5 Prediction language · 6 Event Promise · 7 RP settings · 8 RP timing · 9 Transit dates · 10 Gemstones · 11 A4 reports · 12 Backup and troubleshooting.',
 'Astrological outputs are interpretations of the selected rules and chart data. The childbirth worksheet is not a medical test, and longevity categories are not a confirmed lifespan.'
])
page('2 · Create and save a kundali',[
 '## Birth chart',
 'Use <b>Home → New Horoscope</b> or open Birth details. Enter the person’s details, date and local birth time. Choose the place, then check the coordinates and UTC offset. Calculate or update the chart using the available entry controls.',
 'For India lookup, type at least three letters in the Place field. State and District narrow the search. Select a result to fill coordinates and India UTC +05:30; check that the chosen place is correct.',
 '## Horary and Instant Prashna',
 '<b>New Horary</b> is for a horary question and its chart inputs. <b>Instant Prashna Chart</b> uses the current consultation context. These are separate from the saved natal chart.',
 'Ascendant / Moon transitions belong to the natal chart. Open a ready natal kundali to use that tool.',
 '## Save before experimenting',
 'Use <b>Save Kundali</b> to keep a portable chart file. Use <b>Open Kundali</b> to restore one. Keep an external copy as well as any browser-saved state.',
 'If you enter manual Raphael, ephemeris or cusp values, retain the source values with your chart record. Manual changes affect the resulting analysis.',
 '## Check before you interpret',
 'Verify the person’s identity, chart type, date, AM/PM or 24-hour time, time zone and place. A wrong time zone can shift the Ascendant and cusps even when the displayed place name looks correct.'
])
page('3 · Read the chart and popups',[
 'Home shows the kundali and calculation tables. Use the chart-style selector for South Indian or North Indian presentation.',
 '## Reference popups',
 'Click a <b>planet name</b> for its Karkatva. Click a <b>Rashi name in a planetary or cuspal position table</b> for the Rashi Karkatva. Click an available house number or Nakshatra name for the corresponding reference.',
 'The South Indian chart’s sign headings have been removed. Use the Rashi column in its position tables when you need the sign reference.',
 'Basic, Four-fold, Six-fold, Four-step and Nadi tables offer reference clicks wherever the corresponding planet, house, sign or Nakshatra entries are present.',
 '## Significator views',
 'Use the view buttons to compare the available significator methods. A lettered column has a specific calculation definition; do not interpret the same letter as identical across different methods.',
 '## Fortuna',
 'Click Fortuna’s label or position summary to view the supplied interpretation for its occupied house. Check whether you are viewing natal or transit cusps.',
 '## Retrograde markers',
 'A retrograde marker can appear for a planet whose motion is retrograde. Rahu and Ketu omit the R marker because the software uses mean lunar nodes. This display choice does not change their longitudes.'
])
page('4 · Vedic Kundali and symbols',[
 'Open <b>Tools → Vedic Kundali</b>. Select the chart or calculation view you need. The divisional selector changes the displayed division; D1 is the Rashi chart.',
 '## Vedic-only symbol legend',
 'The chart view includes the Kundali symbol legend. It lists all twelve zodiac signs, their rulers, elements and movable/fixed/dual nature. A second table explains retrograde, direct, combustion, exaltation, debilitation and friendship symbols.',
 'The legend is a reference key. A symbol listed in the key does not assert that every planet in the chart has that condition.',
 'The legend appears in Vedic Kundali and its Rashi report. It is not added to KP chart or significator tables.',
 '## Available Vedic reports',
 'Use the available strength, Ashtakavarga, dasha and other report selections. Some specialised views need calculation before their report is ready; let the preparation finish.',
 '## Keep the chart method clear',
 'Vedic Prediction uses the Vedic D1 ascendant and classical planet house placements. KP Event Promise and cusp/sub-lord analysis use their own KP rules. Check the selected tab before comparing results.',
 'The Vedic source predictions are Marathi. If a source-backed translation is unavailable in the selected language, the software marks it unavailable rather than silently mixing prose from another language.'
])
page('5 · Prediction and language',[
 'Open <b>Prediction</b>. The common <b>Language</b> selector near the top changes the language for all Prediction tabs and their previews. It stays synchronized with Astrologer settings.',
 '## Choose the right prediction tab',
 'Use <b>Vedic Prediction</b> for the Vedic natal reading. Use <b>Marriage Points</b> and <b>Event House Rules</b> to inspect matches against their supplied rules. Use <b>Eighth Cusp Rules</b> for the added eighth-cusp analysis.',
 'The matching views distinguish a complete rule match from a condition that still needs review. Do not read an unverified aspect or compound condition as a confirmed result.',
 '## Childbirth worksheet',
 'The separate Childbirth tab and Child Gender A4 worksheet preserve the supplied traditional checks. Available male/female checks are counted; blanks do not receive votes. A tie remains a tie.',
 'Edit <b>My opinion</b> and <b>Actual outcome</b> before printing when you want those notes in the worksheet. These traditional checks do not determine fetal sex or establish medical facts.',
 '## Previews',
 'Use the tab’s Preview or A4 control. In-app previews provide Zoom +, Zoom −, Fit, Print / Save PDF and Close where available. Zoom changes the view; it does not change the prediction.'
])
page('6 · Event Promise and exact rules',[
 'Open <b>Event Promise</b> and select the event. Review its houses and chosen significator method before interpreting the result.',
 'The event list has no leading event numbers, which makes keyboard searching easier. Type or select the event name.',
 '## Read the rule basis',
 'Uploaded Event House Rules require a complete listed house group for an exact match. Extra planet, sign, aspect or cusp conditions must also be defined and satisfied before treating a source rule as confirmed.',
 'Other Event Promise categories may use the displayed majority-match convention. The exact-match rule views and a majority support assessment serve different checks; read the stated basis.',
 '## DBA support',
 'The DBA support cells display <b>Event is promised</b> or <b>Event is not promised</b> in the selected language. This label refers to the software’s selected house-support test.',
 'Inspect the detailed matching/missing evidence when reviewing why a period qualified. A positive house-support result is an astrological indication, not a guaranteed real-world outcome.',
 '## Marriage checks',
 'Use Marriage Points for the supplied marriage conditions. Its prediction view shows fully matched conditions; unresolved conditions remain for review rather than being presented as exact matches.',
 'When comparing periods, keep the same chart, event and significator method. Changing any of these can change the support result.'
])
page('7 · Configure Ruling Planets',[
 'Open <b>Astrologer settings → Ruling Planets</b>. Save to apply changes; Cancel discards the current settings edits.',
 '<b>Show Sub Lord / Show Sub-sub Lord:</b> controls the extra live RP table columns.',
 '<b>Include retrograde planets in RP:</b> when off, an actually retrograde non-node planet is excluded from RP selection. Rahu and Ketu keep normal eligibility without R markers.',
 '<b>Don’t show RP in retrograde star:</b> excludes a candidate whose star lord is retrograde. <b>Retrograde sub:</b> checks its sub lord. <b>Retrograde star and sub:</b> excludes a candidate only when both are retrograde.',
 'The three lord filters combine. For example, enabling the Star filter already excludes every retrograde-star candidate, whether or not its sub lord is also retrograde. Rahu/Ketu themselves do not count as retrograde triggers.',
 '<b>Node Aspected / Aspecting / Conjunction columns:</b> show the node evidence table. Whole-sign Vedic aspect rules follow the existing Ketu-aspect option; conjunction uses the configured conjunction orb.',
 '<b>Consider Day from Sunrise:</b> uses the sunrise-based day lord. When off, the day changes at local civil midnight.',
 '<b>Hora calculated from Sunrise:</b> uses twelve unequal hours for daytime and twelve for night. When off, equal hours start at local civil midnight with that weekday’s lord. The RP panel states the basis.',
 '<b>Real-time update interval:</b> controls live RP refresh frequency. Use 1 minute for a less frequently updating display, or choose a shorter interval when observing changes.'
])
page('8 · Find RP timing intervals',[
 'Open <b>Tools → Ruling Planet</b>. The RP event-time finder opens with the current consultation time and saved astrologer location.',
 '<b>1.</b> Check Query / RP local time. Use Now to return to the current consultation context.',
 '<b>2.</b> Choose the event. Relevant houses now combines the event’s primary and supporting houses. For example, <b>Higher ambitions = 1, 10</b>. The field remains editable.',
 '<b>3.</b> Review the selected ruling planets. Excluded planets follow your saved RP retrograde filters.',
 '<b>4.</b> Choose the horizon and timing planet. Ascendant is for short searches; Moon, Sun and Jupiter provide progressively broader searches. The tool restricts Ascendant searches to short horizons.',
 '<b>5.</b> Choose Sign AND star AND sub in RP, or Star AND sub in RP. Optionally require all MD / AD / PD event support and retain RP signifying event houses.',
 '<b>6.</b> Open Location &amp; timing method to check Place, Latitude, Longitude and UTC offset. The India lookup has its own row, separate from the coordinate inputs.',
 '<b>7.</b> Select Find matching times. Use Cancel to stop a long search. Narrow time refines a result inside the earlier interval.',
 '## Preview and export',
 'A4 Preview / Print opens an in-app report. Use Zoom +, Zoom −, Fit and Close. Print / Save PDF uses the browser print dialog. CSV becomes available when results exist.',
 'Results are candidate intervals. Entry is inclusive; Exit is exclusive. A wide horizon is useful for screening, then shorter searches refine timing.'
])
page('9 · Find transit dates with DBA',[
 'Open the <b>Find transit dates</b> workflow for the selected event. Check that the event and natal chart are correct.',
 'The three methods are <b>Event significators</b>, <b>DBA through each other</b> and <b>Sun through DBA</b>. Use each method separately. Event significators uses only the Transit Reader rule; the other two methods retain their separately labelled DBA-chain calculations.',
 '<b>1.</b> Start with current DBA, or choose MD, AD and PD manually.',
 '<b>2.</b> Check the date range and search method. Choosing a method does not automatically start a search.',
 '<b>3.</b> For Event significators, the moving planet, nakshatra lord and sub lord must all be event significators. Rashi and transit-house positions are not conditions. No ruling-planet or additional Sun/Moon/Jupiter/Saturn gate is applied.',
 '<b>3a.</b> Start the search. Manual DBA and historical date choices are retained. Unchecked planets and checked planets that are not event significators are excluded.',
 '<b>4.</b> Review matching intervals, the event-house evidence and the period lords. Use the preview to inspect and print the result.',
 '## Automatic Horary results sheet',
 'Select the query and theory, then update results. Enter the question and opinion/result notes before generating the A4 single-page report.',
 '## Transit charts and Panchang',
 'Use Transit Chart for an enlarged chart preview that follows the on-screen design. Check the selected date, location and natal/transit cusp basis.',
 'Transit Panchang is calculated for the displayed time and place. Review its available calculations and stated conventions before using a timing window.'
])
page('10 · Gemstone guidance',[
 'Open <b>Gemstone Guidance</b>. Choose KP event-based or Vedic rules. Under KP, select a purpose and check the relevant houses.',
 'The KP rule ranks eligible planets by the number of unique relevant event houses in their significators. A blocked planet is not recommended, even if its score is high. Eligible ties can share the highest rank.',
 'Houses <b>6, 8 and 12</b> normally block a recommendation, with the confirmed exceptions below. <b>House 8 always blocks.</b>',
 'The exception allows that house; it does not guarantee a recommendation. Another blocking house can still exclude the planet.',
 'The Vedic rule remains a separate sign-lord method. The KP purpose exceptions do not change the Vedic method.',
 'Use the displayed rule and evidence as traditional astrological guidance. Do not substitute gemstones for medical treatment or financial due diligence.'
], [['Purpose','Allowed exception'],['Wealth, promotion, transfer, job-interview success, lottery gains','House 6 allowed; houses 8 and 12 still block.'],['Acquiring a home, foreign travel, education abroad','House 12 allowed; houses 6 and 8 still block.'],['All other purposes','Houses 6, 8 and 12 block.']])
page('11 · Preview, print and export A4',[
 'Open <b>Print report</b>. Select the report pages you want. Some Vedic reports prepare their calculations before preview; wait until they are ready.',
 '<b>Preview:</b> inspect the selected pages first. Long reports continue onto additional A4 sheets. Evidence details expand into normal flowing text, so the complete evidence remains inside its card.',
 '<b>Print:</b> opens the selected-report preview and browser print dialog. Choose <b>A4, portrait</b>. Check the paper size, scale and page range in the print preview. Turn browser headers/footers off if you do not want the URL or browser date.',
 '<b>Export to PDF:</b> creates the selected-report PDF directly. Long sections are divided across pages; continuation pages receive their own border.',
 '## Borders and tables',
 'The print layout repeats a page frame on continuation sheets. Tables retain borders and repeat header rows where supported. Chart blocks retain their aspect ratio.',
 'RP A4 previews have their own visible paper and table borders. Their preview zoom controls do not change the printed scale.',
 '## Cover photos',
 'Use the existing report cover-photo control, or select a photo from Report Photos in Astrologer settings. The redundant Report photo library button has been removed.',
 'If output differs between a browser printer and direct PDF export, inspect both previews before sharing the report. Save a PDF copy with the chart record.'
])
page('12 · Backup, settings and help',[
 '## Connect the software folder',
 'Astrologer settings → Astrologer Info → Choose software folder connects the extracted folder. <b>Kundali Backup</b> stores chart backups; <b>Report Photos</b> stores cover photos.',
 'Use Save current kundali, Restore selected, Add photos to folder and Use selected photo. Browsers can ask for folder access. If folder access is unavailable, use Download Backup, Restore File and Choose Photo.',
 'Copy the Kundali Backup folder to another device or drive regularly. Browser storage alone is not an independent backup.',
 '## Personalise the interface',
 'Home is the first shortcut. Display settings let you choose which shortcut icons appear. Themes provides colour choices; Aspects provides the existing Vedic and Western orb controls. Save applies your changes.',
 'Startup branding and the About portrait are publisher-controlled. Customer photo selection is only for report covers.',
 '## Common fixes',
 '<b>No result:</b> complete the chart, check the event houses, date range and filters. A strict RP match can legitimately return no interval.',
 '<b>Popup blocked:</b> allow the browser’s report preview when requested. Use an in-app preview where offered. For the tutorial, use Download PDF if the built-in PDF viewer is unavailable.',
 '<b>File will not download:</b> open the software in a full browser, check its Downloads list and allow the requested download. Extract ZIP files before opening index.html.',
 '<b>Unexpected language:</b> use the common Prediction language selector or Astrologer settings; avoid leaving an old preview open after changing language.',
 '## Keep this guide',
 'Open Help → Software tutorial to view or download this PDF. It is bundled with the extracted software and embedded in index.html for offline access.'
])
def frame(canvas,doc):
 canvas.saveState();w,h=A4;canvas.setStrokeColor(colors.HexColor('#355b7b'));canvas.setLineWidth(.7);canvas.rect(12*mm,12*mm,w-24*mm,h-24*mm);canvas.setFont('Guide',8);canvas.setFillColor(colors.HexColor('#526b7e'));canvas.drawString(20*mm,h-19*mm,'KP MASTER 1.2.10 · Software tutorial');canvas.drawRightString(w-20*mm,17*mm,f'{doc.page} / {len(pages)}');canvas.restoreState()
story=[]
for i,items in enumerate(pages):
 if i:story.append(PageBreak())
 story.extend(items)
(ROOT/'docs').mkdir(exist_ok=True)
SimpleDocTemplate(str(ROOT/'docs/KP-MASTER-User-Tutorial-1.2.10.pdf'),pagesize=A4,leftMargin=22*mm,rightMargin=22*mm,topMargin=28*mm,bottomMargin=25*mm,title='KP MASTER 1.2.10 — Software tutorial',author='KP MASTER',invariant=1).build(story,onFirstPage=frame,onLaterPages=frame)
print('Built tutorial PDF:',len(pages),'planned pages')
