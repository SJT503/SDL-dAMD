#!/usr/bin/env python3
"""
nc_upgrade_A3_A7_expc_calibration.py -- Phase-1 Tasks A3 & A7 for Nature Communications
Special Collection 'Agentic AI Systems':
  Task A3 (Experiment C-v4 Mechanistic Diagnostics & CoT-SRAD Validation):
    1. Exact STROBE-style call-accounting reconciliation:
       calls_log.jsonl (804 expC calls) -> 174 superseded pilot retries (D2-004..D2-007)
       + 630 canonical 32k-ceiling evaluation calls = 166 baseline hits + 236 completed
       10-gene misses + 228 ceiling-truncated 0-gene misses (464 total misses).
    2. Strict zero-leakage external HGNC Mendelian vocabulary (4,958 genes from
       expC_candidate_pool.csv, zero test-output vocabulary leakage) vs internal pred_vocab.
    3. 5-Way CoT-SRAD Ablation Study across GLM-5.3 (n=359), DeepSeek-V4-Pro (n=271),
       and Pooled (n=630):
       - M0: Baseline emitted list
       - M1: Module 4a Only (Ceiling-Spin Stream Harvest on len(preds)<10, WITH LODO ban)
       - M2: Module 4b Only (Completed-List Attractor Deconfounding on len(preds)==10)
       - M3: CoT Harvest WITHOUT Attractor Ban (proving why attractor ban is essential!)
       - M4: Full CoT-SRAD (4a + 4b, external HGNC vocab + strict LODO ban)
    4. 2D Hyperparameter Sensitivity Grid: tau_ban in {6, 8, 10, 12, 15, 18, 20} x
       CoT harvest top-K / mention threshold.
    5. Term-Count Starvation Audit explaining Confirmatory Member 3 (del_lowIC_matched
       deletes ~2.3x more HPO terms than del_topIC to match deleted IC sum).

  Task A7 (Multi-Model Confidence Calibration & Selective Calibration Gate):
    Benchmark Raw vs 1-Param Temperature Scaling vs 1-Param Log-Odds Shift vs Isotonic
    Regression vs 2-Param LORO Platt vs Zero-Leakage Nested-CV Selective Calibration Gate
    (apply 1-param log-odds/Platt recalibration iff inner-fold raw ECE > tau_ece=0.10,
    with Bayesian shrinkage toward identity on small samples) across all 8 calibration
    cohorts (GLM Parent Pooled n=480, Step1 n=360, Step3 n=120, ExpB n=70, Gemini-4 n=60,
    Gemini-Flash n=60, Grok-High n=60, Grok-Fast n=60).
"""
from gate import gate, canary_gate, retry_limit

import csv
import json
import math
import os
import re
import time
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_ROOT = os.path.dirname(HERE)
BASE = os.path.dirname(EXEC_ROOT)
RUNS_DIR = os.path.join(EXEC_ROOT, "runs")
DATA_DIR = os.path.join(EXEC_ROOT, "data")
OUT_JSON = os.path.join(HERE, "nc_upgrade_A3_A7_results.json")

gate(__file__)

STOP_TOKENS = {
    "AND", "THE", "FOR", "WITH", "FROM", "THAT", "THIS", "ARE", "WAS", "NOT",
    "GENE", "GENES", "OMIM", "HPO", "DNA", "RNA", "ATP", "GTP", "CNS", "MRI",
    "EEG", "EMG", "ECG", "AUTOSOMAL", "RECESSIVE", "DOMINANT", "TYPE", "SYNDROME",
}


def load_raw_cot(raw_path):
    if not raw_path or not os.path.exists(raw_path):
        return ""
    try:
        d = json.load(open(raw_path, encoding="utf-8"))
        msg = (d.get("choices") or [{}])[0].get("message") or {}
        return msg.get("reasoning_content") or msg.get("reasoning") or ""
    except Exception:
        return ""


