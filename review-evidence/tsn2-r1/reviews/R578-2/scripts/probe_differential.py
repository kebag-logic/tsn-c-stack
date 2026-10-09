#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Differential probe: source builder scalar/MAC parsers vs scripts/milan_entity.py.

Usage: probe_differential.py <tsn-c-stack checkout> <milan-fpga endstation_builder.py>

Extracts HEX_TEXT, MAC_OCTETS, _hex_text and _mac48 verbatim from the pinned
source builder and compares accept/refuse and value with the mapper for a fixed
corpus plus a seeded random corpus. Then probes source-valid entity keys and
loader behaviour through project(). Exit 0 iff no scalar or MAC divergence.
"""
import ast
import copy
import json
import random
import re
import sys
from pathlib import Path

repo, builder = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / 'scripts'))
from entity_yaml import Invalid, Loader  # noqa: E402
import milan_entity  # noqa: E402
import yaml  # noqa: E402

src = builder.read_text()
tree = ast.parse(src)
wanted = {'HEX_TEXT', 'MAC_OCTETS', 'MAC48_MAX', 'EUI64_MAX', '_hex_text', '_mac48'}
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) in wanted for t in node.targets):
        nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in wanted:
        nodes.append(node)


class ConfigError(Exception):
    pass


ns = {'re': re, 'Any': object, 'ConfigError': ConfigError}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(builder), 'exec'), ns)
found = sorted(k for k in wanted if k in ns)
print('extracted from source:', found)
assert set(found) == wanted, found


def source_hex(v, bits):
    try:
        return ('ok', ns['_hex_text'](v, bits, 'f', 'x'))
    except ConfigError:
        return ('refused', None)


def mapper_hex(v, bits):
    try:
        return ('ok', milan_entity.hex_text(v, bits, 'f'))
    except Invalid:
        return ('refused', None)


def source_mac(v):
    try:
        return ('ok', ns['_mac48'](v, 'm'))
    except ConfigError:
        return ('refused', None)


def mapper_mac(v):
    try:
        return ('ok', int(milan_entity.station_mac(v).replace(':', ''), 16))
    except Invalid:
        return ('refused', None)


fixed = [1, 0, True, False, 1.0, None, [], {}, b'12', '', '0x', '0X', 'x1', '0x0x1', '1', '01', '0001',
         '1234567890123456', '020000FFFE000001', '0x020000FFFE000001', '0X1', '0b1', '0o7', '_1', '1_', '1__2',
         '0x_1', '+1', '-1', ' 1', '1 ', '1\n', '\t1', 'G', 'g', '１２', '١', '1:2', '1-2', '1.0', '1e3',
         'FFFFFFFFFFFFFFFF', '0FFFFFFFFFFFFFFFF', '1' * 17, '0' * 16 + '1', '0x' + '_'.join('0' * 16 + '1'),
         '0x' + '_'.join('F' * 16), 'ff_ff', 'Ff', '0x00', '0' * 6, '0' * 7, 'FEFFFF', '010000', '0' * 8,
         'deadbeef', 'DEADBEEF0', '1​', 'ß', 'Ａ', '0xG']
rng = random.Random(20261009)
alphabet = '0123456789abcdefABCDEFxX_ -+:G\n'
fuzz = [''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 20))) for _ in range(20000)]
fuzz += [('0x' if rng.random() < .5 else '') + '_'.join(rng.choice('0123456789abcdefABCDEF') for _ in range(rng.randint(1, 18)))
         for _ in range(20000)]

divergent = 0
checked = 0
for bits in (24, 32, 48, 64):
    for v in fixed + fuzz:
        a, b = source_hex(v, bits), mapper_hex(v, bits)
        checked += 1
        if a != b:
            divergent += 1
            if divergent <= 20:
                print(f'HEX DIVERGENCE bits={bits} value={v!r} source={a} mapper={b}')
print(f'hex scalar cases: {checked}, divergent: {divergent}')

macs = fixed + fuzz + ['02:00:00:00:00:01', '02-00-00-00-00-01', '02:00-00:00:00:01', '020000000001', '0x020000000001',
                       '0X02_0000_000001', '02000000001', '0020000000001', '00:00:00:00:00:00', '01:00:00:00:00:01',
                       '03-00-00-00-00-01', '02:00:00:00:00:1', '2:00:00:00:00:01', '02::00:00:00:00:01',
                       '0a:BC:de:F0:12:34', '0A-bc-DE-f0-12-34', '02.00.00.00.00.01', '0x02:00:00:00:00:01',
                       '0200_0000_0001', '02_00_00_00_00_01', '0000000000000', 'FEFFFFFFFFFF', 'FFFFFFFFFFFF']
for _ in range(20000):
    sep = rng.choice([':', '-', ':', '-', '.', '_', ''])
    macs.append(sep.join(''.join(rng.choice('0123456789abcdefABCDEF') for _ in range(2)) for _ in range(6)))
mdiv = 0
for v in macs:
    a, b = source_mac(v), mapper_mac(v)
    if a != b:
        mdiv += 1
        if mdiv <= 20:
            print(f'MAC DIVERGENCE value={v!r} source={a} mapper={b}')
print(f'mac cases: {len(macs)}, divergent: {mdiv}')

# Entity-key behaviour through project(): source-valid keys and loader forms.
fx = json.loads((repo / 'configs/compat/ax7101.json').read_text())
MID, CAPS = fx['expected_adp']['entity_model_id'], fx['expected_adp']['entity_capabilities']


def project(label, mutate, source_view):
    doc = copy.deepcopy(fx['input'])
    mutate(doc)
    try:
        out = milan_entity.project(doc, MID, CAPS)
        res = 'ACCEPTED identity=' + json.dumps(out['identity'], default=str)
    except Invalid as e:
        res = 'REFUSED: ' + str(e)
    print(f'{label}\n  source builder: {source_view}\n  mapper: {res}')


project('E1 entity.firmware_rev: 1 (source-valid optional key, builder line 3727)',
        lambda d: d['entity'].__setitem__('firmware_rev', 1), 'valid (respin revision; AEM firmware_version only)')
project('E2 entity.firmware_rev: 0 (source default value stated explicitly)',
        lambda d: d['entity'].__setitem__('firmware_rev', 0), 'valid')
project('E3 entity.firmware_version: "1.0.0" (source refuses)',
        lambda d: d['entity'].__setitem__('firmware_version', '1.0.0'), 'refused: firmware_version derived from gateware')
project('E4 entity.locale: "en" (source-valid)',
        lambda d: d['entity'].__setitem__('locale', 'en'), 'valid')
project('E5 entity.locale: 5 (source refuses: non-empty string)',
        lambda d: d['entity'].__setitem__('locale', 5), 'refused by _aem_string')
project('E6 entity.vendor_name: null (explicit null)',
        lambda d: d['entity'].__setitem__('vendor_name', None), 'accepted by ent.get (value None); documented: null does not request a default')
project('E7 entity_id "0" (source accepts; portable range 1..2^64-2)',
        lambda d: d['entity'].__setitem__('entity_id', '0'), 'valid _fmt64')
project('E8 entity_id "FFFFFFFFFFFFFFFF"',
        lambda d: d['entity'].__setitem__('entity_id', 'FFFFFFFFFFFFFFFF'), 'valid _fmt64')
project('E9 entity_id "MAC-DERIVED" (case variant)',
        lambda d: d['entity'].__setitem__('entity_id', 'MAC-DERIVED'), 'refused by _fmt64 (not hex)')
project('E10 entity_model_id "HASH-DERIVED" (case variant)',
        lambda d: d['entity'].__setitem__('entity_model_id', 'HASH-DERIVED'), 'refused by _model_id (not hex)')
project('E11 name 64 ASCII bytes', lambda d: d['entity'].__setitem__('name', 'A' * 64), 'refused: exceeds 63 bytes')

# YAML loader forms: source uses yaml.safe_load; mapper uses entity_yaml.Loader.
for label, text in (('Y1 unquoted 0x1234 entity_id', 'entity_id: 0x1234\n'),
                    ('Y2 unquoted 1_000 entity_id', 'entity_id: 1_000\n'),
                    ('Y3 unquoted 020000FFFE000001', 'entity_id: 020000FFFE000001\n'),
                    ('Y4 unquoted 1234567890123456', 'entity_id: 1234567890123456\n'),
                    ('Y5 unquoted 0123', 'entity_id: 0123\n'),
                    ('Y6 unquoted 1e3', 'entity_id: 1e3\n'),
                    ('Y7 unquoted 12:34', 'entity_id: 12:34\n')):
    s = yaml.safe_load(text)['entity_id']
    m = yaml.load(text, Loader=Loader)['entity_id']
    print(f'{label}: safe_load -> {type(s).__name__} {s!r}; mapper Loader -> {type(m).__name__} {m!r}; same={s == m and type(s) is type(m)}')

sys.exit(1 if divergent or mdiv else 0)
