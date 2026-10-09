#!/usr/bin/env python3
"""Read exact-head hosted archives, verify API digests, and retain selected receipts.

Usage: python3 scripts/inspect_hosted.py PACKET
Requires authenticated, read-only repository access through gh.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

packet = Path(sys.argv[1]).resolve()
repo = 'repos/kebag-logic/tsn-c-stack'
head = 'b7c6b7ba0007aaa5791df68d30296423127b003e'
scratch = packet / 'scratch/hosted'
out = packet / 'receipts/hosted'
scratch.mkdir(parents=True, exist_ok=True)
out.mkdir(parents=True, exist_ok=True)


def api(endpoint):
    return subprocess.check_output(['gh', 'api', repo + endpoint])


def redact(data):
    text = data.decode()
    text = text.replace('<home-path>/work/tsn-c-stack/tsn-c-stack', '<checkout>')
    text = re.sub(r'<home-path>/work/_temp/[^\s:]+', '<temporary-file>', text)
    return text.encode()


def inspect(run):
    run_data = json.loads(api(f'/actions/runs/{run}'))
    assert run_data['head_sha'] == head
    artifacts = json.loads(api(f'/actions/runs/{run}/artifacts?per_page=100'))
    results = []
    for artifact in artifacts['artifacts']:
        archive = api(f"/actions/artifacts/{artifact['id']}/zip")
        digest = 'sha256:' + hashlib.sha256(archive).hexdigest()
        assert digest == artifact['digest']
        (scratch / f"{artifact['id']}.zip").write_bytes(archive)
        target = out / str(run) / artifact['name']
        target.mkdir(parents=True, exist_ok=True)
        retained = []
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for name in z.namelist():
                q = Path(name)
                top_quality = q.name in ['gates.json', 'privacy.log', 'privacy.rc', 'privacy-selftest.log',
                    'privacy-selftest.rc', 'gcc-test.log', 'clang-sanitizers-test.log', 'coverage.log', 'graphs.log',
                    'mutation.log', 'static-analysis.log', 'mutation-controls.log', 'boundary.log',
                    'assertion-templates.log', 'dependencies.log'] and len(q.parts) <= 2
                rv32 = artifact['name'] == 'rv32-evidence' and q.suffix in ('.json', '.log')
                if not (top_quality or rv32) or name.endswith('/'): continue
                assert not q.is_absolute() and '..' not in q.parts
                data = z.read(name)
                published = redact(data)
                dest = target / q
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(published)
                retained.append({'file': str(dest.relative_to(packet)),
                    'original_sha256': hashlib.sha256(data).hexdigest(),
                    'published_sha256': hashlib.sha256(published).hexdigest(),
                    'public_path_replacement': data != published})
        results.append({'run': run, 'head_sha': head, 'artifact': artifact['name'],
            'artifact_id': artifact['id'], 'verified_digest': digest, 'retained': retained})
    return results


with ThreadPoolExecutor(max_workers=2) as pool:
    records = [r for group in pool.map(inspect, [37934329322, 37934336629]) for r in group]
(out / 'archive-verification.json').write_text(json.dumps(records, indent=2) + '\n')
for record in records:
    print(record['run'], record['artifact'], 'digest verified;', len(record['retained']), 'receipts retained')
for gates in sorted(out.rglob('gates.json')):
    data = json.loads(gates.read_text())
    assert len(data) == 25 and all(x['rc'] == 0 for x in data)
    print(str(gates.relative_to(out)), '25/25 rc 0')
for results in sorted(out.rglob('results.json')):
    print(str(results.relative_to(out)), results.read_text())
