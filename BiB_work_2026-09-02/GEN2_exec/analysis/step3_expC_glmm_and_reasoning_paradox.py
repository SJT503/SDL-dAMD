#!/usr/bin/env python3
"""
Step 3:
  1. Experiment C-v4 Mechanistic Perturbation Analysis (120/123 Mendelian pairs,
     630 calls across GLM-5.3 and DeepSeek-V4-Pro):
     - Confirmatory Member 2 (dose slope beta_1 in del_topIC)
     - Confirmatory Member 3 (arm x dose interaction beta_3)
     - Literature footprint memorization model (dose x log10(footprint+1))
     - Decoy / canonical-gene attractor concentration analysis
  2. Dimension 6 Self-Knowledge (Confidence Calibration & LORO Platt Recalibration):
     - Confirmatory Member 6 (H0: calibration slope = 1)
     - Parent Step 1 (n=360), Parent Step 3 (n=120), Exp B Stage 1 (n=70)
     - Leave-One-Run-Out (LORO) Platt scaling remediation (Before vs After ECE & Brier)
  3. The Test-Time Reasoning Paradox (joining 8,972 live calls / 35.58M reasoning tokens):
     - Reasoning token expenditure across all experimental blocks
     - Tournament II: reasoning tokens in concordant vs position-biased (primacy-flipped) verdicts
     - Experiment B: reasoning tokens across citation arms and correlation with fabrication
     - Experiment C-v4: reasoning tokens by deletion dose (0%, 25%, 50%) and hit10 outcome
"""

import json
import math
import os
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
PREREG_DIR = os.path.join(BASE, "GEN2_prereg")
EXEC_DIR = os.path.join(BASE, "GEN2_exec")
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
DATA_DIR = os.path.join(EXEC_DIR, "data")
OUT_DIR = os.path.join(EXEC_DIR, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)


