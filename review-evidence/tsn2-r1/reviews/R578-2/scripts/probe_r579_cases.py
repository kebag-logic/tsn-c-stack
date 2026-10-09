#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Re-check the six R579-1-F1 source-valid scalar cases at the reviewed head.
Usage: probe_r579_cases.py <tsn-c-stack checkout>"""
import copy, json, sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / 'scripts'))
from entity_yaml import Invalid, validate
from milan_entity import project
fx = json.loads((root / 'configs/compat/ax7101.json').read_text())
MID, CAPS = fx['expected_adp']['entity_model_id'], fx['expected_adp']['entity_capabilities']
cases = [('entity_id', '1234567890', 'entity_id', 0x0000001234567890),
         ('entity_id', '020000FFFE000001', 'entity_id', 0x020000FFFE000001),
         ('entity_model_id', '001BC5C1935893E1', 'model_id', MID),
         ('model_id_pin', '001BC5C1935893E1', 'model_id', MID),
         ('vendor_oui', '0x001BC5', 'model_id', MID),
         ('entity_capabilities', '0x0000C588', 'flags', CAPS)]
bad = 0
for field, value, key, want in cases:
    doc = copy.deepcopy(fx['input']); doc['entity'][field] = value
    try:
        got = validate(project(doc, MID, CAPS))[key]; ok = got == want
        print(f'{field}={value!r}: {key}=0x{got:016X} expected 0x{want:016X} {"OK" if ok else "MISMATCH"}')
    except Invalid as e:
        ok = False; print(f'{field}={value!r}: REFUSED {e}')
    bad += not ok
sys.exit(bad)
