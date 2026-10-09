#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replace host locations in published receipts with neutral placeholders.
Usage: sanitize.py <packet> OLD=PLACEHOLDER [OLD=PLACEHOLDER ...]  (longest OLD first)"""
import sys
from pathlib import Path
packet = Path(sys.argv[1])
subs = [arg.split("=", 1) for arg in sys.argv[2:]]
for path in (packet / "receipts").rglob("*"):
    if path.is_file():
        text = path.read_text(errors="strict")
        new = text
        for old, rep in subs:
            new = new.replace(old, rep)
        if new != text:
            path.write_text(new)
            print("sanitized", path.relative_to(packet))