def analyze_expC():
    print("=== 1. Experiment C-v4 Perturbation Analysis ===")
    pairs_df = pd.read_csv(os.path.join(PREREG_DIR, "expC_v4_pairs_120_f14.csv"))
    pair_meta = {}
    for _, row in pairs_df.iterrows():
        pair_meta[row["pair_id"]] = {
            "omim_id": row["omim_id"],
            "disease_name": row["disease_name"],
            "gene_symbol": str(row["gene_symbol"]).strip().upper(),
            "footprint": float(row["footprint"]),
            "log10_footprint": math.log10(float(row["footprint"]) + 1.0),
            "n_hpo_terms": int(row["n_hpo_terms"]),
            "organ_system": str(row["primary_organ_system_label"]),
            "window": str(row["window"]),
            "cell": str(row["cell"]),
        }

    rows = []
    results_path = os.path.join(RUNS_DIR, "expC_v4", "results.jsonl")
    with open(results_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if not r.get("ok", False):
                continue
            pid = r["pair_id"]
            meta = pair_meta.get(pid, {})
            target = str(r["gene_symbol"]).strip().upper()
            aliases = set(str(a).strip().upper() for a in r.get("aliases", []) if a)
            valid_targets = {target} | aliases
            preds = [str(p).strip().upper() for p in r.get("predictions", []) if p]

            hit1 = 1 if (len(preds) >= 1 and preds[0] in valid_targets) else 0
            hit10 = 1 if r.get("hit10", False) else 0
            mrr = 0.0
            rank_pos = None
            for idx, p in enumerate(preds[:10]):
                if p in valid_targets:
                    mrr = 1.0 / (idx + 1)
                    rank_pos = idx + 1
                    break

            rows.append({
                "call_id": r["call_id"],
                "vendor": r["vendor"],
                "arm": r["arm"],
                "dose_target": int(r["dose_target"]),
                "dose_realized": float(r["dose_realized"]),
                "pair_id": pid,
                "gene_symbol": target,
                "rep": int(r["rep"]),
                "hit1": hit1,
                "hit10": hit10,
                "mrr": mrr,
                "rank_pos": rank_pos,
                "top1_pred": preds[0] if preds else "NONE",
                "preds": preds[:10],
                "n_pheno_intact": int(r.get("n_pheno_terms_intact", 0)),
                "n_pheno_kept": int(r.get("n_pheno_terms_kept", 0)),
                "footprint": meta.get("footprint", 0.0),
                "log10_footprint": meta.get("log10_footprint", 0.0),
                "organ_system": meta.get("organ_system", ""),
                "window": meta.get("window", ""),
                "cell": meta.get("cell", ""),
            })

    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} valid Experiment C-v4 rows across {df['pair_id'].nunique()} unique pairs.")

    # Descriptive table by vendor, arm, dose_target
    desc = {}
    for (vendor, arm, dose), g in df.groupby(["vendor", "arm", "dose_target"]):
        key = f"{vendor}__{arm}__d{dose}"
        desc[key] = {
            "n_calls": int(len(g)),
            "n_unique_pairs": int(g["pair_id"].nunique()),
            "median_dose_realized": float(g["dose_realized"].median()),
            "mean_dose_realized": float(g["dose_realized"].mean()),
            "hit10_rate": float(g["hit10"].mean()),
            "hit10_count": int(g["hit10"].sum()),
            "hit1_rate": float(g["hit1"].mean()),
            "mrr_mean": float(g["mrr"].mean()),
        }
        print(f"  {key:35s}: n={len(g):3d} (pairs={g['pair_id'].nunique():3d}), "
              f"med_dose={g['dose_realized'].median():.3f}, "
              f"hit@10={g['hit10'].mean()*100:.1f}%, hit@1={g['hit1'].mean()*100:.1f}%, MRR={g['mrr'].mean():.3f}")

    # Regression & Pair-Cluster Bootstrap (10,000 iterations, seed=20260101)
    # Model: hit10 ~ dose_realized + is_lowIC + dose_realized:is_lowIC
    df["is_lowIC"] = (df["arm"] == "del_lowIC_matched").astype(float)
    df["dose_x_lowIC"] = df["dose_realized"] * df["is_lowIC"]

    models_out = {}
    for subset_name, sub_df in [("glm", df[df["vendor"] == "glm"].copy()),
                                ("deepseek", df[df["vendor"] == "deepseek"].copy()),
                                ("pooled", df.copy())]:
        # Logistic regression with cluster-robust SE by pair_id
        X = sm.add_constant(sub_df[["dose_realized", "is_lowIC", "dose_x_lowIC"]])
        y = sub_df["hit10"]
        try:
            logit_mod = sm.Logit(y, X).fit(disp=False, cov_type="cluster", cov_kwds={"groups": sub_df["pair_id"]})
            params = logit_mod.params.to_dict()
            bse = logit_mod.bse.to_dict()
            pvals_two_sided = logit_mod.pvalues.to_dict()
            zvals = logit_mod.tvalues.to_dict()
            # One-sided p-values per prereg: H1: beta_1 (dose_realized) < 0; H1: beta_3 (dose_x_lowIC) > 0
            p_beta1_onesided = float(stats.norm.cdf(zvals["dose_realized"]))
            p_beta3_onesided = float(1.0 - stats.norm.cdf(zvals["dose_x_lowIC"]))
        except Exception as e:
            params, bse, pvals_two_sided, zvals = {}, {}, {}, {}
            p_beta1_onesided, p_beta3_onesided = 1.0, 1.0
            print(f"Logit failed for {subset_name}: {e}")

        # 10,000-iteration pair-cluster bootstrap (seed=20260101) on linear probability & logit slopes
        rng = np.random.default_rng(20260101)
        unique_pairs = sub_df["pair_id"].unique()
        n_pairs = len(unique_pairs)
        pair_groups = {pid: grp for pid, grp in sub_df.groupby("pair_id")}

        # Fast vectorized cluster bootstrap using pre-extracted arrays per pair
        pair_arrays = []
        for pid in unique_pairs:
            g = pair_groups[pid]
            pair_arrays.append(g[["hit10", "dose_realized", "is_lowIC", "dose_x_lowIC", "log10_footprint"]].to_numpy())

        boot_slope_topIC = []
        boot_slope_lowIC = []
        boot_diff_slope = []
        for _ in range(10000):
            sampled_idx = rng.integers(0, n_pairs, size=n_pairs)
            arr = np.vstack([pair_arrays[i] for i in sampled_idx])
            hit = arr[:, 0]
            dose = arr[:, 1]
            low = arr[:, 2]
            # OLS slope in del_topIC (low == 0) and del_lowIC_matched (low == 1)
            m0 = (low == 0)
            m1 = (low == 1)
            if m0.sum() > 2 and np.var(dose[m0]) > 0:
                s0 = np.cov(dose[m0], hit[m0], ddof=0)[0, 1] / np.var(dose[m0])
            else:
                s0 = 0.0
            if m1.sum() > 2 and np.var(dose[m1]) > 0:
                s1 = np.cov(dose[m1], hit[m1], ddof=0)[0, 1] / np.var(dose[m1])
            else:
                s1 = 0.0
            boot_slope_topIC.append(s0)
            boot_slope_lowIC.append(s1)
            boot_diff_slope.append(s1 - s0)

        boot_slope_topIC = np.array(boot_slope_topIC)
        boot_slope_lowIC = np.array(boot_slope_lowIC)
        boot_diff_slope = np.array(boot_diff_slope)

        # Footprint memorization logistic model: hit10 ~ dose_realized * log10_footprint
        sub_df["dose_x_fp"] = sub_df["dose_realized"] * sub_df["log10_footprint"]
        X_fp = sm.add_constant(sub_df[["dose_realized", "log10_footprint", "dose_x_fp"]])
        logit_fp = sm.Logit(y, X_fp).fit(disp=False, cov_type="cluster", cov_kwds={"groups": sub_df["pair_id"]})

        # Stratify recall@10 by footprint tertiles / median
        fp_med = sub_df["footprint"].median()
        high_fp = sub_df[sub_df["footprint"] > fp_med]
        low_fp = sub_df[sub_df["footprint"] <= fp_med]

        models_out[subset_name] = {
            "n_calls": int(len(sub_df)),
            "n_pairs": int(n_pairs),
            "logit_params": params,
            "logit_bse": bse,
            "logit_zvals": zvals,
            "logit_pvals_two_sided": pvals_two_sided,
            "p_beta1_onesided": p_beta1_onesided,
            "p_beta3_onesided": p_beta3_onesided,
            "boot_linear_slope_topIC": {
                "mean": float(boot_slope_topIC.mean()),
                "ci95": [float(np.percentile(boot_slope_topIC, 2.5)), float(np.percentile(boot_slope_topIC, 97.5))],
                "p_lt_0_onesided": float(np.mean(boot_slope_topIC >= 0)),
            },
            "boot_linear_slope_lowIC": {
                "mean": float(boot_slope_lowIC.mean()),
                "ci95": [float(np.percentile(boot_slope_lowIC, 2.5)), float(np.percentile(boot_slope_lowIC, 97.5))],
            },
            "boot_slope_diff_low_minus_top": {
                "mean": float(boot_diff_slope.mean()),
                "ci95": [float(np.percentile(boot_diff_slope, 2.5)), float(np.percentile(boot_diff_slope, 97.5))],
                "p_gt_0_onesided": float(np.mean(boot_diff_slope <= 0)),
            },
            "footprint_model": {
                "params": logit_fp.params.to_dict(),
                "bse": logit_fp.bse.to_dict(),
                "zvals": logit_fp.tvalues.to_dict(),
                "pvals": logit_fp.pvalues.to_dict(),
                "high_footprint_hit10": float(high_fp["hit10"].mean()),
                "low_footprint_hit10": float(low_fp["hit10"].mean()),
                "footprint_median": float(fp_med),
            }
        }
        print(f"  [{subset_name}] beta_1 (dose_topIC) = {params.get('dose_realized', 0):.3f} "
              f"(SE={bse.get('dose_realized', 0):.3f}, p_1sided={p_beta1_onesided:.4f}, p_2sided={pvals_two_sided.get('dose_realized', 1):.4f})")
        print(f"  [{subset_name}] beta_3 (dose x lowIC) = {params.get('dose_x_lowIC', 0):.3f} "
              f"(SE={bse.get('dose_x_lowIC', 0):.3f}, p_1sided={p_beta3_onesided:.4f}, p_2sided={pvals_two_sided.get('dose_x_lowIC', 1):.4f})")
        print(f"  [{subset_name}] Footprint effect: log10_fp beta = {logit_fp.params['log10_footprint']:.3f} "
              f"(p={logit_fp.pvalues['log10_footprint']:.4e}); High-FP hit@10={high_fp['hit10'].mean()*100:.1f}% vs Low-FP={low_fp['hit10'].mean()*100:.1f}%")

    # Decoy / Attractor analysis: When hit10 == 0 (or across all false predictions), which genes dominate?
    false_preds_by_dose = defaultdict(Counter)
    all_preds_by_dose = defaultdict(Counter)
    for _, row in df.iterrows():
        d = row["dose_target"]
        target = row["gene_symbol"]
        for p in row["preds"]:
            all_preds_by_dose[d][p] += 1
            if p != target:
                false_preds_by_dose[d][p] += 1

    decoy_summary = {}
    for d in [0, 25, 50]:
        cnt = false_preds_by_dose[d]
        tot_false = sum(cnt.values())
        top15 = cnt.most_common(15)
        top15_share = sum(v for _, v in top15) / tot_false if tot_false else 0.0
        decoy_summary[f"d{d}"] = {
            "total_non_target_predictions": tot_false,
            "unique_non_target_genes": len(cnt),
            "top15_decoys": [{"gene": g, "count": c, "pct": round(100.0 * c / tot_false, 2)} for g, c in top15],
            "top15_share_pct": round(100.0 * top15_share, 2),
        }

    return {
        "n_total_rows": int(len(df)),
        "n_unique_pairs": int(df["pair_id"].nunique()),
        "descriptive_by_cell": desc,
        "models": models_out,
        "decoy_attractors": decoy_summary,
    }


