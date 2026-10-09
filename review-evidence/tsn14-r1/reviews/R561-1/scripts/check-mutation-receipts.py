#!/usr/bin/env python3
"""Independently inspect the eleven new plants' assertion XML."""
import collections
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

work = Path(sys.argv[1])
rows = json.loads((work / 'results.json').read_text())
assert len(rows) == len({r['name'] for r in rows}) == 322
assert all(r['status'] == 'CAUGHT' for r in rows)
print('campaign:', dict(collections.Counter(r['status'] for r in rows)))
new = [r for r in rows if r['name'].startswith('adp-config-')]
assert len(new) == 11
for record in new:
    assert record['rc'] == 1
    files = list((work / record['name']).glob('*.xml'))
    assert len(files) == 1
    xml = ET.parse(files[0]).getroot()
    tests = xml.findall('.//testcase')
    target = [t for t in tests if t.get('name') == 'AdvertisementFieldsMatchCaller' and t.get('classname') == 'AdpCore']
    assert len(target) == 1
    failures = target[0].findall('failure')
    assert failures
    assert any('advertisement bytes match the independent entity vector' in (f.text or '') for f in failures)
    assert target[0].get('status') == 'run'
    print(record['name'], 'rc=1; named vector assertion failed; XML present')
print('eleven field defects independently confirmed from assertion XML: PASS')
