#!/usr/bin/env python3
"""
gen2_pubmed.py -- retrieval-arm context fetch (construction decision C6
fallback, activated by the certification probe 2026-09-04: the GLM Coding
Plan endpoint ACCEPTS a tools block (billed ~2.5K prompt tokens) but does not
execute it -- the model itself states "I don't have access to a web search
tool in this conversation"; raw archive certify/retrieval/forced_search/*).

"Retrieval tools enabled" (prereg §5.2) is therefore implemented as
deterministic PubMed context injection: a FIXED query per disease, fetched
ONCE per retrieval-arm run (logged with SHA-256 and fetch UTC), injected into
step-1 bucket and step-3 dossier prompts.

The frozen queries are deliberately neutral (MeSH term, best-match sort) --
they must not lead toward any pre-registered axis.
"""

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request

NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MAILTO = os.environ.get("CREDAUDIT_MAILTO", "research@example.org")

FROZEN_QUERIES = {
    "dAMD": {
        "term": '"Macular Degeneration"[MeSH Terms]',
        "retmax": 20,
        "note": "fixed neutral query; best-match default sort",
    },
    "ALS": {
        "term": '"Amyotrophic Lateral Sclerosis"[MeSH Terms]',
        "retmax": 20,
        "note": "fixed neutral query; best-match default sort",
    },
}


def _get(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "gen2-harness/%s" % MAILTO)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def fetch_context(disease, out_path, max_tries=8):
    """Fetch once per run; write {utc, query, records[], sha256} to out_path.

    Robust to transient SSL EOF resets on the NCBI path (observed 2026-09-04):
    8 tries with 10s-capped linear backoff + a fresh connection each try.
    """
    if os.path.exists(out_path):
        return json.load(open(out_path, encoding="utf-8"))
    q = FROZEN_QUERIES[disease]
    term = urllib.parse.quote(q["term"])
    last = None
    for attempt in range(1, max_tries + 1):
        try:
            es = _get("%sesearch.fcgi?db=pubmed&retmode=json&retmax=%d&term=%s"
                      % (NCBI, q["retmax"], term))
            ids = ",".join(es["esearchresult"]["idlist"])
            time.sleep(0.4)
            su = _get("%sesummary.fcgi?db=pubmed&retmode=json&id=%s" % (NCBI, ids))
            records = []
            for pid in es["esearchresult"]["idlist"]:
                it = su.get("result", {}).get(pid, {})
                records.append({
                    "pmid": pid,
                    "title": it.get("title", ""),
                    "journal": it.get("source", ""),
                    "year": (it.get("pubdate") or "")[:4],
                })
            ctx = {
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "disease": disease, "query": q,
                "n_records": len(records), "records": records,
                "note": ("Retrieval-arm context. Fetch is deterministic-input "
                         "but best-match ranking reflects the live index at "
                         "fetch time; fetch UTC and full record list are "
                         "frozen per run."),
            }
            ctx["records_sha256"] = hashlib.sha256(
                json.dumps(records, sort_keys=True).encode()).hexdigest()
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            tmp = out_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(ctx, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, out_path)
            return ctx
        except Exception as e:                                  # noqa: BLE001
            last = e
            time.sleep(min(10.0, 3.0 * attempt))
    raise RuntimeError("PubMed context fetch failed after %d tries: %r"
                       % (max_tries, last))


def context_block(ctx):
    """Render the injection block for step-1/step-3 prompts."""
    lines = ["Retrieved literature context (PubMed, fetched %s, query: %s):"
             % (ctx["utc"], ctx["query"]["term"])]
    for r in ctx["records"]:
        lines.append("- [%s] %s (%s)" % (r["pmid"], r["title"], r["year"]))
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    dis = sys.argv[1] if len(sys.argv) > 1 else "dAMD"
    ctx = fetch_context(dis, os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "runs", "_probe_retrieval_%s.json" % dis))
    print("fetched %d records | sha %s" % (ctx["n_records"],
                                           ctx["records_sha256"][:12]))
    for r in ctx["records"][:5]:
        print("  [%s] %s (%s)" % (r["pmid"], r["title"][:80], r["year"]))
