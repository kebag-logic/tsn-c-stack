#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: fetch_source.sh <output dir>
# Fetches the pinned milan-fpga builder and the five end-station configs (read-only GitHub API).
set -eu
out=$1 sha=5603c353137e90c1fa95429f6d00ef7a2298d9ee
mkdir -p "$out/configs"
gh api "repos/kebag-logic/milan-fpga/contents/sw/builder/endstation_builder.py?ref=$sha" -H 'Accept: application/vnd.github.raw' > "$out/endstation_builder.py"
for f in endstation_arty_4x4 endstation_arty_8ch endstation_arty_current endstation_ax7101_1x1_tdm8 endstation_ax7101_8x8; do
  gh api "repos/kebag-logic/milan-fpga/contents/configs/$f.yaml?ref=$sha" -H 'Accept: application/vnd.github.raw' > "$out/configs/$f.yaml"
done
(cd "$out" && sha256sum endstation_builder.py configs/*.yaml)
