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
        self.fixture = json.loads((ROOT / 'configs/compat/ax7101.json').read_text())
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
        cases = (
            (('schema_version',), '1.3.0', 'milan.schema_version: expected kebag-logic/milan-endstation-config 1.2.0'),
            (('entity', 'typo'), 1, 'milan.entity: unknown field or invalid mapping'),
            (('entity', 'entity_model_id'), '1', 'milan.entity.entity_model_id: resolved value contradicts literal or pin'),
            (('entity', 'model_id_pin'), '1', 'milan.entity.entity_model_id: resolved value contradicts literal or pin'),
            (('entity', 'entity_capabilities'), '1', 'milan.entity.entity_capabilities: contradicts resolved capabilities'),
            (('entity', 'vendor_oui'), '1', 'milan.entity.vendor_oui: contradicts resolved model ID'),
            (('entity', 'vendor_oui'), '010000', 'milan.entity.vendor_oui: I/G bit must be clear'),
            (('clocking', 'crf_sink'), 'yes', 'milan.clocking: CRF enables must be booleans'),
        )
        for path, value, message in cases:
            with self.subTest(path=path, value=value):
                doc = copy.deepcopy(self.fixture['input'])
                parent = doc
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                self.mapping_refuse(doc, message)
        doc = copy.deepcopy(self.fixture['input'])
        del doc['platform']['mac_address']
        self.mapping_refuse(doc, "milan: missing or invalid mapping input: 'mac_address'")

    def mapped(self, doc):
        old = self.fixture['expected_adp']
        return project(doc, old['entity_model_id'], old['entity_capabilities'])

    def mapping_refuse(self, doc, message):
        with self.assertRaises(entity.Invalid) as caught:
            self.mapped(doc)
        self.assertEqual(str(caught.exception), message)

    def test_mapping_digit_only_entity_id(self):
        doc = self.fixture['input']
        doc['entity']['entity_id'] = '1234567890123456'
        self.assertEqual(self.mapped(doc)['identity']['entity_id'], 0x1234567890123456)

    def test_mapping_unprefixed_entity_id(self):
        doc = self.fixture['input']
        doc['entity']['entity_id'] = '020000FFFE000001'
        self.assertEqual(self.mapped(doc)['identity']['entity_id'], 0x020000FFFE000001)

    def test_mapping_hex_spellings(self):
        fields = {'entity_id': '020000FFFE000001', 'entity_model_id': '001BC5C1935893E1',
                  'model_id_pin': '001BC5C1935893E1', 'vendor_oui': '001BC5',
                  'entity_capabilities': '0000C588'}
        for field, digits in fields.items():
            for value in (digits, digits.lower(), '0x' + digits, '0X' + digits, '_'.join(digits), '0x' + '_'.join(digits)):
                with self.subTest(field=field, value=value):
                    doc = copy.deepcopy(self.fixture['input'])
                    doc['entity'][field] = value
                    expected = self.mapped(self.fixture['input'])
                    if field == 'entity_id':
                        expected['identity']['entity_id'] = 0x020000FFFE000001
                    self.assertEqual(self.mapped(doc), expected)

    def test_mapping_hex_boundaries(self):
        for field in ('entity_id', 'entity_model_id', 'model_id_pin'):
            for value, number in (('1', 1), ('FFFFFFFFFFFFFFFE', 0xFFFFFFFFFFFFFFFE)):
                with self.subTest(field=field, value=value):
                    doc = copy.deepcopy(self.fixture['input'])
                    doc['entity'][field] = value
                    mid = self.fixture['expected_adp']['entity_model_id'] if field == 'entity_id' else number
                    mapped = project(doc, mid, 0xC588)
                    self.assertEqual(entity.validate(mapped)['entity_id' if field == 'entity_id' else 'model_id'], number)
        for digits, mid in (('000000', 1), ('FEFFFF', 0xFEFFFF0000000001)):
            doc = copy.deepcopy(self.fixture['input'])
            doc['entity']['vendor_oui'] = digits
            self.assertEqual(project(doc, mid, 0xC588)['identity']['model_id'], mid)
        doc = copy.deepcopy(self.fixture['input'])
        doc['entity']['entity_capabilities'] = '03F8CFFF'
        self.assertEqual(project(doc, 1, 0x03F8CFFF)['capabilities']['entity'], 0x03F8CFFF)

    def test_mapping_pin_precedence_and_literal_validation(self):
        doc = self.fixture['input']
        doc['entity']['model_id_pin'] = '001BC5C1935893E1'
        doc['entity']['entity_model_id'] = '1'
        self.assertEqual(self.mapped(doc)['identity']['model_id'], 0x001BC5C1935893E1)
        doc['entity']['entity_model_id'] = 1
        self.mapping_refuse(doc, 'milan.entity.entity_model_id: quote the hexadecimal value as a YAML string')

    def test_mapping_reserved_models(self):
        for field in ('entity_model_id', 'model_id_pin'):
            for value in ('0', 'FFFFFFFFFFFFFFFF'):
                with self.subTest(field=field, value=value):
                    doc = copy.deepcopy(self.fixture['input'])
                    doc['entity'][field] = value
                    self.mapping_refuse(doc, f'milan.entity.{field}: model identity must not be zero or all ones')

    def test_mapping_default_vendor_name(self):
        doc = self.fixture['input']
        del doc['entity']['vendor_name']
        self.assertEqual(self.mapped(doc)['identity']['vendor_name'], 'Kebag Logic')

    def test_mapping_default_group_name(self):
        doc = self.fixture['input']
        del doc['entity']['group_name']
        self.assertEqual(self.mapped(doc)['identity']['group_name'], '')

    def test_mapping_default_entity_id(self):
        doc = self.fixture['input']
        del doc['entity']['entity_id']
        mapped = self.mapped(doc)
        self.assertEqual(mapped['identity']['entity_id'], 'mac-derived')
        self.assertEqual(entity.validate(mapped)['entity_id'], 0x020000FFFE000001)

    def test_mapping_mac_spellings(self):
        for value in ('02:00:00:00:00:01', '02-00-00-00-00-01', '020000000001', '0x02_0000_000001', '0X020000000001'):
            with self.subTest(value=value):
                doc = copy.deepcopy(self.fixture['input'])
                doc['platform']['mac_address'] = value
                mapped = self.mapped(doc)
                self.assertEqual(mapped['interfaces'][0]['mac'], '02:00:00:00:00:01')
                self.assertEqual(entity.validate(mapped)['entity_id'], 0x020000FFFE000001)

    def test_mapping_mac_refusals(self):
        cases = (
            (1, 'quote the hexadecimal value as a YAML string'),
            ('02000000001', 'expected exactly 12 hexadecimal digits (48 bits)'),
            ('0020000000001', 'expected at most 12 hexadecimal digits (48 bits), including leading zeros'),
            ('02-00:00-00-00-01', 'expected hexadecimal digits with optional 0x and single underscores between digits; no sign or whitespace'),
            ('00-00-00-00-00-00', 'expected nonzero unicast MAC'),
            ('01-00-00-00-00-01', 'expected nonzero unicast MAC'),
        )
        for value, message in cases:
            with self.subTest(value=value):
                doc = copy.deepcopy(self.fixture['input'])
                doc['platform']['mac_address'] = value
                self.mapping_refuse(doc, 'milan.platform.mac_address: ' + message)

    def test_mapping_cli_compiled_identity(self):
        doc = self.fixture['input']
        doc['entity']['entity_id'] = '1234567890'
        source = self.directory / 'source.yaml'
        source.write_text(yaml.safe_dump(doc))
        mapped = self.directory / 'mapped.yaml'
        command = [sys.executable, str(ROOT / 'scripts/milan_entity.py'), str(source), '--model-id', '0x001BC5C1935893E1', '--capabilities', '0xC588', '--output', str(mapped)]
        subprocess.run(command, check=True, capture_output=True)
        subprocess.run([sys.executable, str(ROOT / 'scripts/entity_yaml.py'), str(mapped), '--output', str(self.directory)], check=True, capture_output=True)
        check = self.directory / 'check.c'
        check.write_text('#include "entity_config.h"\nint main(void) { return entity_adp[0].entity_id != UINT64_C(0x0000001234567890) || entity_acmp.entity_id != UINT64_C(0x0000001234567890); }\n')
        binary = self.directory / 'check'
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I' + str(ROOT / 'include'), str(self.directory / 'entity_config.c'), str(check), '-o', str(binary)], check=True, capture_output=True)
        self.assertEqual(subprocess.run([str(binary)]).returncode, 0)

    def test_yaml_integer_compatibility(self):
        for text, number in (('1:00', 60), ('010', 8), ('0x10', 16), ('10', 10)):
            with self.subTest(text=text):
                source = self.directory / 'integer.yaml'
                source.write_text(yaml.safe_dump(self.document).replace('identify_control_index: 0', 'identify_control_index: ' + text))
                self.assertEqual(entity.validate(entity.load(source))['identify'], number)


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


