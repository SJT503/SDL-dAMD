#!/usr/bin/env python3
"""
nc_v2_compute_exact_plot_arrays.py -- Deterministic computation of exact empirical
arrays for Figures 3C, 4C, 5A, 6A and Supplementary Figures 1C, 2B, eliminating all
parametric/interpolated approximations and unifying SEs across plots, tables, and Source Data.
"""
from gate import gate, canary_gate, retry_limit

import csv
import json
import math
import os
from collections import Counter, defaultdict
import numpy as np

gate(__file__)

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_DIR = os.path.dirname(HERE)
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
DATA_DIR = os.path.join(EXEC_DIR, "data")
OUT_JSON = os.path.join(HERE, "nc_v2_exact_plot_arrays.json")


def hunter_mm_top5(wins_mat: np.ndarray, comp_mat: np.ndarray, max_iter: int = 80) -> tuple:
    """Exact Hunter MM BTL solver with Jeffreys alpha=0.5 smoothing matching btl.py."""
    m = wins_mat.shape[0]
    w_s = wins_mat + 0.5 * (comp_mat > 0)
    n_s = comp_mat + 1.0 * (comp_mat > 0)
    np.fill_diagonal(w_s, 0.0)
    np.fill_diagonal(n_s, 0.0)
    w_i = w_s.sum(axis=1)
    pi = np.ones(m, dtype=float)
    for _ in range(max_iter):
        denom = (n_s / (pi[:, None] + pi[None, :])).sum(axis=1)
        pi_new = w_i / np.maximum(denom, 1e-12)
        pi_new /= np.exp(np.mean(np.log(np.maximum(pi_new, 1e-12))))
        if np.max(np.abs(pi_new - pi)) < 1e-8:
            pi = pi_new
            break
        pi = pi_new
    top5 = tuple(sorted(int(x) for x in np.argsort(-pi)[:5]))
    return top5


