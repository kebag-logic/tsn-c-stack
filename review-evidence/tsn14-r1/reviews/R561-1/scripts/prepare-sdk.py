#!/usr/bin/env python3
"""Fetch pinned dependencies into a caller-owned scratch directory only."""
import concurrent.futures
import gzip
import hashlib
from pathlib import Path
import subprocess
import sys
import urllib.request

scratch = Path(sys.argv[1]).resolve()
sdk = scratch / 'sdk'
sdk.mkdir(parents=True, exist_ok=True)
base = 'https://apt.llvm.org/noble/'
index = urllib.request.urlopen(base + 'dists/llvm-toolchain-noble-18/main/binary-amd64/Packages.gz').read()
names = {'clang-18', 'libllvm18', 'libclang-cpp18', 'libclang-common-18-dev', 'libclang-rt-18-dev', 'libclang1-18', 'clang-tidy-18'}
records = []
for block in gzip.decompress(index).decode().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
    if fields.get('Package') in names:
        records.append(fields)
assert len(records) == len(names)

def fetch(record):
    path = scratch / Path(record['Filename']).name
    data = path.read_bytes() if path.exists() else urllib.request.urlopen(base + record['Filename']).read()
    assert hashlib.sha256(data).hexdigest() == record['SHA256']
    path.write_bytes(data)
    return record, path

with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
    for record, path in pool.map(fetch, records):
        print(record['Package'], record['Version'], record['SHA256'], flush=True)
        members = subprocess.check_output(['bsdtar', '-tf', str(path)], text=True).splitlines()
        member = next(x for x in members if x.startswith('data.tar.'))
        payload = scratch / member
        with payload.open('wb') as output:
            subprocess.run(['bsdtar', '-xOf', str(path), member], stdout=output, check=True)
        subprocess.run(['bsdtar', '-xf', str(payload), '-C', str(sdk)], check=True)

base = 'https://archive.ubuntu.com/ubuntu/'
index = urllib.request.urlopen(base + 'dists/noble/main/binary-amd64/Packages.gz').read()
names = {'libedit2', 'libxml2', 'libicu74', 'libbsd0', 'libmd0', 'libgcc-13-dev', 'libstdc++-13-dev'}
records = []
for block in gzip.decompress(index).decode().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
    if fields.get('Package') in names:
        records.append(fields)
assert len(records) == len(names)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for record, path in pool.map(fetch, records):
        print(record['Package'], record['Version'], record['SHA256'], flush=True)
        members = subprocess.check_output(['bsdtar', '-tf', str(path)], text=True).splitlines()
        member = next(x for x in members if x.startswith('data.tar.'))
        payload = scratch / member
        with payload.open('wb') as output:
            subprocess.run(['bsdtar', '-xOf', str(path), member], stdout=output, check=True)
        subprocess.run(['bsdtar', '-xf', str(payload), '-C', str(sdk)], check=True)

pin = 'f8d7d77c06936315286eb55f8de22cd23c188571'
archive = scratch / 'googletest.tar.gz'
data = urllib.request.urlopen('https://codeload.github.com/google/googletest/tar.gz/' + pin).read()
archive.write_bytes(data)
print('googletest', pin, hashlib.sha256(data).hexdigest(), flush=True)
subprocess.run(['tar', '-xzf', str(archive), '-C', str(scratch)], check=True)
subprocess.run(['cmake', '-S', str(scratch / ('googletest-' + pin)), '-B', str(scratch / 'gtest-build'), '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=' + str(scratch / 'gtest')], check=True)
subprocess.run(['cmake', '--build', str(scratch / 'gtest-build'), '-j16'], check=True)
subprocess.run(['cmake', '--install', str(scratch / 'gtest-build')], check=True)
