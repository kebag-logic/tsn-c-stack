#!/bin/sh
# SPDX-License-Identifier: MIT
# Disposable fault probes for publish-port cases outside the planted table.
# Each variant is the exact head tree with one replacement in src/acmp.c; the
# full acmp_tests binary runs and the failing test names are recorded.
# Usage: probes.sh <head checkout> <work dir>   (needs the pinned GoogleTest env)
set -u
head=$1 work=$2
mkdir -p "$work"
probe() {
  name=$1 old=$2 new=$3
  tree=$work/$name
  mkdir -p "$tree"
  git -C "$head" archive HEAD | tar -x -C "$tree"
  if [ "$name" != head ]; then
    python3 -I -c 'import sys; p,o,n=sys.argv[1:]; o=o.encode().decode("unicode_escape"); n=n.encode().decode("unicode_escape"); t=open(p).read(); assert t.count(o)==1, o; open(p,"w").write(t.replace(o,n))' \
      "$tree/src/acmp.c" "$old" "$new" || { echo "$name: replacement failed"; return; }
  fi
  { cmake -S "$tree" -B "$tree/build" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ &&
    cmake --build "$tree/build" -j2 --target acmp_tests; } > "$tree/build.log" 2>&1 || { echo "$name: build failed"; return; }
  "$tree/build/acmp_tests" > "$tree/run.log" 2>&1
  rc=$?
  failed=$(grep -E '^\[  FAILED  \] [A-Za-z]' "$tree/run.log" | sed 's/^\[  FAILED  \] //; s/ (.*//' | sort -u | tr '\n' ' ')
  echo "$name: rc $rc; $(grep -E '^\[  PASSED  \]' "$tree/run.log" | tr -d '\n'); failed: ${failed:-none}"
}
probe head x x &
probe reset-drops-bound-cache-only '\ts->published_bound = published_bound;\n' '\t(void)published_bound;\n' &
probe reset-drops-started-cache-only '\ts->published_started = published_started;\n' '\t(void)published_started;\n' &
probe settled-ignores-rsv-ok 'bool settled = s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK;\n\t\tuint64_t stream' 'bool settled = s->state == ACMP_SETTLED_NO_RSV;\n\t\tuint64_t stream' &
probe moved-means-nonzero 'bool moved = stream != s->published_stream;' 'bool moved = stream != 0u;' &
probe publish-ignores-bound 's->bound != s->published_bound || s->started' 's->started' &
probe publish-skips-last-sink 'for (unsigned k = 0; k < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tbool settled' 'for (unsigned k = 0; k + 1u < a->cfg.n_sinks; ++k) {\n\t\tstruct acmp_sink *s = &a->sinks[k];\n\t\tbool settled' &
probe finish-publishes-after-admission '\tpublish(a);\n\trearm(a);\n\tadmit(a);\n' '\trearm(a);\n\tadmit(a);\n\tpublish(a);\n' &
wait
