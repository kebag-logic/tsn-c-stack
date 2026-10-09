#!/usr/bin/env python3
"""Fetch the pinned public source files used by the focused probes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('output', type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
ref = '5603c353137e90c1fa95429f6d00ef7a2298d9ee'
files = ['sw/builder/endstation_builder.py', 'sw/firmware/ctrl/adp/adp_entity.py',
         'sw/firmware/ctrl/srp/srp_entity.py', 'configs/endstation_ax7101_1x1_tdm8.yaml',
         'docs/reference/FR_NFR.md']
rows = []
for file in files:
    data = subprocess.check_output(['gh', 'api', f'repos/kebag-logic/milan-fpga/contents/{file}?ref={ref}', '-H', 'Accept: application/vnd.github.raw+json'])
    (a.output/Path(file).name).write_bytes(data)
    rows.append({'path': file, 'revision': ref, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
print(json.dumps(rows, indent=2))
