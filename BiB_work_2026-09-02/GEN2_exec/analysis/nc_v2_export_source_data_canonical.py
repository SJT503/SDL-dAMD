#!/usr/bin/env python3
"""
nc_v2_export_source_data_canonical.py -- Export Nature Communications mandatory
Source_Data_NC_v2.0.xlsx (v2.2 Canonical 6-Main-Figure [29 panels] + 4-Supp-Figure
[14 panels] = 43 panels) into GEN2_exec/figures_NC_v2_canonical/Source_Data_NC_v2.0.xlsx.
"""
from gate import gate, canary_gate, retry_limit

import json
import os
import pandas as pd

gate(__file__)

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_DIR = os.path.dirname(HERE)
OUT_XLSX = os.path.join(EXEC_DIR, "figures_NC_v2_canonical", "Source_Data_NC_v2.0.xlsx")


def write_blocks(writer, sheet_name: str, blocks: list):
    cur_row = 0
    for title, df in blocks:
        pd.DataFrame([[f"[{title}]"]]).to_excel(
            writer, sheet_name=sheet_name, index=False, header=False, startrow=cur_row
        )
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=cur_row + 1)
        cur_row += len(df) + 4


@retry_limit(2)
def main():
    s1 = json.load(open(os.path.join(HERE, "step1_pubmed_results.json"), encoding="utf-8"))
    s2 = json.load(open(os.path.join(HERE, "step2_dim2_3_4_rectification_results.json"), encoding="utf-8"))
    s3 = json.load(open(os.path.join(HERE, "step3_expC_dim6_paradox_results.json"), encoding="utf-8"))
    s4 = json.load(open(os.path.join(HERE, "step4_dim5_nli_results.json"), encoding="utf-8"))
    a1 = json.load(open(os.path.join(HERE, "nc_upgrade_A1_A4_results.json"), encoding="utf-8"))
    a2 = json.load(open(os.path.join(HERE, "nc_upgrade_A2_results.json"), encoding="utf-8"))
    a3 = json.load(open(os.path.join(HERE, "nc_upgrade_A3_A7_results.json"), encoding="utf-8"))
    a5_1 = json.load(open(os.path.join(HERE, "nc_upgrade_A5_part1_results.json"), encoding="utf-8"))
    a5_2 = json.load(open(os.path.join(HERE, "nc_upgrade_A5_part2_results.json"), encoding="utf-8"))
    a6 = json.load(open(os.path.join(HERE, "nc_upgrade_A6_A9_results.json"), encoding="utf-8"))
    ex = json.load(open(os.path.join(HERE, "nc_v2_exact_plot_arrays.json"), encoding="utf-8"))

    canary_gate(lambda: "fig3e_lit_footprint" in ex, "Verify canonical arrays loaded")

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        # 1. README
        pd.DataFrame([
            {"Sheet": "Fig1_Arch_and_Scorecard", "Description": "Figure 1A-D: Architecture overview & 4-block token ledger (1A-B), standardized |z| forest scorecard (1C), and 6-dimension radar (1D)."},
            {"Sheet": "Fig2_Citation_Gating", "Description": "Figure 2A-E: Two-tier verification grouped bars & 26 run/domain dots (2A), 12-run Step-6 point-intervals (2B), 14-domain x 3-arm heatmap (2C), GLM CoT phase plane (2D), and 5-LLM closed-loop 100% yield (2E)."},
            {"Sheet": "Fig3_Gene_Benchmark", "Description": "Figure 3A-F: 12-run pathway convergence (3A), multi-scale pairwise Jaccard boxplots (3B), HPO dose-response + Module 4a (3C), pure 2.1% CoT depth ECDF (3D), PubMed literature footprint stratification (3E), and top-10 stacked decoy attractors (3F)."},
            {"Sheet": "Fig4_Primacy_and_NLI", "Description": "Figure 4A-E: T2 12-run x 3-persona flips (4A), T1 grouped bucket boxplots & 12-run dots (4B), CoT Decile-1 Slot-A attention (4C), empirical NLI tail curve (4D), and cross-stage NLI phase space (4E)."},
            {"Sheet": "Fig5_Calibration_Paradox", "Description": "Figure 5A-D: 4-cell paired verdict-bootstrap null violins vs observed cross-run replicates (5A), Selective Platt reliability diagram (5B), and Reasoning Paradoxes 1-3 CoT distributions (5C-D)."},
            {"Sheet": "Fig6_Rectification_Frontier", "Description": "Figure 6A-E: T1/T2 primacy intercepts & Hessian SEs (6A), 9 rescued gold pathways (6B), horizontal paired 4-pillar point-intervals (6C), incremental module progression with 95% CIs (6D), and empirical 2D Pareto frontier (6E)."},
            {"Sheet": "SuppFig1_Entrez_ExpertAudit", "Description": "Supplementary Figure 1A-C: 5-LLM grouped safety & closed-loop yield (1A), 100-slot blinded expert calibration point-intervals (1B), and literature-density strata (1C)."},
            {"Sheet": "SuppFig2_ExpC_Ablation_Grid", "Description": "Supplementary Figure 2A-D: STROBE 630-call accounting (2A), HPO term-starvation ECDF (2B), 5-way external HGNC CoT-SRAD ablation with paired 95% CIs (2C), and 2D sensitivity grid (2D)."},
            {"Sheet": "SuppFig3_OABTL_Validation", "Description": "Supplementary Figure 3A-D: Intra-bucket empirical primacy (3A), Monte Carlo gamma_true recovery (3B), confounded-null Delta_{B1-B3} test at gamma=0 (3C), and L2 lambda sweep (3D)."},
            {"Sheet": "SuppFig4_MultiModel_NLI_Sweep", "Description": "Supplementary Figure 4A-C: 5-LLM T2 flip spectrum & 95% CIs (4A), 5-cohort grouped selective calibration benchmark (4B), and DeBERTa-v3 NLI tau sweep + 50-pair expert audit (4C)."},
        ]).to_excel(writer, sheet_name="README_Overview", index=False)

        # 2. Fig 1A-D
        df_1ab = pd.DataFrame([{"Block": blk, **bd} for blk, bd in a6["A6_token_call_ledger"].items()])
        z_map = ex["fig1c_standardized_z"]
        df_1c = pd.DataFrame([
            {"Member_ID": hk, **z_map[hk]} for hk in ["H1", "H2", "H3", "H4", "H5", "H6"]
        ])
        df_1d = pd.DataFrame([
            {"Radar_Axis": "Dim 1: Verified Citation Yield (%)", "Standard_Unrectified": 42.62, "STAR_Audit_Rectified": 100.00},
            {"Radar_Axis": "Dim 2: Pathway Axis Concordance (%)", "Standard_Unrectified": 20.50, "STAR_Audit_Rectified": 48.33},
            {"Radar_Axis": "Dim 3: T2 Order Consistency (%)", "Standard_Unrectified": 56.96, "STAR_Audit_Rectified": 100.00},
            {"Radar_Axis": "Dim 4: T1 Uniform-Normalized Bucket-3 Parity (%)", "Standard_Unrectified": 40.00, "STAR_Audit_Rectified": 72.50},
            {"Radar_Axis": "Dim 5: Judge NLI Coherence (%)", "Standard_Unrectified": 74.58, "STAR_Audit_Rectified": 90.00},
            {"Radar_Axis": "Dim 6: Calibration Accuracy 100-100*ECE (%)", "Standard_Unrectified": 77.79, "STAR_Audit_Rectified": 97.26},
        ])
        write_blocks(writer, "Fig1_Arch_and_Scorecard", [
            ("Fig 1A-B: Four-Block Call & Reasoning Token Ledger", df_1ab),
            ("Fig 1C: Standardized Test Effect Sizes (|z| +/- 95% CI) & BH-FDR q", df_1c),
            ("Fig 1D: Six-Dimension Normalized Trustworthiness Radar", df_1d),
        ])

        # 3. Fig 2A-E
        df_2ab = pd.DataFrame([{"Run_ID": rid, **rv} for rid, rv in s1["parent_runs_dimension1"]["by_run"].items()])
        expb_slots = json.load(open(os.path.join(HERE, "step1_expB_slots_scored.json"), encoding="utf-8"))
        doms_14 = sorted({r["domain_id"] for r in expb_slots})
        dom_rows = []
        for did in doms_14:
            dname = next(r.get("domain_name", did) for r in expb_slots if r["domain_id"] == did)
            row_d = {"Domain_ID": did, "Domain_Name": dname}
            for arm_k in ["as_discovered", "abstain_probe", "gated"]:
                sub = [r for r in expb_slots if r["domain_id"] == did and r["arm"] == arm_k]
                row_d[f"{arm_k}_Ungrounded_Pct"] = round(100.0 * sum(1 for r in sub if r["ungrounded"]) / max(1, len(sub)), 2)
                row_d[f"{arm_k}_Abstain_Pct"] = round(100.0 * sum(1 for r in sub if r.get("abstained")) / max(1, len(sub)), 2)
            dom_rows.append(row_d)
        df_2cd_dom = pd.DataFrame(dom_rows)
        df_2e_mod = pd.DataFrame([
            {"Model_Cohort": mod_k, "Arm": arm_k, **md}
            for mod_k, arms_d in a2["honest_split_by_model_and_arm"].items()
            for arm_k, md in arms_d.items()
        ])
        df_2e_cl = pd.DataFrame([{"Model": k, **v} for k, v in a2["closed_loop_5model_matched84"].items()])
        write_blocks(writer, "Fig2_Citation_Gating", [
            ("Fig 2A-B: Parent 12-Run Step-6 Protocol Citation Verification", df_2ab),
            ("Fig 2C-D: 14-Domain x 3-Arm Randomized Trial & GLM Phase Plane", df_2cd_dom),
            ("Fig 2E (Part 1): Five-LLM Parametric Arms", df_2e_mod),
            ("Fig 2E (Part 2): Five-LLM Closed-Loop Module 3a+3b 100% Yield", df_2e_cl),
        ])

        # 4. Fig 3A-F
        df_3ab = pd.DataFrame([
            {"Disease": "dAMD", "Granularity": "Lead Target Gene (HGNC)", "Within_Arm_Jaccard": 0.0926, "Cross_Arm_Jaccard": 0.0370},
            {"Disease": "dAMD", "Granularity": "All Dossier Target Genes", "Within_Arm_Jaccard": 0.1563, "Cross_Arm_Jaccard": 0.1502},
            {"Disease": "dAMD", "Granularity": "Canonical Pathway Axis", "Within_Arm_Jaccard": 0.3944, "Cross_Arm_Jaccard": 0.4725},
            {"Disease": "ALS", "Granularity": "Lead Target Gene (HGNC)", "Within_Arm_Jaccard": 0.2037, "Cross_Arm_Jaccard": 0.0741},
            {"Disease": "ALS", "Granularity": "All Dossier Target Genes", "Within_Arm_Jaccard": 0.1721, "Cross_Arm_Jaccard": 0.0897},
            {"Disease": "ALS", "Granularity": "Canonical Pathway Axis", "Within_Arm_Jaccard": 0.5722, "Cross_Arm_Jaccard": 0.4005},
        ])
        df_3c = pd.DataFrame([{"Vendor_Arm_Dose": ck, **cd} for ck, cd in s3["expC_v4"]["descriptive_by_cell"].items()])
        df_3c_4a = pd.DataFrame([
            {"Curve": "DeepSeek-V4 + Module 4a (External HGNC)", "Dose_Pct": int(d), **v}
            for d, v in ex["fig3c_exact"]["deepseek_module4a_del_topIC"].items()
        ])
        ec = ex["fig3d_cot_depth_ecdf"]
        df_3d_ecdf = pd.DataFrame([
            {"Group": "Baseline Hits (Hit@10=1)", "N": ec["hits_n"], "Median_First_Gene_CoT_Depth_Pct": ec["hits_median_pct"]},
            {"Group": "Self-Pruned Completed Misses", "N": ec["self_pruned_n"], "Median_First_Gene_CoT_Depth_Pct": ec["self_pruned_median_pct"]},
            {"Group": "32k Ceiling-Truncated Ghost Misses", "N": ec["ceiling_ghost_n"], "Median_First_Gene_CoT_Depth_Pct": ec["ceiling_ghost_median_pct"]},
        ])
        fp = ex["fig3e_lit_footprint"]
        df_3e_fp = pd.DataFrame([
            {"Cohort": ck, "High_Footprint_Hits": v["high"]["k"], "High_Footprint_N": v["high"]["n"], "High_Recall_Pct": v["high"]["pct"], "High_SE": v["high"]["se"],
             "Low_Footprint_Hits": v["low"]["k"], "Low_Footprint_N": v["low"]["n"], "Low_Recall_Pct": v["low"]["pct"], "Low_SE": v["low"]["se"], "TwoSided_Fisher_p": v["fisher_two_sided_p"]}
            for ck, v in fp.items()
        ])
        df_3f = pd.DataFrame(ex["fig3d_decoys"])
        write_blocks(writer, "Fig3_Gene_Benchmark", [
            ("Fig 3A-B: Multi-Granularity Within-Arm vs Cross-Arm Top-5 Jaccard", df_3ab),
            ("Fig 3C (Part 1): 120-Disease HPO Canonical 630-Call Cells", df_3c),
            ("Fig 3C (Part 2): Module 4a Rectified Dose-Response Curve", df_3c_4a),
            ("Fig 3D: Pure White-Box 2.1% CoT Depth ECDF Summary", df_3d_ecdf),
            ("Fig 3E: Pretraining PubMed Literature Footprint Stratification", df_3e_fp),
            ("Fig 3F: Top 10 Missed-Call Syndromic Decoy Attractors", df_3f),
        ])

        # 5. Fig 4A-E
        f4ae_rows = []
        for rid, rd in s2["dimension_3_position_bias"]["tournament_II_by_run"].items():
            nli_r = s4["cross_stage_coherence"]["by_run"].get(rid, {})
            f4ae_rows.append({
                "Run_ID": rid,
                **{f"T2_{k}": v for k, v in rd.items() if not isinstance(v, (list, dict))},
                "CrossStage_Dir_Contra_per_1k": nli_r.get("dir_contra_per_1k_pairs"),
                "CrossStage_Bidir_Contra_per_1k": nli_r.get("bidir_contra_per_1k_pairs"),
                "Top5_Propagated_Contradictions": nli_r.get("s13_contra_propagated_to_top5"),
            })
        t1_adj = s2["audit_guided_rectification"]["tournament_I_order_adjusted_btl"]
        df_4b = pd.DataFrame([
            {
                "Run_ID": r,
                "Raw_B1_Pct": t1_adj[r]["raw_top10_decades"][0] * 10.0,
                "Raw_B2_Pct": t1_adj[r]["raw_top10_decades"][1] * 10.0,
                "Raw_B3_Pct": t1_adj[r]["raw_top10_decades"][2] * 10.0,
                "OABTL_B1_Pct": t1_adj[r]["adj_top10_decades"][0] * 10.0,
                "OABTL_B2_Pct": t1_adj[r]["adj_top10_decades"][1] * 10.0,
                "OABTL_B3_Pct": t1_adj[r]["adj_top10_decades"][2] * 10.0,
            }
            for r in sorted(t1_adj.keys())
        ])
        att = ex["fig4c_cot_attention"]
        df_4c_att = pd.DataFrame({
            "Reasoning_Decile": list(range(1, 11)),
            "Tournament_I_SlotA_Share_Pct_n4127": att["t1_deciles_pct"],
            "Tournament_II_SlotA_Share_Pct_n3465": att["t2_deciles_pct"],
        })
        f4d_d = ex["fig4c_exact"]
        df_4d = pd.DataFrame({
            "Tau_Threshold": f4d_d["taus"][::10],
            "Primacy_Flipped_Dir_Pct": f4d_d["biased_dir_pct"][::10],
            "Consistent_Dir_Pct": f4d_d["cons_dir_pct"][::10],
            "Primacy_Flipped_StrictBidir_Pct": f4d_d["biased_bidir_pct"][::10],
            "Consistent_StrictBidir_Pct": f4d_d["cons_bidir_pct"][::10],
        })
        write_blocks(writer, "Fig4_Primacy_and_NLI", [
            ("Fig 4A & 4E: Run-Level Tournament II Flip Rates & Cross-Stage NLI Phase Space", pd.DataFrame(f4ae_rows)),
            ("Fig 4B: Per-Run Tournament I Bucket Survival Shares (Unadjusted vs OA-BTL)", df_4b),
            ("Fig 4C: White-Box CoT Decile-by-Decile Slot-A Attention Trajectory (n=7,592 Traces)", df_4c_att),
            ("Fig 4D: Empirical DeBERTa-v3 NLI Tail Curve (n=480 Pairs)", df_4d),
        ])

        # 6. Fig 5A-D
        boot_12 = s2["dimension_4_stability_bootstrap"]
        df_5a = pd.DataFrame([
            {
                "Run_ID": r,
                "Boot_10k_Mean_Jaccard": boot_12[r]["boot_pairwise_jaccard_mean"],
                "Boot_10k_CI95_Low": boot_12[r]["boot_pairwise_jaccard_95ci"][0],
                "Boot_10k_CI95_High": boot_12[r]["boot_pairwise_jaccard_95ci"][1],
                "Empirical_1k_Violin_Mean": ex["fig5a_boot"][r]["mean"],
            }
            for r in sorted(boot_12.keys())
        ])
        sweep_12 = a6["A9_selective_calibration_tau_ece_sweep"]["0.12"]
        cohort_to_sweep = {
            "Gemini-4-Argon-High_ExpC_n60": "Gemini-4-Argon-High",
            "Gemini-3.8-Flash_ExpC_n60": "Gemini-3.8-Flash",
            "Grok-4.7-High_ExpC_n60": "Grok-4.7-High",
            "Grok-4.7-Fast_ExpC_n60": "Grok-4.7-Fast",
        }
        f5b_rows = []
        for ck, cv in a3["A7_calibration_benchmark"].items():
            row = {"Cohort": ck, "N": cv["n"], "Mean_Confidence_Pct": cv["mean_conf_pct"], "Empirical_Accuracy_Pct": cv["empirical_acc_pct"]}
            for mk, mv in cv["methods"].items():
                row[f"ECE_{mk}"] = mv["ece_primary"]
            if ck in cohort_to_sweep:
                sk = cohort_to_sweep[ck]
                row["ECE_selective_gate"] = sweep_12[sk]["ece_5bin"]
                row["Selective_Gate_Folds_Triggered_tau012"] = sweep_12[sk]["triggered_folds"]
            else:
                row["Selective_Gate_Folds_Triggered_tau012"] = cv["selective_gate_triggered_folds"]
            f5b_rows.append(row)
        df_5cd = pd.DataFrame([
            {"Paradox": "Paradox 1 (T2 Consistent, n=1824)", "Median_CoT_Tokens": 2336.0, "Mean_CoT_Tokens": 2615.3},
            {"Paradox": "Paradox 1 (T2 Slot-A Flipped, n=1336)", "Median_CoT_Tokens": 2410.5, "Mean_CoT_Tokens": 2624.8},
            {"Paradox": "Paradox 2 (Citation Ungated, n=70)", "Median_CoT_Tokens": 11798.5, "Mean_CoT_Tokens": 12036.5},
            {"Paradox": "Paradox 2 (Citation Abstain-Probe, n=70)", "Median_CoT_Tokens": 8862.0, "Mean_CoT_Tokens": 8755.9},
            {"Paradox": "Paradox 2 (Citation Epistemic Gated, n=70)", "Median_CoT_Tokens": 1132.0, "Mean_CoT_Tokens": 1660.5},
            {"Paradox": "Paradox 3 (HPO GLM Hit@10=1, n=110)", "Median_CoT_Tokens": 17071.5, "Mean_CoT_Tokens": 17325.0},
            {"Paradox": "Paradox 3 (HPO GLM Hit@10=0, n=249)", "Median_CoT_Tokens": 28959.0, "Mean_CoT_Tokens": 25884.0},
            {"Paradox": "Paradox 3 (HPO DeepSeek Hit@10=1, n=56)", "Median_CoT_Tokens": 19671.0, "Mean_CoT_Tokens": 20214.0},
            {"Paradox": "Paradox 3 (HPO DeepSeek Hit@10=0, n=215)", "Median_CoT_Tokens": 27398.0, "Mean_CoT_Tokens": 25941.0},
        ])
        write_blocks(writer, "Fig5_Calibration_Paradox", [
            ("Fig 5A: 10,000-Draw Verdict-Table Bootstrap Stability & 4-Cell Paired Null vs Observed", df_5a),
            ("Fig 5B: Out-of-Sample Calibration & Selective Gate (tau_ECE = 0.12)", pd.DataFrame(f5b_rows)),
            ("Fig 5C-D: Test-Time Reasoning Paradoxes 1-3 Per-Call CoT Token Summaries", df_5cd),
        ])

        # 7. Fig 6A-E
        t2_adj = s2["audit_guided_rectification"]["tournament_II_debiased_btl"]
        a1_emp = a1["A1_empirical_by_run"]
        t2_h = ex["fig6a_t2_hessian"]
        df_6a = pd.DataFrame([
            {
                "Run_ID": rid,
                "T1_Gamma_Primacy": a1_emp[rid]["gamma_t1_full_oa"],
                "T1_Gamma_SE": a1_emp[rid]["gamma_t1_full_se"],
                "T2_Gamma_Primacy": t2_adj[rid]["t2_gamma_primacy"],
                "T2_Gamma_SE": t2_h[rid]["se_t2"],
                "Raw_Bucket3_Parity_Pct": min(100.0, 30.0 * t1_adj[rid]["raw_top10_decades"][2]),
                "OABTL_Bucket3_Parity_Pct": min(100.0, 30.0 * t1_adj[rid]["adj_top10_decades"][2]),
            }
            for rid in sorted(t1_adj.keys())
        ])
        df_6b = pd.DataFrame([
            {"Run_ID": r, "Mechanism": m, "Raw_BTL_Rank": rk0, "OABTL_Rank": rk1}
            for r, m, rk0, rk1 in [
                ("dAMD_retrieval_R1", "M23: GAS6/PROS1-MERTK Phagocytosis", 11, 7),
                ("dAMD_retrieval_R2", "M25: TIMP3/MMP9 ECM Turnover", 15, 8),
                ("dAMD_retrieval_R3", "M25: ABCA1/LIPC/CETP Lipid Efflux", 15, 6),
                ("dAMD_retrieval_R3", "M14: CD59 MAC Protection", 11, 5),
                ("dAMD_blind_R1", "M22: MTTP/APOB100 Lipoprotein", 12, 6),
                ("ALS_blind_R1", "M18: C1QA/C3 Complement Neurotoxicity", 13, 10),
                ("ALS_blind_R2", "M26: MMP9/LAMA1 NMJ Denervation", 13, 6),
                ("ALS_blind_R3", "M25: MCT1/SLC16A1 Lactate Shuttle", 11, 7),
                ("ALS_retrieval_R3", "M29: CCS/ATP7A Copper Homeostasis", 15, 10),
            ]
        ])
        b6 = ex["fig6de_bootstrap"]
        df_6cde = pd.DataFrame([
            {"Pipeline_State": "1. Standard Unrectified", "S_norm_Pct": 54.34, "S_norm_Boot_SE": b6["s_norm_se"][0], "S_raw_Pct": 47.67, "S_raw_Boot_SE": b6["s_raw_se"][0], "Median_Citation_CoT_Tokens": 11798.5},
            {"Pipeline_State": "2. + Abstention Probe Safety", "S_norm_Pct": 63.27, "S_norm_Boot_SE": b6["s_norm_se"][1], "S_raw_Pct": 56.60, "S_raw_Boot_SE": b6["s_raw_se"][1], "Median_Citation_CoT_Tokens": 8862.0},
            {"Pipeline_State": "3. + OA-BTL & Selective Platt", "S_norm_Pct": 78.09, "S_norm_Boot_SE": b6["s_norm_se"][2], "S_raw_Pct": 66.02, "S_raw_Boot_SE": b6["s_raw_se"][2], "Median_Citation_CoT_Tokens": 11798.5},
            {"Pipeline_State": "4. Full Closed-Loop STAR-Audit", "S_norm_Pct": 92.44, "S_norm_Boot_SE": b6["s_norm_se"][3], "S_raw_Pct": 80.36, "S_raw_Boot_SE": b6["s_raw_se"][3], "Median_Citation_CoT_Tokens": 1132.0},
        ])
        write_blocks(writer, "Fig6_Rectification_Frontier", [
            ("Fig 6A & 6C: Run-Level T1/T2 Primacy Intercepts, Hessian SEs & Normalized Bucket-3 Parity", df_6a),
            ("Fig 6B: Nine Orthogonal Gold-Standard Pathways Rescued into Top 10", df_6b),
            ("Fig 6D-E: Stepwise Composite Score Progression, Bootstrap SEs & Compute Pareto Frontier", df_6cde),
        ])

        # 8-11. Supplementary Figs 1-4
        df_sf1a = pd.DataFrame([{"Model": k, **v} for k, v in a2["closed_loop_5model_matched84"].items()])
        df_sf1b = pd.DataFrame([
            {"Metric_Set": "Tier2_v1_PreReg", **a5_1["tier2_100slot_expert_audit"]["tier2_v1_prereg_blunt_metrics"]},
            {"Metric_Set": "Tier2_v2_EntityAnchor", **a5_1["tier2_100slot_expert_audit"]["tier2_v2_entity_anchored_metrics"]},
        ])
        df_sf1c = pd.DataFrame([
            {"Density_Tier": tk, **ex["sf1c_exact"][tk], "ClosedLoop_Verified_Yield_Pct": 100.0, "ClosedLoop_Ungrounded_Pct": 0.0}
            for tk in ["high", "medium", "low"]
        ])
        write_blocks(writer, "SuppFig1_Entrez_ExpertAudit", [
            ("Supp Fig 1A: Five-LLM Grouped Safety & Closed-Loop Entrez Handoff Yield", df_sf1a),
            ("Supp Fig 1B: 100-Slot Blinded Domain-Expert Verifier Calibration", df_sf1b),
            ("Supp Fig 1C: GLM-5.3 Literature-Density Strata & Analytical Binomial SEs", df_sf1c),
        ])

        df_sf2a = pd.DataFrame([{"Vendor": vk, **vv} for vk, vv in a3["A3_strobe_call_accounting"]["partition_by_vendor"].items()])
        df_sf2b = pd.DataFrame([{"Cell": ck, **{k: v for k, v in cv.items() if not isinstance(v, list)}} for ck, cv in a3["A3_term_count_starvation_audit"]["by_arm_and_dose"].items()])
        df_sf2c = pd.DataFrame([{"Ablation_Variant": mk, "Vendor": vk, **vv} for mk, mv in a3["A3_cot_srad_5way_ablation"].items() for vk, vv in mv.items()])
        df_sf2d = pd.DataFrame(a3["A3_cot_srad_2d_sensitivity_grid"])
        write_blocks(writer, "SuppFig2_ExpC_Ablation_Grid", [
            ("Supp Fig 2A: STROBE 630-Call Intention-to-Diagnose Outcome Partition", df_sf2a),
            ("Supp Fig 2B: HPO Term-Count Starvation Summary by Arm & Dose", df_sf2b),
            ("Supp Fig 2C: Five-Way External HGNC CoT-SRAD Component Ablation", df_sf2c),
            ("Supp Fig 2D: Two-Dimensional Hyperparameter Sensitivity Grid", df_sf2d),
        ])

        emp_b = a1["A1_empirical_within_bucket_primacy"]
        df_sf3a = pd.DataFrame([{"Stratum": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in emp_b.items()])
        df_sf3b = pd.DataFrame(a1["A1_monte_carlo_parameter_recovery"]["scenario1_null_and_scenario2_sweep"])
        df_sf3c = pd.DataFrame(a1["A1_monte_carlo_parameter_recovery"]["scenario3_confounded_bucket_merit"])
        df_sf3d = pd.DataFrame(a1["A4_lambda_sensitivity_sweep"])
        write_blocks(writer, "SuppFig3_OABTL_Validation", [
            ("Supp Fig 3A: Empirical Intra-Bucket vs Between-Bucket Slot-A Win Rates", df_sf3a),
            ("Supp Fig 3B: 400-Run Synthetic Monte Carlo Primacy Recovery (gamma_true in 0..2.0)", df_sf3b),
            ("Supp Fig 3C: Confounded-Null Identifiability Test (gamma_true=0, Delta_{B1-B3} in 0..1.5)", df_sf3c),
            ("Supp Fig 3D: Four-Order Ridge Regularization Hyperparameter Sweep", df_sf3d),
        ])

        df_sf4a = pd.DataFrame([
            {"Model": "Grok-4.7-Fast", "Evaluated_Pairs": 90, "Flipped_Pairs": 8, "Bidirectional_Flip_Rate_Pct": 8.89},
            {"Model": "Gemini-4-Argon-High", "Evaluated_Pairs": 90, "Flipped_Pairs": 10, "Bidirectional_Flip_Rate_Pct": 11.11},
            {"Model": "Grok-4.7-High", "Evaluated_Pairs": 90, "Flipped_Pairs": 12, "Bidirectional_Flip_Rate_Pct": 13.33},
            {"Model": "Gemini-3.8-Flash", "Evaluated_Pairs": 90, "Flipped_Pairs": 24, "Bidirectional_Flip_Rate_Pct": 26.67},
            {"Model": "GLM-5.3 Discovery T2", "Evaluated_Pairs": 1601, "Flipped_Pairs": 689, "Bidirectional_Flip_Rate_Pct": 43.04},
        ])
        df_sf4b = pd.DataFrame(f5b_rows)
        df_sf4c = pd.DataFrame(a6["A9_deberta_nli_tau_sweep"])
        df_sf4_exp = pd.DataFrame([a5_2["tournament_II_judge_nli_validation_n50"]])
        write_blocks(writer, "SuppFig4_MultiModel_NLI_Sweep", [
            ("Supp Fig 4A: Five-LLM Cross-Ecosystem Tournament II Flip Spectrum & Counts", df_sf4a),
            ("Supp Fig 4B: Five-Cohort Grouped Calibration & Selective Gate (tau_ECE = 0.12)", df_sf4b),
            ("Supp Fig 4C: DeBERTa-v3 NLI Threshold Sweep (tau in 0.50..0.95)", df_sf4c),
            ("Supp Fig 4C (Expert Audit): 50-Pair Blinded Judge NLI Validation", df_sf4_exp),
        ])

    print("Saved Canonical Source Data workbook ->", OUT_XLSX)


if __name__ == "__main__":
    main()
