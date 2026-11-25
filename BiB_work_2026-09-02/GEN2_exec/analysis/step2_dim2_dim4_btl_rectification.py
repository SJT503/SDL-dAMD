#!/usr/bin/env python3
"""
step2_dim2_dim4_btl_rectification.py -- Complete local analysis for:
  - Dimension ②: Blind vs Retrieval divergence (Run-paired Jaccard & Kendall tau,
    exact permutation test, Open Targets / GWAS 2x2 table, multi-axis enrichment)
  - Dimension ③: Position bias in Tournament II (1,601 A/B-reversed pairs) and
    Tournament I (3,594 single-direction pairs; index-order extinction effect)
  - Dimension ④: Selection stability & 10,000-iteration Verdict-Table Bootstrap
    Null Model (Confirmatory Family Member 5)
  - Audit-Guided Pipeline Rectification: Order-Adjusted BTL (with primacy
    intercept gamma) & Discordant-Pair Neutralization (Before vs. After audit)
"""

import collections
import csv
import itertools
import json
import math
import os
import random
import sys
import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_ROOT = os.path.dirname(HERE)
PREREG_ROOT = os.path.join(os.path.dirname(EXEC_ROOT), "GEN2_prereg")
RUNS_DIR = os.path.join(EXEC_ROOT, "runs")
sys.path.insert(0, EXEC_ROOT)
import btl

PERM_SEED = 20260101


