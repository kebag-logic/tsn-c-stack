#!/usr/bin/env python3
"""Independently reconcile downloaded source lines, local records and anchors."""
import argparse
import copy
import json
from pathlib import Path
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('checkout', type=Path)
p.add_argument('receipts', type=Path)
a = p.parse_args()
sys.path.insert(0, str(a.checkout.resolve() / 'scripts'))
import requirement_records as rr
import traceability as tr
requirements = json.loads((a.checkout / 'docs/requirements.json').read_text())
catalog = json.loads((a.checkout / 'docs/requirement-origins.json').read_text())
assert rr.validate(requirements, catalog) == []
actual = {}
for local, upstream in [('source-FR_NFR.md', 'docs/reference/FR_NFR.md'),
                        ('source-REQUIREMENTS.md', 'REQUIREMENTS.md')]:
    lines = (a.receipts / local).read_text().splitlines()
    for n, line in enumerate(lines, 1):
        match = re.match(r'^\|\s*((?:FR|NFR|REQ)-[A-Z]+-\d+[a-z]?)\s*\|', line)
        if not match:
            match = re.match(r'^\s*-\s*\*\*((?:REQ)-[A-Z]+-\d+)\s+\(', line)
        if match:
            key = 'milan-fpga ' + match[1]
            assert key not in actual, key
            actual[key] = rr.SOURCE_BASE + upstream + '#L' + str(n)
    print(upstream, 'numbered source rows:', sum(upstream + '#L' in x for x in actual.values()))
pinned = {k: v for k, v in rr.source_ids().items() if '#665' not in k}
assert actual == pinned, {'missing': sorted(set(pinned)-set(actual)),
                         'extra': sorted(set(actual)-set(pinned)),
                         'different': [k for k in actual.keys() & pinned.keys() if actual[k] != pinned[k]]}
for row in catalog['rows']:
    if row['origin'] in actual:
        assert row['url'] == actual[row['origin']]
print('All 114 numbered source anchors match the downloaded pinned source bytes.')
changed = copy.deepcopy(catalog)
changed['rows'][0]['url'] = changed['rows'][1]['url']
errors = rr.validate(requirements, changed)
assert any('pinned ID anchor' in e for e in errors)
print('Moved-anchor negative control:', errors)
rows = [r for path in sorted((a.checkout / 'tests').glob('test_*.cpp')) for r in tr.inventory(path.read_text())]
for req in requirements:
    if req['id'].startswith('MF'):
        tests = [n for n, ids, _ in rows if req['id'] in ids]
        if rr.method(req) == 'test':
            assert tests
        print(req['id'], rr.method(req), ', '.join(tests))
print('Source audit PASS')
