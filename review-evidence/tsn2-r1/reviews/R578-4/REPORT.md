[R578] POSITIVE - exact head 0c5ef532cb782f9e7c73855b41c397679d176ea7

# R578-4: internal independent delta review, kebag-logic/tsn-c-stack#2 / PR #20

- **Exact head:** `0c5ef532cb782f9e7c73855b41c397679d176ea7`, tree `7d4a8d904e073167345d3d7eeecf91fee5bec48e`. The PR head ref equals it.
- **Delta reviewed:** `64888e91..0c5ef53`. This is one manager commit, "Separate the mapper plant table from the following prose", with parent `64888e91fa5bc86c6c0e4efbf707fff3174d10e1`.
- **Assignment:** answer R579-3-F1, which is the same defect as R578-3-R3. Earlier rounds stand for unchanged content.
- **Full PR range:** `1a9f651c..0c5ef53`. The content outside this delta was reviewed in rounds 1-3 and was not re-reviewed here.
- **Authorities:**
  - `CONTRIBUTING.md`;
  - issue #2 acceptance item 6 (Docs: `docs/ENTITY_YAML.md`);
  - the GitHub-flavoured Markdown table rule: a table ends only at a blank line or at another block;
  - `MAPPER_PLANTS` in `scripts/entity_selftest.py:453-469`.
- **Missing files:** the repository has no `AGENTS.md` and no `docs/README`. `README.md` and `CONTRIBUTING.md` are the entry points.

## Verdict

POSITIVE. No BLOCKER, MAJOR or MINOR finding is open at this head.

- **The diff is exactly one blank line.**
  - It touches one file, `docs/ENTITY_YAML.md`, and keeps its mode `100644`. The change is 1 insertion and 0 deletions.
  - The inserted line 169 is a single LF byte. It sits between the last plant row (`unknown-key-generic`, line 168) and the prose that follows ("The [quality workflow]…", now line 170).
  - Deleting line 169 from the head blob gives the parent blob byte for byte (`receipts/byte-check.txt`).
  - No other path changed (`receipts/delta-commit.txt`, `receipts/delta.diff`).
- **The table now renders correctly on GitHub.**
  - GitHub renders 13 plant rows at the exact head. They match `MAPPER_PLANTS` in name, order and killer.
  - The four following sentences now render as a paragraph outside the table.
- **R579-3-F1 and R578-3-R3 are RESOLVED.**

My own verdict and ledger were recorded in `receipts/own-pass-verdict.txt` (2026-10-09T20:22:28Z), before I read any prior public review report.

## Findings

No new findings.

## Evidence (exact head, reviewer executions)

| Check | Result | Receipt |
|---|---|---|
| Raw tree delta | `:100644 100644 69c0e98 3928ca1 M docs/ENTITY_YAML.md` only. Numstat `1 0`. No other path changed. | `receipts/delta-commit.txt`, `receipts/delta.diff` |
| Byte check | Head blob is 20547 bytes, parent blob is 20546. Line 169 is `\n`. Head with line 169 deleted is IDENTICAL to the parent. | `receipts/byte-check.txt` |
| Commit form (CONTRIBUTING) | One-line subject. No body, no trailer, no attribution footer. | `receipts/delta-commit.txt` |
| GitHub rendering, head | Read-only GET of the contents API with the `application/vnd.github.html` media type at the exact SHA. One mapper Plant table, 13 body rows, 3 non-empty cells per row, names equal to the source rows. The following prose is a `<p>`. PASS, rc 0. | `receipts/rendered-ENTITY_YAML-0c5ef53….html`, `receipts/render-check-0c5ef53….txt` |
| GitHub rendering, parent (fault control) | 17 body rows: 4 stray prose rows with empty cells. FAIL, rc 1. This reproduces R579-3-F1, so the check detects the defect. | `receipts/rendered-ENTITY_YAML-64888e91….html`, `receipts/render-check-64888e91….txt` |
| Rendered HTML diff, parent to head | The only content change is the 4 stray rows leaving the mapper table and becoming one `<p>`. The other tables keep their row counts (21, 4, 15, header included). The one other changed line is the per-render mermaid `data-identity` UUID. | `receipts/rendered-compare.txt` |
| Rendering stability | A second fetch of the head rendering is identical apart from the mermaid identity. | `receipts/…refetch.html`, `receipts/refetch-compare.txt` |
| **R579-3 `check_render.py` rerun** | Script verified against R579-3's published `MANIFEST.sha256` (git blob `f14e01e7`, sha256 `ad0e929f…`). At head: **13 rows, rc 0**. At parent: 17 rows, rc 1. | `receipts/rerun-r579-3-check_render.log` |
| R579-3 `check_plant_table.py` rerun | 13/13 OK, rc 0. | `receipts/rerun-r579-3-check_plant_table.log` |
| Own table check against code | 13 code plants and 13 doc rows, in the same order with the same name-to-killer mapping. rc 0. | `receipts/table-vs-plants.txt` |
| Documented command `entity_selftest.py --select mapper_plant` | 13 tests, all ok, rc 0. Work directory was outside the clone. | `receipts/mapper-plant-selftest.log`, `.rc` |
| `check_privacy.py` and `--selftest` | Pass: 11 commits, 206 historical blobs, 96 current files. Selftest: 11 controls. Both rc 0. | `receipts/privacy*.log`, `.rc` |
| Clone restore | HEAD and index tree equal `7d4a8d90…`. Status is empty, with no untracked or ignored files. `diff-index` against HEAD is empty. The index digest equals the HEAD ls-tree digest. 0 worktree blob mismatches across 96 entries. 0 gitlinks, so no submodules are required. | `receipts/restore-verification.txt` |

