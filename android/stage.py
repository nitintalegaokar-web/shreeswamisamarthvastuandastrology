from pathlib import Path
root=Path(__file__).resolve().parent
source=(root.parent/'downloads/Swami-Samarth-HTML/index.html').read_text()
assert 'billPreviewDialog' in source and 'whatsapp://send' in source
source=source.replace('<head>','<head><script>'+(root/'compat.js').read_text()+(root/'theme-init.js').read_text()+'</script>',1)
source=source.replace('</head>','<style>'+ (root/'mobile.css').read_text()+(root/'theme.css').read_text()+'</style></head>',1)
source=source.replace('</body>','<script>'+ (root/'mobile.js').read_text()+(root/'theme.js').read_text()+'</script></body>',1)
source=source.replace('on this computer.','on this phone.').replace('must be installed on this computer','must be installed on this phone')
source=source.replace('Excel report downloaded. Open it in Excel and choose Print; A5 landscape is already set.','Choose a folder and save the Excel report. Open it in Excel to print.')
source=source.replace('Customer Excel report exported.','Choose where to save the customer Excel report.').replace('Excel summary and transaction detail sheets exported.','Choose where to save the Excel workbook.')
target=root/'build/assets';target.mkdir(parents=True,exist_ok=True)
(target/'index.html').write_text(source)
(target/'THIRD-PARTY-NOTICES.txt').write_bytes((root.parent/'previews/source/vendor/THIRD-PARTY-NOTICES.txt').read_bytes())
print('Android mobile HTML staged, with existing data keys and remedies.')
