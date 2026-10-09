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


DIRECTIVES = set('define undef include if ifdef ifndef elif else endif error warning line pragma'.split())
TRIGRAPHS = dict(zip("=/'()!<>-", '#\\^[]|{}~'))


def allowed(body):
    return bool(
        re.fullmatch(r'SPDX-License-Identifier: MIT', body)
        or re.fullmatch(r'SPDX-FileCopyrightText: \d{4}(?:-\d{4})? Kebag Logic', body)
        or re.fullmatch(r'REQ: [A-Z]+-\d+(?:, [A-Z]+-\d+)*', body)
        or re.fullmatch(REFERENCE + r'(?:; ' + REFERENCE + r')*', body))


def check(text, assembly=False):
    # C translation phases 1 and 2 precede comment recognition.
    text = re.sub(r'\?\?([=/\'()!<>-])', lambda m: TRIGRAPHS[m[1]], text)
    text = re.sub(r'\\\r?\n', '', text)
    errors = []
    masked = list(text)
    for match in TOKENS.finditer(text):
        token = match[0]
        masked[match.start():match.end()] = ['\n' if c == '\n' else ' ' for c in token]
        if not token.startswith(('//', '/*')):
            continue
        body = token[2:-2] if token.startswith('/*') else token[2:]
        for offset, line in enumerate(body.splitlines()):
            line = line.strip()
            if token.startswith('/*'):
                line = line.lstrip('*').strip()
            if line and not allowed(line):
                number = text.count('\n', 0, match.start()) + offset + 1
                errors.append(f'logical line {number}: unsupported comment')
    code = ''.join(masked)
    for number, line in enumerate(code.splitlines(), 1):
        directive = re.match(r'^\s*(?:#|%:)\s*(\w+)(.*)', line)
        if directive and directive[1] == 'if':
            expression = re.sub(r'[\s()]', '', directive[2])
            if re.match(r'0(?:[uUlL]*\b|[xX]0+[uUlL]*\b)', expression):
                errors.append(f'logical line {number}: #if 0 is forbidden')
        if assembly and '#' in line:
            if directive and directive[1] in DIRECTIVES:
                continue
            body = line.split('#', 1)[1].strip()
            if body and not allowed(body):
                errors.append(f'logical line {number}: unsupported assembly comment')
    return errors


def selftest():
    refused = {
        'line prose': ('// narrative', False),
        'clause prose': ('// IEEE 1722-2016 Figure 5 explains the field', False),
        'block prose': ('/* narrative */', False),
        'SPDX block prose': ('/* SPDX-License-Identifier: MIT\nnarrative\n*/', False),
        'decorated SPDX block prose': ('/* SPDX-License-Identifier: MIT\n * narrative\n */', False),
        'spliced SPDX prose': ('// SPDX-License-Identifier: MIT \\\nnarrative\n', False),
        'spliced delimiter': ('/\\\n/ narrative', False),
        'trigraph splice': ('// SPDX-License-Identifier: MIT ??/\nnarrative', False),
        'assembly prose': ('# Clear BSS\n_start:', True),
        'assembly trailing prose': ('nop # narrative', True),
        'assembly spliced prose': ('# SPDX-License-Identifier: MIT \\\nnarrative', True),
        'disabled region': ('#if 0\nnarrative\n#endif', False),
        'spliced disabled region': ('#i\\\nf 0\nnarrative\n#endif', False),
        'digraph disabled region': ('%:if (0)\nnarrative\n%:endif', False),
        'comment-separated disabled region': ('#if /* REQ: ADP-01 */ 0\n#endif', False),
    }
    accepted = {
        'SPDX line': ('// SPDX-License-Identifier: MIT', False),
        'SPDX block': ('/* SPDX-FileCopyrightText: 2026 Kebag Logic\n * SPDX-License-Identifier: MIT\n */', False),
        'requirements': ('// REQ: ADP-01, PORT-01', False),
        'standards': ('// IEEE 1722-2016 Table B.7; Milan v1.2 4.3.5.1', False),
        'block tracing': ('/* REQ: ADP-01\n * IEEE 1722.1-2021 6.2\n */', False),
        'string': ('const char *s = "// narrative";', False),
        'raw string': ('const char *s = R"(\n#if 0\n// narrative\n)";', False),
        'assembly SPDX': ('# SPDX-License-Identifier: MIT\n_start:', True),
        'assembly tracing': ('# IEEE 1722-2016 Figure 5\nnop # REQ: PORT-01', True),
        'assembly directives': ('#define LIMIT 4\n#if LIMIT\n#include "port.h"\n#endif', True),
        'spliced tracing': ('// IEEE 1722-2016 \\\nFigure 5', False),
    }
    for expected, controls in ((True, refused), (False, accepted)):
        for name, (source, assembly) in controls.items():
            if bool(check(source, assembly)) != expected:
                raise RuntimeError('comment control failed: ' + name)
            print('comment control ' + name + ': ' + ('refused' if expected else 'pass'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
    errors = []
    files = 0
    for directory in ('src', 'include', 'tests', 'examples'):
        for path in (ROOT / directory).rglob('*'):
            if path.suffix in ('.c', '.h', '.cpp', '.hpp', '.S', '.ld'):
                files += 1
                errors += [str(path.relative_to(ROOT)) + ': ' + e for e in check(path.read_text(), path.suffix == ".S")]
    for plant in json.loads((ROOT / 'tests/mutations.json').read_text()):
        for field in ('old', 'new'):
            errors += [plant['name'] + '/' + field + ': ' + e for e in check(plant[field])]
    print('\n'.join(errors) if errors else f'comments: {files} code files and all mutation fragments pass')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