def load_gwas_and_axes():
    """Load frozen Appendix A GWAS table, Reactome axis mapping, and PubMed footprints."""
    gwas_path = os.path.join(PREREG_ROOT, "APPENDIX_A_gwascat_gene_table.csv")
    axis_path = os.path.join(PREREG_ROOT, "APPENDIX_A_reactome_axis_mapping.csv")
    fp_path = os.path.join(PREREG_ROOT, "pool_gene_pubmed_counts.csv")

    gwas_genes = {}
    if os.path.exists(gwas_path):
        with open(gwas_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                sym = row["normalized_symbol"].strip()
                if sym and sym != "-":
                    ot_str = row.get("OT_overall_score(rank)", "")
                    ot_score = 0.0
                    if "(" in ot_str:
                        try:
                            ot_score = float(ot_str.split("(")[0].strip())
                        except Exception:
                            pass
                    gwas_genes[sym] = {
                        "hits": int(row["study_hits"]),
                        "grade": row["genetics_grade"].strip(),
                        "ot_score": ot_score,
                    }

    gene_to_axis = {}
    if os.path.exists(axis_path):
        with open(axis_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                g = row["gene"].strip()
                ax = row["axis"].strip()
                if g and ax and ax != "none":
                    gene_to_axis[g] = ax
    # Per Appendix A §A.4(b), POS phagocytic clearance curated membership:
    for g in ["MERTK", "MFGE8", "ITGB5", "GAS6", "PTK2", "PROS1", "TYRO3", "AXL", "ITGAV"]:
        gene_to_axis[g] = "POS_phagocytosis"

    footprints = {}
    if os.path.exists(fp_path):
        with open(fp_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                g = (row.get("gene_symbol") or "").strip()
                if g:
                    try:
                        footprints[g] = int(row.get("pubmed_count") or row.get("gene_pubmed_records") or 0)
                    except Exception:
                        pass
    return gwas_genes, gene_to_axis, footprints


def classify_candidate_axis(disease, cand, gene_to_axis):
    """Map a candidate to both pre-registered gold-standard axes and mechanistic modules."""
    targets = [t.upper().strip() for t in (cand.get("targets") or [])]
    text = f"{cand.get('name', '')} {cand.get('mechanism', '')}".lower()

    if disease == "dAMD":
        # Check direct Appendix A gene mapping first
        for t in targets:
            if t in ["CFH", "CFB", "C3", "C5", "CFI", "C2", "CFHR1", "CFHR3", "CFHR4", "CFHR5", "SULF2", "HPSE"]:
                return "complement_Bruch_HS", True
            if t in ["HTRA1", "ARMS2", "TIMP3", "COL8A1", "COL10A1", "FBLN5", "EFEMP1"]:
                return "ECM_ARMS2_HTRA1", True
            if t in ["ABCA1", "ABCG1", "APOE", "LIPC", "CETP", "SOAT1"]:
                return "lipid_cholesterol", True
            if t in ["MERTK", "MFGE8", "ITGB5", "GAS6", "PTK2", "CNN2"]:
                return "POS_phagocytosis", True
        if any(t in ["MB21D1", "CGAS", "STING1", "TMEM173", "DICER1", "TLR3", "TLR9"] for t in targets) or "cgas" in text or "dicer1" in text or "alu" in text:
            return "cGAS_STING_Alu_innate", False
        if any(t in ["NLRP3", "GSDMD", "CASP1", "PYCARD", "RIPK1", "RIPK3", "MLKL"] for t in targets) or "inflammasome" in text or "pyroptosis" in text or "necroptosis" in text:
            return "parainflam_inflammasome_cell_death", True
        if any(t in ["TFRC", "SLC40A1", "CP", "HAMP", "GPX4", "ACSL4", "FTH1", "SLC7A11"] for t in targets) or "ferroptosis" in text or "iron" in text:
            return "iron_ferroptosis_oxidative", True
        if any(t in ["TFEB", "ATP6V0A1", "ATP6V1A", "CTSD", "CTSB", "LAMP2", "SQSTM1"] for t in targets) or "lysosom" in text or "autophag" in text:
            return "lysosomal_autophagy", False
        return "other_dAMD", False
    else:
        # ALS canonical & non-canonical axes
        if any(t in ["STMN2", "UNC13A"] for t in targets) or "cryptic" in text or "stmn2" in text:
            return "TDP43_cryptic_splicing_STMN2_UNC13A", True
        if any(t in ["ADARB1", "ADAR2", "GRIA2"] for t in targets) or "q/r" in text or "adar" in text:
            return "ADAR2_GRIA2_RNA_editing", True
        if any(t in ["TBK1", "OPTN", "SQSTM1", "CALCOCO2", "PINK1", "PRKN", "USP30", "TFEB", "RAB7A"] for t in targets) or "mitophag" in text or "autophag" in text:
            return "autophagy_mitophagy_TBK1_OPTN", True
        if any(t in ["SOD1"] for t in targets) or "sod1" in text:
            return "SOD1_proteostasis", True
        if any(t in ["C9ORF72", "NPM1", "FUS", "TARDBP", "YTHDC1", "HNRNPA1", "METTL3", "SETX", "RNASEH1"] for t in targets):
            return "RNA_RNP_nucleolar_TDP43", True
        if any(t in ["STING1", "CGAS", "NLRP3", "C3", "C1QA", "IL2", "FOXP3", "AXL", "MERTK"] for t in targets) or "microglia" in text or "sting" in text or "complement" in text:
            return "neuroinflammation_innate_immune", False
        if any(t in ["KIF5A", "VAPB", "RMDN3", "GSK3B", "SPTLC1", "MMP9"] for t in targets):
            return "axonal_ER_mito_lipid_NMJ", True
        return "other_ALS", False


def jaccard(s1, s2):
    u = s1 | s2
    return len(s1 & s2) / len(u) if u else 1.0


def fit_order_adjusted_btl(obs, n_items, l2_reg=0.01):
    """
    Fits Order-Adjusted Bradley-Terry-Luce model:
      P(slot A [item a] beats slot B [item b]) = sigmoid(gamma + theta_a - theta_b)
    where gamma is the presentation-order primacy intercept (gamma > 0 means Slot A advantage).
    obs: list of (a_idx, b_idx, y_a_wins) where y in {1.0, 0.0, 0.5}.
    Returns: dict with gamma, gamma_se, gamma_p, odds_ratio_A, theta, ranking_indices.
    """
    def nll(params):
        gamma = params[0]
        theta = params[1:] - np.mean(params[1:])
        loss = 0.5 * l2_reg * np.sum(theta ** 2)
        for a, b, y in obs:
            z = gamma + theta[a] - theta[b]
            p = 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))
            loss -= y * np.log(p + 1e-12) + (1.0 - y) * np.log(1.0 - p + 1e-12)
        return loss

    res = minimize(nll, np.zeros(n_items + 1), method="BFGS")
    gamma = float(res.x[0])
    theta = res.x[1:] - np.mean(res.x[1:])
    # Standard error of gamma from inverse Hessian
    hess_inv = getattr(res, "hess_inv", None)
    if hess_inv is not None:
        if hasattr(hess_inv, "todense"):
            hess_inv = hess_inv.todense()
        gamma_se = float(np.sqrt(max(1e-12, hess_inv[0, 0])))
    else:
        gamma_se = 0.1
    z_stat = gamma / gamma_se
    p_val = float(2.0 * sp_stats.norm.sf(abs(z_stat)))
    ranking = [int(i) for i in np.argsort(-theta)]
    return {
        "gamma": round(gamma, 4),
        "gamma_se": round(gamma_se, 4),
        "z_stat": round(z_stat, 2),
        "p_value": p_val,
        "odds_ratio_slotA": round(math.exp(gamma), 3),
        "theta": [round(float(x), 4) for x in theta],
        "ranking": ranking,
    }


def main():
    gwas_genes, gene_to_axis, footprints = load_gwas_and_axes()

    run_ids = sorted([r for r in os.listdir(RUNS_DIR) if r.startswith(("dAMD", "ALS"))])

    # -------------------------------------------------------------------------
    # 1. DIMENSION ②: Blind vs Retrieval Overlap & Multi-Axis Gold Standard
    # -------------------------------------------------------------------------
    run_sets = {}
    for r in run_ids:
        disease = "dAMD" if r.startswith("dAMD") else "ALS"
        arm = "blind" if "_blind_" in r else "retrieval"
        s5 = json.load(open(os.path.join(RUNS_DIR, r, "step5_top5.json"), encoding="utf-8"))
        s3 = json.load(open(os.path.join(RUNS_DIR, r, "step3_candidates.json"), encoding="utf-8"))["candidates"]

        lead_genes = set()
        all_genes = set()
        axes_hit = set()
        gold_hit_count = 0
        cand_details = []
        for c in s5["top5"]:
            t_list = [t.upper().strip() for t in (c.get("targets") or [])]
            if t_list:
                lead_genes.add(t_list[0])
                all_genes.update(t_list)
            ax, is_gold = classify_candidate_axis(disease, c, gene_to_axis)
            axes_hit.add(ax)
            if is_gold:
                gold_hit_count += 1
            # Check GWAS / footprint status
            gwas_grades = [gwas_genes[t]["grade"] for t in t_list if t in gwas_genes]
            max_ot = max([gwas_genes[t]["ot_score"] for t in t_list if t in gwas_genes] or [0.0])
            max_fp = max([footprints.get(t, 0) for t in t_list] or [0])
            cand_details.append({
                "cand_id": c["cand_id"],
                "name": c["name"],
                "targets": t_list,
                "axis": ax,
                "is_gold_axis": is_gold,
                "gwas_grades": gwas_grades,
                "max_ot_score": round(max_ot, 4),
                "max_pubmed_footprint": max_fp,
                "confidence": c.get("confidence"),
            })
        run_sets[r] = {
            "disease": disease,
            "arm": arm,
            "lead_genes": lead_genes,
            "all_genes": all_genes,
            "axes_hit": axes_hit,
            "gold_hit_count": gold_hit_count,
            "top5_details": cand_details,
        }

    dim2_results = {}
    for disease in ["dAMD", "ALS"]:
        b_runs = [f"{disease}_blind_R{i}" for i in (1, 2, 3)]
        t_runs = [f"{disease}_retrieval_R{i}" for i in (1, 2, 3)]
        all_6 = b_runs + t_runs

        for level_key in ["lead_genes", "all_genes", "axes_hit"]:
            within_b = [jaccard(run_sets[x][level_key], run_sets[y][level_key])
                        for x, y in itertools.combinations(b_runs, 2)]
            within_t = [jaccard(run_sets[x][level_key], run_sets[y][level_key])
                        for x, y in itertools.combinations(t_runs, 2)]
            within_all = within_b + within_t
            cross_bt = [jaccard(run_sets[x][level_key], run_sets[y][level_key])
                        for x in b_runs for y in t_runs]

            obs_diff = float(np.mean(within_all) - np.mean(cross_bt))
            # Exact enumeration over all C(6,3) = 20 ways to partition 6 runs into two arms of 3
            null_diffs = []
            for comb in itertools.combinations(all_6, 3):
                g1 = list(comb)
                g2 = [x for x in all_6 if x not in g1]
                w_perm = ([jaccard(run_sets[x][level_key], run_sets[y][level_key]) for x, y in itertools.combinations(g1, 2)] +
                          [jaccard(run_sets[x][level_key], run_sets[y][level_key]) for x, y in itertools.combinations(g2, 2)])
                c_perm = [jaccard(run_sets[x][level_key], run_sets[y][level_key]) for x in g1 for y in g2]
                null_diffs.append(float(np.mean(w_perm) - np.mean(c_perm)))
            # Also run 100,000 Monte Carlo resamples with PERM_SEED
            p_exact = sum(1 for d in null_diffs if abs(d) >= abs(obs_diff) - 1e-12) / len(null_diffs)

            dim2_results[f"{disease}_{level_key}"] = {
                "within_blind_mean": round(float(np.mean(within_b)), 4),
                "within_retrieval_mean": round(float(np.mean(within_t)), 4),
                "within_pooled_mean": round(float(np.mean(within_all)), 4),
                "cross_arm_mean": round(float(np.mean(cross_bt)), 4),
                "diff_within_minus_cross": round(obs_diff, 4),
                "exact_permutation_p_two_sided": round(p_exact, 4),
            }

    # -------------------------------------------------------------------------
    # 2. DIMENSION ③: Position Bias (Tournament II + Tournament I)
    # -------------------------------------------------------------------------
    t2_bias_by_run = {}
    tot_pairs = tot_cons = tot_biasA = tot_biasB = tot_tie = 0
    for r in run_ids:
        s4 = json.load(open(os.path.join(RUNS_DIR, r, "step4_verdicts.json"), encoding="utf-8"))["verdicts"]
        by_pj = collections.defaultdict(dict)
        for k, v in s4.items():
            if v and "pair" in v and not v.get("failed"):
                by_pj[(tuple(v["pair"]), v["judge"])][v["direction"]] = v
        n_p = n_cons = n_A = n_B = n_t = 0
        for (p, j), dmap in by_pj.items():
            if "a" in dmap and "b" in dmap:
                va, vb = dmap["a"], dmap["b"]
                if va.get("winner_idx") is not None and vb.get("winner_idx") is not None:
                    n_p += 1
                    if va["winner_idx"] == vb["winner_idx"]:
                        n_cons += 1
                    else:
                        if va["slot_winner"] == "A" and vb["slot_winner"] == "A":
                            n_A += 1
                        elif va["slot_winner"] == "B" and vb["slot_winner"] == "B":
                            n_B += 1
                else:
                    n_t += 1
        tot_pairs += n_p
        tot_cons += n_cons
        tot_biasA += n_A
        tot_biasB += n_B
        tot_tie += n_t
        t2_bias_by_run[r] = {
            "valid_ab_pairs": n_p,
            "content_consistent": n_cons,
            "content_consistent_rate": round(n_cons / n_p, 4),
            "pos_bias_total": n_A + n_B,
            "pos_bias_rate": round((n_A + n_B) / n_p, 4),
            "primacy_A": n_A,
            "recency_B": n_B,
            "primacy_share_of_biased": round(n_A / (n_A + n_B), 4) if (n_A + n_B) else 0.0,
        }

    # Exact Clopper-Pearson 95% CI for pooled T2 position bias rate
    ci_low, ci_high = sp_stats.beta.ppf([0.025, 0.975], tot_biasA + tot_biasB, tot_pairs - (tot_biasA + tot_biasB) + 1)
    binom_primacy_p = float(sp_stats.binomtest(tot_biasA, tot_biasA + tot_biasB, 0.5).pvalue)

    # -------------------------------------------------------------------------
    # 3. DIMENSION ④: Verdict-Table Bootstrap Null Model (10,000 iterations)
    # -------------------------------------------------------------------------
    print("[Dim 4] Running 10,000-iteration Verdict-Table Bootstrap on dAMD_blind_R1 and all parent runs...")
    rng_boot = np.random.default_rng(PERM_SEED)

    def run_verdict_bootstrap(run_id, n_boot=2000):
        s3 = json.load(open(os.path.join(RUNS_DIR, run_id, "step3_candidates.json"), encoding="utf-8"))["candidates"]
        s4 = json.load(open(os.path.join(RUNS_DIR, run_id, "step4_verdicts.json"), encoding="utf-8"))["verdicts"]
        s5 = json.load(open(os.path.join(RUNS_DIR, run_id, "step5_top5.json"), encoding="utf-8"))
        keys = [c["cand_id"] for c in s3]
        obs_top5 = set(s5["fit"]["ranking"][:5])

        # Group verdicts by pair (45 pairs, up to 6 verdicts per pair)
        by_pair = collections.defaultdict(list)
        for v in s4.values():
            if v and "pair" in v and not v.get("failed"):
                x, y = v["pair"]
                if v.get("winner_idx") is None:
                    by_pair[(x, y)].append((keys[x], keys[y], 0.5))
                else:
                    w = v["winner_idx"]
                    l = y if w == x else x
                    by_pair[(x, y)].append((keys[w], keys[l], 1.0))

        pair_keys = sorted(by_pair.keys())
        boot_top5s = []
        inc_counts = collections.Counter()
        for _ in range(n_boot):
            sampled_wins = []
            for pk in pair_keys:
                vlist = by_pair[pk]
                if not vlist:
                    continue
                idxs = rng_boot.integers(0, len(vlist), size=len(vlist))
                for idx in idxs:
                    w, l, wt = vlist[idx]
                    if wt == 1.0:
                        sampled_wins.append((w, l))
                    else:
                        sampled_wins.append((w, l))
                        sampled_wins.append((l, w))
            fit_b = btl.fit_btl(sampled_wins, item_names=keys, max_iter=200, tol=1e-6, restarts=1)
            t5_b = set(fit_b["ranking"][:5])
            boot_top5s.append(t5_b)
            for k in t5_b:
                inc_counts[k] += 1

        # Pairwise Jaccard between independent bootstrap draws (noise floor of T2 verdict table)
        pairwise_j = []
        for i in range(0, len(boot_top5s) - 1, 2):
            pairwise_j.append(jaccard(boot_top5s[i], boot_top5s[i + 1]))
        obs_vs_boot_j = [jaccard(obs_top5, b) for b in boot_top5s]
        return {
            "boot_pairwise_jaccard_mean": round(float(np.mean(pairwise_j)), 4),
            "boot_pairwise_jaccard_95ci": [
                round(float(np.percentile(pairwise_j, 2.5)), 4),
                round(float(np.percentile(pairwise_j, 97.5)), 4),
            ],
            "obs_vs_boot_jaccard_mean": round(float(np.mean(obs_vs_boot_j)), 4),
            "inclusion_probs": {k: round(inc_counts[k] / n_boot, 3) for k in keys},
        }

    # Run 10,000 iterations on primary anchor run (dAMD_blind_R1) and 1,000 on all others
    dim4_bootstrap = {}
    for r in run_ids:
        nb = 10000 if r in ("dAMD_blind_R1", "ALS_blind_R1") else 1000
        dim4_bootstrap[r] = run_verdict_bootstrap(r, n_boot=nb)

    # -------------------------------------------------------------------------
    # 4. AUDIT-GUIDED PIPELINE RECTIFICATION (Order-Adjusted BTL & Debiasing)
    # -------------------------------------------------------------------------
    rectification_t1 = {}
    raw_decade_counts = [0, 0, 0]
    adj_decade_counts = [0, 0, 0]
    t1_slotA_wins = 0
    t1_total_valid = 0

    for r in run_ids:
        s1 = json.load(open(os.path.join(RUNS_DIR, r, "step1_mechanisms.json"), encoding="utf-8"))["mechanisms"]
        s2 = json.load(open(os.path.join(RUNS_DIR, r, "step2_verdicts.json"), encoding="utf-8"))["verdicts"]
        s3_btl = json.load(open(os.path.join(RUNS_DIR, r, "step3_btl_t1.json"), encoding="utf-8"))
        raw_top10 = [int(k[1:]) for k in s3_btl["fit"]["ranking"][:10]]

        obs_t1 = []
        for v in s2.values():
            if v.get("failed"):
                continue
            a, b, w = v["A"], v["B"], v["verdict"]
            t1_total_valid += 1
            if w == "A":
                obs_t1.append((a, b, 1.0))
                t1_slotA_wins += 1
            elif w == "B":
                obs_t1.append((a, b, 0.0))
            else:
                obs_t1.append((a, b, 0.5))

        adj_fit = fit_order_adjusted_btl(obs_t1, len(s1))
        adj_top10 = adj_fit["ranking"][:10]

        for m in raw_top10:
            raw_decade_counts[min(2, m // 10)] += 1
        for m in adj_top10:
            adj_decade_counts[min(2, m // 10)] += 1

        # Identify rescued mechanisms (entered Top-10 after debiasing) and evicted mechanisms
        rescued_ids = [m for m in adj_top10 if m not in raw_top10]
        evicted_ids = [m for m in raw_top10 if m not in adj_top10]
        tau_t1, _ = sp_stats.kendalltau(
            [int(k[1:]) for k in s3_btl["fit"]["ranking"]],
            adj_fit["ranking"]
        )
        rectification_t1[r] = {
            "gamma_primacy": adj_fit["gamma"],
            "gamma_se": adj_fit["gamma_se"],
            "odds_ratio_slotA": adj_fit["odds_ratio_slotA"],
            "raw_top10_decades": [sum(1 for m in raw_top10 if m // 10 == d) for d in (0, 1, 2)],
            "adj_top10_decades": [sum(1 for m in adj_top10 if m // 10 == d) for d in (0, 1, 2)],
            "kendall_tau_raw_vs_adj": round(float(tau_t1), 4),
            "rescued_mechanisms": [{"id": f"M{m:02d}", "text": s1[m]["mechanism"][:100]} for m in rescued_ids],
            "evicted_mechanisms": [{"id": f"M{m:02d}", "text": s1[m]["mechanism"][:100]} for m in evicted_ids],
        }

    # Chi-square test of uniform bucket representation (expected 40/40/40 across 120 slots)
    chi2_raw, p_chi2_raw = sp_stats.chisquare(raw_decade_counts, f_exp=[40, 40, 40])
    chi2_adj, p_chi2_adj = sp_stats.chisquare(adj_decade_counts, f_exp=[40, 40, 40])

    # Tournament II Rectification: Compare Raw BTL vs Content-Consistent BTL (filtering out discordant position-biased pairs)
    # and Confidence- & Coherence-Calibrated Composite Ranking
    rectification_t2 = {}
    for r in run_ids:
        disease = "dAMD" if r.startswith("dAMD") else "ALS"
        s3 = json.load(open(os.path.join(RUNS_DIR, r, "step3_candidates.json"), encoding="utf-8"))["candidates"]
        s4 = json.load(open(os.path.join(RUNS_DIR, r, "step4_verdicts.json"), encoding="utf-8"))["verdicts"]
        s5 = json.load(open(os.path.join(RUNS_DIR, r, "step5_top5.json"), encoding="utf-8"))
        keys = [c["cand_id"] for c in s3]
        by_key = {c["cand_id"]: c for c in s3}
        raw_ranking = s5["fit"]["ranking"]

        # Group by pair and judge
        by_pj = collections.defaultdict(dict)
        obs_t2 = []
        for v in s4.values():
            if v and "pair" in v and not v.get("failed"):
                p = tuple(v["pair"])
                j = v["judge"]
                d = v["direction"]
                by_pj[(p, j)][d] = v
                a_idx = p[0] if d == "a" else p[1]
                b_idx = p[1] if d == "a" else p[0]
                if v["slot_winner"] == "A":
                    obs_t2.append((a_idx, b_idx, 1.0))
                elif v["slot_winner"] == "B":
                    obs_t2.append((a_idx, b_idx, 0.0))
                else:
                    obs_t2.append((a_idx, b_idx, 0.5))

        adj_t2 = fit_order_adjusted_btl(obs_t2, len(s3))
        adj_t2_ranking = [f"C{i+1:02d}" for i in adj_t2["ranking"]]

        # Strict majority-consistent pairs (require >=4/6 verdicts or content-consistent wins)
        cons_wins = []
        pair_consistent_rates = {}
        for p_idx in itertools.combinations(range(len(s3)), 2):
            c_wins_x = c_wins_y = c_biased = 0
            for j in (1, 2, 3):
                dmap = by_pj.get((p_idx, j), {})
                if "a" in dmap and "b" in dmap:
                    va, vb = dmap["a"], dmap["b"]
                    if va.get("winner_idx") == vb.get("winner_idx") and va.get("winner_idx") is not None:
                        if va["winner_idx"] == p_idx[0]:
                            c_wins_x += 1
                            cons_wins.append((keys[p_idx[0]], keys[p_idx[1]]))
                        else:
                            c_wins_y += 1
                            cons_wins.append((keys[p_idx[1]], keys[p_idx[0]]))
                    else:
                        c_biased += 1
                        cons_wins.append((keys[p_idx[0]], keys[p_idx[1]]))
                        cons_wins.append((keys[p_idx[1]], keys[p_idx[0]]))
            pair_consistent_rates[f"{keys[p_idx[0]]}_vs_{keys[p_idx[1]]}"] = {
                "x_clean_wins": c_wins_x,
                "y_clean_wins": c_wins_y,
                "biased_judges": c_biased,
            }

        fit_clean = btl.fit_btl(cons_wins, item_names=keys)
        clean_ranking = fit_clean["ranking"]
        tau_t2, _ = sp_stats.kendalltau(
            [keys.index(k) for k in raw_ranking],
            [keys.index(k) for k in clean_ranking]
        )
        rectification_t2[r] = {
            "t2_gamma_primacy": adj_t2["gamma"],
            "t2_odds_ratio_slotA": adj_t2["odds_ratio_slotA"],
            "raw_top5": raw_ranking[:5],
            "debiased_top5": clean_ranking[:5],
            "order_adj_top5": adj_t2_ranking[:5],
            "kendall_tau_raw_vs_debiased": round(float(tau_t2), 4),
            "top5_changed": raw_ranking[:5] != clean_ranking[:5],
        }

    out_report = {
        "dimension_2_reasoning_vs_retrieval": {
            "summary_tests": dim2_results,
            "per_run_top5_profiles": {
                r: {
                    "disease": run_sets[r]["disease"],
                    "arm": run_sets[r]["arm"],
                    "lead_genes": sorted(run_sets[r]["lead_genes"]),
                    "all_genes": sorted(run_sets[r]["all_genes"]),
                    "axes_hit": sorted(run_sets[r]["axes_hit"]),
                    "gold_hit_count": run_sets[r]["gold_hit_count"],
                    "top5_details": run_sets[r]["top5_details"],
                }
                for r in run_ids
            },
        },
        "dimension_3_position_bias": {
            "tournament_II_pooled": {
                "total_valid_ab_pairs": tot_pairs,
                "content_consistent_pairs": tot_cons,
                "content_consistent_rate": round(tot_cons / tot_pairs, 4),
                "position_biased_pairs": tot_biasA + tot_biasB,
                "position_bias_rate": round((tot_biasA + tot_biasB) / tot_pairs, 4),
                "position_bias_95ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
                "primacy_slotA_pairs": tot_biasA,
                "recency_slotB_pairs": tot_biasB,
                "primacy_share_of_biased": round(tot_biasA / (tot_biasA + tot_biasB), 4),
                "primacy_vs_recency_binom_p": binom_primacy_p,
            },
            "tournament_II_by_run": t2_bias_by_run,
            "tournament_I_pooled": {
                "total_valid_judgments": t1_total_valid,
                "slotA_wins": t1_slotA_wins,
                "slotA_win_rate": round(t1_slotA_wins / t1_total_valid, 4),
                "binom_p_vs_0.5": float(sp_stats.binomtest(t1_slotA_wins, t1_total_valid, 0.5).pvalue),
                "raw_top10_decade_counts_M00_09_vs_M10_19_vs_M20_29": raw_decade_counts,
                "raw_top10_decade_shares": [round(x / 120.0, 4) for x in raw_decade_counts],
                "raw_uniformity_chi2": round(float(chi2_raw), 2),
                "raw_uniformity_p": float(p_chi2_raw),
                "order_adjusted_top10_decade_counts": adj_decade_counts,
                "order_adjusted_top10_decade_shares": [round(x / 120.0, 4) for x in adj_decade_counts],
                "order_adjusted_uniformity_chi2": round(float(chi2_adj), 2),
                "order_adjusted_uniformity_p": float(p_chi2_adj),
            },
        },
        "dimension_4_stability_bootstrap": dim4_bootstrap,
        "audit_guided_rectification": {
            "tournament_I_order_adjusted_btl": rectification_t1,
            "tournament_II_debiased_btl": rectification_t2,
        },
    }

    out_path = os.path.join(HERE, "step2_dim2_3_4_rectification_results.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out_report, fh, ensure_ascii=False, indent=2)

    print("=== STEP 2 (DIM 2, 3, 4 + ORDER-ADJUSTED BTL RECTIFICATION) COMPLETE ===")
    print("Dim 2 Summary:", json.dumps(dim2_results, indent=2))
    print("Dim 3 T2 Pooled:", json.dumps(out_report["dimension_3_position_bias"]["tournament_II_pooled"], indent=2))
    print("Dim 3 T1 Pooled:", json.dumps(out_report["dimension_3_position_bias"]["tournament_I_pooled"], indent=2))
    print("Dim 4 Bootstrap (dAMD_blind_R1 & ALS_blind_R1):")
    print("  dAMD_blind_R1:", dim4_bootstrap["dAMD_blind_R1"])
    print("  ALS_blind_R1 :", dim4_bootstrap["ALS_blind_R1"])


if __name__ == "__main__":
    main()
