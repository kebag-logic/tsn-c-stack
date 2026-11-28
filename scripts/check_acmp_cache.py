#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Require an independent hosted restore-loss plant for every ACMP cache field."""
import argparse
import copy
import json
from pathlib import Path
from assertion_messages import assertion_inventory as inventory, pairs, tokens
from needle_audit import validate_needles

ROOT = Path(__file__).resolve().parents[1]


def body(text, prefix):
    words = tokens(text)
    closing = pairs(words)
    starts = [i for i in range(len(words)) if words[i:i + len(prefix)] == prefix]
    if len(starts) != 1:
        raise ValueError('expected one definition: ' + ' '.join(prefix))
    opening = starts[0] + len(prefix) - 1
    return words[opening + 1:closing[opening]]


def cache_fields(header):
    fields = sorted({word for word in body(header, ['struct', 'acmp_sink', '{'])
                     if word.startswith('published_')})
    if not fields:
        raise ValueError('acmp_sink has no publication cache fields')
    return fields


def check(header, source, mutations, messages):
    literals = {name: [message.literal for message in owned]
                for name, owned in messages.items()}
    fields = cache_fields(header)
    reset = body(source, ['static', 'void', 'sink_reset', '(', 'struct', 'acmp', '*',
                          'a', ',', 'unsigned', 'k', ')', '{'])
    errors, owners = [], set()
    for field in fields:
        restore = ['s', '->', field, '=', field, ';']
        dropped = ['(', 'void', ')', field, ';']
        if sum(reset[i:i + len(restore)] == restore for i in range(len(reset))) != 1:
            errors.append(field + ': expected one restore in sink_reset')
        plants = [m for m in mutations if m.get('path') == 'src/acmp.c'
                  and tokens(m.get('old', '')) == restore
                  and tokens(m.get('new', '')) == dropped]
        if len(plants) != 1:
            errors.append(field + ': expected one restore-only loss plant')
            continue
        plant = plants[0]
        if source.count(plant['old']) != 1:
            errors.append(field + ': plant does not select one source restore')
        kills = plant.get('kills', [])
        if len(kills) != 1 or not kills[0].get('test', '').startswith('AcmpCore.'):
            errors.append(field + ': expected one named hosted ACMP assertion')
            continue
        errors += validate_needles([plant], literals)
        needle = kills[0].get('needle', '')
        matches = [message.identity for message in messages.get(kills[0]['test'], ())
                   if needle in message.literal]
        if len(matches) == 1:
            if matches[0] in owners:
                errors.append(field + ': assertion is shared with another cache field')
            owners.add(matches[0])
    return errors


