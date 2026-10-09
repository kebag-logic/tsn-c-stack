#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Probe scripts/milan_entity.py with milan-fpga 1.2.0 inputs the pinned builder accepts.
Usage: probe_mapper.py <tsn-c-stack checkout> <milan-fpga endstation_builder.py>"""
import copy, json, re, sys
from pathlib import Path
repo, builder = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / 'scripts'))
from entity_yaml import Invalid
from milan_entity import project
src = builder.read_text()
HEX_TEXT = re.compile(re.search(r'^HEX_TEXT = re\.compile\(r"(.*)"\)$', src, re.M).group(1))
MAC_OCTETS = re.compile(re.search(r'^MAC_OCTETS = re\.compile\(r"(.*)"\)$', src, re.M).group(1))
def builder_hex(v):
    m = HEX_TEXT.fullmatch(v); assert m, v
    return int(m[1].replace('_', ''), 16)
fx = json.loads((repo / 'configs/compat/ax7101.json').read_text())
MID, CAPS = fx['expected_adp']['entity_model_id'], fx['expected_adp']['entity_capabilities']
def run(label, mutate, builder_view):
    doc = copy.deepcopy(fx['input']); mutate(doc)
    try:
        out = project(doc, MID, CAPS); res = 'ACCEPTED entity_id=0x%016X' % out['identity']['entity_id'] if isinstance(out['identity']['entity_id'], int) else 'ACCEPTED entity_id=%s' % out['identity']['entity_id']
    except Invalid as e:
        res = 'REFUSED: ' + str(e)
    print(f'{label}\n  builder view: {builder_view}\n  mapper: {res}')
run('P1 explicit entity_id "1234567890123456" (digit-only hex text)', lambda d: d['entity'].__setitem__('entity_id', '1234567890123456'),
    'valid, entity_id=0x%016X' % builder_hex('1234567890123456'))
run('P2 explicit entity_id "020000FFFE000001" (hex text without 0x)', lambda d: d['entity'].__setitem__('entity_id', '020000FFFE000001'),
    'valid, entity_id=0x%016X' % builder_hex('020000FFFE000001'))
run('P3 vendor_oui "0x001BC5" (agrees with resolved model ID)', lambda d: d['entity'].__setitem__('vendor_oui', '0x001BC5'),
    'valid, oui=0x%06X; resolved model OUI=0x%06X' % (builder_hex('0x001BC5'), MID >> 40))
run('P4 entity_capabilities "0x0000C588" (agrees with resolved caps)', lambda d: d['entity'].__setitem__('entity_capabilities', '0x0000C588'),
    'valid, caps=0x%08X; resolved=0x%08X' % (builder_hex('0x0000C588'), CAPS))
run('P5 vendor_name omitted (builder default "Kebag Logic")', lambda d: d['entity'].pop('vendor_name'), 'valid (ent.get default)')
run('P6 group_name omitted (builder default "")', lambda d: d['entity'].pop('group_name'), 'valid (ent.get default)')
run('P7 entity_id omitted (builder default mac-derived)', lambda d: d['entity'].pop('entity_id'), 'valid (ent.get default)')
run('P8 platform.mac_address "02-00-00-00-00-01"', lambda d: d['platform'].__setitem__('mac_address', '02-00-00-00-00-01'),
    'valid MAC_OCTETS match=%s' % bool(MAC_OCTETS.fullmatch('02-00-00-00-00-01')))
run('P9 vendor_oui integer 1 (the selftest plant; builder refuses unquoted)', lambda d: d['entity'].__setitem__('vendor_oui', 1), 'invalid: quote the hexadecimal value')
run('P10 entity_capabilities integer 1 (the selftest plant)', lambda d: d['entity'].__setitem__('entity_capabilities', 1), 'invalid: quote the hexadecimal value')
