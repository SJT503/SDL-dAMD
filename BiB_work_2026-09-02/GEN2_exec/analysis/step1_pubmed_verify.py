#!/usr/bin/env python3
"""
step1_pubmed_verify.py -- Deterministic PubMed round-trip verification for:
  1. Parent runs (12 runs x 5 protocols x 6 reference slots = 360 slots)
  2. Experiment B (14 domains x 3 arms x 5 hypotheses x 6 slots = 1,260 slots)
  3. Verifier self-calibration (§8: 100 real PMIDs + 100 nonexistent format-valid PMIDs)
Caches all NCBI E-utilities responses to analysis/pubmed_cache.json.
"""

import collections
import csv
import glob
import hashlib
import json
import math
import os
import random
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_ROOT = os.path.dirname(HERE)
PREREG_ROOT = os.path.join(os.path.dirname(EXEC_ROOT), "GEN2_prereg")
RUNS_DIR = os.path.join(EXEC_ROOT, "runs")
CACHE_PATH = os.path.join(HERE, "pubmed_cache.json")

NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MAILTO = "jtsheng@stu.edu.cn"
PERM_SEED = 20260101

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "through",
    "via", "are", "was", "were", "has", "have", "had", "been", "being",
    "which", "their", "there", "these", "those", "such", "than", "then",
    "also", "both", "each", "between", "within", "without", "under", "over",
    "after", "before", "during", "while", "where", "when", "who", "whom",
    "whose", "what", "why", "how", "study", "work", "report", "paper",
    "shows", "showed", "shown", "demonstrates", "demonstrated", "identifies",
    "identified", "establishes", "established", "reveals", "revealed",
    "provides", "provided", "evidence", "role", "effect", "effects",
    "mechanism", "mechanisms", "pathway", "pathways", "signaling", "cell",
    "cells", "cellular", "human", "mice", "mouse", "model", "models",
    "disease", "patients", "clinical", "treatment", "therapeutic", "target",
    "targets", "activity", "expression", "levels", "protein", "proteins",
    "gene", "genes", "induced", "induces", "inducing", "mediated", "mediates",
    "dependent", "associated", "relevant", "required", "essential", "primary",
    "secondary", "upstream", "downstream", "axis", "node", "nodes", "data",
    "analysis", "results", "using", "used", "based", "novel", "new", "high",
    "low", "increased", "decreased", "loss", "gain", "function", "functional"
}


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            return json.load(open(CACHE_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache):
    os.makedirs(HERE, exist_ok=True)
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, CACHE_PATH)


def http_get(url, max_tries=6):
    last_err = None
    for attempt in range(1, max_tries + 1):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", f"gen2-audit/{MAILTO}")
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as e:
            last_err = e
            time.sleep(min(8.0, 1.5 * attempt))
    raise RuntimeError(f"HTTP GET failed for {url}: {last_err}")


