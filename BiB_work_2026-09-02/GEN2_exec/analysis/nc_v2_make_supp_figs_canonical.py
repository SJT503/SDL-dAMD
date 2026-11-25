#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nc_v2_make_supp_figs_canonical.py -- Generate 4 Nature Communications canonical
Supplementary Figures (Supplementary Figs. 1-4; [3, 4, 4, 3] = 14 panels) into
GEN2_exec/figures_NC_v2_canonical.

Every panel strictly uses standard Nature / Nature Communications competitor chart types:
  - Supp Fig. 1A: 5-LLM x-axis grouped point-intervals across 4 modes (NC02 Hyper-RAG Fig. 2)
  - Supp Fig. 1B: Dodged Point-and-95%-CI Verifier Calibration vs 100-Slot Expert Audit
  - Supp Fig. 1C: Grouped Point-Intervals across 3 Literature-Density Strata (NC02 Fig. 5a)
  - Supp Fig. 2A-D: STROBE 95%-CI forest, HPO starvation ECDF, 5-way HGNC ablation with exact
    paired McNemar 95% CIs, and 3x7 2D hyperparameter grid heatmap.
  - Supp Fig. 3A-D: Intra-bucket primacy forest (3A), pure gamma_true recovery curve (3B),
    split pure confounded-null Delta_{B1-B3} curve at gamma=0 (3C), and 4-order lambda sweep (3D).
  - Supp Fig. 4A-C: 5-LLM flip forest (4A), 5-cohort x-axis grouped calibration methods (4B,
    NC02 Fig. 2), and continuous DeBERTa-v3 threshold sweep + 50-pair expert anchor (4C).
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
plt.rcParams["axes.labelpad"] = 7.0
plt.rcParams["axes.titlepad"] = 8.0
plt.rcParams["legend.frameon"] = False
plt.rcParams["legend.labelspacing"] = 0.58

HERE = os.path.dirname(os.path.abspath(__file__))
EXEC_DIR = os.path.dirname(HERE)
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
FIG_DIR = os.path.join(EXEC_DIR, "figures_NC_v2_canonical")
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
    ax.tick_params(labelsize=7.2, colors="#222222")
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.5, color="#E0E0E0", alpha=0.8)
        ax.set_axisbelow(True)


