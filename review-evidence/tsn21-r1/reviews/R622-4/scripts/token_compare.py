#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare non-comment raw tokens (spelling, line, column) of two C files with clang -dump-raw-tokens."""
import re, subprocess, sys

def toks(path, clang):
    r = subprocess.run([clang, '-cc1', '-x', 'c', '-std=c11', '-dump-raw-tokens', path],
                       capture_output=True, text=True)
    out = []
    for m in re.finditer(r"^([a-z_][a-z_0-9]*) '(.*?)'\s.*?Loc=<[^:]+:(\d+):(\d+)>", r.stderr, re.M | re.S):
        if m[1] == 'comment' or (m[1] == 'unknown' and not m[2].strip()):
            continue  # comments and whitespace runs are not tokens
        out.append((m[1], m[2], int(m[3]), int(m[4])))
    return out

clang = sys.argv[3] if len(sys.argv) > 3 else 'clang'
a, b = toks(sys.argv[1], clang), toks(sys.argv[2], clang)
same_tok = [x[:2] for x in a] == [x[:2] for x in b]
same_pos = a == b
print(f'{sys.argv[1]} vs {sys.argv[2]}: tokens {len(a)}/{len(b)} spelling {"EQUAL" if same_tok else "DIFFER"}; positions {"EQUAL" if same_pos else "DIFFER"}')
if not same_pos:
    for x, y in zip(a, b):
        if x != y:
            print('first difference', x, y); break
sys.exit(0 if same_pos else 1)
