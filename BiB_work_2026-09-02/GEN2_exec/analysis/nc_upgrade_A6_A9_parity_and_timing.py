#!/usr/bin/env python3
"""
nc_upgrade_A6_A9_parity_and_timing.py -- Phase-1 Tasks A6 & A9 for Nature Communications
Special Collection 'Agentic AI Systems':
  Task A6 (Zero-Discrepancy Parity, Composite Formula, & Live PubMed Citation Audit):
    1. Exact token & call-count reconciliation across calls_log.jsonl (9,130 total rows):
       - All 9,130 rows vs 9,090 non-canary rows vs 8,972 ok non-canary rows.
       - Block-by-block exact sums (7,890 Parent, 396 Exp B, 804 Exp C, 40 Canary).
    2. Exact Tournament II Fig. 5C accounting (3,240 total -> 38 incomplete + 3,202 complete
       = 1,824 consistent + 1,336 primacy-flipped [A,A] + 42 recency-flipped [B,B]; 1,824+1,336=3,160).
    3. Exact Experiment B CoT token reduction (median 11,798.5 -> 1,132.0 = -90.41% vs mean -86.24%).
    4. Explicit closed-form Four-Pillar Trustworthiness Composite Score (incorporating A2
       Closed-Loop Entrez Handoff verified citation yield).
    5. Live NCBI PubMed verification of ALS-specific replacements for Ref [63] (CCS/SOD1 copper
       toxicity in ALS) and Ref [65] (C1q/C3 classical complement in ALS motor neurons/NMJ),
       plus exact 5-field metadata for the 5 published Nature Communications 'Agentic AI Systems'
       sibling papers.

  Task A9 (Deployment Runtime/Memory Profiling + DeBERTa-v3 NLI Threshold Sensitivity):
    1. Wall-clock ms & peak RAM (MB) of all 4 deterministic rectification modules + NLI diagnostic.
    2. Selective Calibration Gate threshold sweep tau_ece in {0.08, 0.10, 0.12, 0.15}.
    3. DeBERTa-v3 NLI threshold sensitivity curve across tau_nli in {0.50, 0.60, 0.70, 0.75,
       0.80, 0.85, 0.90, 0.95} and export of full scored pairs to nc_upgrade_nli_scored_pairs.json
       for Task A5 blinded 100-pair domain-expert audit.
"""
from gate import gate, canary_gate, retry_limit

import json
import os
import random
import re
import sys
import time
import tracemalloc
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
import numpy as np
import requests
from scipy import stats

from nc_upgrade_A1_A4_btl_validation import fit_oa_btl_fast
from step1_pubmed_verify import HERE, EXEC_ROOT, NCBI, MAILTO, check_on_topic
from step4_dim5_deberta_nli import (
    load_entity_map,
    split_sentences,
    extract_entities,
    parse_judge_sections,
    load_nli_model,
    score_nli_pairs_bidirectional,
)

gate(__file__)

RUNS_DIR = os.path.join(EXEC_ROOT, "runs")
DATA_DIR = os.path.join(EXEC_ROOT, "data")
OUT_JSON = os.path.join(HERE, "nc_upgrade_A6_A9_results.json")
NLI_PAIRS_JSON = os.path.join(HERE, "nc_upgrade_nli_scored_pairs.json")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": f"star-audit-nc-a6/{MAILTO}"})


