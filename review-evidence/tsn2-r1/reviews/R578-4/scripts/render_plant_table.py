#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Count the rows of the mapper plant table in GitHub-rendered HTML.

Usage: render_plant_table.py RENDERED.html SOURCE.md

RENDERED.html is GitHub's rendering of SOURCE.md at the reviewed commit
(GET /repos/{o}/{r}/contents/{path}?ref={sha} with Accept:
application/vnd.github.html). The script finds the table whose header row
starts with "Plant", counts its body rows, checks that the prose sentence
following the source table is rendered as a paragraph outside the table, and
compares the rendered row names with the source rows. Exit 0 only when all
checks pass.
"""
import html.parser
import re
import sys


class Tables(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.paragraphs = []
        self._table = None
        self._row = None
        self._cell = None
        self._para = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "p" and self._table is None:
            self._para = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None
        elif tag == "p" and self._para is not None:
            self.paragraphs.append(" ".join("".join(self._para).split()))
            self._para = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)
        if self._para is not None:
            self._para.append(data)


def source_rows(md):
    lines = md.splitlines()
    start = next(i for i, l in enumerate(lines)
                 if l.startswith("| Plant | Planted defect |"))
    rows = []
    i = start + 2
    while i < len(lines) and lines[i].startswith("|"):
        rows.append(lines[i].split("|")[1].strip().strip("`"))
        i += 1
    follow = lines[i] if i < len(lines) else ""
    after = lines[i + 1] if i + 1 < len(lines) else ""
    return rows, follow, after


def main():
    rendered = open(sys.argv[1], encoding="utf-8").read()
    md = open(sys.argv[2], encoding="utf-8").read()
    src, follow, after = source_rows(md)
    p = Tables()
    p.feed(rendered)
    plant = [t for t in p.tables if t and t[0][:2] == ["Plant", "Planted defect"]]
    ok = True
    print(f"source plant rows: {len(src)}")
    print(f"source line after last row: {follow!r}")
    print(f"source line after that: {after[:60]!r}")
    print(f"rendered tables with mapper Plant header: {len(plant)}")
    if len(plant) != 1:
        print("FAIL: expected exactly one mapper Plant table")
        return 1
    body = plant[0][1:]
    names = [r[0] for r in body]
    print(f"rendered plant body rows: {len(body)}")
    for n in names:
        print(f"  row: {n}")
    if names != src:
        print("FAIL: rendered row names differ from source rows")
        ok = False
    stray = [r for r in body if len(r) != 3 or not r[0] or not r[2]]
    if stray:
        print(f"FAIL: malformed rendered rows: {stray}")
        ok = False
    nxt = after if not follow.strip() else follow
    prose = re.sub(r"\s+", " ", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", nxt)).strip()
    hit = [q for q in p.paragraphs if q.startswith(prose[:40])] if prose else []
    print(f"following prose rendered as paragraph: {bool(hit)}")
    if not hit:
        ok = False
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
