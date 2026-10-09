#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Project milan-fpga 1.2.0 facts into the portable entity schema."""
import argparse
import copy
from pathlib import Path
import sys

import yaml

from entity_yaml import Invalid, integer, load, validate


def project(document, model_id, capabilities):
    if not isinstance(document, dict) or document.get('schema') != 'kebag-logic/milan-endstation-config' or document.get('schema_version') != '1.2.0':
        raise Invalid('milan.schema_version: expected kebag-logic/milan-endstation-config 1.2.0')
    try:
        source = document['entity']
        fields = {'entity_id', 'entity_model_id', 'model_id_pin', 'name', 'vendor_name', 'serial_number', 'group_name', 'vendor_oui', 'locale', 'entity_capabilities'}
        if not isinstance(source, dict) or set(source) - fields:
            raise Invalid('milan.entity: unknown field or invalid mapping')
        identity = {key: copy.deepcopy(source[key]) for key in ('entity_id', 'name', 'vendor_name', 'serial_number', 'group_name')}
        if identity['entity_id'] != 'mac-derived' and isinstance(identity['entity_id'], str):
            identity['entity_id'] = int(identity['entity_id'], 0)
        declared = source.get('model_id_pin', source['entity_model_id'])
        if declared != 'hash-derived':
            declared = int(declared, 0) if isinstance(declared, str) else declared
            if declared != model_id:
                raise Invalid('milan.entity.entity_model_id: resolved value contradicts literal or pin')
        identity['model_id'] = model_id
        if 'vendor_oui' in source and integer(source['vendor_oui'], 0, 0xFFFFFF, 'milan.entity.vendor_oui') != model_id >> 40:
            raise Invalid('milan.entity.vendor_oui: contradicts resolved model ID')
        if 'entity_capabilities' in source and source['entity_capabilities'] != capabilities:
            raise Invalid('milan.entity.entity_capabilities: contradicts resolved capabilities')
        clocking = document['clocking']
        crf_in = clocking['crf_sink']
        crf_out = clocking.get('crf_output', {'enabled': False})['enabled']
        if type(crf_in) is not bool or type(crf_out) is not bool:
            raise Invalid('milan.clocking: CRF enables must be booleans')
        result = dict(schema_version='1.0.0', identity=identity,
                      capabilities=dict(entity=capabilities, identify_control_index=0),
                      interfaces=[dict(mac=document['platform']['mac_address'])], maap=[])
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
