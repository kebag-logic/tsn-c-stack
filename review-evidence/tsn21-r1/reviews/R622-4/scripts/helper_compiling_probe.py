#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compiling reviewer probe: a future cache field whose only assertion is a helper assertion shared with the
bound field (split streamed literals). The gate must refuse it for shared ownership while the hosted
restore-only campaign still catches every plant (so only the identity gate can see the sharing).
usage: helper_compiling_probe.py <pristine-tree> <work> <jobs>"""
import json, shutil, subprocess, sys
from pathlib import Path
src, work, jobs = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
shutil.rmtree(work, ignore_errors=True)
tree = work / 'source'
shutil.copytree(src, tree, ignore=shutil.ignore_patterns('__pycache__', 'build*'))
def sub(path, old, new):
    p = tree / path; t = p.read_text(); assert t.count(old) == 1, (path, old); p.write_text(t.replace(old, new))
sub('include/acmp.h', 'struct acmp_sink {', 'struct acmp_sink {\n\tbool published_future;')
sub('src/acmp.c', '\tmemset(s, 0, sizeof *s);', '\tbool published_future = s->published_future;\n\tmemset(s, 0, sizeof *s);')
sub('src/acmp.c', '\ts->published_bound = published_bound;', '\ts->published_future = published_future;\n\ts->published_bound = published_bound;')
bound = 'A31 the bound cache survives reset to publish the stopped binding withdrawal'
future = 'A31 reviewer future cache survives the same reset'
sub('tests/test_acmp.cpp', '// REQ: ACMP-10\nTEST_F(AcmpCore, A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal) {',
    'static void a31_reset_cache_check(bool published, bool future)\n{\n'
    f'    ASSERT_TRUE(published && future)\n        << "{bound}"\n        << "{future}";\n}}\n\n'
    '// REQ: ACMP-10\nTEST_F(AcmpCore, A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal) {')
sub('tests/test_acmp.cpp', '    acmp_open(&a);\n    ASSERT_EQ(fk.pubs.size(), 1u)\n        << "' + bound + '";',
    '    acmp_open(&a);\n    a31_reset_cache_check(fk.pubs.size() == 1u, a.sinks[0].published_future);\n    ASSERT_EQ(fk.pubs.size(), 1u);')
sub('tests/test_acmp.cpp', '    const auto none = payload(0u, 0u, 0u, 0u);\n    fk.clear();\n    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);\n    EXPECT_TRUE(fk.pubs.empty()) << "A31 resetting a stopped binding',
    '    const auto none = payload(0u, 0u, 0u, 0u);\n    a.sinks[0].published_future = true;\n    fk.clear();\n    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);\n    EXPECT_TRUE(fk.pubs.empty()) << "A31 resetting a stopped binding')
m = json.loads((tree / 'tests/mutations.json').read_text())
m.append(dict(name='acmp-publish-reset-future-cache', path='src/acmp.c',
              old='\ts->published_future = published_future;\n', new='\t(void)published_future;\n',
              kills=[dict(test='AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal', needle=future)],
              original_tests=['AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal']))
(tree / 'tests/mutations.json').write_text(json.dumps(m, indent=2) + '\n')
out = {}
for label, cmd in (('gate', [sys.executable, 'scripts/check_acmp_cache.py']),
                   ('gate-optimized', [sys.executable, '-O', 'scripts/check_acmp_cache.py']),
                   ('needles', [sys.executable, 'scripts/needle_audit.py']),
                   ('mutation', [sys.executable, 'scripts/mutation.py', '--work', str(work / 'mutations'), '--jobs', jobs, '--select', 'acmp-publish-reset-'])):
    r = subprocess.run(cmd, cwd=tree, capture_output=True, text=True, timeout=540)
    out[label] = dict(rc=r.returncode, tail=(r.stdout + r.stderr).strip().splitlines()[-6:])
    print(label, 'rc', r.returncode, '::', ' | '.join(out[label]['tail']))
res = json.loads((work / 'mutations/results.json').read_text())
out['plants'] = {x['name']: x['status'] for x in res}
ok = (out['gate']['rc'] == 1 and out['gate']['tail'] == ['published_future: assertion is shared with another cache field']
      and out['gate-optimized']['rc'] == 1 and out['needles']['rc'] == 0 and out['mutation']['rc'] == 0
      and len(res) == 5 and all(s == 'CAUGHT' for s in out['plants'].values()))
out['expected_outcome'] = ok
print(json.dumps(out['plants']), 'EXPECTED' if ok else 'UNEXPECTED')
(work / 'summary.json').write_text(json.dumps(out, indent=1) + '\n')
sys.exit(0 if ok else 1)
