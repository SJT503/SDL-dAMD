# Credibility-Audit Triple — Report

> One-page trustworthiness audit for an autonomous scientific-discovery run.
> Produced by `credibility_audit.py`. Fill the bracketed fields (or let the tool
> fill them via `--out`). Leave a metric marked _not computed_ if its inputs
> were not provided.

## Metadata

| Field                | Value                          |
|----------------------|--------------------------------|
| System audited       | `[system name]`                |
| Run / version        | `[run label / version]`        |
| Disease / task       | `[e.g. dry AMD target discovery]` |
| Audit date (UTC)     | `[YYYY-MM-DDThh:mm:ssZ]`       |
| Harness              | `credibility_audit.py`         |
| Auditor              | `[name / initials]`            |

---

## 1 · Hallucination rate (citation round-trip)

| Quantity                         | Value            |
|----------------------------------|------------------|
| Reference slots evaluated        | `[N]`            |
| PMID-not-found (mode a)          | `[n_a]`          |
| Off-topic real record (mode b)   | `[n_b]`          |
| On-topic threshold / deep_topic  | `[0.10] / [no]`  |
| **Hallucination rate (as-discovered)** | **`[__.__%]`** |
| Hallucination rate (grounded / repaired) | `[__.__%]` |

**Interpretation (one line):** `[fraction of cited references that are fabricated
or do not support their claim; report the as-discovered rate next to any grounded
re-run; lower is better]`

---

## 2 · Anti-retrieval separation

| Quantity                                   | Value          |
|--------------------------------------------|----------------|
| Mechanism-first mean association score (n) | `[0.____]` (`[n]`) |
| Retrieval-baseline mean score (n)          | `[0.____]` (`[n]`) |
| Mean-score separation (mech − retrieval)   | `[±0.____]`    |
| Mann-Whitney U / p-value                   | `[U]` / `[p]`  |
| MWU backend                                | `[scipy | stdlib_normal_approx]` |
| Jaccard overlap of gene SETS               | `[0.____]`     |

**Interpretation (one line):** `[low Jaccard + significant score gap => genuine
mechanism-first reasoning, not a database lookup; high Jaccard => retrieval]`

---

## 3 · Position-bias rate (LLM-judge A/B reversal)

| Quantity                            | Value          |
|-------------------------------------|----------------|
| Pairs scored                        | `[N]`          |
| Flagged (same slot wins every verdict) | `[k]`       |
| **Position-bias rate**              | **`[__.__%]`** |
| Flagged pair ids                    | `[pair_.., pair_..]` |

**Interpretation (one line):** `[fraction of pairs whose winner is fixed by
presentation order rather than candidate identity; flagged pairs should be
tie-broken or excluded before the final ranking; lower is better]`

---

## Summary line

> `[System]` `[version]` — hallucination `[__.__%]` (as-discovered),
> anti-retrieval Jaccard `[0.__]` (p = `[__]`),
> position-bias `[__.__%]` (`[k]`/`[N]`).
