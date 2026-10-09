#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Project milan-fpga 1.2.0 facts into the portable entity schema."""
import argparse
import copy
from pathlib import Path
import re
import sys

import yaml

from entity_yaml import Invalid, load, mac, validate


def hex_text(value, bits, path):
    if not isinstance(value, str):
        raise Invalid(f'{path}: quote the hexadecimal value as a YAML string')
    match = re.fullmatch(r'(?:0[xX])?([0-9A-Fa-f](?:_?[0-9A-Fa-f])*)', value)
    if not match:
        raise Invalid(f'{path}: expected hexadecimal digits with optional 0x and single underscores between digits; no sign or whitespace')
    digits = match[1].replace('_', '')
    if len(digits) > bits // 4:
        raise Invalid(f'{path}: expected at most {bits // 4} hexadecimal digits ({bits} bits), including leading zeros')
    return int(digits, 16)


def model_identity(value, path):
    number = hex_text(value, 64, path)
    if number in (0, (1 << 64) - 1):
        raise Invalid(f'{path}: model identity must not be zero or all ones')
    return number


def station_mac(value):
    path = 'milan.platform.mac_address'
    if not isinstance(value, str):
        raise Invalid(f'{path}: quote the hexadecimal value as a YAML string')
    if re.fullmatch(r'[0-9A-Fa-f]{2}([:-])[0-9A-Fa-f]{2}(?:\1[0-9A-Fa-f]{2}){4}', value):
        digits = value.replace(':', '').replace('-', '')
    else:
        number = hex_text(value, 48, path)
        digits = re.sub(r'^0[xX]', '', value).replace('_', '')
        if len(digits) != 12:
            raise Invalid(f'{path}: expected exactly 12 hexadecimal digits (48 bits)')
        digits = f'{number:012X}'
    normalized = ':'.join(digits[i:i + 2] for i in range(0, 12, 2))
    mac(normalized, path)
    return normalized


def project(document, model_id, capabilities):
    if not isinstance(document, dict) or document.get('schema') != 'kebag-logic/milan-endstation-config' or document.get('schema_version') != '1.2.0':
        raise Invalid('milan.schema_version: expected kebag-logic/milan-endstation-config 1.2.0')
    try:
        source = document['entity']
        fields = {'entity_id', 'entity_model_id', 'model_id_pin', 'name', 'vendor_name', 'serial_number', 'group_name', 'vendor_oui', 'locale', 'entity_capabilities'}
        if not isinstance(source, dict) or set(source) - fields:
            raise Invalid('milan.entity: unknown field or invalid mapping')
        identity = {key: copy.deepcopy(source[key]) for key in ('name', 'serial_number')}
        identity.update(entity_id=source.get('entity_id', 'mac-derived'),
                        vendor_name=source.get('vendor_name', 'Kebag Logic'),
                        group_name=source.get('group_name', ''))
        if identity['entity_id'] != 'mac-derived':
            identity['entity_id'] = hex_text(identity['entity_id'], 64, 'milan.entity.entity_id')
        raw = source['entity_model_id']
        declared = None if raw == 'hash-derived' else model_identity(raw, 'milan.entity.entity_model_id')
        if 'model_id_pin' in source:
            declared = model_identity(source['model_id_pin'], 'milan.entity.model_id_pin')
        if declared is not None and declared != model_id:
            raise Invalid('milan.entity.entity_model_id: resolved value contradicts literal or pin')
        identity['model_id'] = model_id
        if 'vendor_oui' in source:
            oui = hex_text(source['vendor_oui'], 24, 'milan.entity.vendor_oui')
            if oui & 0x010000:
                raise Invalid('milan.entity.vendor_oui: I/G bit must be clear')
            if oui != model_id >> 40:
                raise Invalid('milan.entity.vendor_oui: contradicts resolved model ID')
        if 'entity_capabilities' in source and hex_text(source['entity_capabilities'], 32, 'milan.entity.entity_capabilities') != capabilities:
            raise Invalid('milan.entity.entity_capabilities: contradicts resolved capabilities')
        clocking = document['clocking']
        crf_in = clocking['crf_sink']
        crf_out = clocking.get('crf_output', {'enabled': False})['enabled']
        if type(crf_in) is not bool or type(crf_out) is not bool:
            raise Invalid('milan.clocking: CRF enables must be booleans')
        result = dict(schema_version='1.0.0', identity=identity,
                      capabilities=dict(entity=capabilities, identify_control_index=0),
                      interfaces=[dict(mac=station_mac(document['platform']['mac_address']))], maap=[])
        for direction, old, crf in (('inputs', 'listeners', crf_in), ('outputs', 'talkers', crf_out)):
            result[direction] = [dict(name=row['name'], interface=0, kind='audio') for row in document['streams'][old]]
            if crf:
                result[direction].append(dict(name='CRF input' if direction == 'inputs' else 'CRF output', interface=0, kind='clock'))
        if result['outputs']:
            result['maap'] = [dict(interface=0, preferred=0)]
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, Invalid):
            raise
        raise Invalid('milan: missing or invalid mapping input: ' + str(error)) from error
    validate(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--model-id', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--capabilities', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = project(load(args.input), args.model_id, args.capabilities)
        args.output.write_text('# SPDX-License-Identifier: MIT\n' + yaml.safe_dump(result, sort_keys=False), encoding='utf-8')
    except (Invalid, OSError) as error:
        print('milan_entity: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