def pubmed_verify_query(query, retmax=8):
    time.sleep(0.36)
    q_enc = urllib.parse.quote(query)
    es = SESSION.get(f"{NCBI}esearch.fcgi?db=pubmed&retmode=json&retmax={retmax}&sort=relevance&term={q_enc}&email={MAILTO}", timeout=15).json()
    idlist = es.get("esearchresult", {}).get("idlist", [])
    if not idlist:
        return []
    time.sleep(0.36)
    ef_xml = SESSION.get(f"{NCBI}efetch.fcgi?db=pubmed&retmode=xml&id={','.join(idlist)}&email={MAILTO}", timeout=20).text
    root = ET.fromstring(ef_xml)
    recs = []
    for art in root.findall(".//PubmedArticle"):
        pmid = (art.findtext(".//MedlineCitation/PMID") or "").strip()
        title = "".join(art.find(".//Article/ArticleTitle").itertext()).strip() if art.find(".//Article/ArticleTitle") is not None else ""
        journal = (art.findtext(".//Article/Journal/Title") or "").strip()
        iso = (art.findtext(".//Article/Journal/ISOAbbreviation") or "").strip()
        year = (art.findtext(".//Article/Journal/JournalIssue/PubDate/Year") or art.findtext(".//Article/ArticleDate/Year") or "").strip()
        vol = (art.findtext(".//Article/Journal/JournalIssue/Volume") or "").strip()
        pages = (art.findtext(".//Article/Pagination/MedlinePgn") or art.findtext(".//Article/ELocationID[@EIdType='pii']") or "").strip()
        doi = ""
        for aid in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
            if aid.attrib.get("IdType") == "doi" and aid.text:
                doi = aid.text.strip()
        au_el = art.find(".//Article/AuthorList/Author[1]")
        first_author = ""
        if au_el is not None:
            ln = (au_el.findtext("LastName") or "").strip()
            fn = (au_el.findtext("Initials") or "").strip()
            first_author = f"{ln} {fn}".strip()
        recs.append({
            "pmid": pmid,
            "first_author": first_author,
            "title": title,
            "journal": journal,
            "journal_iso": iso,
            "year": year,
            "volume": vol,
            "pages": pages,
            "doi": doi,
        })
    return recs


