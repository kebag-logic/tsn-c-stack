#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Plant coverage defects in disposable copies and run the ACMP cache gate on each.
Usage: TSN_CLANG=<clang-18> gate_probes.py <checkout> <work>"""
import json, shutil, subprocess, sys
from pathlib import Path
checkout, work = Path(sys.argv[1]), Path(sys.argv[2])
H, C, M, T = 'include/acmp.h', 'src/acmp.c', 'tests/mutations.json', 'tests/test_acmp.cpp'
FIELD = '\tuint64_t published_stream;\n'
RESTORE = '\ts->published_stream = published_stream;\n'
NEWTEST = ('\n// REQ: ACMP-10\nTEST_F(AcmpCore, FutureCacheProbe) {\n'
           '    EXPECT_TRUE(a.sinks[0].published_epoch == 0u) << "probe future cache epoch survives reset";\n}\n')


def plant_for(name, test, needle, field='published_epoch'):
    return {'name': name, 'path': C, 'old': '\ts->%s = %s;\n' % (field, field),
            'new': '\t(void)%s;\n' % field, 'kills': [{'test': test, 'needle': needle}], 'original_tests': [test]}


def future(t, restore=True):
    t[H] = t[H].replace(FIELD, FIELD + '\tuint32_t published_epoch;\n', 1)
    if restore:
        t[C] = t[C].replace(RESTORE, RESTORE + '\ts->published_epoch = published_epoch;\n', 1)
        t[C] = t[C].replace('\tuint64_t published_stream = s->published_stream;\n',
                            '\tuint64_t published_stream = s->published_stream;\n'
                            '\tuint32_t published_epoch = s->published_epoch;\n', 1)


def edit_m(t, fn):
    m = json.loads(t[M]); fn(m); t[M] = json.dumps(m, indent=2) + '\n'


def find(m, name):
    return next(x for x in m if x['name'] == name)


BOUND = 'acmp-publish-reset-bound-cache'
STARTED = 'acmp-publish-reset-started-cache'
STARTED_TEST = 'AcmpCore.A31StoreRestoreOfAStoppedRecordPublishesTheStop'
STARTED_NEEDLE = 'A31 the started cache survives reset to publish the restored stop'
cases = []
def case(name, expect):
    def wrap(fn):
        cases.append((name, expect, fn)); return fn
    return wrap

@case('control-head', 0)
def _(t): pass
@case('future-field-header-only', 1)
def _(t): future(t, restore=False)
@case('future-field-restored-no-plant', 1)
def _(t): future(t)
@case('future-field-plant-shares-started-assertion', 1)
def _(t):
    future(t); edit_m(t, lambda m: m.append(plant_for('probe-future', STARTED_TEST, STARTED_NEEDLE)))
@case('future-field-plant-names-missing-test', 1)
def _(t):
    future(t); edit_m(t, lambda m: m.append(plant_for('probe-future', 'AcmpCore.FutureCacheProbe', 'probe future cache epoch')))
@case('future-field-fully-covered', 0)
def _(t):
    future(t); t[T] = t[T].rstrip()[:-1] + NEWTEST + '\n}\n'
    edit_m(t, lambda m: m.append(plant_for('probe-future', 'AcmpCore.FutureCacheProbe', 'probe future cache epoch')))
@case('future-field-inside-ifdef', 1)
def _(t): t[H] = t[H].replace(FIELD, FIELD + '#ifdef PROBE_UNUSED\n\tbool published_hidden;\n#endif\n', 1)
@case('future-field-multi-declarator', 1)
def _(t): t[H] = t[H].replace('\tbool published_started;\n', '\tbool published_started, published_extra;\n', 1)
@case('bound-plant-removed', 1)
def _(t): edit_m(t, lambda m: m.remove(find(m, BOUND)))
@case('bound-plant-shares-started-assertion', 1)
def _(t): edit_m(t, lambda m: find(m, BOUND).update(kills=[{'test': STARTED_TEST, 'needle': STARTED_NEEDLE}]))
@case('bound-plant-shares-started-assertion-shorter-needle', 1)
def _(t): edit_m(t, lambda m: find(m, BOUND).update(kills=[{'test': STARTED_TEST, 'needle': STARTED_NEEDLE[4:]}]))
@case('bound-plant-adds-rv32-smoke-killer', 1)
def _(t): edit_m(t, lambda m: find(m, BOUND)['kills'].append({'test': 'Rv32Smoke.Cache', 'needle': 'smoke cache'}))
@case('bound-plant-drops-two-fields', 1)
def _(t): edit_m(t, lambda m: find(m, BOUND).update(
    old='\ts->published_bound = published_bound;\n\ts->published_started = published_started;\n',
    new='\t(void)published_bound;\n\t(void)published_started;\n'))
@case('started-plant-duplicated', 1)
def _(t): edit_m(t, lambda m: m.append(dict(find(m, STARTED), name='dup-started')))
@case('started-assertion-deleted-from-test', 1)
def _(t): t[T] = t[T].replace('<< "' + STARTED_NEEDLE + '"', '<< "probe changed message"', 1)
@case('started-test-deleted', 1)
def _(t):
    s = t[T]; i = s.index('// REQ: ACMP-10\nTEST_F(AcmpCore, A31StoreRestoreOfAStoppedRecordPublishesTheStop)')
    t[T] = s[:i] + '\n}\n'
@case('started-restore-removed-from-source', 1)
def _(t): t[C] = t[C].replace('\ts->published_started = published_started;\n', '\t(void)published_started;\n', 1)
@case('stream-plant-retargeted-to-header', 1)
def _(t): edit_m(t, lambda m: find(m, 'acmp-publish-reset-stream-cache').update(path=H))

results, status = [], 0
for name, expect, fn in cases:
    d = work / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    subprocess.run(f'git -C {checkout} archive HEAD | tar -x -C {d}', shell=True, check=True)
    t = {p: (d / p).read_text() for p in (H, C, M, T)}
    before = dict(t); fn(t)
    for p in t:
        (d / p).write_text(t[p])
    changed = sorted(p for p in t if t[p] != before[p])
    r = subprocess.run([sys.executable, 'scripts/check_acmp_cache.py'], cwd=d, capture_output=True, text=True)
    rc = 0 if r.returncode == 0 else 1
    ok = rc == expect
    status |= not ok
    out = (r.stdout + r.stderr).strip().splitlines()
    print(f'{"OK " if ok else "BAD"} {name}: expected rc {expect}, got {r.returncode}; changed {changed}; {out[-1] if out else ""}')
sys.exit(status)
