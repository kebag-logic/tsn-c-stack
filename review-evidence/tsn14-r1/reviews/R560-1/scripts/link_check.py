#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check relative Markdown links and anchors in the given files (GitHub anchor rules, explicit ids)."""
import re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
def anchors(p):
    t = p.read_text()
    out = set(re.findall(r'id="([^"]+)"', t))
    seen = {}
    for h in re.findall(r'^#+ (.+)$', t, re.M):
        a = re.sub(r'[^\w\- ]', '', h.strip().lower()).replace(' ', '-')
        n = seen.get(a, 0); seen[a] = n + 1
        out.add(a if n == 0 else f'{a}-{n}')
    return out
bad = 0; n = 0
for f in sys.argv[2:]:
    p = root / f
    text = p.read_text()
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    for m in re.finditer(r'\]\(([^)\s]+)\)', text):
        url = m[1]
        if re.match(r'[a-z]+://|mailto:', url): continue
        n += 1
        path, _, frag = url.partition('#')
        target = (p.parent / path).resolve() if path else p
        if not target.exists():
            bad += 1; print(f'{f}: missing file {url}'); continue
        if frag and target.suffix == '.md' and frag not in anchors(target):
            bad += 1; print(f'{f}: missing anchor {url}')
        if frag and target.suffix != '.md' and not re.fullmatch(r'L\d+(-L\d+)?', frag):
            bad += 1; print(f'{f}: odd fragment {url}')
        if frag and target.suffix != '.md':
            m2 = re.fullmatch(r'L(\d+)', frag)
            if m2 and int(m2[1]) > len(target.read_text().splitlines()):
                bad += 1; print(f'{f}: line past end {url}')
print(f'relative links checked: {n}; broken: {bad}')
sys.exit(1 if bad else 0)
