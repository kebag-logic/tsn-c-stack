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
LOCAL_ORIGINS = {'ENTITY-01': ('tsn-c-stack issue 2', 'https://github.com/kebag-logic/tsn-c-stack/issues/2')}


def source_ids():
    """Pinned file line numbers and IDs, without upstream requirement text."""
    line_ids = {
        'docs/reference/FR_NFR.md': {
            187: 'FR-DISC-01',
            188: 'FR-DISC-02',
            189: 'FR-DISC-03',
            190: 'FR-DISC-04',
            191: 'FR-DISC-05',
            196: 'FR-ENUM-01',
            197: 'FR-ENUM-02',
            198: 'FR-CTRL-01',
            199: 'FR-CTRL-02',
            200: 'FR-CTRL-03',
            201: 'FR-CTRL-04',
            202: 'FR-CTRL-05',
            203: 'FR-CTRL-06',
            208: 'FR-MVU-01',
            209: 'FR-MVU-02',
            210: 'FR-MVU-03',
            215: 'FR-CONN-01',
            216: 'FR-CONN-02',
            217: 'FR-CONN-03',
            218: 'FR-CONN-04',
            223: 'FR-MAAP-01',
            224: 'FR-SRP-01',
            225: 'FR-SRP-02',
            226: 'FR-SRP-03',
            250: 'FR-CLK-01',
            251: 'FR-CLK-02',
            252: 'FR-CLK-03',
            253: 'FR-CLK-04',
            254: 'FR-CLK-05',
            269: 'FR-STR-01',
            270: 'FR-STR-02',
            271: 'FR-STR-03',
            272: 'FR-STR-03a',
            273: 'FR-STR-03b',
            274: 'FR-STR-04',
            275: 'FR-STR-05',
            280: 'FR-QOS-01',
            281: 'FR-QOS-02',
            282: 'FR-QOS-03',
            287: 'FR-MGT-01',
            288: 'FR-MGT-02',
            297: 'NFR-PERF-01',
            298: 'NFR-PERF-02',
            299: 'NFR-LAT-01',
            300: 'NFR-LAT-02',
            301: 'NFR-DET-01',
            306: 'NFR-TIME-01',
            307: 'NFR-TIME-02',
            308: 'NFR-TIME-03',
            313: 'NFR-SCUP-01',
            314: 'NFR-SCUP-02',
            315: 'NFR-SCUP-03',
            316: 'NFR-SCUP-04',
            321: 'NFR-SCOUT-01',
            322: 'NFR-SCOUT-02',
            323: 'NFR-SCOUT-03',
            324: 'NFR-SCOUT-04',
            325: 'NFR-SCOUT-05',
            326: 'NFR-SCOUT-06',
            327: 'NFR-SCOUT-07',
            328: 'NFR-SCOUT-08',
            464: 'NFR-RES-01',
            465: 'NFR-REL-01',
            466: 'NFR-REL-02',
            467: 'NFR-OBS-01',
            468: 'NFR-MAINT-01',
            469: 'NFR-PORT-01',
            470: 'NFR-SEC-01',
        },
        'REQUIREMENTS.md': {
            128: 'REQ-CSR-01',
            132: 'REQ-CSR-02',
            135: 'REQ-CSR-03',
            138: 'REQ-CSR-04',
            140: 'REQ-CSR-05',
            146: 'REQ-PTP-01',
            148: 'REQ-PTP-02',
            150: 'REQ-PTP-03',
            152: 'REQ-PTP-04',
            154: 'REQ-PTP-05',
            156: 'REQ-PTP-06',
            165: 'REQ-PTP-07',
            167: 'REQ-PTP-08',
            170: 'REQ-PTP-09',
            241: 'REQ-CBS-01',
            243: 'REQ-CBS-02',
            245: 'REQ-CBS-03',
            247: 'REQ-CBS-04',
            249: 'REQ-CBS-05',
            251: 'REQ-CBS-06',
            253: 'REQ-CBS-07',
            255: 'REQ-CBS-08',
            265: 'REQ-CLS-01',
            267: 'REQ-CLS-02',
            268: 'REQ-CLS-03',
            270: 'REQ-CLS-04',
            272: 'REQ-CLS-05',
            274: 'REQ-CLS-06',
            276: 'REQ-CLS-07',
            278: 'REQ-CLS-08',
            280: 'REQ-CLS-09',
            282: 'REQ-CLS-10',
            288: 'REQ-MAC-01',
            290: 'REQ-MAC-02',
            292: 'REQ-MAC-03',
            294: 'REQ-MAC-04',
            297: 'REQ-MAC-05',
            298: 'REQ-MAC-06',
            300: 'REQ-MAC-07',
            302: 'REQ-MAC-08',
            307: 'REQ-VER-01',
            309: 'REQ-VER-02',
            311: 'REQ-VER-03',
            314: 'REQ-VER-04',
            317: 'REQ-VER-05',
            322: 'REQ-VER-06',
        },
    }
    origins = {'milan-fpga ' + rid: SOURCE_BASE + filename + f'#L{line}'
               for filename, rows in line_ids.items() for line, rid in rows.items()}
    origins.update({
        'milan-fpga #665 memory': 'https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-5992455815',
        'milan-fpga #665 testing': 'https://github.com/kebag-logic/milan-fpga/issues/665#issuecomment-6008744385',
    })
    return origins


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
    pinned = source_ids()
    if len(origins) != len(set(origins)) or set(origins) != set(pinned):
        errors.append('source inventory is incomplete, duplicated or unknown')
    by_origin = {r.get('origin'): r for r in rows}
    by_id = {r['id']: r for r in requirements}
    for r in requirements:
        imported = r['id'].startswith('MF')
        local = r['id'] in LOCAL_ORIGINS
        if not imported and not local:
            if 'origin' in r or 'verification' in r:
                errors.append('legacy requirement cannot acquire an unchecked exemption: ' + r['id'])
            continue
        origin = r.get('origin')
        if local:
            if origin != LOCAL_ORIGINS[r['id']][0]:
                errors.append('local requirement has no matching issue origin: ' + r['id'])
            if method(r) != 'test':
                errors.append('local requirement must remain tested: ' + r['id'])
        else:
            source = by_origin.get(origin, {})
            if r['id'] not in source.get('requirements', []):
                errors.append('imported requirement has no matching origin row: ' + r['id'])
        if r.get('targets') != TARGETS:
            errors.append('requirement must address both targets: ' + r['id'])
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
        elif row['url'] != pinned.get(origin):
            errors.append('source row must link to its pinned ID anchor: ' + origin)
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
    text = BEGIN + '\n\n## Local requirements\n\n'
    text += 'These requirements originate in repository issues. Each applies to Linux and bare-metal RV32.\n\n'
    text += '| ID | Origin | Required behavior | Authority | Verification |\n|---|---|---|---|---|\n'
    for r in requirements:
        if r['id'] in LOCAL_ORIGINS:
            text += f'| <a id="{r["id"].lower()}"></a>{r["id"]} | {origin_link(r, catalog)} | {r["text"]} | '
            text += '; '.join(link(c) for c in r['clauses']) + ' | ' + verification(r) + ' |\n'
    text += '\n## Imported requirements\n\n'
    text += 'Every row applies to Linux and bare-metal RV32. Port obligations require integration evidence on each target.\n'
    text += 'Inspection rows name build or source evidence. Protocol tests run on Linux; RV32 executes the documented smoke subset.\n'
    text += 'The [traceability matrix](TRACEABILITY.md) names every supporting test.\n\n'
    text += '| ID | Origin | Portable requirement | Authority | Verification |\n|---|---|---|---|---|\n'
    for r in requirements:
        if 'origin' not in r or r['id'] in LOCAL_ORIGINS:
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


