#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Kebag Logic
# SPDX-License-Identifier: MIT
"""Exact gcov branch ratchet and inherited unreachable-state exclusions."""
from __future__ import annotations
import argparse, copy, gzip, json, re, subprocess, sys, tempfile
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MEASURED_ROOTS = ("src/", "include/")
NOT_FIRMWARE = ()
EXCLUSIONS_HEADING = "Coverage exclusions"
class Unmeasured(Exception):
    """The measurement could not be taken: exit 2, never a pass."""


@dataclass
class Line:
    """One source line as the runs saw it: executed or not, and its arcs."""

    count: int = 0
    arcs: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class Exclusion:
    """One row of the README's exclusion table."""

    file: str
    function: str
    statement: str
    uncovered: str
    reason: str


@dataclass(frozen=True)
class Permit:
    """What a row's Uncovered cell names: the positions (from 1) of the
    statement's arcs left uncovered, how many arcs the statement has, and a
    fragment of each unexecuted line."""

    arcs: tuple[int, ...]
    of: int
    lines: tuple[str, ...]


@dataclass
class Source:
    """One firmware source as every run saw it: its lines, and the line range
    of each of its functions."""

    lines: dict[int, Line] = field(default_factory=dict)
    functions: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass(frozen=True)
class Tally:
    """One file's coverage: covered and total lines and branch arcs."""

    lines: tuple[int, int]
    branches: tuple[int, int]


def merge_line(into: Line, count: int, arcs: list[int]) -> None:
    """Fold one build's view of a line into the merged one: the line counts as
    run when any build ran it, and its arcs are those of the builds with the
    most arcs, merged arc by arc. A build reporting fewer arcs (a shape
    constant folded a condition away) reports other arcs, so it neither adds
    to nor replaces the longer builds' measure."""
    into.count = max(into.count, count)
    if len(arcs) > len(into.arcs):
        into.arcs = list(arcs)
    elif len(arcs) == len(into.arcs):
        into.arcs = [max(a, b) for a, b in zip(arcs, into.arcs)]


def relative(path: str) -> str | None:
    """The firmware source a gcov file entry names, repository-relative, or None."""
    p = Path(path)
    try:
        rel = p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None
    if not rel.startswith(MEASURED_ROOTS) or any(part in f"/{rel}" for part in NOT_FIRMWARE):
        return None
    return rel


def read_gcov_json(doc: dict, merged: dict[str, Source]) -> None:
    """Fold one gcov JSON document (one object's data) into `merged`."""
    for entry in doc.get("files", []):
        rel = relative(entry.get("file", ""))
        if rel is None:
            continue
        source = merged.setdefault(rel, Source())
        for fn in entry.get("functions", []):
            source.functions[fn["name"]] = (int(fn["start_line"]), int(fn["end_line"]))
        per_line: dict[int, Line] = {}
        for ln in entry.get("lines", []):
            seen = per_line.setdefault(int(ln["line_number"]), Line())
            seen.count += int(ln.get("count", 0))
            seen.arcs += [int(b.get("count", 0)) for b in ln.get("branches", []) if not b.get("throw", False)]
        for number, seen in per_line.items():
            merge_line(source.lines.setdefault(number, Line()), seen.count, seen.arcs)


def collect(build_dirs: list[Path]) -> dict[str, Source]:
    """Run gcov over every .gcda under the build directories and merge."""
    merged: dict[str, Source] = {}
    gcdas = sorted(p for d in build_dirs for p in d.rglob("*.gcda"))
    if not gcdas:
        raise Unmeasured("no .gcda under the coverage build: nothing ran instrumented")
    with tempfile.TemporaryDirectory(prefix="fw-gcov.") as tmp:
        for k, gcda in enumerate(gcdas):
            out = Path(tmp) / str(k)
            out.mkdir()
            res = subprocess.run(["gcov", "--json-format", "--branch-probabilities", "-o", str(gcda.parent), str(gcda)],
                                 cwd=out, capture_output=True, text=True, check=False)
            docs = sorted(out.glob("*.gcov.json.gz"))
            if res.returncode != 0 or not docs:
                raise Unmeasured(f"gcov on {gcda.name} failed: {res.stderr.strip()[:200]}")
            for doc in docs:
                with gzip.open(doc, "rt", encoding="utf-8") as fh:
                    read_gcov_json(json.load(fh), merged)
    return merged


def exclusions(readme: str) -> list[Exclusion]:
    """The rows of the table under the exclusions heading of the README."""
    rows: list[Exclusion] = []
    inside = False
    for line in readme.splitlines():
        if line.startswith("#"):
            inside = line.lstrip("#").strip() == EXCLUSIONS_HEADING
            continue
        if not inside or not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] == "File":
            continue
        rows.append(Exclusion(*[c[1:-1] if c.startswith("`") and c.endswith("`") else c for c in cells]))
    return rows


