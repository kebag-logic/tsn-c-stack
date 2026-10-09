#!/usr/bin/env python3
# Fetch Ubuntu 24.04 (noble) packages, verifying Release -> Packages -> .deb SHA256 chains.
# Usage: fetch_noble.py OUTDIR PACKAGE...   (writes OUTDIR/<name>.deb and OUTDIR/fetched.tsv)
import hashlib, lzma, sys, urllib.request
from pathlib import Path
M = 'http://archive.ubuntu.com/ubuntu/'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
def get(url): return urllib.request.urlopen(url, timeout=120).read()
index = {}
for dist in ('noble', 'noble-updates'):
    rel = get(M + f'dists/{dist}/Release').decode()
    sha = {}
    on = False
    for line in rel.splitlines():
        if line.startswith('SHA256:'): on = True; continue
        if on and line.startswith(' '):
            h, size, name = line.split(); sha[name] = h
        elif on: on = False
    for comp in ('main', 'universe'):
        name = f'{comp}/binary-amd64/Packages.xz'
        data = get(M + f'dists/{dist}/{name}')
        assert hashlib.sha256(data).hexdigest() == sha[name], name
        for para in lzma.decompress(data).decode().split('\n\n'):
            f = dict(l.split(': ', 1) for l in para.splitlines() if ': ' in l and not l.startswith(' '))
            if 'Package' in f: index[f['Package']] = f  # updates override release
rows = []
for p in sys.argv[2:]:
    f = index[p]
    data = get(M + f['Filename'])
    h = hashlib.sha256(data).hexdigest()
    assert h == f['SHA256'], p
    (out / (p + '.deb')).write_bytes(data)
    rows.append(f"{p}\t{f['Version']}\t{f['Filename']}\t{h}")
    print(rows[-1], flush=True)
with (out / 'fetched.tsv').open('a') as fh: fh.write('\n'.join(rows) + '\n')
