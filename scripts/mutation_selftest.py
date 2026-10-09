#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reject stale and incomplete mutation evidence in reused directories."""
import argparse
import json
from copy import deepcopy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from mutation import execute, matches, MESSAGE_MARKERS
from assertion_messages import instrument, inventory
from needle_audit import validate_needles

ROOT = Path(__file__).resolve().parents[1]


def grading(work):
    source = '''#include <gtest/gtest.h>
#include <string>
TEST(Control, Streamed) { EXPECT_EQ(1, 2) << "specific streamed defect"; }
TEST(Control, Default) {
  EXPECT_EQ(std::string("specific streamed defect"), std::string("other value"))
    << "another assertion message";
}
TEST(Control, Short) { EXPECT_EQ(1, 2) << "e"; }
TEST(Control, Failed) { FAIL() << "Failed"; }
TEST(Control, Fragment) { EXPECT_EQ(1, 2) << "hich is"; }
TEST(Control, Space) { EXPECT_EQ(1, 2) << " equal"; }
TEST(Control, Duplicate) {
  EXPECT_EQ(1, 2) << "duplicate message";
  EXPECT_EQ(2, 3) << "duplicate message";
}
'''
    path = work / 'grading.cpp'
    path.write_text(instrument(source, MESSAGE_MARKERS))
    binary = work / 'grading'
    subprocess.run(['g++', '-std=c++20', '-Wall', '-Wextra', '-Werror', str(path),
                    '-lgtest_main', '-lgtest', '-pthread', '-o', str(binary)], check=True)
    rc, failures, count = execute(binary, work / 'grading.xml', [])
    if rc != 1 or count != 7:
        raise RuntimeError('assertion grading controls did not execute')
    kill = {'test': 'Control.Streamed', 'needle': 'specific streamed defect'}
    if not matches(kill, failures):
        raise RuntimeError('streamed assertion was lost')
    kill['test'] = 'Control.Default'
    if matches(kill, failures):
        raise RuntimeError('default value printout counted as an assertion message')
    messages = inventory(source)
    for name, needle in [('Short', 'e'), ('Failed', 'Failed'), ('Fragment', 'hich is'),
                         ('Space', ' equal'), ('Duplicate', 'duplicate message')]:
        plant = {'name': name, 'kills': [{'test': 'Control.' + name, 'needle': needle}]}
        if not validate_needles([plant], messages):
            raise RuntimeError('generic or ambiguous compiled needle accepted: ' + needle)
    print('grading controls: compiled streamed message accepted; default text and five invalid needles refused')


def reports(work):
    binary = work / 'report-control'
    binary.write_text('''#!/usr/bin/env python3
import pathlib, sys
root = pathlib.Path(__file__).parent
if '--gtest_list_tests' in sys.argv:
    print('Control.\\n  First\\n  Second')
    raise SystemExit(0)
mode = (root / 'mode').read_text()
if mode == 'missing':
    raise SystemExit(1)
output = next(x.split('xml:', 1)[1] for x in sys.argv if x.startswith('--gtest_output='))
pathlib.Path(output).write_bytes((root / 'report').read_bytes())
raise SystemExit(1)
''')
    binary.chmod(0o755)
    xml = work / 'result.xml'
    valid = '<testsuites tests="2" failures="1" errors="0" disabled="0"><testsuite><testcase classname="Control" name="First" status="run" result="completed"><failure message="specific defect"/></testcase><testcase classname="Control" name="Second" status="run" result="completed"/></testsuite></testsuites>'
    (work / 'mode').write_text('write')
    (work / 'report').write_text(valid)
    rc, failures, count = execute(binary, xml, [])
    if not (rc == 1 and count == 2 and failures == {'Control.First': 'specific defect'}):
        raise RuntimeError("validation failed: rc == 1 and count == 2 and failures == {'Control.First': 'specific defect'}")
    (work / 'mode').write_text('missing')
    if not (execute(binary, xml, [])[2] == 0 and not xml.exists()):
        raise RuntimeError('validation failed: execute(binary, xml, [])[2] == 0 and not xml.exists()')
    print('report control: old complete XML removed before an early exit')
    variants = {'truncated': valid[:-20], 'wrong-count': valid.replace('tests="2"', 'tests="3"'),
                'wrong-name': valid.replace('name="Second"', 'name="Third"'),
                'duplicate': valid.replace('name="Second"', 'name="First"'),
                'skipped': valid.replace('result="completed"', 'result="skipped"'),
                'errors': valid.replace('errors="0"', 'errors="1"'),
                'missing-attributes': valid.replace(' disabled="0"', ''),
                'wrong-failures': valid.replace('failures="1"', 'failures="0"')}
    partial = ET.fromstring(valid)
    partial.find('testsuite').remove(partial.find('testsuite')[1])
    partial.set('tests', '1')
    variants['partial-registration'] = ET.tostring(partial, encoding='unicode')
    (work / 'mode').write_text('write')
    for name, content in variants.items():
        (work / 'report').write_text(content)
        if not (execute(binary, xml, [])[2] == 0):
            raise RuntimeError(name)
        print('report control ' + name + ': refused')


