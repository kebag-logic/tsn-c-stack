#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render every Mermaid fence with the installed command-line renderer."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not shutil.which('mmdc'):
    raise SystemExit('mmdc is required for the graph gate')
args.output.mkdir(parents=True, exist_ok=True)
config = args.output / "browser.json"
config.write_text(json.dumps({"args": ["--no-sandbox"]}))
count = 0
for path in [ROOT / 'README.md', *sorted((ROOT / 'docs').glob('*.md'))]:
    for index, graph in enumerate(re.findall(r'```mermaid\n(.*?)```', path.read_text(), re.S)):
        name = path.stem + '-' + str(index)
        source = args.output / (name + '.mmd')
        image = args.output / (name + '.svg')
        source.write_text(graph)
        subprocess.run(['mmdc', '-p', str(config), '-i', str(source), '-o', str(image)], check=True)
        count += 1
if not count:
    raise SystemExit('no graphs found')
print(f'graphs: {count} rendered')
