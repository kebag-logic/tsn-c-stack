#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare the mapper plant table in docs/ENTITY_YAML.md with MAPPER_PLANTS.

Usage: python3 -I check_plant_table.py CLONE
"""
import ast
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
tree = ast.parse((root / 'scripts/entity_selftest.py').read_text())
plants = next(ast.literal_eval(n.value) for n in tree.body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'MAPPER_PLANTS')
rows = {}
for line in (root / 'docs/ENTITY_YAML.md').read_text().splitlines():
    m = re.fullmatch(r'\| `([a-z-]+)` \| (.+) \| `(test_[a-z_]+)` \|', line)
    if m and m[3].startswith(('test_mapping', 'test_ax7101')):
        rows[m[1]] = m[3]
doc = {k: v for k, v in rows.items()}
code = {k: v[2] for k, v in plants.items()}
print('registry plants:', len(code), 'doc rows:', len(doc))
for k in sorted(set(code) | set(doc)):
    print(('OK  ' if code.get(k) == doc.get(k) else 'DIFF'), k, code.get(k), doc.get(k))
sys.exit(0 if code == doc and len(code) == 13 else 1)
