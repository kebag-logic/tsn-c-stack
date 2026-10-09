#!/usr/bin/env python3
"""Probe: does the mapper accept a source-valid entity.firmware_rev?

Usage: probe_firmware_rev.py <dir with milan_entity.py and entity_yaml.py> <AX7101 source yaml> <builder.py>
Prints the builder's own entity.firmware_rev rule and the mapper's outcome
for the pinned AX7101 source with and without `firmware_rev: 1`.
"""
import copy, re, sys
sys.path.insert(0, sys.argv[1])
import yaml
import milan_entity
from entity_yaml import Invalid

src = yaml.safe_load(open(sys.argv[2], encoding='utf-8'))
builder = open(sys.argv[3], encoding='utf-8').read()
rule = [l.strip() for l in builder.splitlines() if 'firmware_rev' in l]
print('builder lines naming firmware_rev:')
for l in rule:
    print('  ' + l)
ok = True
for label, rev in (('without firmware_rev', None), ('firmware_rev: 1', 1), ('firmware_rev: 0', 0)):
    doc = copy.deepcopy(src)
    if rev is not None:
        doc['entity']['firmware_rev'] = rev
    try:
        out = milan_entity.project(doc, 0x001BC5C1935893E1, 0xC588)
        print(f'{label}: ACCEPTED entity_id={out["identity"]["entity_id"]}')
    except Invalid as e:
        print(f'{label}: REFUSED: {e}')
        if rev is not None:
            ok = False
print('FIRMWARE_REV_SOURCE_VALID_ACCEPTED', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
