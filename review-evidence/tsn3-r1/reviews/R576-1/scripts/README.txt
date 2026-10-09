Reviewer scripts (R576-1). Placeholders in receipts: $PACKET = review packet, $CLONE = detached clone at the exact head,
$TOOLS = pinned tool root (gtest-1.14.0, clang-18).
  TOOLS=<root> scripts/run_gates.sh <clone> <packet>        validate.py --graphs and baremetal.py, logs and rc files in receipts/
  gcc -std=c11 -fsanitize=address,undefined -I<clone>/include probe/state_probe.c <clone>/src/adp.c   state and offset probe
  . scripts/env.sh; python3 probe/mutants.py <clone> <workdir> <jobs>                  reviewer mutation probe on disposable copies
  python3 scripts/sanitize.py <packet> OLD=PLACEHOLDER ...                              replace host locations in receipts
