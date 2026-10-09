#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Count the mapper plant table rows (header Plant | Planted defect | Required failing test) in a GitHub-rendered ENTITY_YAML.md HTML file.

Usage: render_check.py RENDERED.html [EXPECTED_ROWS]
Exit 0 when the table has exactly EXPECTED_ROWS (default 13) body rows, every
row has three cells, and the prose after the table is rendered outside it.
"""
from html.parser import HTMLParser
import sys


HEADER = ['Plant', 'Planted defect', 'Required failing test']


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.depth, self.cell, self.row, self.text = [], 0, None, None, []
        self.after = []          # paragraphs seen after the first plant table closed
        self.in_p = False
        self.closed_plant = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.depth += 1
            self.tables.append([])
        elif tag == 'tr' and self.depth:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []
        elif tag == 'p' and not self.depth:
            self.in_p, self.text = True, []

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None
        elif tag == 'table':
            self.depth -= 1
            if self.tables[-1] and self.tables[-1][0] == HEADER:
                self.closed_plant = True
        elif tag == 'p' and self.in_p:
            self.in_p = False
            if self.closed_plant and len(self.after) < 1:
                self.after.append(''.join(self.text).strip())

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
        if self.in_p:
            self.text.append(data)


def main():
    path = sys.argv[1]
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else 13
    parser = Tables()
    parser.feed(open(path, encoding='utf-8').read())
    plant = [t for t in parser.tables if t and t[0] == HEADER]
    if len(plant) != 1:
        print(f'FAIL: {len(plant)} plant tables')
        return 1
    header, body = plant[0][0], plant[0][1:]
    print('header:', header)
    for row in body:
        print('row:', row)
    print('body rows:', len(body))
    print('first paragraph after table:', parser.after[:1])
    ok = len(body) == expected and all(len(r) == 3 for r in body)
    ok = ok and not any('quality workflow' in ' '.join(r) for r in body)
    ok = ok and bool(parser.after) and parser.after[0].startswith('The quality workflow')
    print('PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
