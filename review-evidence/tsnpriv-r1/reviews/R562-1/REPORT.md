[R562] NEGATIVE - exact head 61fb7c9a523b89cb96d493c5baf9f7f866ebed85

# R562-1 internal independent review: tsn-c-stack PR #17 (issue #14 blocker)

- Head `61fb7c9a523b89cb96d493c5baf9f7f866ebed85`, tree `adbb235a09246169ab95756fba0a7f163131924d`, base `18d737832c376f32660eb21fe2796e0b611507e3`.
- Diff: `docs/IMPORT.md` (+2), `docs/VERIFICATION.md` (+1), `scripts/check_privacy.py` (+17 −2), `scripts/validate.py` (+1).
- Reconstruction order: CONTRIBUTING.md (there is no AGENTS.md at this head), then docs/VERIFICATION.md and docs/IMPORT.md. Next came the issue #14 body and the manager's assignment and STOP comments, then the PR #17 body and its review-start comment. After that, the diff and history. Last came the author evidence at `deca7adc…/review-evidence/tsnpriv-r1` and the hosted runs at this head.
- Prior public review findings on PR #17: none. At this head the PR has no reviews, no review comments and no findings comments. Nothing needed to be resolved or retained.

## Verdict summary

The identity rule in `scripts/check_privacy.py` is correct. It accepts exactly two pairs and refuses all 11 mixed or foreign pairs tried. It keeps the one-line message rule and the exact `ae982af` exception. The content scan is unchanged. Hosted CI at the exact head is green for both jobs on both events, with 25 of 25 gates at rc 0, GoogleTest 1.14.0-1 and Clang 18. The RV32 ELF images are byte-identical to the base.

The verdict is NEGATIVE because two MINOR findings are open:

- **F1 (Tests, Robustness):** the new selftest does not catch the regression this change most needs to prevent. Planted faults that accept a different account's noreply address, a reversed pair or a case-varied address, or that drop the one-line rule for the web-flow pair, pass `--selftest`. They also pass the real-history gate.
- **F2 (Docs, Conformance):** `docs/IMPORT.md` still says every new commit must use the holder identity, which contradicts the rule the PR adds. One sentence also lost its antecedent.

## Findings

### F1: MINOR. Lenses: Tests, Robustness

- **Where:** `scripts/check_privacy.py:28-34` (selftest cases); `docs/VERIFICATION.md:40` (acceptance "other identity pairs fail"); `scripts/validate.py:66`.
- **Authority:**
  - Review focus item (2): the selftest controls must be meaningful, and a foreign identity such as a different noreply account must not get through.
  - CONTRIBUTING.md: "A regression needs a failing assertion and a runnable planted defect."
  - VERIFICATION.md:40 says other identity pairs fail.
  - PR body and IMPORT.md:135 say the web-flow pair is accepted "still with a one-line message".
- **Evidence:** `receipts/mutant-probes.tsv` (script `scripts/mutant_probes.py`). The table below lists planted faults in a disposable copy at the exact head. "Missed" means rc 0 with the fault planted.

  | Planted fault | `--selftest` | Real-history gate | Bad synthetic commit admitted |
  |---|---|---|---|
  | Accept any `@users.noreply.github.com` author with the GitHub committer | missed | missed | Foreign noreply account; case variant |
  | Order-insensitive pair | missed | missed | Reversed pair (GitHub author, noreply committer) |
  | Case-insensitive pair | missed | missed | Case-varied noreply address |
  | Web-flow pair exempt from the one-line rule (two variants) | missed | missed | Web-flow commit with a body |
  | Committer-only, author-only or accept-everything rule | caught (rc 1) | missed | – |
  | `main()` keeps the old holder-only check | missed | caught (rc 1) | – |

  The unmutated gate refuses all five synthetic bad commits (control row, rc 1). The six controls test `identity_ok()` alone. They contain no other noreply account, no reversed pair and no message-rule case. The only foreign author is `someone <a@b.c>`, which no plausible widening would accept.
