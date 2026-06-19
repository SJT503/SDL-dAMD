# test_data — minimal reproducible inputs for the credibility-audit harness

A small, self-contained, **synthetic** input set that exercises all three
audit metrics end-to-end **without** requiring the paper's restricted real
tournament data (which lives in the Zenodo deposit, DOI 10.5281/zenodo.20574265).

These are the same demo inputs shipped under `code/examples/`, copied here under
stable names so `run_all_tests.sh` has a fixed reference set. Every file is
clearly labelled `EXAMPLE` and contains no real patient or experimental data.

## Files

| file | metric | what it feeds |
|---|---|---|
| `test_citations.json` | 1. Hallucination rate | 3 synthetic `{pmid, claim}` reference slots |
| `test_ot_scores.json` | 2. Anti-retrieval | synthetic `gene -> association_score` map |
| `verdicts/pair_*_{a,b}_judge{1,2}.json` | 3. Position bias | 3 synthetic pairs × 2 directions × 2 judges = 12 verdict files |

## The three-pair verdict set (synthetic)

- `pair_01` — consistent winner (`a → B,B`; `b → A,A`) → **not flagged**
- `pair_02` — position-biased (`a → B,B`; `b → B,B`, different winners) → **flagged**
- `pair_03` — mixed verdicts → **not flagged**

Expected position-bias rate on this set: **1 of 3 = 33.33 %**.

## Genes used (synthetic)

- Mechanism-first set: `MECHA1..MECHA5, SHARED1` (6 genes)
- Retrieval-baseline set: `LOOKUP1..LOOKUP5, SHARED1` (6 genes)
- `SHARED1` is the single overlap (Jaccard = 1/11 = 0.0909).

## Notes

- The hallucination metric (`test_citations.json`) makes one **live** NCBI
  E-utilities call per slot to verify each PMID. Slot `00000000` is a guaranteed
  non-existent PMID. The on-topic/off-topic split of the two real-PMID slots can
  in principle drift if the PubMed records change; `run_all_tests.sh` asserts the
  structural counts (total slots, PMID-not-found count) rather than the full
  rate, so the suite stays stable across PubMed metadata updates.
- See `code/examples/NOTES.md` for the **real** dAMD Run 1 verdict schema that
  `position_bias()` parses; the files here imitate that schema.
