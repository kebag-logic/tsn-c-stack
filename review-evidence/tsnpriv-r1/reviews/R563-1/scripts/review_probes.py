#!/usr/bin/env python3
"""Read-only review probes; all temporary fixtures remain below --work."""
import argparse
import ast
import contextlib
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys

HEAD = '61fb7c9a523b89cb96d493c5baf9f7f866ebed85'
BASE = '18d737832c376f32660eb21fe2796e0b611507e3'
HOLDER = 'hackerman-kl <hackerman-kl@kebag-logic.com>'
WEB_AUTHOR = 'hackerman-kl <161579364+Mister-M-alt@users.noreply.github.com>'
WEB_COMMITTER = 'GitHub <noreply@github.com>'
EXCEPTION = 'ae982af85ec97286bd35b39403926d8f0eaec81d'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def module(source, filename):
    namespace = {'__file__': str(filename), '__name__': 'review_subject'}
    exec(compile(source, str(filename), 'exec'), namespace)
    return namespace


def capture(function):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = int(function())
    return rc, output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    repo, work = args.repo.resolve(), args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    git = lambda *argv: subprocess.check_output(['git', '-C', str(repo), *argv])
    require(git('rev-parse', 'HEAD').decode().strip() == HEAD, 'wrong review head')
    source = (repo / 'scripts/check_privacy.py').read_text()
    before = git('show', BASE + ':scripts/check_privacy.py').decode()
    subject = module(source, repo / 'scripts/check_privacy.py')
    old = module(before, repo / 'scripts/check_privacy.py')
    require(subject['OWNER_SQUASH'] == old['OWNER_SQUASH'] == EXCEPTION, 'exception changed')
    require(subject['IDENTITY'] == HOLDER, 'holder mismatch')
    require(subject['WEB_FLOW'] == [WEB_AUTHOR, WEB_COMMITTER], 'web-flow mismatch')
    require([(p.pattern, p.flags) for p in subject['PATTERNS']] ==
            [(p.pattern, p.flags) for p in old['PATTERNS']], 'scan patterns changed')
    def fn_ast(text, name):
        node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
        return ast.dump(node, include_attributes=False)
    require(fn_ast(before, 'scan') == fn_ast(source, 'scan'), 'scan helper changed')
    old_main = next(n for n in ast.parse(before).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    new_main = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    old_identity = old_main.body[2].body[2]
    new_identity = new_main.body[2].body[2]
    require(isinstance(old_identity, ast.If) and isinstance(new_identity, ast.If), 'identity location changed')
    old_main.body[2].body[2] = new_identity
    require(ast.dump(old_main) == ast.dump(new_main), 'main changed beyond identity predicate')
    print('PASS: exact constants, patterns, scan helper and complete main except identity predicate unchanged')

    identities = [HOLDER, WEB_AUTHOR, WEB_COMMITTER,
                  'someone <a@b.c>',
                  'hackerman-kl <999999+different-account@users.noreply.github.com>',
                  'hackerman-kl <161579365+Mister-M-alt@users.noreply.github.com>',
                  'hackerman-kl <161579364+different-account@users.noreply.github.com>',
                  'different-name <161579364+Mister-M-alt@users.noreply.github.com>',
                  'GitHub <different@github.com>', HOLDER + ' ', HOLDER.upper()]
    accepted = {(HOLDER, HOLDER), (WEB_AUTHOR, WEB_COMMITTER)}
    count = 0
    for author, committer in itertools.product(identities, repeat=2):
        want = (author, committer) in accepted
        for tail in [[], ['one line'], ['subject', '', 'body']]:
            require(subject['identity_ok']([author, committer] + tail) == want, 'pair matrix mismatch')
            count += 1
    for short in [[], [HOLDER], [WEB_AUTHOR]]:
        require(not subject['identity_ok'](short), 'short metadata accepted')
    print(f'PASS: {count} ordered pair/tail cases plus three short inputs; only two exact pairs accepted')

    rc, output = capture(subject['selftest'])
    require(rc == 0 and '6 identity controls pass' in output, 'shipped selftest failed')
    print(output.strip())
    mutations = {
        'reject-all': 'False',
        'accept-all': 'True',
        'reject-web-flow': 'lines[:2] == [IDENTITY, IDENTITY]',
        'reject-holder': 'lines[:2] == WEB_FLOW',
        'independent-allowlists': 'lines[0] in (IDENTITY, WEB_FLOW[0]) and lines[1] in (IDENTITY, WEB_FLOW[1])',
        'any-author-with-web-committer': 'lines[:2] == [IDENTITY, IDENTITY] or lines[1] == WEB_FLOW[1]',
        'matching-foreign-pair': 'lines[:2] in ([IDENTITY, IDENTITY], WEB_FLOW) or lines[0] == lines[1]',
    }
    original = 'return lines[:2] in ([IDENTITY, IDENTITY], WEB_FLOW)'
    require(source.count(original) == 1, 'mutation anchor mismatch')
    for name, predicate in mutations.items():
        mutated = source.replace(original, 'return ' + predicate)
        path = work / (name + '.py')
        path.write_text(mutated)
        p = subprocess.run([sys.executable, str(path), '--selftest'], text=True, capture_output=True)
        require(p.returncode == 1 and 'privacy selftest: fail' in p.stdout, name + ' escaped')
        print('PASS: shipped selftest detects predicate plant', name)

    fixture = work / 'fixture'
    fixture.mkdir(exist_ok=True)
    subject['ROOT'] = fixture
    marker = b'/' + b'home' + b'/review-fixture'
    cases = []
    ordinary = '1' * 40
    def exercise(name, *, pair=(HOLDER, HOLDER), message='subject\n', commit=ordinary,
                 metadata_marker=False, historical_marker=False, current_marker=False,
                 untracked_marker=False, expected=0, diagnostic=None):
        calls = []
        metadata = ('\n'.join(pair) + '\n' + message).encode()
        if metadata_marker:
            metadata += marker + b'\n'
        (fixture / 'tracked.txt').write_bytes(marker if current_marker else b'clean\n')
        (fixture / 'untracked.txt').write_bytes(marker if untracked_marker else b'clean\n')
        def fake_git(*argv):
            calls.append(argv)
            if argv == ('rev-list', 'HEAD'):
                return (commit + '\n').encode()
            if argv == ('show', '-s', '--format=%an <%ae>%n%cn <%ce>%n%B', commit):
                return metadata
            if argv == ('rev-list', '--objects', 'HEAD'):
                return (commit + '\n' + '2' * 40 + ' deleted.txt\n' + '3' * 40 + ' current.txt\n').encode()
            if len(argv) == 3 and argv[:2] == ('cat-file', '-t'):
                return b'commit\n' if argv[2] == commit else b'blob\n'
            if len(argv) == 3 and argv[:2] == ('cat-file', 'blob'):
                return marker if historical_marker and argv[2] == '2' * 40 else b'clean\n'
            if argv == ('ls-files', '--cached', '--others', '--exclude-standard', '-z'):
                return b'tracked.txt\0untracked.txt\0'
            raise RuntimeError('unexpected git operation ' + repr(argv))
        subject['git'] = fake_git
        rc, output = capture(subject['main'])
        require(rc == expected, name + ': unexpected return code ' + str(rc))
        require(diagnostic is None or diagnostic in output, name + ': missing diagnostic')
        require(sum(x[:2] == ('cat-file', 'blob') for x in calls) == 2, name + ': historical scan skipped')
        require(any(x[0] == 'ls-files' for x in calls), name + ': tree scan skipped')
        cases.append({'case': name, 'rc': rc, 'output': output})
        print('PASS: integration fixture', name, 'rc', rc)
    exercise('holder-single-line')
    exercise('web-flow-single-line', pair=(WEB_AUTHOR, WEB_COMMITTER))
    exercise('different-noreply-account', pair=(identities[4], WEB_COMMITTER), expected=1, diagnostic='unexpected identity')
    exercise('mixed-holder-web', pair=(HOLDER, WEB_COMMITTER), expected=1, diagnostic='unexpected identity')
    exercise('mixed-web-holder', pair=(WEB_AUTHOR, HOLDER), expected=1, diagnostic='unexpected identity')
    exercise('foreign-pair', pair=(identities[3], identities[3]), expected=1, diagnostic='unexpected identity')
    for label, pair in [('holder', (HOLDER, HOLDER)), ('web', (WEB_AUTHOR, WEB_COMMITTER))]:
        exercise(label + '-body', pair=pair, message='subject\n\nbody\n', expected=1, diagnostic='commit message must be one line')
        exercise(label + '-trailer', pair=pair, message='subject\n\nSigned-off-by: review fixture\n', expected=1, diagnostic='commit message must be one line')
        exercise(label + '-empty', pair=pair, message='\n', expected=1, diagnostic='commit message must be one line')
        exercise(label + '-blank-padding', pair=pair, message='\nsubject\n\n')
        exercise(label + '-merge-subject', pair=pair, message='Merge reviewed branch\n')
    exercise('exact-exception', pair=(identities[3], identities[3]), commit=EXCEPTION, message='subject\n\nbody\n')
    exercise('near-exception', pair=(identities[3], identities[3]), commit=EXCEPTION[:-1] + '0', message='subject\n\nbody\n', expected=1, diagnostic='unexpected identity')
    exercise('exception-metadata-scan', commit=EXCEPTION, metadata_marker=True, expected=1, diagnostic='restricted content')
    exercise('exception-historical-scan', commit=EXCEPTION, historical_marker=True, expected=1, diagnostic='restricted content')
    exercise('historical-deleted-blob', historical_marker=True, expected=1, diagnostic='restricted content')
    exercise('tracked-tree-content', current_marker=True, expected=1, diagnostic='tracked.txt: restricted content')
    exercise('untracked-tree-content', untracked_marker=True, expected=1, diagnostic='untracked.txt: restricted content')
    (work / 'integration-results.json').write_text(json.dumps(cases, indent=2) + '\n')
    print('Merge result is a metadata-fixture check: no parent-count query exists; no merge or commit was created.')

    subject = module(source, repo / 'scripts/check_privacy.py')
    rc, output = capture(subject['main'])
    require(rc == 0, 'exact-head privacy failed')
    print('EXACT HEAD:', output.strip())
    rc, output = capture(old['main'])
    require(rc == 1 and BASE + ': unexpected identity' in output, 'old gate did not reproduce base failure')
    print('BASE IMPLEMENTATION ON EXACT-HEAD HISTORY/TREE:', output.strip())
    print('PASS: all independent review probes')


if __name__ == '__main__':
    main()
