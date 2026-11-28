# SPDX-License-Identifier: MIT
"""Compile the future-field shared-assertion counterexample and its repair."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('cache control must select exactly one source fragment: ' + old)
    return text.replace(old, new)


def compiling_controls(root, work, jobs):
    # Issue #21, R623-4-F1: shared_assertion_probe.py, immutable review evidence.
    # https://github.com/kebag-logic/tsn-c-stack/blob/cccb8b15e7b6061b4160832efd142a0def697608/review-evidence/tsn21-r1/reviews/R623-4/scripts/shared_assertion_probe.py
    work.mkdir(parents=True, exist_ok=True)
    tree = work / 'source'
    for name in ('scripts', 'src', 'include', 'tests', 'examples'):
        shutil.copytree(root / name, tree / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__'))
    header = (tree / 'include/acmp.h').read_text()
    source = (tree / 'src/acmp.c').read_text()
    tests = (tree / 'tests/test_acmp.cpp').read_text()
    mutations = json.loads((tree / 'tests/mutations.json').read_text())
    header = replace_once(header, 'struct acmp_sink {',
                          'struct acmp_sink {\n\tbool published_future;')
    source = replace_once(source, '\tmemset(s, 0, sizeof *s);',
                          '\tbool published_future = s->published_future;\n\tmemset(s, 0, sizeof *s);')
    source = replace_once(source, '\ts->published_bound = published_bound;',
                          '\ts->published_future = published_future;\n\ts->published_bound = published_bound;')
    name = 'A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal'
    start = tests.index('TEST_F(AcmpCore, ' + name + ')')
    end = tests.index('\n}', start) + 2
    case = replace_once(tests[start:end], '    fk.clear();',
                        '    a.sinks[0].published_future = true;\n    fk.clear();')
    bound = 'A31 the bound cache survives reset to publish the stopped binding withdrawal'
    future = 'A31 future cache also survives the same reset'
    old = '    ASSERT_EQ(fk.pubs.size(), 1u)\n        << "' + bound + '";'
    shared = ('    ASSERT_TRUE(fk.pubs.size() == 1u && a.sinks[0].published_future)\n'
              '        << "' + bound + '"\n        << "' + future + '";')
    separate = old + '\n    ASSERT_TRUE(a.sinks[0].published_future) << "' + future + '";'
    tests = tests[:start] + replace_once(case, old, shared) + tests[end:]
    mutations.append(dict(name='acmp-publish-reset-future-cache', path='src/acmp.c',
                          old='\ts->published_future = published_future;\n',
                          new='\t(void)published_future;\n',
                          kills=[dict(test='AcmpCore.' + name, needle=future)],
                          original_tests=['AcmpCore.' + name]))
    for path, text in (('include/acmp.h', header), ('src/acmp.c', source),
                       ('tests/test_acmp.cpp', tests),
                       ('tests/mutations.json', json.dumps(mutations, indent=2) + '\n')):
        (tree / path).write_text(text)

    def run(label, command, expected=0, diagnostic=None):
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=tree, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=540)
        (work / (label + '.rc')).write_text(str(result.returncode) + '\n')
        output = (work / (label + '.log')).read_text()
        if result.returncode != expected or (diagnostic and output.strip() != diagnostic):
            raise RuntimeError(label + ' failed: ' + output)

    for kind in ('shared', 'separate'):
        if kind == 'separate':
            (tree / 'tests/test_acmp.cpp').write_text(replace_once(tests, shared, separate))
        for optimized in (False, True):
            run(kind + ('-optimized' if optimized else '') + '-gate',
                [sys.executable, *(['-O'] if optimized else []), 'scripts/check_acmp_cache.py'],
                expected=1 if kind == 'shared' else 0,
                diagnostic=('published_future: assertion is shared with another cache field'
                            if kind == 'shared' else None))
        run(kind + '-needles', [sys.executable, 'scripts/needle_audit.py'])
        campaign = work / (kind + '-mutations')
        run(kind + '-mutation', [sys.executable, 'scripts/mutation.py', '--work', str(campaign),
                                '--jobs', str(jobs), '--select', 'acmp-publish-reset-'])
        results = json.loads((campaign / 'results.json').read_text())
        expected = {m['name'] for m in mutations if 'acmp-publish-reset-' in m['name']}
        if (len(results) != len(expected) or {r['name'] for r in results} != expected
                or any(r['status'] != 'CAUGHT' for r in results)):
            raise RuntimeError(kind + ' cache campaign incomplete')
    print('acmp cache: compiling split-message future field refused; separate assertion accepted; '
          'both hosted control campaigns caught every selected plant')
