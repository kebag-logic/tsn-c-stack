[R579] POSITIVE - exact head 0c5ef532cb782f9e7c73855b41c397679d176ea7

# R579-4: external independent delta review, kebag-logic/tsn-c-stack#2 / PR #20

- **Exact head:** `0c5ef532cb782f9e7c73855b41c397679d176ea7`, tree `7d4a8d904e073167345d3d7eeecf91fee5bec48e`. The PR head reported by the read-only API is the same commit. The detached review clone is verified at this head (`receipts/restore_verification.txt`).
- **Delta reviewed:** `64888e91..0c5ef532`, one manager commit, "Separate the mapper plant table from the following prose" (`receipts/commit_0c5ef53.txt`). The subject is one line with no body or trailer, as `CONTRIBUTING.md` requires.
- **Full PR range:** `1a9f651c..0c5ef532`. Earlier rounds stand for all content this commit does not touch. Unchanged content was not re-reviewed.
- **Scope:** answer R579-3-F1 (the same defect as R578-3-R3):
  - the mapper plant table in `docs/ENTITY_YAML.md` absorbed the four following prose sentences as table rows;
  - the required outcome was one blank line between `:168` and `:169`.

## Verdict

POSITIVE. The delta is exactly the required one-line repair and nothing else.

- GitHub's own rendering of the file at the exact head shows the mapper plant table with exactly 13 body rows.
- The four sentences render again as an ordinary paragraph after the table.
- No new finding. No MINOR, MAJOR or BLOCKER finding is open at this head.

## Delta checks (exact head)

### 1. The diff is exactly one blank line

- **Tree diff:** `git diff --raw 64888e91 0c5ef532` lists one path: `M docs/ENTITY_YAML.md`, mode `100644` before and after, blob `69c0e98` → `3928ca1` (`receipts/delta_64888e9_0c5ef53.raw`).
  - A full `ls-tree -r` comparison of both commits differs only in that blob.
  - The repository has no gitlinks and no `.gitmodules`, so no submodule pointer can have changed.
- **Unified diff:** `receipts/delta_64888e9_0c5ef53.diff` is one hunk, `@@ -166,6 +166,7 @@`, adding one empty line `+` between:
  - the `unknown-key-generic` row (`docs/ENTITY_YAML.md:168`);
  - "The [quality workflow]…" (now `:170`).
- **Byte check:** `receipts/blob_insertion_check.txt`, rc 0.
  - The new blob equals the old blob with exactly one empty line inserted at 1-based line 169.
  - The size grows by one byte (20546 → 20547).
  - The file has no CR bytes.

### 2. GitHub rendering at the exact head: 13 plant rows

- **Source:** GitHub's rendering was fetched read-only through the contents API with the HTML media type, at both the exact head and the parent:
  - `receipts/render-0c5ef53.html`;
  - `receipts/render-64888e9.html`.
- **R579-3's `check_render.py`, rerun unchanged:** copied to `r579-3-rerun/`, sha256 `ad0e929f…58394`, which equals the R579-3 published manifest.

  | Rendering | Body rows | rc | Receipt |
  |---|---|---|---|
  | Head `0c5ef53` | 13, `base-zero` … `unknown-key-generic` | 0 | `receipts/rerun_r579-3_check_render-0c5ef53.log` |
  | Parent `64888e9` (control) | 17, rows 14-17 are the absorbed prose | 1 | `receipts/rerun_r579-3_check_render-64888e9.log` |

  The parent result reproduces R579-3's published `check_render.log` line for line.
- **Independent checker:** `render_check.py` is a structural HTML parser. It selects the table by its exact header (`Plant | Planted defect | Required failing test`). It requires 13 three-cell rows, no prose inside the table, and "The quality workflow…" as the first paragraph after the table.
  - Head: PASS, rc 0 (`receipts/render_check-0c5ef53.txt`).
  - Parent: FAIL, rc 1, 17 rows (`receipts/render_check-64888e9.txt`).
- **Rendered diff:** `receipts/render_diff_64888e9_to_0c5ef53.txt`, normalised only for the per-render random Mermaid `data-identity` UUID.
  - The only change is that the four absorbed `<tr>` rows are removed and one `<p>` holding the same four sentences, with the same three links, is added after `</table>`.
  - Nothing else in the rendered document changes.
- **Rendering stability:** my parent rendering is byte-identical to R579-3's published `ENTITY_YAML.rendered.64888e91.html`, apart from that UUID.
- **Registry agreement:** R579-3's `check_plant_table.py`, rerun unchanged, still matches 13/13 by name and killer (`receipts/rerun_r579-3_check_plant_table.log`, rc 0).

### 3. Nothing else changed, and no sibling defect

- **Sibling tables:** `table_tail_scan.py` checks every Markdown table in all eight `.md` files the PR touches (`1a9f651c..0c5ef532`) for a row followed directly by text.
  - Head: 0 tables running into text (`receipts/table_tail_scan-0c5ef53.log`, rc 0).
  - Control: the parent `ENTITY_YAML.md` reports exactly the R579-3-F1 site (`:169`), rc 1.
