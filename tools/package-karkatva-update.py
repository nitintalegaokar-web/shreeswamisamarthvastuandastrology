"""Package the self-contained HTML and public backend data; never include licence keys or native build directories."""
from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[1];out=root/'KP-MASTER-Karkatva-Vedic-1.2.8.zip'
readme='''KP MASTER — updated HTML 1.2.8 (18 October 2026)

Extract this ZIP and open index.html in Chrome or Edge.

Changes:
- Help now includes a bundled, offline 12-page English A4 tutorial with view/open/download controls. Vedic Kundali has an English/Marathi symbol legend, limited to its own chart/report.
- RP settings include independent retrograde-star, retrograde-sub and combined filters, node evidence columns, sunrise/civil day and hora choices. RP preview has zoom and print borders.
- Report evidence details expand into normal flow before preview/printing; page frames repeat on printed continuation pages and exported PDFs.
- Astrologer Settings > Ruling Planets includes an Include retrograde planets switch. It filters the live RP list and timing finder; Rahu/Ketu retain their normal eligibility and omit the R marker.
- KP gemstone guidance applies confirmed event-specific house 6 and 12 exceptions; house 8 always blocks recommendations.
- Western aspect colour legends use English or Marathi on screen and in reports.
- Ruling Planet timing: relevant houses combine primary and supporting houses; location inputs and India lookup use separate responsive rows.
- The redundant Report photo library button is removed; report photo controls remain in Astrologer Settings.
- Fixes repeated Marathi label updates in the North Indian transit chart.
- Enlarged transit charts retain the colours, fonts, aspect ratio and labels of the on-screen chart.
- Predictions no longer show Jyotish source filenames or line-number references.
- Click a Bhava number for concise standard English/Marathi meanings.
- Click a planet for the supplied Planet Karkatva fields.
- South Indian chart sign headings are removed. Click the Rashi entry in a planetary or cuspal position table for its Karkatva popup.
- Rashi labels/sign numbers in Transit and North Indian charts also open the same popup.
- English, Marathi and bilingual modes are supported in these reference popups.
- Cancer uses the exact text supplied separately by the user. The duplicate Gemini is retained in source provenance, not shown twice.
- Prediction > Vedic Prediction: Marathi source excerpts selected by the Vedic D1 ascendant and seven classical planets' whole-sign houses.
- Undefined auspicious/inauspicious yoga conditions are stored as references, not automatically asserted as confirmed natal matches.
- Vedic predictions show source-backed positive and negative bullet points, without the old introduction.
- Prediction prose follows the selected software language only; missing translations are marked unavailable instead of falling back to another language. The uploaded Vedic source is Marathi.
- Ascendant / Moon transitions are available only with a ready natal chart, never Instant Prashna or Horary.
- Event Promise uses an explicit majority-match convention (more than half a required group), retaining exclusions and marking partial support provisional.
- Longevity choices compare the same supporting/adverse groups, showing the strongest category and mixed support; this is not a confirmed lifespan.
- Separate Childbirth prediction tab: first/second/third child cusps, matching traditional conditions, language-specific text and horary-only delivery reference. Ambiguous or conflicting medical/sex/survival formulas remain review-only; the exact supplied tables are retained in data/childbirth-2026-10-18/.
- Childbirth > Child Gender A4: a separate printable worksheet with seven RP posts, cusp/sub-sub chains, horary-number parity, joint-ruler table, Prashna dasha and editable opinion/outcome. Comparison counts available Male/Female checks equally, excludes blanks, shows the majority or a clear tie/unavailable result; the editable opinion prints on A4. This is a traditional worksheet indication, not fetal-sex determination.
- DBA Event house support cells show only Event is promised / Event is not promised in the selected language; calculation rules remain unchanged.
- Fixed Horary/current DBA checks for supplied events: complete matched/missing proof lists, with cusp-specific rules kept separate from period house support. Horary and Find Transit Dates previews now open inside the app with zoom, fit, print/PDF and close controls.
- Fortuna: click its chart label or position summary for the supplied interpretation of its exact occupied house; English/Marathi, natal/transit cusp boundaries, rotation-independent popup and mobile/dark styling.
- Childbirth and Child Gender previews open in an in-app modal, with visible Zoom +, Zoom -, Fit, Print/PDF and Close controls; no separate-window permission required.
- Basic, Four-fold, Six-fold, Four-step and Nadi Significators: planet names and individual house numbers open their corresponding significations. Rashi and Nakshatra entries also open popups wherever those columns are present. Click a nakshatra name for lord, deity, symbol, gana, zodiac span, themes and pada information (27 English/Marathi entries).
- Prediction > Eighth Cusp Rules: all 40 supplied English/Marathi rules, explicit KP occupied-house/sign checks and existing aspect/benefic/fourfold logic where applicable. Unclear compound rules remain for review. Preview includes Zoom +, Zoom -, Fit, Print/PDF and Close.
- Uploaded event tables: 168 English and 157 Marathi rows preserved independently; Prediction > Event House Rules and Event Promise share the event, cusp, groups and assessment. Unparsed planet/sign qualifiers and missing primary cusps remain for review.
- Home is the first shortcut. Display settings can show/hide each shortcut. Startup opens Home after the fixed-branding splash. Customer-facing startup logo and About-photo selectors are removed, and previous customer branding overrides are ignored.
- Kundali Backup/ and Report Photos/ are included as separate folders. Astrologer Info > Choose software folder connects them; Save current kundali, Restore selected, Add photos to folder and Use selected photo use those folders. Folder access depends on browser support; Download Backup, Restore File and Choose Photo are available as alternatives.
- The duplicate Catalogue language control is removed. Prediction has a common quick Language selector, synchronized with Astrologer Settings and used by all Prediction tabs and previews.
- About uses the publisher-bundled portrait only, without customer photo selection; the layout preserves its proportions.
- Astrologer Settings redesigned: searchable sections, RP sub/sub-sub columns and refresh interval, significator column choices, collapsible Vedic/Western panels, DMS orb editors, supported layout presets, theme swatches/HEX/preview, sticky Save/Cancel and mobile settings navigation. Existing unsupported calculation presets/retrograde filters are not presented as functional controls.
- Transit search: all three methods show an expanded DBA selector and start at current MD/AD/PD. Manual DBA and date selections are respected when scanning; method selection does not start a search automatically.
- Marriage Points and Event House Rules prediction views show only fully matched conditions. Uploaded event groups require all houses; unresolved extra conditions remain review-only.
- Marriage Points: 19 supplied points, existing KP signification/aspect checks, original source grid and 12 spouse-appearance references. Ten relevant marriage point checks are also selectable in Event Promise.
- Original planetary calculations and restored matchmaking rules remain unchanged.

The root HTML is self-contained. data/, vendor/ and tools/ contain the backend source data, translations, reproducible import/sync tools and browser regression harness.
This ZIP contains HTML/source only. Updated Windows installers are separate downloads. Android APK upgrades require the original private Android signing files.
'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(root/'index.html','index.html');z.writestr('READ-ME.txt',readme)
 for folder in ['docs','data','vendor','tools','Kundali Backup','Report Photos','App Logo']:
  for p in sorted((root/folder).rglob('*')):
   if p.is_file() and p.relative_to(root).as_posix()!='vendor/panchang/toolkit-engine.js' and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,str(p.relative_to(root)))
 for name in ['karkatva.test.cjs','vedic-natal-predictions.test.cjs','prediction-language.test.cjs','event-support.test.cjs','childbirth.test.cjs','child-gender-sheet.test.cjs','fortuna-interpretation.test.cjs','nakshatra-karkatva.test.cjs','eighth-cusp-rules.test.cjs','event-house-rules.test.cjs','marriage-points.test.cjs','horary-dba.test.cjs','settings-easy.test.cjs','gemstone-event-ranking.test.cjs','live-ruling.test.cjs']:z.write(root/'desktop/test'/name,'desktop/test/'+name)
with zipfile.ZipFile(out) as z:
 assert z.read('index.html')==(root/'index.html').read_bytes()
 assert 'data/rashi-karkatva-2026-10-18/Cancer-supplied.txt' in z.namelist()
 assert z.testzip() is None
meta={'version':'1.2.8','file':out.name,'size':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'nativeBinariesRebuilt':False}
(root/'KP-MASTER-Karkatva-Vedic-1.2.8.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta))
