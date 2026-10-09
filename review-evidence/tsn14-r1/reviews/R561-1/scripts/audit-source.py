#!/usr/bin/env python3
"""Compare the pinned public source inventory and exact review tree."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

root, authorities = map(lambda p: Path(p).resolve(), sys.argv[1:3])
head = 'db950cfa959f501932a47d4113733a671f882a83'
base = '18d737832c376f32660eb21fe2796e0b611507e3'
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])

assert git('rev-parse', 'HEAD').decode().strip() == head
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == 'b7885c12e7e6077c1dabf07f1a0a53046c42d15a'
assert not git('diff', base, head, '--', 'src', 'include')
assert git('write-tree') == git('rev-parse', 'HEAD^{tree}')
tracked, gitlinks = 0, []
for item in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
    if not item:
        continue
    metadata, name = item.split(b'\t', 1)
    mode, kind, blob = metadata.decode().split()
    path = root / os.fsdecode(name)
    if mode == '160000':
        gitlinks.append((os.fsdecode(name), blob))
        assert subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD']).decode().strip() == blob
        continue
    data = os.fsencode(os.readlink(path)) if mode == '120000' else path.read_bytes()
    assert data == git('cat-file', 'blob', blob), str(path)
    actual = '120000' if path.is_symlink() else ('100755' if path.stat().st_mode & 0o111 else '100644')
    assert mode == actual, (path, mode, actual)
    tracked += 1
print('exact_head', head)
print('tracked_blob_bytes_and_modes', tracked, 'PASS')
print('index_tree_equals_HEAD PASS')
print('src_and_include_equal_source_base PASS')
print('required_gitlinks', json.dumps(gitlinks))

catalog = json.loads((root / 'docs/requirement-origins.json').read_text())
requirements = json.loads((root / 'docs/requirements.json').read_text())
found = {}
for name, pattern in [('FR_NFR.md', r'^\| ((?:FR|NFR)-[A-Z]+-\d+[a-z]?) \|'),
                      ('REQUIREMENTS.md', r'^- \*\*((?:REQ)-[A-Z]+-\d+) ')]:
    lines = (authorities / name).read_text().splitlines()
    ids = {}
    for line_no, line in enumerate(lines, 1):
        match = re.match(pattern, line)
        if match:
            assert match[1] not in ids
            ids[match[1]] = line_no
    found.update(ids)
    print('source_inventory', name, len(ids), hashlib.sha256((authorities / name).read_bytes()).hexdigest())
numbered = {r['origin'].removeprefix('milan-fpga '): r for r in catalog['rows'] if ' #665 ' not in r['origin']}
assert found.keys() == numbered.keys(), (found.keys() - numbered.keys(), numbered.keys() - found.keys())
for origin, line in found.items():
    assert numbered[origin]['url'].endswith('#L' + str(line)), (origin, line, numbered[origin]['url'])
print('all_114_numbered_sources_and_line_links PASS')
print('source_dispositions', dict(collections.Counter(r['disposition'] for r in catalog['rows'])))
imported = [r for r in requirements if 'origin' in r]
print('imported_requirements', len(imported), dict(collections.Counter(r['verification']['method'] for r in imported)))
sys.path.insert(0, str(root / 'scripts'))
import requirement_records
import traceability
assert not requirement_records.validate(requirements, catalog)
assert not requirement_records.check_document(requirements, catalog)
rows = [row for path in sorted((root / 'tests').glob('test_*.cpp')) for row in traceability.inventory(path.read_text())]
assert not traceability.validate(requirements, rows)
plants = json.loads((root / 'tests/mutations.json').read_text())
for req in imported:
    tests = [name for name, ids, line in rows if req['id'] in ids]
    print(req['id'], req['verification']['method'], ','.join(tests) or 'linked reason and evidence')
print('requirements_and_generated_source_map PASS')
print('test_declarations', len(rows), 'plants', len(plants))
new_plants = [p for p in plants if p['name'].startswith('adp-config-')]
assert len(new_plants) == 11
for plant in new_plants:
    assert (root / plant['path']).read_text().count(plant['old']) == 1
    assert plant['kills'][0]['test'] == 'AdpCore.AdvertisementFieldsMatchCaller'
print('eleven_ADP_vector_plants_unique_and_named PASS')
