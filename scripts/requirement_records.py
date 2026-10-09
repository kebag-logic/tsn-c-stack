# SPDX-License-Identifier: MIT
"""Validate and render the pinned source dispositions and imported requirements."""
import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = '5603c353137e90c1fa95429f6d00ef7a2298d9ee'
SOURCE_BASE = 'https://github.com/kebag-logic/milan-fpga/blob/' + SOURCE_COMMIT + '/'
TARGETS = ['Linux', 'bare-metal RV32']
METHODS = {'test', 'verified by inspection', 'port obligation'}
BEGIN = '<!-- requirements-port:start -->'
END = '<!-- requirements-port:end -->'


def source_ids():
    """The complete numbered row inventory at the cited source commit."""
    counts = {
        'FR-DISC': 5, 'FR-ENUM': 2, 'FR-CTRL': 6, 'FR-MVU': 3,
        'FR-CONN': 4, 'FR-MAAP': 1, 'FR-SRP': 3, 'FR-CLK': 5,
        'FR-STR': 5, 'FR-QOS': 3, 'FR-MGT': 2, 'NFR-PERF': 2,
        'NFR-LAT': 2, 'NFR-DET': 1, 'NFR-TIME': 3, 'NFR-SCUP': 4,
        'NFR-SCOUT': 8, 'NFR-RES': 1, 'NFR-REL': 2, 'NFR-OBS': 1,
        'NFR-MAINT': 1, 'NFR-PORT': 1, 'NFR-SEC': 1, 'REQ-CSR': 5,
        'REQ-PTP': 9, 'REQ-CBS': 8, 'REQ-CLS': 10, 'REQ-MAC': 8, 'REQ-VER': 6,
    }
    return {'milan-fpga ' + prefix + f'-{i:02d}'
            for prefix, count in counts.items() for i in range(1, count + 1)} | {
                'milan-fpga FR-STR-03a', 'milan-fpga FR-STR-03b',
                'milan-fpga #665 memory', 'milan-fpga #665 testing'}


def method(record):
    return record.get('verification', {}).get('method', 'test')


def link(part):
    return f"[{part['text']}]({part['url']})"


