#!/bin/sh
# SPDX-License-Identifier: MIT
# Disposable witness tests for two publish-port claims, run against the head
# tree and against one fault probe each. A witness that passes on head and
# fails on its probe shows the probe is observable and not equivalent.
# Usage: witness.sh <head checkout> <work dir>
set -u
head=$1 work=$2
mkdir -p "$work"
cat > "$work/witness.cpp" <<'EOF'
TEST_F(AcmpCore, R622WitnessTheSettlementIsPublishedBeforeTheTimerPort) {
    bind(0);
    fk.clear();
    rx(probe_answer(0));
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness the settlement publishes once";
    const int timer = fk.position(Call::TIMER);
    ASSERT_GE(timer, 0) << "R622 witness the settlement re-arms the interface timer";
    EXPECT_LE(fk.pubs[0].before, static_cast<std::size_t>(timer))
        << "R622 witness publication precedes the timer port in finish";
}

TEST_F(AcmpCore, R622WitnessAStoreResetOfASettledSinkMovesItsStream) {
    to_state(0, ACMP_SETTLED_NO_RSV);
    ASSERT_NE(a.sinks[0].published_stream, 0u) << "R622 witness the settled stream was published";
    const auto none = payload(0u, 0u, 0u, 0u);
    fk.clear();
    ASSERT_EQ(acmp_restore_binding(&a, 0, none.data(), spec::BINDING_BYTES), ACMP_RESTORE_APPLIED);
    acmp_open(&a);
    ASSERT_EQ(fk.pubs.size(), 1u) << "R622 witness the reset sink is published at the next open";
    EXPECT_TRUE(!fk.pubs[0].bound && fk.pubs[0].stream == 0u && fk.pubs[0].moved)
        << "R622 witness the withdrawn stream is reported moved";
}

}
EOF
status=0
for variant in head finish-publishes-after-timers reset-drops-stream-cache-only; do
  tree=$work/$variant
  rm -rf "$tree"; mkdir -p "$tree"
  git -C "$head" archive HEAD | tar -x -C "$tree"
  case $variant in
    finish-publishes-after-timers)
      python3 -I -c 'import sys; p=sys.argv[1]; t=open(p).read(); o="\tpublish(a);\n\trearm(a);\n\tadmit(a);\n"; assert t.count(o)==1; open(p,"w").write(t.replace(o,"\trearm(a);\n\tpublish(a);\n\tadmit(a);\n"))' "$tree/src/acmp.c" ;;
    reset-drops-stream-cache-only)
      python3 -I -c 'import sys; p=sys.argv[1]; t=open(p).read(); o="\ts->published_stream = published_stream;\n\ts->interface"; assert t.count(o)==1; open(p,"w").write(t.replace(o,"\t(void)published_stream;\n\ts->interface"))' "$tree/src/acmp.c" ;;
  esac
  # Replace the namespace's closing brace (the file's last non-empty line) with the witnesses.
  python3 -I -c 'import sys; p,w=sys.argv[1:]; t=open(p).read().rstrip(); assert t.endswith("}"); open(p,"w").write(t[:-1]+open(w).read())' "$tree/tests/test_acmp.cpp" "$work/witness.cpp"
  { cmake -S "$tree" -B "$tree/build" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ &&
    cmake --build "$tree/build" -j8 --target acmp_tests; } > "$tree/build.log" 2>&1 || { echo "$variant: build failed"; status=1; continue; }
  "$tree/build/acmp_tests" --gtest_filter='AcmpCore.R622*:AcmpCore.A31*' > "$tree/run.log" 2>&1
  rc=$?
  echo "$variant: rc $rc; $(grep -E '^\[  (PASSED|FAILED)  \]' "$tree/run.log" | tr '\n' ' ')"
  grep -E 'R622 witness .*$' "$tree/run.log" | grep -v -E '^\s*$' | sed 's/^/    /' | head -4
done
exit $status