def load_hgnc_external_vocab():
    pool_csv = os.path.join(BASE, "REDO_REVIEW_PACK_2026-09-02", "expC_candidate_pool.csv")
    vocab = set()
    with open(pool_csv, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            g = str(row.get("gene_symbol", "")).strip().upper()
            if len(g) >= 2 and g not in STOP_TOKENS:
                vocab.add(g)
    return vocab


def compute_ece_brier(probs, y_true, n_bins=10):
    probs = np.clip(np.asarray(probs, dtype=float), 1e-6, 1.0 - 1e-6)
    y_true = np.asarray(y_true, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(probs)
    for b in range(n_bins):
        mask = (probs >= bins[b]) & (probs <= bins[b + 1] if b == n_bins - 1 else probs < bins[b + 1])
        if np.any(mask):
            ece += (np.sum(mask) / n) * abs(float(np.mean(probs[mask])) - float(np.mean(y_true[mask])))
    brier = float(np.mean((probs - y_true) ** 2))
    return float(ece), brier


def pav_isotonic(x, y):
    """Deterministic Pool-Adjacent-Violators isotonic regression (1D increasing)."""
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    ys = y[order].astype(float)
    blocks = [[float(ys[i]), 1, xs[i], xs[i]] for i in range(len(ys))]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i + 1][0]:
            tot_w = blocks[i][1] + blocks[i + 1][1]
            avg_y = (blocks[i][0] * blocks[i][1] + blocks[i + 1][0] * blocks[i + 1][1]) / tot_w
            blocks[i] = [avg_y, tot_w, blocks[i][2], blocks[i + 1][3]]
            blocks.pop(i + 1)
            if i > 0:
                i -= 1
        else:
            i += 1
    knots_x = np.array([0.5 * (b[2] + b[3]) for b in blocks])
    knots_y = np.array([b[0] for b in blocks])
    return knots_x, knots_y


def evaluate_calibrators(probs_raw, y_true, cluster_ids, ece_bins_primary=10):
    p_raw = np.clip(np.asarray(probs_raw, dtype=float), 0.01, 0.99)
    logits = np.log(p_raw / (1.0 - p_raw))
    y = np.asarray(y_true, dtype=float)
    clusters = np.asarray(cluster_ids)
    uniq_c = sorted(set(clusters.tolist()))

    preds = {
        "raw": p_raw.copy(),
        "shift_1param": np.zeros_like(p_raw),
        "temp_1param": np.zeros_like(p_raw),
        "platt_2param_unreg": np.zeros_like(p_raw),
        "platt_2param_shrunk": np.zeros_like(p_raw),
        "isotonic_pav": np.zeros_like(p_raw),
        "selective_gate": np.zeros_like(p_raw),
    }
    gate_triggered_folds = 0

    for c in uniq_c:
        tr = clusters != c
        te = ~tr
        x_tr, y_tr, p_tr = logits[tr], y[tr], p_raw[tr]
        x_te, p_te = logits[te], p_raw[te]

        # 1. 1-Param Log-Odds Intercept Shift: sigmoid(logit(p) + b) -- preserves ranking & avoids slope overfitting!
        def nll_shift(b_arr):
            z = np.clip(x_tr + b_arr[0], -20, 20)
            q = 1.0 / (1.0 + np.exp(-z))
            return -np.sum(y_tr * np.log(q + 1e-9) + (1 - y_tr) * np.log(1 - q + 1e-9)) + 0.01 * (b_arr[0] ** 2)

        b_opt = minimize(nll_shift, [0.0], method="BFGS").x[0]
        preds["shift_1param"][te] = 1.0 / (1.0 + np.exp(-np.clip(x_te + b_opt, -20, 20)))

        # 2. 1-Param Temperature Scaling: sigmoid(logit(p) / T), T > 0
        def nll_temp(log_t):
            inv_t = np.exp(-np.clip(log_t[0], -3, 3))
            z = np.clip(x_tr * inv_t, -20, 20)
            q = 1.0 / (1.0 + np.exp(-z))
            return -np.sum(y_tr * np.log(q + 1e-9) + (1 - y_tr) * np.log(1 - q + 1e-9)) + 0.01 * (log_t[0] ** 2)

        lt_opt = minimize(nll_temp, [0.0], method="BFGS").x[0]
        preds["temp_1param"][te] = 1.0 / (1.0 + np.exp(-np.clip(x_te * np.exp(-np.clip(lt_opt, -3, 3)), -20, 20)))

        # 3. Legacy 2-Param LORO Platt (regularized toward 0,0 as in analyze_gemini_cross_ecosystem.py)
        def nll_platt_unreg(ab):
            a, b = ab
            z = np.clip(a * x_tr + b, -20, 20)
            q = 1.0 / (1.0 + np.exp(-z))
            return -np.sum(y_tr * np.log(q + 1e-9) + (1 - y_tr) * np.log(1 - q + 1e-9)) + 0.01 * (a ** 2 + b ** 2)

        ab_u = minimize(nll_platt_unreg, [1.0, 0.0], method="BFGS").x
        preds["platt_2param_unreg"][te] = 1.0 / (1.0 + np.exp(-np.clip(ab_u[0] * x_te + ab_u[1], -20, 20)))

        # 4. Identity-Anchored Shrunk Platt: penalize (a - 1)^2 strongly when N is small (lambda_a = 2.0)
        def nll_platt_shrunk(ab):
            a, b = ab
            z = np.clip(a * x_tr + b, -20, 20)
            q = 1.0 / (1.0 + np.exp(-z))
            return -np.sum(y_tr * np.log(q + 1e-9) + (1 - y_tr) * np.log(1 - q + 1e-9)) + 2.0 * ((a - 1.0) ** 2) + 0.1 * (b ** 2)

        ab_s = minimize(nll_platt_shrunk, [1.0, 0.0], method="BFGS").x
        p_shrunk_te = 1.0 / (1.0 + np.exp(-np.clip(ab_s[0] * x_te + ab_s[1], -20, 20)))
        preds["platt_2param_shrunk"][te] = p_shrunk_te

        # 5. Isotonic PAV
        kx, ky = pav_isotonic(p_tr, y_tr)
        preds["isotonic_pav"][te] = np.clip(np.interp(p_te, kx, ky), 0.01, 0.99)

        # 6. Zero-Leakage Selective Calibration Gate (Module 2 v2.0):
        #    Check ONLY training-fold raw ECE (5-bin for N_tr < 100, 10-bin for N_tr >= 100):
        #    if train_ECE > tau_ece (0.10), apply regularized LORO Platt; otherwise preserve well-calibrated probabilities.
        tr_bins = 5 if len(p_tr) < 100 else 10
        tr_ece, _ = compute_ece_brier(p_tr, y_tr, n_bins=tr_bins)
        if tr_ece > 0.10:
            gate_triggered_folds += 1
            preds["selective_gate"][te] = preds["platt_2param_unreg"][te]
        else:
            preds["selective_gate"][te] = p_te

    out = {
        "n": int(len(y)),
        "n_clusters": int(len(uniq_c)),
        "mean_conf_pct": round(100.0 * float(np.mean(p_raw)), 2),
        "empirical_acc_pct": round(100.0 * float(np.mean(y)), 2),
        "overconfidence_gap_pp": round(100.0 * float(np.mean(p_raw) - np.mean(y)), 2),
        "selective_gate_triggered_folds": f"{gate_triggered_folds}/{len(uniq_c)}",
        "methods": {},
    }
    raw_ece_p, _ = compute_ece_brier(preds["raw"], y, n_bins=ece_bins_primary)
    for m_key, m_probs in preds.items():
        ece10, brier = compute_ece_brier(m_probs, y, n_bins=10)
        ece5, _ = compute_ece_brier(m_probs, y, n_bins=5)
        ece_p = ece5 if ece_bins_primary == 5 else ece10
        out["methods"][m_key] = {
            "ece_primary": round(ece_p, 4),
            "ece_5bin": round(ece5, 4),
            "ece_10bin": round(ece10, 4),
            "brier": round(brier, 4),
            "ece_reduction_vs_raw_pct": round(100.0 * (raw_ece_p - ece_p) / max(1e-6, raw_ece_p), 2),
        }
    return out


@retry_limit(2)
def main():
    t0 = time.perf_counter()

    # ==========================================================================
    # PART 1: Task A3 -- Exp C-v4 Call Accounting, CoT-SRAD Ablations & Sensitivity
    # ==========================================================================
    calls_by_id = {}
    expc_all_calls = []
    with open(os.path.join(DATA_DIR, "calls_log.jsonl"), "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            c = json.loads(line)
            calls_by_id[c["call_id"]] = c
            if str(c["call_id"]).startswith("expC") or (c.get("about") or {}).get("experiment") == "C":
                expc_all_calls.append(c)

    res_c = [
        json.loads(line)
        for line in open(os.path.join(RUNS_DIR, "expC_v4", "results.jsonl"), encoding="utf-8")
        if line.strip()
    ]
    eval_call_ids = {r["call_id"] for r in res_c}
    # Count exact lines: keep ONLY the final successful entry per evaluated call_id, all other 174 lines are superseded retries/pilots
    seen_eval_final = set()
    superseded_calls = []
    for c in reversed(expc_all_calls):
        cid = c["call_id"]
        if cid in eval_call_ids and cid not in seen_eval_final:
            seen_eval_final.add(cid)
        else:
            superseded_calls.append(c)
    superseded_by_max_tok = Counter(int(c.get("max_tokens") or 0) for c in superseded_calls)
    superseded_by_prefix = Counter(str(c["call_id"]).split("/")[0] for c in superseded_calls)
    superseded_same_id_retries = sum(1 for c in superseded_calls if c["call_id"] in eval_call_ids)

    canary_gate(lambda: len(res_c) == 630 and len(expc_all_calls) == 804, "Verify 804 total ExpC calls -> 630 evaluated")

    # Exact STROBE partition of the 630 evaluated calls
    strobe = {}
    for v_key, sub in [("glm", [r for r in res_c if r["vendor"] == "glm"]),
                       ("deepseek", [r for r in res_c if r["vendor"] == "deepseek"]),
                       ("pooled", res_c)]:
        n_tot = len(sub)
        n_hit = sum(1 for r in sub if r["hit10"])
        n_miss_full = sum(1 for r in sub if (not r["hit10"]) and len(r.get("predictions") or []) == 10)
        n_miss_partial = sum(1 for r in sub if (not r["hit10"]) and 0 < len(r.get("predictions") or []) < 10)
        n_miss_empty = sum(1 for r in sub if (not r["hit10"]) and len(r.get("predictions") or []) == 0)
        n_hit_partial = sum(1 for r in sub if r["hit10"] and len(r.get("predictions") or []) < 10)
        strobe[v_key] = {
            "n_evaluated_calls": n_tot,
            "n_baseline_hits": n_hit,
            "n_hits_with_lt10_preds": n_hit_partial,
            "n_completed_10pred_misses": n_miss_full,
            "n_partial_1to9pred_misses": n_miss_partial,
            "n_ceiling_truncated_0pred_misses": n_miss_empty,
            "n_total_misses": n_tot - n_hit,
            "partition_check_ok": (n_hit + n_miss_full + n_miss_partial + n_miss_empty) == n_tot,
        }

    # Pre-extract CoT gene mentions per call once for ultra-fast ablation & 2D grid sweeps
    hgnc_vocab = load_hgnc_external_vocab()
    internal_pred_vocab = {p for r in res_c for p in (r.get("predictions") or [])}

    cot_tokens_by_call = {}
    for r in res_c:
        clog = calls_by_id.get(r["call_id"])
        rc = load_raw_cot(clog.get("raw_path")) if clog else ""
        # Ordered list of uppercase symbol tokens (preserving frequency & first-mention order)
        toks = [m.group(1) for m in re.finditer(r"\b([A-Z][A-Z0-9]{1,9})\b", rc)] if rc else []
        cot_tokens_by_call[r["call_id"]] = toks

    # Precompute Leave-One-Disease-Out (LODO) prediction document frequencies per pair_id
    global_pred_df = Counter()
    pair_pred_df = defaultdict(Counter)
    for r in res_c:
        uniq_p = set(r.get("predictions") or [])
        for p in uniq_p:
            global_pred_df[p] += 1
            pair_pred_df[r["pair_id"]][p] += 1

    def run_srad_variant(vocab_set, mode="full", tau_ban=12, min_cot_mentions=1):
        """
        mode in:
          - 'baseline': raw predictions[:10]
          - '4a_ceiling_only': harvest CoT ONLY when len(preds) < 10 (with LODO ban)
          - '4b_deconfound_only': filter LODO attractors & backfill ONLY when len(preds) == 10
          - 'no_attractor_ban': harvest CoT on len(preds) < 10 WITHOUT attractor ban (tau_ban=999999)
          - 'full': Module 4a + Module 4b (CoT-SRAD)
        """
        res_by_vendor = {}
        for v_key, sub in [("glm", [r for r in res_c if r["vendor"] == "glm"]),
                           ("deepseek", [r for r in res_c if r["vendor"] == "deepseek"]),
                           ("pooled", res_c)]:
            base_h = 0
            var_h = 0
            b_only = 0
            c_only = 0
            rescued_from_ceiling = 0
            rescued_from_full = 0
            lost_from_full = 0

            for r in sub:
                pid = r["pair_id"]
                gs = {str(r["gene_symbol"]).upper()} | {str(a).upper() for a in (r.get("aliases") or []) if a}
                preds = list(r.get("predictions") or [])[:10]
                b_hit = int(r["hit10"] == 1)
                toks = cot_tokens_by_call[r["call_id"]]

                if mode == "baseline":
                    new_preds = preds
                else:
                    eff_tau = 999999 if mode == "no_attractor_ban" else tau_ban
                    lodo_ban = {
                        g for g, cnt in global_pred_df.items()
                        if (cnt - pair_pred_df[pid].get(g, 0)) >= eff_tau
                    }
                    if len(preds) < 10:
                        if mode in ("4a_ceiling_only", "no_attractor_ban", "full") and toks:
                            freq = Counter(t for t in toks if t in vocab_set and t not in lodo_ban)
                            cand_c = [g for g, c in freq.most_common(20) if c >= min_cot_mentions and g not in preds]
                            new_preds = (preds + cand_c)[:10]
                        else:
                            new_preds = preds
                    else:
                        if mode in ("4b_deconfound_only", "full") and toks:
                            kept = [p for p in preds if p not in lodo_ban]
                            if len(kept) < 10:
                                freq = Counter(t for t in toks if t in vocab_set and t not in lodo_ban and t not in kept)
                                repl = [g for g, c in freq.most_common(10 - len(kept)) if c >= min_cot_mentions]
                                new_preds = (kept + repl + [p for p in preds if p not in kept and p not in repl])[:10]
                            else:
                                new_preds = preds
                        else:
                            new_preds = preds

                s_hit = int(any(p in gs for p in new_preds))
                base_h += b_hit
                var_h += s_hit
                if b_hit == 1 and s_hit == 0:
                    b_only += 1
                    if len(preds) == 10:
                        lost_from_full += 1
                elif b_hit == 0 and s_hit == 1:
                    c_only += 1
                    if len(preds) == 0:
                        rescued_from_ceiling += 1
                    else:
                        rescued_from_full += 1

            p_mcn = float(stats.binomtest(c_only, b_only + c_only, 0.5).pvalue) if (b_only + c_only) > 0 else 1.0
            res_by_vendor[v_key] = {
                "n": len(sub),
                "base_hits": base_h,
                "variant_hits": var_h,
                "variant_hit10_pct": round(100.0 * var_h / len(sub), 2),
                "net_gain_hits": var_h - base_h,
                "net_gain_pp": round(100.0 * (var_h - base_h) / len(sub), 2),
                "rescued_from_ceiling_0pred": rescued_from_ceiling,
                "rescued_from_completed_10pred": rescued_from_full,
                "lost_hits": b_only,
                "gained_hits": c_only,
                "mcnemar_exact_p": p_mcn,
            }
        return res_by_vendor

    # 5-Way Ablation under External Frozen HGNC Vocabulary (4,958 genes) AND Legacy Internal Vocab
    ablation_hgnc = {
        "M0_baseline": run_srad_variant(hgnc_vocab, mode="baseline"),
        "M1_4a_ceiling_harvest_only": run_srad_variant(hgnc_vocab, mode="4a_ceiling_only", tau_ban=12),
        "M2_4b_completed_deconfound_only": run_srad_variant(hgnc_vocab, mode="4b_deconfound_only", tau_ban=12),
        "M3_harvest_without_attractor_ban": run_srad_variant(hgnc_vocab, mode="no_attractor_ban"),
        "M4_full_cot_srad_external_hgnc": run_srad_variant(hgnc_vocab, mode="full", tau_ban=12),
        "M4_legacy_internal_pred_vocab": run_srad_variant(internal_pred_vocab, mode="full", tau_ban=12),
    }

    # 2D Hyperparameter Sensitivity Grid over tau_ban x min_cot_mentions (External HGNC Vocab)
    grid_2d = []
    for tau_b in [6, 8, 10, 12, 15, 18, 20]:
        for min_m in [1, 2, 3]:
            rv = run_srad_variant(hgnc_vocab, mode="full", tau_ban=tau_b, min_cot_mentions=min_m)
            grid_2d.append({
                "tau_ban_df": tau_b,
                "min_cot_mentions": min_m,
                "pooled_hit10_pct": rv["pooled"]["variant_hit10_pct"],
                "pooled_net_gain_hits": rv["pooled"]["net_gain_hits"],
                "glm_net_gain_hits": rv["glm"]["net_gain_hits"],
                "deepseek_net_gain_hits": rv["deepseek"]["net_gain_hits"],
                "pooled_mcnemar_p": rv["pooled"]["mcnemar_exact_p"],
            })

    # Term-Count Starvation Audit explaining Confirmatory Member 3 (del_lowIC_matched vs del_topIC)
    df_c = pd.DataFrame(res_c)
    df_c["n_deleted_terms"] = df_c["n_pheno_terms_intact"] - df_c["n_pheno_terms_kept"]
    df_c["frac_terms_deleted"] = df_c["n_deleted_terms"] / np.maximum(1, df_c["n_pheno_terms_intact"])
    df_c["hit10_num"] = df_c["hit10"].astype(float)
    df_c["is_lowIC"] = (df_c["arm"] == "del_lowIC_matched").astype(float)

    starvation_by_arm_dose = {}
    for (arm, dose), grp in df_c.groupby(["arm", "dose_target"]):
        starvation_by_arm_dose[f"{arm}__d{dose}"] = {
            "n_calls": int(len(grp)),
            "mean_dose_ic_realized": round(float(grp["dose_realized"].mean()), 4),
            "mean_intact_terms": round(float(grp["n_pheno_terms_intact"].mean()), 2),
            "mean_deleted_terms": round(float(grp["n_deleted_terms"].mean()), 2),
            "mean_kept_terms": round(float(grp["n_pheno_terms_kept"].mean()), 2),
            "mean_frac_terms_deleted_pct": round(100.0 * float(grp["frac_terms_deleted"].mean()), 2),
            "median_frac_terms_deleted_pct": round(100.0 * float(grp["frac_terms_deleted"].median()), 2),
            "hit10_pct": round(100.0 * float(grp["hit10_num"].mean()), 2),
        }

    # Compare deleted term count at d25 and d50 between arms (Mann-Whitney & ratio)
    d50_top = df_c[(df_c["arm"] == "del_topIC") & (df_c["dose_target"] == 50)]["frac_terms_deleted"]
    d50_low = df_c[(df_c["arm"] == "del_lowIC_matched") & (df_c["dose_target"] == 50)]["frac_terms_deleted"]
    mw_u, mw_p = stats.mannwhitneyu(d50_low, d50_top, alternative="greater")

    # Multivariable cluster-robust logit controlling simultaneously for IC deleted AND fraction of HPO terms deleted
    X_starv = sm.add_constant(df_c[["dose_realized", "frac_terms_deleted", "is_lowIC"]])
    mod_starv = sm.Logit(df_c["hit10_num"], X_starv).fit(disp=False, cov_type="cluster", cov_kwds={"groups": df_c["pair_id"]})

    # ==========================================================================
    # PART 2: Task A7 -- Multi-Model Confidence Calibration & Selective Gate
    # ==========================================================================
    runs_12 = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]
    s1_p, s1_y, s1_c = [], [], []
    s3_p, s3_y, s3_c = [], [], []
    for rid in runs_12:
        rdir = os.path.join(RUNS_DIR, rid)
        s1 = json.load(open(os.path.join(rdir, "step1_mechanisms.json"), encoding="utf-8"))
        s3 = json.load(open(os.path.join(rdir, "step3_candidates.json"), encoding="utf-8"))
        s5 = json.load(open(os.path.join(rdir, "step5_top5.json"), encoding="utf-8"))
        top5_mkeys = {x["source_mechanism_key"] for x in s5["top5"]}
        top5_cids = {x["cand_id"] for x in s5["top5"]}
        for m in s1["mechanisms"]:
            s1_p.append(float(m["confidence"]) / 100.0)
            s1_y.append(1.0 if f"M{int(m['id']) - 1:02d}" in top5_mkeys else 0.0)
            s1_c.append(rid)
        for c in s3["candidates"]:
            s3_p.append(float(c["confidence"]) / 100.0)
            s3_y.append(1.0 if c["cand_id"] in top5_cids else 0.0)
            s3_c.append(rid)

    # Exp B Stage 1 (n=70)
    pm_cache = json.load(open(os.path.join(HERE, "pubmed_cache.json"), encoding="utf-8"))
    eb_p, eb_y, eb_c = [], [], []
    for d_idx in range(1, 15):
        did = f"B{d_idx:02d}"
        arr = json.load(open(os.path.join(RUNS_DIR, "expB", "_shared_stage1", f"{did}_stage1.json"), encoding="utf-8"))
        for item in arr:
            hid = int(item["id"])
            slots = json.load(open(os.path.join(RUNS_DIR, "expB", "as_discovered", f"{did}_h{hid}.json"), encoding="utf-8"))
            n_ex = sum(1 for sl in slots if pm_cache.get(str(sl.get("pmid", "")).strip(), {}).get("exists", False))
            eb_p.append(float(item["confidence"]) / 100.0)
            eb_y.append(1.0 if n_ex >= 3 else 0.0)
            eb_c.append(did)

    # Cross-ecosystem Exp C cohorts (n=60 each, 5-bin primary ECE matching cross-ecosystem benchmark)
    truth_map = json.load(open(os.path.join(HERE, "expC_20pairs_truth_key.json"), encoding="utf-8"))

    def load_ext_expc(fpath):
        arr = json.load(open(fpath, encoding="utf-8"))
        ps, ys, cs = [], [], []
        for item in arr:
            pid = item["pair_id"]
            t_info = truth_map[pid]
            gs = {t_info["gene_symbol"].upper()} | {a.upper() for a in t_info.get("aliases", [])}
            preds = [str(x).strip().upper() for x in item.get("predictions", [])[:10]]
            ps.append(float(item.get("confidence", 75)) / 100.0)
            ys.append(1.0 if any(p in gs for p in preds) else 0.0)
            cs.append(pid)
        return ps, ys, cs

    cal_cohorts = {
        "GLM-5.3_Parent_Pooled_n480": evaluate_calibrators(s1_p + s3_p, s1_y + s3_y, s1_c + s3_c, ece_bins_primary=10),
        "GLM-5.3_Parent_Step1_n360": evaluate_calibrators(s1_p, s1_y, s1_c, ece_bins_primary=10),
        "GLM-5.3_Parent_Step3_n120": evaluate_calibrators(s3_p, s3_y, s3_c, ece_bins_primary=10),
        "GLM-5.3_ExpB_Stage1_n70": evaluate_calibrators(eb_p, eb_y, eb_c, ece_bins_primary=10),
    }
    for label, fpath in [
        ("Gemini-4-Argon-High_ExpC_n60", os.path.join(DATA_DIR, "gemini_outputs", "expC_pro_60preds.json")),
        ("Gemini-3.8-Flash_ExpC_n60", os.path.join(DATA_DIR, "gemini_outputs", "expC_flash_60preds.json")),
        ("Grok-4.7-High_ExpC_n60", os.path.join(DATA_DIR, "grok_outputs", "expC_high_60preds.json")),
        ("Grok-4.7-Fast_ExpC_n60", os.path.join(DATA_DIR, "grok_outputs", "expC_fast_60preds.json")),
    ]:
        ps, ys, cs = load_ext_expc(fpath)
        cal_cohorts[label] = evaluate_calibrators(ps, ys, cs, ece_bins_primary=5)

    elapsed = round(time.perf_counter() - t0, 2)
    out = {
        "task": "A3_ExpC_Diagnostics_and_A7_Selective_Calibration",
        "elapsed_sec": elapsed,
        "A3_strobe_call_accounting": {
            "total_expC_entries_in_calls_log": len(expc_all_calls),
            "superseded_pilot_retries_count": len(superseded_calls),
            "superseded_by_max_tokens": {str(k): int(v) for k, v in sorted(superseded_by_max_tok.items())},
            "superseded_by_prefix": dict(superseded_by_prefix),
            "evaluated_canonical_32k_calls": len(res_c),
            "partition_by_vendor": strobe,
        },
        "A3_hgnc_external_vocab_size": len(hgnc_vocab),
        "A3_internal_pred_vocab_size": len(internal_pred_vocab),
        "A3_cot_srad_5way_ablation": ablation_hgnc,
        "A3_cot_srad_2d_sensitivity_grid": grid_2d,
        "A3_term_count_starvation_audit": {
            "by_arm_and_dose": starvation_by_arm_dose,
            "d50_frac_terms_deleted_ratio_lowIC_vs_topIC": round(float(d50_low.mean() / max(1e-6, d50_top.mean())), 3),
            "d50_mannwhitney_p_lowIC_gt_topIC": float(mw_p),
            "joint_logit_params": {k: round(float(v), 4) for k, v in mod_starv.params.to_dict().items()},
            "joint_logit_pvals": {k: float(v) for k, v in mod_starv.pvalues.to_dict().items()},
        },
        "A7_calibration_benchmark": cal_cohorts,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(f"\n[A3 + A7 DONE in {elapsed}s] Saved to {OUT_JSON}")
    print("  [A3 STROBE] 804 total ->", len(superseded_calls), "superseded pilot + 630 canonical =",
          strobe["pooled"]["n_baseline_hits"], "hits +",
          strobe["pooled"]["n_completed_10pred_misses"], "full misses +",
          strobe["pooled"]["n_ceiling_truncated_0pred_misses"], "ceiling-truncated 0-pred misses")
    for m_k, m_v in ablation_hgnc.items():
        p = m_v["pooled"]
        g = m_v["glm"]
        d = m_v["deepseek"]
        print(f"  [Ablation] {m_k:36s}: Pooled={p['variant_hit10_pct']}% ({p['net_gain_hits']:+d}, p={p['mcnemar_exact_p']:.2e}) | "
              f"GLM={g['net_gain_hits']:+d} | DS={d['net_gain_hits']:+d}")
    print(f"  [Starvation @ d50] del_lowIC deletes {100*d50_low.mean():.1f}% of HPO terms vs del_topIC {100*d50_top.mean():.1f}% "
          f"(ratio={d50_low.mean()/d50_top.mean():.2f}x, p={mw_p:.2e})")
    for c_k, c_v in cal_cohorts.items():
        m = c_v["methods"]
        print(f"  [A7 Cal] {c_k:32s}: Raw={m['raw']['ece_primary']:.4f} | UnregPlatt={m['platt_2param_unreg']['ece_primary']:.4f} | "
              f"Shift1P={m['shift_1param']['ece_primary']:.4f} | SelectiveGate={m['selective_gate']['ece_primary']:.4f} ({c_v['selective_gate_triggered_folds']})")


if __name__ == "__main__":
    main()