def mapping_hex_refusal(field, value, message):
    def test(self):
        doc = self.fixture['input']
        doc['entity'][field] = value
        self.mapping_refuse(doc, f'milan.entity.{field}: {message}')
    return test


for field, bits in (('entity_id', 64), ('entity_model_id', 64), ('model_id_pin', 64),
                    ('vendor_oui', 24), ('entity_capabilities', 32)):
    for form, value in (('integer', 1), ('boolean', True), ('float', 1.0), ('null', None), ('list', []), ('mapping', {})):
        setattr(EntityTests, f'test_mapping_refuse_{field}_{form}',
                mapping_hex_refusal(field, value, 'quote the hexadecimal value as a YAML string'))
    for form, value in (('empty', ''), ('prefix_only', '0x'), ('leading_underscore', '_1'),
                        ('prefix_underscore', '0x_1'), ('trailing_underscore', '1_'),
                        ('double_underscore', '1__2'), ('sign', '+1'), ('negative', '-1'),
                        ('leading_space', ' 1'), ('trailing_space', '1 '), ('newline', '1\n'),
                        ('nonhex', 'G1'), ('unicode', '１２'), ('separator', '1:2')):
        setattr(EntityTests, f'test_mapping_refuse_{field}_{form}', mapping_hex_refusal(field, value,
                'expected hexadecimal digits with optional 0x and single underscores between digits; no sign or whitespace'))
    for form, value in (('overflow', '1' * (bits // 4 + 1)), ('extra_zero', '0' * (bits // 4) + '1'),
                        ('wide_underscores', '0x' + '_'.join('0' * (bits // 4) + '1'))):
        setattr(EntityTests, f'test_mapping_refuse_{field}_{form}', mapping_hex_refusal(field, value,
                f'expected at most {bits // 4} hexadecimal digits ({bits} bits), including leading zeros'))


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
