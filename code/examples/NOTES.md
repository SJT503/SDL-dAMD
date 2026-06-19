# NOTES — the real dAMD Run 1 verdict schema (position-bias validation)

This file documents the **actual** on-disk schema that `position_bias()` parses,
as observed by reading the paper's real tournament data. The synthetic files in
`examples/verdicts/` imitate this schema so the tool can be run end-to-end
without the real (restricted) data.

## Where the real data lives

The paper's internal tournament data (45 pairs x 6 verdict files = 270 files)
is deposited in the Zenodo archive accompanying the paper
(DOI 10.5281/zenodo.20574265), not shipped with this harness. The harness only
needs to *match its schema*, which the synthetic files in `examples/verdicts/`
reproduce.

## File layout

- One JSON file **per judge verdict**.
- Naming: `pair_<NN>_<dir>_judge<R>.json`
  - `<NN>` = zero-padded pair id, `01` … `45`
  - `<dir>` = presentation order: `a` (A-then-B) or `b` (B-then-A, i.e. the two
    candidates swapped)
  - `<R>`  = judge replicate, `1` … `3`
- Per pair: 2 directions × 3 judges = **6 verdict files**.
- Total: 45 pairs × 6 = **270 files**.
- **Encoding: UTF-8.** Files contain non-ASCII text (curly quotes, Greek
  letters such as αvβ5 in `winner_name`/`reasoning`). Opening them with the
  Windows default codec (GBK/cp936) raises `UnicodeDecodeError`. The harness
  always opens verdict files with `encoding="utf-8"`.

## Fields (per file)

| field             | type   | meaning                                                        |
|-------------------|--------|----------------------------------------------------------------|
| `pair_id`         | str    | `"04"` — the pair, matches the filename                        |
| `direction`       | str    | `"a"` or `"b"` — which presentation order was judged           |
| `judge_replicate` | str    | `"1"`/`"2"`/`"3"`                                               |
| `verdict`         | str    | **`"A"` or `"B"` — which presentation SLOT won** (the field the harness reads) |
| `winner_name`     | str    | the actual candidate that occupied the winning slot            |
| `science`/`feasibility`/`novelty` | str | per-dimension slot picks (not needed for the metric) |
| `reasoning`       | str    | free-text rationale (not needed for the metric)                |

The harness reads `verdict` (falling back, for other systems, to
`winner_slot` / `winner` / `choice` / `selected`) and coerces it to `A`/`B`.

## The flagging rule and why it gives 7/45

`verdict` records the **winning presentation slot**, not the candidate's
identity. A pair is **position-biased** when the *same slot letter* wins in
**every** verdict (all 3 judges in both directions). Two cases:

- **Healthy / consistent winner** (NOT flagged): the same real candidate wins
  regardless of order. In direction `a` it sits in slot B → `verdict = "B"`; in
  direction `b` it has been swapped into slot A → `verdict = "A"`. The verdict
  letters therefore **differ** between directions. Example — `pair_01`:
  `a → B,B,B` and `b → A,A,A` (ADAM10/ADAM17 wins both orders). Mixed letters →
  not flagged.
- **Position-biased** (FLAGGED): the same *slot* wins both ways, so a *different*
  real candidate wins in each direction. All six letters are identical. Example
  — `pair_04`: `a → B,B,B` (winner_name = GAS6) and `b → B,B,B`
  (winner_name = PTK2/FAK). Slot B won no matter who sat there → flagged.

Applying "all six verdict letters identical ⇒ flag" to the 45 real pairs yields
exactly:

```
pair_04, pair_07, pair_12, pair_19, pair_22, pair_25, pair_38
= 7 of 45 = 15.56%
```

This matches the independently-recorded ground truth in the same directory's
`checkpoint_log.json`:

```json
"position_bias_cumulative_FINAL": {
  "all_pairs": ["pair_04","pair_07","pair_12","pair_19","pair_22","pair_25","pair_38"],
  "cumulative_count": 7,
  "cumulative_total_pairs": 45,
  "cumulative_rate_pct": 15.56
}
```

## Reproduce it

```bash
python credibility_audit.py \
  --verdicts "/path/to/tournament2_verdicts/"
```

Expected: `Pairs scored: 45`, `Flagged: 7`, `Position-bias rate = 15.56%`,
flagged pairs `pair_04, pair_07, pair_12, pair_19, pair_22, pair_25, pair_38`.

## The synthetic example set (`examples/verdicts/`)

A deliberately tiny 3-pair stand-in (2 judges × 2 directions per pair) for
running the tool without the real data:

- `pair_01` — consistent winner (`a → B,B`; `b → A,A`) → **not flagged**
- `pair_02` — position-biased (`a → B,B`; `b → B,B`, different winners) → **flagged**
- `pair_03` — mixed verdicts → **not flagged**

Result on this set: 1 of 3 flagged (33.3%). The numbers here are illustrative
synthetic values, clearly marked `EXAMPLE` in each file's `_note`.
