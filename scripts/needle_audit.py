#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refuse missing or generic assertion identifiers in the mutation table."""
import argparse
import copy
import json
from pathlib import Path
import re
from assertion_messages import inventory
from test_registry import canonical

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES = ('Expected equality of these values:', 'Which is: ', 'Value of: ',
                     'Actual: false', 'Actual: true', 'Expected: true', 'Expected: false',
                     'Expected: (', ') <= (', ') != (', 'Failed', 'Google Test trace:')


def assertion_literals(root=ROOT):
    messages = {}
    for path in sorted((root / 'tests').glob('test_*.cpp')):
        found = inventory(path.read_text())
        if messages.keys() & found.keys():
            raise ValueError('duplicate test declaration in assertion inventory')
        messages.update(found)
    return messages


def validate_needles(mutations, messages=None):
    if messages is None:
        messages = assertion_literals()
    errors = []
    for plant in mutations:
        if not plant.get('kills'):
            errors.append(plant['name'] + ': no required assertion')
        for kill in plant.get('kills', []):
            needle = kill.get('needle', '').strip()
            if len(needle) < 8 or any(needle in template for template in DEFAULT_TEMPLATES) or re.fullmatch(
                    r'(Expected|Actual|Value of|Which is|Expected equality of these values)(:.*)?|true|false|[01]',
                    needle, re.I):
                errors.append(plant['name'] + ': empty or generic assertion needle')
            try:
                name = canonical(kill.get('test', ''))
            except ValueError:
                name = ''
            if sum(needle in value for value in messages.get(name, ())) != 1:
                errors.append(plant['name'] + ': needle must identify exactly one assertion message literal in ' + name)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    mutations = json.loads((ROOT / 'tests/mutations.json').read_text())
    if args.selftest:
        controls = ('', ' ', 'Expected: true', 'Actual: false', 'Value of: x', 'true',
                    '    Which is: 5', 'Which is: 1', 'Expected equality of these values:', 'Actual:',
                    'is: 5', '5u', 'r.frames.size()', 'Expected equality', 'equality of these values',
                    'e', 'Failed', 'hich is', ' equal')
        messages = assertion_literals()
        for value in controls:
            planted = copy.deepcopy(mutations)
            planted[0]['kills'][0]['needle'] = value
            if not validate_needles(planted, messages):
                raise RuntimeError('generic needle accepted: ' + repr(value))
        print(f'needles: {len(controls)} empty or generic table controls refused')
        source = '''
void helper() { EXPECT_EQ(1, 2) << "helper message"; }
void callback() { EXPECT_TRUE(false) << "callback message"; }
TEST(Control, First) {
    const char *unused = "unused message";
    EXPECT_STREQ("argument message", unused);
    log_stream << "unrelated stream";
    // EXPECT_TRUE(false) << "comment message";
    EXPECT_TRUE(false) << "own " "message" << 7;
    EXPECT_TRUE(false) << R"tag(raw message)tag";
    EXPECT_TRUE(false) << "suffix message" + 3;
    helper(); install(callback);
}
TEST(Control, Other) { EXPECT_TRUE(false) << "other test message"; }
'''
        messages = inventory(source)
        for value, refused in (
                ('own message', False), ('raw message', False), ('helper message', False),
                ('callback message', False), ('unused message', True), ('argument message', True),
                ('unrelated stream', True), ('comment message', True), ('other test message', True),
                ('suffix message', True), ('own message7', True)):
            table = [{'name': 'control', 'kills': [{'test': 'Control.First', 'needle': value}]}]
            if bool(validate_needles(table, messages)) != refused:
                raise RuntimeError('assertion ownership control failed: ' + value)
        print('needles: named-test, helper, callback and streamed-literal controls pass')
        duplicated = {'Control.First': ['unique marker', 'unique marker']}
        if not validate_needles([{'name': 'duplicate', 'kills': [
                {'test': 'Control.First', 'needle': 'unique marker'}]}], duplicated):
            raise RuntimeError('ambiguous assertion message accepted')
    errors = validate_needles(mutations)
    print('\n'.join(errors) if errors else 'needles: zero unspecific killers; no inherited exceptions')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
