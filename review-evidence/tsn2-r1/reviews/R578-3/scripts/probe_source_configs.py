#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Project each pinned milan-fpga end-station config through the mapper.
Usage: probe_source_configs.py <tsn-c-stack checkout> <dir with source configs>
Model ID: the stated pin, else the stated literal, else a placeholder with the
Kebag OUI (hash-derived configs need the full builder to resolve). Capabilities 0xC588."""
import sys
from pathlib import Path
root, configs = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(root / 'scripts'))
from entity_yaml import Invalid, load
import milan_entity
for path in sorted(configs.glob('*.yaml')):
    doc = load(path)
    ent = doc.get('entity', {})
    stated = ent.get('model_id_pin', ent.get('entity_model_id'))
    mid = milan_entity.hex_text(stated, 64, 'probe') if stated != 'hash-derived' else 0x001BC50000000001
    try:
        out = milan_entity.project(doc, mid, 0xC588)
        print(f'{path.name}: ACCEPTED entity keys={sorted(ent)} mac={out["interfaces"][0]["mac"]} inputs={len(out["inputs"])} outputs={len(out["outputs"])} entity_id={out["identity"]["entity_id"]}')
    except Invalid as e:
        print(f'{path.name}: REFUSED {e} (entity keys={sorted(ent)})')