- **Graph gate:** this gate reads every `docs/*.md`. The single Mermaid fence in `docs/ENTITY_YAML.md` is byte-identical at parent and head (`receipts/mermaid_fence_equivalence.txt`, rc 0), so the graph gate's input is unchanged.
- **Other readers of the file:** the only other reader is the requirement evidence link `docs/requirements.json:905`, `"url": "ENTITY_YAML.md"`. It has no fragment, so `requirement_records.py` checks only that the file exists. The delta adds or removes no heading line. The privacy gate scans the file and passes (below).
- **Focused gates:** reviewer executions at the exact head.

  | Gate | Result |
  |---|---|
  | `check_privacy.py` (scans current files and history) | pass, 11 commits, 206 historical blobs, 96 files, rc 0 |
  | `check_privacy.py --selftest` | rc 0 |
  | `check_license.py --selftest` | rc 0 |
  | `entity_yaml.py --examples --check` | rc 0 |
  | `entity_selftest.py` | 196 tests OK, rc 0 |
  | `entity_selftest.py --select mapper_plant` | 13 tests OK, rc 0 |

## Findings

No new finding at this head.

## Prior public findings at this head

| Finding | Severity | State at 0c5ef532 | Evidence |
|---|---|---|---|
| R579-3-F1 = R578-3-R3 | MINOR (R579-3) / RESIDUE (R578-3) | **RESOLVED** | One blank line at `docs/ENTITY_YAML.md:169`. Rendered table has 13 rows (R579-3's `check_render.py` rc 0). Prose is rendered as a paragraph. |
| R579-3-S1 | SUGGESTION | **RETAINED** (optional, not adopted) | The `firmware_rev` mapping row `docs/ENTITY_YAML.md:196` is unchanged. |
| R578-3-R1 | RESIDUE | **RETAINED**, carried to the residue checklist | Still present at `docs/ENTITY_YAML.md:245` (shifted by one line): "The accepted entity keys are the keys read by the source entity loader." Exact fix as published: "The accepted entity keys are the `entity:` keys the source builder reads." |
| R578-3-R2 | RESIDUE | **RETAINED**, carried to the residue checklist | Still present at `docs/ENTITY_YAML.md:196`: the source-loader anchor is `#L3720-L3730`. Exact fix as published: `#L3720-L3735`. |
| R578-3-S1 | SUGGESTION | **RETAINED** (optional) | Mapper unchanged in this delta. |
| R578-2-F1 = R579-2-F1 | MINOR | **RESOLVED** (round 3), still holds | Mapper and selftests unchanged in this delta. 196 selftests and 13 mapper plants pass at head. |
| R578-2-S1 | SUGGESTION | **RESOLVED** (round 3), still holds | 13 registered plants run and pass at head. Doc table matches the registry 13/13. |
| R578-2-S2 | SUGGESTION | **ADOPTED** (round 3) | Unchanged. |
| R578-2-S3 | SUGGESTION | **RETAINED** (optional) | Unchanged. |
| R578-1-F1 = R579-1-F1 | MAJOR | **RESOLVED** (round 2), still holds | No script change in this delta. The scalar-grammar plants are registered and pass. |
| R578-1-F2, R578-1-F3 | MINOR | **RESOLVED** (round 2), still holds | No script or requirement change in this delta. |
| R578-1-R1, R578-1-R2 | RESIDUE | **RESOLVED** (round 2), still holds | Text unchanged, shifted by one line where after `:169`. |
| R578-1-S1 | SUGGESTION | Addressed by documentation (round 2) | Unchanged. |
| R578-1-S2 | SUGGESTION | **RETAINED** (optional) | Unchanged. |

## Five lenses

| Lens | Result | Artifact-specific evidence |
|---|---|---|
| Conformance | **CLEAN** | The delta changes no mapping row, clause reference, source anchor or conformance claim. The byte check shows that only an empty line was added. Earlier rounds' conformance results hold. |
| RTL / implementation interface | **CLEAN** | The delta changes no C, header, generated golden, script or HDL file (one-path raw diff). `entity_yaml.py --examples --check` rc 0. The graph-gate input is identical. No RTL is in scope, so Verilator was not used. |
| Robustness | **CLEAN** | No executable change. The robustness of the document markup is checked: across all eight PR-touched Markdown files, no table runs into the following text. The scan control catches the parent defect. |
| Tests | **CLEAN** | Both render checks discriminate: PASS at head, FAIL at the parent control. The table-scan control fails on the parent. 196 selftests and 13 mapper plants pass. Privacy and licence selftests pass. |
| Docs | **CLEAN** (RESIDUE R578-3-R1 and R578-3-R2 retained, carried) | R579-3-F1 is resolved in GitHub's own rendering: 13 rows, and the four sentences are restored verbatim as a paragraph with their links. The text "register 13 mapper plants" now matches the rendered table. |

## Reviewer-owned ledger

| Lens | CLEAN/UNCLEAN | Examined artifacts | Covering round | Exact head |
|---|---|---|---|---|
| Conformance | CLEAN | `receipts/delta_64888e9_0c5ef53.{raw,diff}`; `receipts/blob_insertion_check.txt`; `docs/ENTITY_YAML.md:196-197,245` (unchanged rows) | R579-4 (delta); R579-3 and earlier for unchanged content | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| RTL | CLEAN | One-path tree diff; `receipts/head_entity_golden.log`; `receipts/mermaid_fence_equivalence.txt`; `receipts/hosted_runs.txt` | R579-4 (delta); R579-3 and earlier for generated C and RV32 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Robustness | CLEAN | `table_tail_scan.py`; `receipts/table_tail_scan-0c5ef53.log`; `receipts/table_tail_scan-64888e9-control.log` | R579-4 (delta); R579-3 for mapper behaviour | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Tests | CLEAN | `r579-3-rerun/check_render.py`; `r579-3-rerun/check_plant_table.py`; `render_check.py`; `receipts/rerun_r579-3_*`; `receipts/render_check-*`; `receipts/head_selftest_full.log`; `receipts/head_selftest_mapper_plant.log`; `receipts/head_privacy*.log`; `receipts/head_license_selftest.log` | R579-4 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |
| Docs | CLEAN (RESIDUE R578-3-R1, R578-3-R2 retained) | `docs/ENTITY_YAML.md:144-173`; `receipts/render-0c5ef53.html`; `receipts/render-64888e9.html`; `receipts/render_diff_64888e9_to_0c5ef53.txt`; PR body (no round-4 section; none is needed for a markup-only repair) | R579-4 | 0c5ef532cb782f9e7c73855b41c397679d176ea7 |

## Real limits

- **No author receipts at this head:** the public evidence tree `942742507d…/review-evidence/tsn2-r1` binds the round-1 head `0a1a14a1` and holds no receipts for `64888e91` or `0c5ef532`.
  - The repair is a manager commit, so no author gate run exists at this exact head.
  - Source-head execution evidence for this head is therefore my focused reruns above and the exact-head hosted runs.
  - The author's REVIEW READY gate claims (27 Linux gates, RV32 Debug/Release, 330 plants) were made at `64888e91`. They carry over only because this delta is one empty Markdown line. Apart from the privacy gate, the graph gate and the fragment-free requirement link covered above, no build, test or campaign reads this file.
- **Not rerun by me:** the full 27-gate kit, the C mutation campaign, coverage, RV32 and the Mermaid renderer. The delta cannot reach them; the graph-gate input is shown to be identical.
- **Hosted CI at this head:** both runs were still in progress when recorded (`receipts/hosted_runs.txt`, 2026-10-09T20:24:27Z).
  - Push run 37986303628: `bare-metal` completed with success (7/7 steps); `quality` was in progress.
  - Pull-request run 37986308167: both jobs were in progress.
  - No job had been skipped. The manager owns hosted/act acceptance.
- **No manager source bank:** none ran at this head, and none is claimed or inferred.
- **Rendering:** the rendered HTML is GitHub's contents-API rendering. It differs between fetches only by a random Mermaid container UUID.
- **Hardware:** physical calibration was not run and no hardware was used. Field skips are not hardware proof.
- **Final candidate:** the current-dev merge candidate (source base `1a9f651c`, live dev `7c1b52be`) was not built or validated here.

## Pending manager duties

- Confirm that hosted runs 37986303628 and 37986308167 complete successfully at this head, and own hosted/act acceptance.
- Carry RESIDUE R578-3-R1 and R578-3-R2, with their published exact fixes, to the residue checklist.
- Optionally carry SUGGESTIONS R579-3-S1, R578-3-S1, R578-2-S3 and R578-1-S2.
- Obtain the second independent positive review required at this exact head.
- Build and validate the final current-dev merge candidate with the builder and native banks, and publish the receipts on the PR.
- File and link the milan-fpga integration follow-up issue required by issue item 7.
- Handle publication.

## Packet

- **Scripts:** portable, run with `python3 -I`, taking paths as arguments:
  - `render_check.py RENDERED.html [ROWS]`;
  - `table_tail_scan.py FILE...`;
  - `r579-3-rerun/check_render.py` and `r579-3-rerun/check_plant_table.py`, unchanged copies of R579-3's published scripts.
- **Receipts:** raw logs and rc files are under `receipts/`. The author e-mail is redacted in `commit_0c5ef53.txt`.
- **Manifest:** `MANIFEST.sha256` lists every publishable file.
- **Clone state:** after the gate runs, the clone was restored and verified (`receipts/restore_verification.txt`):
  - the index tree equals the HEAD tree `7d4a8d90…`;
  - all 96 worktree blobs and modes match the index;
  - nothing is modified, untracked or ignored;
  - there are no submodule gitlinks.

R579-4 FINISHED
