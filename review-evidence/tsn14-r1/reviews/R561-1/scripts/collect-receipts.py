#!/usr/bin/env python3
"""Collect execution records, normalizing locations while retaining raw hashes."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

root, packet = (Path(p).resolve() for p in sys.argv[1:3])
scratch = packet / 'scratch'
receipts = packet / 'receipts'
records = []
replacements = [(str(packet), '$PACKET'), (str(root), '$SOURCE'), (str(Path.home()), '$USER_HOME')]

def keep(source, relative):
    original = source.read_bytes()
    text = original.decode()
    for old, new in replacements:
        text = text.replace(old, new)
    published = text.encode()
    target = receipts / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(published)
    records.append({'file': str(target.relative_to(packet)), 'original_sha256': hashlib.sha256(original).hexdigest(), 'published_sha256': hashlib.sha256(published).hexdigest(), 'path_redacted': original != published})

for kind in ('validate-compatible', 'baremetal-compatible'):
    keep(scratch / (kind + '.log'), kind + '/runner.log')
    keep(scratch / (kind + '.rc'), kind + '/runner.rc')
for pattern in ('*.log', '*.rc', 'gates.json', 'mutations/results.json', 'mutations/message-markers.json', 'mutations/*/*.xml', 'conditionals/results.json', 'assertion-templates/*.xml', 'graphs/*.svg'):
    for source in sorted((scratch / 'validate-compatible').glob(pattern)):
        keep(source, 'validate-compatible/' + str(source.relative_to(scratch / 'validate-compatible')))
for pattern in ('results.json', '*/*.log', '*/*.map'):
    for source in sorted((scratch / 'baremetal-compatible').glob(pattern)):
        keep(source, 'baremetal-compatible/' + str(source.relative_to(scratch / 'baremetal-compatible')))
for relative in ('gates.json', 'clang-sanitizers-build.log', 'clang-sanitizers-build.rc'):
    keep(scratch / 'validate' / relative, 'initial-environment/' + relative)
keep(scratch / 'sdk-setup-final.log', 'sdk-setup.log')
for name in ('GATES.json', 'INTEGRITY.json'):
    keep(scratch / 'published/author' / name, 'published-author/' + name)

pr = json.loads((scratch / 'pr18.json').read_text())
(receipts / 'pr-body.md').write_text(pr['body'])
summary = []
for filename in ('pr18-reviews.json', 'pr18-inline-comments.json', 'pr18-comments-final.json', 'issue14-comments-final.json'):
    entries = json.loads((scratch / filename).read_text())
    summary.append({'collection': filename, 'count': len(entries), 'ids': [e['id'] for e in entries], 'findings': [e['id'] for e in entries if 'FINDINGS' in e.get('body', '')]})
(receipts / 'prior-findings.json').write_text(json.dumps(summary, indent=2) + '\n')
for name in ('quality', 'baremetal'):
    source = scratch / ('hosted-' + name + '.log')
    text = source.read_text()
    # Keep only the checkout identity and executed validation output.
    lines = [line for line in text.splitlines() if re.search(r'HEAD is now|^[^ ]+ db950cfa|\b[a-z][a-z-]+: rc \d|"configuration"|"rc"|"unresolved_final"|"smoke"', line)]
    (receipts / ('hosted-' + name + '-extract.log')).write_text('\n'.join(lines) + '\n')
    records.append({'file': 'receipts/hosted-' + name + '-extract.log', 'original_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'extracted': True, 'selection': 'checkout identity and executed validation output'})
(receipts / 'NORMALIZATION.json').write_text(json.dumps(records, indent=2) + '\n')
print('receipt files collected:', len(records))
