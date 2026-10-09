# SPDX-License-Identifier: MIT
"""Independent check of the pinned source line-to-ID map.

Usage: python3 -I anchor_check.py <repo> <upstream-dir>
<upstream-dir> holds FR_NFR.md and REQUIREMENTS.md fetched at the pinned commit.
Checks: every mapped line defines exactly that ID; every defining row in the
upstream files is mapped; every catalog URL equals its mapped anchor; and a
planted moved anchor is refused by the repository validator.
"""
import copy, json, re, sys
from pathlib import Path

repo, up = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / 'scripts'))
import requirement_records as rr  # noqa: E402

files = {'docs/reference/FR_NFR.md': up / 'FR_NFR.md', 'REQUIREMENTS.md': up / 'REQUIREMENTS.md'}
define = {'docs/reference/FR_NFR.md': re.compile(r'^\| *((?:FR|NFR)-[A-Z]+-[0-9]+[a-z]?) *\|'),
          'REQUIREMENTS.md': re.compile(r'^- \*\*(REQ-[A-Z]+-[0-9]+) \(')}
pinned = rr.source_ids()
errors = []
mapped = {}
for origin, url in pinned.items():
    m = re.fullmatch(re.escape(rr.SOURCE_BASE) + r'(.+)#L([0-9]+)', url)
    if not m:
        continue
    mapped.setdefault(m.group(1), {})[int(m.group(2))] = origin.split(' ', 1)[1]
found = {}
for name, path in files.items():
    lines = path.read_text().splitlines()
    for n, text in enumerate(lines, 1):
        m = define[name].match(text)
        if m:
            found.setdefault(name, {})[n] = m.group(1)
for name in files:
    a, b = mapped.get(name, {}), found.get(name, {})
    for line, rid in a.items():
        if b.get(line) != rid:
            errors.append(f'{name}:L{line} map says {rid}, upstream defines {b.get(line)}')
    for line, rid in b.items():
        if a.get(line) != rid:
            errors.append(f'{name}:L{line} upstream defines {rid}, not mapped')
print('mapped rows', sum(len(v) for v in mapped.values()), 'upstream defining rows', sum(len(v) for v in found.values()))
catalog = rr.load() if hasattr(rr, 'load') else json.loads((repo / 'docs/requirement-origins.json').read_text())
for row in catalog['rows']:
    if pinned.get(row['origin']) != row['url']:
        errors.append('catalog url differs: ' + row['origin'])
print('catalog rows', len(catalog['rows']), 'pinned origins', len(pinned))
reqs = json.loads((repo / 'docs/requirements.json').read_text())
base = rr.validate(reqs, catalog)
print('baseline validator errors', base)
for i in (0, 10, len(catalog['rows']) - 3):
    c = copy.deepcopy(catalog)
    url = c['rows'][i]['url']
    if '#L' not in url:
        continue
    pre, line = url.rsplit('#L', 1)
    c['rows'][i]['url'] = f'{pre}#L{int(line) + 1}'
    got = rr.validate(reqs, c)
    print(f'moved anchor +1 on {c["rows"][i]["origin"]}:', 'REFUSED' if got else 'ACCEPTED', got)
    if not got:
        errors.append('moved anchor accepted: ' + c['rows'][i]['origin'])
print('errors', len(errors))
for e in errors:
    print('ERROR', e)
sys.exit(1 if errors or base else 0)
