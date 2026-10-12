#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build one hosted ACMP test binary with one planted fault and record failing tests.
Usage: probe.py <checkout> <probes.json> <name> <work>"""
import json, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
checkout, table, name, work = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
probe = next(p for p in json.loads(table.read_text()) if p['name'] == name)
tree = work / name / 'src'
shutil.rmtree(work / name, ignore_errors=True)
tree.mkdir(parents=True)
subprocess.run(f'git -C {checkout} archive HEAD | tar -x -C {tree}', shell=True, check=True)
if probe['old']:
    target = tree / probe['path']
    text = target.read_text()
    if text.count(probe['old']) != 1:
        raise SystemExit(name + ': plant must match exactly once')
    target.write_text(text.replace(probe['old'], probe['new']))
build = work / name / 'build'
subprocess.run(['cmake', '-S', str(tree), '-B', str(build), '-DCMAKE_BUILD_TYPE=Debug',
                '-DCMAKE_C_COMPILER=gcc', '-DCMAKE_CXX_COMPILER=g++'], check=True, capture_output=True)
subprocess.run(['cmake', '--build', str(build), '--target', 'acmp_tests', '-j2'], check=True, capture_output=True)
xml = work / name / 'acmp.xml'
rc = subprocess.run([str(build / 'acmp_tests'), '--gtest_output=xml:' + str(xml)], capture_output=True).returncode
root = ET.parse(xml).getroot()
failed = {}
for case in root.iter('testcase'):
    msgs = [f.get('message', '') for f in case.findall('failure')]
    if msgs:
        failed[case.get('classname') + '.' + case.get('name')] = '\n'.join(msgs)
result = {'probe': name, 'rc': rc, 'tests': int(root.get('tests')), 'failed': sorted(failed),
          'messages': failed}
(work / name / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
print(json.dumps({'probe': name, 'rc': rc, 'tests': result['tests'], 'failed': result['failed']}))
