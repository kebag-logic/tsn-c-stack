#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Map each pinned source end-station config with the head mapper.

Usage: python3 -I probe_five_configs.py TSN_CHECKOUT CFG.yaml...
The model ID passed is the pin, else the literal, else an arbitrary valid value
(hash-derived models are resolved by the source builder, not the mapper).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts'))
import entity_yaml
import milan_entity

ok = True
for path in sys.argv[2:]:
    doc = entity_yaml.load(path)
    ent = doc['entity']
    raw = ent.get('model_id_pin', ent['entity_model_id'])
    mid = 0x001BC5C1935893E1 if raw == 'hash-derived' else int(raw.replace('_', ''), 16)
    for rev in (None, 3):
        if rev is not None:
            doc['entity']['firmware_rev'] = rev
        try:
            out = milan_entity.project(doc, mid, 0xC588)
            print(f'MAPPED {Path(path).name} firmware_rev={rev}: {len(out["inputs"])} inputs, {len(out["outputs"])} outputs, model 0x{out["identity"]["model_id"]:016X}')
        except entity_yaml.Invalid as error:
            ok = False
            print(f'REFUSED {Path(path).name} firmware_rev={rev}: {error}')
print('five-config probe:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