#: The two parts of a row's Uncovered cell: "arc 1 of 2" or "arcs 2, 4 of 4",
#: and "line `frag`" or "lines `a`, `b`", the second after "; " when both
#: are there. A fragment may hold a semicolon of its own, so the cell is
#: read part by part, never split on one.
ARCS_PART = re.compile(r"arcs? (\d+(?:, \d+)*) of (\d+)")
LINES_PART = re.compile(r"lines? (`[^`]+`(?:, `[^`]+`)*)")


def parse_uncovered(text: str) -> Permit | None:
    """The items a row's Uncovered cell names, or None when it cannot be read."""
    rest = text.strip()
    arcs: tuple[int, ...] = ()
    of = 0
    m = ARCS_PART.match(rest)
    if m is not None:
        arcs, of = tuple(int(k) for k in m.group(1).split(", ")), int(m.group(2))
        rest = rest[m.end():]
        if rest and not rest.startswith("; "):
            return None
        rest = rest[2:]
    lines = LINES_PART.fullmatch(rest) if rest else None
    if (rest and lines is None) or not (arcs or lines):
        return None
    if list(arcs) != sorted(set(arcs)) or any(not 1 <= k <= of for k in arcs):
        return None
    return Permit(arcs, of, tuple(re.findall(r"`([^`]+)`", lines.group(1))) if lines else ())


def code_of(line: str) -> str:
    """A source line without its comments."""
    return re.sub(r"/\*.*?\*/", "", line).split("//", 1)[0].rstrip()


def statement_end(text: list[str], first: int, last: int) -> int | None:
    """The last line of the statement that starts on line `first`: the first
    line from it on, up to the function's `last`, where its parentheses close
    and its code ends a statement, opens a block or closes a control header.
    `text` is the whole file, numbered from 1."""
    depth = 0
    for n in range(first, last + 1):
        code = code_of(text[n - 1])
        depth += code.count("(") - code.count(")")
        if depth <= 0 and code.endswith((";", "{", ")")):
            return n
    return None


def uncovered_in(source: Source, span: tuple[int, int]) -> tuple[set[tuple[int, int]], set[int]]:
    """The uncovered arcs, as (line, index on the line), and the unexecuted
    lines of a function's line range."""
    arcs = {(n, k) for n, ln in source.lines.items() if span[0] <= n <= span[1]
            for k, a in enumerate(ln.arcs) if a == 0}
    return arcs, {n for n, ln in source.lines.items() if span[0] <= n <= span[1] and ln.count == 0}


def permitted(source: Source, text: list[str], span: tuple[int, int], row: Exclusion,
              permit: Permit) -> tuple[set[tuple[int, int]], set[int], list[str]]:
    """The arcs and lines one row names, located in the measurement, and
    what about them disagrees with it."""
    what = f"exclusion {row.file} {row.function}(): `{row.statement}`"
    starts = [n for n in range(span[0], span[1] + 1) if row.statement in text[n - 1]]
    hits = sum(text[n - 1].count(row.statement) for n in starts)
    if hits != 1:
        return set(), set(), [f"{what}: the statement occurs {hits} times in the function, not once"]
    first = starts[0]
    last = statement_end(text, first, span[1])
    if last is None:
        return set(), set(), [f"{what}: the statement does not end inside the function"]
    found: list[str] = []
    order = [(n, k, a) for n in range(first, last + 1) if n in source.lines
             for k, a in enumerate(source.lines[n].arcs)]
    arcs: set[tuple[int, int]] = set()
    if len(order) != permit.of:
        found.append(f"{what}: the statement (lines {first}-{last}) has {len(order)} arcs, the row says {permit.of}")
    else:
        open_at = tuple(p for p, (_n, _k, a) in enumerate(order, 1) if a == 0)
        if open_at != permit.arcs:
            found.append(f"{what}: arcs {list(open_at)} of the statement's {len(order)} are uncovered, "
                         f"the row names {list(permit.arcs)}")
        arcs = {(n, k) for p, (n, k, _a) in enumerate(order, 1) if p in permit.arcs}
    lines: set[int] = set()
    for frag in permit.lines:
        at = next((n for n in range(first, span[1] + 1) if frag in text[n - 1]), None)
        if at is None:
            found.append(f"{what}: no line from the statement's on holds `{frag}`")
        elif at not in source.lines:
            found.append(f"{what}: line {at} `{frag}` is not a line gcov measures")
        elif source.lines[at].count != 0:
            found.append(f"{what}: line {at} `{frag}` runs now")
        else:
            lines.add(at)
    return arcs, lines, found


