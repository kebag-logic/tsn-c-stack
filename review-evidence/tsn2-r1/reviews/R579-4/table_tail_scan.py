#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Report Markdown tables whose last row is followed by a non-blank, non-table line.

Usage: table_tail_scan.py FILE...   (exit 1 if any table runs into following text)
Lines inside fenced code blocks are ignored.
"""
import sys

bad = 0
for path in sys.argv[1:]:
    lines = open(path, encoding='utf-8').read().split('\n')
    fence = False
    for i, line in enumerate(lines[:-1]):
        if line.lstrip().startswith(('```', '~~~')):
            fence = not fence
        if fence:
            continue
        nxt = lines[i + 1]
        if line.startswith('|') and nxt.strip() and not nxt.startswith('|') and not nxt.lstrip().startswith(('```', '~~~')):
            print(f'{path}:{i + 2}: text directly after table row: {nxt[:80]}')
            bad += 1
print('tables running into text:', bad)
sys.exit(1 if bad else 0)
