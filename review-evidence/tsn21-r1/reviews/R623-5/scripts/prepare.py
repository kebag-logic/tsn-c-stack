#!/usr/bin/env python3
"""Prepare disposable integration and pinned interface authorities; read-only network."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
from pathlib import Path
import subprocess
import tarfile

p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
packet=Path(__file__).resolve().parents[1]
scratch=packet/'scratch';scratch.mkdir(exist_ok=True)
integration=scratch/'integration';integration.mkdir(exist_ok=True)
archive=subprocess.check_output(['git','archive','3c9ca52fc44b4a37e11149392363686f0ea426e0'],cwd=a.source)
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(integration,filter='data')
upstream=scratch/'upstream';upstream.mkdir(exist_ok=True)
paths={'acmp.c':'sw/firmware/ctrl/acmp/acmp.c','acmp.h':'sw/firmware/ctrl/acmp/acmp.h',
       'wire.h':'sw/firmware/ctrl/wire/wire.h','test_acmp.cpp':'sw/firmware/ctrl/test/test_acmp.cpp',
       'acmp_fake.hpp':'sw/firmware/ctrl/test/acmp_fake.hpp'}
def fetch(item):
    name,path=item
    data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',
        'repos/kebag-logic/milan-fpga/contents/'+path+'?ref=09c7231eca343607c97c0d66abebb2553688712c'])
    (upstream/name).write_bytes(data)
with ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(fetch,paths.items()))
