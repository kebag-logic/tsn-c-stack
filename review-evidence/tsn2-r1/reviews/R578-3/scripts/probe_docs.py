#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check docs/ENTITY_YAML.md mapper-plant table against the MAPPER_PLANTS registry.
Usage: probe_docs.py <tsn-c-stack tree>"""
import re
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))
import entity_selftest as s  # noqa: E402
doc = (root / 'docs/ENTITY_YAML.md').read_text()
rows = dict(re.findall(r'^\| `([a-z-]+)` \| [^|]+ \| `(test_\w+)` \|$', doc, re.M))
reg = {k: v[2] for k, v in s.MAPPER_PLANTS.items()}
print('doc rows', len(rows), 'registry', len(reg), 'equal', rows == reg)
for k in sorted(set(rows) | set(reg)):
    if rows.get(k) != reg.get(k):
        print('MISMATCH', k, rows.get(k), reg.get(k))
tests = {n for n in dir(s.EntityTests) if n.startswith('test_')}
print('all killers exist', all(v in tests for v in reg.values()), 'test count', len(tests))
print('doc states 13:', '13 mapper plants' in doc, '13 registered mapper plants' in (root / 'docs/VERIFICATION.md').read_text())
sys.exit(0 if rows == reg and len(reg) == 13 else 1)
