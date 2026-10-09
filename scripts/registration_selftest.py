#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile registration controls for formatting, unknown IDs and missing plants."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from test_inventory import validate_targets
from test_registry import reconcile, registered
from traceability import inventory, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-registration-controls'))
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.work.resolve()) as temporary:
        work = Path(temporary)
        reqs = [{'id': 'R1'}]
        for label, declaration in (
                ('indented', '  TEST(Control, Added)'),
                ('multiline', '  TEST(\n Control,\n Added\n )'),
                ('macro-wrapper', '#define DECL TEST\nDECL(Control, Added)')):
            source = '#include <gtest/gtest.h>\n// REQ: UNKNOWN\n' + declaration + ' { SUCCEED(); }\n'
            path = work / 'control.cpp'
            path.write_text(source)
            binary = work / 'control'
            subprocess.run(['g++', '-std=c++20', '-Wall', '-Wextra', '-Werror', str(path),
                            '-lgtest_main', '-lgtest', '-pthread', '-o', str(binary)], check=True)
            names = registered(binary)
            subprocess.run([str(binary)], check=True)
            assert names == ['Control.Added'], names
            rows = inventory(source)
            if label == 'macro-wrapper':
                assert reconcile(rows, names)
                print(label + ': executable declaration missing from source inventory refused')
                continue
            assert not reconcile(rows, names)
            assert any('unknown requirement' in e for e in validate(reqs, rows))
            known = inventory(source.replace('UNKNOWN', 'R1'))
            assert not validate(reqs, known)
            assert validate_targets({r[0] for r in known}, [])
            mapped = [{'kills': [{'test': 'Control.Added', 'needle': 'specific assertion'}]}]
            assert not validate_targets({r[0] for r in known}, mapped)
            print(label + ': unknown ID and missing plant refused; mapped known ID passes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
