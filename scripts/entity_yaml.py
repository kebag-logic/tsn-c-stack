#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate entity schema 1.0.0 and emit freestanding C configuration."""
import argparse
from pathlib import Path
import re
import sys

import yaml

VERSION = '1.0.0'
ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ('listener', 'talker', 'duplex', 'ax7101')
POOL_BASE = 0x91E0F0000000
POOL_END = POOL_BASE + 0xFE00
SPDX = '// SPDX-License-Identifier: MIT\n'


class Invalid(ValueError):
    """An input cannot describe a supported static entity."""


class Loader(yaml.SafeLoader):
    """Refuse aliases and duplicate keys instead of hiding declarations."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise Invalid('yaml: aliases are unsupported')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise Invalid('yaml: mapping keys must be strings')
            if key in result:
                raise Invalid(f'yaml: duplicate field {key}')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load(path):
    try:
        return yaml.load(Path(path).read_text(encoding='utf-8'), Loader=Loader)
    except (yaml.YAMLError, UnicodeError) as error:
        raise Invalid('yaml: invalid document') from error


def mapping(value, fields, path):
    if not isinstance(value, dict):
        raise Invalid(f'{path}: expected a mapping')
    for key in value:
        if key not in fields:
            raise Invalid(f'{path}.{key}: unknown field')
    for key in fields:
        if key not in value:
            raise Invalid(f'{path}.{key}: required field missing')
    return value


def integer(value, low, high, path):
    if type(value) is not int or not low <= value <= high:
        raise Invalid(f'{path}: expected integer in {low}..{high}')
    return value


def sequence(value, low, high, path):
    if not isinstance(value, list) or not low <= len(value) <= high:
        raise Invalid(f'{path}: expected list with {low}..{high} entries')
    return value


def name(value, path):
    if not isinstance(value, str):
        raise Invalid(f'{path}: expected UTF-8 string of 0..64 bytes without controls')
    try:
        valid = len(value.encode('utf-8')) <= 64 and all(ord(c) >= 32 and not 127 <= ord(c) <= 159 for c in value)
    except UnicodeError:
        valid = False
    if not valid:
        raise Invalid(f'{path}: expected UTF-8 string of 0..64 bytes without controls')
    return value


def mac(value, path):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', value):
        raise Invalid(f'{path}: expected six colon-separated hexadecimal octets')
    result = int(value.replace(':', ''), 16)
    if result == 0 or result & (1 << 40):
        raise Invalid(f'{path}: expected nonzero unicast MAC')
    return result


def validate(document):
    d = mapping(document, ('schema_version', 'identity', 'capabilities', 'interfaces', 'inputs', 'outputs', 'maap'), 'entity')
    if d['schema_version'] != VERSION:
        raise Invalid('entity.schema_version: supported version is 1.0.0')
    identity = mapping(d['identity'], ('entity_id', 'model_id', 'name', 'vendor_name', 'serial_number', 'group_name'), 'identity')
    for field in ('name', 'vendor_name', 'serial_number', 'group_name'):
        name(identity[field], 'identity.' + field)
    model_id = integer(identity['model_id'], 1, (1 << 64) - 2, 'identity.model_id')
    interfaces = sequence(d['interfaces'], 1, 4, 'interfaces')
    macs = []
    for index, interface in enumerate(interfaces):
        path = f'interfaces[{index}]'
        mapping(interface, ('mac',), path)
        address = mac(interface['mac'], path + '.mac')
        if address in macs:
            raise Invalid(path + '.mac: duplicate MAC')
        macs.append(address)
    eid = identity['entity_id']
    if eid == 'mac-derived':
        eid = ((macs[0] >> 24) << 40) | (0xFFFE << 24) | (macs[0] & 0xFFFFFF)
    else:
        eid = integer(eid, 1, (1 << 64) - 2, 'identity.entity_id')
    caps = mapping(d['capabilities'], ('entity', 'identify_control_index'), 'capabilities')
    flags = integer(caps['entity'], 0, 0x03FFFFFF, 'capabilities.entity')
    if flags & 0xC588 != 0xC588 or flags & 0x73000:
        raise Invalid('capabilities.entity: requires Milan flags 0xC588 and clears 0x73000')
    identify = integer(caps['identify_control_index'], 0, 65535, 'capabilities.identify_control_index')
    streams = {}
    stream_caps = {}
    for direction in ('inputs', 'outputs'):
        rows = sequence(d[direction], 0, 16, direction)
        stream_caps[direction] = 1 if rows else 0
        streams[direction] = []
        for index, row in enumerate(rows):
            path = f'{direction}[{index}]'
            mapping(row, ('name', 'interface', 'kind'), path)
            name(row['name'], path + '.name')
            port = integer(row['interface'], 0, len(macs) - 1, path + '.interface')
            if row['kind'] not in ('audio', 'clock'):
                raise Invalid(path + '.kind: expected audio or clock')
            stream_caps[direction] |= 0x4000 if row['kind'] == 'audio' else 0x0800
            streams[direction].append(port)
    counts = [streams['outputs'].count(i) for i in range(len(macs))]
    reservations = sequence(d['maap'], 0, len(macs), 'maap')
    preferred = [0] * len(macs)
    seen = set()
    for index, row in enumerate(reservations):
        path = f'maap[{index}]'
        mapping(row, ('interface', 'preferred'), path)
        port = integer(row['interface'], 0, len(macs) - 1, path + '.interface')
        if port in seen:
            raise Invalid(path + '.interface: duplicate reservation')
        if not counts[port]:
            raise Invalid(path + '.interface: has no outputs')
        seen.add(port)
        base = integer(row['preferred'], 0, (1 << 48) - 1, path + '.preferred')
        if base and not POOL_BASE <= base <= POOL_END - counts[port]:
            raise Invalid(path + '.preferred: complete range must be in the MAAP dynamic pool')
        preferred[port] = base
    if seen != {i for i, count in enumerate(counts) if count}:
        raise Invalid('maap: exactly one reservation is required per output interface')
    return dict(identity=identity, entity_id=eid, model_id=model_id, macs=macs, flags=flags,
                identify=identify, streams=streams, stream_caps=stream_caps, counts=counts, preferred=preferred)


def cstring(value):
    return '"' + ''.join(f'\\{b:03o}' for b in value.encode('utf-8')) + '"'


def render(document, prefix='entity'):
    if not re.fullmatch(r'[a-z][a-z0-9_]*', prefix):
        raise Invalid('prefix: expected a lower-case C identifier')
    d = validate(document)
    upper = prefix.upper()
    guard = upper + '_ENTITY_CONFIG_V1_0_0_H'
    n = len(d['macs'])
    h = SPDX + f'''#ifndef {guard}
#define {guard}

#include "adp.h"
#include "acmp.h"

#define {upper}_ENTITY_SCHEMA_VERSION 0x010000u

#ifdef __cplusplus
extern "C" {{
#endif

struct {prefix}_identity {{
    char name[65];
    char vendor_name[65];
    char serial_number[65];
    char group_name[65];
}};

// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4
struct {prefix}_maap_config {{
    unsigned interface;
    uint64_t mac;
    uint16_t count;
    uint64_t preferred;
}};

extern const struct {prefix}_identity {prefix}_identity;
extern const struct adp_entity {prefix}_adp[{n}];
extern const struct acmp_config {prefix}_acmp;
extern const struct {prefix}_maap_config {prefix}_maap[{n}];

#ifdef __cplusplus
}}
#endif

#endif
'''
    c = SPDX + '#include "entity_config.h"\n\n'
    c += f'_Static_assert({upper}_ENTITY_SCHEMA_VERSION == 0x010000u, "entity schema version mismatch");\n'
    for macro, count in (('ACMP_MAX_INTERFACES', n), ('ACMP_MAX_SINKS', len(d['streams']['inputs'])), ('ACMP_MAX_SOURCES', len(d['streams']['outputs']))):
        c += f'_Static_assert({macro} >= {count}u, "entity capacity mismatch");\n'
    c += f'\nconst struct {prefix}_identity {prefix}_identity = {{\n'
    for field in ('name', 'vendor_name', 'serial_number', 'group_name'):
        c += f'    .{field} = {cstring(d["identity"][field])},\n'
    c += '};\n\n// IEEE 1722.1-2021 6.2.2; Milan v1.2 5.6.2\n'
    c += f'const struct adp_entity {prefix}_adp[{n}] = {{\n'
    for address in d['macs']:
        c += '    {\n'
        for field, value in (('entity_id', d['entity_id']), ('entity_model_id', d['model_id']), ('mac', address)):
            c += f'        .{field} = UINT64_C(0x{value:016x}),\n'
        for field, value in (('entity_capabilities', d['flags']), ('talker_stream_sources', len(d['streams']['outputs'])), ('talker_capabilities', d['stream_caps']['outputs']), ('listener_stream_sinks', len(d['streams']['inputs'])), ('listener_capabilities', d['stream_caps']['inputs']), ('identify_control_index', d['identify'])):
            c += f'        .{field} = {value}u,\n'
        c += '    },\n'
    c += '};\n\n// Milan v1.2 5.5.3.5.1\n'
    c += f'const struct acmp_config {prefix}_acmp = {{\n    .entity_id = UINT64_C(0x{d["entity_id"]:016x}),\n    .n_interfaces = {n}u,\n'
    c += '    .mac = {' + ', '.join(f'UINT64_C(0x{x:012x})' for x in d['macs']) + '},\n'
    for direction, role in (('inputs', 'sink'), ('outputs', 'source')):
        ports = d['streams'][direction]
        c += f'    .n_{role}s = {len(ports)}u,\n'
        c += f'    .{role}_interface = {{' + ', '.join(f'{x}u' for x in (ports or [0])) + '},\n'
    c += '};\n\n// IEEE 1722-2016 B.3.2; IEEE 1722-2016 B.4\n'
    c += f'const struct {prefix}_maap_config {prefix}_maap[{n}] = {{\n'
    for i in range(n):
        c += f'    {{.interface = {i}u, .mac = UINT64_C(0x{d["macs"][i]:012x}), .count = {d["counts"][i]}u, .preferred = UINT64_C(0x{d["preferred"][i]:012x})}},\n'
    c += '};\n'
    return {'entity_config.h': h, 'entity_config.c': c}


def emit(document, output, prefix='entity', check=False):
    files = render(document, prefix)
    if check:
        for name, contents in files.items():
            path = output / name
            if not path.is_file() or path.read_bytes() != contents.encode('ascii'):
                raise Invalid(f'{prefix}/{name}: generated file drift')
    else:
        output.mkdir(parents=True, exist_ok=True)
        for name, contents in files.items():
            (output / name).write_bytes(contents.encode('ascii'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, nargs='?')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--prefix', default='entity')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--examples', action='store_true')
    args = parser.parse_args()
    try:
        if args.examples:
            if args.input or args.output or args.prefix != 'entity':
                parser.error('--examples cannot be combined with input, output or prefix')
            for persona in PERSONAS:
                emit(load(ROOT / 'configs' / (persona + '.yaml')), ROOT / 'examples/entities' / persona, persona, args.check)
        else:
            if not args.input or not args.output:
                parser.error('input and --output are required')
            emit(load(args.input), args.output, args.prefix, args.check)
    except (Invalid, OSError) as error:
        print('entity_yaml: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
