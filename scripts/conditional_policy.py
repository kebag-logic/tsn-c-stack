# SPDX-License-Identifier: MIT
"""Closed set of source conditionals, shared by lexical and compilation gates."""
from compiler_tokens import directives

MACROS = {'__cplusplus': None, 'NDEBUG': '1', 'CTRL_REENTRY_ASSERT': '1',
          'ADP_TEST_RELEASE': '1', 'ADP_TEST_COVERAGE': '1',
          'ACMP_MAX_SINKS': '16u', 'ACMP_MAX_SOURCES': '16u'}
GUARDS = {'include/adp.h': 'ADP_H', 'include/acmp.h': 'ACMP_H',
          'include/maap.h': 'CTRL_MAAP_H', 'include/wire.h': 'CTRL_WIRE_H',
          'tests/acmp_fake.hpp': 'ACMP_FAKE_HPP', 'examples/adp_port.h': 'EXAMPLE_ADP_PORT_H',
          'examples/rv32/include/assert.h': 'TSN_PORT_ASSERT_H',
          'examples/rv32/include/string.h': 'TSN_PORT_STRING_H',
          'examples/entity_roundtrip.h': 'EXAMPLE_ENTITY_ROUNDTRIP_H',
          'examples/entities/listener/entity_config.h': 'LISTENER_ENTITY_CONFIG_V1_0_0_H',
          'examples/entities/talker/entity_config.h': 'TALKER_ENTITY_CONFIG_V1_0_0_H',
          'examples/entities/duplex/entity_config.h': 'DUPLEX_ENTITY_CONFIG_V1_0_0_H',
          'examples/entities/ax7101/entity_config.h': 'AX7101_ENTITY_CONFIG_V1_0_0_H',
          }
DIRECTIVES = {'define', 'undef', 'include', 'ifdef', 'ifndef', 'else', 'endif',
              'if', 'elif', 'elifdef', 'elifndef', 'pragma', 'error', 'warning', 'line'}


def inspect(tokens, path=None, fragment=False):
    errors, regions, stack = [], [], []
    guard = GUARDS.get(path)
    rows = directives(tokens)
    significant = [t for t in tokens if t[0] != 'comment' and not t[1].isspace()]
    for index, row in enumerate(rows):
        words = [t[1] for t in row]
        if len(words) < 2:
            continue
        op, args = words[1], words[2:]
        at = row[0][4]
        if op in ('if', 'elif', 'elifdef', 'elifndef', 'pragma', 'line'):
            errors.append(f'line {at}: #{op} is forbidden')
        elif op in ('ifdef', 'ifndef'):
            macro = args[0] if len(args) == 1 else ''
            is_guard = macro == guard and not stack and not regions and op == 'ifndef'
            if is_guard:
                following = rows[index + 1] if index + 1 < len(rows) else []
                if (row[0] != significant[0] or not following
                        or [t[1] for t in following] != ['#', 'define', guard]
                        or following[0][4] != at + 1):
                    errors.append(f'line {at}: guard needs an immediate matching #define')
            elif macro not in MACROS:
                errors.append(f'line {at}: unlisted conditional macro {macro}')
            region = {'macro': macro, 'guard': is_guard, 'start': row,
                      'else': None, 'end': None}
            stack.append(region)
            regions.append(region)
        elif op == 'else':
            if args or not stack or stack[-1]['else'] is not None:
                errors.append(f'line {at}: unmatched or repeated #else')
            else:
                stack[-1]['else'] = row
                if stack[-1]['guard']:
                    errors.append(f'line {at}: include guard cannot have #else')
        elif op == 'endif':
            if args or not stack:
                if not fragment:
                    errors.append(f'line {at}: unmatched #endif')
            else:
                region = stack.pop()
                region['end'] = row
                if region['guard'] and row[-1] != significant[-1]:
                    errors.append(f'line {at}: include guard must enclose the file')
        elif op in ('define', 'undef') and args:
            macro = args[0]
            if macro in MACROS or macro in GUARDS.values():
                default = (op == 'define' and stack and stack[-1]['macro'] == macro
                           and stack[-1]['start'][1][1] == 'ifndef'
                           and stack[-1]['else'] is None
                           and at == stack[-1]['start'][0][4] + 1
                           and (stack[-1]['guard'] or macro in ('ACMP_MAX_SINKS', 'ACMP_MAX_SOURCES')))
                if not default:
                    errors.append(f'line {at}: conditional macro {macro} cannot be redefined or undefined')
        elif op not in DIRECTIVES:
            errors.append(f'line {at}: unknown directive #{op}')
    if stack and not fragment:
        errors.append('unterminated conditional region')
    if guard and not any(r['guard'] for r in regions) and not fragment:
        errors.append('missing file include guard')
    return errors, regions