def origin_link(record, catalog):
    if record['id'] in LOCAL_ORIGINS:
        text, url = LOCAL_ORIGINS[record['id']]
        return link(dict(text=text, url=url))
    if 'origin' in record:
        source = next(row for row in catalog['rows'] if row['origin'] == record['origin'])
        return link(dict(text=record['origin'], url=source['url']))
    return '[Import baseline](REQUIREMENTS.md)'


def documented(requirements, text):
    ids = set(re.findall(r'^\|\s*(?:<a id="[^"]+"></a>)?([A-Z][A-Z0-9-]+)\s*\|', text, re.M))
    return ['requirement missing from REQUIREMENTS.md: ' + r['id'] for r in requirements if r['id'] not in ids]


def check_document(requirements, catalog, write=False):
    path = ROOT / 'docs/REQUIREMENTS.md'
    text = path.read_text()
    generated = render(requirements, catalog)
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return ['requirements document needs one generated section']
    updated = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: generated, text, flags=re.S)
    missing = documented(requirements, updated if write else text)
    if missing:
        return missing
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
        ('moved source anchor', lambda r, c: c['rows'][0].update(url=c['rows'][1]['url'])),
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
    local = next(i for i, r in enumerate(requirements) if r['id'] == 'ENTITY-01')
    controls += [
        ('missing issue origin', lambda r, c: r[local].pop('origin')),
        ('wrong issue origin', lambda r, c: r[local].update(origin='tsn-c-stack issue 3')),
        ('local exemption', lambda r, c: r[local]['verification'].update(method='port obligation')),
    ]
    for name, plant in controls:
        r, c = copy.deepcopy(requirements), copy.deepcopy(catalog)
        plant(r, c)
        if not validate(r, c):
            raise RuntimeError('metadata defect escaped: ' + name)
        print('requirement control caught: ' + name)
    document = (ROOT / 'docs/REQUIREMENTS.md').read_text()
    if documented(requirements, document):
        raise RuntimeError(documented(requirements, document))
    for record in requirements:
        rid = record['id']
        planted = re.sub(r'^\|\s*(?:<a id="[^"]+"></a>)?' + re.escape(rid) + r'\s*\|[^\n]*\n', '', document, flags=re.M)
        if documented(requirements, planted) != ['requirement missing from REQUIREMENTS.md: ' + rid]:
            raise RuntimeError('missing requirement definition escaped: ' + rid)
    print(f'requirement definitions: {len(requirements)} missing-row controls caught')
    print(f'requirement records: {len(controls)} metadata defects caught')


def load():
    return json.loads((ROOT / 'docs/requirement-origins.json').read_text())
