#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare the documented mapper plant table with MAPPER_PLANTS.

Usage: table_vs_plants.py REPO_ROOT
"""
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
src = (root / 'scripts/entity_selftest.py').read_text()
tree = ast.parse(src)
plants = None
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'MAPPER_PLANTS':
        plants = {k.value: v.elts[2].value for k, v in zip(node.value.keys, node.value.values)}
lines = (root / 'docs/ENTITY_YAML.md').read_text().splitlines()
i = next(n for n, l in enumerate(lines) if l.startswith('| Plant | Planted defect |')) + 2
doc = {}
while lines[i].startswith('|'):
    cells = [c.strip().strip('`') for c in lines[i].split('|')[1:-1]]
    doc[cells[0]] = cells[2]
    i += 1
print('code plants:', len(plants), 'doc rows:', len(doc))
print('same order:', list(plants) == list(doc))
print('same name->killer mapping:', plants == doc)
sys.exit(0 if plants == doc and list(plants) == list(doc) else 1)
