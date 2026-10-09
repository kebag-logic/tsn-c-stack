#!/usr/bin/env python3
"""Replay focused privacy controls without creating commits or modifying the source checkout.

Usage: python3 scripts/focused_review.py SOURCE PACKET
The published R562-1 probe must be present in receipts/published/reviews/R562-1/scripts/.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

SOURCE = Path(sys.argv[1]).resolve()
PACKET = Path(sys.argv[2]).resolve()
SCRATCH = PACKET / 'scratch' / 'focused'
RECEIPTS = PACKET / 'receipts' / 'focused'
SCRATCH.mkdir(parents=True, exist_ok=True)
RECEIPTS.mkdir(parents=True, exist_ok=True)
HEAD = 'b7c6b7ba0007aaa5791df68d30296423127b003e'
BASE = '18d737832c376f32660eb21fe2796e0b611507e3'
OWNER = 'ae982af85ec97286bd35b39403926d8f0eaec81d'
HOLDER = 'hackerman-kl <hackerman-kl@kebag-logic.com>'
AUTHOR = 'hackerman-kl <161579364+Mister-M-alt@users.noreply.github.com>'
COMMITTER = 'GitHub <noreply@github.com>'
ORIGINAL = (SOURCE / 'scripts/check_privacy.py').read_text()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def save(name, result):
    (RECEIPTS / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')


def cli():
    root = SCRATCH / 'cli'
    (root / 'scripts').mkdir(parents=True, exist_ok=True)
    gate = root / 'scripts/check_privacy.py'
    gate.write_text(ORIGINAL)
    records = []
    for name, args, want in [
        ('selftest', ['--selftest'], 0), ('misspelled', ['--selftst'], 1),
        ('unknown', ['--bogus'], 1), ('repeat', ['--selftest', '--selftest'], 1),
        ('combined', ['--selftest', '--bogus'], 1), ('positional', ['extra'], 1),
    ]:
        r = subprocess.run([sys.executable, '-I', str(gate), *args], capture_output=True, text=True)
        (RECEIPTS / (name + '.log')).write_text(r.stdout + r.stderr)
        (RECEIPTS / (name + '.rc')).write_text(str(r.returncode) + '\n')
        assert r.returncode == want, (name, r.returncode)
        records.append({'case': name, 'rc': r.returncode, 'expected_rc': want})
    save('cli', records)
    return 'CLI: 11 commit controls pass; five unknown/repeated/combined argument vectors refused'


def mutants():
    published = PACKET / 'receipts/published/reviews/R562-1/scripts/mutant_probes.py'
    parsed = ast.parse(published.read_text())
    selected = [n for n in parsed.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id in ('OK', 'MUTANTS') for t in n.targets)]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(published), 'exec'), namespace)
    cases = namespace['MUTANTS']
    assert len(cases) == 10
    records = []
    for i, (name, edits) in enumerate(cases.items()):
        data = ORIGINAL
        for old, new in edits:
            assert data.count(old) == 1, (name, old)
            data = data.replace(old, new)
        root = SCRATCH / ('mutant-' + str(i))
        (root / 'scripts').mkdir(parents=True, exist_ok=True)
        gate = root / 'scripts/check_privacy.py'
        gate.write_text(data)
        r = subprocess.run([sys.executable, '-I', str(gate), '--selftest'], capture_output=True, text=True)
        want = 0 if i == 0 else 1
        assert r.returncode == want, (name, r.returncode, r.stdout, r.stderr)
        assert r.stdout.startswith('privacy selftest: ' + ('11 commit controls pass' if i == 0 else 'fail '))
        assert not r.stderr
        (RECEIPTS / ('mutant-' + str(i) + '.log')).write_text(r.stdout + r.stderr)
        (RECEIPTS / ('mutant-' + str(i) + '.rc')).write_text(str(r.returncode) + '\n')
        records.append({'case': name, 'rc': r.returncode, 'expected_rc': want,
                        'planted_sha256': hashlib.sha256(data.encode()).hexdigest()})
        gate.write_text(ORIGINAL)
        assert gate.read_bytes() == ORIGINAL.encode()
    save('r562-1-mutants', records)
    return 'R562-1 nine original fault transformations: 9/9 selftest refusals; unmutated control rc 0; copies restored'


def behavior():
    gate_path = SCRATCH / 'behavior.py'
    gate_path.write_text(ORIGINAL)
    gate = module(gate_path, 'review_behavior')
    identities = [HOLDER, AUTHOR, COMMITTER, AUTHOR.lower(), 'hackerman-kl <99999999+someone@users.noreply.github.com>',
                  'other <x@y.z>', 'Other <161579364+Mister-M-alt@users.noreply.github.com>',
                  'hackerman-kl <161579365+Mister-M-alt@users.noreply.github.com>',
                  'hackerman-kl <161579364+other@users.noreply.github.com>']
    messages = [[], ['Subject'], ['Subject', '', 'Body'], ['', 'Subject', '']]
    count = 0
    for a, c, msg in itertools.product(identities, identities, messages):
        want = (a, c) in [(HOLDER, HOLDER), (AUTHOR, COMMITTER)] and len([x for x in msg if x.strip()]) == 1
        assert (not gate.commit_errors('0' * 40, [a, c, *msg])) == want
        count += 1
    owner_lines = ['foreign <x@y.z>', 'foreign <x@y.z>', 'Subject', 'Body']
    assert not gate.commit_errors(OWNER, owner_lines)
    for near in [OWNER[:-1] + '0', OWNER[:7] + '0' * 33, OWNER[:7], 'a' * 40]:
        assert gate.commit_errors(near, owner_lines)
    fixtures = []
    restricted = ('/' + 'home' + '/synthetic')

    def fixture(name, commit, lines, history=b'clean', current=b'clean'):
        root = SCRATCH / ('fixture-' + name)
        root.mkdir(exist_ok=True)
        (root / 'probe.txt').write_bytes(current)
        gate.ROOT = root
        metadata = ('\n'.join(lines) + '\n').encode()

        def fake_git(*args):
            if args == ('rev-list', 'HEAD'): return (commit + '\n').encode()
            if args[0] == 'show': return metadata
            if args == ('rev-list', '--objects', 'HEAD'): return b'1111111111111111111111111111111111111111 retired.txt\n'
            if args[:2] == ('cat-file', '-t'): return b'blob\n'
            if args[:2] == ('cat-file', 'blob'): return history
            if args[0] == 'ls-files': return b'probe.txt\0'
            raise AssertionError(args)

        gate.git = fake_git
        out = io.StringIO()
        with contextlib.redirect_stdout(out): rc = int(gate.main())
        (RECEIPTS / ('fixture-' + name + '.log')).write_text(out.getvalue())
        fixtures.append({'case': name, 'rc': rc})
        return rc

    assert fixture('holder', '0' * 40, [HOLDER, HOLDER, 'Subject']) == 0
    assert fixture('web-flow', '0' * 40, [AUTHOR, COMMITTER, 'Subject']) == 0
    assert fixture('foreign', '0' * 40, owner_lines) == 1
    assert fixture('multiline', '0' * 40, [AUTHOR, COMMITTER, 'Subject', 'Body']) == 1
    assert fixture('owner', OWNER, owner_lines) == 0
    assert fixture('near-owner', OWNER[:7] + '0' * 33, owner_lines) == 1
    assert fixture('owner-metadata-scan', OWNER, [*owner_lines, restricted]) == 1
    assert fixture('owner-history-scan', OWNER, owner_lines, history=restricted.encode()) == 1
    assert fixture('owner-current-scan', OWNER, owner_lines, current=restricted.encode()) == 1
    save('behavior', {'pair_message_combinations': count, 'near_owner_refusals': 4, 'integration_fixtures': fixtures})
    return f'Behavior: {count} identity/message combinations; 4 near-owner refusals; 9 scan/wiring fixtures pass'


def source_audit():
    gate = module(SOURCE / 'scripts/check_privacy.py', 'review_real')
    output = io.StringIO()
    with contextlib.redirect_stdout(output): rc = int(gate.main())
    (RECEIPTS / 'real-head.log').write_text(output.getvalue())
    (RECEIPTS / 'real-head.rc').write_text(str(rc) + '\n')
    assert rc == 0
    base = subprocess.check_output(['git', 'show', BASE + ':scripts/check_privacy.py'], cwd=SOURCE).decode()
    before = ast.parse(base)
    after = ast.parse(ORIGINAL)
    def fn(tree, name): return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    assert ast.dump(fn(before, 'scan')) == ast.dump(fn(after, 'scan'))
    # Reconstitute the original main routine by replacing the factored call with its two original checks.
    old_main = fn(before, 'main')
    new_main = fn(after, 'main')
    old_loop = old_main.body[2]
    new_loop = new_main.body[2]
    assert isinstance(old_loop, ast.For) and isinstance(new_loop, ast.For)
    new_loop.body[2:3] = old_loop.body[2:4]
    assert ast.dump(old_main) == ast.dump(new_main)
    for name in ('WORDS', 'PATTERNS', 'OWNER_SQUASH', 'IDENTITY'):
        def assignments(t):
            return [ast.dump(n) for n in t.body if isinstance(n, (ast.Assign, ast.AugAssign))
                    and name in [x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)]]
        assert assignments(before) == assignments(after), name
    base_path = SCRATCH / 'base.py'
    base_path.write_text(base)
    base_module = module(base_path, 'review_base')
    base_module.ROOT = SOURCE
    output = io.StringIO()
    with contextlib.redirect_stdout(output): base_rc = int(base_module.main())
    (RECEIPTS / 'base-code-on-head-history.log').write_text(output.getvalue())
    assert base_rc == 1 and BASE + ': unexpected identity' in output.getvalue()
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, HEAD], cwd=SOURCE).decode().splitlines()
    assert changed == ['CHANGELOG.md', 'docs/IMPORT.md', 'docs/VERIFICATION.md', 'scripts/check_privacy.py', 'scripts/validate.py']
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=SOURCE).decode().split('\0')
    hdl = [x for x in tracked if Path(x).suffix.lower() in ('.v', '.sv', '.vhd', '.vhdl', '.xdc', '.sdc')]
    assert not hdl
    save('source-audit', {'changed_files': changed, 'rtl_constraint_files': hdl, 'unchanged_scan_patterns_exception': True,
                          'main_equivalent_except_commit_errors_call': True, 'head_rc': rc, 'base_code_on_head_history_rc': base_rc})
    return 'Source audit: real head passes; base rule rejects base identity; scan/exception unchanged; no RTL/interface changes'


def validator():
    import unittest.mock as mock
    records = []
    for graphs, failing in [(False, False), (True, False), (False, True)]:
        v = module(SOURCE / 'scripts/validate.py', 'review_validator')
        work = SCRATCH / f'validator-{graphs}-{failing}'
        commands = []
        def fake_run(argv, **kwargs):
            commands.append(argv)
            rc = int(failing and argv[1:] == ['scripts/check_privacy.py', '--selftest'])
            return subprocess.CompletedProcess(argv, rc)
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['validate.py', '--work', str(work), '--jobs', '16'] + (['--graphs'] if graphs else [])), \
                mock.patch.object(v.subprocess, 'run', fake_run), contextlib.redirect_stdout(output):
            rc = v.main()
        results = json.loads((work / 'gates.json').read_text())
        assert len(results) == (14 if failing else 25 if graphs else 24)
        assert rc == int(failing)
        if failing: assert all(x['gate'] not in ('gcc-configure', 'mutation') for x in results)
        (RECEIPTS / f'validator-{graphs}-{failing}.log').write_text(output.getvalue())
        records.append({'graphs': graphs, 'selftest_failure_injected': failing, 'rc': rc, 'gates': results})
    save('validator-fixtures', records)
    return 'Validator fixtures: 24 gates without graphs, 25 with graphs; failed privacy selftest blocks build campaigns'


assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE).decode().strip() == HEAD
# Independent probe campaigns share no mutable modules or scratch paths. The foreground driver joins all children.
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(lambda f: f(), [cli, mutants, behavior, source_audit]))
results.append(validator())
for result in results: print(result)
(RECEIPTS / 'summary.log').write_text('\n'.join(results) + '\n')
assert (SOURCE / 'scripts/check_privacy.py').read_text() == ORIGINAL
print('Source gate bytes unchanged; no commits created')
