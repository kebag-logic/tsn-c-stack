#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate default diagnostics from a failing instance of every allowed assertion."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from assertion_forms import ALLOWED, GTEST_VERSION, errors, package_flags, refused_macros, require_version
from assertion_messages import instrument
from test_registry import environment

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'scripts/assertion-defaults.json'
MARKERS = ('TSN_TEMPLATE_BEGIN', 'TSN_TEMPLATE_END')


def generate(work):
    require_version()
    work.mkdir(parents=True, exist_ok=True)
    forms = {}
    for prefix in ('EXPECT_', 'ASSERT_'):
        for suffix, args in (('TRUE', 'false'), ('FALSE', 'true'), ('EQ', 'left, right'),
                             ('NE', '1, 1'), ('LE', '2, 1'), ('GE', '1, 2')):
            forms[prefix + suffix] = prefix + suffix + '(' + args + ') << "discarded stream";'
            if suffix == 'EQ':
                forms[prefix + suffix] = 'int left = 1, right = 2; ' + forms[prefix + suffix]
    forms['EXPECT_EXIT'] = 'EXPECT_EXIT(std::_Exit(1), ::testing::ExitedWithCode(0), "") << "discarded stream";'
    forms['EXPECT_CALL'] = 'Mock mock; EXPECT_CALL(mock, call()).Times(1);'
    if set(forms) != ALLOWED:
        raise RuntimeError('missing assertion template form')
    source = '#include <gtest/gtest.h>\n#include <gmock/gmock.h>\n#include <cstdlib>\n'
    source += 'struct Mock { MOCK_METHOD(void, call, ()); };\n'
    for name, body in sorted(forms.items()):
        source += '#line 1 "assertion-forms.cpp"\n'
        source += 'TEST(Forms, ' + name + ') { SCOPED_TRACE("template trace"); ' + body + ' }\n'
    source = instrument(source, MARKERS)
    path = work / 'forms.cpp'
    path.write_text(source)
    binary, report = work / 'forms', work / 'forms.xml'
    flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'gmock', 'gtest_main'], text=True).split()
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    str(path), *flags, '-o', str(binary)], check=True)
    report.unlink(missing_ok=True)
    result = subprocess.run([str(binary), '--gtest_output=xml:' + str(report)],
                            capture_output=True, text=True, env=environment(), timeout=30)
    (work / 'forms.log').write_text(result.stdout + result.stderr)
    doc = ET.parse(report).getroot()
    cases = list(doc.iter('testcase'))
    if (result.returncode != 1 or int(doc.get('tests', '0')) != len(ALLOWED)
            or int(doc.get('failures', '0')) != len(ALLOWED)
            or {case.get('name') for case in cases} != ALLOWED
            or len(cases) != len(ALLOWED)
            or any(case.get('result') != 'completed' or len(case.findall('failure')) != 1 for case in cases)):
        raise RuntimeError('each allowed assertion must produce exactly one complete failure')
    templates = {}
    for case in cases:
        message = case.find('failure').get('message', '')
        if case.get('name') != 'EXPECT_CALL':
            begin, end = ('\n' + marker + '\n' for marker in MARKERS)
            if message.count(begin) != 1 or message.count(end) != 1:
                raise RuntimeError('template stream delimiters missing')
            before, _, rest = message.partition(begin)
            _, _, after = rest.partition(end)
            message = before + after
        message = re.sub(r'assertion-forms\.cpp:\d+', 'assertion-forms.cpp:LINE', message)
        if not message.strip() or 'discarded stream' in message or any(m in message for m in MARKERS):
            raise RuntimeError('invalid default template')
        templates[case.get('name')] = message
    return {'googletest_version': GTEST_VERSION, 'refused_macros': refused_macros(),
            'templates': dict(sorted(templates.items()))}


