#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Differential probe: pinned source _load_entity firmware rule vs scripts/milan_entity.py.

Usage: probe_firmware_rev.py <tsn-c-stack tree> <milan-fpga endstation_builder.py> <milan_csr.sv>

Extracts the firmware_version refusal, the firmware_rev read and check, and the
63-byte cstr64 check verbatim from the pinned source _load_entity (AST), renders
firmware_version with the pinned RTL VERSION parameter, and compares
accept/refuse with project() over a YAML-text corpus loaded by each side's own
loader (source: yaml.safe_load; mapper: entity_yaml.Loader). Also checks that an
accepted firmware_rev leaves the whole projection identical to the golden
ax7101 mapping, and that every unknown key is refused by its own name.
Exit 0 iff the only divergences are the documented class 'BOUND' (decimal
revisions too long for the derived 63-byte string, which the mapper cannot
evaluate without the gateware VERSION).
"""
import ast
import copy
import json
import re
import sys
from pathlib import Path

import yaml

repo, builder, csr = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(repo / 'scripts'))
import entity_yaml  # noqa: E402
from entity_yaml import Invalid  # noqa: E402
import milan_entity  # noqa: E402

v = int(re.search(r"parameter\s+logic\s*\[31:0\]\s*VERSION\s*=\s*32'h([0-9A-Fa-f_]+)", csr.read_text())[1].replace('_', ''), 16)
MAJOR, MINOR = v >> 16 & 0xFFFF, v & 0xFFFF
print(f'pinned RTL VERSION 0x{v:08X} -> firmware_version prefix "{MAJOR}.{MINOR}."')

fn = next(n for n in ast.parse(builder.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == '_load_entity')
seg = []
for stmt in fn.body:
    text = ast.unparse(stmt)
    if text.startswith("if 'firmware_version' in ent") or text.startswith("rev = ent.get('firmware_rev'") \
            or text.startswith('if isinstance(rev, bool)'):
        seg.append(stmt)
assert len(seg) == 3, [ast.unparse(s)[:60] for s in seg]
print('extracted source statements:')
for s in seg:
    print('  ' + ast.unparse(s).splitlines()[0])
body = seg + ast.parse("fw = f'{MAJOR}.{MINOR}.{int(rev)}'\n"
                       "if len(str(fw).encode()) > 63:\n    raise ConfigError('entity.firmware_version: exceeds 63 bytes (AEM cstr64)')\n"
                       "return rev").body
src_fn = ast.FunctionDef(name='source_rule', args=ast.arguments(posonlyargs=[], args=[ast.arg('ent')], kwonlyargs=[], kw_defaults=[], defaults=[]),
                         body=body, decorator_list=[], returns=None, type_params=[])
mod = ast.fix_missing_locations(ast.Module(body=[src_fn], type_ignores=[]))


class ConfigError(Exception):
    pass


ns = {'ConfigError': ConfigError, 'MAJOR': MAJOR, 'MINOR': MINOR, 'rtl_firmware_version': lambda rev=0: f'{MAJOR}.{MINOR}.{int(rev)}'}
exec(compile(mod, str(builder), 'exec'), ns)

fx = json.loads((repo / 'configs/compat/ax7101.json').read_text())
MID, CAPS = fx['expected_adp']['entity_model_id'], fx['expected_adp']['entity_capabilities']
golden = entity_yaml.load(repo / 'configs/ax7101.yaml')

corpus = [None, '0', '1', '2', '00', '007', '0x10', '0o17', '0b101', '1_000', '+5', '-0', '-1', '1:30', '1.0', '1e3', '.inf',
          'true', 'false', 'yes', 'on', 'null', '~', '"1"', "'0'", '[]', '{}', '[1]', '9223372036854775807', '18446744073709551616',
          '1' + '0' * 57, '9' * 58, '1' + '0' * 58, '9' * 59, '1' + '0' * 80, '0x' + 'F' * 64]
rows, div, bound = [], 0, 0
for text in corpus:
    if text is None:
        src_ent, map_ent = {}, {}
        label = '(omitted)'
    else:
        doc = f'firmware_rev: {text}\n'
        src_ent = yaml.safe_load(doc)
        map_ent = yaml.load(doc, Loader=entity_yaml.Loader)
        label = text if len(text) < 24 else text[:10] + f'...({len(text)} chars)'
    try:
        s = ('accept', ns['source_rule'](src_ent))
    except ConfigError as e:
        s = ('refuse', str(e)[:60])
    d = copy.deepcopy(fx['input'])
    d['entity'].update(map_ent)
    try:
        out = milan_entity.project(d, MID, CAPS)
        m = ('accept', 'projection == golden' if out == golden else 'PROJECTION CHANGED')
    except Invalid as e:
        m = ('refuse', str(e))
    same = s[0] == m[0] and (m[0] == 'refuse' or m[1] == 'projection == golden')
    cls = 'same'
    if not same:
        if s[0] == 'refuse' and 'exceeds 63 bytes' in s[1] and m[0] == 'accept':
            cls, bound = 'BOUND', bound + 1
        else:
            cls, div = 'DIVERGENT', div + 1
    print(f'{cls:9} firmware_rev: {label:28} source={s[0]:6} mapper={m[0]:6} {m[1] if m[0] == "refuse" else m[1]}')

# firmware_version precedence and unknown-key naming.
for extra, want in (({'firmware_version': '2.96.0'}, 'milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev'),
                    ({'firmware_version': '2.96.0', 'firmware_rev': 1}, 'milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev'),
                    ({'zz_typo': 1}, 'milan.entity.zz_typo: unknown field'),
                    ({'Name': 'x'}, 'milan.entity.Name: unknown field'),
                    ({'firmware_revision': 1}, 'milan.entity.firmware_revision: unknown field'),
                    ({'b': 1, 'a': 2}, 'milan.entity.a: unknown field'),
                    ({'model_id': 1}, 'milan.entity.model_id: unknown field')):
    d = copy.deepcopy(fx['input'])
    d['entity'].update(extra)
    try:
        milan_entity.project(d, MID, CAPS)
        got = 'ACCEPTED'
    except Invalid as e:
        got = str(e)
    ok = got == want
    div += not ok
    print(f'{"same" if ok else "DIVERGENT":9} keys {sorted(extra)} -> {got}')
print(f'divergent: {div}; bound-class (59+ decimal digits with prefix "{MAJOR}.{MINOR}."): {bound}')
sys.exit(1 if div else 0)
