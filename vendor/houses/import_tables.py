"""Validate and pack the supplied Swiss Placidus workbooks; never recompute cusps."""
from pathlib import Path
import hashlib
import json
import math
import re
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
HEADERS = ['ST HH:MM:SS', 'ST Hours', 'ST Minutes', 'ST Seconds', '10H', '11H', '12H', 'Asc DM', '2H', '3H', '10H 360', '11H 360', '12H 360', 'Asc 360', '2H 360', '3H 360']


SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

def printed_value(text, asc=False):
    match=re.fullmatch(r'([A-Za-z]+) (\d{2})°(?:(\d{2})′)?',text)
    assert match and match[1] in SIGNS, text
    degree=int(match[2]); minute=int(match[3] or 0)
    assert 0<=degree<=30 and 0<=minute<60 and bool(match[3])==asc, text
    return (SIGNS.index(match[1])*30+degree+minute/60)%360

def build():
    tables, printed_tables, sources, duplicate_count = {}, {}, [], 0
    for path in sorted((ROOT / 'source').glob('*.xlsx')):
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheets = []
        for sheet in workbook:
            assert sheet.title.endswith('N'), sheet.title
            latitude = int(sheet.title[:-1])
            assert 0 <= latitude <= 60 and latitude not in tables
            rows = iter(sheet.values)
            assert list(next(rows)) == HEADERS
            packed, printed_packed, previous = [], [], -1
            for row in rows:
                hour, minute, second = row[1:4]
                assert all(type(n) is int for n in (hour, minute, second))
                assert 0 <= hour <= 24 and 0 <= minute < 60 and 0 <= second < 60
                time = hour * 3600 + minute * 60 + second
                assert time <= 86400 and row[0] == f'{hour:02}:{minute:02}:{second:02}'
                values = list(row[10:16])
                printed=[printed_value(text,i==3) for i,text in enumerate(row[4:10])]
                assert len(values) == 6 and all(isinstance(n, (int, float)) and math.isfinite(n) and 0 <= n < 360 for n in values)
                assert time >= previous
                if time == previous:
                    assert values == packed[-1][1:] and printed == printed_packed[-1][1:], (sheet.title, row[0])
                    duplicate_count += 1
                    continue
                packed.append([time, *values]); printed_packed.append([time,*printed])
                previous = time
            assert len(packed) == 361 and packed[0][0] == 0 and packed[-1][0] == 86400
            assert packed[0][1:] == packed[-1][1:]
            for a, b in zip(packed, packed[1:]):
                assert 0 < b[0] - a[0] <= 262
                assert all(0 < (y - x) % 360 < 10 for x, y in zip(a[1:], b[1:]))
            tables[latitude] = packed; printed_tables[latitude] = printed_packed
            sheets.append(sheet.title)
        workbook.close()
        sources.append({'filename': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sheets': sheets})
    assert sorted(tables) == list(range(61))
    times = [r[0] for r in tables[0]]
    assert all([r[0] for r in table] == times for table in tables.values())
    data = {'metadata': {'format': 1, 'latitudeMin': 0, 'latitudeMax': 60, 'latitudeStep': 1, 'houses': [10, 11, 12, 1, 2, 3], 'zodiac': 'tropical', 'sourceColumns': HEADERS[10:16], 'printedSourceColumns': HEADERS[4:10], 'worksheetColumns': 'printed', 'uniqueRows': 61 * 361, 'removedIdenticalDuplicates': duplicate_count, 'sources': sources}, 'printedValues': [[r[1:] for r in printed_tables[lat]] for lat in range(61)], 'times': times, 'values': [[r[1:] for r in tables[lat]] for lat in range(61)]}
    (ROOT / 'tables.json').write_text(json.dumps(data, separators=(',', ':')) + '\n')
    return data


if __name__ == '__main__':
    result = build()
    print(f"Imported {result['metadata']['uniqueRows']:,} unique rows across 61 latitudes; removed {result['metadata']['removedIdenticalDuplicates']} identical boundary duplicates.")