def valid_link(part):
    if not isinstance(part, dict) or not all(isinstance(part.get(k), str) and part[k].strip()
                                           for k in ('text', 'url')):
        return False
    url = part['url']
    if re.fullmatch(r'https://[^\s]+', url):
        return True
    path, _, fragment = url.partition('#')
    resolved = (ROOT / 'docs' / path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        return False
    if fragment and resolved.suffix == '.md':
        headings = re.findall(r'^#+ (.+)$', resolved.read_text(), re.M)
        anchors = {re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings}
        return fragment in anchors or f'id="{fragment}"' in resolved.read_text()
    return not fragment or bool(re.fullmatch(r'L[1-9][0-9]*', fragment))


def validate(requirements, catalog):
    errors = []
    if catalog.get('source_commit') != SOURCE_COMMIT:
        errors.append('source commit differs from the reviewed inventory')
    rows = catalog.get('rows', [])
    origins = [r.get('origin') for r in rows]
    if len(origins) != len(set(origins)) or set(origins) != source_ids():
        errors.append('source inventory is incomplete, duplicated or unknown')
    by_origin = {r.get('origin'): r for r in rows}
    by_id = {r['id']: r for r in requirements}
    for r in requirements:
        imported = r['id'].startswith('MF')
        if not imported:
            if 'origin' in r or 'verification' in r:
                errors.append('legacy requirement cannot acquire an unchecked exemption: ' + r['id'])
            continue
        origin = r.get('origin')
        source = by_origin.get(origin, {})
        if r['id'] not in source.get('requirements', []):
            errors.append('imported requirement has no matching origin row: ' + r['id'])
        if r.get('targets') != TARGETS:
            errors.append('imported requirement must address both targets: ' + r['id'])
        if not isinstance(r.get('text'), str) or not r['text'].strip():
            errors.append('empty requirement: ' + r['id'])
        clauses = r.get('clauses', [])
        if not clauses or not all(valid_link(c) for c in clauses):
            errors.append('missing or broken clause link: ' + r['id'])
        elif len({c['url'] for c in clauses}) != len(clauses):
            errors.append('repeat citation instead of one link per authority: ' + r['id'])
        verification = r.get('verification', {})
        if verification.get('method') not in METHODS:
            errors.append('unknown verification method: ' + r['id'])
        elif method(r) != 'test':
            if not isinstance(verification.get('reason'), str) or not verification['reason'].strip():
                errors.append('verification exemption needs a reason: ' + r['id'])
            evidence = verification.get('evidence', [])
            if not evidence or not all(valid_link(e) for e in evidence):
                errors.append('verification exemption needs linked evidence: ' + r['id'])
            if method(r) == 'port obligation' and not any(
                    e.get('url', '').startswith('PORTING.md#') for e in evidence):
                errors.append('port obligation needs a named port contract: ' + r['id'])
    for row in rows:
        origin = row.get('origin', '')
        ids = row.get('requirements', [])
        if not isinstance(row.get('reason'), str) or not row['reason'].strip():
            errors.append('source disposition needs a reason: ' + origin)
        if not valid_link({'text': origin, 'url': row.get('url')}):
            errors.append('source disposition needs a link: ' + origin)
        elif ' #665 ' not in origin:
            filename = 'REQUIREMENTS.md' if ' REQ-' in origin else 'docs/reference/FR_NFR.md'
            if not re.fullmatch(re.escape(SOURCE_BASE + filename) + r'#L[1-9][0-9]*', row['url']):
                errors.append('source row must link to the pinned file and line: ' + origin)
        elif not re.fullmatch(r'https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-[0-9]+', row['url']):
            errors.append('decision must link to its source comment: ' + origin)
        if len(ids) != len(set(ids)) or any(i not in by_id for i in ids):
            errors.append('source row has duplicate or unknown local IDs: ' + origin)
            continue
        if any(by_id[i].get('origin') != origin for i in ids):
            errors.append('source row and local origin disagree: ' + origin)
        expected = ('port obligation' if all(method(by_id[i]) == 'port obligation' for i in ids)
                    else 'ported') if ids else 'excluded'
        if row.get('disposition') != expected:
            errors.append('source disposition disagrees with local verification: ' + origin)
    return errors


def verification(record):
    v = record.get('verification', {})
    if method(record) == 'test':
        return 'Tested through the linked declarations.'
    return method(record) + ': ' + v['reason'] + ' ' + '; '.join(link(p) for p in v['evidence'])


def render(requirements, catalog):
    rows = {r['origin']: r for r in catalog['rows']}
    text = BEGIN + '\n\n## Imported requirements\n\n'
    text += 'Every row applies to Linux and bare-metal RV32. Port obligations require integration evidence on each target.\n'
    text += 'Inspection rows name build or source evidence. Protocol tests run on Linux; RV32 executes the documented smoke subset.\n'
    text += 'The [traceability matrix](TRACEABILITY.md) names every supporting test.\n\n'
    text += '| ID | Origin | Portable requirement | Authority | Verification |\n|---|---|---|---|---|\n'
    for r in requirements:
        if 'origin' not in r:
            continue
        source = rows[r['origin']]
        text += f'| <a id="{r["id"].lower()}"></a>{r["id"]} | [{r["origin"]}]({source["url"]}) | {r["text"]} | '
        text += '; '.join(link(c) for c in r['clauses']) + ' | ' + verification(r) + ' |\n'
    text += '\n## Source dispositions\n\n'
    text += 'This inventory covers all 68 FR/NFR rows and all 46 numbered product rows at the [source commit]('
    text += 'https://github.com/kebag-logic/milan-fpga/commit/' + SOURCE_COMMIT + ').\n'
    text += 'The two decision labels identify source comments; they are local locators, not upstream requirement IDs.\n'
    text += 'A ported row can split into tested behavior and port obligations. Excluded parts remain stated in its reason.\n\n'
    text += '| Source | Disposition | Local IDs | Reason or change to proposed mapping |\n|---|---|---|---|\n'
    for row in catalog['rows']:
        ids = '; '.join(f'[{i}](#{i.lower()})' for i in row['requirements']) or 'None'
        text += f'| [{row["origin"]}]({row["url"]}) | {row["disposition"]} | {ids} | {row["reason"]} |\n'
    return text + '\n' + END


def check_document(requirements, catalog, write=False):
    path = ROOT / 'docs/REQUIREMENTS.md'
    text = path.read_text()
    generated = render(requirements, catalog)
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return ['requirements document needs one generated section']
    updated = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: generated, text, flags=re.S)
    if write:
        path.write_text(updated)
    elif updated != text:
        return ['requirements source mapping is stale']
    return []


