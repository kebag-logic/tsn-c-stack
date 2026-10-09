#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Print the table shapes and full text diff of two GitHub-rendered HTML files.

Usage: compare_rendered_tables.py PARENT.html HEAD.html
"""
import difflib
import html.parser
import sys


class T(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._t = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._t = 0
        elif tag == "tr" and self._t is not None:
            self._t += 1

    def handle_endtag(self, tag):
        if tag == "table" and self._t is not None:
            self.tables.append(self._t)
            self._t = None


def shapes(path):
    p = T()
    p.feed(open(path, encoding="utf-8").read())
    return p.tables


a, b = shapes(sys.argv[1]), shapes(sys.argv[2])
print("parent table row counts (incl. header):", a)
print("head   table row counts (incl. header):", b)
diff = list(difflib.unified_diff(open(sys.argv[1]).read().splitlines(),
                                 open(sys.argv[2]).read().splitlines(),
                                 "parent", "head", lineterm="", n=1))
print(f"rendered HTML diff lines: {len(diff)}")
print("\n".join(diff))
