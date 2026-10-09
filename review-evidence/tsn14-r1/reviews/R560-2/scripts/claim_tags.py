# SPDX-License-Identifier: MIT
"""Map claim_probe.py failures to `// REQ:` tags at the reviewed tree.

Usage: python3 -I claim_tags.py <repo> <result.json>...
Each argument after the repo is NAME=REQ1+REQ2:path; a probe passes when at
least one failing test carries every listed requirement.
"""
import json, re, sys
from pathlib import Path

repo = Path(sys.argv[1])
tags = {}
for f in (repo / 'tests').glob('*.cpp'):
    lines = f.read_text().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'\s*TEST(?:_F|_P)?\(\s*(\w+)\s*,\s*(\w+)\s*\)', line)
        if m:
            j, req = i - 1, []
            while j >= 0 and lines[j].startswith('//'):
                r = re.match(r'// REQ:\s*(.+)', lines[j])
                if r:
                    req += [x.strip() for x in r.group(1).split(',')]
                j -= 1
            tags[f'{m.group(1)}.{m.group(2)}'] = req
rc = 0
for arg in sys.argv[2:]:
    spec, path = arg.split(':', 1)
    name, _, need = spec.partition('=')
    need = set(filter(None, need.split('+')))
    d = json.loads(Path(path).read_text())
    rows = {t: tags.get(t, []) for t in d['failed']}
    killers = [t for t, r in rows.items() if need <= set(r)]
    ok = (not d['failed'] and d['build_rc'] == 0) if not need else bool(killers) and d['build_rc'] == 0
    rc |= not ok
    print(f"{name}: build_rc={d['build_rc']} needs={sorted(need)} -> {'PASS' if ok else 'FAIL'}")
    for t, r in sorted(rows.items()):
        print(f"   failed {t} tags={r}{'  <- tagged killer' if t in killers else ''}")
sys.exit(rc)
