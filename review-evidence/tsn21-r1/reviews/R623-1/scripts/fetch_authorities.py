#!/usr/bin/env python3
"""Download only named public repository authorities, never local author material."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

PACKET = Path(__file__).resolve().parents[1]
REF = '09c7231eca343607c97c0d66abebb2553688712c'
PATHS = ['sw/firmware/ctrl/acmp/acmp.c', 'sw/firmware/ctrl/acmp/acmp.h',
         'sw/firmware/ctrl/wire/wire.h', 'sw/firmware/ctrl/test/test_acmp.cpp',
         'sw/firmware/ctrl/test/acmp_fake.hpp', 'docs/ARCHITECTURE_HW_SW_SPLIT.md',
         'docs/design/MAILBOX_SPLIT.md', 'docs/reference/MAILBOX_CONTRACT.md',
         'sw/firmware/ctrl/acmp/acmp_mbx.c', 'sw/mailbox/mailbox.yaml',
         'hdl/milan/mailbox/KL_mbx.sv']

def fetch(task):
    path, ref, target = task
    raw = subprocess.check_output(['gh', 'api', f'repos/kebag-logic/milan-fpga/contents/{path}?ref={ref}'])
    data = json.loads(raw)
    dest = PACKET / 'scratch' / target
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = base64.b64decode(data['content'])
    dest.write_bytes(content)
    return {'path': path, 'ref': ref, 'blob': data['sha'], 'bytes': len(content)}

tasks = [(path, REF, 'upstream/' + path) for path in PATHS]
tasks += [('sw/firmware/ctrl/acmp/acmp.' + suffix,
           '0a62616e08dd58928e73183ecdf16dbee330becd', 'pre-fint-acmp.' + suffix)
          for suffix in ['c', 'h']]
with ThreadPoolExecutor(max_workers=4) as pool:
    rows = list(pool.map(fetch, tasks))
(PACKET / 'receipts/authority-files.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
