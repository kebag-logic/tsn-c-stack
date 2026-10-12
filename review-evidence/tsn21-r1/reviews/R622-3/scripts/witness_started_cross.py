#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Append one witness test to a disposable copy and run it on the control and on
the started-from-bound restore mutant. Usage: witness_started_cross.py <checkout> <work>"""
import shutil, subprocess, sys
from pathlib import Path
checkout, work = Path(sys.argv[1]), Path(sys.argv[2])
WITNESS = '''
// REQ: ACMP-10
TEST_F(AcmpCore, WitnessRestoreOfAStartedRecordOverAStoppedBinding) {
    bind(0, kTkA, 1, kCtl1, true);
    ASSERT_EQ(fk.pubs.size(), 1u) << "witness stopped binding published";
    const auto started = payload(kRecValid | kRecStarted, 1u, kTkA, kCtl1);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, started.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "witness restored start is published at open";
    EXPECT_TRUE(fk.pubs[0].bound && fk.pubs[0].started) << "witness restored binding published started";
}
'''
MUT = ('\ts->published_started = published_started;\n',
       '\t(void)published_started;\n\ts->published_started = published_bound;\n')
for name, plant in (('control', None), ('started-from-bound', MUT)):
    d = work / name
    shutil.rmtree(d, ignore_errors=True); (d / 'src').mkdir(parents=True)
    subprocess.run(f'git -C {checkout} archive HEAD | tar -x -C {d / "src"}', shell=True, check=True)
    t = d / 'src/tests/test_acmp.cpp'
    s = t.read_text().rstrip()
    t.write_text(s[:-1] + WITNESS + '\n}\n')
    if plant:
        c = d / 'src/src/acmp.c'; text = c.read_text()
        assert text.count(plant[0]) == 1
        c.write_text(text.replace(*plant))
    subprocess.run(['cmake', '-S', str(d / 'src'), '-B', str(d / 'build'), '-DCMAKE_BUILD_TYPE=Debug'], check=True, capture_output=True)
    subprocess.run(['cmake', '--build', str(d / 'build'), '--target', 'acmp_tests', '-j4'], check=True, capture_output=True)
    r = subprocess.run([str(d / 'build/acmp_tests')], capture_output=True, text=True)
    failed = [l.split('] ')[1] for l in r.stdout.splitlines() if l.startswith('[  FAILED  ] ') and 'test' not in l.split('] ')[1][:5]]
    print(f'{name}: rc {r.returncode}; failed {sorted(set(failed))}')
