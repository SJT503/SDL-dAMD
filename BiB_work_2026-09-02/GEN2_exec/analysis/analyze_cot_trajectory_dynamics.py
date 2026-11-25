#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
analyze_cot_trajectory_dynamics.py
White-Box Chain-of-Thought (CoT) Trajectory & Commitment Dynamics Analyzer
across 8,973 raw JSON telemetry traces (35.58M reasoning tokens) in GEN2_exec/data/raw/,
plus 3-Arm Experiment B Deconfounded Citation Gating & Zero-Leakage CoT-SRAD Rectification.

Complies with PROJECT_CONSTITUTION.md §4 Entry 5-Checks.
"""

import os
import sys
import glob
import json
import re
from collections import Counter, defaultdict
import numpy as np
from scipy import stats

# ==============================================================================
# Entry 5-Checks (PROJECT_CONSTITUTION.md §4)
# ==============================================================================
BASE_ROOT = r"D:\Papers\Robin_Nature_2026"
EXEC_DIR = os.path.join(BASE_ROOT, "BiB_work_2026-09-02", "GEN2_exec")
DATA_DIR = os.path.join(EXEC_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
CALLS_LOG_PATH = os.path.join(DATA_DIR, "calls_log.jsonl")
EXPC_RESULTS_PATH = os.path.join(RUNS_DIR, "expC_v4", "results.jsonl")
EXPB_PROMPTS_PATH = os.path.join(EXEC_DIR, "expB_prompts.json")
OUTPUT_PATH = os.path.join(EXEC_DIR, "analysis", "cot_trajectory_dynamics_summary.json")

assert os.path.abspath(EXEC_DIR).startswith(BASE_ROOT), "Check 1 Failed: Not inside Robin_Nature_2026 root"
for req_file in [CALLS_LOG_PATH, EXPC_RESULTS_PATH, EXPB_PROMPTS_PATH]:
    assert os.path.exists(req_file), f"Check 2 Failed: Missing required input {req_file}"

calls_list = [json.loads(line) for line in open(CALLS_LOG_PATH, encoding="utf-8")]
assert len(calls_list) == 9130, f"Check 3 Failed: Expected 9130 calls, got {len(calls_list)}"
res_c_list = [json.loads(line) for line in open(EXPC_RESULTS_PATH, encoding="utf-8")]
assert len(res_c_list) == 630, f"Check 3b Failed: Expected 630 Exp C rows, got {len(res_c_list)}"


def load_raw_cot(rel_path):
    if not rel_path:
        return ""
    full_p = os.path.join(EXEC_DIR, rel_path)
    if not os.path.exists(full_p):
        return ""
    try:
        d = json.load(open(full_p, encoding="utf-8"))
        return d.get("choices", [{}])[0].get("message", {}).get("reasoning_content") or ""
    except Exception:
        return ""


def analyze_all():
    summary = {}
    calls_by_id = {c["call_id"]: c for c in calls_list if c.get("call_id")}

    # ==========================================================================
    # 1. Experiment B: 3-Arm Deconfounded Analysis + CoT Parametric PMID Dredging
    # ==========================================================================
    expb_summary_path = os.path.join(EXEC_DIR, "analysis", "results_summary.json")
    prev_summary = json.load(open(expb_summary_path, encoding="utf-8")) if os.path.exists(expb_summary_path) else {}

    expb_cot = {}
    for arm in ["as_discovered", "abstain_probe", "gated"]:
        arm_dir = os.path.join(RUNS_DIR, "expB", arm)
        h_files = sorted(glob.glob(os.path.join(arm_dir, "B*_h*.json")))
        total_slots = 0
        abstain_slots = 0
        emitted_pmids = []
        for hf in h_files:
            arr = json.load(open(hf, encoding="utf-8"))
            for item in arr:
                total_slots += 1
                p_str = str(item.get("pmid", "")).strip()
                if p_str.upper() == "NO_CITATION" or not re.match(r"^\d+$", p_str):
                    abstain_slots += 1
                else:
                    emitted_pmids.append(p_str)

        # Raw CoT traces for this arm
        recs = [
            x for x in calls_list
            if x.get("about", {}).get("experiment") == "B"
            and x.get("about", {}).get("stage") == 2
            and x.get("about", {}).get("arm") == arm
            and x.get("raw_path")
        ]
        pmid_mentions, uniq_pmids, uncert_counts, r_tokens, cot_chars = [], [], [], [], []
        year_mentions = []
        for r in recs:
            rc = load_raw_cot(r.get("raw_path"))
            if not rc:
                continue
            cands = re.findall(r"\b[1-3]\d{6,7}\b", rc)
            pmid_mentions.append(len(cands))
            uniq_pmids.append(len(set(cands)))
            uncert = len(re.findall(
                r"(not sure|not certain|hmm|maybe|perhaps|wait|let me recall|i think|unsure|\?)",
                rc.lower()
            ))
            uncert_counts.append(uncert)
            r_tokens.append(r.get("reasoning_tokens") or 0)
            cot_chars.append(len(rc))
            yrs = re.findall(r"\b(19[89]\d|20[012]\d)\b", rc)
            year_mentions.append(len(yrs))

        expb_cot[arm] = {
            "n_files": len(h_files),
            "total_slots": total_slots,
            "abstain_slots": abstain_slots,
            "abstain_rate_pct": round(100.0 * abstain_slots / max(1, total_slots), 2),
            "emitted_slots": len(emitted_pmids),
            "emitted_rate_pct": round(100.0 * len(emitted_pmids) / max(1, total_slots), 2),
            "n_cot_traces": len(pmid_mentions),
            "median_reasoning_tokens": float(np.median(r_tokens)),
            "iqr_reasoning_tokens": [float(np.percentile(r_tokens, 25)), float(np.percentile(r_tokens, 75))],
            "mean_pmid_mentions_in_cot": round(float(np.mean(pmid_mentions)), 2),
            "median_pmid_mentions_in_cot": float(np.median(pmid_mentions)),
            "mean_unique_pmids_trialed_in_cot": round(float(np.mean(uniq_pmids)), 2),
            "median_unique_pmids_trialed_in_cot": float(np.median(uniq_pmids)),
            "mean_uncertainty_markers_in_cot": round(float(np.mean(uncert_counts)), 2),
            "median_uncertainty_markers_in_cot": float(np.median(uncert_counts)),
            "mean_year_anchors_in_cot": round(float(np.mean(year_mentions)), 2),
        }

    # Kruskal-Wallis & Mann-Whitney across the 3 arms on unique PMIDs trialed in CoT
    recs_asd = [len(set(re.findall(r"\b[1-3]\d{6,7}\b", load_raw_cot(x.get("raw_path")))))
                for x in calls_list if x.get("about", {}).get("experiment") == "B" and x.get("about", {}).get("stage") == 2 and x.get("about", {}).get("arm") == "as_discovered" and load_raw_cot(x.get("raw_path"))]
    recs_abs = [len(set(re.findall(r"\b[1-3]\d{6,7}\b", load_raw_cot(x.get("raw_path")))))
                for x in calls_list if x.get("about", {}).get("experiment") == "B" and x.get("about", {}).get("stage") == 2 and x.get("about", {}).get("arm") == "abstain_probe" and load_raw_cot(x.get("raw_path"))]
    recs_gat = [len(set(re.findall(r"\b[1-3]\d{6,7}\b", load_raw_cot(x.get("raw_path")))))
                for x in calls_list if x.get("about", {}).get("experiment") == "B" and x.get("about", {}).get("stage") == 2 and x.get("about", {}).get("arm") == "gated" and load_raw_cot(x.get("raw_path"))]

    kw_stat, kw_p = stats.kruskal(recs_asd, recs_abs, recs_gat)
    mw_asd_gat = stats.mannwhitneyu(recs_asd, recs_gat, alternative="two-sided")
    mw_abs_gat = stats.mannwhitneyu(recs_abs, recs_gat, alternative="two-sided")
    expb_cot["statistical_tests"] = {
        "kruskal_unique_pmids_H": float(kw_stat),
        "kruskal_unique_pmids_p": float(kw_p),
        "mannwhitney_as_discovered_vs_gated_U": float(mw_asd_gat.statistic),
        "mannwhitney_as_discovered_vs_gated_p": float(mw_asd_gat.pvalue),
        "mannwhitney_abstain_probe_vs_gated_U": float(mw_abs_gat.statistic),
        "mannwhitney_abstain_probe_vs_gated_p": float(mw_abs_gat.pvalue),
    }
    summary["expB_cot_dredging_dynamics"] = expb_cot

    # ==========================================================================
    # 2. Experiment C: Instant-Recognition Law, Self-Pruning vs Ceiling-Spin, & CoT-SRAD
    # ==========================================================================
    pred_vocab = set()
    for r in res_c_list:
        for p in (r.get("predictions") or []):
            pred_vocab.add(p)

    expc_dynamics = {}
    pooled_base_hits = 0
    pooled_srad_hits = 0
    pooled_b_only = 0
    pooled_c_only = 0

    for v in ["glm", "deepseek"]:
        sub = [r for r in res_c_list if r["vendor"] == v]
        sub_full = [r for r in sub if len(r.get("predictions") or []) == 10]
        sub_empty = [r for r in sub if len(r.get("predictions") or []) == 0]
        hits_all = [r for r in sub if r["hit10"] == 1]
        miss_all = [r for r in sub if r["hit10"] == 0]
        miss_full = [r for r in sub_full if r["hit10"] == 0]

        pos_true_in_hits = []
        pos_true_in_miss_full = []
        pos_true_in_empty = []
        pos_attractor_in_miss = []
        uniq_caps_hits, uniq_caps_miss = [], []

        ghost_in_miss_full = 0
        ghost_in_empty = 0

        # Identify LODO attractors
        other_df_global = Counter()
        for r2 in res_c_list:
            for p in set(r2.get("predictions") or []):
                other_df_global[p] += 1
        top_attractors = [g for g, c in other_df_global.most_common(10) if c >= 12]

        base_hits = 0
        srad_hits = 0
        b_only = 0
        c_only = 0

        for r in sub:
            clog = calls_by_id.get(r["call_id"])
            rc = load_raw_cot(clog.get("raw_path")) if clog else ""
            gs = [r["gene_symbol"]] + (r.get("aliases") or [])
            found_pos = None
            for g in gs:
                if not g or len(g) < 2:
                    continue
                m = re.search(r"\b" + re.escape(g) + r"\b", rc)
                if m:
                    p = m.start() / max(1, len(rc))
                    if found_pos is None or p < found_pos:
                        found_pos = p

            caps = set(re.findall(r"\b[A-Z][A-Z0-9]{2,9}\b", rc))
            if r["hit10"] == 1:
                uniq_caps_hits.append(len(caps))
                if found_pos is not None:
                    pos_true_in_hits.append(found_pos)
            else:
                uniq_caps_miss.append(len(caps))
                # check attractor position
                for att in top_attractors[:5]:
                    ma = re.search(r"\b" + re.escape(att) + r"\b", rc)
                    if ma:
                        pos_attractor_in_miss.append(ma.start() / max(1, len(rc)))
                        break
                if len(r.get("predictions") or []) == 10:
                    if found_pos is not None:
                        ghost_in_miss_full += 1
                        pos_true_in_miss_full.append(found_pos)
                else:
                    if found_pos is not None:
                        ghost_in_empty += 1
                        pos_true_in_empty.append(found_pos)

            # Strict Zero-Leakage Leave-One-Disease-Out CoT-SRAD
            other_df = Counter()
            for r2 in res_c_list:
                if r2["pair_id"] == r["pair_id"]:
                    continue
                for p in set(r2.get("predictions") or []):
                    other_df[p] += 1
            lodo_attractors = {g for g, c in other_df.items() if c >= 12}

            preds = list(r.get("predictions") or [])[:10]
            if len(preds) < 10 and rc:
                mentions = [
                    m.group(1) for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,9})\b", rc)
                    if m.group(1) in pred_vocab and m.group(1) not in lodo_attractors
                ]
                freq = Counter(mentions)
                harvested = [g for g, _ in freq.most_common(10)]
                new_preds = (preds + [g for g in harvested if g not in preds])[:10]
            elif len(preds) == 10 and rc:
                kept = [p for p in preds if p not in lodo_attractors]
                if len(kept) < 10:
                    mentions = [
                        m.group(1) for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,9})\b", rc)
                        if m.group(1) in pred_vocab and m.group(1) not in lodo_attractors and m.group(1) not in kept
                    ]
                    freq = Counter(mentions)
                    repl = [g for g, _ in freq.most_common(10 - len(kept))]
                    new_preds = (kept + repl + preds)[:10]
                else:
                    new_preds = preds
            else:
                new_preds = preds

            gs_set = set(gs)
            b_hit = int(r["hit10"] == 1)
            s_hit = int(any(p in gs_set for p in new_preds))
            base_hits += b_hit
            srad_hits += s_hit
            if b_hit == 1 and s_hit == 0:
                b_only += 1
            elif b_hit == 0 and s_hit == 1:
                c_only += 1

        pooled_base_hits += base_hits
        pooled_srad_hits += srad_hits
        pooled_b_only += b_only
        pooled_c_only += c_only

        mcnemar_p = float(stats.binomtest(c_only, b_only + c_only, 0.5).pvalue) if (b_only + c_only) > 0 else 1.0
        expc_dynamics[v] = {
            "n_total": len(sub),
            "n_full_10": len(sub_full),
            "n_ceiling_truncated": len(sub_empty),
            "median_first_true_gene_pos_in_hits": round(float(np.median(pos_true_in_hits)), 4),
            "iqr_first_true_gene_pos_in_hits": [
                round(float(np.percentile(pos_true_in_hits, 25)), 4),
                round(float(np.percentile(pos_true_in_hits, 75)), 4),
            ],
            "n_miss_full": len(miss_full),
            "self_pruned_ghost_in_miss_full": ghost_in_miss_full,
            "self_pruned_ghost_rate_pct": round(100.0 * ghost_in_miss_full / max(1, len(miss_full)), 2),
            "median_ghost_pos_in_miss_full": round(float(np.median(pos_true_in_miss_full)), 4) if pos_true_in_miss_full else None,
            "true_gene_in_ceiling_truncated": ghost_in_empty,
            "true_gene_in_ceiling_truncated_rate_pct": round(100.0 * ghost_in_empty / max(1, len(sub_empty)), 2),
            "median_true_gene_pos_in_ceiling_truncated": round(float(np.median(pos_true_in_empty)), 4) if pos_true_in_empty else None,
            "mean_unique_symbols_in_cot_hit": round(float(np.mean(uniq_caps_hits)), 1),
            "mean_unique_symbols_in_cot_miss": round(float(np.mean(uniq_caps_miss)), 1),
            "base_hit10_count": base_hits,
            "base_hit10_pct": round(100.0 * base_hits / len(sub), 2),
            "cot_srad_hit10_count": srad_hits,
            "cot_srad_hit10_pct": round(100.0 * srad_hits / len(sub), 2),
            "cot_srad_net_gain": srad_hits - base_hits,
            "mcnemar_b_only": b_only,
            "mcnemar_c_only": c_only,
            "mcnemar_exact_p": mcnemar_p,
        }

    pooled_mcnemar_p = float(stats.binomtest(pooled_c_only, pooled_b_only + pooled_c_only, 0.5).pvalue)
    expc_dynamics["pooled"] = {
        "n_total": 630,
        "base_hit10_count": pooled_base_hits,
        "base_hit10_pct": round(100.0 * pooled_base_hits / 630.0, 2),
        "cot_srad_hit10_count": pooled_srad_hits,
        "cot_srad_hit10_pct": round(100.0 * pooled_srad_hits / 630.0, 2),
        "cot_srad_net_gain": pooled_srad_hits - pooled_base_hits,
        "mcnemar_b_only": pooled_b_only,
        "mcnemar_c_only": pooled_c_only,
        "mcnemar_exact_p": pooled_mcnemar_p,
        "pooled_self_pruned_ghost_count": expc_dynamics["glm"]["self_pruned_ghost_in_miss_full"] + expc_dynamics["deepseek"]["self_pruned_ghost_in_miss_full"],
        "pooled_miss_full_count": expc_dynamics["glm"]["n_miss_full"] + expc_dynamics["deepseek"]["n_miss_full"],
        "pooled_self_pruned_ghost_rate_pct": round(
            100.0 * (expc_dynamics["glm"]["self_pruned_ghost_in_miss_full"] + expc_dynamics["deepseek"]["self_pruned_ghost_in_miss_full"])
            / (expc_dynamics["glm"]["n_miss_full"] + expc_dynamics["deepseek"]["n_miss_full"]), 2
        ),
        "pooled_ceiling_truncated_ghost_count": expc_dynamics["glm"]["true_gene_in_ceiling_truncated"] + expc_dynamics["deepseek"]["true_gene_in_ceiling_truncated"],
        "pooled_ceiling_truncated_count": expc_dynamics["glm"]["n_ceiling_truncated"] + expc_dynamics["deepseek"]["n_ceiling_truncated"],
        "pooled_ceiling_truncated_ghost_rate_pct": round(
            100.0 * (expc_dynamics["glm"]["true_gene_in_ceiling_truncated"] + expc_dynamics["deepseek"]["true_gene_in_ceiling_truncated"])
            / (expc_dynamics["glm"]["n_ceiling_truncated"] + expc_dynamics["deepseek"]["n_ceiling_truncated"]), 2
        ),
    }
    summary["expC_cot_trajectory_and_srad"] = expc_dynamics

    # ==========================================================================
    # 3. Tournament I & Tournament II CoT Attention & Commitment Dynamics
    # ==========================================================================
    t1_recs = [x for x in calls_list if x.get("about", {}).get("step") == 2 and x.get("raw_path")]
    t2_recs = [x for x in calls_list if x.get("about", {}).get("step") == 4 and x.get("raw_path")]

    # Compute decile mention profile of Candidate/Option A vs B across CoT deciles 0..9
    decile_a_share_t1 = np.zeros((len(t1_recs), 10))
    valid_t1 = 0
    for r in t1_recs:
        rc = load_raw_cot(r.get("raw_path"))
        if len(rc) < 200:
            continue
        L = len(rc)
        row = []
        for d_idx in range(10):
            seg = rc[int(d_idx * L / 10): int((d_idx + 1) * L / 10)]
            ca = len(re.findall(r"\b(option\s*a|candidate\s*a|hypothesis\s*a|mechanism\s*a)\b", seg, re.I))
            cb = len(re.findall(r"\b(option\s*b|candidate\s*b|hypothesis\s*b|mechanism\s*b)\b", seg, re.I))
            row.append(ca / (ca + cb) if (ca + cb) > 0 else 0.5)
        decile_a_share_t1[valid_t1, :] = row
        valid_t1 += 1
    decile_a_share_t1 = decile_a_share_t1[:valid_t1, :]

    decile_a_share_t2 = np.zeros((len(t2_recs), 10))
    valid_t2 = 0
    pivots_t2 = []
    for r in t2_recs:
        rc = load_raw_cot(r.get("raw_path"))
        if len(rc) < 200:
            continue
        L = len(rc)
        row = []
        for d_idx in range(10):
            seg = rc[int(d_idx * L / 10): int((d_idx + 1) * L / 10)]
            ca = len(re.findall(r"\b(option\s*a|candidate\s*a)\b", seg, re.I))
            cb = len(re.findall(r"\b(option\s*b|candidate\s*b)\b", seg, re.I))
            row.append(ca / (ca + cb) if (ca + cb) > 0 else 0.5)
        decile_a_share_t2[valid_t2, :] = row
        valid_t2 += 1
        pivots_t2.append(len(re.findall(r"\b(however|but|on the other hand|conversely|wait|although|yet|nevertheless)\b", rc, re.I)))
    decile_a_share_t2 = decile_a_share_t2[:valid_t2, :]

    summary["tournament_cot_attention_profile"] = {
        "t1_n_traces": int(valid_t1),
        "t1_decile_slot_a_attention_share": [round(float(x), 4) for x in np.mean(decile_a_share_t1, axis=0)],
        "t1_early_q1_slot_a_share": round(float(np.mean(decile_a_share_t1[:, :3])), 4),
        "t1_middle_q23_slot_a_share": round(float(np.mean(decile_a_share_t1[:, 3:7])), 4),
        "t1_final_decile_slot_a_share": round(float(np.mean(decile_a_share_t1[:, 9])), 4),
        "t2_n_traces": int(valid_t2),
        "t2_decile_slot_a_attention_share": [round(float(x), 4) for x in np.mean(decile_a_share_t2, axis=0)],
        "t2_early_q1_slot_a_share": round(float(np.mean(decile_a_share_t2[:, :3])), 4),
        "t2_final_decile_slot_a_share": round(float(np.mean(decile_a_share_t2[:, 9])), 4),
        "t2_mean_adversarial_pivots_per_trace": round(float(np.mean(pivots_t2)), 2),
        "t2_median_adversarial_pivots_per_trace": float(np.median(pivots_t2)),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print("Saved CoT trajectory dynamics summary to:", OUTPUT_PATH)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    analyze_all()
