[R562] POSITIVE - exact head b7c6b7ba0007aaa5791df68d30296423127b003e

# R562-2 internal independent review: tsn-c-stack PR #17 (blocker for issue #14)

- Head `b7c6b7ba0007aaa5791df68d30296423127b003e`, tree `611e16d1d01f6fe901ceb2eb0c07b7be4acaa284`, base `18d737832c376f32660eb21fe2796e0b611507e3`.
- Delta under review: `61fb7c9..b7c6b7b`, two one-line commits made with the holder identity.
  - `738b131` changes `docs/IMPORT.md`.
  - `b7c6b7b` changes `scripts/check_privacy.py`, `docs/VERIFICATION.md` and `CHANGELOG.md`.
  - I also read the full base..head diff (5 files, +50 −6).
- [Public review start](https://github.com/kebag-logic/tsn-c-stack/pull/17#issuecomment-6081468568).
- Reconstruction order:
  1. CONTRIBUTING.md (this head has no AGENTS.md), README.md, docs/VERIFICATION.md and docs/IMPORT.md.
  2. The issue #14 body, the manager assignment, the author STOP and the manager ruling.
  3. The PR #17 body.
  4. The diff and the history, including raw commit identities.
  5. The public evidence at `5f9b951b…/review-evidence/tsnpriv-r1`: the author HANDOFF for round 2 and the `validate-r2` receipts.
  6. The hosted runs at this head.
- I wrote my own verdict and ledger (`receipts/independent-verdict.md`) before I read the prior R562-1 and R563-1 reports.

## Verdict summary

All three prior MINOR findings are resolved at this head. Suggestions S1 and S4 are adopted in the tree, and S3 is applied in the repository settings. I found no new MINOR, MAJOR or BLOCKER defect. This round records one RESIDUE item (the stale PR body) and four suggestions. All five lenses are CLEAN.

- `commit_errors()` (`scripts/check_privacy.py:28-34`) holds the full per-commit check: identity pair, one-line message and the exact `ae982af` exception. `main()` calls it at `:71`.
- `--selftest` (`:37-58`) runs 11 controls through `commit_errors()`. All 11 pass, locally and on the hosted run.
- Each of R562-1's 9 planted faults makes `--selftest` return rc 1. The unmutated control returns rc 0.
- Unknown arguments are refused with rc 1 (`:93-94`).
- The repository now allows only squash merges, with the PR title as subject and a blank body.
- Hosted CI at this head:
  - Push run: both jobs succeeded, with 25 of 25 gates at rc 0.
  - Pull-request run: `quality` succeeded. `bare-metal` was cancelled by its 20-minute timeout while apt was still downloading packages, before the RV32 step ran (see Real limits).

## Prior public findings: status at this head

| ID | Prior severity | Status | Evidence at `b7c6b7b` |
|---|---|---|---|
| R562-1-F1 (Tests, Robustness): the selftest missed plausible widenings | MINOR | **RESOLVED** | `check_privacy.py:37-58` runs `commit_errors()` with the controls listed below this table. All 9 R562-1 faults are caught (see Tests). |
| R562-1-F2 (Docs, Conformance): IMPORT.md contradicted the rule, and "It" had lost its antecedent | MINOR | **RESOLVED** | `docs/IMPORT.md:133` says the gate "exempts only that exact commit". Line 134 follows directly: "It still scans that commit's content and every reachable blob." Lines 136-137 now name both pairs, each with a one-line subject: "the configured holder identity as author and committer, or that hosted squash pair". No line still states a holder-only rule. |
| R563-1-F1 (Conformance, Docs): IMPORT.md:136 contradicted the policy | MINOR | **RESOLVED** | Line 136 now reads exactly as that finding proposed: "Every new commit must use one of these two identity pairs and a one-line subject". Line 137 lists the two pairs. The content-scan sentence and the exact exception are unchanged. |
| R562-1-S1: refuse unknown arguments | SUGGESTION | **ADOPTED, verified** | `--selftst` and `--bogus` print `usage: check_privacy.py [--selftest]` and return rc 1 (`receipts/identity-probes-r2.tsv`, `receipts/clone-integrity.txt`). In R562-1, a misspelled switch ran the full gate and returned rc 0. |
| R562-1-S2: scan raw commit objects | SUGGESTION | **DEFERRED** to the residue checklist by scope decision. The gap still reproduces. | The `raw-hidden-path-holder` and `raw-hidden-path-webflow` probes both return rc 0, and each raw object has the path on 2 lines. The scan code is unchanged by this PR, and the holder pair behaves the same way. |
| R562-1-S3: squash merges only, title-only message | SUGGESTION | **APPLIED** (repository setting) | `receipts/repo-settings.txt`: `allow_squash_merge: True`, `allow_merge_commit: False`, `allow_rebase_merge: False`, `squash_merge_commit_title: PR_TITLE`, `squash_merge_commit_message: BLANK`, `web_commit_signoff_required: False`. |
| R562-1-S4: changelog line | SUGGESTION | **ADOPTED** | `CHANGELOG.md:5`. |

The R562-1-F1 fix adds these selftest controls:

- must fail: another account's noreply address;
- must fail: the reversed pair;
- must fail: a case variant of the noreply address;
- must fail: the holder author with the GitHub committer;
- must fail: the noreply author with the holder committer;
- must fail: a multi-line message on the web-flow pair;
- must fail: a multi-line message on the holder pair;
- must pass: the exact owner squash.

## Findings (this round)

### R562-2-R1: RESIDUE. Lens: Docs

- **Where:** the PR #17 body, second bullet: "`check_privacy.py --selftest` checks the rule with six identity controls: both accepted pairs pass, mixed or foreign pairs fail."
- **Evidence:**
  - At this head the selftest prints "privacy selftest: 11 commit controls pass" (hosted `receipts/hosted/37934329322-privacy-selftest.log`, local `receipts/validate/validate-privacy-selftest.log`).
  - It also covers the multi-line message cases and the exact owner squash.
  - The body does not mention that unknown arguments are refused.
- **Why RESIDUE:**
  - The body under-describes a test that is stronger than it claims.
  - The privacy rule the body states is correct: "accepts exactly that identity pair, still with a one-line message, beside the holder identity".
  - With the BLANK squash-body setting, the PR body never enters history.
  - Fixing it changes no code, test, figure or verdict.
- **Exact fix:** replace the bullet with: "`check_privacy.py --selftest` runs the per-commit check against eleven controls. The holder pair, the GitHub squash pair and the exact owner squash pass. Mixed, reversed, case-varied and other-account pairs fail, and so does a multi-line message on either pair. Unknown arguments are refused. `validate.py` runs it."

### Suggestions (do not affect the verdict)

- **S1 (Tests, Robustness): prove the `ae982af` exception is exact.**
  - Evidence: the fault `owner-exception-by-prefix` exempts every commit that starts with the same first character as `ae982af`. It passes `--selftest`, the published-history gate and all 7 synthetic bad commits (`receipts/mutant-probes-r2.tsv`).
  - Current code: the exception is exact by inspection, a full 40-hex string comparison at `:30` and `:32`.
  - Fix: add a control that gives the owner-squash metadata (foreign identity, multi-line message) a different commit id, for example one sharing the 7-character prefix, and requires a failure.
- **S2 (Tests): add a zero-line message control.**
  - Evidence: the fault `accept-empty-message` (`!= 1` changed to `> 1`) survives every detector.
  - Impact is low: git refuses empty messages by default, and GitHub squash commits always carry the PR title.
- **S3 (Tests, Robustness): drive the wiring in `main()`.**
  - Evidence: the faults `main-skips-commit-errors` and `main-uses-identity-only` survive both `--selftest` and the published-history gate. Only the reviewer's synthetic commits catch them.
  - Fix: run `main()` once against a throw-away repository with one bad commit. This could share work with the deferred raw-object scan (R562-1-S2).
- **S4 (style): two layout points in `scripts/check_privacy.py`.**
  - Line 59 has one blank line before `def scan`. Two are used elsewhere in the file.
  - `import sys` is inside the `__main__` block.
  - CODING_STANDARD.md has no Python rule, so this is style only.

## Lens results and evidence

### Conformance: CLEAN

- **Item (1), the import guide (IMPORT.md:128-138).**
  - Lines 136-137 name both accepted pairs, each with a one-line subject.
  - The content-scan sentence (`:134`) directly follows the exact `ae982af` exception (`:133`).
  - Nothing in IMPORT.md, VERIFICATION.md, CONTRIBUTING.md or CHANGELOG.md contradicts this.
  - CONTRIBUTING.md agrees with the gate and with the BLANK squash setting: "Use one-line commit subjects. Use no body, trailers or attribution footer."
- **Item (2), the predicate (`check_privacy.py:24-34`).**
  - The first two formatted lines must equal `[IDENTITY, IDENTITY]` or `WEB_FLOW` exactly.
  - Every commit except the exact `ae982af` must have exactly one non-blank message line.
  - `main()` uses `commit_errors()` at `:71`. Apart from that call, the scan code is byte-unchanged from the base.
- **Synthetic identity probes.** 21 synthetic histories were built at this head (`receipts/identity-probes-r2.tsv`, `scripts/identity_probes_r2.sh`):
  - Accepted: the holder pair; the web-flow pair; a one-line web-flow merge whose side commit uses the holder pair.
  - Refused by the message rule: a commit-list body, a co-author trailer and the default merge message.
  - Refused by the identity rule: 11 mixed or foreign pairs, a foreign side commit, and a foreign pair masked by `.mailmap` with `log.mailmap=true`.
- **Squash preview.**
  - I modelled the squash commit GitHub would create for this PR under the current settings. It has the PR title plus ` (#17)`, a blank body, the web-flow pair and parent `18d73783`.
  - The gate passes it: 4 commits, rc 0 (`receipts/squash-preview.txt`, `scripts/squash_preview.sh`).
  - This is a model, not a hosted merge.
- **The hard-coded noreply address.**
  - Exact matching requires it.
  - It is already public in the metadata of `ae982af` and `18d73783`, and every future squash commit will carry it.
  - The docs call it "the account's noreply author" and do not repeat the address.
- **Item (3), VERIFICATION.md and CHANGELOG.**
  - VERIFICATION.md:40 names exactly the passing and failing control classes present in `selftest()`.
  - CHANGELOG.md:5 states the accepted pair and the one-line rule it keeps.
  - Both are accurate.

### RTL: CLEAN

- The repository and the diff contain no HDL, so a scoped simulator run does not apply.
- For the hardware-target view, the hosted push run's `bare-metal` job passed at the exact head.
- Its Debug and Release ELF and core-object hashes equal those R562-1 recorded at `61fb7c9`. R562-1 showed that those equal the base (`receipts/rv32-prev-vs-head.txt`).
- `scripts/baremetal.py` reads none of the changed files.

### Robustness: CLEAN

- **Planted faults.** `scripts/mutant_probes_r2.py` ran on a disposable clone at the exact head (`receipts/mutant-probes-r2.tsv`). It planted 18 faults plus an unmutated control. Ten detectors checked each fault: `--selftest`, the unknown-argument check, the published-history gate and 7 synthetic bad commits.
  - `--selftest` catches 12 faults: R562-1's 9, plus `holder-exempt-from-one-line-rule`, `one-line-rule-dropped` and `owner-exception-dropped`.
  - The synthetic-commit or argument detectors catch 3 more: `main-skips-commit-errors`, `main-uses-identity-only` and `unknown-args-run-main` (S3).
  - No detector catches `owner-exception-by-prefix` or `accept-empty-message` (S1 and S2).
  - `selftest-always-passes` also survives. Every selftest has this self-referential limit, so it is not a defect.
  - The run ends with `restored: True`.
- **Fail-closed behaviour.**
  - Unknown arguments are refused.
  - A `.mailmap` mask is refused.
  - The gate refuses the default merge message, the rebase identity pair and a multi-commit squash body. The repository settings now also prevent those merge forms.
- **Deferred gap.** The raw-object scan gap (R562-1-S2) still reproduces. It predates this PR and is deferred by scope decision.

### Tests: CLEAN

- **Selftest coverage.** `--selftest` runs `commit_errors()` with 11 controls (`:39-51`), covering every case this round requires:
  - Pass: the holder pair, the web-flow pair and the exact owner squash.
  - Fail: a mixed pair, the holder author with the GitHub committer, another account's noreply address, the reversed pair, a case variant, a multi-line message on either pair, and a foreign pair.
- **R562-1's `mutant_probes.py`, run unchanged** on a disposable copy (`receipts/mutant-probes-r562-1-unchanged.tsv`):
  - All 9 planted faults make `--selftest` return rc 1. The control returns rc 0. This matches the author's HANDOFF claim.
  - Caveat: the unchanged script reads the gate file before it checks out its pinned `61fb7c9`. It therefore plants faults into this head's gate code, but runs its history and synthetic columns against `61fb7c9`, and it prints `restored: False`.
  - The `--selftest` column does not depend on history, so the claim stands.
  - The adapted run at the exact head (Robustness) gives the same 9 catches and restores cleanly.
- **Validator wiring.** `validate.py:66` runs `privacy-selftest` before `privacy` in the fail-fast group.
- **Hosted push run 37934329322** (checkout of `b7c6b7b…`):
  - `gates.json` has 25 of 25 gates at rc 0, including `privacy-selftest`, `privacy` and `graphs`.
  - The job log shows `libgtest-dev`/`libgmock-dev 1.14.0-1` and `clang-18 1:18.1.3` (`receipts/hosted/`).
- **Hosted pull-request run 37934336629:** `quality` succeeded.
- **Author receipts:** `validate-r2` shows 24 of 24 gates at rc 0, without `--graphs`.
- **Local reviewer run** (`scripts/run_validate_r2.sh`; Clang 18.1.8 release; GoogleTest 1.14.0 built from `f8d7d77c`; `--jobs 16 --graphs`):
  - 23 of 24 recorded gates returned rc 0, including `privacy-selftest`, `privacy`, `gcc-test`, `coverage`, `mutation`, `mutation-controls`, `static-analysis` and `graphs`.
  - `clang-sanitizers-build` returned rc 2: the release Clang 18 cannot parse this host's GCC 16 libstdc++ headers. R562-1 hit the same host mismatch. It is unrelated to the diff (`receipts/validate/clang-sanitizers-build-host-header-excerpt.txt`).
  - I re-ran that configuration with Clang 18.1.8, its own libc++ and a libc++ build of GoogleTest 1.14.0, with the address and undefined-behaviour sanitizers. Configure, build and test all returned rc 0, and ctest passed 7 of 7 (`receipts/validate/clang18-libcxx-summary.txt`).
  - The validator's peak resident memory was 0.44 GB. Wall time was 1 min 51 s.

### Docs: CLEAN

- IMPORT.md:128-138, VERIFICATION.md:39-40 and CHANGELOG.md:5 are accurate and consistent with the code (see Conformance).
- IMPORT.md:138 says the selftest "checks the identity rule". It also checks the message rule and the exception, so this understates it. It is not wrong.
- The only stale text is the PR body (R562-2-R1, RESIDUE).

## Reviewer-owned ledger

| Lens | Result | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | IMPORT.md:128-138; check_privacy.py:15-95; VERIFICATION.md:39-40; CHANGELOG.md:5; CONTRIBUTING.md; repository merge settings; 21 synthetic identity histories; squash preview | R562-2 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| RTL | CLEAN | No HDL in the tree or diff; hosted push `bare-metal` success; RV32 ELF and object hashes equal to the prior head and the base | R562-2 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Robustness | CLEAN | 18 planted faults plus control, 10 detectors each; argument refusal; mailmap, merge and rebase shapes; raw-object probe (deferred S2) | R562-2 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Tests | CLEAN | 11 selftest controls; R562-1 mutant script run unchanged (9/9) and adapted; validate.py:66; hosted 25/25; local 23/24 plus libc++ sanitizer rerun 7/7; author 24/24 | R562-2 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Docs | CLEAN (R1 RESIDUE carried) | IMPORT.md, VERIFICATION.md, CHANGELOG.md, CONTRIBUTING.md, PR body, author HANDOFF | R562-2 | b7c6b7ba0007aaa5791df68d30296423127b003e |

## Real limits

- **No manager source bank** exists at this head, and I claim or infer none. Source-head execution evidence is the author's published gate receipts, the hosted runs at this head and my local runs.
- **Pull-request `bare-metal` context** (run 37934336629, job 113832507547):
  - It was cancelled after 20 min 16 s inside the "Install RV32 dependencies" step. The last line before cancellation was the download of `qemu-system-misc`.
  - "Validate the freestanding cores" was skipped, so no RV32 validation ran in that context.
  - `gh pr checks` reports it as `fail`. It was a stall in the hosted infrastructure, not a failure of executed checks.
  - The push-event `bare-metal` job for the same SHA ran and passed in 57 s.
  - Receipts: `receipts/hosted/37934336629-bare-metal-job.json` and `receipts/hosted/37934336629-bare-metal-install-tail.txt`.
- **Local toolchain.**
  - The local run used the release Clang 18.1.8 and GoogleTest 1.14.0 built from source.
  - The sanitizer configuration needed libc++ on this host.
  - Local GCC 16 and cppcheck 2.22 differ from the pinned hosted image, so the hosted run remains the pinned reference.
- **Bare-metal coverage.** I did not run the bare-metal job locally. That coverage comes from the hosted push run and the ELF hash identity.
- **Modelled merges.** I modelled GitHub merge and squash behaviour with `commit-tree`, not with a real hosted merge.
- **Hardware.** Physical calibration NOT RUN. No hardware was used, and skipped contexts are not hardware proof.
- **Merge candidate.** I did not build or judge the final current-dev merge candidate (source base `18d73783…`, live dev `5603c353…`).
- **Redaction.** Host paths in the published receipts are replaced with `<packet>`, `<scratch>` and `<review-clone>`.

## Pending manager duties

- Re-run the cancelled pull-request `bare-metal` job at `b7c6b7b`, and confirm that it runs and passes, before hosted acceptance. The manager owns hosted and act acceptance.
- Build and validate the current-dev merge candidate (builder and native banks) at the merge turn, and link its receipts on the PR.
- Carry R562-2-R1 (PR body wording) and R562-1-S2 (raw commit-object scan) to the residue checklist.
- Decide on S1-S4.
- Obtain the second independent positive review for this head before merge.

## Clone integrity

`receipts/clone-integrity.txt`, produced by `scripts/clone_integrity.sh`, shows the review clone is unchanged:

- HEAD and tree are the exact values above.
- `status --porcelain --ignored` is empty.
- The index tree equals the HEAD tree.
- All 74 tracked entries match HEAD in index oid, raw work-tree bytes and mode.
- The tree has no gitlinks and no `.gitmodules`, so there are no submodule gitlinks to check.
- All probes ran in disposable clones under `scratch/`.

R562-2 FINISHED
