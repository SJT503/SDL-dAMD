# Credibility-Audit Harness

A small, dependency-light, **honest** tool that computes three *measurable*
trustworthiness metrics for the output of **any** autonomous scientific-discovery
system. It is the open companion tool for:

> **A measurable trustworthiness audit for AI-driven scientific discovery.**
> Sheng J. et al. (2026).

The harness does not score "intelligence" or "novelty." It answers three
concrete, checkable questions about a discovery run:

1. **Are the citations real and on-topic?** (hallucination rate)
2. **Did the system actually reason, or just look up a database?** (anti-retrieval separation)
3. **Did the LLM judge decide by content, or by where a candidate was printed?** (position-bias rate)

Each metric is independent — run whichever inputs you have.

---

## The three metrics

### 1. Hallucination rate (citation round-trip)

Input: a list of reference *slots*, each `{pmid, claim}`. For every slot the tool
queries **NCBI E-utilities** (`esummary`, `db=pubmed`, `retmode=json`) over the
Python standard library (`urllib`, no `requests` dependency) and marks the slot a
**hallucination** if either:

- **(a) the PMID returns no real record** — it does not exist; or
- **(b) the real record is off-topic** for the claim it was cited to support.

Failure mode (b) uses a **transparent, tunable heuristic** (`on_topic()`): the
fraction of the claim's content words (stop-words removed) that appear in the
returned title — optionally also the abstract via `efetch` (`--deep-topic`). If
that overlap is below `--threshold` (default `0.10`) the slot is off-topic. This
is a deliberately simple, inspectable rule, **not** a semantic ground truth — you
can tune the threshold, extend the comparison text, or replace `on_topic()` with
your own (e.g. embedding similarity).

`rate = hallucinated_slots / total_slots`. Calls sleep `~0.4 s` apart to respect
NCBI's ~3 requests/second limit for un-keyed access.

### 2. Anti-retrieval separation

Input: two gene rankings — the system's **mechanism-first** ranking vs a
**retrieval/lookup baseline** — plus a `gene -> association_score` map (e.g. Open
Targets overall association score). The tool reports:

- the **mean association score** of each set;
- a **Mann-Whitney U** p-value between the two score distributions;
- the **Jaccard overlap** of the two gene *sets*.

Interpretation: a genuinely mechanism-first system should **not** simply
reproduce what a database lookup returns. Low Jaccard + a significant
score difference = evidence of independent reasoning; high Jaccard = the "system"
is effectively a retriever.

