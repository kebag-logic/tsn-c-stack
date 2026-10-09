# SPDX-License-Identifier: MIT
"""Disposable fault probes against an exact-head export.

Usage: python3 -I probe_driver.py <repo> <work> <probes.json> <jobs>
Each probe exports HEAD with git archive into <work>/<name>, applies exact
single-occurrence edits, builds the four GoogleTest binaries and runs them.
Failing tests are mapped to their `// REQ:` tags from the probe's own sources.
A probe passes the check when at least one failing test carries every
requirement listed in `breaks`. The baseline probe must fail nothing.
"""
import concurrent.futures as cf, json, re, subprocess, sys
from pathlib import Path

repo, work, spec, jobs = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
probes = json.loads(spec.read_text())
BINS = ['adp_tests', 'acmp_tests', 'maap_tests', 'port_tests']


def tags(root):
    out = {}
    for f in (root / 'tests').glob('*.cpp'):
        lines = f.read_text().splitlines()
        for i, line in enumerate(lines):
            m = re.match(r'\s*TEST(?:_F)?\(\s*(\w+)\s*,\s*(\w+)\s*\)', line)
            if m:
                j, req = i - 1, []
                while j >= 0 and lines[j].startswith('//'):
                    r = re.match(r'// REQ:\s*(.+)', lines[j])
                    if r:
                        req += [x.strip() for x in r.group(1).split(',')]
                    j -= 1
                out[f'{m.group(1)}.{m.group(2)}'] = req
    return out


def sh(cmd, log, cwd=None):
    with open(log, 'a') as fh:
        fh.write('$ ' + ' '.join(map(str, cmd)) + '\n')
        fh.flush()
        return subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT).returncode


def one(p):
    d = work / p['name']
    log = work / (p['name'] + '.log')
    log.write_text('')
    subprocess.run(['rm', '-rf', str(d)], check=True)
    d.mkdir(parents=True)
    a = subprocess.Popen(['git', '-C', str(repo), 'archive', 'HEAD'], stdout=subprocess.PIPE)
    subprocess.run(['tar', '-x', '-C', str(d)], stdin=a.stdout, check=True)
    a.wait()
    for e in p.get('edits', []):
        f = d / e['path']
        text = f.read_text()
        n = text.count(e['old'])
        if n != 1:
            return {'name': p['name'], 'error': f"edit matches {n} times in {e['path']}"}
        f.write_text(text.replace(e['old'], e['new']))
    b = d / 'build'
    if sh(['cmake', '-S', d, '-B', b, '-DCMAKE_BUILD_TYPE=Debug'], log):
        return {'name': p['name'], 'error': 'configure failed'}
    if sh(['cmake', '--build', b, '-j2', '--target'] + BINS, log):
        return {'name': p['name'], 'build': 'failed (compile error counts as no kill)'}
    failed = []
    for exe in BINS:
        x = b / (exe + '.json')
        sh([b / exe, f'--gtest_output=json:{x}'], log)
        if x.exists():
            for suite in json.loads(x.read_text())['testsuites']:
                for t in suite['testsuite']:
                    if t.get('failures'):
                        failed.append(f"{suite['name']}.{t['name']}")
        else:
            failed.append(exe + ':<no report>')
    tg = tags(d)
    res = {'name': p['name'], 'breaks': p.get('breaks', []), 'failed': {t: tg.get(t, []) for t in failed}}
    need = set(p.get('breaks', []))
    if p.get('baseline'):
        res['verdict'] = 'PASS' if not failed else 'FAIL'
    else:
        hit = [t for t, r in res['failed'].items() if need <= set(r)]
        res['tagged_killers'] = hit
        res['verdict'] = 'KILLED-BY-TAGGED' if hit else ('KILLED-UNTAGGED' if failed else 'SURVIVED')
    return res


work.mkdir(parents=True, exist_ok=True)
with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
    results = list(ex.map(one, probes))
for r in results:
    print(json.dumps(r, sort_keys=True))
(work / 'results.json').write_text(json.dumps(results, indent=1, sort_keys=True))
