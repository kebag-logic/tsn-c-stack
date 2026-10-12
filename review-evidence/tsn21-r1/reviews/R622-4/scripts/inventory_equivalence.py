#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare assertion_messages.inventory() before (old tree) and after (new tree) on the new tree's test files.
usage: inventory_equivalence.py <old-tree> <new-tree>"""
import importlib.util, sys
from pathlib import Path
old, new = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
def load(tree, tag):
    sys.path.insert(0, str(tree / 'scripts'))
    for m in ('assertion_messages', 'compiler_tokens', 'assertion_forms'):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location('am_' + tag, tree / 'scripts/assertion_messages.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod.inventory
fo, fn = load(old, 'old'), load(new, 'new')
bad = 0; total = 0
for path in sorted((new / 'tests').glob('test_*.cpp')):
    text = path.read_text()
    a, b = fo(text), fn(text)
    n = sum(len(v) for v in b.values()); total += n
    same = a == b
    bad += not same
    print(f'{path.name}: tests {len(b)} literals {n} {"IDENTICAL" if same else "DIFFERENT"}')
print('files', len(list((new / 'tests').glob('test_*.cpp'))), 'literals', total, 'different', bad)
sys.exit(1 if bad else 0)