Mann-Whitney U uses `scipy.stats.mannwhitneyu` when SciPy is installed; otherwise
a correct **stdlib normal-approximation MWU** (tie-corrected variance + continuity
correction) is used. The report records which backend produced the p-value. (The
two agree to < 1e-3 against SciPy's asymptotic method on random samples.)

### 3. Position-bias rate (LLM-judge A/B reversal)

Input: tournament verdicts where each pair was judged in **both** presentation
orders (A-then-B and B-then-A) by multiple judges. A pair is **flagged** when the
**same presentation slot wins in every verdict** — every judge in every direction
picks slot A, or every judge in every direction picks slot B. That strict
"same-position 6/6" pattern means the *position*, not the candidate's identity,
drove the decision. Partial patterns are **not** flagged; in particular the
healthy "consistent winner" case (the same real candidate wins in both orders,
appearing as slot B one way and slot A the other) is correctly **not** flagged.

`rate = flagged_pairs / total_pairs`.

---

## Install

Python **3.8+**. No required third-party packages.

```bash
# nothing to install for the core tool; everything else is stdlib
python --version          # 3.8 or newer
# OPTIONAL: exact Mann-Whitney U for metric 2
pip install scipy
```

The hallucination metric needs outbound HTTPS access to
`eutils.ncbi.nlm.nih.gov`. The other two metrics are fully offline.

---

## Input schemas

### `--citations cites.json` (metric 1)

A JSON **list** of slot objects:

```json
[
  {"candidate": "MERTK", "pmid": "18207454", "claim": "MERTK retinal pigment epithelium phagocytosis photoreceptor outer segment"},
  {"candidate": "MERTK", "pmid": "00000000", "claim": "fabricated reference example"}
]
```

`candidate` is optional metadata. `pmid` and `claim` are required.

### Anti-retrieval (metric 2)

Three inputs supplied together:

```bash
--sdl-genes MERTK,GAS6,MFG-E8,ITGB5 \
--retrieval-genes CFH,C3,ARMS2,VEGFA \
--ot-scores scores.json
```

`scores.json` is a JSON **object** `gene -> score`:

```json
{ "MERTK": 0.21, "GAS6": 0.09, "CFH": 0.95, "C3": 0.88 }
```

Keys beginning with `_` (e.g. `_comment`) and non-numeric values are ignored, so
you may annotate the file. Genes with no score are dropped from the U-test and
listed under `missing_scores`.

### `--verdicts <dir|json>` (metric 3)

Either:

- **A directory** of the per-judge files `pair_<NN>_<a|b>_judge<R>.json`
  (the layout of the paper's data; see `examples/NOTES.md`). Each file is UTF-8
  JSON containing at least `verdict` ∈ `{"A","B"}` (the winning slot). The
  loader also accepts `winner_slot` / `winner` / `choice` / `selected` for other
  systems; or
- **A single JSON file** — either a list of verdict records, or a dict mapping
  `pair_id -> [records]`. Each record carries a slot field as above and (when a
  single file is used) should include `direction` and `pair_id`.

A runnable synthetic set lives in `examples/verdicts/`.

---

## CLI usage

```bash
python credibility_audit.py \
    --verdicts <dir-or-json> \
    [--citations cites.json] \
    [--sdl-genes a,b,c --retrieval-genes x,y,z --ot-scores scores.json] \
    [--threshold 0.10] [--deep-topic] [--sleep 0.4] \
    [--system "MySystem v1"] [--version "run3"] \
    [--out report.md] [--json-out results.json] [--quiet]
```

Every metric is optional; the tool computes whichever input group you supply and
emits the **Credibility-Audit Triple** report (Markdown + optional results JSON).

End-to-end demo on the bundled synthetic examples (one live NCBI call group):

```bash
python credibility_audit.py \
  --verdicts examples/verdicts \
  --citations examples/example_citations.json \
  --sdl-genes MECHA1,MECHA2,MECHA3,MECHA4,MECHA5,SHARED1 \
  --retrieval-genes LOOKUP1,LOOKUP2,LOOKUP3,LOOKUP4,LOOKUP5,SHARED1 \
  --ot-scores examples/example_ot_scores.json \
  --out examples/example_report.md
```

---

## Validation — dAMD Run 1 position-bias (7 / 45)

The position-bias function reproduces the paper's reported dАMD Run 1 result
**exactly**. Pointed at the real tournament directory:

```bash
python credibility_audit.py \
  --verdicts "/path/to/tournament2_verdicts/"
```

it returns **7 of 45 pairs flagged = 15.56 %**, with flagged pairs

```
pair_04, pair_07, pair_12, pair_19, pair_22, pair_25, pair_38
```

matching the independently-recorded ground truth in that directory's
`checkpoint_log.json` (`position_bias_cumulative_FINAL`). See `examples/NOTES.md`
for the exact verdict schema and the derivation. This is the harness's
end-to-end correctness check: the parser is built against the real file schema,
not against a hardcoded answer.

---

## On-topic heuristic — caveat

Failure mode (b) of the hallucination metric is a **heuristic**, not a verdict on
scientific correctness. Token overlap can mark a correct-but-differently-worded
citation as off-topic (false positive) or pass a superficially keyword-matching
but irrelevant paper (false negative). Treat metric 1 as a **screen**: it
reliably catches non-existent PMIDs and grossly mismatched citations, and it
flags borderline cases for human review. Tune `--threshold`, add `--deep-topic`
to include abstracts, or replace `on_topic()` to suit your field. Always report
the heuristic and threshold you used (the report does this automatically).

---

## Output

- A Markdown **Credibility-Audit Triple** report (stdout, and `--out`), matching
  `REPORTING_TEMPLATE.md`.
- Optional full machine-readable `--json-out` with per-slot / per-pair verdicts.

---

## Files

```
audit_harness/
├── credibility_audit.py     # the tool (stdlib-first; scipy optional)
├── README.md                # this file
├── REPORTING_TEMPLATE.md    # one-page fillable triple-report form
└── examples/
    ├── example_citations.json   # synthetic {pmid, claim} slots
    ├── example_ot_scores.json   # synthetic gene -> score map
    ├── verdicts/                # synthetic per-judge verdict files
    ├── example_report.md        # sample generated report
    ├── example_results.json     # sample generated results JSON
    └── NOTES.md                 # the real dAMD verdict schema (validation)
```

All files under `examples/` are clearly-labelled **synthetic** demo data, not
real paper results.

---

## Citation

If you use this harness, please cite:

> Sheng J. et al. **A measurable trustworthiness audit for AI-driven scientific
> discovery.** (2026).
