#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refuse missing or generic assertion identifiers in the mutation table."""
import argparse
import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def validate_needles(mutations):
    errors = []
    for plant in mutations:
        if not plant.get('kills'):
            errors.append(plant['name'] + ': no required assertion')
        for kill in plant.get('kills', []):
            needle = kill.get('needle', '').strip()
            if not needle or re.fullmatch(r'(Expected|Actual|Value of)(:.*)?|true|false|[01]', needle, re.I):
                errors.append(plant['name'] + ': empty or generic assertion needle')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    mutations = json.loads((ROOT / 'tests/mutations.json').read_text())
    if args.selftest:
        for value in ('', ' ', 'Expected: true', 'Actual: false', 'Value of: x', 'true'):
            planted = copy.deepcopy(mutations)
            planted[0]['kills'][0]['needle'] = value
            assert validate_needles(planted), value
        print('needles: six empty or generic table controls refused')
    errors = validate_needles(mutations)
    print('\n'.join(errors) if errors else 'needles: zero unspecific killers; no inherited exceptions')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