def selftest(work, generated):
    source = '#include <gtest/gtest.h>\nTEST(Control, Near) { EXPECT_NEAR(1.0, 2.0, 0.1) << "The difference between"; }\n'
    path = work / 'near.cpp'
    path.write_text(source)
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    *package_flags('--cflags'),
                    '-c', str(path), '-o', str(work / 'near.o')], check=True)
    if errors(source) != ['unsupported assertion form: EXPECT_NEAR']:
        raise RuntimeError('numeric-nearness form accepted')
    from assertion_messages import inventory
    from needle_audit import validate_needles
    kill = {'name': 'near', 'kills': [{'test': 'Control.Near', 'needle': 'The difference between'}]}
    if not validate_needles([kill], inventory(source)):
        raise RuntimeError('unsupported assertion message accepted')
    for name, template in generated['templates'].items():
        needle = next(line.strip() for line in template.splitlines()
                      if len(line.strip()) >= 8 and not line.startswith('assertion-forms.cpp:'))
        kill = {'name': name, 'kills': [{'test': 'Control.Default', 'needle': needle}]}
        if not validate_needles([kill], {'Control.Default': [needle]}):
            raise RuntimeError('generated default text accepted: ' + name)
    if errors('TEST(Control, Allowed) { EXPECT_TRUE(false) << "owned diagnostic"; }'):
        raise RuntimeError('allowed assertion refused')
    for name, definition, statement, expected, failures in (
            ('alias', '', 'GTEST_ASSERT_LT(2, 1);', 'unsupported assertion form: GTEST_ASSERT_LT', 1),
            ('failure', '', 'GTEST_FAIL();', 'unsupported assertion form: GTEST_FAIL', 1),
            ('internal', '', 'GTEST_NONFATAL_FAILURE_("owned failure");',
             'unsupported assertion form: GTEST_NONFATAL_FAILURE_', 1),
            *((form.lower(), '#include <gtest/gtest-spi.h>\n',
               form + '(' + assertion + '(false) << "owned failure", "owned failure");',
               'unsupported assertion form: ' + form, 0)
              for form, assertion in (
                  ('EXPECT_NONFATAL_FAILURE', 'EXPECT_TRUE'),
                  ('EXPECT_FATAL_FAILURE', 'ASSERT_TRUE'),
                  ('EXPECT_NONFATAL_FAILURE_ON_ALL_THREADS', 'EXPECT_TRUE'),
                  ('EXPECT_FATAL_FAILURE_ON_ALL_THREADS', 'ASSERT_TRUE'))),
            ('pasted', '#define JOIN(a, b) a##b\n', 'JOIN(EXPE, CT_NEAR)(1.0, 2.0, 0.1);',
             'token pasting is forbidden in tests', 1)):
        source = '#include <gtest/gtest.h>\n' + definition + 'TEST(Control, Probe) { ' + statement + ' }\n'
        path = work / (name + '.cpp')
        path.write_text(source)
        binary, report = work / name, work / (name + '.xml')
        subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                        *package_flags('--cflags'), str(path), *package_flags('--libs'),
                        '-lgtest_main', '-o', str(binary)], check=True)
        report.unlink(missing_ok=True)
        result = subprocess.run([str(binary), '--gtest_output=xml:' + str(report)],
                                capture_output=True, env=environment(), timeout=30)
        doc = ET.parse(report).getroot()
        if result.returncode != failures or int(doc.get('failures', '-1')) != failures or int(doc.get('tests', '0')) != 1:
            raise RuntimeError(name + ': control did not execute with the expected assertion result')
        if errors(source) != [expected]:
            raise RuntimeError(name + ': unsupported assertion accepted')
        print('assertion control ' + name + ': compiled, executed with ' + str(failures) +
              ' failures and refused by source gate')
    for prefix in ('EXPECT_', 'ASSERT_', 'GTEST_'):
        name = prefix + 'UNLISTED_'
        if errors(name + '(false);') != ['unsupported assertion form: ' + name]:
            raise RuntimeError('unknown prefixed assertion accepted: ' + name)
    if errors('// GTEST_FAIL() ##\nconst char *text = "GTEST_FAIL ##";'):
        raise RuntimeError('literal assertion text refused')
    print('assertion controls: EXPECT_NEAR compiles and is refused; all 14 generated defaults are refused')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-assertion-templates'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    work = args.work.resolve()
    result = generate(work)
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    elif json.loads(OUTPUT.read_text()) != result:
        raise RuntimeError('assertion templates differ; regenerate with --write and review')
    if args.selftest:
        selftest(work, result)
    print('assertion templates: ' + GTEST_VERSION + '; 14 compiled failing forms; current')


if __name__ == '__main__':
    main()
