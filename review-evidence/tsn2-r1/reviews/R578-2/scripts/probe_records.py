#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Probe requirement_records at the reviewed head (read-only).
Usage: probe_records.py <tsn-c-stack checkout>
R1 a record added to requirements.json with no REQUIREMENTS.md row is refused;
R2 the ENTITY-01 row removed from REQUIREMENTS.md text is refused;
R3 ENTITY-01 with a wrong origin / missing origin / non-test method is refused;
R4 the unplanted head passes validate() and check_document()."""
import copy, json, re, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
import requirement_records as rr
reqs = json.loads((root / 'docs/requirements.json').read_text())
cat = rr.load()
text = (root / 'docs/REQUIREMENTS.md').read_text()
print('R4 head validate:', rr.validate(reqs, cat), 'check_document:', rr.check_document(reqs, cat))
added = copy.deepcopy(reqs) + [dict(id='ZZZ-01', text='planted', clauses=reqs[0].get('clauses', []))]
print('R1 added record documented():', rr.documented(added, text))
print('R1 added record check_document():', rr.check_document(added, cat))
planted = re.sub(r'^\|\s*<a id="entity-01"></a>ENTITY-01\s*\|[^\n]*\n', '', text, flags=re.M)
print('R2 removed ENTITY-01 row documented():', rr.documented(reqs, planted))
i = next(k for k, r in enumerate(reqs) if r['id'] == 'ENTITY-01')
for label, f in (('wrong origin', lambda r: r.update(origin='tsn-c-stack issue 3')),
                 ('missing origin', lambda r: r.pop('origin')),
                 ('port obligation', lambda r: r['verification'].update(method='port obligation')),
                 ('one target', lambda r: r.update(targets=['Linux']))):
    r = copy.deepcopy(reqs); f(r[i]); print('R3', label, '->', rr.validate(r, cat))
