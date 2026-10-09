#!/usr/bin/env python3
"""Independently check completed XML and owned messages for every declared killer."""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser()
p.add_argument('repo', type=Path)
p.add_argument('work', type=Path)
a = p.parse_args()
plants = json.loads((a.repo/'tests/mutations.json').read_text())
rows = json.loads((a.work/'results.json').read_text())
assert len(plants) == len(rows) == 330
assert {x['name'] for x in plants} == {x['name'] for x in rows}
assert all(x['status'] == 'CAUGHT' and x['rc'] == 1 for x in rows)
start, end = json.loads((a.work/'message-markers.json').read_text())
checked = 0
xmls = 0
named = []
for plant in plants:
    failures = []
    for path in (a.work/plant['name']).glob('*.xml'):
        root = ET.parse(path).getroot()
        assert root.tag == 'testsuites'
        cases = list(root.iter('testcase'))
        assert cases and len(cases) == int(root.attrib['tests'])
        assert root.attrib['errors'] == root.attrib['disabled'] == '0'
        assert len({(c.attrib['classname'], c.attrib['name']) for c in cases}) == len(cases)
        assert int(root.attrib['failures']) == sum(bool(c.findall('failure')) for c in cases)
        for case in cases:
            assert case.attrib['status'] == 'run' and case.attrib['result'] == 'completed'
            assert not case.findall('skipped') and not case.findall('error')
            for fail in case.findall('failure'):
                failures.append((path.stem, case.attrib['classname']+'.'+case.attrib['name'], fail.attrib['message']))
        xmls += 1
    for kill in plant['kills']:
        test = kill['test']
        matches = []
        for arm, name, message in failures:
            if kill.get('arm', arm) != arm:
                continue
            if not (name.startswith(test) if test.endswith('/') else name == test):
                continue
            portions = re.findall(re.escape('\n'+start+'\n')+'(.*?)'+re.escape('\n'+end+'\n'), message, re.S)
            if any(kill['needle'] in text for text in portions):
                matches.append(name)
        assert matches, (plant['name'], kill)
        named.append({'plant': plant['name'], 'test': test, 'needle': kill['needle'], 'matched': matches})
        checked += 1
print(json.dumps({'plants': len(plants), 'caught': len(rows), 'escaped': 0, 'errors': 0,
                  'completed_xml_reports': xmls, 'required_named_assertions_verified': checked,
                  'named_assertions': named}, indent=2))