def selftest(header, source, mutations, messages):
    controls = 0

    def refuse(label, h=header, s=source, m=mutations, a=messages):
        nonlocal controls
        if not check(h, s, m, a):
            raise RuntimeError('cache control accepted: ' + label)
        controls += 1

    for field in cache_fields(header):
        old = ['s', '->', field, '=', field, ';']
        plant = next(m for m in mutations if tokens(m['old']) == old)
        refuse(field + ' missing plant', m=[m for m in mutations if m is not plant])
        killed = plant['kills'][0]
        absent = copy.deepcopy(messages)
        del absent[killed['test']]
        refuse(field + ' missing test', a=absent)
        absent = copy.deepcopy(messages)
        absent[killed['test']] = [value for value in absent[killed['test']]
                                 if killed['needle'] not in value.literal]
        refuse(field + ' missing assertion', a=absent)
        for label, update in (
                ('empty killers', {'kills': []}),
                ('unchanged restore', {'new': plant['old']}),
                ('multiple fields', {'old': plant['old'] + 's->published_extra = published_extra;',
                                     'new': plant['new'] + '(void)published_extra;'}),
                ('wrong source', {'path': 'include/acmp.h'})):
            changed = [dict(m, **update) if m is plant else m for m in mutations]
            refuse(field + ' ' + label, m=changed)
        refuse(field + ' duplicate plant', m=mutations + [plant])
        refuse(field + ' missing restore', s=source.replace(plant['old'], plant['new']))

    extra = 'published_future'
    h = header.replace('struct acmp_sink {', 'struct acmp_sink {\n\tbool ' + extra + ';')
    old = '\ts->' + extra + ' = ' + extra + ';\n'
    s = source.replace('\ts->state = ACMP_UNBOUND;', old + '\ts->state = ACMP_UNBOUND;', 1)
    refuse('future field without coverage', h=h, s=s)
    plant = dict(name='future-cache-control', path='src/acmp.c', old=old,
                 new='\t(void)' + extra + ';\n',
                 kills=[dict(test='AcmpCore.FutureCacheControl', needle='future cache assertion')])
    a = dict(messages, **inventory('TEST_F(AcmpCore, FutureCacheControl) { '
                                 'EXPECT_TRUE(false) << "future cache assertion"; }'))
    if check(h, s, mutations + [plant], a):
        raise RuntimeError('covered future field refused')
    reused = copy.deepcopy(plant)
    first = cache_fields(header)[0]
    reused['kills'] = copy.deepcopy(next(m['kills'] for m in mutations
                                        if tokens(m['old']) == ['s', '->', first, '=', first, ';']))
    refuse('future field reuses assertion', h=h, s=s, m=mutations + [reused], a=a)
    reused['kills'][0]['needle'] = reused['kills'][0]['needle'][4:]
    refuse('future field reuses assertion with another needle', h=h, s=s, m=mutations + [reused], a=a)
    first_plant = next(m for m in mutations
                       if tokens(m['old']) == ['s', '->', first, '=', first, ';'])
    owner = first_plant['kills'][0]['test']
    suite, test = owner.split('.')
    needle = first_plant['kills'][0]['needle']
    future = plant['kills'][0]['needle']
    shared = f'EXPECT_TRUE(false) << "{needle}" << "{future}";'
    separate = f'EXPECT_TRUE(false) << "{needle}"; EXPECT_TRUE(false) << "{future}";'
    reused['kills'] = [dict(test=owner, needle=future)]
    for label, before, call in (
            ('direct', '', '{assertions}'),
            ('helper', 'void helper() {{ {assertions} }}', 'helper();'),
            ('nested callback', 'void helper() {{ {assertions} }} void callback() { helper(); }',
             'install(callback);')):
        for assertions, reject in ((shared, True), (separate, False)):
            prefix = before.replace('{assertions}', assertions).replace('{{', '{').replace('}}', '}')
            text = prefix + f'TEST_F({suite}, {test}) {{ ' + call.replace('{assertions}', assertions) + ' }'
            owned = dict(messages, **inventory(text))
            errors = check(h, s, mutations + [reused], owned)
            if reject:
                if errors != [extra + ': assertion is shared with another cache field']:
                    raise RuntimeError(label + ' split-message ownership control failed: ' + repr(errors))
                controls += 1
            elif errors:
                raise RuntimeError(label + ' separate assertions refused: ' + repr(errors))
    same = inventory('void helper() { EXPECT_TRUE(false) << "same message"; }\n'
                     'TEST_F(AcmpCore, One) { helper(); }\n'
                     'TEST_F(AcmpCore, Two) { helper(); }', 'control.cpp')
    for owner in ('AcmpCore.One', 'AcmpCore.Two'):
        if same[owner][0].identity != (owner, 'control.cpp', 1, 17):
            raise RuntimeError('helper definition location or test ownership lost')
    print(f'acmp cache: {controls} missing or invalid coverage controls refused; covered future field accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--work', type=Path, default=Path('build-acmp-cache-controls'))
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    header = (ROOT / 'include/acmp.h').read_text()
    source = (ROOT / 'src/acmp.c').read_text()
    mutations = json.loads((ROOT / 'tests/mutations.json').read_text())
    messages = inventory((ROOT / 'tests/test_acmp.cpp').read_text(), 'tests/test_acmp.cpp')
    errors = check(header, source, mutations, messages)
    if errors:
        print('\n'.join(errors))
        return 1
    if args.selftest:
        selftest(header, source, mutations, messages)
        from acmp_cache_controls import compiling_controls
        compiling_controls(ROOT, args.work.resolve(), args.jobs)
    print('acmp cache: every field has its own hosted assertion and restore-only plant: '
          + ', '.join(cache_fields(header)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