def selftest(requirements, catalog):
    """Planted metadata losses must fail without weakening test registration."""
    if validate(requirements, catalog):
        raise RuntimeError(validate(requirements, catalog))
    tested = next(i for i, r in enumerate(requirements) if r['id'].startswith('MF') and method(r) == 'test')
    port = next(i for i, r in enumerate(requirements) if method(r) == 'port obligation')
    inspection = next(i for i, r in enumerate(requirements) if method(r) == 'verified by inspection')
    source = next(i for i, r in enumerate(catalog['rows']) if r['requirements'])
    controls = [
        ('missing source', lambda r, c: c['rows'].pop()),
        ('duplicate source', lambda r, c: c['rows'].append(c['rows'][0])),
        ('unknown source', lambda r, c: c['rows'][0].update(origin='milan-fpga FR-UNKNOWN-01')),
        ('changed pin', lambda r, c: c.update(source_commit='0' * 40)),
        ('moving source link', lambda r, c: c['rows'][0].update(url=SOURCE_BASE.replace(SOURCE_COMMIT, 'dev') + 'REQUIREMENTS.md#L1')),
        ('missing origin', lambda r, c: r[tested].pop('origin')),
        ('different origin', lambda r, c: r[tested].update(origin=r[port]['origin'])),
        ('missing target', lambda r, c: r[tested]['targets'].pop()),
        ('empty text', lambda r, c: r[tested].update(text='')),
        ('missing clauses', lambda r, c: r[tested].update(clauses=[])),
        ('unlinked clause', lambda r, c: r[tested]['clauses'][0].update(url='')),
        ('duplicate authority', lambda r, c: r[tested]['clauses'].append(r[tested]['clauses'][0])),
        ('unknown method', lambda r, c: r[tested]['verification'].update(method='waived')),
        ('missing port reason', lambda r, c: r[port]['verification'].update(reason='')),
        ('missing inspection reason', lambda r, c: r[inspection]['verification'].update(reason='')),
        ('missing evidence', lambda r, c: r[inspection]['verification'].update(evidence=[])),
        ('broken evidence', lambda r, c: r[inspection]['verification']['evidence'][0].update(url='missing-file.md')),
        ('broken contract anchor', lambda r, c: r[port]['verification']['evidence'][0].update(url='PORTING.md#missing-contract')),
        ('legacy exemption', lambda r, c: r[0].update(verification={'method': 'port obligation'})),
        ('false exclusion', lambda r, c: c['rows'][source].update(disposition='excluded')),
        ('orphan import', lambda r, c: c['rows'][source].update(requirements=[])),
        ('unknown local ID', lambda r, c: c['rows'][source]['requirements'].append('MFUNKNOWN-01')),
        ('duplicate local ID', lambda r, c: c['rows'][source]['requirements'].append(c['rows'][source]['requirements'][0])),
        ('missing exclusion reason', lambda r, c: c['rows'][-3].update(reason='')),
    ]
    for name, plant in controls:
        r, c = copy.deepcopy(requirements), copy.deepcopy(catalog)
        plant(r, c)
        if not validate(r, c):
            raise RuntimeError('metadata defect escaped: ' + name)
        print('requirement control caught: ' + name)
    print(f'requirement records: {len(controls)} metadata defects caught')


def load():
    return json.loads((ROOT / 'docs/requirement-origins.json').read_text())
