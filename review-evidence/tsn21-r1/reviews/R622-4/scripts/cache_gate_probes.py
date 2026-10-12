#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reviewer probes of check_acmp_cache.check() identity semantics at a given tree (in memory only).
usage: cache_gate_probes.py <tree>"""
import json, sys
from pathlib import Path
tree = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(tree / 'scripts'))
from check_acmp_cache import check
from assertion_messages import assertion_inventory as inv

H = (tree / 'include/acmp.h').read_text()
S = (tree / 'src/acmp.c').read_text()
M = json.loads((tree / 'tests/mutations.json').read_text())
T = (tree / 'tests/test_acmp.cpp').read_text()
SHARED = 'published_future: assertion is shared with another cache field'

def future(field='published_future'):
    h = H.replace('struct acmp_sink {', 'struct acmp_sink {\n\tbool ' + field + ';', 1)
    old = '\ts->' + field + ' = ' + field + ';\n'
    s = S.replace('\ts->state = ACMP_UNBOUND;', old + '\ts->state = ACMP_UNBOUND;', 1)
    return h, s, old

def plant(test, needle, field='published_future'):
    _, _, old = future(field)
    return dict(name='probe-future', path='src/acmp.c', old=old, new='\t(void)' + field + ';\n',
                kills=[dict(test=test, needle=needle)])

BOUND = 'A31 the bound cache survives reset to publish the stopped binding withdrawal'
BT = 'AcmpCore.A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal'
FUT = 'A31 future cache survives the same reset'
base_msgs = inv(T, 'tests/test_acmp.cpp')
results, bad = [], 0

def probe(label, extra_src, kill_test, needle, expect, field='published_future', replace_tests=None):
    global bad
    msgs = dict(base_msgs)
    src = extra_src
    msgs.update(inv(src, 'tests/test_acmp.cpp'))
    h, s, _ = future(field)
    errs = check(h, s, M + [plant(kill_test, needle, field)], msgs)
    ok = (errs == expect) if isinstance(expect, list) else expect(errs)
    bad += not ok
    results.append(dict(probe=label, errors=errs, expected=expect if isinstance(expect, list) else expect.__doc__, ok=ok))
    print(('PASS ' if ok else 'FAIL ') + label + ' -> ' + repr(errs))

def accept(errs):
    """no errors (accepted)"""
    return errs == []
def shared_any(errs):
    """exactly one shared-assertion error (either field named)"""
    return len(errs) == 1 and errs[0].endswith(': assertion is shared with another cache field')
def needle_err(errs):
    """needle-uniqueness refusal"""
    return any('needle must identify exactly one' in e for e in errs)

TF = 'TEST_F(AcmpCore, A31StoreResetOfABoundStoppedSinkPublishesItsWithdrawal) { '
probe('P0 baseline head (no future field) accepted', '', BT, BOUND, accept, field='published_future') if False else None
errs0 = check(H, S, M, base_msgs); print(('PASS' if errs0 == [] else 'FAIL') + ' P0 head accepted -> ' + repr(errs0)); bad += errs0 != []
probe('P1 split literals on one direct assertion', TF + f'ASSERT_TRUE(x && y) << "{BOUND}" << "{FUT}"; }}', BT, FUT, [SHARED])
probe('P2 split literals on one assertion inside a lambda', TF + f'auto c = [&] {{ ASSERT_TRUE(x) << "{BOUND}" << 3 << "{FUT}"; }}; c(); }}', BT, FUT, [SHARED])
probe('P3 one literal holding both needles', TF + f'ASSERT_TRUE(x) << "{BOUND} / {FUT}"; }}', BT, FUT, [SHARED])
probe('P4 split literals in a helper called by the owning test', f'static void chk(bool x) {{ ASSERT_TRUE(x) << "{BOUND}" << "{FUT}"; }} ' + TF + 'chk(true); }', BT, FUT, [SHARED])
probe('P5 separate assertions on the same line', TF + f'ASSERT_TRUE(x) << "{BOUND}"; ASSERT_TRUE(y) << "{FUT}"; }}', BT, FUT, accept)
probe('P6 separate assertion in its own helper', f'static void fut() {{ EXPECT_TRUE(y) << "{FUT}"; }} ' + TF + f'ASSERT_TRUE(x) << "{BOUND}"; fut(); }}', BT, FUT, accept)
probe('P7 future needle not unique in test', TF + f'ASSERT_TRUE(x) << "{BOUND}"; ASSERT_TRUE(y) << "{FUT}"; EXPECT_TRUE(z) << "{FUT}"; }}', BT, FUT, needle_err)
probe('P8 future sorts before existing fields, shared', TF + f'ASSERT_TRUE(x && y) << "{BOUND}" << "{FUT}"; }}', BT, FUT, shared_any, field='published_aaa')
probe('P9 future field with no assertion at all', '', BT, FUT, needle_err)
# By-design boundary: identity includes the owning test, so one helper assertion run by two tests gives two identities.
probe('P10 one helper assertion owned by two different tests (ruled identity includes owner)',
      f'static void both(bool x) {{ ASSERT_TRUE(x) << "{BOUND}" << "{FUT}"; }} ' + TF + 'both(true); } TEST_F(AcmpCore, FutureOwner) { both(true); }',
      'AcmpCore.FutureOwner', FUT, accept)
Path(sys.argv[2]).write_text(json.dumps(results, indent=1, default=str) + '\n') if len(sys.argv) > 2 else None
print('probes:', len(results) + 1, 'unexpected:', bad)
sys.exit(1 if bad else 0)
