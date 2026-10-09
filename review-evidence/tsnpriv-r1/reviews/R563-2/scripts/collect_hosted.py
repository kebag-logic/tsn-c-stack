#!/usr/bin/env python3
"""Read exact-head public job metadata and verify downloaded artifact digests.

Usage: collect_hosted.py PACKET
All downloads and extraction stay in PACKET/scratch. Published raw receipts
are selected JSON, rc files, and logs without local-machine path rewriting.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

packet = Path(sys.argv[1]).resolve()
receipts = packet / 'receipts'
scratch = packet / 'scratch' / 'hosted'
receipts.mkdir(exist_ok=True)
scratch.mkdir(parents=True, exist_ok=True)
head = 'b7c6b7ba0007aaa5791df68d30296423127b003e'
base = 'repos/kebag-logic/tsn-c-stack'

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', f'{base}/{endpoint}']))

def save(name, data):
    (receipts / name).write_text(json.dumps(data, indent=2) + '\n')

runs = api('actions/runs?head_sha=' + head)['workflow_runs']
artifacts = []
for run in runs:
    rid = run['id']
    if run['head_sha'] != head:
        raise RuntimeError('Wrong run head')
    jobs = api(f'actions/runs/{rid}/jobs')
    summary = {'run': {k: run[k] for k in ['id', 'head_sha', 'event', 'status', 'conclusion', 'html_url']},
               'jobs': [{k: j[k] for k in ['id', 'name', 'head_sha', 'status', 'conclusion', 'started_at', 'completed_at', 'html_url', 'steps']} for j in jobs['jobs']]}
    save(f'hosted-jobs-{rid}.json', summary)
    print(rid, run['event'], [(j['name'], j['conclusion']) for j in jobs['jobs']])
    for artifact in api(f'actions/runs/{rid}/artifacts')['artifacts']:
        artifact['review_run'] = rid
        artifacts.append(artifact)

def download(a):
    data = subprocess.check_output(['gh', 'api', f'{base}/actions/artifacts/{a["id"]}/zip'])
    digest = 'sha256:' + hashlib.sha256(data).hexdigest()
    if digest != a['digest']:
        raise RuntimeError('Artifact digest mismatch')
    archive = scratch / f'{a["review_run"]}-{a["name"]}.zip'
    archive.write_bytes(data)
    dest = scratch / str(a['review_run']) / a['name']
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            target = (dest / info.filename).resolve()
            if not target.is_relative_to(dest.resolve()):
                raise RuntimeError('Unsafe artifact path')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
    return dict(run=a['review_run'], id=a['id'], name=a['name'], head=a['workflow_run']['head_sha'],
                expected_digest=a['digest'], actual_digest=digest, verified=True)

with ThreadPoolExecutor(max_workers=4) as pool:
    verified = list(pool.map(download, artifacts))
save('artifact-digests.json', verified)

selected = {'gates.json', 'privacy.log', 'privacy.rc', 'privacy-selftest.log', 'privacy-selftest.rc',
            'gcc-test.log', 'gcc-test.rc', 'clang-sanitizers-test.log', 'clang-sanitizers-test.rc',
            'coverage.log', 'coverage.rc', 'graphs.log', 'graphs.rc', 'mutation.rc', 'static-analysis.rc'}
for item in verified:
    src = scratch / str(item['run']) / item['name']
    dst = receipts / 'hosted' / str(item['run']) / item['name']
    dst.mkdir(parents=True, exist_ok=True)
    if item['name'] == 'quality-evidence':
        for file in src.iterdir():
            if file.name in selected:
                (dst / file.name).write_bytes(file.read_bytes())
        gates = json.loads((src / 'gates.json').read_text())
        if not all(g['rc'] == 0 for g in gates):
            raise RuntimeError('Hosted gate failure')
        print(item['run'], 'gates', len(gates), 'all rc 0')
        mutation = json.loads((src / 'mutations/results.json').read_text())
        (dst / 'mutation-results.json').write_text(json.dumps(mutation, indent=2) + '\n')
    elif item['name'] == 'rv32-evidence':
        for file in src.rglob('*'):
            if file.is_file() and (file.name == 'results.json' or file.name == 'smoke.log'):
                target = dst / file.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(file.read_bytes())
print('Verified', len(verified), 'artifact archives')