def campaign(work, jobs):
    copy = work / 'repository'
    for directory in ('scripts', 'tests', 'include', 'src', 'examples'):
        shutil.copytree(ROOT / directory, copy / directory)
    table = copy / 'tests/mutations.json'
    plant = next(m for m in json.loads(table.read_text()) if m['name'] == 'departing-keeps-index')
    table.write_text(json.dumps([plant]))
    command = [sys.executable, str(copy / 'scripts/mutation.py'), '--work', str(work / 'campaign'),
               '--jobs', str(jobs)]
    def run(label, expected, status):
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (work / (label + '.log')).write_text(result.stdout)
        if not (result.returncode == expected):
            raise RuntimeError(result.stdout)
        results = json.loads((work / 'campaign/results.json').read_text())
        if not (results[0]['status'] == status):
            raise RuntimeError(results)
    genuine = deepcopy(plant)
    run('genuine-catch', 0, 'CAUGHT')
    old_xml = list((work / 'campaign' / plant['name']).glob('*.xml'))
    if not (len(old_xml) == 2):
        raise RuntimeError('validation failed: len(old_xml) == 2')
    plant['new'] = plant['old'] + '\texit(1);\n'
    table.write_text(json.dumps([plant]))
    path = copy / 'src/adp.c'
    path.write_text(path.read_text().replace('#include <string.h>', '#include <string.h>\n#include <stdlib.h>'))
    run('early-exit-reused', 1, 'ESCAPED')
    if any(path.exists() for path in old_xml):
        raise RuntimeError('validation failed: not any(path.exists() for path in old_xml)')
    print('reused campaign: genuine catch followed by early exit(1) ESCAPED; both old reports removed')
    for mixed in (False, True):
        plant = deepcopy(genuine)
        missing = dict(plant['kills'][0], test='Missing.Unknown')
        plant['kills'] = [plant['kills'][0], missing] if mixed else [missing]
        table.write_text(json.dumps([plant]))
        run('unknown-test-' + str(mixed), 1, 'ERROR')
        print('unknown test control: ERROR, including a mixed known/unknown selection' if mixed
              else 'unknown test control: ERROR replaces the old campaign summary')
    table.write_text(json.dumps([genuine]))
    result = subprocess.run(command, env=dict(os.environ, CXX='false'), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (work / 'baseline-failure.log').write_text(result.stdout)
    if result.returncode == 0 or (work / 'campaign/results.json').exists():
        raise RuntimeError('failed baseline preserved old campaign results')
    print('baseline failure control: old campaign summary removed before building')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-mutation-controls'))
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.work.resolve()) as temporary:
        work = Path(temporary)
        grading(work)
        reports(work)
        campaign(work, args.jobs)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
