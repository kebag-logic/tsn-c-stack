#!/usr/bin/env python3
"""Fetch only the two pinned public source registers needed by audit-source.py."""
import hashlib
from pathlib import Path
import subprocess
import sys

packet = Path(sys.argv[1]).resolve()
destination = packet / 'scratch/authorities'
destination.mkdir(parents=True, exist_ok=True)
pin = '5603c353137e90c1fa95429f6d00ef7a2298d9ee'
for name, expected in [
    ('docs/reference/FR_NFR.md', '7ca56fa950c00c0a9623087fc141b8a0aa99db0fa0e421c5bf667e0d2d7067f1'),
    ('REQUIREMENTS.md', '10bac6a48664f607fb99b3ed89505da4ebc4ee80282582f4200b1b8227e75ab5')]:
    data = subprocess.check_output(['gh', 'api', 'repos/kebag-logic/milan-fpga/contents/' + name + '?ref=' + pin, '-H', 'Accept: application/vnd.github.raw+json'])
    assert hashlib.sha256(data).hexdigest() == expected
    (destination / Path(name).name).write_bytes(data)
    print(name, expected)