def compute_ece(probs, y_true, n_bins=10):
    probs = np.asarray(probs, dtype=float)
    y_true = np.asarray(y_true, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bin_details = []
    for i in range(n_bins):
        if i < n_bins - 1:
            mask = (probs >= bins[i]) & (probs < bins[i + 1])
        else:
            mask = (probs >= bins[i]) & (probs <= bins[i + 1])
        if np.sum(mask) > 0:
            avg_conf = float(np.mean(probs[mask]))
            avg_acc = float(np.mean(y_true[mask]))
            weight = float(np.sum(mask)) / len(probs)
            ece += weight * abs(avg_conf - avg_acc)
            bin_details.append({
                "bin": f"[{bins[i]:.1f}, {bins[i+1]:.1f}]",
                "n": int(np.sum(mask)),
                "mean_conf": avg_conf,
                "emp_acc": avg_acc,
            })
    brier = float(np.mean((probs - y_true) ** 2))
    return float(ece), brier, bin_details


def analyze_dim6_calibration(step1_res_path):
    print("\n=== 2. Dimension 6: Self-Knowledge & Calibration Analysis ===")
    runs = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]

    # 2A. Parent Step 1 (360 mechanisms across 12 runs) & Step 3 (120 candidates across 12 runs)
    s1_rows = []
    s3_rows = []
    for run_id in runs:
        rdir = os.path.join(RUNS_DIR, run_id)
        s1 = json.load(open(os.path.join(rdir, "step1_mechanisms.json"), encoding="utf-8"))
        btl1 = json.load(open(os.path.join(rdir, "step3_btl_t1.json"), encoding="utf-8"))
        s3 = json.load(open(os.path.join(rdir, "step3_candidates.json"), encoding="utf-8"))
        s5 = json.load(open(os.path.join(rdir, "step5_top5.json"), encoding="utf-8"))

        top10_mkeys = set(btl1["fit"]["ranking"][:10])
        top5_mkeys = set(x["source_mechanism_key"] for x in s5["top5"])
        top5_cids = set(x["cand_id"] for x in s5["top5"])

        for m in s1["mechanisms"]:
            mid = int(m["id"])
            mkey = f"M{mid - 1:02d}"
            conf = float(m["confidence"]) / 100.0
            s1_rows.append({
                "run_id": run_id,
                "disease": s1["disease"],
                "arm": s1["arm"],
                "item_id": mkey,
                "conf": conf,
                "y_top10_t1": 1 if mkey in top10_mkeys else 0,
                "y_top5_final": 1 if mkey in top5_mkeys else 0,
            })

        for c in s3["candidates"]:
            cid = c["cand_id"]
            conf = float(c["confidence"]) / 100.0
            s3_rows.append({
                "run_id": run_id,
                "disease": s1["disease"],
                "arm": s1["arm"],
                "item_id": cid,
                "conf": conf,
                "y_top5_final": 1 if cid in top5_cids else 0,
            })

    df_s1 = pd.DataFrame(s1_rows)
    df_s3 = pd.DataFrame(s3_rows)

    # 2B. Experiment B Stage 1 (70 hypotheses across 14 domains)
    expB_rows = []
    shared_dir = os.path.join(RUNS_DIR, "expB", "_shared_stage1")
    # Load pubmed cache if available to check groundedness of each hypothesis in as_discovered
    pm_cache_path = os.path.join(OUT_DIR, "pubmed_cache.json")
    pm_cache = json.load(open(pm_cache_path, encoding="utf-8")) if os.path.exists(pm_cache_path) else {}

    for d_idx in range(1, 15):
        did = f"B{d_idx:02d}"
        s1_file = os.path.join(shared_dir, f"{did}_stage1.json")
        if not os.path.exists(s1_file):
            continue
        arr = json.load(open(s1_file, encoding="utf-8"))
        for item in arr:
            h_id = int(item["id"])
            conf = float(item["confidence"]) / 100.0
            # Check how many of the 6 slots in as_discovered exist in PubMed
            h_file = os.path.join(RUNS_DIR, "expB", "as_discovered", f"{did}_h{h_id}.json")
            n_exist = 0
            if os.path.exists(h_file):
                slots = json.load(open(h_file, encoding="utf-8"))
                for sl in slots:
                    pmid = str(sl.get("pmid", "")).strip()
                    if pmid in pm_cache and pm_cache[pmid].get("exists", False):
                        n_exist += 1
            expB_rows.append({
                "domain_id": did,
                "h_id": h_id,
                "conf": conf,
                "n_exist_slots": n_exist,
                "prop_exist": n_exist / 6.0,
                "y_maj_exist": 1 if n_exist >= 3 else 0,
            })
    df_expB = pd.DataFrame(expB_rows)

    def fit_calibration(probs, y, cluster_ids, name):
        probs_clipped = np.clip(probs, 1e-4, 1.0 - 1e-4)
        logit_p = np.log(probs_clipped / (1.0 - probs_clipped))
        X = sm.add_constant(logit_p)
        mod = sm.Logit(y, X).fit(disp=False, cov_type="cluster", cov_kwds={"groups": cluster_ids})
        intercept = float(mod.params[0])
        slope = float(mod.params[1])
        se_slope = float(mod.bse[1])
        # Test H0: slope = 1 (Confirmatory Family Member 6)
        z_vs_1 = (slope - 1.0) / se_slope if se_slope > 0 else 0.0
        p_vs_1 = float(2.0 * (1.0 - stats.norm.cdf(abs(z_vs_1))))
        p_vs_0 = float(mod.pvalues[1])

        ece_raw, brier_raw, bins_raw = compute_ece(probs, y)

        # Leave-One-Cluster-Out (LORO) Platt Scaling Recalibration
        unique_clusters = np.unique(cluster_ids)
        recal_probs = np.zeros_like(probs, dtype=float)
        for c in unique_clusters:
            train_mask = (cluster_ids != c)
            test_mask = (cluster_ids == c)
            X_tr = sm.add_constant(logit_p[train_mask])
            y_tr = y[train_mask]
            try:
                m_tr = sm.Logit(y_tr, X_tr).fit(disp=False)
                X_te = sm.add_constant(logit_p[test_mask], has_constant="add")
                recal_probs[test_mask] = m_tr.predict(X_te)
            except Exception:
                recal_probs[test_mask] = np.mean(y_tr)

        ece_recal, brier_recal, bins_recal = compute_ece(recal_probs, y)
        spearman_r, spearman_p = stats.spearmanr(probs, y)

        print(f"  [{name}] n={len(y)}, mean_conf={np.mean(probs)*100:.1f}%, emp_rate={np.mean(y)*100:.1f}%, "
              f"slope={slope:.3f} (SE={se_slope:.3f}, p_H0_slope=1: {p_vs_1:.4e}), "
              f"ECE: {ece_raw:.3f} -> LORO Platt {ece_recal:.3f} (Brier: {brier_raw:.3f} -> {brier_recal:.3f})")

        return {
            "n": int(len(y)),
            "mean_conf": float(np.mean(probs)),
            "sd_conf": float(np.std(probs)),
            "min_conf": float(np.min(probs)),
            "max_conf": float(np.max(probs)),
            "empirical_rate": float(np.mean(y)),
            "overconfidence_gap": float(np.mean(probs) - np.mean(y)),
            "calibration_intercept": intercept,
            "calibration_slope": slope,
            "calibration_slope_se": se_slope,
            "z_slope_eq_1": float(z_vs_1),
            "p_slope_eq_1": p_vs_1,
            "p_slope_eq_0": p_vs_0,
            "spearman_r": float(spearman_r),
            "spearman_p": float(spearman_p),
            "ece_before": ece_raw,
            "brier_before": brier_raw,
            "ece_after_loro_platt": ece_recal,
            "brier_after_loro_platt": brier_recal,
            "ece_reduction_pct": float(100.0 * (ece_raw - ece_recal) / ece_raw) if ece_raw > 0 else 0.0,
            "bins_before": bins_raw,
            "bins_after": bins_recal,
        }

    cal_s1_top5 = fit_calibration(
        df_s1["conf"].to_numpy(), df_s1["y_top5_final"].to_numpy(), df_s1["run_id"].to_numpy(),
        "Parent_Step1_Mechanism_to_Top5 (n=360)"
    )
    cal_s1_top10 = fit_calibration(
        df_s1["conf"].to_numpy(), df_s1["y_top10_t1"].to_numpy(), df_s1["run_id"].to_numpy(),
        "Parent_Step1_Mechanism_to_T1_Top10 (n=360)"
    )
    cal_s3_top5 = fit_calibration(
        df_s3["conf"].to_numpy(), df_s3["y_top5_final"].to_numpy(), df_s3["run_id"].to_numpy(),
        "Parent_Step3_Candidate_to_Top5 (n=120)"
    )

    # Pooled Parent Calibration (Step 1 + Step 3 = 480 confidence statements)
    pooled_probs = np.concatenate([df_s1["conf"].to_numpy(), df_s3["conf"].to_numpy()])
    pooled_y = np.concatenate([df_s1["y_top5_final"].to_numpy(), df_s3["y_top5_final"].to_numpy()])
    pooled_clusters = np.concatenate([df_s1["run_id"].to_numpy(), df_s3["run_id"].to_numpy()])
    cal_pooled_parent = fit_calibration(
        pooled_probs, pooled_y, pooled_clusters,
        "Parent_Pooled_All_Confidence_to_Top5 (n=480)"
    )

    cal_expB = {}
    if len(df_expB) > 0:
        cal_expB = fit_calibration(
            df_expB["conf"].to_numpy(), df_expB["y_maj_exist"].to_numpy(), df_expB["domain_id"].to_numpy(),
            "ExpB_Stage1_Confidence_to_VerifiedPMID_Maj (n=70)"
        )

    return {
        "step1_to_top5": cal_s1_top5,
        "step1_to_t1_top10": cal_s1_top10,
        "step3_to_top5": cal_s3_top5,
        "parent_pooled_n480": cal_pooled_parent,
        "expB_stage1_n70": cal_expB,
    }