- **Impact:** a later edit could admit another GitHub account's identity, or allow multi-line squash bodies. Neither `--selftest` nor the privacy gate on the published history would show it. The documented acceptance overstates what the controls prove. The current implementation is correct. The defect is the sensitivity of the controls in a privacy gate.
- **Required outcome:** add selftest controls that fail for at least these cases:
  - the holder name with a different account's noreply address and the GitHub committer;
  - the reversed web-flow pair;
  - the account's noreply address with different letter case;
  - a web-flow pair with a two-line message.

  The last control means the selftest must exercise the per-commit check (identity plus message, with the exact `ae982af` exception), not only `identity_ok()`. Update the VERIFICATION.md:40 acceptance text to match.
- **Verification:** rerun `scripts/mutant_probes.py` on a disposable clone of the fixed head (the fix will need its planted-fault anchors updated). Every planted fault in the table must give `--selftest` rc ≠ 0, and the control row must stay rc 0. `validate.py` and hosted CI stay green.

### F2: MINOR. Lenses: Docs, Conformance

- **Where:** `docs/IMPORT.md:136` (in the paragraph at 130-136).
- **Authority:** review focus item (3) says IMPORT.md must describe the rule accurately. The owner rule is that RESIDUE excludes any text that touches a privacy rule.
- **Evidence:**
  - Line 136 still says "Every new commit must use the configured holder identity and one-line subject." Lines 134-135 and `check_privacy.py:25` now accept the web-flow pair on new commits, and every future squash commit on `main` uses it. The privacy-rule statement contradicts itself.
  - Line 136 also opens "It still scans that commit's content…". After the inserted line 135 ("`check_privacy.py --selftest` checks the identity rule."), "It" reads as the selftest, which scans nothing. "That commit" no longer clearly means `ae982af`.
- **Impact:** a reader of the documented privacy rule cannot tell which identities are allowed on new commits. This is prose, but it states a privacy rule, so it is not RESIDUE.
- **Required outcome (example wording):**
  - "The gate still scans every commit's metadata, including that commit, every reachable blob and the current tree."
  - "Commits made outside GitHub must use the configured holder identity and a one-line subject. GitHub squash merges carry the noreply pair above, also with a one-line message."
- **Verification:** read docs/IMPORT.md 130-137 at the fixed head and compare it with `identity_ok()` and `main()`.

### Suggestions (do not affect the verdict)

- **S1 (Robustness):** `check_privacy.py:73` runs the full gate for any argv other than exactly `["--selftest"]`. For example, `--selftst` returns rc 0 from the full gate (`receipts/identity-probes.tsv`, last line). Refuse unknown arguments so that a misspelled caller cannot look like a passing selftest. `validate.py` passes the exact switch today, so this is not a defect.
- **S2 (Robustness, pre-existing, follow-up issue):** the content scan reads `git show --format=%an <%ae>%n%cn <%ce>%n%B` output, not the raw commit object. A commit made with `hash-object --literally` can carry a restricted path in an extra header and after the parsed author email. It passes with either accepted pair: rc 0 for both rows `raw-hidden-path-*`, and the raw object contains the path on 2 lines. The scan code is unchanged by this PR and the case reproduces with the holder pair, so the PR did not introduce it. Suggest a follow-up to scan `git cat-file commit` bytes.
- **S3 (process, owner/manager):** repository settings allow merge commits and rebase merges, and the default squash message is the commit list (`squash_merge_commit_message: COMMIT_MESSAGES`). The gate fails closed on all three defaults, but only after the merge, on `main`:
  - a rebase merge gives the holder author with the GitHub committer, and the gate reports "unexpected identity";
  - the default merge-commit message has two lines;
  - a multi-commit squash body has more than one line.

  Consider restricting merges to squash with a title-only message. Merge commits: a GitHub merge with a one-line message and the web-flow pair passes. That is acceptable, because each side-branch commit is still checked (a foreign side commit is refused) and every reachable blob is still scanned. The default merge message is refused.