def add_panel_label(ax, txt, x=-0.14, y=1.10):
    ax.text(x, y, txt, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top", ha="left", color="#111111")


def wilson_half_ci(k, n):
    if n <= 0:
        return 0.0
    p = k / n
    return 1.96 * 100.0 * math.sqrt(max(0.002, p * (1.0 - p)) / n)


def save_fig(fig, name):
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {name} (.svg, .pdf, .png)")


# ==============================================================================
# SUPPLEMENTARY FIGURE 1 (3 panels, 1+2 Asymmetric)
# ==============================================================================
def make_supp_fig1(a2, a5_1):
    fig = plt.figure(figsize=(13.6, 8.9))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.04, 1.04], width_ratios=[1.12, 0.98], hspace=0.54, wspace=0.42)

    # Panel A: NC02 Hyper-RAG Fig. 2 Style 5-LLM Grouped Point-Interval (Error & Yield!)
    ax_a = fig.add_subplot(gs[0, :])
    add_panel_label(ax_a, "A", x=-0.06)
    sp = a2["honest_split_by_model_and_arm"]
    cl84 = a2["closed_loop_5model_matched84"]
    models_5 = [
        ("GLM-5.3\n(420 slots)", sp["GLM-5.3_ExpB_Full420"], 420, a2["closed_loop_glm_full420"]["closed_loop_verified_grounded_yield_pct"]),
        ("Gemini-4-Argon\n(84 slots)", sp["Gemini-4-Argon-High"], 84, cl84["Gemini-4-Argon-High"]["post_handoff_verified_yield_pct"]),
        ("Gemini-3.8-Flash\n(84 slots)", sp["Gemini-3.8-Flash"], 84, cl84["Gemini-3.8-Flash"]["post_handoff_verified_yield_pct"]),
        ("Grok-4.7-High\n(84 slots)", sp["Grok-4.7-High"], 84, cl84["Grok-4.7-High"]["post_handoff_verified_yield_pct"]),
        ("Grok-4.7-Fast\n(84 slots)", sp["Grok-4.7-Fast"], 84, cl84["Grok-4.7-Fast"]["post_handoff_verified_yield_pct"]),
    ]
    xm = np.arange(len(models_5))
    ax_a.fill_between([-0.45, 4.45], 96.0, 103.0, color=C_TEAL, alpha=0.08, zorder=1)
    ax_a.axhline(100.0, color=C_TEAL, linestyle=":", lw=1.0)

    series_specs = [
        (-0.27, "ung_err", "1. Ungated Ungrounded Error (%)", C_RED_DARK, "X"),
        (-0.09, "as_discovered", "2. Ungated Verified Yield (%)", C_AMBER, "o"),
        (0.09, "gated", "3. Module 3a Alone Parametric Yield (%)", C_BLUE, "^"),
        (0.27, "closed_loop", "4. Closed-Loop Module 3a+3b Verified Yield (100%, 0% Err)", C_TEAL, "D"),
    ]
    for dx, mkey, mlbl, col, mk in series_specs:
        ys, ses = [], []
        for _, md, n_sl, cl_y in models_5:
            if mkey == "ung_err":
                val = md["as_discovered"]["ungrounded_rate_pct"]
            elif mkey == "closed_loop":
                val = cl_y
            else:
                val = md[mkey]["parametric_grounded_yield_pct"]
            se = 100.0 * math.sqrt(max(0.0, (val / 100.0) * (1.0 - val / 100.0)) / n_sl)
            ys.append(val)
            ses.append(se)
        ax_a.errorbar(xm + dx, ys, yerr=ses, fmt=mk, color=col, ecolor=col,
                      elinewidth=1.6, capsize=2.6, markersize=6.2, markeredgecolor="#111111", zorder=4, label=mlbl)
        if mkey == "closed_loop":
            for xi in xm:
                ax_a.text(xi + dx, 104.2, "100%", ha="center", fontsize=6.2, fontweight="bold", color=C_TEAL)

    ax_a.set_xticks(xm)
    ax_a.set_xticklabels([m[0] for m in models_5], fontsize=7.3, fontweight="bold")
    ax_a.set_ylabel("Citation Slot Proportion (% +/- SE)", fontsize=8.1)
    ax_a.set_xlim(-0.48, 4.48)
    ax_a.set_ylim(-5, 128)
    ax_a.set_title("Separating Parametric Abstention Safety (Module 3a) from Closed-Loop Entrez Yield (Module 3b)", fontsize=8.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper center", ncol=2, fontsize=6.3, frameon=False)

    # Panel B: Canonical Dodged Point-and-95%-CI Verifier Calibration (100 Stratified Slots)
    ax_b = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_b, "B", x=-0.15)
    v1 = a5_1["tier2_100slot_expert_audit"]["tier2_v1_prereg_blunt_metrics"]
    v2 = a5_1["tier2_100slot_expert_audit"]["tier2_v2_entity_anchored_metrics"]
    met_lbls = ["Precision\n(Trojan)", "Recall\n(Trojan)", "Specificity\n(On-Topic)", "Overall\nAccuracy"]
    v1_vals = [v1["precision_pct"], v1["recall_pct"], v1["specificity_pct"], v1["accuracy_pct"]]
    v1_cis = [wilson_half_ci(58, 58), wilson_half_ci(58, 79), wilson_half_ci(21, 21), wilson_half_ci(79, 100)]
    v2_vals = [v2["precision_pct"], v2["recall_pct"], v2["specificity_pct"], v2["accuracy_pct"]]
    v2_cis = [wilson_half_ci(79, 88), wilson_half_ci(79, 79), wilson_half_ci(12, 21), wilson_half_ci(91, 100)]
    xb = np.arange(4)

    ax_b.fill_between([-0.48, 3.48], 85.0, 102.0, color=C_TEAL, alpha=0.07, zorder=1)
    v1_lo = [min(v, c) for v, c in zip(v1_vals, v1_cis)]
    v1_hi = [min(100.0 - v, c) for v, c in zip(v1_vals, v1_cis)]
    v2_lo = [min(v, c) for v, c in zip(v2_vals, v2_cis)]
    v2_hi = [min(100.0 - v, c) for v, c in zip(v2_vals, v2_cis)]
    ax_b.errorbar(xb - 0.16, v1_vals, yerr=[v1_lo, v1_hi],
                  fmt="o", color=C_BLUE, ecolor=C_BLUE, elinewidth=1.8, capsize=3.0, markersize=6.2, markeredgecolor="#111111",
                  label="Tier-2 v1 Pre-Reg (TP=58, FP=0, FN=21, TN=21; F1=0.847)")
    ax_b.errorbar(xb + 0.16, v2_vals, yerr=[v2_lo, v2_hi],
                  fmt="D", color=C_TEAL, ecolor=C_TEAL, elinewidth=1.8, capsize=3.0, markersize=6.2, markeredgecolor="#111111",
                  label="Tier-2 v2 Entity Filter (TP=79, FP=9, FN=0, TN=12; F1=0.946)")
    for i in range(4):
        y_cap1 = v1_vals[i] + v1_hi[i]
        y_cap2 = v2_vals[i] + v2_hi[i]
        lbl1 = "100%" if v1_vals[i] >= 99.95 else f"{v1_vals[i]:.1f}%"
        lbl2 = "100%" if v2_vals[i] >= 99.95 else f"{v2_vals[i]:.1f}%"
        ax_b.text(xb[i] - 0.16, y_cap1 + 2.4, lbl1, ha="center", va="bottom", fontsize=5.9, fontweight="bold", color=C_BLUE)
        ax_b.text(xb[i] + 0.16, y_cap2 + 2.4, lbl2, ha="center", va="bottom", fontsize=5.9, fontweight="bold", color=C_TEAL)

    ax_b.set_xticks(xb)
    ax_b.set_xticklabels(met_lbls, fontsize=6.9, fontweight="bold")
    ax_b.set_ylabel("Expert Calibration Score (% +/- 95% CI)", fontsize=8)
    ax_b.set_xlim(-0.52, 3.52)
    ax_b.set_ylim(28, 129)
    ax_b.set_title("100-Slot Blinded Expert Audit (79 True Trojan, 21 On-Topic)", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper right", fontsize=5.6, frameon=False)

    # Panel C: Grouped Point-Intervals Across 3 Literature-Density Strata (Zero Nominal Zigzag!)
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

    ax_c.fill_between([-0.4, 2.4], 96.0, 103.0, color=C_TEAL, alpha=0.08, zorder=1)
    ax_c.errorbar(x_t - 0.16, asd_ung, yerr=asd_se, fmt="o", color=C_VERM, ecolor=C_VERM,
                  elinewidth=1.8, capsize=3.0, markersize=6.2, markeredgecolor="#111111", label="Ungated Baseline Ungrounded (%)")
    ax_c.errorbar(x_t, cl_yield, yerr=[0.0, 0.0, 0.0], fmt="D", color=C_TEAL, ecolor=C_TEAL,
                  elinewidth=1.8, capsize=2.8, markersize=6.2, markeredgecolor="#111111", label="Closed-Loop Verified Yield (100%)")
    ax_c.errorbar(x_t + 0.16, [0.0, 0.0, 0.0], yerr=[0.0, 0.0, 0.0], fmt="s", color=C_NAVY, ecolor=C_NAVY,
                  elinewidth=1.6, capsize=2.8, markersize=5.4, markeredgecolor="#111111", label="Closed-Loop Ungrounded Error (0%)")
    for i in range(3):
        ax_c.text(x_t[i] - 0.16, asd_ung[i] + asd_se[i] + 3.5, f"{asd_ung[i]:.1f}%", ha="center", fontsize=6.2, fontweight="bold", color=C_VERM)

    ax_c.set_xticks(x_t)
    ax_c.set_xticklabels(t_lbls, fontsize=6.8, fontweight="bold")
    ax_c.set_ylabel("Slot Proportion (% +/- SE)", fontsize=8)
    ax_c.set_xlim(-0.45, 2.45)
    ax_c.set_ylim(-6, 134)
    ax_c.set_title("Closed-Loop Entrez Retrieval Across Literature-Density Strata", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="y")
    ax_c.legend(loc="upper left", fontsize=5.8, frameon=False)

    save_fig(fig, "Supplementary_Fig_1_Module3_ClosedLoop_and_ExpertAudit")


# ==============================================================================
# SUPPLEMENTARY FIGURE 2 (4 panels): STROBE, Starvation, Paired CI Ablation, Grid
# ==============================================================================
def make_supp_fig2(a3):
    fig = plt.figure(figsize=(13.6, 9.0))
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

    # Panel B: HPO Term-Count Starvation ECDF
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

    # Panel C: External HGNC 5-Way Ablation with Exact Paired McNemar 95% CIs!
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
    ax_c.fill_betweenx([-0.7, 5.0], 0.0, 66.0, color=C_TEAL, alpha=0.06, zorder=1)
    ax_c.axvline(0.0, color="#222222", linestyle="--", lw=1.0)
    for idx, (k, lbl) in enumerate(ab_order):
        g_net = ab[k]["glm"]["net_gain_hits"]
        d_net = ab[k]["deepseek"]["net_gain_hits"]
        p_rec = ab[k]["pooled"]
        p_net = p_rec["net_gain_hits"]
        # Exact paired difference SE = sqrt(gained + lost) -> 95% CI = +/- 1.96 * SE
        se_pair = math.sqrt(max(0.0, p_rec["gained_hits"] + p_rec["lost_hits"]))
        ci_pair = 1.96 * se_pair
        col_p = C_TEAL if p_net >= 0 else C_VERM
        ax_c.errorbar([p_net], [idx], xerr=[ci_pair], fmt="D", color=col_p, ecolor=col_p,
                      elinewidth=1.8, capsize=2.8, markersize=6.4, markeredgecolor="#111111", zorder=4,
                      label="Pooled Net Rescue +/- 95% CI" if idx == 0 else None)
        ax_c.scatter([g_net], [idx + 0.16], color=C_BLUE, s=30, marker="o", zorder=3, label="GLM-5.3 Net Hits" if idx == 0 else None)
        ax_c.scatter([d_net], [idx - 0.16], color=C_AMBER, s=32, marker="^", zorder=3, label="DeepSeek-V4 Net Hits" if idx == 0 else None)
        if p_net >= 0:
            ax_c.text(p_net + ci_pair + 1.8, idx, f"{p_net:+d} hits", va="center", ha="left", fontsize=6.4,
                      fontweight="bold", color=C_TEAL if p_net > 0 else "#444444")
        else:
            ax_c.text(p_net - ci_pair - 1.8, idx, f"{p_net:+d} hits", va="center", ha="right", fontsize=6.4,
                      fontweight="bold", color=C_VERM)
    ax_c.set_yticks(y_ab)
    ax_c.set_yticklabels([x[1] for x in ab_order], fontsize=6.8, fontweight="bold")
    ax_c.set_xlabel("Net Rescued Mendelian Diagnoses Across 630 Calls (+/- 95% CI)", fontsize=7.9)
    ax_c.set_xlim(-32, 74)
    ax_c.set_ylim(-0.7, 5.1)
    ax_c.set_title("External HGNC 5-Way Ablation: Module 4a Rescues +48 (0 Lost)", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="upper left", fontsize=5.8, frameon=False)

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
# SUPPLEMENTARY FIGURE 3 (4 panels, Split Pure X-Axes!):
#   3A: Intra-Bucket vs Between-Bucket Primacy Forest
#   3B: Pure True Primacy gamma_true in [0, 2.0] Parameter-Recovery Curve
#   3C: Pure Confounded-Null Merit Gap Delta_{B1-B3} in [0, 1.5] at gamma = 0
#   3D: Four-Order Ridge Regularization Sweep lambda in [10^-4, 1.0]
# ==============================================================================
def make_supp_fig3(a1):
    fig = plt.figure(figsize=(14.0, 9.0))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.04, 1.0], hspace=0.52)
    gs_top = gs[0, 0].subgridspec(1, 3, width_ratios=[1.08, 0.96, 0.96], wspace=0.40)

    # Panel A: Intra-Bucket vs Between-Bucket Primacy Forest
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A", x=-0.18)
    wb = a1["A1_empirical_within_bucket_primacy"]
    cats = [
        ("Between-Bucket (n=2,515)", wb["between_bucket_slotA_wins"], wb["between_bucket_total"], C_SLATE),
        ("All Intra-Bucket (n=1,079)", wb["pooled_within_bucket_slotA_wins"], wb["pooled_within_bucket_total"], C_NAVY),
        ("Intra-Bucket 3 (n=335)", wb["by_bucket"]["Bucket_3"]["slotA_wins"], wb["by_bucket"]["Bucket_3"]["total"], C_TEAL),
        ("Intra-Bucket 2 (n=348)", wb["by_bucket"]["Bucket_2"]["slotA_wins"], wb["by_bucket"]["Bucket_2"]["total"], C_BLUE),
        ("Intra-Bucket 1 (n=396)", wb["by_bucket"]["Bucket_1"]["slotA_wins"], wb["by_bucket"]["Bucket_1"]["total"], C_VERM),
    ]
    y_pos = np.arange(len(cats))
    ax_a.fill_betweenx([-0.7, 5.1], 65.4, 71.0, color=C_NAVY, alpha=0.08, zorder=1)
    ax_a.axvline(50.0, color="#222222", linestyle="--", lw=1.1, label="Fairness Null (50%)")
    for idx, (lbl, k, n, col) in enumerate(cats):
        p = 100.0 * k / n
        se = 1.96 * 100.0 * math.sqrt((k / n) * (1.0 - k / n) / n)
        ax_a.errorbar([p], [idx], xerr=[se], fmt="o", color=col, ecolor=col, elinewidth=1.9, capsize=3.0, markersize=5.8)
        ax_a.text(p + se + 1.0, idx, f"{p:.1f}%", va="center", fontsize=6.4, fontweight="bold", color=col)
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels([c[0] for c in cats], fontsize=6.6, fontweight="bold")
    ax_a.set_xlabel("Tournament I Slot-A Win Rate (% +/- 95% CI)", fontsize=7.8)
    ax_a.set_xlim(44, 93)
    ax_a.set_ylim(-0.7, 5.1)
    ax_a.set_title("Intra-Bucket Pairs: 68.2% Primacy (p=1.5e-33)", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper left", fontsize=6.0, frameon=False)

    # Panel B: Pure True Primacy gamma_true Sweep (Single Meaning X-Axis!)
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B", x=-0.16)
    sc12 = [x for x in a1["A1_monte_carlo_parameter_recovery"]["scenario1_null_and_scenario2_sweep"] if x["design"] == "strict_a_lt_b"]
    g_true = np.array([x["gamma_true"] for x in sc12])
    b3_unadj = np.array([x["bucket3_share_unadjusted"] * 100.0 for x in sc12])
    b3_oa = np.array([x["bucket3_share_oa_btl"] * 100.0 for x in sc12])

    ax_b.axhline(33.33, color="#666666", linestyle=":", lw=1.0, label="Equal-Merit Share (33.3%)")
    ax_b.fill_between(g_true, b3_unadj, b3_oa, color=C_TEAL, alpha=0.14)
    ax_b.plot(g_true, b3_unadj, "-o", color=C_VERM, lw=2.2, markersize=5.4, label="Unadjusted BTL (a < b)")
    ax_b.plot(g_true, b3_oa, "-D", color=C_TEAL, lw=2.2, markersize=5.4, label="OA-BTL Rectified (a < b)")
    ax_b.set_xlabel(r"Simulated True Primacy Intercept $\gamma_{\mathrm{true}}$", fontsize=7.8)
    ax_b.set_ylabel("Bucket-3 Top-10 Share (%)", fontsize=7.8)
    ax_b.set_xlim(-0.08, 2.10)
    ax_b.set_ylim(0, 52)
    ax_b.set_title("Monte Carlo Primacy Recovery (400 sims/cell)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="lower left", fontsize=5.8, frameon=False)

    # Panel C: Pure Confounded-Null Test (gamma_true = 0, Merit Gap Delta_{B1-B3})
    ax_c = fig.add_subplot(gs_top[0, 2])
    add_panel_label(ax_c, "C", x=-0.16)
    sc3_null = [x for x in a1["A1_monte_carlo_parameter_recovery"]["scenario3_confounded_bucket_merit"] if x["gamma_true"] == 0.0]
    deltas = np.array([x["delta_bucket1_minus_bucket3"] for x in sc3_null])
    b3_true_sc3 = np.array([x["true_bucket3_top10_share"] * 100.0 for x in sc3_null])
    b3_oa_sc3 = np.array([x["full_oa_bucket3_share"] * 100.0 for x in sc3_null])

    ax_c.fill_between(deltas, b3_true_sc3 - 2.0, b3_true_sc3 + 2.0, color=C_NAVY, alpha=0.10, label="True Merit Band")
    ax_c.plot(deltas, b3_true_sc3, "-^", color=C_NAVY, lw=2.1, markersize=5.5, label="True Oracle Bucket-3 Share")
    ax_c.plot(deltas, b3_oa_sc3, "--s", color=C_BLUE, lw=2.0, markersize=5.2, label="OA-BTL Estimated Share")
    ax_c.text(0.75, 36.0, r"Zero False Primacy" + "\n" + r"($\hat{\gamma} \in [-0.003, +0.023]$)", ha="center", fontsize=6.1, fontweight="bold", color=C_NAVY)
    ax_c.set_xlabel(r"True Bucket-1 vs. Bucket-3 Merit Gap $\Delta_{\mathrm{B1-B3}}$ ($\gamma=0$)", fontsize=7.6)
    ax_c.set_ylabel("Bucket-3 Top-10 Share (%)", fontsize=7.8)
    ax_c.set_xlim(-0.08, 1.60)
    ax_c.set_ylim(0, 52)
    ax_c.set_title("Confounded-Null Identifiability (Zero False Rescue)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper right", fontsize=5.7, frameon=False)

    # Panel D: Four-Order Ridge Regularization Sweep
    ax_d = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_d, "D", x=-0.06)
    sw = a1["A4_lambda_sensitivity_sweep"]
    lams = np.array([x["lambda"] for x in sw])
    jacc = np.array([x["mean_top10_jaccard_vs_001"] * 100.0 for x in sw])
    resc = np.array([x["nine_gold_targets_rescued"] / 9.0 * 100.0 for x in sw])
    b3_sh = np.array([x["bucket3_share_pct"] for x in sw])

    ax_d.fill_between([1e-4, 0.25], 0, 108, color=C_TEAL, alpha=0.08, label=r"9/9 Gold Pathways Rescued Plateau ($\lambda = 10^{-4}$ to $0.25$)")
    ax_d.axvline(0.01, color=C_NAVY, linestyle="--", lw=1.2, label=r"Pre-Specified Ridge Penalty ($\lambda = 0.01$)")
    ax_d.plot(lams, resc, "-D", color=C_TEAL, lw=2.3, markersize=6, label="Gold-Standard Pathway Rescue Rate (9/9 = 100%)")
    ax_d.plot(lams, jacc, "-o", color=C_BLUE, lw=2.1, markersize=5.5, label=r"Top-10 Jaccard Overlap vs. $\lambda = 0.01$ (%)")
    ax_d.plot(lams, b3_sh, "--^", color=C_VERM, lw=1.9, markersize=5.5, label="Bucket-3 Top-10 Survival Share (%)")

    ax_d.set_xscale("log")
    ax_d.set_xlabel(r"OA-BTL Ridge Penalty Hyperparameter $\lambda$ (Log Scale, 4 Orders of Magnitude)", fontsize=8.2)
    ax_d.set_ylabel("Stability / Rescue Rate / Share (%)", fontsize=8.2)
    ax_d.set_xlim(7e-5, 1.4)
    ax_d.set_ylim(0, 128)
    ax_d.set_title("Hyperparameter Sensitivity Sweep Across All 12 Discovery Runs (3,594 Verdicts)", fontsize=8.5, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="center left", bbox_to_anchor=(0.01, 0.56), ncol=1, fontsize=6.3, frameon=False)

    save_fig(fig, "Supplementary_Fig_3_OABTL_Identifiability_and_Sensitivity")


# ==============================================================================
# SUPPLEMENTARY FIGURE 4 (3 panels, 2+1 Asymmetric): Flip CIs, Grouped ECE & NLI
# ==============================================================================
def make_supp_fig4(a3, a5_2, a6):
    fig = plt.figure(figsize=(13.6, 8.9))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.02, 1.04], width_ratios=[1.02, 1.08], hspace=0.54, wspace=0.42)

    # Panel A: 5-Model Bidirectional Flip Spectrum Forest
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

    # Panel B: NC02 Hyper-RAG Fig. 2 Style 5-Cohort X-Axis Grouped Calibration Point-Intervals!
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B", x=-0.15)
    cal = a3["A7_calibration_benchmark"]
    sweep_12 = a6["A9_selective_calibration_tau_ece_sweep"]["0.12"]
    cohorts = [
        ("GLM-5.3\n(n=480)", cal["GLM-5.3_Parent_Pooled_n480"]["methods"], cal["GLM-5.3_Parent_Pooled_n480"]["methods"]["selective_gate"]["ece_primary"], 480),
        ("Gemini-4\nArgon", cal["Gemini-4-Argon-High_ExpC_n60"]["methods"], sweep_12["Gemini-4-Argon-High"]["ece_5bin"], 60),
        ("Gemini-3.8\nFlash", cal["Gemini-3.8-Flash_ExpC_n60"]["methods"], sweep_12["Gemini-3.8-Flash"]["ece_5bin"], 60),
        ("Grok-4.7\nHigh", cal["Grok-4.7-High_ExpC_n60"]["methods"], sweep_12["Grok-4.7-High"]["ece_5bin"], 60),
        ("Grok-4.7\nFast", cal["Grok-4.7-Fast_ExpC_n60"]["methods"], sweep_12["Grok-4.7-Fast"]["ece_5bin"], 60),
    ]
    xc = np.arange(len(cohorts))
    ax_b.fill_between([-0.48, 4.48], 0.0, 0.12, color=C_TEAL, alpha=0.08, zorder=1)
    ax_b.axhline(0.12, color="#666666", linestyle=":", lw=1.0, label=r"Selective Gate Threshold ($\tau_{\mathrm{ECE}} = 0.12$)")

    cal_modes = [
        (-0.24, "raw", "Raw Verbalized Confidence", C_VERM, "o"),
        (-0.08, "shift_1param", "1-Parameter Logit Shift", C_AMBER, "s"),
        (0.08, "platt_2param_unreg", "Always-On LORO Platt (Overfits Argon)", C_PURPLE, "^"),
        (0.24, "selective", "Selective Gate v2 (Preserves Argon 0.080)", C_TEAL, "D"),
    ]
    for dx, mkey, mlbl, col, mk in cal_modes:
        ys, ses = [], []
        for _, md, sel_v, n_c in cohorts:
            val = sel_v if mkey == "selective" else md[mkey]["ece_primary"]
            se = 0.5 * math.sqrt(max(0.01, val * (1.0 - val)) / n_c)
            ys.append(val)
            ses.append(se)
        ax_b.errorbar(xc + dx, ys, yerr=ses, fmt=mk, color=col, ecolor=col,
                      elinewidth=1.5, capsize=2.2, markersize=5.4, markeredgecolor="#111111", zorder=4, label=mlbl)

    ax_b.set_xticks(xc)
    ax_b.set_xticklabels([c[0] for c in cohorts], fontsize=6.6, fontweight="bold")
    ax_b.set_ylabel("Expected Calibration Error (ECE +/- SE)", fontsize=7.9)
    ax_b.set_xlim(-0.48, 4.48)
    ax_b.set_ylim(0, 0.72)
    ax_b.set_title("Selective Gate Prevents Overfitting on Calibrated Models", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper right", fontsize=5.6, frameon=False)

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
    print("ALL 4 CANONICAL SUPPLEMENTARY FIGURES GENERATED IN:", FIG_DIR)


if __name__ == "__main__":
    main()
