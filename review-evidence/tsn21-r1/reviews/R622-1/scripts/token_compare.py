#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare C sources by their non-comment tokens, two independent ways.

Method A: the Clang 18 raw lexer (-cc1 -dump-raw-tokens), dropping comment and
whitespace tokens, so macros and directives stay as written.
Method B: GCC's comment removal without macro expansion (-fpreprocessed -E),
then whitespace collapsed between the remaining characters.

Usage: token_compare.py <clang-18> <gcc> <left> <right> [<left> <right> ...]
Prints one line per pair and exits 1 when any pair differs in either method.
"""
import hashlib
import re
import subprocess
import sys


def clang_tokens(clang, path):
    out = subprocess.run([clang, '-cc1', '-x', 'c', '-std=c11', '-dump-raw-tokens', path],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit('clang raw lexing failed for ' + path + ': ' + out.stderr[:400])
    tokens = []
    for line in out.stderr.splitlines():
        m = re.match(r"^([a-z_][a-z_0-9]*) '(.*)'\s+(?:\[[^\]]*\]\s*)?Loc=<", line)
        if not m:
            continue
        kind, spelling = m.group(1), m.group(2)
        if kind == 'comment' or (kind == 'unknown' and spelling.strip() == ''):
            continue
        tokens.append((kind, spelling))
    return tokens


def gcc_text(gcc, path):
    out = subprocess.run([gcc, '-fpreprocessed', '-dD', '-E', '-P', '-x', 'c', path],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit('gcc comment removal failed for ' + path + ': ' + out.stderr[:400])
    return re.sub(r'\s+', ' ', out.stdout).strip()


def digest(obj):
    return hashlib.sha256(repr(obj).encode()).hexdigest()[:16]


def main(argv):
    if len(argv) < 5 or len(argv[3:]) % 2:
        raise SystemExit(__doc__)
    clang, gcc, rest = argv[1], argv[2], argv[3:]
    bad = 0
    for left, right in zip(rest[::2], rest[1::2]):
        a, b = clang_tokens(clang, left), clang_tokens(clang, right)
        ga, gb = gcc_text(gcc, left), gcc_text(gcc, right)
        same_a, same_b = a == b, ga == gb
        print(f'{left} vs {right}: clang-tokens {len(a)}/{len(b)} '
              f'{"EQUAL" if same_a else "DIFFER"} [{digest(a)} {digest(b)}]; '
              f'gcc-stripped {"EQUAL" if same_b else "DIFFER"}')
        if not same_a:
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print(f'  first token difference at {i}: {x} != {y}')
                    break
        bad |= not (same_a and same_b)
    return int(bad)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