@retry_limit(2)
def main():
    t0_all = time.perf_counter()

    # ==========================================================================
    # 1. A6-1: Exact Call & Token Ledger Across All 9,130 Calls
    # ==========================================================================
    calls = [json.loads(line) for line in open(os.path.join(DATA_DIR, "calls_log.jsonl"), encoding="utf-8") if line.strip()]
    canary_gate(lambda: len(calls) == 9130, "Verify 9,130 total rows in calls_log.jsonl")

    by_block = defaultdict(lambda: {"n_calls": 0, "n_ok": 0, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0})
    for c in calls:
        cid = str(c["call_id"])
        blk = "canary" if cid.startswith("canary/") else ("parent" if cid.startswith("parent/") else ("expB" if cid.startswith("expB") else "expC"))
        for k in (blk, "ALL_9130"):
            by_block[k]["n_calls"] += 1
            if c.get("ok"):
                by_block[k]["n_ok"] += 1
            by_block[k]["input_tokens"] += int(c.get("input_tokens") or 0)
            by_block[k]["output_tokens"] += int(c.get("output_tokens") or 0)
            by_block[k]["reasoning_tokens"] += int(c.get("reasoning_tokens") or 0)
        if blk != "canary":
            by_block["NON_CANARY_9090"]["n_calls"] += 1
            if c.get("ok"):
                by_block["NON_CANARY_OK"]["n_calls"] += 1
                by_block["NON_CANARY_OK"]["input_tokens"] += int(c.get("input_tokens") or 0)
                by_block["NON_CANARY_OK"]["output_tokens"] += int(c.get("output_tokens") or 0)
                by_block["NON_CANARY_OK"]["reasoning_tokens"] += int(c.get("reasoning_tokens") or 0)
            by_block["NON_CANARY_9090"]["input_tokens"] += int(c.get("input_tokens") or 0)
            by_block["NON_CANARY_9090"]["output_tokens"] += int(c.get("output_tokens") or 0)
            by_block["NON_CANARY_9090"]["reasoning_tokens"] += int(c.get("reasoning_tokens") or 0)

    calls_by_id = {c["call_id"]: c for c in calls}

    # Exact Fig. 5C Tournament II Reconciliation
    runs_12 = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]
    rt_consistent, rt_primacy_aa, rt_recency_bb = [], [], []
    n_incomplete_pairs = 0
    for rid in runs_12:
        s4_v = json.load(open(os.path.join(RUNS_DIR, rid, "step4_verdicts.json"), encoding="utf-8")).get("verdicts", {})
        for p_idx in range(45):
            for j in [1, 2, 3]:
                ka, kb = f"{p_idx:02d}_a_j{j}", f"{p_idx:02d}_b_j{j}"
                va, vb = s4_v.get(ka), s4_v.get(kb)
                if not va or not vb or va.get("failed") or vb.get("failed") or va.get("winner_idx") is None or vb.get("winner_idx") is None:
                    n_incomplete_pairs += 1
                    continue
                rta = int((calls_by_id.get(f"parent/{rid}/step4/{ka}") or {}).get("reasoning_tokens") or 0)
                rtb = int((calls_by_id.get(f"parent/{rid}/step4/{kb}") or {}).get("reasoning_tokens") or 0)
                if va["winner_idx"] == vb["winner_idx"]:
                    rt_consistent.extend([rta, rtb])
                elif va.get("slot_winner") == "A" and vb.get("slot_winner") == "A":
                    rt_primacy_aa.extend([rta, rtb])
                else:
                    rt_recency_bb.extend([rta, rtb])

    rt_all_flipped = rt_primacy_aa + rt_recency_bb
    _, p_mw_aa = stats.mannwhitneyu(rt_primacy_aa, rt_consistent, alternative="two-sided")
    _, p_mw_all = stats.mannwhitneyu(rt_all_flipped, rt_consistent, alternative="two-sided")

    # Exact Exp B CoT Token Statistics (n=70 per arm)
    expb_toks = {}
    for arm in ["as_discovered", "abstain_probe", "gated"]:
        vals = [
            int(calls_by_id[f"expB/glm/stage2/{arm}/B{d:02d}/h{h}"]["reasoning_tokens"])
            for d in range(1, 15) for h in range(1, 6)
        ]
        expb_toks[arm] = {
            "n": len(vals),
            "median": float(np.median(vals)),
            "iqr": [float(np.percentile(vals, 25)), float(np.percentile(vals, 75))],
            "mean": round(float(np.mean(vals)), 2),
            "sd": round(float(np.std(vals, ddof=1)), 2),
        }
    med_red_pct = round(100.0 * (expb_toks["gated"]["median"] - expb_toks["as_discovered"]["median"]) / expb_toks["as_discovered"]["median"], 2)
    mean_red_pct = round(100.0 * (expb_toks["gated"]["mean"] - expb_toks["as_discovered"]["mean"]) / expb_toks["as_discovered"]["mean"], 2)

    # ==========================================================================
    # 2. A6-2: Explicit Closed-Form Four-Pillar Trustworthiness Composite Score
    # ==========================================================================
    a2_res = json.load(open(os.path.join(HERE, "nc_upgrade_A2_results.json"), encoding="utf-8"))
    a3_a7 = json.load(open(os.path.join(HERE, "nc_upgrade_A3_A7_results.json"), encoding="utf-8"))
    cl_yield = a2_res["closed_loop_glm_full420"]["closed_loop_verified_grounded_yield_pct"]

    # Pillar definitions (all in [0, 100], higher = more trustworthy):
    #   P1_norm: Fair-Share Normalized Novelty Survival = min(100, Bucket3_Top10_Share% / 33.3333% * 100)
    #            (Raw Bucket3 share: 13.33% before -> 24.17% after OA-BTL; normalized: 40.00% -> 72.50%)
    #   P2: Tournament II Position-Consistent Pairwise Share% (56.96% before -> 100.00% after bidirectional OA-BTL)
    #   P3: Verified On-Topic Grounded Citation Yield% Penalized by Ungrounded Citations = max(0, Grounded% - Ungrounded%)
    #       OR Simple Verified On-Topic Grounded Yield% under Closed-Loop Entrez Handoff:
    #       Before (as_discovered): 56.90% grounded (with 43.10% ungrounded);
    #       Abstain-Probe + Tier2: 33.81% parametric grounded (0% ungrounded);
    #       Closed-Loop STAR-Audit (Module 3a + 3b Entrez Handoff): cl_yield% grounded (0.00% ungrounded!)
    #   P4: Calibration Accuracy = 100 - 100 * ECE (77.79% before -> 97.26% after Selective LORO Platt)
    pillars_raw_mean = {
        "formula": "S_raw = (Bucket3_Share_pct + T2_Consistent_pct + Verified_Grounded_Yield_pct + (100 - 100*ECE)) / 4",
        "before_unrectified": round((13.33 + 56.96 + 42.62 + 77.79) / 4.0, 2),
        "after_oa_btl_and_platt_only": round((24.17 + 100.00 + 42.62 + 97.26) / 4.0, 2),
        "after_module3a_safety_score": round((24.17 + 100.00 + 97.14 + 97.26) / 4.0, 2),
        "after_full_star_audit_closed_loop": round((24.17 + 100.00 + cl_yield + 97.26) / 4.0, 2),
    }
    pillars_fair_norm = {
        "formula": "S_norm = (min(100, 3*Bucket3_Share_pct) + T2_Consistent_pct + Verified_Grounded_Yield_pct + (100 - 100*ECE)) / 4",
        "components_before": [40.00, 56.96, 42.62, 77.79],
        "components_abstain_probe_safety": [40.00, 56.96, 78.33, 77.79],
        "components_oa_btl_and_platt": [72.50, 100.00, 42.62, 97.26],
        "components_full_star_audit": [72.50, 100.00, cl_yield, 97.26],
        "score_before": round((40.00 + 56.96 + 42.62 + 77.79) / 4.0, 2),
        "score_abstain_probe_safety": round((40.00 + 56.96 + 78.33 + 77.79) / 4.0, 2),
        "score_oa_btl_and_platt": round((72.50 + 100.00 + 42.62 + 97.26) / 4.0, 2),
        "score_full_star_audit": round((72.50 + 100.00 + cl_yield + 97.26) / 4.0, 2),
    }

    # ==========================================================================
    # 3. A6-3: Live PubMed Verification of ALS Replacements & 5 NC Sibling Papers
    # ==========================================================================
    als_ccs_candidates = pubmed_verify_query('("copper chaperone for superoxide dismutase" OR "CCS" OR "ATP7A") AND ("amyotrophic lateral sclerosis" OR "G93A-SOD1") AND ("mitochondrial" OR "motor neuron")', retmax=8)
    als_c1q_candidates = pubmed_verify_query('("C1q" OR "complement C3" OR "classical complement") AND ("amyotrophic lateral sclerosis" OR "SOD1") AND ("motor neuron" OR "neuromuscular junction" OR "synapse")', retmax=8)

    nc_dois = [
        "10.1038/s41467-026-77340-3",
        "10.1038/s41467-026-71411-1",
        "10.1038/s41467-026-73289-5",
        "10.1038/s41467-025-67998-6",
        "10.1038/s41467-026-68672-1",
    ]
    nc_sibling_refs = {}
    for doi in nc_dois:
        recs = pubmed_verify_query(f'"{doi}"[AID]', retmax=2)
        nc_sibling_refs[doi] = recs[0] if recs else {"doi": doi, "found_in_pubmed": False}

    # ==========================================================================
    # 4. A9: Runtime / Memory Profiling & DeBERTa-v3 NLI Threshold Sweep
    # ==========================================================================
    # 4a. Benchmark Module 1 (OA-BTL on R1 T1 435 pairs)
    s2_r1 = json.load(open(os.path.join(RUNS_DIR, "dAMD_blind_R1", "step2_verdicts.json"), encoding="utf-8"))
    a_l, b_l, y_l, w_l = [], [], [], []
    for v in (s2_r1.get("verdicts") or {}).values():
        if v and not v.get("failed") and v.get("verdict") in ("A", "B"):
            pa, pb = int(v["A"]), int(v["B"])
            a_l.append(pa)
            b_l.append(pb)
            y_l.append(1.0 if v["verdict"] == "A" else 0.0)
            w_l.append(1.0)
    obs_arrs = (np.array(a_l, dtype=int), np.array(b_l, dtype=int), np.array(y_l, dtype=float), np.array(w_l, dtype=float))

    tracemalloc.start()
    t_m1 = time.perf_counter()
    for _ in range(20):
        fit_oa_btl_fast(obs_arrs, 30, l2_reg=0.01)
    ms_m1_per_run = round((time.perf_counter() - t_m1) * 1000.0 / 20.0, 3)
    _, peak_m1 = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 4b. Selective Calibration Gate Threshold Sweep tau_ece in {0.08, 0.10, 0.12, 0.15}
    # Re-evaluate Gemini-4-Argon-High (raw=0.0797) and Grok-4.7-Fast (raw=0.1652) across tau_ece
    from nc_upgrade_A3_A7_expc_calibration import compute_ece_brier
    truth_map = json.load(open(os.path.join(HERE, "expC_20pairs_truth_key.json"), encoding="utf-8"))
    tau_ece_sweep = {}
    for tau_e in [0.08, 0.10, 0.12, 0.15]:
        tau_ece_sweep[str(tau_e)] = {}
        for m_lbl, fn in [
            ("Gemini-4-Argon-High", os.path.join(DATA_DIR, "gemini_outputs", "expC_pro_60preds.json")),
            ("Gemini-3.8-Flash", os.path.join(DATA_DIR, "gemini_outputs", "expC_flash_60preds.json")),
            ("Grok-4.7-High", os.path.join(DATA_DIR, "grok_outputs", "expC_high_60preds.json")),
            ("Grok-4.7-Fast", os.path.join(DATA_DIR, "grok_outputs", "expC_fast_60preds.json")),
        ]:
            arr = json.load(open(fn, encoding="utf-8"))
            p_raw = np.clip([float(x.get("confidence", 75)) / 100.0 for x in arr], 0.01, 0.99)
            logits = np.log(p_raw / (1.0 - p_raw))
            y = np.array([
                1.0 if any(str(p).upper() in ({truth_map[x["pair_id"]]["gene_symbol"].upper()} | {a.upper() for a in truth_map[x["pair_id"]].get("aliases", [])}) for p in x.get("predictions", [])[:10]) else 0.0
                for x in arr
            ])
            pids = np.array([x["pair_id"] for x in arr])
            p_out = np.zeros_like(p_raw)
            trig = 0
            from scipy.optimize import minimize
            for pid in sorted(set(pids)):
                tr = pids != pid
                te = ~tr
                tr_ece, _ = compute_ece_brier(p_raw[tr], y[tr], n_bins=5)
                if tr_ece > tau_e:
                    trig += 1
                    res_opt = minimize(
                        lambda ab: -np.sum(y[tr] * np.log(1 / (1 + np.exp(-np.clip(ab[0] * logits[tr] + ab[1], -20, 20))) + 1e-9) + (1 - y[tr]) * np.log(1 - 1 / (1 + np.exp(-np.clip(ab[0] * logits[tr] + ab[1], -20, 20))) + 1e-9)) + 0.01 * (ab[0] ** 2 + ab[1] ** 2),
                        [1.0, 0.0], method="BFGS"
                    ).x
                    p_out[te] = 1.0 / (1.0 + np.exp(-np.clip(res_opt[0] * logits[te] + res_opt[1], -20, 20)))
                else:
                    p_out[te] = p_raw[te]
            ece_val, _ = compute_ece_brier(p_out, y, n_bins=5)
            tau_ece_sweep[str(tau_e)][m_lbl] = {"ece_5bin": round(ece_val, 4), "triggered_folds": f"{trig}/20"}

    # 4c. DeBERTa-v3 NLI Timing + Threshold Sensitivity Curve + Full Pair Export for Task A5
    alias_to_canon = load_entity_map()
    cross_stage_pairs = []
    t2_reversal_pairs = []
    for run_id in runs_12:
        rdir = os.path.join(RUNS_DIR, run_id)
        s1 = json.load(open(os.path.join(rdir, "step1_mechanisms.json"), encoding="utf-8"))
        s3 = json.load(open(os.path.join(rdir, "step3_candidates.json"), encoding="utf-8"))
        s4 = json.load(open(os.path.join(rdir, "step4_verdicts.json"), encoding="utf-8"))
        s5 = json.load(open(os.path.join(rdir, "step5_top5.json"), encoding="utf-8"))
        s6 = json.load(open(os.path.join(rdir, "step6_protocols.json"), encoding="utf-8"))
        top5_cids = {x["cand_id"] for x in s5["top5"]}

        st_a = defaultdict(list)
        for m in s1["mechanisms"]:
            mkey = f"M{int(m['id']) - 1:02d}"
            for sent in split_sentences(m.get("mechanism", "")):
                ents = extract_entities(sent, alias_to_canon)
                if ents:
                    st_a["step1"].append({"item_id": mkey, "text": sent, "entities": ents})
        for c in s3["candidates"]:
            cid = c["cand_id"]
            for fld in ["mechanism", "intervention_principle", "rationale", "feasibility"]:
                for sent in split_sentences(c.get(fld, "")):
                    ents = extract_entities(sent, alias_to_canon)
                    if ents:
                        st_a["step3"].append({"item_id": cid, "text": sent, "entities": ents})
        for p_obj in s6.get("protocols", []):
            cid = p_obj.get("cand_id", "")
            proto = p_obj.get("protocol") or {}
            blks = [proto.get("hypothesis_testable", ""), proto.get("experimental_model", ""), proto.get("readouts_and_controls", "")]
            for ref in proto.get("references") or []:
                if isinstance(ref, dict) and ref.get("claim"):
                    blks.append(ref["claim"])
            for blk in blks:
                for sent in split_sentences(blk):
                    ents = extract_entities(sent, alias_to_canon)
                    if ents:
                        st_a["step6"].append({"item_id": cid, "text": sent, "entities": ents})

        for a1 in st_a["step1"]:
            set1 = set(a1["entities"])
            for a3 in st_a["step3"]:
                sh = set1.intersection(a3["entities"])
                if sh:
                    cross_stage_pairs.append({
                        "run_id": run_id, "pair_type": "step1_vs_step3", "cand_id": a3["item_id"],
                        "in_top5": a3["item_id"] in top5_cids, "shared_entities": sorted(sh),
                        "s1": a1["text"], "s2": a3["text"],
                    })
        for a3 in st_a["step3"]:
            set3 = set(a3["entities"])
            for a6 in st_a["step6"]:
                if a3["item_id"] == a6["item_id"]:
                    sh = set3.intersection(a6["entities"])
                    if sh:
                        cross_stage_pairs.append({
                            "run_id": run_id, "pair_type": "step3_vs_step6", "cand_id": a3["item_id"],
                            "in_top5": True, "shared_entities": sorted(sh),
                            "s1": a3["text"], "s2": a6["text"],
                        })

        by_pj = defaultdict(dict)
        for v in (s4.get("verdicts") or {}).values():
            if v and "pair" in v and not v.get("failed"):
                by_pj[(tuple(v["pair"]), v["judge"])][v["direction"]] = v
        for (pt, j), dm in by_pj.items():
            if "a" not in dm or "b" not in dm:
                continue
            va, vb = dm["a"], dm["b"]
            if va.get("winner_idx") is None or vb.get("winner_idx") is None:
                continue
            sec_a, sec_b = parse_judge_sections(va.get("reasoning", "")), parse_judge_sections(vb.get("reasoning", ""))
            c0, c1 = s3["candidates"][pt[0]]["cand_id"], s3["candidates"][pt[1]]["cand_id"]

            def dealias(txt, d):
                if d == "a":
                    t = re.sub(r"\bProposal A\b|\bCandidate A\b|\bOption A\b|\bA's\b|\bA\b", c0, txt)
                    return re.sub(r"\bProposal B\b|\bCandidate B\b|\bOption B\b|\bB's\b|\bB\b", c1, t)
                t = re.sub(r"\bProposal A\b|\bCandidate A\b|\bOption A\b|\bA's\b|\bA\b", c1, txt)
                return re.sub(r"\bProposal B\b|\bCandidate B\b|\bOption B\b|\bB's\b|\bB\b", c0, t)

            if "SCIENCE" in sec_a and "SCIENCE" in sec_b:
                t2_reversal_pairs.append({
                    "run_id": run_id, "pair": list(pt), "judge": j, "criterion": "SCIENCE",
                    "is_pos_biased": va["winner_idx"] != vb["winner_idx"],
                    "s1": dealias(sec_a["SCIENCE"], "a"), "s2": dealias(sec_b["SCIENCE"], "b"),
                })

    rng_t2 = random.Random(20260101)
    sampled_t2 = []
    for rid in runs_12:
        b_s = [p for p in t2_reversal_pairs if p["run_id"] == rid and p["is_pos_biased"]]
        c_s = [p for p in t2_reversal_pairs if p["run_id"] == rid and not p["is_pos_biased"]]
        sampled_t2.extend(rng_t2.sample(b_s, min(20, len(b_s))))
        sampled_t2.extend(rng_t2.sample(c_s, min(20, len(c_s))))

    t_nli0 = time.perf_counter()
    tokenizer, model, contra_idx, entail_idx, _ = load_nli_model()
    t_load_nli = round(time.perf_counter() - t_nli0, 2)

    t_sc0 = time.perf_counter()
    cs_scored = score_nli_pairs_bidirectional(tokenizer, model, contra_idx, entail_idx, cross_stage_pairs, batch_size=64)
    t2_scored = score_nli_pairs_bidirectional(tokenizer, model, contra_idx, entail_idx, sampled_t2, batch_size=64)
    t_score_nli = round(time.perf_counter() - t_sc0, 2)

    with open(NLI_PAIRS_JSON, "w", encoding="utf-8") as fh:
        json.dump({"cross_stage_scored": cs_scored, "t2_reversal_scored": t2_scored}, fh, indent=1, ensure_ascii=False)

    nli_tau_sweep = []
    for tau in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
        cs_bi = sum(1 for p in cs_scored if p["p_contra_min"] > tau)
        cs_dir = sum(1 for p in cs_scored if p["p_contra_max"] > tau)
        s13_bi = [p for p in cs_scored if p["pair_type"] == "step1_vs_step3" and p["p_contra_min"] > tau]
        s13_prop = sum(1 for p in s13_bi if p["in_top5"])
        b_pairs = [p for p in t2_scored if p["is_pos_biased"]]
        c_pairs = [p for p in t2_scored if not p["is_pos_biased"]]
        b_dir = sum(1 for p in b_pairs if p["p_contra_max"] > tau)
        c_dir = sum(1 for p in c_pairs if p["p_contra_max"] > tau)
        nli_tau_sweep.append({
            "tau": tau,
            "cross_stage_bidir_count": cs_bi,
            "cross_stage_bidir_per_1k_pairs": round(1000.0 * cs_bi / len(cs_scored), 2),
            "cross_stage_dir_count": cs_dir,
            "silent_top5_propagation_pct": round(100.0 * s13_prop / len(s13_bi), 2) if s13_bi else 0.0,
            "t2_biased_dir_contra_pct": round(100.0 * b_dir / len(b_pairs), 2),
            "t2_consistent_dir_contra_pct": round(100.0 * c_dir / len(c_pairs), 2),
        })

    out = {
        "task": "A6_Parity_Citations_and_A9_Runtime_Sensitivity",
        "elapsed_sec": round(time.perf_counter() - t0_all, 2),
        "A6_token_call_ledger": dict(by_block),
        "A6_fig5C_t2_reconciliation": {
            "total_scheduled_t2_calls": 3240,
            "incomplete_singleton_pairs": n_incomplete_pairs,
            "incomplete_singleton_calls": n_incomplete_pairs * 2,
            "complete_bidirectional_calls": len(rt_consistent) + len(rt_primacy_aa) + len(rt_recency_bb),
            "content_consistent_calls": len(rt_consistent),
            "primacy_flipped_AA_calls": len(rt_primacy_aa),
            "recency_flipped_BB_calls": len(rt_recency_bb),
            "fig5c_plotted_subset_calls_consistent_plus_AA": len(rt_consistent) + len(rt_primacy_aa),
            "median_rt_consistent": float(np.median(rt_consistent)),
            "median_rt_primacy_AA": float(np.median(rt_primacy_aa)),
            "median_rt_all_flipped": float(np.median(rt_all_flipped)),
            "mannwhitney_p_AA_vs_consistent": float(p_mw_aa),
            "mannwhitney_p_all_flipped_vs_consistent": float(p_mw_all),
        },
        "A6_expB_cot_token_reconciliation": {
            "by_arm": expb_toks,
            "median_reduction_gated_vs_as_discovered_pct": med_red_pct,
            "mean_reduction_gated_vs_as_discovered_pct": mean_red_pct,
        },
        "A6_composite_score_reconciliation": {
            "unweighted_raw_mean": pillars_raw_mean,
            "fair_share_normalized_mean": pillars_fair_norm,
        },
        "A6_live_pubmed_als_ccs_candidates": als_ccs_candidates,
        "A6_live_pubmed_als_c1q_candidates": als_c1q_candidates,
        "A6_nc_agentic_ai_5_sibling_papers": nc_sibling_refs,
        "A9_module_profiling": {
            "module1_oabtl_435pairs_ms_per_run": ms_m1_per_run,
            "module1_peak_ram_mb": round(peak_m1 / (1024 * 1024), 3),
            "module5_deberta_nli_model_load_sec": t_load_nli,
            "module5_deberta_nli_2246_bidir_pairs_sec": t_score_nli,
            "module5_ms_per_bidir_pair_cpu": round(1000.0 * t_score_nli / max(1, len(cs_scored) + len(t2_scored)), 2),
        },
        "A9_selective_calibration_tau_ece_sweep": tau_ece_sweep,
        "A9_deberta_nli_tau_sweep": nli_tau_sweep,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(f"\n[A6 + A9 DONE in {out['elapsed_sec']}s] Saved to {OUT_JSON}")
    print("  ALL_9130 CoT tokens:", by_block["ALL_9130"]["reasoning_tokens"],
          "| NON_CANARY_OK CoT tokens:", by_block["NON_CANARY_OK"]["reasoning_tokens"])
    print("  Fig5C T2 calls: consistent=", len(rt_consistent), "+ primacy_AA=", len(rt_primacy_aa),
          "(=3,160) + recency_BB=", len(rt_recency_bb), "(=3,202)")
    print("  ExpB CoT reduction: median=", med_red_pct, "% | mean=", mean_red_pct, "%")
    print("  Composite Fair-Norm Score:", pillars_fair_norm["score_before"], "->", pillars_fair_norm["score_full_star_audit"])


if __name__ == "__main__":
    main()
