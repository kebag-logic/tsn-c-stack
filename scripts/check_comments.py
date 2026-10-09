#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep source comments limited to licence, requirement and standard tracing."""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compiler_tokens import compiler, logical, raw_tokens
from conditional_policy import DIRECTIVES, inspect

ROOT = Path(__file__).resolve().parents[1]
NUMBER = r'(?:B(?:\.\d+)*|\d+(?:[.-]\d+)*)'
REFERENCE = (r'(?:IEEE 1722\.1-2021|IEEE 1722-2016|Milan v1\.2) '
             r'(?:(?:Table|Figure|Annex) )?' + NUMBER +
             r'(?:\s*(?:and|to|/|-)\s*' + NUMBER + r')*')


def allowed(body):
    return bool(
        re.fullmatch(r'SPDX-License-Identifier: MIT', body)
        or re.fullmatch(r'SPDX-FileCopyrightText: \d{4}(?:-\d{4})? Kebag Logic', body)
        or re.fullmatch(r'REQ: [A-Z]+-\d+(?:, [A-Z]+-\d+)*', body)
        or re.fullmatch(REFERENCE + r'(?:; ' + REFERENCE + r')*', body))


def comment_errors(value, line):
    body = value[2:-2] if value.startswith('/*') else value[2:]
    errors = []
    for offset, part in enumerate(body.splitlines()):
        part = part.strip()
        if value.startswith('/*'):
            part = part.lstrip('*').strip()
        if part and not allowed(part):
            errors.append(f'line {line + offset}: unsupported comment')
    return errors


def check(text, assembly=False, language='c++', path=None, fragment=False):
    errors = []
    if assembly:
        if "'" in text:
            errors.append('single quotes are forbidden in assembly')
        # Hash comments have no quote escape in the permitted assembly subset.
        lines = logical(text).splitlines(keepends=True)
        for number, line in enumerate(lines, 1):
            first = line.lstrip()
            words = first[1:].lstrip().split() if first.startswith('#') else []
            directive = bool(words and words[0] in DIRECTIVES)
            start = line.index('#') + 1 if directive else 0
            at = line.find('#', start)
            if at >= 0:
                errors += comment_errors('//' + line[at + 1:], number)
                lines[number - 1] = line[:at] + '\n'
        text = ''.join(lines)
        language = 'c'
    tokens = raw_tokens(text, language)
    for kind, value, _, _, number in tokens:
        if kind == 'comment':
            errors += comment_errors(value, number)
    if assembly:
        code = [t for t in tokens if t[0] != 'comment' and not t[1].isspace()]
        for previous, token in zip(code, code[1:]):
            if previous[1] == '.' and (token[1].lower().startswith('if') or
                    token[1].lower() in ('macro', 'rept', 'irp', 'irpc')):
                errors.append(f'line {token[4]}: assembler conditional or macro is forbidden')
    errors += inspect(tokens, path, fragment)[0]
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--work', type=Path, default=ROOT / 'build-comment-controls')
    args = parser.parse_args()
    print('comment lexer: ' + compiler())
    if args.selftest:
        from comment_selftest import selftest
        selftest(args.work)
    errors = []
    files = 0
    for directory in ('src', 'include', 'tests', 'examples'):
        for path in sorted((ROOT / directory).rglob('*')):
            if path.suffix in ('.c', '.h', '.cpp', '.hpp', '.S', '.ld'):
                files += 1
                relative = path.relative_to(ROOT).as_posix()
                errors += [relative + ': ' + e for e in check(
                    path.read_text(), path.suffix == '.S',
                    'c++' if path.suffix in ('.cpp', '.hpp') else 'c', relative)]
    for plant in json.loads((ROOT / 'tests/mutations.json').read_text()):
        for field in ('old', 'new'):
            errors += [plant['name'] + '/' + field + ': ' + e
                       for e in check(plant[field], language='c', fragment=True)]
    print('\n'.join(errors) if errors else f'comments: {files} code files and all mutation fragments pass')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
