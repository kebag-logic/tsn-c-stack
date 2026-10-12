#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Record-level union audit of tests/mutations.json across base, main, port and merge commits.
usage: merge_audit.py <git-dir> <base> <main> <port> <merge>"""
import json, subprocess, sys
g, base, main, port, merge = sys.argv[1:6]
def load(rev):
    return json.loads(subprocess.run(['git', '-C', g, 'show', rev + ':tests/mutations.json'],
                                     capture_output=True, check=True, text=True).stdout)
B, A, P, M = (load(r) for r in (base, main, port, merge))
def by(lst):
    d = {}
    for m in lst:
        assert m['name'] not in d, 'duplicate ' + m['name']
        d[m['name']] = m
    return d
b, a, p, m = by(B), by(A), by(P), by(M)
errors = []
for name in set(a) | set(p) | set(b):
    ca = a.get(name) != b.get(name); cp = p.get(name) != b.get(name)
    if ca and cp and a.get(name) != p.get(name):
        errors.append('both sides changed ' + name)
    want = a.get(name) if ca else p.get(name)
    if m.get(name) != want:
        errors.append('merge record differs for ' + name)
extra = set(m) - (set(a) | set(p))
errors += ['extra ' + n for n in sorted(extra)]
print(json.dumps(dict(base=len(B), main=len(A), port=len(P), merge=len(M),
                      main_changed=sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n)),
                      port_changed=sorted(n for n in set(p) | set(b) if p.get(n) != b.get(n)),
                      errors=errors), indent=1))
sys.exit(1 if errors else 0)
