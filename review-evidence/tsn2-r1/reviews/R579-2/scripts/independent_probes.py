#!/usr/bin/env python3
"""Compare scalar parsing against isolated functions from the public source pin."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

p = argparse.ArgumentParser()
p.add_argument('repo', type=Path)
p.add_argument('authority', type=Path)
a = p.parse_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(a.repo / 'scripts'))
import entity_yaml as entity
import milan_entity as mapper
import requirement_records as records

text = (a.authority / 'endstation_builder.py').read_text()
tree = ast.parse(text)
names = {'HEX_TEXT', 'MAC_OCTETS', '_hex_text', '_eui64', '_model_id', '_mac48'}
nodes = [n for n in tree.body if
         (isinstance(n, ast.FunctionDef) and n.name in names) or
         (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets))]
class ConfigError(ValueError):
    pass
ns = dict(re=re, Any=object, ConfigError=ConfigError, EUI64_MAX=(1 << 64)-1, MAC48_MAX=(1 << 48)-1)
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pinned scalar functions>', 'exec'), ns)

def outcome(fn, *args):
    try:
        return ('value', fn(*args))
    except (ValueError, TypeError) as error:
        return ('refused', type(error).__name__)

comparisons = 0
for bits in (24, 32, 64):
    width = bits // 4
    values = [None, True, False, 0, 1, 1.0, [], {}, '', '0x', '+1', '-1',
              ' 1', '1 ', '1\n', '0x_1', '_1', '1_', '1__2', '１２', '1:2',
              'G1', '0'*width+'1', 'F'*(width+1), '1234567890123456', '020000FFFE000001']
    for digits in ('0', '1', '123', 'F'*width, '0'*(width-1)+'1'):
        for prefix in ('', '0x', '0X'):
            values += [prefix+digits, prefix+'_'.join(digits), prefix+digits.lower()]
    for value in values:
        old = outcome(ns['_hex_text'], value, bits, 'field', 'hex')
        new = outcome(mapper.hex_text, value, bits, 'field')
        assert old[0] == new[0] and (old[0] != 'value' or old[1] == new[1]), (bits, value, old, new)
        comparisons += 1
print('SOURCE_HEX_PARITY', comparisons, 'PASS')

mac_values = ['02:00:00:00:00:01', '02-00-00-00-00-01', 'FE-DC-BA-98-76-54',
              '02-00:00-00-00-01', '020000000001', '0x02_0000_000001', '0X020000000001',
              '000000000000', '010000000001', '02000000001', '0020000000001',
              '02:00:00:00:00:01\n', '0x_020000000001', 2199023255553, None, True]
for value in mac_values:
    old = outcome(ns['_mac48'], value, 'mac')
    new = outcome(mapper.station_mac, value)
    assert old[0] == new[0], (value, old, new)
    if old[0] == 'value':
        assert old[1] == int(new[1].replace(':', ''), 16)
print('SOURCE_MAC_PARITY', len(mac_values), 'PASS')

fixture = json.loads((a.repo/'configs/compat/ax7101.json').read_text())
source_path = a.authority / 'endstation_ax7101_1x1_tdm8.yaml'
raw = source_path.read_bytes()
assert len(raw) == fixture['source_bytes']
assert hashlib.sha256(raw).hexdigest() == fixture['source_sha256']
source = entity.load(source_path)
for key, value in fixture['input'].items():
    assert source[key] == value, key
expected = fixture['expected_adp']
def project(doc):
    return mapper.project(doc, expected['entity_model_id'], expected['entity_capabilities'])
assert project(source) == entity.load(a.repo/'configs/ax7101.yaml')
for scalar, number in [('1234567890123456', 0x1234567890123456), ('020000FFFE000001', 0x020000FFFE000001)]:
    doc = copy.deepcopy(source)
    doc['entity']['entity_id'] = scalar
    result = project(doc)
    assert entity.validate(result)['entity_id'] == number
    rendered = entity.render(result)['entity_config.c']
    assert rendered.count(f'.entity_id = UINT64_C(0x{number:016x})') == 2
    print('IDENTITY', scalar, f'0x{number:016X}', 'ADP_ACMP_PASS')
doc = copy.deepcopy(source)
for key in ('entity_id', 'vendor_name', 'group_name'):
    del doc['entity'][key]
doc['platform']['mac_address'] = '02-00-00-00-00-01'
result = project(doc)
assert result['identity']['vendor_name'] == 'Kebag Logic'
assert result['identity']['group_name'] == ''
assert entity.validate(result)['entity_id'] == 0x020000FFFE000001
print('COMBINED_DEFAULTS_AND_HYPHEN_MAC PASS')

reqs = json.loads((a.repo/'docs/requirements.json').read_text())
document = (a.repo/'docs/REQUIREMENTS.md').read_text()
assert records.documented(reqs, document) == []
planted = re.sub(r'^.*<a id="entity-01".*\n', '', document, flags=re.M)
assert records.documented(reqs, planted) == ['requirement missing from REQUIREMENTS.md: ENTITY-01']
added = reqs + [{'id':'REVIEW-NEW-01'}]
assert records.documented(added, document) == ['requirement missing from REQUIREMENTS.md: REVIEW-NEW-01']
print('REQUIREMENT_MISSING_EXISTING_AND_NEW_ROW PASS')
print('INDEPENDENT_PROBES PASS')