## Hosted CI at exact head (observed, not accepted)

Snapshot taken at `receipts/hosted-snapshot-time.txt`. The manager owns hosted/act acceptance.

- **Push run 37986303628:**
  - `bare-metal` completed with success, 7 steps, none skipped.
  - `quality` was still in progress.
- **pull_request run 37986308167:**
  - `quality` and `bare-metal` were both still in progress.
  - No step had been skipped so far.
- **Not claimed:** no hosted run result is claimed beyond this snapshot (`receipts/hosted-check-runs.tsv`, `receipts/hosted-runs.tsv`).

## Five lenses

| Lens | Result | Evidence |
|---|---|---|
| Conformance | CLEAN | The delta changes no requirement, clause claim, mapping rule or field range. Issue #2 item 6 (`docs/ENTITY_YAML.md` documents the schema and its controls) is now met for the plant table as rendered. The commit follows the CONTRIBUTING form. |
| RTL / implementation interface | CLEAN | The delta contains no C, header, generated golden, HDL or script change. The tree diff touches only `docs/ENTITY_YAML.md`. Hosted push `bare-metal` completed with success at this head. No Verilator or RTL build was needed for a one-line Markdown change. |
| Robustness | CLEAN | Byte-level proof that only one LF was inserted, with no whitespace or CR variant. The rendering is stable across two fetches. The other three tables in the file are unaffected. A parent fault control shows that the render check detects the defect class. |
| Tests | CLEAN | Rerun of R579-3's `check_render.py`: 13 rows, rc 0 (17 rows, rc 1 at the parent). Own render and table checks pass. The documented focused command kills 13/13 registered plants. The privacy gate and its selftest pass. No test changed in the delta. |
| Docs | CLEAN | GitHub shows 13 plant rows, and the quality-workflow, RV32-gate and coverage-denominator sentences are back in a prose paragraph. R578-3-R1 and R578-3-R2 stay open as RESIDUE carried by the manager. RESIDUE does not leave the lens unclean. |

## Prior public findings at this head

| Finding | Severity | State at 0c5ef53 | Evidence |
|---|---|---|---|
| R579-3-F1 | MINOR | **RESOLVED** | Blank line at `docs/ENTITY_YAML.md:169`. R579-3 `check_render.py`: 13 rows, rc 0. `check_plant_table.py`: 13/13. |
| R578-3-R3 | RESIDUE | **RESOLVED** (same defect as R579-3-F1) | 0 absorbed prose rows. See `receipts/render-check-0c5ef53….txt`. |
| R578-3-R1 | RESIDUE | **RETAINED**, carried by the manager | The sentence is unchanged and is now at `docs/ENTITY_YAML.md:245`. Exact fix as published: "The accepted entity keys are the `entity:` keys the source builder reads." |
| R578-3-R2 | RESIDUE | **RETAINED**, carried by the manager | The anchor `#L3720-L3730` is unchanged and is now at `docs/ENTITY_YAML.md:196`. Exact fix as published: `#L3720-L3735`. |
| R578-3-S1 = R579-3-S1 (sibling) | SUGGESTION | **RETAINED** (optional) | `scripts/milan_entity.py` is unchanged in this delta. |
| R578-2-F1 = R579-2-F1 | MINOR | **RESOLVED** (round 3), still holds | No script changed in this delta. The mapper plants pass at head. |
| R578-2-S1, R578-2-S2 | SUGGESTION | **ADOPTED** (round 3), still holds | 13 registered plants run at head. `requirement_records.py` is unchanged. |
| R578-2-S3, R578-1-S2 | SUGGESTION | **RETAINED** (optional) | Unchanged. |
| R578-1-F1 / R579-1-F1 (MAJOR), R578-1-F2, R578-1-F3 (MINOR), R578-1-R1, R578-1-R2 (RESIDUE), R578-1-S1 | various | **RESOLVED or disposed** (round 2), not regressed | The delta changes no text they cite. Lines after `docs/ENTITY_YAML.md:168` shift down by one, so R578-1-R1, cited at `:207` at the previous head, is now at `:208`. Earlier rounds stand. |