def apply_exclusions(merged: dict[str, Source], rows: list[Exclusion],
                     root: Path = ROOT) -> tuple[dict[str, Source], list[str]]:
    """Take out exactly the items the rows name; (what is left, the findings)."""
    found: list[str] = []
    named: dict[tuple[str, str], tuple[set[tuple[int, int]], set[int]]] = {}
    for row in rows:
        what = f"exclusion {row.file} {row.function}(): `{row.statement}`"
        span = merged.get(row.file, Source()).functions.get(row.function)
        permit = parse_uncovered(row.uncovered)
        if not row.reason:
            found.append(f"{what}: no reason given")
        elif permit is None:
            found.append(f"{what}: cannot read {row.uncovered!r}")
        elif span is None:
            found.append(f"{what}: no such function in the measurement")
        else:
            text = (root / row.file).read_text(encoding="utf-8").splitlines()
            arcs, lines, wrong = permitted(merged[row.file], text, span, row, permit)
            found += wrong
            have = named.setdefault((row.file, row.function), (set(), set()))
            if arcs & have[0] or lines & have[1]:
                found.append(f"{what}: names an arc or a line another row of the function names")
            have[0].update(arcs)
            have[1].update(lines)
    for (rel, function), (arcs, lines) in named.items():
        source = merged[rel]
        open_arcs, open_lines = uncovered_in(source, source.functions[function])
        for n, k in sorted(open_arcs - arcs):
            found.append(f"exclusion {rel} {function}(): line {n} arc {k + 1} is uncovered, and no row names it")
        for n in sorted(open_lines - lines):
            found.append(f"exclusion {rel} {function}(): line {n} is unexecuted, and no row names it")
        for n, ln in list(source.lines.items()):
            ln.arcs = [a for k, a in enumerate(ln.arcs) if (n, k) not in arcs or a != 0]
            if n in lines and ln.count == 0:
                del source.lines[n]
    return merged, found


def tally(merged: dict[str, Source]) -> dict[str, Tally]:
    """Per file: covered and total lines and branch arcs."""
    out = {}
    for rel, source in sorted(merged.items()):
        lines = source.lines
        arcs = [a for ln in lines.values() for a in ln.arcs]
        out[rel] = Tally((sum(1 for ln in lines.values() if ln.count > 0), len(lines)),
                         (sum(1 for a in arcs if a > 0), len(arcs)))
    return out


def fraction(pair: tuple[int, int]) -> Fraction:
    """covered / total, a file with nothing to cover counting whole."""
    return Fraction(pair[0], pair[1]) if pair[1] else Fraction(1)


def read_ratchet(text: str) -> dict[str, Tally]:
    """The ratchet file: `file lines C/T branches C/T` per line, `#` comments."""
    out = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        rel, _l, lines, _b, branches = line.split()
        out[rel] = Tally(tuple(map(int, lines.split("/"))), tuple(map(int, branches.split("/"))))
    return out


def compare(measured: dict[str, Tally], ratchet: dict[str, Tally]) -> list[str]:
    """Every drop, and every file in one table and not the other."""
    found = []
    for rel in sorted(set(measured) | set(ratchet)):
        if rel not in ratchet:
            found.append(f"{rel}: measured, but the ratchet does not record it")
            continue
        if rel not in measured:
            found.append(f"{rel}: recorded in the ratchet, but nothing measured it")
            continue
        for kind in ("lines", "branches"):
            got, floor = getattr(measured[rel], kind), getattr(ratchet[rel], kind)
            if fraction(got) < fraction(floor):
                found.append(f"{rel}: {kind} {got[0]}/{got[1]} fell below the recorded {floor[0]}/{floor[1]}")
    return found


def render_ratchet(measured: dict[str, Tally]) -> str:
    """The ratchet file for a measurement."""
    head = ["# Exact per-file line and branch ratchet.",
            "# Exclusions and reasons: docs/COVERAGE.md",
            "# Generated by scripts/coverage.py --write."]
    rows = [f"{rel}  lines {t.lines[0]}/{t.lines[1]}  branches {t.branches[0]}/{t.branches[1]}"
            for rel, t in sorted(measured.items())]
    return "\n".join(head + rows) + "\n"


def report(raw: dict[str, Tally], kept: dict[str, Tally]) -> None:
    """The per-file table: before and after the exclusions."""
    print(f"{'file':<46} {'lines':>11} {'branches':>11}   after exclusions")
    for rel in sorted(kept):
        r, k = raw[rel], kept[rel]
        print(f"{rel:<46} {r.lines[0]:>5}/{r.lines[1]:<5} {r.branches[0]:>5}/{r.branches[1]:<5}   "
              f"lines {float(fraction(k.lines)) * 100:6.2f} %  branches {float(fraction(k.branches)) * 100:6.2f} %")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    raw = collect([args.build.resolve()])
    kept, errors = apply_exclusions(copy.deepcopy(raw), exclusions((ROOT / "docs/COVERAGE.md").read_text()))
    measured = tally(kept)
    report(tally(raw), measured)
    for file, source in kept.items():
        for n, line in source.lines.items():
            if line.count == 0 or any(a == 0 for a in line.arcs):
                errors.append(f"{file}:{n}: count={line.count}, arcs={line.arcs}")
    expected = {"src/adp.c", "src/acmp.c", "src/maap.c", "include/wire.h"}
    if set(measured) != expected:
        errors.append("measured source set differs from the four required files")
    ratchet = ROOT / "tests/coverage.ratchet"
    if ratchet.exists():
        errors += compare(measured, read_ratchet(ratchet.read_text()))
    elif not args.write:
        errors.append("ratchet missing")
    if errors:
        print("\n".join(errors))
        return 1
    if args.write:
        ratchet.write_text(render_ratchet(measured))
    return 0

if __name__ == "__main__":
    sys.exit(main())
