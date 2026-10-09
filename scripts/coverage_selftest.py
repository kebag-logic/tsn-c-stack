#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Planted controls for the inherited coverage reader and ratchet."""
import copy
from pathlib import Path
import tempfile
import coverage as reader


def main():
    full = {'src/x.c': reader.Tally((2, 2), (2, 2))}
    if reader.compare(full, full):
        raise RuntimeError('validation failed: not reader.compare(full, full)')
    if not (reader.compare({'src/x.c': reader.Tally((2, 2), (1, 2))}, full)):
        raise RuntimeError("validation failed: reader.compare({'src/x.c': reader.Tally((2, 2), (1, 2))}, full)")
    if not (reader.compare({}, full)):
        raise RuntimeError('validation failed: reader.compare({}, full)')
    if not (reader.compare(full, {})):
        raise RuntimeError('validation failed: reader.compare(full, {})')
    with tempfile.TemporaryDirectory(prefix='coverage-control-') as directory:
        root = Path(directory)
        (root / 'src').mkdir()
        (root / 'src/x.c').write_text('int f(int x) {\nif (x) {\nreturn 0;\n}\nreturn 1;\n}\n')
        src = reader.Source(lines={2: reader.Line(1, [1, 0]), 3: reader.Line(1), 5: reader.Line(0)}, functions={'f': (1, 6)})
        row = reader.Exclusion('src/x.c', 'f', 'if (x) {', 'arc 2 of 2; line `return 1;`', 'synthetic impossible branch')
        _, errors = reader.apply_exclusions({'src/x.c': copy.deepcopy(src)}, [row], root)
        if errors:
            raise RuntimeError(errors)
        src.lines[2].arcs = [0, 1]
        _, errors = reader.apply_exclusions({'src/x.c': copy.deepcopy(src)}, [row], root)
        if not (errors):
            raise RuntimeError('moving the missed branch must fail even with equal totals')
        src.lines[2].arcs = [1, 1]
        _, errors = reader.apply_exclusions({'src/x.c': src}, [row], root)
        if not (errors):
            raise RuntimeError('a now-reachable exclusion must fail')
    print('coverage controls: branch drop, missing/extra file, moved arc and stale exclusion refused')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