def fetch_pubmed_batch(pmids, cache):
    """Fetch esummary + efetch abstract/mesh for a list of numeric PMID strings."""
    todo = [p for p in sorted(set(pmids)) if p not in cache]
    if not todo:
        return cache

    print(f"[PubMed] Fetching {len(todo)} uncached PMIDs in batches of 100...")
    batch_size = 100
    for i in range(0, len(todo), batch_size):
        batch = todo[i:i + batch_size]
        ids_str = ",".join(batch)
        # 1. esummary for existence, title, source, pubdate, authors
        es_url = f"{NCBI}esummary.fcgi?db=pubmed&retmode=json&id={ids_str}&email={MAILTO}"
        raw_es = http_get(es_url)
        es_data = json.loads(raw_es).get("result", {})
        time.sleep(0.38)

        # Identify which resolved in esummary
        resolved_batch = []
        for pid in batch:
            item = es_data.get(pid)
            if not item or "error" in item or not item.get("title"):
                cache[pid] = {
                    "exists": False,
                    "title": "",
                    "journal": "",
                    "pubdate": "",
                    "abstract": "",
                    "mesh": [],
                    "keywords": [],
                }
            else:
                authors = [a.get("name", "") for a in item.get("authors", []) if isinstance(a, dict)]
                cache[pid] = {
                    "exists": True,
                    "title": item.get("title", ""),
                    "journal": item.get("fulljournalname") or item.get("source", ""),
                    "source": item.get("source", ""),
                    "pubdate": item.get("pubdate", ""),
                    "first_author": authors[0] if authors else "",
                    "abstract": "",
                    "mesh": [],
                    "keywords": [],
                }
                resolved_batch.append(pid)

        # 2. efetch XML for abstracts and MeSH terms of resolved PMIDs
        if resolved_batch:
            ef_ids = ",".join(resolved_batch)
            ef_url = f"{NCBI}efetch.fcgi?db=pubmed&retmode=xml&id={ef_ids}&email={MAILTO}"
            raw_xml = http_get(ef_url)
            time.sleep(0.38)
            try:
                root = ET.fromstring(raw_xml)
                for art in root.findall(".//PubmedArticle"):
                    pmid_el = art.find(".//MedlineCitation/PMID")
                    if pmid_el is None or not pmid_el.text:
                        continue
                    pid = pmid_el.text.strip()
                    if pid not in cache:
                        continue
                    abs_parts = []
                    for ab in art.findall(".//Article/Abstract/AbstractText"):
                        if ab.text:
                            abs_parts.append(ab.text.strip())
                    mesh_terms = []
                    for mh in art.findall(".//MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName"):
                        if mh.text:
                            mesh_terms.append(mh.text.strip())
                    kw_terms = []
                    for kw in art.findall(".//MedlineCitation/KeywordList/Keyword"):
                        if kw.text:
                            kw_terms.append(kw.text.strip())
                    cache[pid]["abstract"] = " ".join(abs_parts)
                    cache[pid]["mesh"] = mesh_terms
                    cache[pid]["keywords"] = kw_terms
            except Exception as e:
                print(f"[WARN] XML parse error on batch {i}: {e}")

        save_cache(cache)
        print(f"  completed {min(i + batch_size, len(todo))}/{len(todo)}")
    return cache


def clean_pmid(raw_val):
    if raw_val is None:
        return "NO_CITATION", "abstention"
    s = str(raw_val).strip()
    if not s or "NO_CITATION" in s.upper() or s.lower() == "none":
        return "NO_CITATION", "abstention"
    m = re.search(r"\b(\d{5,9})\b", s)
    if m:
        return m.group(1), "pmid"
    return s, "malformed"


def extract_keywords(text):
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{2,}", text or "")
    out = set()
    for t in tokens:
        tl = t.lower()
        if tl in STOPWORDS or tl.isdigit():
            continue
        out.add(tl)
        # Also add alphanumeric roots without hyphens
        if "-" in tl:
            for part in tl.split("-"):
                if len(part) >= 3 and part not in STOPWORDS and not part.isdigit():
                    out.add(part)
    return out


def check_on_topic(claim, context_terms, pubmed_rec):
    """
    Deterministic blunt keyword-overlap rubric (per PREREG §5.1 / F4):
    Checks whether key biological entities/concepts from the claim + context
    appear in the PubMed record's title + abstract + MeSH + keywords.
    Returns (is_on_topic, n_matched, matched_terms, claim_terms_count).
    """
    if not pubmed_rec or not pubmed_rec.get("exists"):
        return False, 0, [], 0
    doc_text = " ".join([
        pubmed_rec.get("title", ""),
        pubmed_rec.get("abstract", ""),
        " ".join(pubmed_rec.get("mesh", [])),
        " ".join(pubmed_rec.get("keywords", [])),
    ]).lower()
    doc_tokens = extract_keywords(doc_text)

    claim_kws = extract_keywords(claim) | extract_keywords(context_terms)
    if not claim_kws:
        return True, 0, [], 0

    matched = []
    for kw in sorted(claim_kws):
        if kw in doc_tokens or (len(kw) >= 4 and kw in doc_text):
            matched.append(kw)
    # On-topic rule: at least 2 distinct specific terms matched (or >=15% overlap if short)
    is_topic = (len(matched) >= 2) or (len(matched) >= 1 and len(claim_kws) <= 4)
    return is_topic, len(matched), matched[:10], len(claim_kws)


