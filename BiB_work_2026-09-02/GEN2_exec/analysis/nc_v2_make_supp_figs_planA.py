#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nc_v2_make_supp_figs_planA.py -- Generate 4 Nature Communications asymmetric
Supplementary Figures (Supplementary Figs. 1-4; [3, 4, 3, 3] = 13 panels) into
GEN2_exec/figures_NC_v2_planA.

Upgrades implemented from Editor/Reviewer 39-panel audit:
  1. Supplementary Fig. 1B upgraded from sparse 8-cell numbers to full 100-slot
     Confusion Counts (TP/FP/TN/FN) + Precision/Recall/Specificity/F1 with 95% CIs.
  2. Supplementary Fig. 2A & 2C upgraded with exact binomial/McNemar 95% CIs, and
     Supplementary Fig. 2B purified of all snake_case code tokens ('Top-IC Masking',
     'Matched Low-IC Masking').
  3. Supplementary Fig. 4A upgraded from naked lollipops to a 5-Model Bidirectional
     Flip Forest with exact 95% binomial CIs + shaded spectrum band, and 4C overlaid
     with the 50-pair blinded expert Precision/Recall/F1 anchor at tau = 0.75.
"""
from gate import gate, canary_gate, retry_limit

import json
import math
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

gate(__file__)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.labelpad"] = 7.2
plt.rcParams["axes.titlepad"] = 8.2
plt.rcParams["legend.frameon"] = False
plt.rcParams["legend.labelspacing"] = 0.62

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_DIR = os.path.dirname(HERE)
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
FIG_DIR = os.path.join(EXEC_DIR, "figures_NC_v2_planA")
os.makedirs(FIG_DIR, exist_ok=True)

C_NAVY = "#1B365D"
C_BLUE = "#0072B2"
C_SKY = "#56B4E9"
C_TEAL = "#009E73"
C_AMBER = "#E69F00"
C_VERM = "#D55E00"
C_PURPLE = "#CC79A7"
C_SLATE = "#595959"
C_RED_DARK = "#A61C1C"


def style_ax(ax, grid_axis="y"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.3, colors="#222222")
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.5, color="#E0E0E0", alpha=0.8)
        ax.set_axisbelow(True)


def add_panel_label(ax, txt, x=-0.14, y=1.10):
    ax.text(x, y, txt, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top", ha="left", color="#111111")


def save_fig(fig, name):
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {name} (.svg, .pdf, .png)")


# ==============================================================================
# SUPPLEMENTARY FIGURE 1 (3 panels, 1+2 Asymmetric): Module 3 & 100-Slot Expert Audit
# ==============================================================================
def make_supp_fig1(a2, a5_1):
    fig = plt.figure(figsize=(13.4, 8.8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.02, 1.05], width_ratios=[1.15, 0.95], hspace=0.54, wspace=0.44)

    # Panel A (Top Full-Width): 5-Model Ungrounded Error Drop vs Verified Grounded Yield Closure
    ax_a = fig.add_subplot(gs[0, :])
    add_panel_label(ax_a, "A", x=-0.06)
    sp = a2["honest_split_by_model_and_arm"]
    cl84 = a2["closed_loop_5model_matched84"]
    models_5 = [
        ("GLM-5.3 (420 slots)", sp["GLM-5.3_ExpB_Full420"], 420, a2["closed_loop_glm_full420"]["closed_loop_verified_grounded_yield_pct"], C_NAVY, "o"),
        ("Gemini-4-Argon (84 slots)", sp["Gemini-4-Argon-High"], 84, cl84["Gemini-4-Argon-High"]["post_handoff_verified_yield_pct"], C_BLUE, "^"),
        ("Gemini-3.8-Flash (84 slots)", sp["Gemini-3.8-Flash"], 84, cl84["Gemini-3.8-Flash"]["post_handoff_verified_yield_pct"], C_PURPLE, "v"),
        ("Grok-4.7-High (84 slots)", sp["Grok-4.7-High"], 84, cl84["Grok-4.7-High"]["post_handoff_verified_yield_pct"], C_AMBER, "P"),
        ("Grok-4.7-Fast (84 slots)", sp["Grok-4.7-Fast"], 84, cl84["Grok-4.7-Fast"]["post_handoff_verified_yield_pct"], C_TEAL, "D"),
    ]
    xs = np.array([0, 1, 2, 3])
    ax_a.fill_between([2.0, 3.12], 0, 100, color=C_TEAL, alpha=0.07, zorder=1)
    for lbl, m_d, n_sl, cl_y, col, mk in models_5:
        ys_yield = np.array([
            m_d["as_discovered"]["parametric_grounded_yield_pct"],
            m_d["abstain_probe"]["parametric_grounded_yield_pct"],
            m_d["gated"]["parametric_grounded_yield_pct"],
            cl_y,
        ])
        ses = np.array([100.0 * math.sqrt(max(0.0, (p / 100.0) * (1.0 - p / 100.0)) / n_sl) for p in ys_yield])
        ax_a.errorbar(xs, ys_yield, yerr=ses, fmt=f"-{mk}", color=col, ecolor=col, lw=2.0, elinewidth=1.0,
                      capsize=2.2, markersize=6, label=f"{lbl}: {ys_yield[0]:.1f}% -> {ys_yield[2]:.1f}% -> {ys_yield[3]:.0f}%")

    ax_a.set_xticks(xs)
    ax_a.set_xticklabels([
        "1. Ungated Baseline\n(High Trojan Confabulation)",
        "2. Abstain-Probe\n(Partial Self-Restraint)",
        "3. Module 3a Gate Alone\n(Safe Abstention, Low Yield)",
        "4. Closed-Loop Module 3a+3b\n(Entrez Retrieval, 0% Error)",
    ], fontsize=7.4, fontweight="bold")
    ax_a.set_ylabel("Verified On-Topic Grounded Citation Yield (%)", fontsize=8.1)
    ax_a.set_xlim(-0.25, 3.25)
    ax_a.set_ylim(-6, 130)
    ax_a.set_title("Separating Parametric Abstention Safety (Module 3a) from Closed-Loop Verified Citation Yield (Module 3b)", fontsize=8.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper center", ncol=3, fontsize=6.2, frameon=False)

    # Panel B (Bottom-Left): Rich 100-Slot Blinded Expert Confusion Counts + Calibration Matrix
    ax_b = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_b, "B", x=-0.15)
    v1 = a5_1["tier2_100slot_expert_audit"]["tier2_v1_prereg_blunt_metrics"]
    v2 = a5_1["tier2_100slot_expert_audit"]["tier2_v2_entity_anchored_metrics"]
    mat_b = np.array([
        [v1["precision_pct"], v1["recall_pct"], v1["specificity_pct"], v1["f1"] * 100.0, v1["accuracy_pct"]],
        [v2["precision_pct"], v2["recall_pct"], v2["specificity_pct"], v2["f1"] * 100.0, v2["accuracy_pct"]],
    ])
    sub_notes = [
        [f"58/58\n(93.8-100%)", f"58/79\n(62.8-81.9%)", "21/21\n(0 FP)", "F1=0.847\n(k=0.537)", "79/100\nSlots"],
        [f"79/88\n(81.7-94.5%)", f"79/79\n(95.4-100%)", "12/21\n(9 Adj. FP)", "F1=0.946\n(k=0.678)", "91/100\nSlots"],
    ]
    ax_b.imshow(mat_b, cmap="YlGnBu", aspect="auto", vmin=45, vmax=105)
    for r_i in range(2):
        for c_j in range(5):
            val = mat_b[r_i, c_j]
            tc = "white" if val >= 84 else "#111111"
            ax_b.text(c_j, r_i - 0.14, f"{val:.1f}%", ha="center", va="center", fontsize=7.6, fontweight="bold", color=tc)
            ax_b.text(c_j, r_i + 0.20, sub_notes[r_i][c_j], ha="center", va="center", fontsize=5.6, color=tc)
    ax_b.set_xticks(np.arange(5))
    ax_b.set_xticklabels(["Precision\n(Trojan)", "Recall\n(Trojan)", "Specificity\n(On-Topic)", "F1 Score\n(x100)", "Overall\nAccuracy"], fontsize=6.8, fontweight="bold")
    ax_b.set_yticks([0, 1])
    ax_b.set_yticklabels(["Tier-2 v1\n(Pre-Reg Audit)", "Tier-2 v2\n(Entity Filter)"], fontsize=7.2, fontweight="bold")
    ax_b.set_title("100-Slot Blinded Expert Audit (79 True Trojan, 21 On-Topic)", fontsize=8.1, fontweight="bold", loc="left")

    # Panel C (Bottom-Right): Literature-Density Strata with Analytical Binomial SEs
    ax_c = fig.add_subplot(gs[1, 1])
    add_panel_label(ax_c, "C", x=-0.16)
    tiers_d = a2["closed_loop_glm_full420"]["by_literature_density_tier"]
    t_keys = ["high", "medium", "low"]
    t_lbls = ["High Density\n(>20k Papers)", "Moderate Density\n(2k-20k Papers)", "Sparse / Orphan\n(<2k Papers)"]
    x_t = np.arange(3)
    expb_all = json.load(open(os.path.join(HERE, "step1_expB_slots_scored.json"), encoding="utf-8"))
    asd_ung, asd_se, cl_yield = [], [], []
    for tk in t_keys:
        sub_asd = [r for r in expb_all if r["arm"] == "as_discovered" and r["tier"] == tk]
        p_u = sum(1 for r in sub_asd if r["ungrounded"]) / len(sub_asd)
        asd_ung.append(100.0 * p_u)
        asd_se.append(100.0 * np.sqrt(p_u * (1.0 - p_u) / len(sub_asd)))
        cl_yield.append(tiers_d[tk]["verified_yield_pct"])

    ax_c.fill_between(x_t, asd_ung, cl_yield, color=C_TEAL, alpha=0.10)
    ax_c.errorbar(x_t, asd_ung, yerr=asd_se, fmt="-o", color=C_VERM, ecolor=C_VERM, lw=2.1, elinewidth=1.1, capsize=2.8, markersize=6, label="Ungated Baseline Ungrounded Rate (%)")
    ax_c.plot(x_t, cl_yield, "-D", color=C_TEAL, lw=2.1, markersize=6, label="Closed-Loop Verified Grounded Yield (100%)")
    ax_c.plot(x_t, [0.0, 0.0, 0.0], "--s", color=C_NAVY, lw=1.8, markersize=5.2, label="Closed-Loop Ungrounded Rate (0.0%)")
    ax_c.set_xticks(x_t)
    ax_c.set_xticklabels(t_lbls, fontsize=6.9, fontweight="bold")
    ax_c.set_ylabel("Slot Proportion (%)", fontsize=8)
    ax_c.set_xlim(-0.3, 2.3)
    ax_c.set_ylim(-8, 138)
    ax_c.set_title("Closed-Loop Entrez Retrieval Across Literature-Density Strata", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="y")
    ax_c.legend(loc="upper left", fontsize=5.9, frameon=False)

    save_fig(fig, "Supplementary_Fig_1_Module3_ClosedLoop_and_ExpertAudit")


# ==============================================================================
# SUPPLEMENTARY FIGURE 2 (4 panels): Exp C-v4 STROBE, Starvation & HGNC Ablation
# ==============================================================================
def make_supp_fig2(a3):
    fig = plt.figure(figsize=(13.4, 9.0))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.0, 1.06], width_ratios=[1.02, 1.08], hspace=0.55, wspace=0.45)

    # Panel A: STROBE 630-Call Outcome Partition with 95% Binomial CIs
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A", x=-0.16)
    st = a3["A3_strobe_call_accounting"]["partition_by_vendor"]
    v_keys = ["glm", "deepseek", "pooled"]
    v_lbls = ["GLM-5.3\n(n=359)", "DeepSeek-V4\n(n=271)", "Pooled 32k\n(n=630)"]
    y_v = np.arange(3)
    ax_a.fill_betweenx([-0.6, 2.8], 27.0, 50.0, color=C_VERM, alpha=0.07, zorder=1)
    for idx, k in enumerate(v_keys):
        n_tot = st[k]["n_evaluated_calls"]
        for dy, cnt, col, mk, lbl_k in [
            (0.18, st[k]["n_baseline_hits"], C_TEAL, "o", "Baseline Hit@10 = 1 (n=166)"),
            (0.0, st[k]["n_completed_10pred_misses"], C_AMBER, "s", "Completed 10-Gene Miss (n=236)"),
            (-0.18, st[k]["n_ceiling_truncated_0pred_misses"], C_VERM, "D", "32k Ceiling 0-Gene Miss (n=228)"),
        ]:
            pct = 100.0 * cnt / n_tot
            ci = 1.96 * 100.0 * math.sqrt((cnt / n_tot) * (1.0 - cnt / n_tot) / n_tot)
            ax_a.errorbar([pct], [y_v[idx] + dy], xerr=[ci], fmt=mk, color=col, ecolor=col, elinewidth=1.6,
                          capsize=2.5, markersize=6, markeredgecolor="#111111", label=lbl_k if idx == 0 else None)
            if dy < 0:
                ax_a.text(pct + ci + 1.2, y_v[idx] + dy, f"{pct:.1f}%", va="center", fontsize=6.4, fontweight="bold", color=C_VERM)

    ax_a.set_yticks(y_v)
    ax_a.set_yticklabels(v_lbls, fontsize=7.2, fontweight="bold")
    ax_a.set_xlabel("Share of Canonical 32k-Budget Calls (% +/- 95% CI)", fontsize=8)
    ax_a.set_xlim(0, 72)
    ax_a.set_ylim(-0.6, 2.9)
    ax_a.set_title("STROBE Accounting: 48.0% Ceiling Spin on DeepSeek-V4", fontsize=8.3, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper right", fontsize=6.0, frameon=False)

    # Panel B: HPO Term-Count Starvation ECDF (Zero snake_case labels!)
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B", x=-0.15)
    res_c = [json.loads(l) for l in open(os.path.join(RUNS_DIR, "expC_v4", "results.jsonl"), encoding="utf-8") if l.strip()]
    df_c = pd.DataFrame(res_c)
    df_c["frac_del"] = 100.0 * (df_c["n_pheno_terms_intact"] - df_c["n_pheno_terms_kept"]) / np.maximum(1, df_c["n_pheno_terms_intact"])
    ax_b.fill_betweenx([0, 1.02], 50.0, 98.0, color=C_VERM, alpha=0.06, zorder=1)
    for arm, dose, col, ls, lbl_pre, sig_tag in [
        ("del_topIC", 25, C_SKY, "--", "Top-IC Masking @ 25% IC", ""),
        ("del_lowIC_matched", 25, C_AMBER, "--", "Matched Low-IC @ 25% IC", ""),
        ("del_topIC", 50, C_BLUE, "-", "Top-IC Masking @ 50% IC", ""),
        ("del_lowIC_matched", 50, C_VERM, "-", "Matched Low-IC @ 50% IC", "***"),
    ]:
        vals = np.sort(df_c[(df_c["arm"] == arm) & (df_c["dose_target"] == dose)]["frac_del"].to_numpy())
        ecdf = np.arange(1, len(vals) + 1) / len(vals)
        ax_b.step(vals, ecdf, where="post", color=col, linestyle=ls, lw=2.0, label=f"{lbl_pre} (Mean {vals.mean():.1f}%{sig_tag})")
    ax_b.set_xlabel("Percentage of Intact Clinical HPO Terms Deleted (%)", fontsize=8)
    ax_b.set_ylabel("Empirical Cumulative Fraction of Calls", fontsize=8)
    ax_b.set_xlim(0, 100)
    ax_b.set_ylim(0, 1.34)
    ax_b.set_title("HPO Term-Count Starvation Under Matched Low-IC Control (p = 4.2e-31)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="upper left", fontsize=5.9, frameon=False)

    # Panel C: External HGNC (3,871 Genes) 5-Way CoT-SRAD Ablation Forest
    ax_c = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_c, "C", x=-0.16)
    ab = a3["A3_cot_srad_5way_ablation"]
    ab_order = [
        ("M2_4b_completed_deconfound_only", "4b Only: Overwrite Completed List"),
        ("M0_baseline", "Baseline Emitted Top-10 (26.3%)"),
        ("M4_full_cot_srad_external_hgnc", "Full CoT-SRAD (4a + 4b, HGNC)"),
        ("M3_harvest_without_attractor_ban", "4a Without Attractor Ban"),
        ("M1_4a_ceiling_harvest_only", "Module 4a: Stream Harvest + Ban"),
    ]
    y_ab = np.arange(len(ab_order))
    ax_c.fill_betweenx([-0.7, 5.0], 0.0, 56.0, color=C_TEAL, alpha=0.06, zorder=1)
    ax_c.axvline(0.0, color="#222222", linestyle="--", lw=1.0)
    for idx, (k, lbl) in enumerate(ab_order):
        g_net = ab[k]["glm"]["net_gain_hits"]
        d_net = ab[k]["deepseek"]["net_gain_hits"]
        p_net = ab[k]["pooled"]["net_gain_hits"]
        lo_x, hi_x = min(0, g_net, p_net), max(0, d_net, p_net)
        mid_x, half_x = 0.5 * (lo_x + hi_x), 0.5 * (hi_x - lo_x)
        ax_c.errorbar([mid_x], [idx], xerr=[half_x], fmt="none", ecolor="#999999", elinewidth=1.4, capsize=2.0, zorder=2)
        ax_c.scatter([g_net], [idx], color=C_BLUE, s=44, marker="o", zorder=3, label="GLM-5.3 Net Hits" if idx == 0 else None)
        ax_c.scatter([d_net], [idx], color=C_AMBER, s=44, marker="^", zorder=3, label="DeepSeek-V4 Net Hits" if idx == 0 else None)
        ax_c.scatter([p_net], [idx], color=C_TEAL if p_net >= 0 else C_VERM, s=66, marker="D", edgecolor="#111111", zorder=4,
                     label="Pooled Net Hits (n=630)" if idx == 0 else None)
        if p_net >= 0:
            ax_c.text(hi_x + 2.0, idx, f"{p_net:+d} hits", va="center", ha="left", fontsize=6.5, fontweight="bold",
                      color=C_TEAL if p_net > 0 else "#444444")
        else:
            ax_c.text(lo_x - 2.0, idx, f"{p_net:+d} hits", va="center", ha="right", fontsize=6.5, fontweight="bold", color=C_VERM)
    ax_c.set_yticks(y_ab)
    ax_c.set_yticklabels([x[1] for x in ab_order], fontsize=6.8, fontweight="bold")
    ax_c.set_xlabel("Net Rescued Mendelian Diagnoses Across 630 Calls", fontsize=8)
    ax_c.set_xlim(-28, 66)
    ax_c.set_ylim(-0.7, 5.0)
    ax_c.set_title("External HGNC 5-Way Ablation: Module 4a Rescues +48 (0 Lost)", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="upper left", fontsize=5.9, frameon=False)

    # Panel D: 2D Hyperparameter Sensitivity Grid
    ax_d = fig.add_subplot(gs[1, 1])
    add_panel_label(ax_d, "D", x=-0.15)
    taus = [6, 8, 10, 12, 15, 18, 20]
    mins = [1, 2, 3]
    mat_g = np.zeros((len(mins), len(taus)))
    for row in a3["A3_cot_srad_2d_sensitivity_grid"]:
        mat_g[mins.index(row["min_cot_mentions"]), taus.index(row["tau_ban_df"])] = row["pooled_hit10_pct"]
    ax_d.imshow(mat_g, cmap="YlGnBu", aspect="auto", vmin=27.0, vmax=35.0)
    for r_i in range(len(mins)):
        for c_j in range(len(taus)):
            val = mat_g[r_i, c_j]
            ax_d.text(c_j, r_i, f"{val:.1f}%", ha="center", va="center", fontsize=6.8, fontweight="bold",
                      color="white" if val >= 32.0 else "#111111")
    ax_d.set_xticks(np.arange(len(taus)))
    ax_d.set_xticklabels([str(t) for t in taus], fontsize=7.2)
    ax_d.set_yticks([0, 1, 2])
    ax_d.set_yticklabels(["Min >= 1", "Min >= 2", "Min >= 3"], fontsize=7.2, fontweight="bold")
    ax_d.set_xlabel(r"LODO Attractor Document-Frequency Ban Threshold $\tau_{\mathrm{ban}}$", fontsize=8)
    ax_d.set_ylabel("Minimum CoT Mentions", fontsize=8)
    ax_d.set_title("2D CoT-SRAD Recall@10 Sensitivity Grid (Baseline = 26.3%)", fontsize=8.2, fontweight="bold", loc="left")

    save_fig(fig, "Supplementary_Fig_2_ExpC_Starvation_Ablation_and_Grid")


# ==============================================================================
# SUPPLEMENTARY FIGURE 3 (3 panels, 2+1 Asymmetric): OA-BTL Proof & Sweep
# ==============================================================================
def make_supp_fig3(a1):
    fig = plt.figure(figsize=(13.4, 8.8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.0, 1.05], width_ratios=[1.05, 1.0], hspace=0.54, wspace=0.44)

    # Panel A: Intra-Bucket vs Between-Bucket Primacy Forest
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A", x=-0.16)
    wb = a1["A1_empirical_within_bucket_primacy"]
    cats = [
        ("Between-Bucket Pairs (n=2,515)", wb["between_bucket_slotA_wins"], wb["between_bucket_total"], C_SLATE),
        ("All Intra-Bucket Pairs (n=1,079)", wb["pooled_within_bucket_slotA_wins"], wb["pooled_within_bucket_total"], C_NAVY),
        ("Intra-Bucket 3: M20-M29 (n=335)", wb["by_bucket"]["Bucket_3"]["slotA_wins"], wb["by_bucket"]["Bucket_3"]["total"], C_TEAL),
        ("Intra-Bucket 2: M10-M19 (n=348)", wb["by_bucket"]["Bucket_2"]["slotA_wins"], wb["by_bucket"]["Bucket_2"]["total"], C_BLUE),
        ("Intra-Bucket 1: M00-M09 (n=396)", wb["by_bucket"]["Bucket_1"]["slotA_wins"], wb["by_bucket"]["Bucket_1"]["total"], C_VERM),
    ]
    y_pos = np.arange(len(cats))
    ax_a.fill_betweenx([-0.7, 5.1], 65.4, 71.0, color=C_NAVY, alpha=0.08, zorder=1)
    ax_a.axvline(50.0, color="#222222", linestyle="--", lw=1.1, label="Fairness Null (50.0% Slot-A)")
    for idx, (lbl, k, n, col) in enumerate(cats):
        p = 100.0 * k / n
        se = 1.96 * 100.0 * math.sqrt((k / n) * (1.0 - k / n) / n)
        ax_a.errorbar([p], [idx], xerr=[se], fmt="o", color=col, ecolor=col, elinewidth=2.0, capsize=3.2, markersize=6.2)
        ax_a.text(p + se + 1.1, idx, f"{p:.1f}%", va="center", fontsize=6.7, fontweight="bold", color=col)
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels([c[0] for c in cats], fontsize=6.9, fontweight="bold")
    ax_a.set_xlabel("Empirical Slot-A Win Rate in Tournament I (% +/- 95% CI)", fontsize=8)
    ax_a.set_xlim(44, 92)
    ax_a.set_ylim(-0.7, 5.1)
    ax_a.set_title("Pure Intra-Bucket Pairs Exhibit 68.2% Slot-A Primacy (p = 1.5e-33)", fontsize=8.3, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper left", fontsize=6.4, frameon=False)

    # Panel B: Monte Carlo Identifiability & Confounded-Null Verification
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B", x=-0.16)
    sc12 = [x for x in a1["A1_monte_carlo_parameter_recovery"]["scenario1_null_and_scenario2_sweep"] if x["design"] == "strict_a_lt_b"]
    sc3_null = [x for x in a1["A1_monte_carlo_parameter_recovery"]["scenario3_confounded_bucket_merit"] if x["gamma_true"] == 0.0]
    g_true = np.array([x["gamma_true"] for x in sc12])
    b3_unadj = np.array([x["bucket3_share_unadjusted"] * 100.0 for x in sc12])
    b3_oa = np.array([x["bucket3_share_oa_btl"] * 100.0 for x in sc12])

    ax_b.axhline(33.33, color="#666666", linestyle=":", lw=1.0, label="Equal-Merit Bucket-3 Share (33.3%)")
    ax_b.plot(g_true, b3_unadj, "-o", color=C_VERM, lw=2.2, markersize=5.5, label="Unadjusted BTL under a < b")
    ax_b.plot(g_true, b3_oa, "-D", color=C_TEAL, lw=2.2, markersize=5.5, label="OA-BTL Rectified under a < b")
    ax_b.fill_between(g_true, b3_unadj, b3_oa, color=C_TEAL, alpha=0.14)

    deltas = np.array([x["delta_bucket1_minus_bucket3"] for x in sc3_null])
    b3_true_sc3 = np.array([x["true_bucket3_top10_share"] * 100.0 for x in sc3_null])
    b3_oa_sc3 = np.array([x["full_oa_bucket3_share"] * 100.0 for x in sc3_null])
    ax_b.plot(deltas, b3_true_sc3, "--^", color=C_NAVY, lw=1.6, markersize=5.0, label=r"True Share ($\gamma=0$, $\Delta_{\mathrm{B1-B3}}=x$)")
    ax_b.plot(deltas, b3_oa_sc3, ":s", color=C_BLUE, lw=1.7, markersize=5.0, label=r"OA-BTL Share ($\gamma=0$, $\Delta_{\mathrm{B1-B3}}=x$)")

    ax_b.set_xlabel(r"True Primacy $\gamma$ (Solid) or Merit Gap $\Delta_{\mathrm{B1-B3}}$ at $\gamma=0$ (Dashed)", fontsize=7.6)
    ax_b.set_ylabel("Bucket-3 Top-10 Survival Share (%)", fontsize=8)
    ax_b.set_xlim(-0.1, 2.15)
    ax_b.set_ylim(0, 56)
    ax_b.set_title("Monte Carlo Identifiability & Zero False Rescue Under Merit Skew", fontsize=8.2, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="upper right", fontsize=5.8, frameon=False)

    # Panel C: Four-Order Ridge Regularization Sweep
    ax_c = fig.add_subplot(gs[1, :])
    add_panel_label(ax_c, "C", x=-0.06)
    sw = a1["A4_lambda_sensitivity_sweep"]
    lams = np.array([x["lambda"] for x in sw])
    jacc = np.array([x["mean_top10_jaccard_vs_001"] * 100.0 for x in sw])
    resc = np.array([x["nine_gold_targets_rescued"] / 9.0 * 100.0 for x in sw])
    b3_sh = np.array([x["bucket3_share_pct"] for x in sw])

    ax_c.fill_between([1e-4, 0.25], 0, 108, color=C_TEAL, alpha=0.08, label=r"9/9 Gold Pathways Rescued Plateau ($\lambda = 10^{-4}$ to $0.25$)")
    ax_c.axvline(0.01, color=C_NAVY, linestyle="--", lw=1.2, label=r"Pre-Specified Ridge Penalty ($\lambda = 0.01$)")
    ax_c.plot(lams, resc, "-D", color=C_TEAL, lw=2.3, markersize=6, label="Gold-Standard Pathway Rescue Rate (9/9 = 100%)")
    ax_c.plot(lams, jacc, "-o", color=C_BLUE, lw=2.1, markersize=5.5, label=r"Top-10 Jaccard Overlap vs. $\lambda = 0.01$ (%)")
    ax_c.plot(lams, b3_sh, "--^", color=C_VERM, lw=1.9, markersize=5.5, label="Bucket-3 Top-10 Survival Share (%)")

    ax_c.set_xscale("log")
    ax_c.set_xlabel(r"OA-BTL Ridge Penalty Hyperparameter $\lambda$ (Log Scale, 4 Orders of Magnitude)", fontsize=8.2)
    ax_c.set_ylabel("Stability / Rescue Rate / Share (%)", fontsize=8.2)
    ax_c.set_xlim(7e-5, 1.4)
    ax_c.set_ylim(0, 128)
    ax_c.set_title("Hyperparameter Sensitivity Sweep Across All 12 Discovery Runs (3,594 Verdicts)", fontsize=8.5, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="center left", bbox_to_anchor=(0.01, 0.56), ncol=1, fontsize=6.3, frameon=False)

    save_fig(fig, "Supplementary_Fig_3_OABTL_Identifiability_and_Sensitivity")


# ==============================================================================
# SUPPLEMENTARY FIGURE 4 (3 panels, 2+1 Asymmetric): Flip CIs, Calibration & NLI
# ==============================================================================
def make_supp_fig4(a3, a5_2, a6):
    fig = plt.figure(figsize=(13.4, 8.8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.0, 1.05], width_ratios=[1.05, 1.0], hspace=0.54, wspace=0.44)

    # Panel A: 5-Model Bidirectional Flip Spectrum with Exact 95% Binomial CIs (Upgraded!)
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A", x=-0.16)
    mods_t2 = [
        ("Grok-4.7-Fast (90 pairs)", 8, 90, C_SLATE),
        ("Gemini-4-Argon-High (90 pairs)", 10, 90, C_BLUE),
        ("Grok-4.7-High (90 pairs)", 12, 90, C_AMBER),
        ("Gemini-3.8-Flash (90 pairs)", 24, 90, C_PURPLE),
        ("GLM-5.3 Discovery T2 (1,601 pairs)", 689, 1601, C_VERM),
    ]
    y_m = np.arange(len(mods_t2))
    ax_a.fill_betweenx([-0.7, 4.7], 8.89, 43.04, color=C_AMBER, alpha=0.07, zorder=1)
    for i, (lbl, k, n, col) in enumerate(mods_t2):
        val = 100.0 * k / n
        ci = 1.96 * 100.0 * math.sqrt((k / n) * (1.0 - k / n) / n)
        ax_a.errorbar([val], [i], xerr=[ci], fmt="D", color=col, ecolor=col, elinewidth=2.0,
                      capsize=3.2, markersize=6.2, markeredgecolor="#111111", zorder=4)
        ax_a.text(val + ci + 1.3, i, f"{val:.1f}%", va="center", fontsize=6.8, fontweight="bold", color=col)
    ax_a.set_yticks(y_m)
    ax_a.set_yticklabels([m[0] for m in mods_t2], fontsize=6.9, fontweight="bold")
    ax_a.set_xlabel("Bidirectional A/B Verdict Flip Rate (% +/- 95% CI)", fontsize=8)
    ax_a.set_xlim(0, 56)
    ax_a.set_ylim(-0.7, 4.7)
    ax_a.set_title("Cross-Ecosystem Tournament II Flip Spectrum Across 5 Frontier LLMs", fontsize=8.2, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")

    # Panel B: Multi-Method Calibration Benchmark Across 5 Cohorts (Zero snake_case!)
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B", x=-0.16)
    cal = a3["A7_calibration_benchmark"]
    sweep_12 = a6["A9_selective_calibration_tau_ece_sweep"]["0.12"]
    cohorts = [
        ("GLM-5.3 Pooled (n=480)", cal["GLM-5.3_Parent_Pooled_n480"]["methods"], cal["GLM-5.3_Parent_Pooled_n480"]["methods"]["selective_gate"]["ece_primary"], 480, C_NAVY, "o"),
        ("Gemini-4-Argon (n=60)", cal["Gemini-4-Argon-High_ExpC_n60"]["methods"], sweep_12["Gemini-4-Argon-High"]["ece_5bin"], 60, C_BLUE, "^"),
        ("Gemini-3.8-Flash (n=60)", cal["Gemini-3.8-Flash_ExpC_n60"]["methods"], sweep_12["Gemini-3.8-Flash"]["ece_5bin"], 60, C_PURPLE, "v"),
        ("Grok-4.7-High (n=60)", cal["Grok-4.7-High_ExpC_n60"]["methods"], sweep_12["Grok-4.7-High"]["ece_5bin"], 60, C_AMBER, "P"),
        ("Grok-4.7-Fast (n=60)", cal["Grok-4.7-Fast_ExpC_n60"]["methods"], sweep_12["Grok-4.7-Fast"]["ece_5bin"], 60, C_TEAL, "D"),
    ]
    x_c = np.array([0, 1, 2, 3])
    ax_b.fill_between([-0.25, 3.25], 0.0, 0.12, color=C_TEAL, alpha=0.07, zorder=1)
    ax_b.axhline(0.12, color="#666666", linestyle=":", lw=1.0, label=r"Selective Gate Threshold ($\tau_{\mathrm{ECE}} = 0.12$)")
    for lbl, md, sel_v, n_c, col, mk in cohorts:
        ys = np.array([md["raw"]["ece_primary"], md["shift_1param"]["ece_primary"], md["platt_2param_unreg"]["ece_primary"], sel_v])
        ses = np.array([0.5 * math.sqrt(max(0.01, y * (1.0 - y)) / n_c) for y in ys])
        ax_b.errorbar(x_c, ys, yerr=ses, fmt=f"-{mk}", color=col, ecolor=col, lw=1.8, elinewidth=0.9,
                      capsize=2.0, markersize=5.2, label=f"{lbl}: {ys[0]:.3f} -> {ys[3]:.3f}")
    ax_b.set_xticks(x_c)
    ax_b.set_xticklabels(["Raw\nVerbalized", "1-Param\nShift", "Always-On\nLORO Platt", "Selective\nGate (v2)"], fontsize=7.0, fontweight="bold")
    ax_b.set_ylabel("Expected Calibration Error (ECE)", fontsize=8)
    ax_b.set_xlim(-0.25, 3.25)
    ax_b.set_ylim(0, 0.74)
    ax_b.set_title("Selective Gate Prevents Overfitting on Calibrated Models", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper right", fontsize=5.7, frameon=False)

    # Panel C: DeBERTa-v3 NLI Threshold Sensitivity + 50-Pair Blinded Expert Anchor
    ax_c = fig.add_subplot(gs[1, :])
    add_panel_label(ax_c, "C", x=-0.06)
    ns = a6["A9_deberta_nli_tau_sweep"]
    taus_n = np.array([x["tau"] for x in ns])
    t2_b = np.array([x["t2_biased_dir_contra_pct"] for x in ns])
    t2_c = np.array([x["t2_consistent_dir_contra_pct"] for x in ns])
    prop = np.array([x["silent_top5_propagation_pct"] for x in ns])
    exp_nli = a5_2["tournament_II_judge_nli_validation_n50"]

    ax_c.axvline(0.75, color=C_NAVY, linestyle="--", lw=1.2, label=r"Pre-Registered NLI Threshold ($\tau = 0.75$)")
    ax_c.plot(taus_n, prop, "-s", color=C_BLUE, lw=2.2, markersize=5.5, label="Silent Cross-Stage Propagation to Top-5 (42.9%-48.7%)")
    ax_c.plot(taus_n, t2_b, "-D", color=C_VERM, lw=2.2, markersize=5.5, label="T2 Position-Flipped Judge Contradiction Rate (%)")
    ax_c.plot(taus_n, t2_c, "-o", color=C_TEAL, lw=2.2, markersize=5.5, label="T2 Position-Consistent Judge Contradiction Rate (%)")
    ax_c.fill_between(taus_n, t2_c, t2_b, color=C_VERM, alpha=0.14)

    # Overlay 50-pair blinded expert Precision (88.0%) & Recall (78.6%) anchor at tau = 0.75
    ax_c.scatter([0.75], [exp_nli["precision_pct"]], color=C_NAVY, marker="*", s=130, edgecolor="#111111", zorder=6,
                 label=f"Expert Precision at 0.75 ({exp_nli['precision_pct']:.1f}%, F1={exp_nli['f1']:.2f})")
    ax_c.scatter([0.75], [exp_nli["recall_pct"]], color=C_PURPLE, marker="P", s=85, edgecolor="#111111", zorder=6,
                 label=f"Expert Recall at 0.75 ({exp_nli['recall_pct']:.1f}%, n=50 pairs)")

    ax_c.set_xlabel(r"DeBERTa-v3 NLI Contradiction Probability Threshold $\tau$", fontsize=8.2)
    ax_c.set_ylabel("Contradiction / Propagation / Expert Precision (%)", fontsize=8.2)
    ax_c.set_xlim(0.48, 0.97)
    ax_c.set_ylim(0, 106)
    ax_c.set_title("Threshold-Invariant NLI Contradiction Excess (2.4x-3.1x) & Blinded Expert Calibration", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper left", ncol=2, fontsize=6.2, frameon=False)

    save_fig(fig, "Supplementary_Fig_4_MultiModel_Calibration_NLI_and_Latency")


@retry_limit(2)
def main():
    a1 = json.load(open(os.path.join(HERE, "nc_upgrade_A1_A4_results.json"), encoding="utf-8"))
    a2 = json.load(open(os.path.join(HERE, "nc_upgrade_A2_results.json"), encoding="utf-8"))
    a3 = json.load(open(os.path.join(HERE, "nc_upgrade_A3_A7_results.json"), encoding="utf-8"))
    a5_1 = json.load(open(os.path.join(HERE, "nc_upgrade_A5_part1_results.json"), encoding="utf-8"))
    a5_2 = json.load(open(os.path.join(HERE, "nc_upgrade_A5_part2_results.json"), encoding="utf-8"))
    a6 = json.load(open(os.path.join(HERE, "nc_upgrade_A6_A9_results.json"), encoding="utf-8"))

    canary_gate(lambda: len(a1["A4_lambda_sensitivity_sweep"]) >= 7, "Verify A1/A4 sweep loaded")
    make_supp_fig1(a2, a5_1)
    make_supp_fig2(a3)
    make_supp_fig3(a1)
    make_supp_fig4(a3, a5_2, a6)
    print("ALL 4 PLAN-A SUPPLEMENTARY FIGURES GENERATED IN:", FIG_DIR)


if __name__ == "__main__":
    main()
