#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
analyze_grok_cross_ecosystem.py
Analyzes the xAI Grok-4.7 (`high`: grok-4.7 High-Thinking vs `fast`: grok-4.7-build-fast Low-Thinking)
Cross-Ecosystem Validation Cohort across:
  1. Arena 1: Tournament II Bidirectional Pairwise Evaluation (dAMD & ALS, 720 verdicts: 360 Blinded Independent-Session + 360 Joint-Context Control)
  2. Arena 2: Experiment B 3-Arm Clinical Citation Gating across 14 Specialties (504 citation slots, verified via NCBI PubMed E-utilities)
  3. Arena 3: Experiment C Mendelian HPO Phenotype Perturbation across 0%, 25%, 50% del_topIC (120 evaluations) + LORO Platt Calibration
  4. Grok-4.7 Native Reasoning Token Telemetry Summary

Complies with PROJECT_CONSTITUTION.md §4 Entry 5-Checks.
"""

import os
import sys
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
import numpy as np
from scipy import stats
from scipy.optimize import minimize

BASE_ROOT = r"D:\Papers\Robin_Nature_2026"
EXEC_DIR = os.path.join(BASE_ROOT, "BiB_work_2026-09-02", "GEN2_exec")
GROK_DIR = os.path.join(EXEC_DIR, "data", "grok_outputs")
STIM_DIR = os.path.join(EXEC_DIR, "data", "gemini_stimuli")
TRUTH_KEY_PATH = os.path.join(EXEC_DIR, "analysis", "expC_20pairs_truth_key.json")
PUBMED_CACHE_PATH = os.path.join(EXEC_DIR, "analysis", "pubmed_verification_cache.json")
OUTPUT_PATH = os.path.join(EXEC_DIR, "analysis", "grok_cross_ecosystem_summary.json")

assert os.path.abspath(EXEC_DIR).startswith(BASE_ROOT), "Check 1 Failed"
for fn in [
    "t2_dAMD_high_blind_fwd45.json",
    "t2_dAMD_high_blind_rev45.json",
    "t2_dAMD_fast_blind_fwd45.json",
    "t2_dAMD_fast_blind_rev45.json",
    "t2_ALS_high_blind_fwd45.json",
    "t2_ALS_high_blind_rev45.json",
    "t2_ALS_fast_blind_fwd45.json",
    "t2_ALS_fast_blind_rev45.json",
    "t2_dAMD_high_90verdicts.json",
    "t2_dAMD_fast_90verdicts.json",
    "t2_ALS_high_90verdicts.json",
    "t2_ALS_fast_90verdicts.json",
    "expB_high_42lists.json",
    "expB_fast_42lists.json",
    "expC_high_60preds.json",
    "expC_fast_60preds.json",
]:
    p = os.path.join(GROK_DIR, fn)
    assert os.path.exists(p), f"Check 2 Failed: Missing {p}"


def fetch_pubmed_batch(pmids, cache):
    missing = [p for p in set(pmids) if p not in cache and re.match(r"^\d+$", p)]
    batch_size = 50
    for i in range(0, len(missing), batch_size):
        chunk = missing[i:i + batch_size]
        ids_str = ",".join(chunk)
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "STAR-Audit-Verifier/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            res = data.get("result", {})
            for pid in chunk:
                rec = res.get(pid)
                if rec and isinstance(rec, dict) and "error" not in rec and rec.get("title"):
                    cache[pid] = {
                        "exists": True,
                        "title": rec.get("title", ""),
                        "source": rec.get("source", ""),
                        "pubdate": rec.get("pubdate", ""),
                    }
                else:
                    cache[pid] = {"exists": False, "title": "", "source": "", "pubdate": ""}
        except Exception as e:
            print("PubMed esummary warning:", e)
        time.sleep(0.35)

    need_abs = [p for p in set(pmids) if cache.get(p, {}).get("exists") and "abstract" not in cache[p]]
    for i in range(0, len(need_abs), 40):
        chunk = need_abs[i:i + 40]
        ids_str = ",".join(chunk)
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids_str}&retmode=xml"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "STAR-Audit-Verifier/2.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml_txt = resp.read().decode("utf-8", errors="ignore")
            articles = re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml_txt, re.S)
            found_map = {}
            for art in articles:
                m_id = re.search(r"<PMID[^>]*>(\d+)</PMID>", art)
                if m_id:
                    pid = m_id.group(1)
                    abs_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", art, re.S)
                    mesh_parts = re.findall(r"<DescriptorName[^>]*>(.*?)</DescriptorName>", art, re.S)
                    found_map[pid] = " ".join(abs_parts + mesh_parts)
            for pid in chunk:
                cache[pid]["abstract"] = found_map.get(pid, "")
        except Exception as e:
            print("PubMed efetch warning:", e)
            for pid in chunk:
                cache[pid].setdefault("abstract", "")
        time.sleep(0.35)


def check_domain_topic_match(domain_name, mech_text, pub_rec):
    if not pub_rec or not pub_rec.get("exists"):
        return False
    blob = (pub_rec.get("title", "") + " " + pub_rec.get("abstract", "")).lower()
    dom_syns = {
        "asthma": ["asthma", "airway", "bronch", "il-33", "il33", "st2", "il1rl1", "ilc2", "nuocyte", "natural helper", "il-5", "il-13", "eosinophil", "goblet"],
        "osteoarthritis": ["osteoarthritis", "cartilage", "chondrocyte", "articular", "synovi", "mmp-13", "mmp13", "adamts-5", "adamts5", "aggrecan", "col2a1"],
        "atrial fibrillation": ["atrial fibrillation", "atrial", "arrhythmia", "pitx2", "kcnq1", "kcnd3", "refractory period", "action potential duration"],
        "psoriasis": ["psoriasis", "psoriatic", "keratinocyte", "il-17", "il17", "il-23", "il23", "th17", "acanthosis", "s100a"],
        "hearing loss, sensorineural": ["hearing", "deaf", "cochlea", "hair cell", "hair-cell", "tmc1", "mechanotransduction", "auditory", "inner ear", "sensorineural"],
        "anemia, sickle cell": ["sickle", "hemoglobin s", "haemoglobin s", "hbs", "deoxyhemoglobin", "hbb", "glu6val", "vaso-occlus", "sickling"],
        "cleft palate": ["cleft", "palat", "irf6", "grhl3", "tp63", "p63", "van der woude", "periderm", "craniofacial", "orofacial"],
        "cholangiocarcinoma": ["cholangiocarcinoma", "biliary tract", "bile duct", "intrahepatic cholangio", "fgfr2", "pemigatinib", "infigratinib", "bgj398"],
        "gaucher disease": ["gaucher", "gba1", "glucocerebrosidase", "glucosylceramide", "glucosylsphingosine", "beta-glucosidase"],
        "de lange syndrome": ["de lange", "cdls", "nipbl", "cohesin", "scc2", "chromatid cohesion"],
        "diabetes insipidus, nephrogenic": ["diabetes insipidus", "nephrogenic", "avpr2", "vasopressin", "aqp2", "aquaporin-2", "aquaporin 2", "collecting duct", "collecting tubule", "water channel"],
        "buruli ulcer": ["buruli", "ulcerans", "mycolactone", "sec61"],
        "leber congenital amaurosis": ["amaurosis", "leber", "rpe65", "isomerohydrolase", "retinoid isomerase", "11-cis", "visual cycle", "retinal dystrophy"],
        "pelizaeus-merzbacher disease": ["pelizaeus", "merzbacher", "plp1", "dm20", "proteolipid protein", "dysmyelinat", "hypomyelinat", "oligodendrocyte"],
    }
    d_key = domain_name.lower().strip()
    syns = dom_syns[d_key]
    return bool(any(s in blob for s in syns))


def compute_ece(confs, hits, n_bins=5):
    confs = np.array(confs, dtype=float) / 100.0
    hits = np.array(hits, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(confs)
    for b in range(n_bins):
        mask = (confs >= bins[b]) & (confs <= bins[b + 1] if b == n_bins - 1 else confs < bins[b + 1])
        if np.any(mask):
            ece += (np.sum(mask) / n) * abs(np.mean(confs[mask]) - np.mean(hits[mask]))
    return float(ece)


def loro_platt_ece(confs, hits, pair_ids):
    p_raw = np.clip(np.array(confs, dtype=float) / 100.0, 0.01, 0.99)
    logits = np.log(p_raw / (1.0 - p_raw))
    y = np.array(hits, dtype=float)
    cal_probs = np.zeros_like(p_raw)
    uniq_pids = sorted(set(pair_ids))
    for pid in uniq_pids:
        train_mask = np.array([p != pid for p in pair_ids])
        test_mask = ~train_mask
        x_tr, y_tr = logits[train_mask], y[train_mask]

        def nll(params):
            a, b = params
            z = np.clip(a * x_tr + b, -20, 20)
            p = 1.0 / (1.0 + np.exp(-z))
            return -np.sum(y_tr * np.log(p + 1e-9) + (1 - y_tr) * np.log(1 - p + 1e-9)) + 0.01 * (a ** 2 + b ** 2)

        res = minimize(nll, [1.0, 0.0], method="BFGS")
        a_hat, b_hat = res.x
        cal_probs[test_mask] = 1.0 / (1.0 + np.exp(-np.clip(a_hat * logits[test_mask] + b_hat, -20, 20)))
    return compute_ece(cal_probs * 100.0, y)


def main():
    summary = {}

    # 1. Arena 1: Tournament II Bidirectional Evaluation (dAMD & ALS, High vs Fast)
    t2_summary = {}
    for dis in ["dAMD", "ALS"]:
        stim_raw = json.load(open(os.path.join(STIM_DIR, f"t2_{dis}_45pairs.json"), encoding="utf-8"))
        stim_pairs = stim_raw["pairs"] if isinstance(stim_raw, dict) else stim_raw
        rev_key = json.load(open(os.path.join(EXEC_DIR, "analysis", f"t2_{dis}_rev_key.json"), encoding="utf-8"))
        m_to_pair = {}
        for idx, p in enumerate(stim_pairs, 1):
            mid = f"M{idx:02d}"
            m_to_pair[mid] = {
                "pair_id": p["pair_id"],
                "cand_i": p["cand_i"]["cand_id"],
                "cand_j": p["cand_j"]["cand_id"],
                "name_i": p["cand_i"]["name"],
                "name_j": p["cand_j"]["name"],
            }

        for tier in ["high", "fast"]:
            fwd_fn = os.path.join(GROK_DIR, f"t2_{dis}_{tier}_blind_fwd45.json")
            rev_fn = os.path.join(GROK_DIR, f"t2_{dis}_{tier}_blind_rev45.json")
            fwd_arr = json.load(open(fwd_fn, encoding="utf-8"))
            rev_arr = json.load(open(rev_fn, encoding="utf-8"))
            assert len(fwd_arr) == 45 and len(rev_arr) == 45, f"Expected 45 in {fwd_fn}/{rev_fn}"

            fwd_by_pid = {}
            for item in fwd_arr:
                pinfo = m_to_pair[item["match_id"]]
                fwd_by_pid[pinfo["pair_id"]] = (item, pinfo)

            rev_by_pid = {}
            for item in rev_arr:
                rk = rev_key[item["match_id"]]
                pid = rk["orig_pair_id"] if isinstance(rk, dict) else rk
                rev_by_pid[pid] = item

            slot_a_wins = 0
            nli_discordant = 0
            confs = []
            consistent = 0
            flipped = 0
            flip_to_a = 0
            flip_to_b = 0

            cands = sorted(list({p["cand_i"]["cand_id"] for p in stim_pairs} | {p["cand_j"]["cand_id"] for p in stim_pairs}))
            naive_fwd_wins = Counter({c: 0.0 for c in cands})
            bi_wins = Counter({c: 0.0 for c in cands})

            for pid, (f_item, pinfo) in fwd_by_pid.items():
                r_item = rev_by_pid[pid]
                ci, cj = pinfo["cand_i"], pinfo["cand_j"]

                for v in (f_item, r_item):
                    w = str(v["winner"]).strip().upper()
                    if w == "A":
                        slot_a_wins += 1
                    confs.append(float(v.get("confidence", 75)))
                    votes_a = sum(1 for k in ("science", "feasibility", "novelty") if str(v.get(k, "")).upper() == "A")
                    votes_b = sum(1 for k in ("science", "feasibility", "novelty") if str(v.get(k, "")).upper() == "B")
                    if (w == "A" and votes_b > votes_a) or (w == "B" and votes_a > votes_b):
                        nli_discordant += 1

                wf = str(f_item["winner"]).strip().upper()
                wr = str(r_item["winner"]).strip().upper()
                if wf == "A":
                    naive_fwd_wins[ci] += 1.0
                    bi_wins[ci] += 0.5
                else:
                    naive_fwd_wins[cj] += 1.0
                    bi_wins[cj] += 0.5
                if wr == "A":
                    bi_wins[cj] += 0.5
                else:
                    bi_wins[ci] += 0.5

                if (wf == "A" and wr == "B") or (wf == "B" and wr == "A"):
                    consistent += 1
                else:
                    flipped += 1
                    if wf == "A" and wr == "A":
                        flip_to_a += 1
                    else:
                        flip_to_b += 1

            rank_naive = [c for c, _ in sorted(naive_fwd_wins.items(), key=lambda x: (-x[1], x[0]))]
            rank_oabtl = [c for c, _ in sorted(bi_wins.items(), key=lambda x: (-x[1], x[0]))]
            tau, _ = stats.kendalltau(
                [rank_naive.index(c) for c in cands],
                [rank_oabtl.index(c) for c in cands],
            )
            binom_p = stats.binomtest(slot_a_wins, 90, 0.5, alternative="two-sided").pvalue

            jc_fn = f"t2_{dis}_{tier}_90verdicts.json"
            jc_verdicts = json.load(open(os.path.join(GROK_DIR, jc_fn), encoding="utf-8"))
            jc_by_pair = {}
            jc_slot_a = 0
            for v in jc_verdicts:
                jc_by_pair.setdefault(v["pair_id"], {})[v["direction"]] = v
                if str(v["winner"]).strip().upper() == "A":
                    jc_slot_a += 1
            jc_flipped = sum(
                1 for pid, dm in jc_by_pair.items()
                if "fwd" in dm and "rev" in dm and not (
                    (str(dm["fwd"]["winner"]).strip().upper() == "A" and str(dm["rev"]["winner"]).strip().upper() == "B")
                    or (str(dm["fwd"]["winner"]).strip().upper() == "B" and str(dm["rev"]["winner"]).strip().upper() == "A")
                )
            )

            t2_summary[f"{dis}_{tier}"] = {
                "n_verdicts": 90,
                "n_pairs": 45,
                "slot_a_win_count": slot_a_wins,
                "slot_a_win_rate_pct": round(100.0 * slot_a_wins / 90.0, 2),
                "slot_a_binom_p": float(binom_p),
                "consistent_pairs": consistent,
                "consistent_rate_pct": round(100.0 * consistent / 45.0, 2),
                "flipped_pairs": flipped,
                "flip_rate_pct": round(100.0 * flipped / 45.0, 2),
                "flip_both_slot_a": flip_to_a,
                "flip_both_slot_b": flip_to_b,
                "nli_discordant_count": nli_discordant,
                "nli_discordant_rate_pct": round(100.0 * nli_discordant / 90.0, 2),
                "mean_confidence": round(float(np.mean(confs)), 2),
                "naive_fwd_top3": rank_naive[:3],
                "oabtl_top3": rank_oabtl[:3],
                "top1_changed_by_oabtl": rank_naive[0] != rank_oabtl[0],
                "kendall_tau_naive_vs_oabtl": round(float(tau), 4),
                "joint_context_flip_rate_pct": round(100.0 * jc_flipped / 45.0, 2),
                "joint_context_slot_a_pct": round(100.0 * jc_slot_a / 90.0, 2),
            }

    for tier in ["high", "fast"]:
        d_sub = t2_summary[f"dAMD_{tier}"]
        a_sub = t2_summary[f"ALS_{tier}"]
        tot_flips = d_sub["flipped_pairs"] + a_sub["flipped_pairs"]
        tot_slot_a = d_sub["slot_a_win_count"] + a_sub["slot_a_win_count"]
        tot_nli = d_sub["nli_discordant_count"] + a_sub["nli_discordant_count"]
        t2_summary[f"pooled_{tier}"] = {
            "n_verdicts": 180,
            "n_pairs": 90,
            "flipped_pairs": tot_flips,
            "flip_rate_pct": round(100.0 * tot_flips / 90.0, 2),
            "slot_a_win_count": tot_slot_a,
            "slot_a_win_rate_pct": round(100.0 * tot_slot_a / 180.0, 2),
            "slot_a_binom_p": float(stats.binomtest(tot_slot_a, 180, 0.5, alternative="two-sided").pvalue),
            "nli_discordant_count": tot_nli,
            "nli_discordant_rate_pct": round(100.0 * tot_nli / 180.0, 2),
        }
    summary["arena1_t2_grok"] = t2_summary

    # 2. Arena 2: Experiment B 3-Arm Clinical Citation Gating (High vs Fast)
    cache = json.load(open(PUBMED_CACHE_PATH, encoding="utf-8")) if os.path.exists(PUBMED_CACHE_PATH) else {}
    stim_b = json.load(open(os.path.join(STIM_DIR, "expB_14domains_h1.json"), encoding="utf-8"))
    dom_mech_map = {d["domain_id"]: (d["domain"], d["h1_mechanism"]) for d in stim_b["domains"]}

    all_new_pmids = []
    for tier in ["high", "fast"]:
        arr = json.load(open(os.path.join(GROK_DIR, f"expB_{tier}_42lists.json"), encoding="utf-8"))
        for obj in arr:
            for s in obj["slots"]:
                p_str = str(s.get("pmid", "")).strip()
                if re.match(r"^\d+$", p_str):
                    all_new_pmids.append(p_str)

    fetch_pubmed_batch(all_new_pmids, cache)
    with open(PUBMED_CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2, ensure_ascii=False)

    expb_grok = {}
    for tier in ["high", "fast"]:
        arr = json.load(open(os.path.join(GROK_DIR, f"expB_{tier}_42lists.json"), encoding="utf-8"))
        tier_res = {}
        for arm in ["as_discovered", "abstain_probe", "gated"]:
            sub = [x for x in arr if x["arm"] == arm]
            tot = 0
            abstained = 0
            fabricated = 0
            trojan = 0
            grounded = 0
            for obj in sub:
                did = obj["domain_id"]
                dname, mech = dom_mech_map[did]
                for s in obj["slots"]:
                    tot += 1
                    p_str = str(s.get("pmid", "")).strip()
                    if p_str.upper() == "NO_CITATION" or not re.match(r"^\d+$", p_str):
                        abstained += 1
                    else:
                        rec = cache.get(p_str, {"exists": False})
                        if not rec.get("exists"):
                            fabricated += 1
                        elif check_domain_topic_match(dname, mech, rec):
                            grounded += 1
                        else:
                            trojan += 1
            emitted = tot - abstained
            tier_res[arm] = {
                "total_slots": tot,
                "abstained_slots": abstained,
                "abstain_rate_pct": round(100.0 * abstained / max(1, tot), 2),
                "emitted_slots": emitted,
                "fabricated_slots": fabricated,
                "fabricated_rate_of_total_pct": round(100.0 * fabricated / max(1, tot), 2),
                "trojan_horse_slots": trojan,
                "trojan_rate_of_total_pct": round(100.0 * trojan / max(1, tot), 2),
                "trojan_rate_of_emitted_pct": round(100.0 * trojan / max(1, emitted), 2) if emitted > 0 else 0.0,
                "grounded_slots": grounded,
                "grounded_rate_of_total_pct": round(100.0 * grounded / max(1, tot), 2),
                "grounded_rate_of_emitted_pct": round(100.0 * grounded / max(1, emitted), 2) if emitted > 0 else 0.0,
                "total_ungrounded_slots": fabricated + trojan,
                "total_ungrounded_rate_of_total_pct": round(100.0 * (fabricated + trojan) / max(1, tot), 2),
            }
        # Fisher's exact test: as_discovered vs gated ungrounded slots
        u_as = tier_res["as_discovered"]["total_ungrounded_slots"]
        t_as = tier_res["as_discovered"]["total_slots"]
        u_gt = tier_res["gated"]["total_ungrounded_slots"]
        t_gt = tier_res["gated"]["total_slots"]
        _, p_fisher = stats.fisher_exact([[u_as, t_as - u_as], [u_gt, t_gt - u_gt]])
        tier_res["gating_fisher_p"] = float(p_fisher)
        tier_res["gating_ungrounded_delta_pp"] = round(
            tier_res["gated"]["total_ungrounded_rate_of_total_pct"]
            - tier_res["as_discovered"]["total_ungrounded_rate_of_total_pct"],
            2,
        )
        expb_grok[tier] = tier_res
    summary["arena2_expB_grok"] = expb_grok

    # 3. Arena 3: Experiment C Mendelian HPO Perturbation (High vs Fast)
    truth_map = json.load(open(TRUTH_KEY_PATH, encoding="utf-8"))
    expc_grok = {}
    for tier in ["high", "fast"]:
        arr = json.load(open(os.path.join(GROK_DIR, f"expC_{tier}_60preds.json"), encoding="utf-8"))
        by_dose = {0: [], 25: [], 50: []}
        all_hits, all_confs, all_pids = [], [], []
        fp_counter = Counter()
        for item in arr:
            pid = item["pair_id"]
            dose = int(item["dose_target"])
            preds = [str(x).strip().upper() for x in item.get("predictions", [])[:10]]
            t_info = truth_map[pid]
            gs = set([t_info["gene_symbol"].upper()] + [a.upper() for a in t_info.get("aliases", [])])
            hit = int(any(p in gs for p in preds))
            by_dose[dose].append(hit)
            all_hits.append(hit)
            all_confs.append(float(item.get("confidence", 75)))
            all_pids.append(pid)
            for p in preds:
                if p not in gs:
                    fp_counter[p] += 1

        raw_ece = compute_ece(all_confs, all_hits)
        cal_ece = loro_platt_ece(all_confs, all_hits, all_pids)
        expc_grok[tier] = {
            "n_total": len(arr),
            "overall_hit10_count": int(sum(all_hits)),
            "overall_hit10_pct": round(100.0 * np.mean(all_hits), 2),
            "hit10_dose0_pct": round(100.0 * np.mean(by_dose[0]), 2),
            "hit10_dose25_pct": round(100.0 * np.mean(by_dose[25]), 2),
            "hit10_dose50_pct": round(100.0 * np.mean(by_dose[50]), 2),
            "mean_confidence_pct": round(float(np.mean(all_confs)), 2),
            "overconfidence_gap_pct": round(float(np.mean(all_confs) - 100.0 * np.mean(all_hits)), 2),
            "raw_ece": round(raw_ece, 4),
            "loro_platt_ece": round(cal_ece, 4),
            "ece_reduction_pct": round(100.0 * (raw_ece - cal_ece) / max(1e-6, raw_ece), 2),
            "top_false_positive_attractors": fp_counter.most_common(8),
        }
    summary["arena3_expC_grok"] = expc_grok

    # 4. Telemetry Summary across all chunk telemetry files
    chunk_dir = os.path.join(GROK_DIR, "chunks")
    telem = []
    if os.path.exists(chunk_dir):
        for fn in sorted(os.listdir(chunk_dir)):
            if fn.endswith("_telem.json"):
                telem.append(json.load(open(os.path.join(chunk_dir, fn), encoding="utf-8")))
    by_t = {"high": [], "fast": []}
    for r in telem:
        by_t.setdefault(r["tier"], []).append(r.get("usage", {}))
    summary["telemetry"] = {
        "total_cli_calls": len(telem),
        "high_reasoning_tokens_total": sum(u.get("reasoning_tokens", 0) for u in by_t["high"]),
        "fast_reasoning_tokens_total": sum(u.get("reasoning_tokens", 0) for u in by_t["fast"]),
        "all_reasoning_tokens_total": sum(u.get("reasoning_tokens", 0) for u in by_t["high"] + by_t["fast"]),
        "high_total_tokens": sum(u.get("total_tokens", 0) for u in by_t["high"]),
        "fast_total_tokens": sum(u.get("total_tokens", 0) for u in by_t["fast"]),
        "all_total_tokens": sum(u.get("total_tokens", 0) for u in by_t["high"] + by_t["fast"]),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print("Saved Grok Cross-Ecosystem Summary to:", OUTPUT_PATH)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
