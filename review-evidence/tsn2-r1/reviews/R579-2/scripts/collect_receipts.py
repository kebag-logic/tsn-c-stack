#!/usr/bin/env python3
"""Publish gate receipts with checkout/work paths normalized; preserve both hashes."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('repo', type=Path)
p.add_argument('packet', type=Path)
p.add_argument('--gtest', required=True)
a = p.parse_args()
repo, packet = a.repo.resolve(), a.packet.resolve()
scratch = packet/'scratch'
replacements = [(str(scratch), '<scratch>'), (str(repo), '<checkout>'),
                (str(packet), '<packet>'), (a.gtest, '<test-prefix>'),
                (str(Path.home()), '<home>')]
provenance = []
def save(source, relative):
    raw = source.read_bytes()
    text = raw.decode()
    for old, new in replacements:
        text = text.replace(old, new)
    data = text.encode()
    dst = packet/'receipts'/relative
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    provenance.append({'source': str(source.relative_to(packet)), 'published': 'receipts/'+str(relative),
                       'original_sha256': hashlib.sha256(raw).hexdigest(),
                       'published_sha256': hashlib.sha256(data).hexdigest(),
                       'path_normalized': raw != data})
gates = scratch/'gates'
for f in gates.iterdir():
    if f.is_file(): save(f, Path('gate-runs')/f.name)
linux = gates/'linux'
for f in linux.iterdir():
    if f.is_file() and f.suffix in ('.log', '.rc', '.json'):
        save(f, Path('validation')/f.name)
for f in (linux/'graphs').glob('*.svg'):
    save(f, Path('graphs')/f.name)
save(linux/'conditionals/results.json', Path('validation/conditionals.json'))
mutations = linux/'mutations'
for name in ('results.json', 'message-markers.json'):
    save(mutations/name, Path('mutations')/name)
for f in sorted(mutations.glob('*/*.xml')):
    save(f, Path('mutations')/f.relative_to(mutations))
rv = gates/'rv32'
save(rv/'results.json', Path('rv32/results.json'))
for f in sorted(rv.glob('*/*.log')):
    save(f, Path('rv32')/f.relative_to(rv))
for f in sorted((scratch/'mapper-plants').glob('*/selftest.log')):
    save(f, Path('mapper-plants')/f.relative_to(scratch/'mapper-plants'))
save(scratch/'mapper-plants/results.json', Path('mapper-plants/results.json'))
for name in ('MANIFEST.json', 'integrity.json', 'gates.json', 'mutation-summary.json', 'mapper-plants.json',
             'mapping-regression.json', 'rv32-results.json', 'environment.json', 'coverage.log'):
    save(scratch/'public-r2/round2'/name, Path('author-r2')/name)
(packet/'receipts/receipt-provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
print('published receipt copies:', len(provenance))
