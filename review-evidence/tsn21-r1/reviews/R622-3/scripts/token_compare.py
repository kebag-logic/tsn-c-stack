#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare non-comment compiler tokens of two C files, with line and column.
Usage: TSN_CLANG=<clang-18> token_compare.py <repo scripts dir> <left> <right>"""
import sys
sys.path.insert(0, sys.argv[1])
from compiler_tokens import raw_tokens


def lexed(path):
    text = open(path, encoding='utf-8').read()
    starts = [0] + [i + 1 for i, c in enumerate(text.encode()) if c == 10]
    out = []
    for kind, value, start, _, line in raw_tokens(text, 'c'):
        if kind == 'comment' or (kind == 'unknown' and value.isspace()):
            continue
        out.append((kind, value, line, start - starts[line - 1] + 1))
    return out


left, right = lexed(sys.argv[2]), lexed(sys.argv[3])
values = [t[:2] for t in left] == [t[:2] for t in right]
positions = left == right
first = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)
print(f'{sys.argv[2]} vs {sys.argv[3]}: tokens {len(left)}/{len(right)}; '
      f'values {"EQUAL" if values else "DIFFER"}; line+column {"EQUAL" if positions else "DIFFER"}'
      + ('' if first is None else f'; first difference {left[first]} vs {right[first]}'))
sys.exit(0 if values and positions else 1)
