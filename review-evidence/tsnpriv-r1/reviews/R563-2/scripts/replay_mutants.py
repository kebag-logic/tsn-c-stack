#!/usr/bin/env python3
"""Replay the published nine substitutions, without creating synthetic commits.

Usage: replay_mutants.py SOURCE PUBLISHED_SCRIPT SCRATCH RECEIPTS
The published script's declarations and MUTANTS are evaluated unchanged.
Only its selftest detector is replayed; old-head checkout and synthetic-history
creation are deliberately omitted to preserve the no-commit review boundary.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root, published, scratch, out = (Path(p).resolve() for p in sys.argv[1:])
scratch.mkdir(parents=True, exist_ok=True)
out.mkdir(parents=True, exist_ok=True)
source = (root / 'scripts/check_privacy.py').read_text()
raw = published.read_bytes()
module = ast.parse(raw, filename=published.name)
declarations = []
for node in module.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        break
    declarations.append(node)
namespace = {'__name__': 'published_mutant_declarations'}
saved_argv = sys.argv
try:
    sys.argv = [str(published), str(root)]
    exec(compile(ast.Module(body=declarations, type_ignores=[]), published.name, 'exec'), namespace)
finally:
    sys.argv = saved_argv
rows = []
for number, (name, edits) in enumerate(namespace['MUTANTS'].items()):
    changed = source
    for before, after in edits:
        if changed.count(before) != 1:
            raise RuntimeError(f'Nonunique published anchor: {name}')
        changed = changed.replace(before, after)
    case = scratch / f'case-{number:02d}' / 'scripts'
    case.mkdir(parents=True, exist_ok=True)
    gate = case / 'check_privacy.py'
    gate.write_text(changed)
    run = subprocess.run([sys.executable, '-I', str(gate), '--selftest'], capture_output=True, text=True)
    optimized = subprocess.run([sys.executable, '-I', '-O', str(gate), '--selftest'], capture_output=True, text=True)
    (out / f'mutant-{number:02d}.log').write_text(run.stdout + run.stderr)
    (out / f'mutant-{number:02d}.rc').write_text(str(run.returncode) + '\n')
    (out / f'mutant-{number:02d}-optimized.log').write_text(optimized.stdout + optimized.stderr)
    (out / f'mutant-{number:02d}-optimized.rc').write_text(str(optimized.returncode) + '\n')
    want_zero = not edits
    passed = (run.returncode == 0) == want_zero and (optimized.returncode == 0) == want_zero
    if edits and 'privacy selftest: fail ' not in run.stdout:
        passed = False
    rows.append(dict(name=name, substitutions=len(edits), selftest_rc=run.returncode,
                     optimized_selftest_rc=optimized.returncode, passed=passed))
    print(f'{name}\t{run.returncode}\t{optimized.returncode}\t{"PASS" if passed else "FAIL"}')
summary = dict(head=subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
               published_script_sha256=hashlib.sha256(raw).hexdigest(),
               original_script_unchanged=True, detector='real --selftest, normal and optimized Python',
               adaptation='Replay published substitutions only; omit old-head checkout and synthetic commit creation',
               cases=rows)
(out / 'mutant-results.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(int(not all(r['passed'] for r in rows)))
