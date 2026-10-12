#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare C sources by non-comment raw tokens and by their source line numbers.

Usage: token_lines.py <clang-18> <left> <right> [<left> <right> ...]
For each pair prints the token counts, token equality, and (kind, spelling, line)
equality. The comparison uses the Clang raw lexer (-cc1 -dump-raw-tokens) in C11
mode; comments and whitespace are dropped, directives and macros stay as written.
Exits 1 when any pair differs in tokens or token lines.
"""
import re
import subprocess
import sys

LINE = re.compile(r"^([a-z_][a-z_0-9]*) '(.*)'\s+(?:\[[^\]]*\]\s*)?Loc=<[^:>]*:(\d+):(\d+)>")


def tokens(clang, path):
    out = subprocess.run([clang, '-cc1', '-x', 'c', '-std=c11', '-dump-raw-tokens', path],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit('raw lexing failed: ' + path + ': ' + out.stderr[:300])
    result = []
    for line in out.stderr.splitlines():
        m = LINE.match(line)
        if not m:
            continue
        kind, spelling, ln, col = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        if kind == 'comment' or (kind == 'unknown' and spelling.strip() == ''):
            continue
        result.append((kind, spelling, ln, col))
    if not result:
        raise SystemExit('no tokens: ' + path)
    return result


def main(argv):
    if len(argv) < 4 or len(argv[2:]) % 2:
        raise SystemExit(__doc__)
    clang, rest = argv[1], argv[2:]
    bad = 0
    for left, right in zip(rest[::2], rest[1::2]):
        a, b = tokens(clang, left), tokens(clang, right)
        same_tok = [t[:2] for t in a] == [t[:2] for t in b]
        same_line = [t[:3] for t in a] == [t[:3] for t in b]
        same_col = a == b
        print(f'{left} vs {right}: tokens {len(a)}/{len(b)} {"EQUAL" if same_tok else "DIFFER"}; '
              f'token lines {"EQUAL" if same_line else "DIFFER"}; token columns {"EQUAL" if same_col else "DIFFER"}')
        shown = 0
        for x, y in zip(a, b):
            if x[:3] != y[:3] and shown < 3:
                print(f'  first difference: {x} != {y}')
                shown += 1
        bad |= not (same_tok and same_line)
    return int(bad)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
