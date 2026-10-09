#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep source comments limited to licence, requirement and standard tracing."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKENS = re.compile(r'R"([^ ()\\\t\r\n]*)\(.*?\)\1"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/', re.S)
NUMBER = r'(?:B(?:\.\d+)*|\d+(?:[.-]\d+)*)'
REFERENCE = (r'(?:IEEE 1722\.1-2021|IEEE 1722-2016|Milan v1\.2) '
             r'(?:(?:Table|Figure|Annex) )?' + NUMBER +
             r'(?:\s*(?:and|to|/|-)\s*' + NUMBER + r')*')


def check(text):
    errors = []
    for match in TOKENS.finditer(text):
        token = match[0]
        if not token.startswith(('//', '/*')):
            continue
        body = token[2:-2].strip() if token.startswith('/*') else token[2:].strip()
        if body.startswith('SPDX-'):
            continue
        if re.fullmatch(r'REQ: [A-Z]+-\d+(?:, [A-Z]+-\d+)*', body):
            continue
        if re.fullmatch(REFERENCE + r'(?:; ' + REFERENCE + r')*', body):
            continue
        errors.append(f'line {text.count(chr(10), 0, match.start()) + 1}: unsupported comment')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        for source in ('// narrative', '// IEEE 1722-2016 Figure 5 explains the field', '/* narrative */'):
            assert check(source), source
        for source in ('// SPDX-License-Identifier: MIT', '// REQ: ADP-01, PORT-01',
                       '// IEEE 1722-2016 Table B.7; Milan v1.2 4.3.5.1',
                       'const char *s = "// narrative";'):
            assert not check(source), source
        print('comments: three prose controls refused; four tracing and string controls pass')
    errors = []
    files = 0
    for directory in ('src', 'include', 'tests', 'examples'):
        for path in (ROOT / directory).rglob('*'):
            if path.suffix in ('.c', '.h', '.cpp', '.hpp', '.S', '.ld'):
                files += 1
                errors += [str(path.relative_to(ROOT)) + ': ' + e for e in check(path.read_text())]
    for plant in json.loads((ROOT / 'tests/mutations.json').read_text()):
        for field in ('old', 'new'):
            errors += [plant['name'] + '/' + field + ': ' + e for e in check(plant[field])]
    print('\n'.join(errors) if errors else f'comments: {files} code files and all mutation fragments pass')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