def analyze_reasoning_paradox():
    print("\n=== 3. The Test-Time Reasoning Paradox (8,972 Live Calls / 35.58M Reasoning Tokens) ===")
    log_path = os.path.join(DATA_DIR, "calls_log.jsonl")
    calls_by_id = {}
    all_live_calls = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("mock", False):
                continue
            all_live_calls.append(rec)
            # Keep latest successful call per call_id
            cid = rec.get("call_id", "")
            if rec.get("ok", False):
                calls_by_id[cid] = rec

    print(f"Total live call records: {len(all_live_calls)}; unique successful call_ids: {len(calls_by_id)}")

    # Categorize all live calls by block
    block_stats = defaultdict(lambda: {"n_calls": 0, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "elapsed_s": 0.0, "r_tokens_list": []})
    for rec in all_live_calls:
        cid = rec.get("call_id", "")
        vendor = rec.get("vendor", "unknown")
        if cid.startswith("parent/"):
            parts = cid.split("/")
            step = parts[2] if len(parts) > 2 else "other"
            bkey = f"parent_{step}"
        elif cid.startswith("expB/"):
            parts = cid.split("/")
            stage = parts[2] if len(parts) > 2 else "other"
            arm = parts[3] if len(parts) > 3 else ""
            bkey = f"expB_{stage}_{arm}" if arm else f"expB_{stage}"
        elif cid.startswith("expC_v4/"):
            bkey = f"expC_v4_{vendor}"
        elif cid.startswith("canary/"):
            bkey = f"canary_{vendor}"
        else:
            bkey = f"other_{vendor}"

        rt = int(rec.get("reasoning_tokens") or 0)
        ot = int(rec.get("output_tokens") or 0)
        it = int(rec.get("input_tokens") or 0)
        el = float(rec.get("elapsed_s") or 0.0)

        bs = block_stats[bkey]
        bs["n_calls"] += 1
        bs["input_tokens"] += it
        bs["output_tokens"] += ot
        bs["reasoning_tokens"] += rt
        bs["elapsed_s"] += el
        bs["r_tokens_list"].append(rt)

    block_summary = {}
    tot_rt = 0
    tot_ot = 0
    tot_it = 0
    for bkey, bs in sorted(block_stats.items()):
        arr = np.array(bs["r_tokens_list"], dtype=float)
        tot_rt += bs["reasoning_tokens"]
        tot_ot += bs["output_tokens"]
        tot_it += bs["input_tokens"]
        block_summary[bkey] = {
            "n_calls": bs["n_calls"],
            "input_tokens": bs["input_tokens"],
            "output_tokens": bs["output_tokens"],
            "reasoning_tokens": bs["reasoning_tokens"],
            "reasoning_share_of_output_pct": round(100.0 * bs["reasoning_tokens"] / max(1, bs["output_tokens"]), 2),
            "median_reasoning_tokens": float(np.median(arr)) if len(arr) else 0.0,
            "iqr_reasoning_tokens": [float(np.percentile(arr, 25)), float(np.percentile(arr, 75))] if len(arr) else [0.0, 0.0],
            "max_reasoning_tokens": int(np.max(arr)) if len(arr) else 0,
            "total_elapsed_hours": round(bs["elapsed_s"] / 3600.0, 2),
        }
        print(f"  {bkey:28s}: calls={bs['n_calls']:4d}, reasoning_tokens={bs['reasoning_tokens']:10,d} "
              f"(median={np.median(arr):.0f}, IQR={np.percentile(arr,25):.0f}-{np.percentile(arr,75):.0f}, max={np.max(arr):.0f})")

    print(f"  TOTAL ACROSS ALL LIVE CALLS : calls={len(all_live_calls)}, input={tot_it:,d}, output={tot_ot:,d}, reasoning={tot_rt:,d}")

    # Paradox Test 1: Tournament II Position Bias vs Reasoning Tokens
    # Map call_id: parent/{run_id}/step4_t2/{pair_idx:02d}_{dir}_j{j}
    runs = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]
    concordant_rt = []
    discordant_primacy_rt = []
    discordant_recency_rt = []
    pair_sum_concordant_rt = []
    pair_sum_discordant_rt = []

    for run_id in runs:
        s4 = json.load(open(os.path.join(RUNS_DIR, run_id, "step4_verdicts.json"), encoding="utf-8"))
        verdicts = s4["verdicts"]
        for p_idx in range(45):
            for j in [1, 2, 3]:
                ka = f"{p_idx:02d}_a_j{j}"
                kb = f"{p_idx:02d}_b_j{j}"
                va = verdicts.get(ka)
                vb = verdicts.get(kb)
                if not va or not vb or va.get("failed") or vb.get("failed"):
                    continue
                wa_idx = va.get("winner_idx")
                wb_idx = vb.get("winner_idx")
                sa = va.get("slot_winner")
                sb = vb.get("slot_winner")
                if wa_idx is None or wb_idx is None:
                    continue
                cid_a = f"parent/{run_id}/step4/{ka}"
                cid_b = f"parent/{run_id}/step4/{kb}"
                rec_a = calls_by_id.get(cid_a)
                rec_b = calls_by_id.get(cid_b)
                if not rec_a or not rec_b:
                    continue
                rt_a = int(rec_a.get("reasoning_tokens") or 0)
                rt_b = int(rec_b.get("reasoning_tokens") or 0)
                if wa_idx == wb_idx:
                    concordant_rt.extend([rt_a, rt_b])
                    pair_sum_concordant_rt.append(rt_a + rt_b)
                else:
                    pair_sum_discordant_rt.append(rt_a + rt_b)
                    if sa == "A" and sb == "A":
                        discordant_primacy_rt.extend([rt_a, rt_b])
                    else:
                        discordant_recency_rt.extend([rt_a, rt_b])

    concordant_rt = np.array(concordant_rt, dtype=float)
    discordant_primacy_rt = np.array(discordant_primacy_rt, dtype=float)
    pair_sum_concordant_rt = np.array(pair_sum_concordant_rt, dtype=float)
    pair_sum_discordant_rt = np.array(pair_sum_discordant_rt, dtype=float)

    u_stat, u_pval = stats.mannwhitneyu(discordant_primacy_rt, concordant_rt, alternative="two-sided")
    print(f"  [Paradox T2 Judging] Concordant call reasoning tokens: median={np.median(concordant_rt):.0f} (mean={np.mean(concordant_rt):.0f}, n={len(concordant_rt)})")
    print(f"  [Paradox T2 Judging] Position-biased (Slot-A primacy) call reasoning tokens: median={np.median(discordant_primacy_rt):.0f} (mean={np.mean(discordant_primacy_rt):.0f}, n={len(discordant_primacy_rt)}), M-W p={u_pval:.4e}")

    # Paradox Test 2: Experiment B Stage 2 reasoning tokens vs citation behavior
    expB_rt_by_arm = defaultdict(list)
    for d_idx in range(1, 15):
        did = f"B{d_idx:02d}"
        for arm in ["as_discovered", "abstain_probe", "gated"]:
            for h in range(1, 6):
                cid = f"expB/glm/stage2/{arm}/{did}/h{h}"
                rec = calls_by_id.get(cid)
                if rec:
                    expB_rt_by_arm[arm].append(int(rec.get("reasoning_tokens") or 0))

    expB_rt_summary = {}
    for arm, rts in expB_rt_by_arm.items():
        arr = np.array(rts, dtype=float)
        expB_rt_summary[arm] = {
            "n_calls": int(len(arr)),
            "mean_reasoning_tokens": float(np.mean(arr)),
            "median_reasoning_tokens": float(np.median(arr)),
            "iqr": [float(np.percentile(arr, 25)), float(np.percentile(arr, 75))],
            "max": int(np.max(arr)),
            "total_reasoning_tokens": int(np.sum(arr)),
        }
        print(f"  [Paradox ExpB {arm:14s}] n={len(arr)}, median_rt={np.median(arr):.0f}, mean_rt={np.mean(arr):.0f}, max={np.max(arr):.0f}")

    # Paradox Test 3: Experiment C-v4 reasoning tokens by vendor, dose, and hit10
    expC_rt_rows = []
    with open(os.path.join(RUNS_DIR, "expC_v4", "results.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if not r.get("ok", False):
                continue
            cid = r["call_id"]
            rec = calls_by_id.get(cid)
            if rec:
                expC_rt_rows.append({
                    "vendor": r["vendor"],
                    "arm": r["arm"],
                    "dose": int(r["dose_target"]),
                    "hit10": 1 if r.get("hit10", False) else 0,
                    "reasoning_tokens": int(rec.get("reasoning_tokens") or 0),
                })
    df_crt = pd.DataFrame(expC_rt_rows)
    expC_rt_summary = {}
    for (vendor, hit), g in df_crt.groupby(["vendor", "hit10"]):
        arr = g["reasoning_tokens"].to_numpy()
        expC_rt_summary[f"{vendor}_hit{hit}"] = {
            "n": int(len(arr)),
            "mean_rt": float(np.mean(arr)),
            "median_rt": float(np.median(arr)),
            "iqr": [float(np.percentile(arr, 25)), float(np.percentile(arr, 75))],
        }
        print(f"  [Paradox ExpC {vendor} hit10={hit}] n={len(arr)}, median_rt={np.median(arr):.0f}, mean_rt={np.mean(arr):.0f}")

    for (vendor, dose), g in df_crt.groupby(["vendor", "dose"]):
        arr = g["reasoning_tokens"].to_numpy()
        expC_rt_summary[f"{vendor}_d{dose}"] = {
            "n": int(len(arr)),
            "mean_rt": float(np.mean(arr)),
            "median_rt": float(np.median(arr)),
        }

    return {
        "total_live_calls": len(all_live_calls),
        "total_input_tokens": tot_it,
        "total_output_tokens": tot_ot,
        "total_reasoning_tokens": tot_rt,
        "overall_reasoning_share_of_output_pct": round(100.0 * tot_rt / max(1, tot_ot), 2),
        "by_block": block_summary,
        "t2_judging_paradox": {
            "n_concordant_calls": int(len(concordant_rt)),
            "concordant_median_rt": float(np.median(concordant_rt)),
            "concordant_mean_rt": float(np.mean(concordant_rt)),
            "concordant_iqr_rt": [float(np.percentile(concordant_rt, 25)), float(np.percentile(concordant_rt, 75))],
            "n_primacy_biased_calls": int(len(discordant_primacy_rt)),
            "primacy_biased_median_rt": float(np.median(discordant_primacy_rt)),
            "primacy_biased_mean_rt": float(np.mean(discordant_primacy_rt)),
            "primacy_biased_iqr_rt": [float(np.percentile(discordant_primacy_rt, 25)), float(np.percentile(discordant_primacy_rt, 75))],
            "total_rt_spent_on_primacy_flips": int(np.sum(discordant_primacy_rt)),
            "mannwhitney_u": float(u_stat),
            "mannwhitney_p": float(u_pval),
        },
        "expB_reasoning_by_arm": expB_rt_summary,
        "expC_reasoning": expC_rt_summary,
    }


def main():
    expC_res = analyze_expC()
    dim6_res = analyze_dim6_calibration(os.path.join(OUT_DIR, "step1_dim1_expB_results.json"))
    paradox_res = analyze_reasoning_paradox()

    out = {
        "expC_v4": expC_res,
        "dim6_self_knowledge": dim6_res,
        "reasoning_paradox": paradox_res,
    }
    out_path = os.path.join(OUT_DIR, "step3_expC_dim6_paradox_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved complete Step 3 analysis to {out_path}")


if __name__ == "__main__":
    main()
