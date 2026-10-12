#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Disposable fault probes of the ACMP publish port, outside the repository's plant list.

Usage: probe.py <head checkout> <work dir> <jobs>
Each probe is an exact, unique text replacement in src/acmp.c of an exported
copy of the head tree. The copy is built with GCC and its hosted tests run;
the RV32 smoke build is not used. A probe is CAUGHT when the build or any
AcmpCore test fails, ESCAPED when every test passes. Results go to
<work>/probes.json and stdout.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

PROBES = [
    ('control-blank-line-only',
     '// REQ: ACMP-10\nstatic void publish(struct acmp *a)',
     '// REQ: ACMP-10\n\nstatic void publish(struct acmp *a)'),
    ('loop-skips-last-sink',
     'for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tbool settled',
     'for (unsigned k = 0; k + 1u < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tbool settled'),
    ('settled-excludes-rsv-ok',
     'bool settled = s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK;',
     'bool settled = s->state == ACMP_SETTLED_NO_RSV;'),
    ('publish-only-when-send-refused',
     '\tpublish(a);\n\tif (a->owed_count == 0u && p_send(a, interface, frame)) {\n\t\treturn SENT;\n\t}\n',
     '\tif (a->owed_count == 0u && p_send(a, interface, frame)) {\n\t\treturn SENT;\n\t}\n\tpublish(a);\n'),
    ('moved-means-nonzero',
     'bool moved = stream != s->published_stream;',
     'bool moved = stream != 0u;'),
    ('guard-left-set',
     'a->ports->publish(a->ports->ctx, interface, sink, bound, started, stream, moved);\n\ta->in_port = false;',
     'a->ports->publish(a->ports->ctx, interface, sink, bound, started, stream, moved);'),
    ('finish-publishes-after-timers-and-admission',
     '\tpublish(a);\n\trearm(a);\n\tadmit(a);\n',
     '\trearm(a);\n\tadmit(a);\n\tpublish(a);\n'),
    ('finish-publishes-after-timers',
     '\tpublish(a);\n\trearm(a);\n\tadmit(a);\n',
     '\trearm(a);\n\tpublish(a);\n\tadmit(a);\n'),
    ('finish-publishes-after-persistence',
     '\tpublish(a);\n\trearm(a);\n\tadmit(a);\n\tfor (unsigned k = 0; k < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tuint8_t record[ACMP_BINDING_BYTES];\n\t\trecord_of(s, record);\n\t\tif (!same_record(record, s->saved)) {\n\t\t\tmemcpy(s->saved, record, ACMP_BINDING_BYTES);\n\t\t\tp_persist(a, k);\n\t\t}\n',
     '\trearm(a);\n\tadmit(a);\n\tfor (unsigned k = 0; k < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tuint8_t record[ACMP_BINDING_BYTES];\n\t\trecord_of(s, record);\n\t\tif (!same_record(record, s->saved)) {\n\t\t\tmemcpy(s->saved, record, ACMP_BINDING_BYTES);\n\t\t\tp_persist(a, k);\n\t\t}\n\t\tpublish(a);\n'),
    ('reset-drops-stream-cache-only',
     '\ts->published_stream = published_stream;\n\ts->interface',
     '\t(void)published_stream;\n\ts->interface'),
    ('reset-drops-bound-cache-only',
     '\ts->published_bound = published_bound;\n',
     '\t(void)published_bound;\n'),
]


def run(argv, cwd, log):
    result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.append(f'$ {" ".join(argv)}\n{result.stdout}\nrc {result.returncode}\n')
    return result.returncode, result.stdout


def probe(head, work, item, jobs):
    name, old, new = item
    tree = work / name
    subprocess.run(['rm', '-rf', str(tree)], check=True)
    tree.mkdir(parents=True)
    archive = subprocess.run(['git', '-C', str(head), 'archive', 'HEAD'], stdout=subprocess.PIPE, check=True).stdout
    subprocess.run(['tar', '-x', '-C', str(tree)], input=archive, check=True)
    source = tree / 'src/acmp.c'
    text = source.read_text()
    log = []
    if text.count(old) != 1 or old == new:
        return {'probe': name, 'status': 'INVALID', 'detail': f'old text occurs {text.count(old)} times'}
    source.write_text(text.replace(old, new))
    build = tree / 'build'
    rc, _ = run(['cmake', '-S', str(tree), '-B', str(build), '-DCMAKE_BUILD_TYPE=Debug',
                 '-DCMAKE_C_COMPILER=gcc', '-DCMAKE_CXX_COMPILER=g++'], tree, log)
    if rc == 0:
        rc, _ = run(['cmake', '--build', str(build), f'-j{jobs}'], tree, log)
    if rc != 0:
        (work / f'{name}.log').write_text(''.join(log))
        return {'probe': name, 'status': 'CAUGHT', 'detail': 'build failed'}
    rc, out = run(['ctest', '--test-dir', str(build), '--output-on-failure', f'-j{jobs}'], tree, log)
    (work / f'{name}.log').write_text(''.join(log))
    failed = sorted({line.split()[1] for line in out.splitlines() if line.startswith('[  FAILED  ]') and len(line.split()) > 1 and '.' in line.split()[1]})
    return {'probe': name, 'status': 'CAUGHT' if rc else 'ESCAPED', 'failed_tests': failed}


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__)
    head, work, jobs = Path(argv[1]).resolve(), Path(argv[2]).resolve(), int(argv[3])
    work.mkdir(parents=True, exist_ok=True)
    per = max(1, 16 // jobs)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(lambda item: probe(head, work, item, per), PROBES))
    for r in results:
        print(json.dumps(r))
    (work / 'probes.json').write_text(json.dumps(results, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
