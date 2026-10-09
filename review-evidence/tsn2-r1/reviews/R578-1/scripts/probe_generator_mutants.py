#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Plant single-line defects in a disposable copy of scripts/entity_yaml.py and
scripts/milan_entity.py; each must make entity_selftest.py or --examples --check fail.
Usage: probe_generator_mutants.py <tsn-c-stack checkout> <scratch dir>"""
import shutil, subprocess, sys, tarfile, io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
repo, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
archive = subprocess.run(['git', '-C', str(repo), 'archive', 'HEAD'], check=True, capture_output=True).stdout
PLANTS = [
 ('entity_yaml.py', "if flags & 0xC588 != 0xC588 or flags & 0x73000:", "if flags & 0xC588 != 0xC588:"),
 ('entity_yaml.py', "result & (1 << 40)", "result & (1 << 47)"),
 ('entity_yaml.py', "        if address in macs:", "        if False:"),
 ('entity_yaml.py', "POOL_BASE <= base <= POOL_END - counts[port]", "POOL_BASE <= base <= POOL_END"),
 ('entity_yaml.py', "        if not counts[port]:", "        if False:"),
 ('entity_yaml.py', "    if seen != {i for i, count in enumerate(counts) if count}:", "    if False:"),
 ('entity_yaml.py', "        if port in seen:", "        if False:"),
 ('entity_yaml.py', "not 127 <= ord(c) <= 159", "True"),
 ('entity_yaml.py', "0x4000 if row['kind'] == 'audio' else 0x0800", "0x4000"),
 ('entity_yaml.py', "(0xFFFE << 24)", "(0xFEFF << 24)"),
 ('entity_yaml.py', "rows = sequence(d[direction], 0, 16, direction)", "rows = sequence(d[direction], 0, 17, direction)"),
 ('entity_yaml.py', "interfaces = sequence(d['interfaces'], 1, 4, 'interfaces')", "interfaces = sequence(d['interfaces'], 1, 5, 'interfaces')"),
 ('entity_yaml.py', "    if d['schema_version'] != VERSION:", "    if False:"),
 ('entity_yaml.py', "        if key not in fields:", "        if False:"),
 ('entity_yaml.py', "            raise Invalid(f'yaml: duplicate field {key}')", "            pass"),
 ('entity_yaml.py', "', '.join(f'{x}u' for x in (ports or [0]))", "', '.join(f'{x}u' for x in reversed(ports or [0]))"),
 ('entity_yaml.py', "c += f'_Static_assert({upper}_ENTITY_SCHEMA_VERSION == 0x010000u", "c += f'_Static_assert({upper}_ENTITY_SCHEMA_VERSION >= 0x010000u"),
 ('milan_entity.py', "        if crf:", "        if False:"),
 ('milan_entity.py', "            if declared != model_id:", "            if False:"),
 ('milan_entity.py', "            result['maap'] = [dict(interface=0, preferred=0)]", "            result['maap'] = [dict(interface=0, preferred=0x91E0F0000000)]"),
]
def one(index):
    name, old, new = PLANTS[index]
    d = work / f'm{index:02d}'; d.mkdir()
    tarfile.open(fileobj=io.BytesIO(archive)).extractall(d)
    p = d / 'scripts' / name; text = p.read_text()
    if text.count(old) != 1: return index, 'PLANT-NOT-UNIQUE', name, old
    p.write_text(text.replace(old, new))
    a = subprocess.run([sys.executable, '-I', 'scripts/entity_selftest.py', '--work', str(d / 'w')], cwd=d, capture_output=True, text=True)
    b = subprocess.run([sys.executable, '-I', 'scripts/entity_yaml.py', '--examples', '--check'], cwd=d, capture_output=True, text=True)
    failed = [l.split(' ')[0] for l in a.stderr.splitlines() if l.startswith(('FAIL:', 'ERROR:'))]
    failed = [l for l in a.stderr.splitlines() if l.startswith(('FAIL: ', 'ERROR: '))]
    status = 'CAUGHT' if a.returncode or b.returncode else 'ESCAPED'
    return index, status, name, f'{old!r} -> {new!r}; selftest rc={a.returncode} golden rc={b.returncode}; first={failed[:2]}'
with ThreadPoolExecutor(8) as pool:
    for r in pool.map(one, range(len(PLANTS))): print(*r, sep=' | ')
