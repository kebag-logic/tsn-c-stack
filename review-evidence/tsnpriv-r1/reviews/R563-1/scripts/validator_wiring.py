#!/usr/bin/env python3
"""Test validation dispatch and failure propagation with command stubs, not builds."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    args = p.parse_args()
    source = args.repo.resolve() / 'scripts/validate.py'
    for failing in [False, True]:
        work = (args.work / ('reject' if failing else 'accept')).resolve()
        namespace = {'__name__': 'review_subject', '__file__': str(source)}
        exec(compile(source.read_text(), str(source), 'exec'), namespace)
        calls = []
        def stub(argv, **kwargs):
            calls.append(argv)
            is_selftest = argv[1:] == ['scripts/check_privacy.py', '--selftest']
            kwargs['stdout'].write('command stub: return code only; no build executed\n')
            return SimpleNamespace(returncode=int(failing and is_selftest))
        namespace['subprocess'] = SimpleNamespace(run=stub, STDOUT=subprocess.STDOUT)
        namespace['sys'] = SimpleNamespace(executable=sys.executable)
        saved = sys.argv
        sys.argv = [str(source), '--work', str(work), '--jobs', '16', '--graphs']
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc = namespace['main']()
        finally:
            sys.argv = saved
        gates = json.loads((work / 'gates.json').read_text())
        test_calls = [x for x in calls if x[1:] == ['scripts/check_privacy.py', '--selftest']]
        scan_calls = [x for x in calls if x[1:] == ['scripts/check_privacy.py']]
        expected_gates = 14 if failing else 25
        if rc != int(failing) or len(test_calls) != 1 or len(scan_calls) != 1 or len(gates) != expected_gates:
            raise RuntimeError('dispatch or failure propagation mismatch')
        row = next(x for x in gates if x['gate'] == 'privacy-selftest')
        if row['rc'] != int(failing):
            raise RuntimeError('selftest return code not preserved')
        if failing and any(x[0] == 'cmake' for x in calls):
            raise RuntimeError('heavy work started after a failed preflight')
        print('PASS: privacy selftest dispatched exactly once with --selftest; separate content scan dispatched; injected selftest rc', int(failing), 'produces validator rc', rc, 'and', len(gates), 'gate rows')
    print('These are orchestration fixtures, not validation-bank receipts.')


if __name__ == '__main__':
    main()
