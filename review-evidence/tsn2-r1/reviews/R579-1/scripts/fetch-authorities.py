#!/usr/bin/env python3
"""Fetch only the pinned public source files needed by the mapping probes.
Usage: python3 fetch-authorities.py SCRATCH_DIRECTORY
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
revision="5603c353137e90c1fa95429f6d00ef7a2298d9ee"
files={"sw/builder/endstation_builder.py":"4372d698990537b1d7ca8b43c66283be8b70989a1cb18542975dde53cd20838f",
       "configs/endstation_ax7101_1x1_tdm8.yaml":"6e1463f68ec2cf8b97b7c89a8b5930ed62e05e267ddb16bd87bf2b36dd992fa1"}
for path,expected in files.items():
 response=json.loads(subprocess.check_output(["gh","api",f"repos/kebag-logic/milan-fpga/contents/{path}?ref={revision}"]))
 data=base64.b64decode(response["content"])
 assert hashlib.sha256(data).hexdigest()==expected,path
 (out/Path(path).name).write_bytes(data)
 print(expected,Path(path).name)