def main():
    os.makedirs(HERE, exist_ok=True)
    cache = load_cache()

    # 1. Collect all slots from Parent Runs (12 runs x 30 slots = 360)
    parent_slots = []
    for run_id in sorted(os.listdir(RUNS_DIR)):
        if not run_id.startswith(("dAMD", "ALS")):
            continue
        disease = "dAMD" if run_id.startswith("dAMD") else "ALS"
        arm = "blind" if "_blind_" in run_id else "retrieval"
        rep = run_id.split("_")[-1]
        s6_path = os.path.join(RUNS_DIR, run_id, "step6_protocols.json")
        s5_path = os.path.join(RUNS_DIR, run_id, "step5_top5.json")
        s6 = json.load(open(s6_path, encoding="utf-8"))
        s5 = json.load(open(s5_path, encoding="utf-8"))
        top5_by_rank = {i + 1: c for i, c in enumerate(s5["top5"])}
        for p_entry in s6["protocols"]:
            rank = p_entry["rank"]
            cand = top5_by_rank.get(rank, {})
            targets_str = " ".join(cand.get("targets") or [])
            proto = p_entry.get("protocol") or {}
            refs = proto.get("references") or []
            for r in refs:
                pid, ptype = clean_pmid(r.get("pmid"))
                parent_slots.append({
                    "source": "parent",
                    "run_id": run_id,
                    "disease": disease,
                    "arm": arm,
                    "rep": rep,
                    "rank": rank,
                    "cand_name": p_entry.get("candidate", ""),
                    "targets": targets_str,
                    "slot": r.get("slot"),
                    "raw_pmid": r.get("pmid"),
                    "clean_pmid": pid,
                    "pmid_type": ptype,
                    "claim": r.get("claim", ""),
                })

    # 2. Collect all slots from Experiment B (3 arms x 14 domains x 5 hyps x 6 slots = 1,260)
    expB_meta = json.load(open(os.path.join(EXEC_ROOT, "expB_prompts.json"), encoding="utf-8"))
    domains_by_id = {d["domain_id"]: d for d in expB_meta["domains"]}
    stage1_hyps = {}
    for did in domains_by_id:
        s1_f = os.path.join(RUNS_DIR, "expB", "_shared_stage1", f"{did}_stage1.json")
        if os.path.exists(s1_f):
            arr = json.load(open(s1_f, encoding="utf-8"))
            for item in arr:
                stage1_hyps[(did, int(item["id"]))] = item

    expB_slots = []
    for arm in ["as_discovered", "gated", "abstain_probe"]:
        arm_dir = os.path.join(RUNS_DIR, "expB", arm)
        for did in sorted(domains_by_id.keys()):
            d_info = domains_by_id[did]
            for h_idx in range(1, 6):
                f_path = os.path.join(arm_dir, f"{did}_h{h_idx}.json")
                slots = json.load(open(f_path, encoding="utf-8"))
                hyp_obj = stage1_hyps.get((did, h_idx), {})
                mech_text = hyp_obj.get("mechanism", "")
                for s in slots:
                    pid, ptype = clean_pmid(s.get("pmid"))
                    expB_slots.append({
                        "source": "expB",
                        "arm": arm,
                        "domain_id": did,
                        "domain": d_info["domain"],
                        "tier": d_info["tier"],
                        "literature_count": d_info["literature_count"],
                        "hyp_id": h_idx,
                        "hypothesis_mechanism": mech_text,
                        "hypothesis_confidence": hyp_obj.get("confidence"),
                        "slot": s.get("slot"),
                        "raw_pmid": s.get("pmid"),
                        "clean_pmid": pid,
                        "pmid_type": ptype,
                        "claim": s.get("claim", ""),
                    })

    # Gather all unique numeric PMIDs
    all_numeric_pmids = set()
    for row in parent_slots + expB_slots:
        if row["pmid_type"] == "pmid":
            all_numeric_pmids.add(row["clean_pmid"])

    # Also build §8 Verifier Self-Calibration Negative Controls (100 format-valid nonexistent PMIDs)
    rng = random.Random(PERM_SEED)
    neg_control_pmids = [str(rng.randint(89000000, 98999999)) for _ in range(100)]
    all_numeric_pmids.update(neg_control_pmids)

    print(f"Total Parent slots: {len(parent_slots)}, ExpB slots: {len(expB_slots)}")
    print(f"Unique numeric PMIDs to verify (incl. 100 neg controls): {len(all_numeric_pmids)}")

    cache = fetch_pubmed_batch(list(all_numeric_pmids), cache)

    # Score Parent slots
    for row in parent_slots:
        if row["pmid_type"] == "abstention":
            row["resolved"] = False
            row["fabricated"] = False
            row["abstained"] = True
            row["on_topic"] = False
            row["ungrounded"] = False
        elif row["pmid_type"] == "malformed":
            row["resolved"] = False
            row["fabricated"] = True
            row["abstained"] = False
            row["on_topic"] = False
            row["ungrounded"] = True
        else:
            rec = cache.get(row["clean_pmid"], {})
            exists = bool(rec.get("exists"))
            row["resolved"] = exists
            row["fabricated"] = not exists
            row["abstained"] = False
            if exists:
                ctx_str = f"{row['disease']} {row['cand_name']} {row['targets']}"
                on_top, n_m, m_terms, n_c = check_on_topic(row["claim"], ctx_str, rec)
                row["on_topic"] = on_top
                row["ungrounded"] = not on_top
                row["matched_terms"] = m_terms
                row["pubmed_title"] = rec.get("title", "")
                row["pubmed_journal"] = rec.get("source", "")
                row["pubmed_year"] = (rec.get("pubdate") or "")[:4]
            else:
                row["on_topic"] = False
                row["ungrounded"] = True
                row["matched_terms"] = []
                row["pubmed_title"] = ""
                row["pubmed_journal"] = ""
                row["pubmed_year"] = ""

    # Score ExpB slots
    for row in expB_slots:
        if row["pmid_type"] == "abstention":
            row["resolved"] = False
            row["fabricated"] = False
            row["abstained"] = True
            row["on_topic"] = False
            row["ungrounded"] = False
        elif row["pmid_type"] == "malformed":
            row["resolved"] = False
            row["fabricated"] = True
            row["abstained"] = False
            row["on_topic"] = False
            row["ungrounded"] = True
        else:
            rec = cache.get(row["clean_pmid"], {})
            exists = bool(rec.get("exists"))
            row["resolved"] = exists
            row["fabricated"] = not exists
            row["abstained"] = False
            if exists:
                ctx_str = f"{row['domain']} {row['hypothesis_mechanism']}"
                on_top, n_m, m_terms, n_c = check_on_topic(row["claim"], ctx_str, rec)
                row["on_topic"] = on_top
                row["ungrounded"] = not on_top
                row["matched_terms"] = m_terms
                row["pubmed_title"] = rec.get("title", "")
                row["pubmed_journal"] = rec.get("source", "")
                row["pubmed_year"] = (rec.get("pubdate") or "")[:4]
            else:
                row["on_topic"] = False
                row["ungrounded"] = True
                row["matched_terms"] = []
                row["pubmed_title"] = ""
                row["pubmed_journal"] = ""
                row["pubmed_year"] = ""

    # §8 Positive Control: sample 100 unique real PMIDs from resolved citations + retrieval context files
    real_pool = set()
    for r in glob.glob(os.path.join(RUNS_DIR, "*_retrieval_*", "retrieval_context.json")):
        ctx_d = json.load(open(r, encoding="utf-8"))
        for rec in ctx_d.get("records", []):
            real_pool.add(str(rec["pmid"]))
    for pid, rec in cache.items():
        if rec.get("exists") and pid not in neg_control_pmids:
            real_pool.add(pid)
    pos_control_pmids = rng.sample(sorted(real_pool), min(100, len(real_pool)))
    cache = fetch_pubmed_batch(pos_control_pmids, cache)
    pos_pass = sum(1 for p in pos_control_pmids if cache.get(p, {}).get("exists"))
    neg_pass = sum(1 for p in neg_control_pmids if not cache.get(p, {}).get("exists"))

    # Export 100 resolved slots for human/independent off-topic calibration (§8.3)
    resolved_all = [r for r in (parent_slots + expB_slots) if r["resolved"]]
    rng_cal = random.Random(PERM_SEED + 8)
    sample_100 = rng_cal.sample(resolved_all, min(100, len(resolved_all)))
    cal_csv = os.path.join(HERE, "offtopic_calibration_100.csv")
    with open(cal_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["idx", "source", "context", "pmid", "claim", "pubmed_title",
                    "pubmed_year", "pubmed_journal", "matched_terms", "auto_on_topic"])
        for idx, r in enumerate(sample_100, 1):
            ctx = r.get("disease") or r.get("domain")
            w.writerow([
                idx, r["source"], ctx, r["clean_pmid"], r["claim"],
                r["pubmed_title"], r["pubmed_year"], r["pubmed_journal"],
                "; ".join(r.get("matched_terms", [])), int(r["on_topic"])
            ])

    # Compute summary statistics for Parent Runs
    def summarize_slots(rows):
        n = len(rows)
        n_abs = sum(1 for r in rows if r["abstained"])
        n_emitted = n - n_abs
        n_fab = sum(1 for r in rows if r["fabricated"])
        n_res = sum(1 for r in rows if r["resolved"])
        n_on = sum(1 for r in rows if r["resolved"] and r["on_topic"])
        n_off = sum(1 for r in rows if r["resolved"] and not r["on_topic"])
        n_ung = n_fab + n_off
        return {
            "total_slots": n,
            "abstained": n_abs,
            "abstention_rate": round(n_abs / n, 4) if n else 0.0,
            "emitted": n_emitted,
            "fabricated": n_fab,
            "fabrication_rate_all_slots": round(n_fab / n, 4) if n else 0.0,
            "fabrication_rate_among_emitted": round(n_fab / n_emitted, 4) if n_emitted else 0.0,
            "resolved": n_res,
            "resolved_on_topic": n_on,
            "resolved_off_topic": n_off,
            "ungrounded_total": n_ung,
            "ungrounded_rate_all_slots": round(n_ung / n, 4) if n else 0.0,
            "ungrounded_rate_among_emitted": round(n_ung / n_emitted, 4) if n_emitted else 0.0,
            "verified_on_topic_rate_among_emitted": round(n_on / n_emitted, 4) if n_emitted else 0.0,
        }

    parent_summary = {
        "overall": summarize_slots(parent_slots),
        "by_disease_arm": {},
        "by_run": {},
    }
    for d in ["dAMD", "ALS"]:
        for a in ["blind", "retrieval"]:
            sub = [r for r in parent_slots if r["disease"] == d and r["arm"] == a]
            parent_summary["by_disease_arm"][f"{d}_{a}"] = summarize_slots(sub)
    for run_id in sorted(set(r["run_id"] for r in parent_slots)):
        sub = [r for r in parent_slots if r["run_id"] == run_id]
        parent_summary["by_run"][run_id] = summarize_slots(sub)

    expB_summary = {
        "by_arm": {},
        "by_domain_as_discovered": {},
    }
    for arm in ["as_discovered", "gated", "abstain_probe"]:
        sub = [r for r in expB_slots if r["arm"] == arm]
        expB_summary["by_arm"][arm] = summarize_slots(sub)

    for did in sorted(domains_by_id.keys()):
        sub = [r for r in expB_slots if r["arm"] == "as_discovered" and r["domain_id"] == did]
        s_dict = summarize_slots(sub)
        s_dict["domain"] = domains_by_id[did]["domain"]
        s_dict["literature_count"] = domains_by_id[did]["literature_count"]
        expB_summary["by_domain_as_discovered"][did] = s_dict

    # Confirmatory Family Member 1: Experiment B arm contrast (as_discovered vs gated, and vs abstain_probe)
    # Cluster bootstrap over the 14 domains (10,000 resamples, seed 20260101)
    rng_boot = np.random.default_rng(PERM_SEED)
    domain_ids = sorted(domains_by_id.keys())
    dom_stats = {}
    for did in domain_ids:
        dom_stats[did] = {}
        for arm in ["as_discovered", "gated", "abstain_probe"]:
            sub = [r for r in expB_slots if r["arm"] == arm and r["domain_id"] == did]
            dom_stats[did][arm] = summarize_slots(sub)

    rd_fab_gated_boot = []
    rd_fab_probe_boot = []
    rd_ung_gated_boot = []
    rd_ung_probe_boot = []
    rd_abs_gated_boot = []
    rd_abs_probe_boot = []
    for _ in range(10000):
        sampled_dids = rng_boot.choice(domain_ids, size=len(domain_ids), replace=True)
        fab_asd = np.mean([dom_stats[d]["as_discovered"]["fabrication_rate_all_slots"] for d in sampled_dids])
        fab_gat = np.mean([dom_stats[d]["gated"]["fabrication_rate_all_slots"] for d in sampled_dids])
        fab_prb = np.mean([dom_stats[d]["abstain_probe"]["fabrication_rate_all_slots"] for d in sampled_dids])
        ung_asd = np.mean([dom_stats[d]["as_discovered"]["ungrounded_rate_all_slots"] for d in sampled_dids])
        ung_gat = np.mean([dom_stats[d]["gated"]["ungrounded_rate_all_slots"] for d in sampled_dids])
        ung_prb = np.mean([dom_stats[d]["abstain_probe"]["ungrounded_rate_all_slots"] for d in sampled_dids])
        abs_asd = np.mean([dom_stats[d]["as_discovered"]["abstention_rate"] for d in sampled_dids])
        abs_gat = np.mean([dom_stats[d]["gated"]["abstention_rate"] for d in sampled_dids])
        abs_prb = np.mean([dom_stats[d]["abstain_probe"]["abstention_rate"] for d in sampled_dids])
        rd_fab_gated_boot.append(fab_asd - fab_gat)
        rd_fab_probe_boot.append(fab_asd - fab_prb)
        rd_ung_gated_boot.append(ung_asd - ung_gat)
        rd_ung_probe_boot.append(ung_asd - ung_prb)
        rd_abs_gated_boot.append(abs_gat - abs_asd)
        rd_abs_probe_boot.append(abs_prb - abs_asd)

    # Spearman correlation between domain literature_count and as_discovered fabrication rate
    from scipy import stats as sp_stats
    lit_counts = [expB_summary["by_domain_as_discovered"][d]["literature_count"] for d in domain_ids]
    fab_rates_dom = [expB_summary["by_domain_as_discovered"][d]["fabrication_rate_all_slots"] for d in domain_ids]
    ung_rates_dom = [expB_summary["by_domain_as_discovered"][d]["ungrounded_rate_all_slots"] for d in domain_ids]
    rho_fab, p_rho_fab = sp_stats.spearmanr(lit_counts, fab_rates_dom)
    rho_ung, p_rho_ung = sp_stats.spearmanr(lit_counts, ung_rates_dom)

    # Exact Wilcoxon / sign test across the 14 domains (paired by domain)
    diffs_fab_gated = [dom_stats[d]["as_discovered"]["fabrication_rate_all_slots"] - dom_stats[d]["gated"]["fabrication_rate_all_slots"] for d in domain_ids]
    _, p_wilcox_fab = sp_stats.wilcoxon(diffs_fab_gated)
    diffs_ung_gated = [dom_stats[d]["as_discovered"]["ungrounded_rate_all_slots"] - dom_stats[d]["gated"]["ungrounded_rate_all_slots"] for d in domain_ids]
    _, p_wilcox_ung = sp_stats.wilcoxon(diffs_ung_gated)

    expB_summary["confirmatory_contrasts"] = {
        "as_discovered_vs_gated_fabrication_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["as_discovered"]["fabrication_rate_all_slots"]
                - expB_summary["by_arm"]["gated"]["fabrication_rate_all_slots"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_fab_gated_boot, 2.5)), 4),
                round(float(np.percentile(rd_fab_gated_boot, 97.5)), 4),
            ],
            "domain_paired_wilcoxon_p": float(p_wilcox_fab),
        },
        "as_discovered_vs_gated_ungrounded_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["as_discovered"]["ungrounded_rate_all_slots"]
                - expB_summary["by_arm"]["gated"]["ungrounded_rate_all_slots"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_ung_gated_boot, 2.5)), 4),
                round(float(np.percentile(rd_ung_gated_boot, 97.5)), 4),
            ],
            "domain_paired_wilcoxon_p": float(p_wilcox_ung),
        },
        "as_discovered_vs_abstain_probe_ungrounded_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["as_discovered"]["ungrounded_rate_all_slots"]
                - expB_summary["by_arm"]["abstain_probe"]["ungrounded_rate_all_slots"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_ung_probe_boot, 2.5)), 4),
                round(float(np.percentile(rd_ung_probe_boot, 97.5)), 4),
            ],
        },
        "as_discovered_vs_abstain_probe_fabrication_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["as_discovered"]["fabrication_rate_all_slots"]
                - expB_summary["by_arm"]["abstain_probe"]["fabrication_rate_all_slots"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_fab_probe_boot, 2.5)), 4),
                round(float(np.percentile(rd_fab_probe_boot, 97.5)), 4),
            ],
        },
        "gated_vs_as_discovered_abstention_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["gated"]["abstention_rate"]
                - expB_summary["by_arm"]["as_discovered"]["abstention_rate"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_abs_gated_boot, 2.5)), 4),
                round(float(np.percentile(rd_abs_gated_boot, 97.5)), 4),
            ],
        },
        "abstain_probe_vs_as_discovered_abstention_RD": {
            "point_estimate": round(
                expB_summary["by_arm"]["abstain_probe"]["abstention_rate"]
                - expB_summary["by_arm"]["as_discovered"]["abstention_rate"], 4),
            "cluster_boot_95ci": [
                round(float(np.percentile(rd_abs_probe_boot, 2.5)), 4),
                round(float(np.percentile(rd_abs_probe_boot, 97.5)), 4),
            ],
        },
        "domain_literature_count_spearman": {
            "rho_fabrication": round(float(rho_fab), 4),
            "p_fabrication": round(float(p_rho_fab), 4),
            "rho_ungrounded": round(float(rho_ung), 4),
            "p_ungrounded": round(float(p_rho_ung), 4),
        }
    }

    report = {
        "verifier_self_calibration_sec8": {
            "positive_control_n": len(pos_control_pmids),
            "positive_control_resolved": pos_pass,
            "positive_control_sensitivity": round(pos_pass / len(pos_control_pmids), 4),
            "negative_control_n": len(neg_control_pmids),
            "negative_control_rejected": neg_pass,
            "negative_control_specificity": round(neg_pass / len(neg_control_pmids), 4),
        },
        "parent_runs_dimension1": parent_summary,
        "experiment_B": expB_summary,
    }

    out_json = os.path.join(HERE, "step1_pubmed_results.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(HERE, "step1_parent_slots_scored.json"), "w", encoding="utf-8") as fh:
        json.dump(parent_slots, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "step1_expB_slots_scored.json"), "w", encoding="utf-8") as fh:
        json.dump(expB_slots, fh, ensure_ascii=False, indent=1)

    print("=== STEP 1 PUBMED VERIFICATION COMPLETE ===")
    print("Verifier Self-Calibration (§8):", report["verifier_self_calibration_sec8"])
    print("Parent Runs Overall (360 slots):", parent_summary["overall"])
    for k, v in parent_summary["by_disease_arm"].items():
        print(f"  {k:18s}: fab_all={v['fabrication_rate_all_slots']:.3f}, ung_all={v['ungrounded_rate_all_slots']:.3f}, on_topic={v['verified_on_topic_rate_among_emitted']:.3f}")
    print("Experiment B by Arm (420 slots each):")
    for k, v in expB_summary["by_arm"].items():
        print(f"  {k:18s}: abs={v['abstention_rate']:.3f}, fab_all={v['fabrication_rate_all_slots']:.3f}, fab_emitted={v['fabrication_rate_among_emitted']:.3f}, on_topic_emitted={v['verified_on_topic_rate_among_emitted']:.3f}")
    print("Confirmatory Contrasts:", json.dumps(expB_summary["confirmatory_contrasts"], indent=2))


if __name__ == "__main__":
    main()
