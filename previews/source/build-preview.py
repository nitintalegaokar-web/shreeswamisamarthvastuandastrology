from pathlib import Path
import base64
root=Path(__file__).resolve().parents[2]
s=(root/'Remedy.html').read_text()
s=s.replace("astroRemedies_v10_bw_dualprint","astroRemedies_a5_design_preview_v1")
s=s.replace('<title>Shree Swami Samarth Vastu & Astrology Consultancy</title>','<title>Swami Samarth | Booking & A5 Print Preview</title>')
s=s.replace('</head>','<style>'+(root/'previews/source/booking-preview.css').read_text()+'</style></head>',1)
s=s.replace('<div class="nav-active"><span>▦</span> Remedy Library</div>','''<nav class="bk-nav" aria-label="Workspace"><button id="bkNavRemedies" onclick="showConsultancyPage('remedies')"><span>▤</span>Remedy Library <b class="bk-count">209</b></button><button id="bkNavBookings" class="active" onclick="showConsultancyPage('bookings')"><span>▦</span>Matrugaya Bookings</button></nav>''')
s=s.replace('''  <!-- Modal: Add/Edit Remedy -->''',(root/'previews/source/booking-preview-markup.html').read_text()+'''\n  <!-- Modal: Add/Edit Remedy -->''',1)
s=s.replace('</body>','<script>'+(root/'previews/source/booking-preview.js').read_text()+'</script></body>',1)
s=s.replace('>↗ Print list<','>Print A5 list<').replace('>Print list<','>Print A5 list<')
s=s.replace('</head>','<style>'+(root/'previews/source/settings.css').read_text()+'</style></head>',1)
s=s.replace('</body>',(root/'previews/source/settings.html').read_text()+'<script>'+(root/'previews/source/settings.js').read_text()+'</script></body>',1)
excel_library=(root/'previews/source/vendor/exceljs.min.js').read_text().replace('</script','<\\/script')
s=s.replace('</body>','<script>'+excel_library+'</script><script>'+(root/'previews/source/booking-excel.js').read_text()+'</script></body>',1)
for module in ['crm','finance','billing']:
 s=s.replace('</head>','<style>'+(root/('previews/source/'+module+'.css')).read_text()+'</style></head>',1)
 s=s.replace('</body>',(root/('previews/source/'+module+'.html')).read_text()+'<script>'+(root/('previews/source/'+module+'.js')).read_text()+'</script></body>',1)
logo_data='data:image/png;base64,'  +base64.b64encode((root/'previews/source/branding/software-logo.png').read_bytes()).decode('ascii')
s=s.replace('</head>','<link rel="icon" type="image/png" sizes="512x512" href="'+logo_data+'"><link rel="apple-touch-icon" href="'+logo_data+'"><style>.brand-symbol{border:0!important;flex-shrink:0;width:64px!important;height:64px!important}.brand-symbol img{display:block;width:64px;height:64px;border-radius:9px;object-fit:contain}</style></head>',1)
s=s.replace('<div class="brand-symbol">✧</div>','<div class="brand-symbol"><img src="'+logo_data+'" alt="Shree Swami Samarth logo"></div>',1)
(root/'previews'/'consultancy-preview.html').write_text(s)
print('Created separate combined preview. Production Remedy.html and installer untouched.')