- **S4 (Docs):** CHANGELOG.md `Unreleased` lists the gate changes from earlier PRs but has no line for this identity-rule change.

## Lens results and evidence

- **Conformance (UNCLEAN, F2).** Item (1) holds:
  - `identity_ok()` compares the first two formatted lines for exact equality with `[IDENTITY, IDENTITY]` or `WEB_FLOW`.
  - The one-line rule (`check_privacy.py:50`) and the `ae982af` exception (`:15`, `:48`, `:50`) are unchanged apart from the identity call.
  - The scan of metadata, every reachable blob and the current tree (`:52-67`) is byte-unchanged in the diff.

  Probes on 15 single-commit synthetic histories (`receipts/identity-probes.tsv`):
  - Accepted: holder pair; web-flow pair.
  - Refused for the message rule: web-flow with a commit-list body or a co-author trailer.
  - Refused for identity (11):
    - noreply author with holder committer;
    - holder author with GitHub committer (rebase-merge shape);
    - a different account's noreply address, with the holder name or another name;
    - the same noreply address under another name;
    - a lower-case variant;
    - the legacy noreply form;
    - the GitHub committer with another email;
    - the reversed pair;
    - noreply in both roles;
    - GitHub in both roles.
  - A foreign pair rewritten by an untracked `.mailmap` with `log.mailmap=true` is still refused, because `%an`/`%ae` are raw.
  - The base gate fails at `18d73783` with "unexpected identity" (`receipts/base-gate.txt`; hosted base run 37928415766 failed only `privacy`).

  The hard-coded noreply address is required for exactness. It is already public in the metadata of `ae982af` and `18d73783`, and IMPORT.md does not repeat it. Item (3) fails on IMPORT.md:136 (F2). VERIFICATION.md:40 is accurate for the rule but overstates the controls (F1).
- **RTL (CLEAN).** The repository and the diff contain no HDL. For the hardware-target view, the bare-metal RV32 job passed at the exact head on both events. Its Debug and Release ELF and core-object hashes equal those of the base run (`receipts/rv32-base-vs-head.txt`). `scripts/baremetal.py` reads none of the changed files.
- **Robustness (UNCLEAN, F1).** Planted-fault sensitivity is above. Merge, rebase and mailmap behaviour fail closed. S1 and S2 are recorded as suggestions.
- **Tests (UNCLEAN, F1).**
  - The six controls pass at the head, locally and hosted ("privacy selftest: 6 identity controls pass").
  - `validate.py:66` runs them before `privacy` in the fail-fast group, and the hosted `gates.json` lists `privacy-selftest` rc 0.
  - The controls miss four plausible widenings (F1).
- **Docs (UNCLEAN, F2).** The VERIFICATION.md row and the IMPORT.md lines 134-135 are accurate. Line 136 is not. S4 notes the missing changelog line.

### Gate execution (source head)

- **Hosted CI at exact head (both jobs, both events):**
  - Pull-request run 37932096604 and push run 37932088705: `quality` success and `bare-metal` success.
  - Each `quality` artifact `gates.json` has 25 of 25 gates at rc 0, including `privacy-selftest`, `privacy` and `graphs`.
  - Job logs show checkout of `61fb7c9…` and install of `libgtest-dev 1.14.0-1`, `googletest 1.14.0-1`, `clang-tidy 1:18.0` and `cppcheck 2.13.0`. The comment and assertion lexing gates require `clang version 18.` and passed.
  - Receipts are in `receipts/hosted/`.
