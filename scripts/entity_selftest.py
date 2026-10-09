#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise schema refusals, deterministic goldens and compatibility facts."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

import entity_yaml as entity
from milan_entity import project

ROOT = entity.ROOT
WORK = None


class EntityTests(unittest.TestCase):
    def setUp(self):
        self.document = entity.load(ROOT / 'configs/duplex.yaml')
        self.temp = tempfile.TemporaryDirectory(dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def refuse(self, document, diagnostic):
        with self.assertRaises(entity.Invalid) as caught:
            entity.validate(document)
        self.assertEqual(str(caught.exception), diagnostic)

    def test_golden_bytes(self):
        for persona in entity.PERSONAS:
            with self.subTest(persona=persona):
                doc = entity.load(ROOT / 'configs' / (persona + '.yaml'))
                entity.emit(doc, ROOT / 'examples/entities' / persona, persona, check=True)
                first = entity.render(doc, persona)
                second = entity.render(dict(reversed(list(doc.items()))), persona)
                self.assertEqual(first, second)
                entity.emit(doc, self.directory, persona)
                self.assertEqual({n: (self.directory / n).read_bytes() for n in first},
                                 {n: s.encode('ascii') for n, s in first.items()})

    def test_golden_planted_drift(self):
        plants = json.loads((ROOT / 'tests/mutations.json').read_text())[-3:]
        self.assertEqual({p['name'] for p in plants}, {'entity-wrong-count', 'entity-swapped-interface', 'entity-dropped-field'})
        for plant in plants:
            with self.subTest(plant=plant['name']):
                persona = Path(plant['path']).parent.name
                doc = entity.load(ROOT / 'configs' / (persona + '.yaml'))
                entity.emit(doc, self.directory, persona)
                path = self.directory / 'entity_config.c'
                source = path.read_text()
                self.assertEqual(source.count(plant['old']), 1)
                path.write_text(source.replace(plant['old'], plant['new']))
                with self.assertRaisesRegex(entity.Invalid, 'generated file drift'):
                    entity.emit(doc, self.directory, persona, check=True)

    def test_dropped_required_fields(self):
        for path in ((), ('identity',), ('capabilities',), ('interfaces', 0), ('inputs', 0), ('outputs', 0), ('maap', 0)):
            obj = self.document
            for key in path:
                obj = obj[key]
            for field in obj:
                with self.subTest(path=path, field=field):
                    doc = copy.deepcopy(self.document)
                    changed = doc
                    for key in path:
                        changed = changed[key]
                    del changed[field]
                    with self.assertRaisesRegex(entity.Invalid, 'required field missing'):
                        entity.validate(doc)

    def test_unknown_fields_at_each_level(self):
        for path in ((), ('identity',), ('capabilities',), ('interfaces', 0), ('inputs', 0), ('outputs', 0), ('maap', 0)):
            with self.subTest(path=path):
                doc = copy.deepcopy(self.document)
                changed = doc
                for key in path:
                    changed = changed[key]
                changed['typo'] = 1
                with self.assertRaisesRegex(entity.Invalid, 'typo: unknown field'):
                    entity.validate(doc)

    def test_yaml_refusals(self):
        for text, message in (('identity: 1\nidentity: 2\n', 'yaml: duplicate field identity'),
                              ('true: 1\n', 'yaml: mapping keys must be strings'),
                              ('a: &x 1\nb: *x\n', 'yaml: aliases are unsupported'),
                              ('[broken', 'yaml: invalid document'),
                              ('!!python/object:bad {}', 'yaml: invalid document'),
                              ('---\na: 1\n---\nb: 2', 'yaml: invalid document')):
            with self.subTest(message=message):
                source = self.directory / 'input.yaml'
                source.write_text(text)
                with self.assertRaises(entity.Invalid) as caught:
                    entity.load(source)
                self.assertEqual(str(caught.exception), message)

    def test_integer_boolean_and_float_refusals(self):
        for value in (True, False, 1.0, '1', None, -1, 65536):
            with self.subTest(value=value):
                self.document['capabilities']['identify_control_index'] = value
                self.refuse(self.document, 'capabilities.identify_control_index: expected integer in 0..65535')

    def test_valid_boundaries(self):
        self.document['interfaces'] += [{'mac': '02:00:00:00:00:03'}, {'mac': '02:00:00:00:00:04'}]
        for key in ('inputs', 'outputs'):
            self.document[key] = [dict(name='', interface=3, kind='audio') for _ in range(16)]
        self.document['maap'] = [dict(interface=3, preferred=entity.POOL_END - 16)]
        self.document['identity']['entity_id'] = (1 << 64) - 2
        self.document['identity']['model_id'] = (1 << 64) - 2
        self.document['identity']['name'] = 'é' * 32
        self.document['capabilities']['identify_control_index'] = 65535
        result = entity.validate(self.document)
        self.assertEqual(result['counts'], [0, 0, 0, 16])
        source = entity.render(self.document)['entity_config.c']
        self.assertTrue(source.isascii())
        self.assertIn('\\303\\251', source)
        self.document['maap'][0]['preferred'] += 1
        self.refuse(self.document, 'maap[0].preferred: complete range must be in the MAAP dynamic pool')

    def test_explicit_identity_and_literal_escaping(self):
        self.document['identity']['entity_id'] = 123
        self.document['identity']['name'] = '"\\??/'
        self.assertEqual(entity.validate(self.document)['entity_id'], 123)
        self.assertIn('\\042\\134\\077\\077\\057', entity.render(self.document)['entity_config.c'])

    def test_schema_header_guard(self):
        entity.emit(self.document, self.directory)
        header = self.directory / 'entity_config.h'
        header.write_text(header.read_text().replace('0x010000u', '0x020000u'))
        command = ['gcc', '-std=c11', '-I' + str(ROOT / 'include'), '-c', str(self.directory / 'entity_config.c'), '-o', str(self.directory / 'entity.o')]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('entity schema version mismatch', result.stderr)

    def test_invalid_prefix(self):
        for prefix in ('UPPER', '_reserved', 'bad-name', '1entity', ''):
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(entity.Invalid, 'prefix: expected a lower-case C identifier'):
                    entity.render(self.document, prefix)

    def test_missing_golden_file(self):
        with self.assertRaisesRegex(entity.Invalid, 'entity/entity_config.h: generated file drift'):
            entity.emit(self.document, self.directory, check=True)

    def test_invalid_cli_preserves_outputs(self):
        entity.emit(self.document, self.directory)
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        self.document['schema_version'] = '2.0.0'
        source = self.directory / 'bad.yaml'
        source.write_text(yaml.safe_dump(self.document))
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/entity_yaml.py'), str(source), '--output', str(self.directory)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('supported version is 1.0.0', result.stderr)
        for name, contents in before.items():
            self.assertEqual((self.directory / name).read_bytes(), contents)

    def test_ax7101_mapping(self):
        fixture = json.loads((ROOT / 'configs/compat/ax7101.json').read_text())
        old = fixture['expected_adp']
        mapped = project(fixture['input'], old['entity_model_id'], old['entity_capabilities'])
        self.assertEqual(mapped, entity.load(ROOT / 'configs/ax7101.yaml'))
        d = entity.validate(mapped)
        fields = dict(entity_id=d['entity_id'], entity_model_id=d['model_id'], mac=d['macs'][0], entity_capabilities=d['flags'],
                      talker_stream_sources=len(d['streams']['outputs']), talker_capabilities=d['stream_caps']['outputs'],
                      listener_stream_sinks=len(d['streams']['inputs']), listener_capabilities=d['stream_caps']['inputs'], identify_control_index=d['identify'])
        self.assertEqual(fields, old)
        for path in ('inputs', 'outputs'):
            self.assertEqual(mapped[path][1]['kind'], 'clock')
            self.assertEqual([row['interface'] for row in mapped[path]], [0, 0])

    def test_mapping_refusals(self):
        fixture = json.loads((ROOT / 'configs/compat/ax7101.json').read_text())
        for defect in ('version', 'unknown', 'missing', 'pin', 'caps', 'oui', 'clock'):
            with self.subTest(defect=defect):
                doc = copy.deepcopy(fixture['input'])
                if defect == 'version': doc['schema_version'] = '1.3.0'
                if defect == 'unknown': doc['entity']['typo'] = 1
                if defect == 'missing': del doc['platform']['mac_address']
                if defect == 'pin': doc['entity']['model_id_pin'] = 1
                if defect == 'caps': doc['entity']['entity_capabilities'] = 1
                if defect == 'oui': doc['entity']['vendor_oui'] = 1
                if defect == 'clock': doc['clocking']['crf_sink'] = 'yes'
                with self.assertRaises(entity.Invalid):
                    project(doc, fixture['expected_adp']['entity_model_id'], fixture['expected_adp']['entity_capabilities'])


REFUSALS = {
    'version': (('schema_version',), '2.0.0', 'entity.schema_version: supported version is 1.0.0'),
    'root_type': ((), [], 'entity: expected a mapping'),
    'interfaces_empty': (('interfaces',), [], 'interfaces: expected list with 1..4 entries'),
    'interfaces_count': (('interfaces',), [{}] * 5, 'interfaces: expected list with 1..4 entries'),
    'sink_count': (('inputs',), [{}] * 17, 'inputs: expected list with 0..16 entries'),
    'source_count': (('outputs',), [{}] * 17, 'outputs: expected list with 0..16 entries'),
    'sink_interface': (('inputs', 0, 'interface'), 2, 'inputs[0].interface: expected integer in 0..1'),
    'source_interface': (('outputs', 0, 'interface'), -1, 'outputs[0].interface: expected integer in 0..1'),
    'mac_format': (('interfaces', 0, 'mac'), 2, 'interfaces[0].mac: expected six colon-separated hexadecimal octets'),
    'missing_mac': (('interfaces', 0), {}, 'interfaces[0].mac: required field missing'),
    'mac_zero': (('interfaces', 0, 'mac'), '00:00:00:00:00:00', 'interfaces[0].mac: expected nonzero unicast MAC'),
    'mac_multicast': (('interfaces', 0, 'mac'), '01:00:00:00:00:01', 'interfaces[0].mac: expected nonzero unicast MAC'),
    'mac_duplicate': (('interfaces', 1, 'mac'), '02:00:00:00:00:01', 'interfaces[1].mac: duplicate MAC'),
    'entity_id_zero': (('identity', 'entity_id'), 0, 'identity.entity_id: expected integer in 1..18446744073709551614'),
    'model_id_ones': (('identity', 'model_id'), (1 << 64) - 1, 'identity.model_id: expected integer in 1..18446744073709551614'),
    'name_length': (('identity', 'name'), 'é' * 33, 'identity.name: expected UTF-8 string of 0..64 bytes without controls'),
    'name_control': (('identity', 'name'), 'bad\x00', 'identity.name: expected UTF-8 string of 0..64 bytes without controls'),
    'name_c1_control': (('identity', 'name'), 'bad\x85', 'identity.name: expected UTF-8 string of 0..64 bytes without controls'),
    'name_surrogate': (('identity', 'name'), '\ud800', 'identity.name: expected UTF-8 string of 0..64 bytes without controls'),
    'name_type': (('identity', 'name'), 3, 'identity.name: expected UTF-8 string of 0..64 bytes without controls'),
    'capability_range': (('capabilities', 'entity'), 0x04000000, 'capabilities.entity: expected integer in 0..67108863'),
    'capability_milan': (('capabilities', 'entity'), 0, 'capabilities.entity: requires Milan flags 0xC588 and clears 0x73000'),
    'capability_auth': (('capabilities', 'entity'), 0xD588, 'capabilities.entity: requires Milan flags 0xC588 and clears 0x73000'),
    'kind': (('inputs', 0, 'kind'), 'video', 'inputs[0].kind: expected audio or clock'),
    'maap_missing': (('maap',), [], 'maap: exactly one reservation is required per output interface'),
    'maap_duplicate': (('maap', 1, 'interface'), 0, 'maap[1].interface: duplicate reservation'),
    'maap_interface': (('maap', 1, 'interface'), 2, 'maap[1].interface: expected integer in 0..1'),
    'maap_pool': (('maap', 0, 'preferred'), 0x91E0F000FE01, 'maap[0].preferred: complete range must be in the MAAP dynamic pool'),
    'maap_range': (('maap', 0, 'preferred'), -1, 'maap[0].preferred: expected integer in 0..281474976710655'),
    'maap_no_outputs': (('outputs',), [], 'maap[0].interface: has no outputs'),
}


def refusal_test(path, value, diagnostic):
    def test(self):
        if not path:
            self.document = value
        else:
            obj = self.document
            for key in path[:-1]:
                obj = obj[key]
            obj[path[-1]] = value
        self.refuse(self.document, diagnostic)
    return test


for refusal, arguments in REFUSALS.items():
    setattr(EntityTests, 'test_refuse_' + refusal, refusal_test(*arguments))


def main():
    global WORK
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-entity'))
    args = parser.parse_args()
    WORK = args.work.resolve()
    WORK.mkdir(parents=True, exist_ok=True)
    os.environ['TMPDIR'] = str(WORK)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EntityTests))
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    raise SystemExit(main())