## Reviewer-owned ledger

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | Issue #2 body (acceptance item 6); `CONTRIBUTING.md`; commit object `0c5ef53`; `docs/ENTITY_YAML.md:150-175`; `receipts/delta-commit.txt` | R578-4 (delta); rounds 1-3 for unchanged content | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| RTL | CLEAN | Raw tree delta (one Markdown path, no C/HDL/golden/script path); hosted check runs at head | R578-4 (delta); rounds 1-3 for generated C and RV32 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Robustness | CLEAN | `receipts/byte-check.txt`; `receipts/rendered-compare.txt`; `receipts/refetch-compare.txt`; parent fault control | R578-4 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Tests | CLEAN | R579-3 `check_render.py` and `check_plant_table.py` reruns; `scripts/render_plant_table.py`; `scripts/table_vs_plants.py`; `scripts/entity_selftest.py:453-493` and the `--select mapper_plant` run; privacy gate and selftest | R578-4 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Docs | CLEAN (RESIDUE R578-3-R1, R578-3-R2 carried) | GitHub rendering of `docs/ENTITY_YAML.md` at head and parent; `docs/ENTITY_YAML.md:154-173,196,245` | R578-4 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |

## Real limits

- **Delta-only review:** content unchanged since `64888e91` was not re-reviewed. Earlier rounds stand for it.
- **No manager source bank:** none ran at this head, and none is claimed or inferred.
- **Author receipts:** the public author receipts in `942742507d…/review-evidence/tsn2-r1` are for head `4c939ef1`. They contain no receipt for this manager commit. Source-head execution evidence for this head is therefore the author's published gate receipts at earlier heads plus my focused reruns above.
- **Not rerun by me:** the full gate kit, C builds, the mutation campaign, coverage, traceability and RV32. A one-blank-line Markdown change cannot affect their inputs. Verilator was not used.
- **Hosted CI:** the runs were still in progress at my snapshot. Only push `bare-metal` had completed.
- **Rendering check scope:** GitHub's contents API HTML rendering was used. Its file-view rendering was not checked separately in a browser.
- **Hardware:** physical calibration was NOT RUN and no hardware was used. Field skips are not hardware proof.
- **Final candidate:** the current-dev merge candidate (source base `1a9f651cdf7846b8e10ac246a6ef6916960fbb92`, live dev `7c1b52bee26b497080ee22b1c1986109f80a5ee7`) was not built or validated here.

## Pending manager duties

- Carry RESIDUE R578-3-R1 and R578-3-R2 to the residue checklist with their exact fixes.
- Optionally carry SUGGESTIONs R578-3-S1 / R579-3-S1, R578-2-S3 and R578-1-S2.
- Obtain the second independent positive review at this exact head.
- Accept the hosted runs at this head (push 37986303628, pull_request 37986308167) once they complete.
- Build and validate the final current-dev merge candidate with the builder and native banks at the merge turn, and link the receipts on the PR.
- Own publication and the merge decision.
- File and link the milan-fpga integration follow-up issue that issue #2 item 7 requires.

## Packet

- **Scripts:** portable, MIT SPDX, run with `python3 -I`, taking paths as arguments:
  - `scripts/render_plant_table.py RENDERED.html SOURCE.md`
  - `scripts/compare_rendered_tables.py PARENT.html HEAD.html`
  - `scripts/table_vs_plants.py REPO_ROOT`
- **R579-3 reruns:** the R579-3 scripts were fetched from the published evidence commit `463387d8`, checked against its manifest, and run from outside the clone. They are not republished here.
- **Receipts:** raw receipts are under `receipts/`, with host paths redacted to `<clone>` and `<packet>`.
- **Manifest:** `MANIFEST.sha256` lists every publishable file.

R578-4 FINISHED
