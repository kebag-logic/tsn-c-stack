#!/usr/bin/env python3
"""Restore the archived exact-head public run, downloading it if not packaged."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

packet=Path(__file__).resolve().parents[1]
scratch=packet/'scratch'; scratch.mkdir(exist_ok=True)
def api(path): return subprocess.check_output(['gh','api','repos/kebag-logic/tsn-c-stack/'+path])
meta=packet/'receipts/hosted-artifacts.json'
if not meta.exists(): meta.write_bytes(api('actions/runs/38186240742/artifacts'))
artifacts=json.loads(meta.read_text())
(scratch/'hosted-artifacts.json').write_text(json.dumps(artifacts))
jobs=packet/'receipts/hosted-jobs.json'
if not jobs.exists(): jobs.write_bytes(api('actions/runs/38186240742/jobs?per_page=100'))
for item in artifacts['artifacts']:
    name={'quality-evidence':'quality','rv32-evidence':'rv32'}[item['name']]
    target=scratch/f'hosted-{name}.zip'
    packaged=packet/f'receipts/hosted-{name}.zip'
    if packaged.exists(): shutil.copyfile(packaged,target)
    else: target.write_bytes(api(f'actions/artifacts/{item["id"]}/zip'))
    digest='sha256:'+hashlib.sha256(target.read_bytes()).hexdigest()
    assert digest==item['digest']
    with zipfile.ZipFile(target) as archive: archive.extractall(scratch/f'hosted-{name}')
    print(name,digest)
