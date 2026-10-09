#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare the pinned milan-fpga numbered rows with docs/requirement-origins.json and check every line anchor.

Usage: source_inventory_check.py REPO FR_NFR.md REQUIREMENTS.md
FR_NFR.md and REQUIREMENTS.md must be the files at the commit pinned in requirement-origins.json.
Exit status 0 only when the inventory is complete and every #L anchor lands on its own row.
"""
import json
import re
import sys
from pathlib import Path

repo, fr_path, req_path = map(Path, sys.argv[1:4])
files = {'docs/reference/FR_NFR.md': fr_path.read_text().splitlines(),
         'REQUIREMENTS.md': req_path.read_text().splitlines()}
ident = r'(?:FR|NFR|REQ)-[A-Z]+-[0-9]+[a-z]?'
defined = set()
for lines in files.values():
    for line in lines:
        m = re.match(r'^(?:\|\s*|- \*\*)(' + ident + r')\b', line)
        if m:
            defined.add('milan-fpga ' + m[1])
catalog = json.loads((repo / 'docs/requirement-origins.json').read_text())
rows = catalog['rows']
listed = {r['origin'] for r in rows if '#665' not in r['origin']}
errors = []
if listed != defined:
    errors.append(f'missing {sorted(defined - listed)} unknown {sorted(listed - defined)}')
pin = catalog['source_commit']
for r in rows:
    if '#665' in r['origin']:
        continue
    m = re.fullmatch(r'https://github.com/kebag-logic/milan-fpga/blob/([0-9a-f]{40})/(\S+)#L(\d+)', r['url'])
    if not m or m[1] != pin or m[2] not in files:
        errors.append('bad url ' + r['origin'])
        continue
    line = files[m[2]][int(m[3]) - 1]
    rid = r['origin'].split(' ', 1)[1]
    if not re.match(r'^(?:\|\s*|- \*\*)' + re.escape(rid) + r'\b', line):
        errors.append(f'anchor {r["origin"]} L{m[3]} lands on: {line[:60]}')
print(f'pinned commit {pin}')
print(f'numbered source rows defined: {len(defined)}; dispositioned: {len(listed)}; decision rows: {len(rows) - len(listed)}')
print(f'line anchors checked: {len(listed)}; errors: {len(errors)}')
print('\n'.join(errors))
sys.exit(1 if errors else 0)
