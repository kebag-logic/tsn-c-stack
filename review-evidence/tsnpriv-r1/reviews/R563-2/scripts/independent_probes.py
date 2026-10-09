#!/usr/bin/env python3
"""Run focused privacy controls without changing source or creating commits."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('privacy_review', root / 'scripts/check_privacy.py')
gate = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(gate)
results = []

def record(name, actual, expected):
    results.append(dict(case=name, actual=actual, expected=expected, pass_=actual == expected))

holder = [gate.IDENTITY, gate.IDENTITY]
web = list(gate.WEB_FLOW)
ordinary = '0' * 40
cases = [
    ('holder', ordinary, holder + ['Subject'], 0),
    ('web-flow', ordinary, web + ['Subject (#1)'], 0),
    ('owner-exact', gate.OWNER_SQUASH, ['x <x@y.z>', 'x <x@y.z>', 'Subject', '', 'Body'], 0),
    ('owner-prefix-only', gate.OWNER_SQUASH[:7], ['x <x@y.z>', 'x <x@y.z>', 'Subject', '', 'Body'], 2),
    ('owner-nearby-hash', gate.OWNER_SQUASH[:-1] + '0', ['x <x@y.z>', 'x <x@y.z>', 'Subject', '', 'Body'], 2),
    ('mixed-noreply-holder', ordinary, [web[0], holder[1], 'Subject'], 1),
    ('mixed-holder-github', ordinary, [holder[0], web[1], 'Subject'], 1),
    ('other-noreply-account', ordinary, [web[0].replace('161579364+', '99999999+'), web[1], 'Subject'], 1),
    ('reversed', ordinary, web[::-1] + ['Subject'], 1),
    ('case-variant', ordinary, [web[0].lower(), web[1], 'Subject'], 1),
    ('holder-body', ordinary, holder + ['Subject', '', 'Body'], 1),
    ('web-body', ordinary, web + ['Subject', '', 'Body'], 1),
    ('holder-empty', ordinary, holder, 1),
    ('web-empty', ordinary, web, 1),
    ('foreign', ordinary, ['x <x@y.z>', 'x <x@y.z>', 'Subject'], 1),
]
for name, commit, lines, want in cases:
    record('helper/' + name, len(gate.commit_errors(commit, lines)), want)

for args, want in [([], 0), (['--selftest'], 0), (['--selftes'], 1), (['--selftest', '--extra'], 1), (['--selftest', '--selftest'], 1), (['--'], 1)]:
    proc = subprocess.run([sys.executable, str(root / 'scripts/check_privacy.py'), *args], cwd=root, capture_output=True, text=True)
    label = 'normal' if not args else '-'.join(a.lstrip('-') or 'separator' for a in args)
    (out / ('cli-' + label + '.log')).write_text(proc.stdout + proc.stderr)
    (out / ('cli-' + label + '.rc')).write_text(str(proc.returncode) + '\n')
    record('cli/' + label, proc.returncode, want)

original_git = gate.git
original_scan = gate.scan
original_commit_errors = gate.commit_errors
for name, commit, lines, want in cases:
    seen_commits = []
    scanned = []
    metadata = ('\n'.join(lines) + '\n').encode()
    def fake_git(*args):
        if args == ('rev-list', 'HEAD'): return (commit + '\n').encode()
        if args[:2] == ('show', '-s'): return metadata
        if args == ('rev-list', '--objects', 'HEAD'): return b''
        if args[0] == 'ls-files': return b''
        raise RuntimeError('Unexpected command in main control')
    def observe_check(c, ls):
        seen_commits.append(c)
        return original_commit_errors(c, ls)
    def observe_scan(label, data):
        scanned.append(label)
        return original_scan(label, data)
    gate.git, gate.commit_errors, gate.scan = fake_git, observe_check, observe_scan
    with contextlib.redirect_stdout(io.StringIO()):
        rc = int(gate.main())
    record('main/' + name, rc, int(want != 0))
    record('delegation/' + name, seen_commits, [commit])
    record('metadata-scanned/' + name, scanned, [commit])

for label, commit in [('owner-content', gate.OWNER_SQUASH), ('web-content', ordinary)]:
    def fake_git(*args):
        if args == ('rev-list', 'HEAD'): return (commit + '\n').encode()
        if args[:2] == ('show', '-s'): return ('\n'.join(web + ['Subject /' + 'tmp' + '/probe']) + '\n').encode()
        if args == ('rev-list', '--objects', 'HEAD'): return b''
        if args[0] == 'ls-files': return b''
        raise RuntimeError('Unexpected command in scan control')
    gate.git, gate.commit_errors, gate.scan = fake_git, original_commit_errors, original_scan
    with contextlib.redirect_stdout(io.StringIO()):
        rc = int(gate.main())
    record('main/' + label, rc, 1)

gate.git, gate.scan, gate.commit_errors = original_git, original_scan, original_commit_errors
(out / 'independent-probes.json').write_text(json.dumps(results, indent=2) + '\n')
for item in results:
    print(('PASS ' if item['pass_'] else 'FAIL ') + item['case'])
print(f'{sum(r["pass_"] for r in results)}/{len(results)} focused controls passed')
raise SystemExit(int(not all(r['pass_'] for r in results)))
