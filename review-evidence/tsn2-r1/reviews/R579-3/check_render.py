#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Count the rows of the rendered mapper plant table in docs/ENTITY_YAML.md.

Usage: python3 -I check_render.py RENDERED_HTML
RENDERED_HTML is the GitHub rendering of docs/ENTITY_YAML.md at the exact head, from
  gh api -H 'Accept: application/vnd.github.html' \
    'repos/kebag-logic/tsn-c-stack/contents/docs/ENTITY_YAML.md?ref=<head>'
Exit 0 only if the table has exactly the 13 plant rows.
"""
import re
import sys

html = open(sys.argv[1], encoding='utf-8').read()
start = html.find('<code>base-zero</code>')
table = html[html.rfind('<table', 0, start):html.find('</table>', start)]
rows = re.findall(r'<tr>(.*?)</tr>', table, re.S)[1:]
first = [re.sub(r'<[^>]+>|\s+', ' ', re.findall(r'<td>(.*?)</td>', r, re.S)[0]).strip() for r in rows]
for i, cell in enumerate(first, 1):
    print(f'{i:2d} {cell[:110]}')
print('rendered plant-table body rows:', len(first))
sys.exit(0 if len(first) == 13 else 1)
