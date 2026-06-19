#!/usr/bin/env python3
"""
credibility_audit.py -- The Credibility-Audit Harness.

A small, dependency-light, *honest* tool that computes the three measurable
trustworthiness metrics described in:

    "A measurable trustworthiness audit for AI-driven scientific discovery",
    Sheng J. et al. (2026).

It runs on ANY autonomous-discovery system's output, not just the system used
in the paper. Each metric is independent; you run whichever inputs you provide.

The three metrics
-----------------
1. HALLUCINATION RATE  (citation round-trip)
   For each {pmid, claim} reference slot, query NCBI E-utilities and decide
   whether the slot is a *hallucination*:
     (a) the PMID returns no real record (does not exist), OR
     (b) the real record is off-topic for the claim it is cited to support.
   (b) uses a transparent, tunable token-overlap heuristic (see on_topic()).
   Rate = hallucinated_slots / total_slots.

2. ANTI-RETRIEVAL SEPARATION
   Given a mechanism-first ranking and a retrieval/lookup baseline ranking,
   plus a gene -> association-score map, compute the mean score of each set,
   a Mann-Whitney U p-value between the two score distributions, and the
   Jaccard overlap of the two gene SETS. A genuinely mechanism-first system
   should NOT simply reproduce what a database lookup returns.

3. POSITION-BIAS RATE  (LLM-judge A/B reversal)
   Each pair is judged in BOTH presentation orders (A-then-B and B-then-A) by
   multiple judges. A pair is FLAGGED when the *same presentation slot* wins in
   ALL verdicts (every judge in every direction picks slot A, or every judge in
   every direction picks slot B). That is the strict same-position 6/6 pattern:
   the winning position is constant across orderings, so position -- not the
   candidate's identity -- drove the decision. Partial patterns are NOT flagged.
   Rate = flagged_pairs / total_pairs.

Design constraints (deliberate)
-------------------------------
* Standard library first: urllib, json, argparse, statistics, glob, re.
* scipy is OPTIONAL and used only for the Mann-Whitney U test. If scipy is not
  installed, a correct stdlib normal-approximation MWU (with tie correction and
  continuity correction) is used instead; the report records which path ran.
* No fabricated numbers, no hardcoded results, no placeholder logic.
* All verdict files are read as UTF-8 (the real data contains non-ASCII text).

CLI
---
    python credibility_audit.py --verdicts <dir-or-json> \
        [--citations cites.json] \
        [--sdl-genes a,b,c --retrieval-genes x,y,z --ot-scores scores.json] \
        [--out report.md]

Run with no metric inputs to print usage. Provide any subset of the three
metric input groups; the report covers exactly what was computed.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# scipy is optional; only used for the Mann-Whitney U test.
try:
    from scipy.stats import mannwhitneyu as _scipy_mannwhitneyu  # type: ignore
    _HAVE_SCIPY = True
except Exception:  # pragma: no cover - environment dependent
    _scipy_mannwhitneyu = None
    _HAVE_SCIPY = False

NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Tokens that carry no topical signal; stripped before overlap scoring.
_STOPWORDS = frozenset("""
a an and are as at be by for from has have in into is it its of on or that the
their this to was were will with we our using use used based via between both
role roles study studies analysis effect effects novel new can may show shows
shown identify identification function functional level levels these those
""".split())


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------
def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tokenize(text: str) -> set:
    """Lowercase alphanumeric tokens of length >= 3, minus stopwords."""
    if not text:
        return set()
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in toks if len(t) >= 3 and t not in _STOPWORDS}


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# METRIC 1 -- HALLUCINATION RATE (citation round-trip via NCBI E-utilities)
# ===========================================================================
def _ncbi_esummary(pmid: str, timeout: float = 20.0) -> dict | None:
    """Return the esummary record dict for a PMID, or None if it does not exist.

    Uses NCBI E-utilities esummary (db=pubmed, retmode=json) over urllib.
    A PMID is treated as non-existent if the API returns an error for that uid
    or returns no usable record.
    """
    params = urllib.parse.urlencode(
        {"db": "pubmed", "id": str(pmid), "retmode": "json"}
    )
    url = f"{NCBI_ESUMMARY}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "credibility-audit-harness/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return None

    result = payload.get("result")
    if not isinstance(result, dict):
        return None
    rec = result.get(str(pmid))
    if not isinstance(rec, dict):
        return None
    # NCBI signals a bad uid with an "error" key on the record.
    if rec.get("error"):
        return None
    # A genuine record carries a title (possibly empty for very old items, but
    # esummary still returns the uid). Require at least a title or sortpubdate.
    if not (rec.get("title") or rec.get("sortpubdate") or rec.get("pubdate")):
        return None
    return rec


def _ncbi_efetch_abstract(pmid: str, timeout: float = 20.0) -> str:
    """Fetch the abstract text for a PMID via efetch (rettype=abstract).

    Best-effort: returns "" on any failure. Only called when deep_topic=True.
    """
    params = urllib.parse.urlencode(
        {"db": "pubmed", "id": str(pmid), "rettype": "abstract", "retmode": "text"}
    )
    url = f"{NCBI_EFETCH}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "credibility-audit-harness/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return ""


def on_topic(claim: str, title: str, extra: str = "", threshold: float = 0.10) -> tuple:
    """Transparent on-topic HEURISTIC. Returns (is_on_topic, overlap_score).

    overlap_score = |tokens(claim) & tokens(title+extra)| / |tokens(claim)|
    i.e. the fraction of the claim's content words that appear in the returned
    record's title (and optional extra text such as MeSH terms / abstract).
    is_on_topic = overlap_score >= threshold.

    This is a deliberately simple, inspectable rule -- NOT a ground-truth
    semantic judgement. Tune `threshold`, extend `extra`, or replace this
    function with your own (e.g. an embedding similarity) to suit your domain.
    A claim with no scorable tokens cannot be assessed and returns (True, None)
    so it is never counted as a hallucination on heuristic grounds alone.
    """
    claim_tokens = _tokenize(claim)
    if not claim_tokens:
        return True, None
    record_tokens = _tokenize(title) | _tokenize(extra)
    overlap = len(claim_tokens & record_tokens) / len(claim_tokens)
    return (overlap >= threshold), overlap


def hallucination_rate(
    slots: list,
    threshold: float = 0.10,
    sleep: float = 0.4,
    deep_topic: bool = False,
    verbose: bool = False,
) -> dict:
    """Compute the citation round-trip hallucination rate.

    Parameters
    ----------
    slots : list of {"pmid": str, "claim": str, ["candidate": str]}
        Reference slots produced by the system under audit.
    threshold : float
        On-topic overlap threshold passed to on_topic().
    sleep : float
        Seconds to sleep between NCBI calls (NCBI allows ~3 req/s without a key;
        0.4 s keeps a comfortable margin). Each slot makes 1 esummary call, plus
        1 efetch call when deep_topic=True.
    deep_topic : bool
        If True, also fetch the abstract via efetch and include it in the
        on-topic comparison text.
    verbose : bool
        Print per-slot progress to stderr.

    Returns
    -------
    dict with keys: total_slots, hallucinated_slots, rate, threshold,
    deep_topic, mwu_backend(n/a), per_slot (list of verdicts).
    Each per-slot verdict records: pmid, claim, exists, on_topic, overlap,
    title, journal, year, reason, hallucination(bool).
    """
    per_slot = []
    hallucinated = 0

    for i, slot in enumerate(slots):
        pmid = str(slot.get("pmid", "")).strip()
        claim = slot.get("claim", "") or ""
        candidate = slot.get("candidate")

        verdict = {
            "pmid": pmid,
            "candidate": candidate,
            "claim": claim,
            "exists": None,
            "on_topic": None,
            "overlap": None,
            "title": "",
            "journal": "",
            "year": "",
            "reason": "",
            "hallucination": False,
        }

        if not pmid:
            verdict.update(exists=False, reason="empty_pmid", hallucination=True)
            hallucinated += 1
            per_slot.append(verdict)
            if verbose:
                print(f"[{i + 1}/{len(slots)}] (no pmid) -> HALLUCINATION", file=sys.stderr)
            continue

        rec = _ncbi_esummary(pmid)
        if sleep:
            time.sleep(sleep)

        if rec is None:
            # Failure mode (a): PMID returns no real record.
            verdict.update(exists=False, reason="pmid_not_found", hallucination=True)
            hallucinated += 1
            per_slot.append(verdict)
            if verbose:
                print(f"[{i + 1}/{len(slots)}] PMID {pmid} not found -> HALLUCINATION", file=sys.stderr)
            continue

        title = rec.get("title", "") or ""
        journal = rec.get("fulljournalname") or rec.get("source", "") or ""
        pubdate = rec.get("pubdate", "") or rec.get("sortpubdate", "") or ""
        year = pubdate[:4] if pubdate else ""

        extra = ""
        if deep_topic:
            extra = _ncbi_efetch_abstract(pmid)
            if sleep:
                time.sleep(sleep)

        is_on, overlap = on_topic(claim, title, extra=extra, threshold=threshold)
        verdict.update(
            exists=True,
            on_topic=is_on,
            overlap=overlap,
            title=title,
            journal=journal,
            year=year,
        )
        if not is_on:
            # Failure mode (b): real record, off-topic for the claim.
            verdict.update(reason="off_topic", hallucination=True)
            hallucinated += 1
        else:
            verdict.update(reason="ok")

        per_slot.append(verdict)
        if verbose:
            tag = "OFF-TOPIC -> HALLUCINATION" if not is_on else "ok"
            ov = "n/a" if overlap is None else f"{overlap:.2f}"
            print(f"[{i + 1}/{len(slots)}] PMID {pmid} exists, overlap={ov} -> {tag}", file=sys.stderr)

    total = len(slots)
    rate = (hallucinated / total) if total else 0.0
    return {
        "total_slots": total,
        "hallucinated_slots": hallucinated,
        "rate": rate,
        "threshold": threshold,
        "deep_topic": deep_topic,
        "per_slot": per_slot,
    }


# ===========================================================================
# METRIC 2 -- ANTI-RETRIEVAL SEPARATION
# ===========================================================================
def _mwu_stdlib(x: list, y: list) -> tuple:
    """Two-sided Mann-Whitney U via normal approximation (stdlib only).

    Includes a tie correction in the variance and a continuity correction.
    Returns (U, p_two_sided). For tiny samples the normal approximation is
    only that -- an approximation -- which is why scipy's exact test is used
    when available. The report records which backend produced the p-value.
    """
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")

    combined = [(v, 0) for v in x] + [(v, 1) for v in y]
    combined.sort(key=lambda t: t[0])

    # Average ranks for ties.
    ranks = [0.0] * len(combined)
    i = 0
    tie_term = 0.0
    N = len(combined)
    while i < N:
        j = i
        while j < N and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0  # ranks are 1-based: positions i..j-1
        for k in range(i, j):
            ranks[k] = avg_rank
        t = j - i
        if t > 1:
            tie_term += t ** 3 - t
        i = j

    r1 = sum(ranks[k] for k in range(N) if combined[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    U = min(u1, u2)

    mu = n1 * n2 / 2.0
    sigma_sq = (n1 * n2 / 12.0) * ((N + 1) - tie_term / (N * (N - 1)))
    if sigma_sq <= 0:
        return U, float("nan")
    sigma = sigma_sq ** 0.5

    # Continuity correction toward the mean.
    z = (abs(U - mu) - 0.5) / sigma
    if z < 0:
        z = 0.0
    # Two-sided p from the standard normal survival function.
    p = 2.0 * _norm_sf(z)
    p = min(1.0, max(0.0, p))
    return U, p


def _norm_sf(z: float) -> float:
    """Upper-tail standard normal probability P(Z > z) via erfc (stdlib math)."""
    import math
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def anti_retrieval_separation(
    sdl_genes: list,
    retrieval_genes: list,
    scores: dict,
) -> dict:
    """Compare a mechanism-first ranking against a retrieval/lookup baseline.

    Parameters
    ----------
    sdl_genes : list of gene symbols (mechanism-first ranking under audit).
    retrieval_genes : list of gene symbols (database/lookup baseline).
    scores : dict gene -> association_score (e.g. Open Targets overall score).
        Genes absent from `scores` are dropped from the distribution test and
        listed under `missing_scores` for transparency.

    Returns
    -------
    dict with: n_sdl_scored, n_retrieval_scored, sdl_mean, retrieval_mean,
    mean_separation (sdl_mean - retrieval_mean), mwu_U, mwu_p, mwu_backend,
    jaccard (of the two gene SETS), intersection, union_size, missing_scores.
    """
    def _norm(g):
        return str(g).strip()

    sdl = [_norm(g) for g in sdl_genes if _norm(g)]
    ret = [_norm(g) for g in retrieval_genes if _norm(g)]
    # Build gene -> float score, skipping metadata keys (those starting with
    # '_') and any entry whose value is not coercible to a number. This keeps
    # the score map tolerant of an embedded "_comment" without silently
    # dropping real gene scores.
    norm_scores = {}
    for k, v in scores.items():
        key = _norm(k)
        if key.startswith("_"):
            continue
        try:
            norm_scores[key] = float(v)
        except (TypeError, ValueError):
            continue

    sdl_scores = [norm_scores[g] for g in sdl if g in norm_scores]
    ret_scores = [norm_scores[g] for g in ret if g in norm_scores]
    missing = sorted({g for g in sdl + ret if g not in norm_scores})

    sdl_mean = statistics.fmean(sdl_scores) if sdl_scores else float("nan")
    ret_mean = statistics.fmean(ret_scores) if ret_scores else float("nan")

    # Mann-Whitney U: scipy exact when available, else stdlib normal approx.
    if sdl_scores and ret_scores:
        if _HAVE_SCIPY:
            res = _scipy_mannwhitneyu(sdl_scores, ret_scores, alternative="two-sided")
            mwu_U, mwu_p = float(res.statistic), float(res.pvalue)
            backend = "scipy.stats.mannwhitneyu(exact/auto)"
        else:
            mwu_U, mwu_p = _mwu_stdlib(sdl_scores, ret_scores)
            backend = "stdlib_normal_approx(tie+continuity corrected)"
    else:
        mwu_U, mwu_p, backend = float("nan"), float("nan"), "not_computed(empty_group)"

    set_sdl, set_ret = set(sdl), set(ret)
    inter = sorted(set_sdl & set_ret)
    union = set_sdl | set_ret
    jaccard = (len(inter) / len(union)) if union else float("nan")

    return {
        "n_sdl_scored": len(sdl_scores),
        "n_retrieval_scored": len(ret_scores),
        "sdl_mean": sdl_mean,
        "retrieval_mean": ret_mean,
        "mean_separation": (sdl_mean - ret_mean)
        if not (sdl_mean != sdl_mean or ret_mean != ret_mean)
        else float("nan"),
        "mwu_U": mwu_U,
        "mwu_p": mwu_p,
        "mwu_backend": backend,
        "jaccard": jaccard,
        "intersection": inter,
        "union_size": len(union),
        "missing_scores": missing,
    }


# ===========================================================================
# METRIC 3 -- POSITION-BIAS RATE (LLM-judge A/B reversal)
# ===========================================================================
# Real schema observed in:
#   audit_data/stage1_dAMD/run1/step4_tournament2/
# Files: pair_<NN>_<a|b>_judge<N>.json  (2 directions x 3 judges = 6 per pair,
# 45 pairs = 270 files). Each file is UTF-8 JSON with at least:
#   {"pair_id": "04", "direction": "a", "judge_replicate": "1",
#    "verdict": "A"|"B", "winner_name": "...", ...}
# `verdict` names which PRESENTATION SLOT (A or B) won in that file's ordering.
# See examples/NOTES.md for the full field map and the derivation of 7/45.
_VERDICT_FILE_RE = re.compile(r"pair_(\w+?)_([ab])_judge(\w+)\.json$", re.IGNORECASE)

# Field names this loader will look for, in priority order, to read the winning
# slot letter from a verdict record. Kept explicit and inspectable.
_VERDICT_KEYS = ("verdict", "winner_slot", "winner", "choice", "selected")
_DIRECTION_KEYS = ("direction", "order", "ordering")


def _coerce_slot_letter(value) -> str | None:
    """Map a verdict value to 'A' or 'B' if possible, else None."""
    if value is None:
        return None
    s = str(value).strip().upper()
    if s in ("A", "B"):
        return s
    if s in ("SLOT_A", "CANDIDATE_A", "FIRST", "LEFT"):
        return "A"
    if s in ("SLOT_B", "CANDIDATE_B", "SECOND", "RIGHT"):
        return "B"
    return None


def _load_verdict_records(source: str) -> dict:
    """Load verdict records grouped by pair id.

    `source` may be:
      * a directory of pair_<NN>_<a|b>_judge<N>.json files (the real layout), or
      * a single JSON file that is either a list of verdict objects or a dict
        mapping pair_id -> list of verdict objects.

    Returns: dict pair_id -> list of verdict dicts, each guaranteed to carry a
    'slot' ('A'/'B') and a 'direction' ('a'/'b') when derivable.
    Raises ValueError if nothing parseable is found.
    """
    pairs: dict = {}

    def _push(pid, direction, slot, raw):
        pairs.setdefault(str(pid), []).append(
            {"direction": direction, "slot": slot, "raw": raw}
        )

    if os.path.isdir(source):
        files = sorted(glob.glob(os.path.join(source, "pair_*_judge*.json")))
        if not files:
            raise ValueError(
                f"No pair_*_judge*.json files found in directory: {source}"
            )
        for fp in files:
            m = _VERDICT_FILE_RE.search(os.path.basename(fp))
            if not m:
                continue
            pid, direction, _judge = m.group(1), m.group(2).lower(), m.group(3)
            try:
                rec = _read_json(fp)
            except (ValueError, OSError) as exc:
                raise ValueError(f"Failed to parse verdict file {fp}: {exc}") from exc
            slot = None
            for k in _VERDICT_KEYS:
                if k in rec:
                    slot = _coerce_slot_letter(rec[k])
                    if slot:
                        break
            # Prefer the direction encoded in the record if present & valid.
            rec_dir = None
            for k in _DIRECTION_KEYS:
                if k in rec and str(rec[k]).strip().lower() in ("a", "b"):
                    rec_dir = str(rec[k]).strip().lower()
                    break
            _push(pid, rec_dir or direction, slot, rec)
        return pairs

    # Single JSON file.
    data = _read_json(source)
    if isinstance(data, dict):
        items = []
        for pid, recs in data.items():
            if isinstance(recs, list):
                for rec in recs:
                    items.append((pid, rec))
            elif isinstance(recs, dict):
                items.append((pid, recs))
    elif isinstance(data, list):
        items = [(rec.get("pair_id"), rec) for rec in data]
    else:
        raise ValueError(
            "Verdicts JSON must be a list of records or a dict of pair_id->records."
        )

    for pid, rec in items:
        if pid is None:
            pid = rec.get("pair_id")
        slot = None
        for k in _VERDICT_KEYS:
            if k in rec:
                slot = _coerce_slot_letter(rec[k])
                if slot:
                    break
        direction = None
        for k in _DIRECTION_KEYS:
            if k in rec and str(rec[k]).strip().lower() in ("a", "b"):
                direction = str(rec[k]).strip().lower()
                break
        _push(pid, direction, slot, rec)
    return pairs


def position_bias(source: str) -> dict:
    """Compute the LLM-judge position-bias rate.

    A pair is FLAGGED when EVERY verdict for that pair (all judges, both
    orderings) names the SAME presentation slot ('A' or 'B'). When the winning
    slot is constant across the A-then-B and B-then-A orderings, the outcome was
    driven by position rather than by candidate identity. Pairs with any
    disagreement in slot letter -- including the healthy "consistent winner"
    pattern where the same real candidate wins as slot B in one order and slot A
    in the other -- are NOT flagged.

    Pointed at the paper's dAMD Run 1 data (step4_tournament2/) this returns
    7 of 45 pairs flagged (15.56%): pair_04, 07, 12, 19, 22, 25, 38.

    Returns
    -------
    dict with: total_pairs, flagged_pairs (count), rate, flagged (list of ids),
    per_pair (id -> {n_verdicts, slots, all_same, flagged}), skipped (pairs
    with no derivable slot for at least one verdict).
    """
    pairs = _load_verdict_records(source)

    per_pair = {}
    flagged = []
    skipped = []
    for pid in sorted(pairs):
        recs = pairs[pid]
        slots = [r["slot"] for r in recs]
        if any(s is None for s in slots) or not slots:
            skipped.append(pid)
            per_pair[pid] = {
                "n_verdicts": len(recs),
                "slots": slots,
                "all_same": None,
                "flagged": None,
                "note": "undeterminable_slot",
            }
            continue
        all_same = (len(set(slots)) == 1)
        per_pair[pid] = {
            "n_verdicts": len(recs),
            "slots": slots,
            "all_same": all_same,
            "flagged": all_same,
        }
        if all_same:
            flagged.append(pid)

    scored = [pid for pid in pairs if pid not in skipped]
    total = len(scored)
    rate = (len(flagged) / total) if total else 0.0
    return {
        "total_pairs": total,
        "flagged_pairs": len(flagged),
        "rate": rate,
        "flagged": flagged,
        "skipped": skipped,
        "per_pair": per_pair,
    }


# ===========================================================================
# REPORT RENDERING (fills REPORTING_TEMPLATE.md structure)
# ===========================================================================
def _fmt(x, nd=4):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        if x != x:  # NaN
            return "n/a"
        return f"{x:.{nd}f}"
    return str(x)


def render_report(results: dict, meta: dict) -> str:
    lines = []
    lines.append("# Credibility-Audit Triple Report")
    lines.append("")
    lines.append(f"- **System audited:** {meta.get('system', '(unspecified)')}")
    lines.append(f"- **Run / version:** {meta.get('version', '(unspecified)')}")
    lines.append(f"- **Audit date (UTC):** {meta.get('date', _utc_now())}")
    lines.append(f"- **Harness:** credibility_audit.py")
    lines.append("")

    # --- Metric 1 ---
    lines.append("## 1. Hallucination rate (citation round-trip)")
    h = results.get("hallucination")
    if h is None:
        lines.append("_Not computed (no `--citations` input provided)._")
    else:
        lines.append(f"- Reference slots evaluated: **{h['total_slots']}**")
        lines.append(f"- Hallucinated slots: **{h['hallucinated_slots']}**")
        lines.append(
            f"  (non-existent PMIDs + off-topic real records, "
            f"on-topic threshold = {h['threshold']}, deep_topic = {h['deep_topic']})"
        )
        lines.append(f"- **Hallucination rate = {h['rate'] * 100:.1f}%**")
        not_found = sum(1 for s in h["per_slot"] if s["exists"] is False and s["reason"] != "off_topic")
        off_topic = sum(1 for s in h["per_slot"] if s["reason"] == "off_topic")
        lines.append(f"  - of which PMID-not-found: {not_found}; off-topic: {off_topic}")
        lines.append(
            f"- _Interpretation:_ fraction of cited references that do not exist "
            f"or do not support their claim. Lower is better; report the "
            f"as-discovered rate alongside any grounded/repaired rate."
        )
    lines.append("")

    # --- Metric 2 ---
    lines.append("## 2. Anti-retrieval separation")
    a = results.get("anti_retrieval")
    if a is None:
        lines.append("_Not computed (no `--sdl-genes/--retrieval-genes/--ot-scores` input provided)._")
    else:
        lines.append(
            f"- Mechanism-first mean score: **{_fmt(a['sdl_mean'])}** "
            f"(n = {a['n_sdl_scored']})"
        )
        lines.append(
            f"- Retrieval-baseline mean score: **{_fmt(a['retrieval_mean'])}** "
            f"(n = {a['n_retrieval_scored']})"
        )
        lines.append(f"- Mean-score separation (mechanism - retrieval): **{_fmt(a['mean_separation'])}**")
        lines.append(f"- Mann-Whitney U: U = {_fmt(a['mwu_U'], 2)}, **p = {_fmt(a['mwu_p'])}**")
        lines.append(f"  (backend: {a['mwu_backend']})")
        lines.append(f"- Jaccard overlap of gene SETS: **{_fmt(a['jaccard'])}** "
                     f"(|A∩B| = {len(a['intersection'])}, |A∪B| = {a['union_size']})")
        if a["missing_scores"]:
            lines.append(f"- Genes lacking an association score (excluded from test): "
                         f"{', '.join(a['missing_scores'])}")
        lines.append(
            "- _Interpretation:_ low Jaccard + a significant score difference "
            "indicates the system is not merely reproducing a database lookup. "
            "A high Jaccard would suggest retrieval, not mechanism-first discovery."
        )
    lines.append("")

    # --- Metric 3 ---
    lines.append("## 3. Position-bias rate (LLM-judge A/B reversal)")
    p = results.get("position_bias")
    if p is None:
        lines.append("_Not computed (no `--verdicts` input provided)._")
    else:
        lines.append(f"- Pairs scored: **{p['total_pairs']}**")
        lines.append(f"- Flagged (same slot wins in every verdict): **{p['flagged_pairs']}**")
        lines.append(f"- **Position-bias rate = {p['rate'] * 100:.2f}%**")
        if p["flagged"]:
            lines.append(f"  - Flagged pairs: {', '.join('pair_' + x for x in p['flagged'])}")
        if p["skipped"]:
            lines.append(f"  - Skipped (undeterminable slot): {', '.join(p['skipped'])}")
        lines.append(
            "- _Interpretation:_ fraction of A/B pairs whose winner is fixed by "
            "presentation order rather than candidate identity. Lower is better; "
            "flagged pairs should be tie-broken or excluded before final ranking."
        )
    lines.append("")

    lines.append("---")
    lines.append(
        '_Generated by the credibility-audit harness for "A measurable '
        'trustworthiness audit for AI-driven scientific discovery", '
        "Sheng J. et al. (2026)._"
    )
    lines.append("")
    return "\n".join(lines)


# ===========================================================================
# CLI
# ===========================================================================
def _parse_gene_list(arg: str | None) -> list:
    if not arg:
        return []
    return [g.strip() for g in arg.split(",") if g.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="credibility_audit.py",
        description="Compute the credibility-audit triple "
                    "(hallucination rate, anti-retrieval separation, position-bias rate) "
                    "on any autonomous-discovery system's output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--verdicts", metavar="DIR|JSON",
                    help="Directory of pair_<NN>_<a|b>_judge<N>.json files, or a "
                         "single verdicts JSON (list of records or pair_id->records). "
                         "Triggers the position-bias metric.")
    ap.add_argument("--citations", metavar="JSON",
                    help="JSON list of {pmid, claim[, candidate]} slots. "
                         "Triggers the hallucination metric (queries NCBI).")
    ap.add_argument("--sdl-genes", metavar="a,b,c",
                    help="Comma-separated mechanism-first gene ranking.")
    ap.add_argument("--retrieval-genes", metavar="x,y,z",
                    help="Comma-separated retrieval/lookup baseline gene ranking.")
    ap.add_argument("--ot-scores", metavar="JSON",
                    help="JSON dict gene->association_score (e.g. Open Targets). "
                         "Required for the anti-retrieval metric.")
    ap.add_argument("--threshold", type=float, default=0.10,
                    help="On-topic overlap threshold for the hallucination "
                         "heuristic (default 0.10).")
    ap.add_argument("--sleep", type=float, default=0.4,
                    help="Seconds between NCBI calls (default 0.4; ~3 req/s limit).")
    ap.add_argument("--deep-topic", action="store_true",
                    help="Also fetch abstracts via efetch for the on-topic check "
                         "(slower; doubles NCBI calls).")
    ap.add_argument("--out", metavar="report.md",
                    help="Write the Markdown report here (also printed to stdout).")
    ap.add_argument("--json-out", metavar="results.json",
                    help="Write the full machine-readable results JSON here.")
    ap.add_argument("--system", default="(unspecified)",
                    help="Name of the system under audit (report metadata).")
    ap.add_argument("--version", default="(unspecified)",
                    help="Run/version label (report metadata).")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress per-slot NCBI progress on stderr.")
    args = ap.parse_args(argv)

    results = {}

    # --- Position-bias ---
    if args.verdicts:
        results["position_bias"] = position_bias(args.verdicts)

    # --- Anti-retrieval ---
    if args.sdl_genes or args.retrieval_genes or args.ot_scores:
        if not (args.sdl_genes and args.retrieval_genes and args.ot_scores):
            ap.error("--sdl-genes, --retrieval-genes and --ot-scores must be "
                     "provided together for the anti-retrieval metric.")
        scores = _read_json(args.ot_scores)
        if not isinstance(scores, dict):
            ap.error("--ot-scores must be a JSON object (gene -> score).")
        results["anti_retrieval"] = anti_retrieval_separation(
            _parse_gene_list(args.sdl_genes),
            _parse_gene_list(args.retrieval_genes),
            scores,
        )

    # --- Hallucination ---
    if args.citations:
        slots = _read_json(args.citations)
        if not isinstance(slots, list):
            ap.error("--citations must be a JSON list of {pmid, claim} objects.")
        results["hallucination"] = hallucination_rate(
            slots,
            threshold=args.threshold,
            sleep=args.sleep,
            deep_topic=args.deep_topic,
            verbose=not args.quiet,
        )

    if not results:
        ap.print_help()
        print("\nNo metric inputs provided. Supply at least one of "
              "--verdicts / --citations / (--sdl-genes + --retrieval-genes + --ot-scores).",
              file=sys.stderr)
        return 2

    meta = {"system": args.system, "version": args.version, "date": _utc_now()}
    report = render_report(results, meta)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"[written] {args.out}", file=sys.stderr)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"meta": meta, "results": results}, fh, indent=2, ensure_ascii=False)
        print(f"[written] {args.json_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
