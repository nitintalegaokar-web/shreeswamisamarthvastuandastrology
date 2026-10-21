"""Package the review HTML only; native 1.2.11 releases are left unchanged."""
from pathlib import Path
import zipfile,hashlib,json,datetime
root=Path(__file__).resolve().parents[1];source=(root/'index.html').read_bytes()
manifest={'kind':'HTML testing build','builtAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':hashlib.sha256(source).hexdigest(),'nativeInstallersRebuilt':False,'manualData':json.loads((root/'vendor/transit/manual-tool-source.json').read_text())}
readme='''KP MASTER — HTML TESTING BUILD

Extract this ZIP completely, then open index.html in current Chrome or Edge.
Everything needed by this HTML is embedded; keep your existing saved-chart backups.
Windows installers and Android APKs have not been rebuilt for this testing update.

WHAT TO CHECK
Significators: Four-fold uses the first nonempty A, B, C or D level only. Six-fold uses the same priority through E and F. Lower levels are ignored even when the chosen level does not match the event houses.
1. Open Transits -> Manually Search Transit. Current MD / AD / PD appear first.
2. Dasha, Bhukti and Antara are linked to the native timeline. Changing a parent rebuilds valid child periods.
3. Sookshma has None / Blank. Blank uses the selected full Antara/PD dates and MD/AD/PD target planets only. Choosing Sookshma uses that child's dates.
4. Cusp, Search event and Event remain available on every transit tab. The chosen event is included in the manual report. Use event selects its significators under Of Planet(s).
5. Tick Sign / Star / Sub for the moving planets and select Of Planet(s). All checked levels must match for each moving planet. Manual dates can include past years.
6. Manual results use daily 05:30 IST samples from 1900–2500, not exact intraday entry/exit times. Graha longitudes come from your supplied file; KP lords are derived from these longitudes by the existing engine. Outer planets use Astronomy Engine aligned to the supplied Sun.
7. The compact manual tool follows your selected theme colours. Compute, then Print A4 to open the in-app report preview.
8. On Home or the chart tab, right-click a chart and choose North Indian. KP Cusp Chart is stacked above Lagna Chart, using the active natal or horary model. Right-click South Indian to switch back.

TESTING-MANIFEST.json identifies this HTML and the supplied source data.
'''
out=root/'KP-MASTER-HTML-Testing.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('KP-MASTER/index.html',source);z.writestr('KP-MASTER/START-HERE.txt',readme);z.writestr('KP-MASTER/TESTING-MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:assert z.testzip() is None;assert hashlib.sha256(z.read('KP-MASTER/index.html')).hexdigest()==manifest['sourceSHA256']
print(json.dumps({'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
