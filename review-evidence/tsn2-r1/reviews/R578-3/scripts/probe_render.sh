#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: probe_render.sh <work dir> <ref>...
# Read-only GET of GitHub's rendered docs/ENTITY_YAML.md at each ref; lists table rows whose
# only non-empty cell is the first one (prose absorbed into a preceding table).
set -eu
w=$1; shift
for ref in "$@"; do
  gh api "repos/kebag-logic/tsn-c-stack/contents/docs/ENTITY_YAML.md?ref=$ref" -H 'Accept: application/vnd.github.html' > "$w/render-$ref.html"
  python3 -c '
import re, sys
t = re.sub(r"\s+", " ", open(sys.argv[1]).read())
rows = re.findall(r"<tr> <td>((?:(?!</tr>).)*?)</td>(?: <td></td>)+ </tr>", t)
print(sys.argv[2], "absorbed prose rows:", len(rows))
for r in rows:
    print("   ", re.sub("<[^>]+>", "", r).strip())
' "$w/render-$ref.html" "$ref"
done