- **Author receipts (`deca7adc…/review-evidence/tsnpriv-r1`):** 24 of 24 gates at rc 0, without `--graphs`. The published `change.diff` is byte-identical to the head diff.
- **Local reviewer run** (`scripts/run_validate.sh`; disposable clone at the exact head; Clang 18.1.8 release; GoogleTest 1.14.0 built from `f8d7d77c`; `--jobs 16 --graphs`):
  - 23 of 24 recorded gates are rc 0, including `privacy-selftest`, `privacy`, `gcc-test`, `coverage`, `mutation`, `mutation-controls`, `static-analysis` and `graphs`.
  - `clang-sanitizers-build` is rc 2 because the release Clang 18 cannot parse this host's GCC 16 libstdc++ headers (`stl_iterator.h` incomplete type). This is a host mismatch and unrelated to the diff. `clang-sanitizers-test` was therefore not reached in that run.
  - The reviewer re-ran that configuration's configure, build and test steps (`scripts/run_clang18_libcxx.sh`) with Clang 18.1.8, its libc++ and GoogleTest 1.14.0 built against libc++, with `-fsanitize=address,undefined` and the runner's ASAN/UBSAN options. All three steps were rc 0 and 7/7 ctest passed (`receipts/validate/clang18-libcxx-summary.txt`).
  - Local GCC 16 and cppcheck 2.22 differ from the pinned hosted image. The hosted run remains the pinned reference.
- **Clone integrity after probes** (`receipts/clone-integrity.txt`): HEAD and tree are exact. Status shows no entries, including ignored files. The index equals the HEAD tree in mode, blob and path. The work-tree blob bytes equal HEAD. The tree has no gitlinks (no submodules), and the privacy gate is rc 0 in the review clone.

## Reviewer-owned ledger

| Lens | Result | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | UNCLEAN (F2) | check_privacy.py:15-73 vs focus items (1) and (3); 15 single-commit, 3 merge and 1 mailmap synthetic histories; base gate failure | R562-1 | 61fb7c9a523b89cb96d493c5baf9f7f866ebed85 |
| RTL | CLEAN | No HDL in tree or diff; hosted bare-metal jobs; RV32 ELF and object hashes equal to base | R562-1 | 61fb7c9a523b89cb96d493c5baf9f7f866ebed85 |
| Robustness | UNCLEAN (F1) | 10 planted-fault rows × 7 detectors; merge, rebase and mailmap probes; raw-header probe; argv probe | R562-1 | 61fb7c9a523b89cb96d493c5baf9f7f866ebed85 |
| Tests | UNCLEAN (F1) | `--selftest` cases; validate.py:66 ordering; hosted 25/25 gates; local 23/24 plus libc++ sanitizer rerun; author 24/24 | R562-1 | 61fb7c9a523b89cb96d493c5baf9f7f866ebed85 |
| Docs | UNCLEAN (F2) | IMPORT.md:130-136; VERIFICATION.md:39-40; PR body; CHANGELOG.md; CONTRIBUTING.md | R562-1 | 61fb7c9a523b89cb96d493c5baf9f7f866ebed85 |

## Real limits

- No manager source bank exists at this head, and none is claimed or inferred. Source-head execution evidence is the author's published receipts, the hosted runs at this head and this reviewer's local runs.
- The local full run used the release Clang 18.1.8 build and GoogleTest 1.14.0 built from source. The Clang sanitizer configuration needed libc++ on this host, and the local GCC and cppcheck versions differ from the pinned hosted image.
- The bare-metal job was not run locally. Coverage comes from hosted execution at the exact head plus ELF hash identity with the base.
- GitHub merge behaviour was modelled with synthetic commits (`commit-tree`), not with a real hosted merge.
- Physical calibration was NOT RUN. Hardware was not used, and skipped contexts are not hardware proof.
- The final current-dev merge candidate (source base `18d73783…`, live dev `5603c353…`) was not built or judged here.

## Pending manager duties

- Build and validate the current-dev merge candidate (builder and native banks) at the merge turn and link its receipts.
- Own hosted and act acceptance.
- Route F1 and F2 to the author. After the fix, re-review at the new head with `scripts/mutant_probes.py` and the IMPORT.md check.
- Decide on S2 (follow-up issue) and S3 (repository merge settings, an owner action).

R562-1 FINISHED
