#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate and check requirement-to-test links from test annotations."""
import argparse
import json
from pathlib import Path
import re
import test_registry
import requirement_records

ROOT = Path(__file__).resolve().parents[1]


def inventory(text):
    rows = []
    # Preserve offsets while hiding comments and literals. Registration is the
    # authority: unsupported macros cannot silently vanish from the inventory.
    token = r'R"([^ ()\\\t\r\n]*)\(.*?\)\1"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*'
    code = re.sub(token, lambda m: re.sub(r'[^\n]', ' ', m[0]), text, flags=re.S)
    pattern = r'\bTEST(?:_F|_P)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)'
    for match in re.finditer(pattern, code):
        n = text.count('\n', 0, match.start())
        lines = text[:match.start()].splitlines()
        before = next((line.strip() for line in reversed(lines) if line.strip()), '')
        annotation = re.fullmatch(r'//\s*REQ:\s*(.*)', before)
        ids = [value.strip() for value in annotation[1].split(',')] if annotation else []
        rows.append((match[1] + '.' + match[2], ids, n + 1))
    return rows


def clauses(record):
    return '; '.join(f"[{part['text']}]({part['url']})" for part in record['clauses'])


def validate(requirements, rows):
    known = {r["id"] for r in requirements}
    errors = []
    if len(known) != len(requirements):
        errors.append("duplicate requirement ID")
    used = set()
    names = set()
    for name, ids, _ in rows:
        if name in names:
            errors.append("duplicate test: " + name)
        names.add(name)
        if not ids:
            errors.append("untraced test: " + name)
        for req in ids:
            if req not in known:
                errors.append("unknown requirement: " + req)
            used.add(req)
    exempt = {r['id'] for r in requirements
              if r['id'].startswith('MF') and requirement_records.method(r) in
              {'verified by inspection', 'port obligation'} and
              r.get('verification', {}).get('reason', '').strip() and
              r.get('verification', {}).get('evidence')}
    errors += ["untested requirement: " + req for req in sorted(known - used - exempt)]
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument('--build', type=Path, default=Path('build-registration'))
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    if args.selftest:
        reqs = [{"id": "R1"}]
        if validate(reqs, inventory("// REQ: R1\nTEST(S, T) {}")):
            raise RuntimeError('validation failed: not validate(reqs, inventory("// REQ: R1\\nTEST(S, T) {}"))')
        if not (validate(reqs, inventory("// REQ: WRONG\nTEST(S, T) {}"))):
            raise RuntimeError('validation failed: validate(reqs, inventory("// REQ: WRONG\\nTEST(S, T) {}"))')
        if not (validate(reqs, inventory("TEST(S, T) {}"))):
            raise RuntimeError('validation failed: validate(reqs, inventory("TEST(S, T) {}"))')
        if not (validate(reqs, [])):
            raise RuntimeError('validation failed: validate(reqs, [])')
        for declaration in (' TEST(S, T)', '  TEST(\n S,\n T\n )'):
            if not (validate(reqs, inventory('// REQ: WRONG\n' + declaration + ' {}'))):
                raise RuntimeError("validation failed: validate(reqs, inventory('// REQ: WRONG\\n' + declaration + ' {}'))")
            if validate(reqs, inventory('// REQ: R1\n' + declaration + ' {}')):
                raise RuntimeError("validation failed: not validate(reqs, inventory('// REQ: R1\\n' + declaration + ' {}'))")
        if not (test_registry.reconcile([], ['S.T'])):
            raise RuntimeError("validation failed: test_registry.reconcile([], ['S.T'])")
        print("traceability: unknown ID, untraced test and untested requirement controls refused")
    reqs = json.loads((ROOT / "docs/requirements.json").read_text())
    catalog = requirement_records.load()
    record_errors = requirement_records.validate(reqs, catalog)
    if record_errors:
        print('\n'.join(record_errors))
        return 1
    if args.selftest:
        requirement_records.selftest(reqs, catalog)
        tested = next(r for r in reqs if r['id'].startswith('MF') and requirement_records.method(r) == 'test')
        if not validate([tested], []):
            raise RuntimeError('imported tested requirement lost its test without failure')
        for r in reqs:
            if requirement_records.method(r) != 'test' and validate([r], []):
                raise RuntimeError('documented inspection or port obligation refused: ' + r['id'])
    rows = []
    locations = {}
    for path in sorted((ROOT / "tests").glob("test_*.cpp")):
        found = inventory(path.read_text())
        rows += found
        locations.update({name: f"../tests/{path.name}#L{line}" for name, _, line in found})
    errors = validate(reqs, rows)
    errors += requirement_records.check_document(reqs, catalog, args.write)
    errors += test_registry.reconcile(rows, test_registry.read_build(ROOT, args.build, args.jobs))
    if errors:
        print("\n".join(errors))
        return 1
    text = "# Traceability\n\nGenerated by [traceability.py](../scripts/traceability.py).\nEdit [requirement records](requirements.json), [source dispositions](requirement-origins.json) and the test annotations.\nSee [requirements](REQUIREMENTS.md) for scope and [test defects](TESTS.md) for sensitivity.\nBoth Linux and bare-metal RV32 are required. The [verification guide](VERIFICATION.md) distinguishes hosted campaigns from RV32 smoke execution.\nPort obligations are not claims of completed integration or measured target timing.\n\n| Requirement | Origin | Clause | Verification and tests |\n|---|---|---|---|\n"
    origins = {r['origin']: r for r in catalog['rows']}
    for r in reqs:
        tests = [f"[{name}]({locations[name]})" for name, ids, _ in rows if r['id'] in ids]
        origin = f"[{r['origin']}]({origins[r['origin']]['url']})" if 'origin' in r else '[Import baseline](REQUIREMENTS.md)'
        evidence = '; '.join(tests) if requirement_records.method(r) == 'test' else requirement_records.verification(r)
        text += f"| [{r['id']}](REQUIREMENTS.md) | {origin} | {clauses(r)} | {evidence} |\n"
    path = ROOT / "docs/TRACEABILITY.md"
    if args.write:
        path.write_text(text)
    elif not path.exists() or path.read_text() != text:
        print("traceability matrix is stale")
        return 1
    print(f"traceability: {len(reqs)} requirements; {len(rows)} test declarations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