@retry_limit(2)
def main():
    canary_gate(lambda: os.path.exists(os.path.join(HERE, "nc_upgrade_nli_scored_pairs.json")), "Verify NLI pairs JSON")

    # 1. Exact empirical DeBERTa-v3 NLI tail curves across 201 thresholds tau in [0, 1]
    nli = json.load(open(os.path.join(HERE, "nc_upgrade_nli_scored_pairs.json"), encoding="utf-8"))["t2_reversal_scored"]
    bias_dir = np.array([float(r["p_contra_max"]) for r in nli if r["is_pos_biased"]], dtype=float)
    cons_dir = np.array([float(r["p_contra_max"]) for r in nli if not r["is_pos_biased"]], dtype=float)
    bias_bi = np.array([float(r["p_contra_min"]) for r in nli if r["is_pos_biased"]], dtype=float)
    cons_bi = np.array([float(r["p_contra_min"]) for r in nli if not r["is_pos_biased"]], dtype=float)
    taus = np.linspace(0.0, 0.995, 200)
    fig4c_exact = {
        "n_biased": int(len(bias_dir)),
        "n_consistent": int(len(cons_dir)),
        "mean_biased_dir": round(float(np.mean(bias_dir)), 4),
        "mean_cons_dir": round(float(np.mean(cons_dir)), 4),
        "taus": [round(float(t), 4) for t in taus],
        "biased_dir_pct": [round(float(100.0 * np.mean(bias_dir > t)), 4) for t in taus],
        "cons_dir_pct": [round(float(100.0 * np.mean(cons_dir > t)), 4) for t in taus],
        "biased_bidir_pct": [round(float(100.0 * np.mean(bias_bi > t)), 4) for t in taus],
        "cons_bidir_pct": [round(float(100.0 * np.mean(cons_bi > t)), 4) for t in taus],
    }

    # 2. Exact empirical Verdict-Table Bootstrap Top-5 Jaccard draws for Fig 5A (2,000 fits -> 1,000 independent pairs per run)
    runs_12 = [
        "dAMD_blind_R1", "dAMD_blind_R2", "dAMD_blind_R3",
        "dAMD_retrieval_R1", "dAMD_retrieval_R2", "dAMD_retrieval_R3",
        "ALS_blind_R1", "ALS_blind_R2", "ALS_blind_R3",
        "ALS_retrieval_R1", "ALS_retrieval_R2", "ALS_retrieval_R3",
    ]
    rng = np.random.default_rng(20260902)
    fig5a_boot = {}
    for rid in runs_12:
        s4v = json.load(open(os.path.join(RUNS_DIR, rid, "step4_verdicts.json"), encoding="utf-8"))["verdicts"]
        m = 10
        valid_tuples = []
        for v in s4v.values():
            if v and not v.get("failed") and "pair" in v and v.get("winner_idx") is not None:
                ia, ib = int(v["pair"][0]), int(v["pair"][1])
                win_a = 1.0 if int(v["winner_idx"]) == ia else 0.0
                valid_tuples.append((ia, ib, win_a))
        n_v = len(valid_tuples)
        arr_a = np.array([t[0] for t in valid_tuples], dtype=int)
        arr_b = np.array([t[1] for t in valid_tuples], dtype=int)
        arr_w = np.array([t[2] for t in valid_tuples], dtype=float)

        top5_draws = []
        for _ in range(2000):
            pick = rng.integers(0, n_v, size=n_v)
            wm = np.zeros((m, m), dtype=float)
            cm = np.zeros((m, m), dtype=float)
            np.add.at(wm, (arr_a[pick], arr_b[pick]), arr_w[pick])
            np.add.at(wm, (arr_b[pick], arr_a[pick]), 1.0 - arr_w[pick])
            np.add.at(cm, (arr_a[pick], arr_b[pick]), 1.0)
            np.add.at(cm, (arr_b[pick], arr_a[pick]), 1.0)
            top5_draws.append(set(hunter_mm_top5(wm, cm)))

        j_samples = []
        for k in range(0, 2000, 2):
            s_u, s_v = top5_draws[k], top5_draws[k + 1]
            j_samples.append(round(len(s_u & s_v) / len(s_u | s_v), 4))
        fig5a_boot[rid] = {
            "empirical_jaccard_draws_1000": j_samples,
            "mean": round(float(np.mean(j_samples)), 4),
            "ci95": [round(float(np.percentile(j_samples, 2.5)), 4), round(float(np.percentile(j_samples, 97.5)), 4)],
        }

    # 3. Exact Fig 3C binomial SEs and External 3,871-HGNC Module 4a dose-response on DeepSeek & GLM
    s3 = json.load(open(os.path.join(HERE, "step3_expC_dim6_paradox_results.json"), encoding="utf-8"))
    cells = s3["expC_v4"]["descriptive_by_cell"]
    fig3c_exact = {"glm_del_topIC": {}, "deepseek_del_topIC": {}}
    for v_key, out_k in [("glm", "glm_del_topIC"), ("deepseek", "deepseek_del_topIC")]:
        for d in [0, 25, 50]:
            cd = cells[f"{v_key}__del_topIC__d{d}"]
            n_c = int(cd["n_calls"])
            p_c = float(cd["hit10_rate"])
            se_pct = 100.0 * math.sqrt(p_c * (1.0 - p_c) / n_c)
            fig3c_exact[out_k][str(d)] = {
                "n": n_c,
                "hit10_pct": round(100.0 * p_c, 2),
                "binomial_se_pct": round(se_pct, 2),
            }

    # Compute External-HGNC Module 4a dose-by-dose recall on canonical 630 calls (exact match to nc_upgrade_A3_A7)
    BASE = os.path.dirname(EXEC_DIR)
    STOP_TOKENS = {
        "AND", "THE", "FOR", "WITH", "FROM", "THAT", "THIS", "ARE", "WAS", "NOT",
        "GENE", "GENES", "OMIM", "HPO", "DNA", "RNA", "ATP", "GTP", "CNS", "MRI",
        "EEG", "EMG", "ECG", "AUTOSOMAL", "RECESSIVE", "DOMINANT", "TYPE", "SYNDROME",
    }
    hgnc_vocab = set()
    with open(os.path.join(BASE, "REDO_REVIEW_PACK_2026-09-02", "expC_candidate_pool.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            g = str(row.get("gene_symbol", "")).strip().upper()
            if len(g) >= 2 and g not in STOP_TOKENS:
                hgnc_vocab.add(g)

    canon_630 = [json.loads(l) for l in open(os.path.join(RUNS_DIR, "expC_v4", "results.jsonl"), encoding="utf-8") if l.strip()]
    calls_by_id = {}
    with open(os.path.join(DATA_DIR, "calls_log.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                calls_by_id[obj["call_id"]] = obj

    import re
    cot_tokens_by_call = {}
    cot_raw_by_call = {}
    for r in canon_630:
        clog = calls_by_id.get(r["call_id"])
        rp = clog.get("raw_path") if clog else None
        rc = ""
        if rp and os.path.exists(rp):
            try:
                d_raw = json.load(open(rp, encoding="utf-8"))
                msg = (d_raw.get("choices") or [{}])[0].get("message") or {}
                rc = msg.get("reasoning_content") or msg.get("reasoning") or ""
            except Exception:
                rc = ""
        cot_raw_by_call[r["call_id"]] = rc
        cot_tokens_by_call[r["call_id"]] = [m.group(1) for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,9})\b", rc)] if rc else []

    global_pred_df = Counter()
    pair_pred_df = defaultdict(Counter)
    for r in canon_630:
        for p in set(r.get("predictions") or []):
            global_pred_df[p] += 1
            pair_pred_df[r["pair_id"]][p] += 1

    ds_4a_by_dose = defaultdict(lambda: [0, 0])
    glm_4a_by_dose = defaultdict(lambda: [0, 0])
    ds_tot_4a = [0, 0]
    sf2b_ecdf = {}
    for arm in ["del_topIC", "del_lowIC_matched"]:
        for d in [25, 50]:
            sub_f = [
                100.0 * (r["n_pheno_terms_intact"] - r["n_pheno_terms_kept"]) / max(1, r["n_pheno_terms_intact"])
                for r in canon_630 if r["arm"] == arm and int(r["dose_target"]) == d
            ]
            sf2b_ecdf[f"{arm}_d{d}"] = {
                "n": len(sub_f),
                "mean_pct": round(float(np.mean(sub_f)), 2),
                "sorted_vals": [round(float(x), 3) for x in sorted(sub_f)],
            }

    decoy_miss = defaultdict(lambda: {"glm": 0, "deepseek": 0, "diseases": set()})
    for r in canon_630:
        pid = r["pair_id"]
        gs = {str(r["gene_symbol"]).upper()} | {str(a).upper() for a in (r.get("aliases") or []) if a}
        preds = list(r.get("predictions") or [])[:10]
        if not r["hit10"]:
            for p in preds:
                pu = str(p).upper()
                if pu not in gs:
                    decoy_miss[pu][r["vendor"]] += 1
                    decoy_miss[pu]["diseases"].add(pid)
        lodo_ban = {g for g, cnt in global_pred_df.items() if (cnt - pair_pred_df[pid].get(g, 0)) >= 12}
        toks = cot_tokens_by_call[r["call_id"]]
        if len(preds) < 10 and toks:
            freq = Counter(t for t in toks if t in hgnc_vocab and t not in lodo_ban)
            cand_c = [g for g, c in freq.most_common(20) if c >= 1 and g not in preds]
            preds_4a = (preds + cand_c)[:10]
        else:
            preds_4a = preds
        hit_4a = int(any(p in gs for p in preds_4a))
        if r["vendor"] == "deepseek":
            ds_tot_4a[0] += hit_4a
            ds_tot_4a[1] += 1
        if r["arm"] == "del_topIC":
            tgt = ds_4a_by_dose if r["vendor"] == "deepseek" else glm_4a_by_dose
            tgt[int(r["dose_target"])][0] += hit_4a
            tgt[int(r["dose_target"])][1] += 1

    top10_decoys = sorted(decoy_miss.items(), key=lambda kv: kv[1]["glm"] + kv[1]["deepseek"], reverse=True)[:10]
    fig3d_decoys = [
        {
            "gene": g,
            "glm_false_calls": v["glm"],
            "deepseek_false_calls": v["deepseek"],
            "total_false_calls": v["glm"] + v["deepseek"],
            "n_diseases": len(v["diseases"]),
        }
        for g, v in top10_decoys
    ]

    fig3c_exact["deepseek_module4a_overall"] = {"hits": ds_tot_4a[0], "n": ds_tot_4a[1], "hit10_pct": round(100.0 * ds_tot_4a[0] / ds_tot_4a[1], 2)}
    fig3c_exact["deepseek_module4a_del_topIC"] = {
        str(d): {"hits": ds_4a_by_dose[d][0], "n": ds_4a_by_dose[d][1], "hit10_pct": round(100.0 * ds_4a_by_dose[d][0] / max(1, ds_4a_by_dose[d][1]), 2)}
        for d in [0, 25, 50]
    }
    fig3c_exact["glm_module4a_del_topIC"] = {
        str(d): {"hits": glm_4a_by_dose[d][0], "n": glm_4a_by_dose[d][1], "hit10_pct": round(100.0 * glm_4a_by_dose[d][0] / max(1, glm_4a_by_dose[d][1]), 2)}
        for d in [0, 25, 50]
    }

    # 4. Exact Supp Fig 1C binomial SEs
    expb_all = json.load(open(os.path.join(HERE, "step1_expB_slots_scored.json"), encoding="utf-8"))
    sf1c_exact = {}
    for tk in ["high", "medium", "low"]:
        sub = [r for r in expb_all if r["arm"] == "as_discovered" and r["tier"] == tk]
        n_s = len(sub)
        p_s = sum(1 for r in sub if r["ungrounded"]) / n_s
        se_s = 100.0 * math.sqrt(p_s * (1.0 - p_s) / n_s)
        sf1c_exact[tk] = {"n": n_s, "ungrounded_pct": round(100.0 * p_s, 2), "binomial_se_pct": round(se_s, 2)}

    # 5. Exact White-Box CoT First-Mention Depth ECDF (Hits n=166, Self-Pruned Misses n=55, Ceiling Ghost Misses n=76)
    hits_depth_pct = []
    pruned_depth_pct = []
    ceil_ghost_depth_pct = []
    for r in canon_630:
        rc = cot_raw_by_call.get(r["call_id"], "")
        if not rc:
            continue
        gs = {str(r["gene_symbol"]).upper()} | {str(a).upper() for a in (r.get("aliases") or []) if a}
        first_pos = None
        for sym in gs:
            if not sym:
                continue
            m_sym = re.search(rf"\b{re.escape(sym)}\b", rc)
            if m_sym:
                pos = m_sym.start() / max(1, len(rc)) * 100.0
                if first_pos is None or pos < first_pos:
                    first_pos = pos
        if first_pos is None:
            continue
        preds = list(r.get("predictions") or [])[:10]
        if r["hit10"]:
            hits_depth_pct.append(round(float(first_pos), 4))
        elif len(preds) >= 10:
            pruned_depth_pct.append(round(float(first_pos), 4))
        else:
            ceil_ghost_depth_pct.append(round(float(first_pos), 4))

    hits_depth_pct.sort()
    pruned_depth_pct.sort()
    ceil_ghost_depth_pct.sort()
    fig3d_cot_depth_ecdf = {
        "hits_n": len(hits_depth_pct),
        "hits_median_pct": round(float(np.median(hits_depth_pct)), 2),
        "hits_sorted_pct": hits_depth_pct,
        "self_pruned_n": len(pruned_depth_pct),
        "self_pruned_median_pct": round(float(np.median(pruned_depth_pct)), 2),
        "self_pruned_sorted_pct": pruned_depth_pct,
        "ceiling_ghost_n": len(ceil_ghost_depth_pct),
        "ceiling_ghost_median_pct": round(float(np.median(ceil_ghost_depth_pct)), 2),
        "ceiling_ghost_sorted_pct": ceil_ghost_depth_pct,
    }

    # 6. Exact Pairwise Run Jaccard Dots (Fig 3B & Fig 5A) + Fig 2A Run/Domain Dots + Fig 4C Decile Attention
    s1_p = json.load(open(os.path.join(HERE, "step1_pubmed_results.json"), encoding="utf-8"))["parent_runs_dimension1"]["by_run"]
    s2_p = json.load(open(os.path.join(HERE, "step2_dim2_3_4_rectification_results.json"), encoding="utf-8"))["dimension_2_reasoning_vs_retrieval"]["per_run_top5_profiles"]
    cot_dyn = json.load(open(os.path.join(HERE, "cot_trajectory_dynamics_summary.json"), encoding="utf-8"))

    def jacc_sets(a, b):
        sa, sb = set(a), set(b)
        return round(len(sa & sb) / max(1, len(sa | sb)), 4)

    fig3b_5a_pairwise = {}
    for dis in ["dAMD", "ALS"]:
        b_runs = [f"{dis}_blind_R{r}" for r in [1, 2, 3]]
        r_runs = [f"{dis}_retrieval_R{r}" for r in [1, 2, 3]]
        w_pairs = [(b_runs[0], b_runs[1]), (b_runs[0], b_runs[2]), (b_runs[1], b_runs[2]),
                   (r_runs[0], r_runs[1]), (r_runs[0], r_runs[2]), (r_runs[1], r_runs[2])]
        c_pairs = [(br, rr) for br in b_runs for rr in r_runs]
        fig3b_5a_pairwise[dis] = {
            "within_lead_genes": [jacc_sets(s2_p[u]["lead_genes"], s2_p[v]["lead_genes"]) for u, v in w_pairs],
            "cross_lead_genes": [jacc_sets(s2_p[u]["lead_genes"], s2_p[v]["lead_genes"]) for u, v in c_pairs],
            "within_all_genes": [jacc_sets(s2_p[u]["all_genes"], s2_p[v]["all_genes"]) for u, v in w_pairs],
            "cross_all_genes": [jacc_sets(s2_p[u]["all_genes"], s2_p[v]["all_genes"]) for u, v in c_pairs],
            "within_axes": [jacc_sets(s2_p[u]["axes_hit"], s2_p[v]["axes_hit"]) for u, v in w_pairs],
            "cross_axes": [jacc_sets(s2_p[u]["axes_hit"], s2_p[v]["axes_hit"]) for u, v in c_pairs],
        }

    fig2a_dots = {
        "parent_12_tier1_valid_pct": [round(100.0 * (1.0 - s1_p[r]["fabrication_rate_all_slots"]), 2) for r in runs_12],
        "parent_12_tier2_verified_pct": [round(100.0 * (1.0 - s1_p[r]["ungrounded_rate_all_slots"]), 2) for r in runs_12],
        "expb_14_tier1_valid_pct": [],
        "expb_14_tier2_verified_pct": [],
    }
    for d_i in range(1, 15):
        did = f"B{d_i:02d}"
        sub_d = [r for r in expb_all if r["domain_id"] == did and r["arm"] == "as_discovered"]
        fig2a_dots["expb_14_tier1_valid_pct"].append(round(100.0 * sum(1 for r in sub_d if r["resolved"]) / len(sub_d), 2))
        fig2a_dots["expb_14_tier2_verified_pct"].append(round(100.0 * sum(1 for r in sub_d if r["resolved"] and r["on_topic"]) / len(sub_d), 2))

    fig4c_cot_attention = {
        "t1_n_traces": cot_dyn["tournament_cot_attention_profile"]["t1_n_traces"],
        "t1_deciles_pct": [round(100.0 * x, 2) for x in cot_dyn["tournament_cot_attention_profile"]["t1_decile_slot_a_attention_share"]],
        "t2_n_traces": cot_dyn["tournament_cot_attention_profile"]["t2_n_traces"],
        "t2_deciles_pct": [round(100.0 * x, 2) for x in cot_dyn["tournament_cot_attention_profile"]["t2_decile_slot_a_attention_share"]],
    }

    out = {
        "fig2a_dots": fig2a_dots,
        "fig3b_5a_pairwise": fig3b_5a_pairwise,
        "fig3c_exact": fig3c_exact,
        "fig3d_cot_depth_ecdf": fig3d_cot_depth_ecdf,
        "fig3d_decoys": fig3d_decoys,
        "fig4c_cot_attention": fig4c_cot_attention,
        "fig4c_exact": fig4c_exact,
        "fig5a_boot": fig5a_boot,
        "sf1c_exact": sf1c_exact,
        "sf2b_ecdf": sf2b_ecdf,
    }
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=2)
    print("Saved exact plot arrays ->", OUT_JSON)
    print("CoT Depth ECDF summary:", {k: v for k, v in fig3d_cot_depth_ecdf.items() if not k.endswith("_pct") or "median" in k})
    print("Pairwise dAMD & ALS:", {d: {k: round(float(np.mean(v)), 4) for k, v in vd.items()} for d, vd in fig3b_5a_pairwise.items()})


if __name__ == "__main__":
    main()
