[R563] POSITIVE - exact head b7c6b7ba0007aaa5791df68d30296423127b003e

R563-2-F1 is **RESOLVED**. The current PR body correctly reports eleven commit controls and identifies the complete identity/message check. Earlier substantive findings remain resolved. No open BLOCKER, MAJOR or MINOR artifact finding was identified. One incomplete prose enumeration is RESIDUE; all five artifact lenses are CLEAN.

Tree: `611e16d1d01f6fe901ceb2eb0c07b7be4acaa284`. Source base: `18d737832c376f32660eb21fe2796e0b611507e3`. [Public review start](https://github.com/kebag-logic/tsn-c-stack/pull/17#issuecomment-6081888966). The [PR body](receipts/current-pr.json) and head remained unchanged at the [final capture](receipts/final-public-state.json).

**Review-process limitation:** the independent diff assessment was recorded before consulting prior findings, but fetching public discussion also displayed complete earlier review reports before this verdict and ledger were written. The requested report-isolation order was not fully preserved. This limitation accompanies the verdict; the manager must determine whether a fresh cleared-context review is needed for the required independent approval. No private author packet, private management material or other checkout was inspected.

**Scope and authorities.** The supplied repository instructions, CONTRIBUTING.md, README.md, coding/verification/import documents, requirements, architecture and port contract were examined. The [issue body](https://github.com/kebag-logic/tsn-c-stack/issues/14) freezes six acceptance items for the separate requirements-port lane. The [assignment](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6080704899), [base failure](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081068576) and [manager ruling](https://github.com/kebag-logic/tsn-c-stack/issues/14#issuecomment-6081168071) establish PR #17 as its privacy-gate prerequisite. PR #17 does not perform that requirements port.

The [owner squash decision](https://github.com/kebag-logic/milan-fpga/issues/697#issuecomment-6074811248) fixes the historical exception. Local requirement/interface authorities were read before the diff; upstream requirements at `5603c353137e90c1fa95429f6d00ef7a2298d9ee` and the public Mark II issue body were additionally checked for scope. This delta introduces no protocol, interface or standard-clause claim. The complete [diff](receipts/diff.txt) and [three-commit history](receipts/history.txt) were examined before executable evidence. The [independent static assessment](receipts/independent-diff-pass.txt) records that pass.

**Current PR claim audit.** Code locations below refer to the exact reviewed head.

| PR claim | Artifact-specific evidence | Assessment |
|---|---|---|
| Base fails on the later squash identity | Base gate code run against reviewed history reports `18d73783: unexpected identity`; head gate passes. [Receipt](receipts/focused/base-code-on-head-history.log). This is not a separate base-checkout bank. | Matches |
| Exactly two accepted pairs | check_privacy.py:15–25 uses ordered, case-sensitive equality: holder/holder or exact account-author/GitHub-committer. Independent literal identities drive 324 pair/message combinations. | Matches |
| One-line message rule | :32–33 requires exactly one nonblank message line for either pair. Empty/multiline messages fail. Blank padding retains the base behavior. The adjacent exception statement qualifies the general rule. | Matches |
| Exact `ae982af` exception; unchanged content scan | Full 40-character comparisons at :30,32. Metadata, historical blobs and current files remain scanned at :71–87. Four near-match IDs fail; restricted metadata/history/current-content fixtures fail even for the exempt ID. Structural comparison confirms unchanged scan patterns and logic. | Matches |
| `commit_errors()` holds the per-commit check | :28–34 holds identity/message validation and its exception; main():71 calls it. Content scanning remains the separate call at :72. | Matches in the identity/message context |
| Eleven commit controls and pass/fail split | :39–50 contains **3 expected passes and 8 expected refusals**. Local and both hosted selftests report eleven successful control outcomes. The PR names all three passes but omits one refusal from its enumeration. | Count correct; R563-3-R1 below |
| Validator runs selftest; unknown arguments fail | validate.py:66 and check_privacy.py:93–95. Five invalid argument vectors fail. A simulated selftest failure makes validation fail before build campaigns. | Matches |
| Squash-only setting, title subject, blank body | [Live settings](receipts/repo-settings.json): squash enabled, merge/rebase disabled, `PR_TITLE`, `BLANK`. The gate itself does not enforce commit topology. | Matches |
| All 24 validation gates pass with specified dependencies | Published round-two table has 24/24 zero codes without graphs. Orchestration confirms 24 without graphs, 25 with graphs. Both hosted quality tables have 25/25 zero codes; hosted package logs show GoogleTest/GMock 1.14.0-1 and Clang 18.1.3. | Matches |
| Nine original faults fail selftest; control passes | Exact original nine substitutions replayed on disposable exact-head gate copies: nine explicit selftest failures; control rc 0. Failure logs name controls, with no syntax errors or crashes. | Matches |
| Bare-metal unaffected; docs describe the rule | Only three prose files and two privacy/validation scripts differ. Core/header bytes, RV32 examples, build configuration, baremetal.py and workflow are unchanged. IMPORT.md:133–138, VERIFICATION.md:39–40 and CHANGELOG.md:5 agree with the rule. | Matches; hosted PR execution limit below |

The three expected passes are holder/holder, hosted squash pair, and exact owner squash. The eight expected refusals are noreply author/holder committer, holder author/GitHub committer, another noreply account, reversed pair, case variant, multiline hosted pair, multiline holder pair, and generic foreign pair. Expected refusal is a successful control outcome.

**R563-3-R1 — RESIDUE — OPEN. All attributable lenses: Docs, Tests.**

- **Artifact:** [PR #17 body](https://github.com/kebag-logic/tsn-c-stack/pull/17), `fail:` list under eleven controls; [snapshot](receipts/current-pr.json).
- **Authority/evidence:** check_privacy.py:50 contains the additional `foreign` refusal. The prose enumerates seven of eight refusals while correctly stating eleven total controls. [Mutation receipt](receipts/focused/mutant-6.log) also identifies `foreign`.
- **Impact/classification:** the list under-describes existing tests. The stated count, measured results, test behavior and privacy rule remain correct. Adding the omitted case name changes no measurement, figure, verdict, test, generated artifact, conformance/clause claim or privacy rule. Under the supplied owner rule this is wording-only RESIDUE and leaves both lenses CLEAN.
- **Required outcome / exact fix:** end the list with “a case variant, a multi-line message on either accepted pair, and a foreign pair.”
- **Verification:** reconcile the enumeration with :39–50: three expected passes and eight expected refusals. No source change is required.

**Prior findings and suggestions.** Public submitted reviews and inline review comments are empty. Earlier findings are in the public issue-comment discussion: [inventory](receipts/pr-discussion-inventory.json).

| Prior ID | Severity; all attributable lenses | Disposition and evidence at this head |
|---|---|---|
| R563-2-F1 | MINOR; Docs, Tests | **RESOLVED.** “Six identity controls” became eleven commit controls; message controls and exact exception are described. R563-3-R1 is a separate enumeration residue. |
| R563-1-F1 | MINOR; Conformance, Docs | **RESOLVED.** IMPORT.md:136–137 permits either complete pair plus one-line subject. Both acceptance controls and real scan pass. |
| R562-1-F1 | MINOR; Tests, Robustness | **RESOLVED.** Selftest exercises commit_errors(); other-account, reversed, case-varied and multiline controls are present. All nine original faults are caught. |
| R562-1-F2 | MINOR; Docs, Conformance | **RESOLVED.** IMPORT.md:133–138 removes the holder-only contradiction and restores the scanning sentence's antecedent. |
| R562-1-S1 | SUGGESTION; Robustness | **ADOPTED.** Unknown, misspelled, repeated and combined arguments are refused; local subprocess receipts confirm it. |
| R562-1-S2 | SUGGESTION; Robustness | **RETAINED / deferred.** :69 scans formatted fields rather than every raw commit header. Published handoff explicitly defers raw-object scanning. No broader raw-header claim is made here. |
| R562-1-S3 | SUGGESTION; Conformance, Robustness / merge process | **ADOPTED.** Live settings confirm squash only, PR-title subject and blank body. |
| R562-1-S4 | SUGGESTION; Docs | **ADOPTED.** CHANGELOG.md:5 describes the pair and preserved message rule. |
| R562-2-R1 | RESIDUE; Docs | **RESOLVED as originally stated.** Stale six-control wording and omitted argument refusal were corrected. Carry the narrower R563-3-R1 now. |
| R562-2-S1 | SUGGESTION; Tests, Robustness | **RETAINED.** Shipped selftest has no near-match exception-ID control. Current code is exact; four independent near-match probes pass here. |
| R562-2-S2 | SUGGESTION; Tests | **RETAINED.** No shipped zero-line message control. Current predicate rejects it; independently checked here. |
| R562-2-S3 | SUGGESTION; Tests, Robustness | **RETAINED.** Shipped selftest calls commit_errors(), not main(). This round's mocked-history fixtures verify current wiring; a permanent integration control remains optional. |
| R562-2-S4 | SUGGESTION; code style | **RETAINED.** Blank-line/import placement is unchanged; no applicable Python style requirement was identified. |

**Executed evidence.** [Replay instructions](REPLAY.md), [focused script](scripts/focused_review.py) and [summary](receipts/focused/summary.log) cover local selftest, arguments, 324 pair/message combinations, four near-exception IDs, nine metadata/content fixtures, real scan, base-rule reproduction and validator failure/dispatch fixtures. The real head scan passes **6 commits, 122 historical blobs, 74 current files**. Validator fixtures are orchestration tests, not compiler-bank execution.

The [original public fault script](receipts/published/reviews/R562-1/scripts/mutant_probes.py) was read as executable evidence. All nine original substitution definitions were reused unchanged. The replay wrapper avoids that script's old-head checkout and synthetic commit creation; actual selftest subprocesses run on disposable exact-head gate copies. [Fault results](receipts/focused/r562-1-mutants.json) and individual logs preserve nine catches and the passing control. Copies were restored; no commits were created.

Five selected files from the specified [published packet](https://github.com/kebag-logic/tsn-c-stack/tree/5f9b951b14fa8c22b03ea9b5cde49ed57033279b/review-evidence/tsnpriv-r1) match its manifest: [verification](receipts/published-verification.json). The author's round-two [handoff](receipts/published/author/HANDOFF.md), [gate table](receipts/published/author/receipts/validate-gates-r2.json) and [log](receipts/published/author/receipts/validate-r2.log) supply source-validation evidence. The historical commit receipt identifies round one and is not represented as a current-head receipt.

Both hosted quality archives and the push RV32 archive match their API SHA-256 digests: [verification](receipts/hosted/archive-verification.json). Both quality runs show seven passing test executables per native configuration, 100% lines/branches after existing exclusions, 311 caught plants with zero escapes/errors, and three rendered graphs. Push RV32 results show Debug/Release build, link and smoke execution with no unresolved final symbols.

| Exact-head hosted context | Observed execution |
|---|---|
| [Push quality](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37934329322/job/113832483545) | SUCCESS; 25/25 gates, including privacy and eleven-control selftest |
| [Push bare-metal](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37934329322/job/113832483151) | SUCCESS; Debug/Release smoke checks executed |
| [PR quality](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37934336629/job/113832508812) | SUCCESS; 25/25 gates |
| [PR bare-metal](https://github.com/kebag-logic/tsn-c-stack/actions/runs/37934336629/job/113832507547) | CANCELLED during dependency installation; freestanding validation SKIPPED |

“Both jobs green” is **not true for all current PR checks**. Final [plain output](receipts/pr-checks-final.txt) labels cancelled PR bare-metal `fail`; [structured output](receipts/pr-checks-final-json.txt) reports `CANCELLED`. The command returned zero here, so context states and executed steps govern this assessment. Both jobs are green on the push event. Hosted acceptance remains a manager duty; no rerun or public write was performed.

| lens | CLEAN/UNCLEAN | examined artifacts | covering round | exact head |
|---|---|---|---|---|
| Conformance | CLEAN | Issue #14 scope/ruling; CONTRIBUTING; IMPORT:128–138; check_privacy:15–34,65–95; settings; identity/message/exception fixtures | R563-3 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| RTL | CLEAN | Full diff/inventory: no RTL/constraints or gitlinks; unchanged C/headers, RV32 examples, CMake, baremetal.py and workflow; executed push RV32 receipts | R563-3 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Robustness | CLEAN | Nine original fault substitutions; 324 pair/message checks; near-exception and content fixtures; argument subprocesses; unchanged scanner comparison | R563-3 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Tests | CLEAN | Eleven shipped controls; 9/9 catches; validator fixtures; author 24-gate and hosted 25-gate receipts; native/RV32 executed results; R1 residue | R563-3 | b7c6b7ba0007aaa5791df68d30296423127b003e |
| Docs | CLEAN | README, CONTRIBUTING, requirements/interface authorities, IMPORT, VERIFICATION, CHANGELOG; complete PR claim audit; receipts; R1 residue | R563-3 | b7c6b7ba0007aaa5791df68d30296423127b003e |

**Real limits and pending manager duties.** The review-process limitation near the beginning applies to the whole ledger. Local execution was limited to focused privacy/orchestration probes; full source banks were not rerun. Native/RV32 execution claims rely on inspected public source/hosted receipts. No RTL simulation was needed or run. No parent, protocol-processor, timing-protocol, synthesis or builder banks, container workflow, host workflow selftest, hardware, shared installation, privilege, source fix, commit, push, merge, public write or author contact occurred. Independent probe campaigns were joined by a foreground driver with at most four workers. Disposable files/downloads stayed under scratch/.

There is **no manager source bank at this exact head**, and none is claimed or inferred. Source validation is distinct from the final current-dev merge candidate. The manager owns hosted/local-workflow acceptance, must resolve the cancelled PR bare-metal context, and must validate the final candidate with builder/native banks at the merge turn using source base `18d737832c376f32660eb21fe2796e0b611507e3` and designated live dev `5603c353137e90c1fa95429f6d00ef7a2298d9ee`, then link receipts on the PR. The manager must carry R563-3-R1 and deferred suggestions, determine the independence limitation's disposition, and obtain two independent positive approvals before merge.

Physical calibration **NOT RUN**. Field skips and simulated smoke checks are not hardware proof. Repository publication remains a separate owner action.

[Final integrity](receipts/checkout-integrity.json) verifies exact detached head/tree, all 74 tracked raw blob bytes and executable modes, unchanged original index, clean status including ignored files, no .gitmodules and zero required submodule gitlinks. Generated cache files were removed. Scratch is excluded from publication. [MANIFEST.sha256](MANIFEST.sha256) lists every publishable script and receipt, including REPORT.md. The manager publishes after terminal execution.

R563-3 FINISHED
