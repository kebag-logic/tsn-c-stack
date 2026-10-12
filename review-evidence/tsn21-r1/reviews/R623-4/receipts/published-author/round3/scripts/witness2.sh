#!/bin/sh
# SPDX-License-Identifier: MIT
# Disposable witnesses for the per-field publication cache preserved by sink_reset.
# Each witness must pass on the exact head tree and fail on its fault probe, which
# shows the probe is observable through the public API and not equivalent.
# Usage: witness2.sh <head checkout> <work dir>   (needs the pinned GoogleTest env)
set -u
head=$1 work=$2
mkdir -p "$work"
cat > "$work/witness.cpp" <<'EOF'
TEST_F(AcmpCore, R622W2StoreResetOfABoundStoppedSinkPublishesItsWithdrawal) {
    bind(0, kTkA, 1, kCtl1, true);
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness2 the STREAMING_WAIT bind publishes once";
    ASSERT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u)
        << "R622 witness2 bound, stopped, no stream";
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness2 the withdrawal of a bound stopped sink is published at open";
    EXPECT_TRUE(!fk.pubs[0].bound && !fk.pubs[0].started && fk.pubs[0].stream == 0u)
        << "R622 witness2 published unbound";
}

TEST_F(AcmpCore, R622W3StoreRestoreOfAStoppedRecordPublishesTheStop) {
    bind(0);
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness3 the bind publishes once";
    ASSERT_TRUE(fk.pubs[0].bound && fk.pubs[0].started) << "R622 witness3 bound and started";
    const auto stopped = payload(kRecValid, 1u, kTkA, kCtl1);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, stopped.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness3 the restored stop is published at open";
    EXPECT_TRUE(fk.pubs[0].bound && !fk.pubs[0].started) << "R622 witness3 published bound and stopped";
}

}
EOF
run() {
  variant=$1 old=$2 new=$3
  tree=$work/$variant
  mkdir -p "$tree"
  git -C "$head" archive HEAD | tar -x -C "$tree"
  if [ "$variant" != head ]; then
    python3 -I -c 'import sys; p,o,n=sys.argv[1:]; o=o.encode().decode("unicode_escape"); n=n.encode().decode("unicode_escape"); t=open(p).read(); assert t.count(o)==1, o; open(p,"w").write(t.replace(o,n))' \
      "$tree/src/acmp.c" "$old" "$new" || { echo "$variant: replacement failed"; return; }
  fi
  python3 -I -c 'import sys; p,w=sys.argv[1:]; t=open(p).read().rstrip(); assert t.endswith("}"); open(p,"w").write(t[:-1]+open(w).read())' "$tree/tests/test_acmp.cpp" "$work/witness.cpp"
  { cmake -S "$tree" -B "$tree/build" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ &&
    cmake --build "$tree/build" -j4 --target acmp_tests; } > "$tree/build.log" 2>&1 || { echo "$variant: build failed"; return; }
  "$tree/build/acmp_tests" > "$tree/run.log" 2>&1
  rc=$?
  failed=$(grep -E '^\[  FAILED  \] [A-Za-z]' "$tree/run.log" | sed 's/^\[  FAILED  \] //; s/ (.*//' | sort -u | tr '\n' ' ')
  echo "$variant: rc $rc; $(grep -E '^\[  PASSED  \]' "$tree/run.log" | tr -d '\n'); failed: ${failed:-none}"
}
run head x x &
run reset-drops-bound-cache-only '\ts->published_bound = published_bound;\n' '\t(void)published_bound;\n' &
run reset-drops-started-cache-only '\ts->published_started = published_started;\n' '\t(void)published_started;\n' &
run settled-ignores-rsv-ok 'bool settled = s->state == ACMP_SETTLED_NO_RSV || s->state == ACMP_SETTLED_RSV_OK;\n\t\tuint64_t stream' 'bool settled = s->state == ACMP_SETTLED_NO_RSV;\n\t\tuint64_t stream' &
wait
