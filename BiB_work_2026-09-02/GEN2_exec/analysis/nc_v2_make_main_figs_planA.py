#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nc_v2_make_main_figs_planA.py -- Generate all 6 Nature Communications asymmetric
Main Figures (Figs. 1-6; [4, 5, 5, 5, 4, 5] = 28 panels) for STAR-Audit (Plan A).

Upgrades implemented from Editor/Reviewer 39-panel audit:
  1. Architectural schematic promoted from former Fig. 7 to full-width Hero Panel Fig. 1A
     (aspect='equal' on 600-DPI illustration), paired with Stage Token Violins (1B),
     Effect-Scaled BH-FDR Confirmatory Scorecard (1C), and 6-Dimension Polar Radar (1D).
  2. Non-2x2 asymmetric GridSpec layouts ([4, 5, 5, 5, 4, 5] organic panel counts),
     0% bar charts, 7 distinct visual families, and >=2 visual layers per data panel.
  3. Eliminated dual-meaning x-axis in Fig. 2D (pure GLM-5.3 CoT token phase plane) and
     added Fig. 2E closing the loop across all 5 models (Module 3a safety -> Module 3b 100% yield).
  4. Added Fig. 3D White-Box 2.1% CoT Instant-Recognition ECDF + Literature Footprint split
     (spelling out 'High/Low Lit. Footprint' with zero 'FP' false-positive ambiguity).
  5. Added Fig. 4C White-Box Decile-1 Slot-A Attention Trajectory (88.4% T1 / 90.6% T2)
     and Speech-Act Polarity Filter vector in Fig. 4E.
  6. Overlaid individual run/domain/pair scatter points in Figs. 2A, 3B, 4B, 5A, 6C,
     fair-share normalized all 4 pillars in Fig. 6C (0-100%), and added Fig. 6D stepwise
     composite gain envelope alongside Fig. 6E Pareto frontier.
  7. Replaced all internal block/stage ciphers ('Exp B', 'Exp C-v4', 'd-B1..A-R3', snake_case)
     with self-explanatory scientific terminology + programmatic bbox collision auditing.
"""
from gate import gate, canary_gate, retry_limit

import json
import math
import os
from collections import Counter, defaultdict
import numpy as np
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
plt.rcParams["xtick.major.pad"] = 4.5
plt.rcParams["ytick.major.pad"] = 4.5
plt.rcParams["legend.frameon"] = False
plt.rcParams["legend.labelspacing"] = 0.58

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
EXEC_DIR = os.path.join(BASE, "GEN2_exec")
ANAL_DIR = os.path.join(EXEC_DIR, "analysis")
HERE = ANAL_DIR
DATA_DIR = os.path.join(EXEC_DIR, "data")
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


def load_data():
    s1 = json.load(open(os.path.join(ANAL_DIR, "step1_pubmed_results.json"), encoding="utf-8"))
    s2 = json.load(open(os.path.join(ANAL_DIR, "step2_dim2_3_4_rectification_results.json"), encoding="utf-8"))
    s3 = json.load(open(os.path.join(ANAL_DIR, "step3_expC_dim6_paradox_results.json"), encoding="utf-8"))
    s4 = json.load(open(os.path.join(ANAL_DIR, "step4_dim5_nli_results.json"), encoding="utf-8"))
    a1 = json.load(open(os.path.join(ANAL_DIR, "nc_upgrade_A1_A4_results.json"), encoding="utf-8"))
    a2 = json.load(open(os.path.join(ANAL_DIR, "nc_upgrade_A2_results.json"), encoding="utf-8"))
    a6 = json.load(open(os.path.join(ANAL_DIR, "nc_upgrade_A6_A9_results.json"), encoding="utf-8"))
    ex = json.load(open(os.path.join(ANAL_DIR, "nc_v2_exact_plot_arrays.json"), encoding="utf-8"))
    expB_slots = json.load(open(os.path.join(ANAL_DIR, "step1_expB_slots_scored.json"), encoding="utf-8"))

    calls_by_id = {}
    stage_rt = defaultdict(list)
    stage_ans = defaultdict(list)
    with open(os.path.join(DATA_DIR, "calls_log.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("mock", False):
                continue
            cid = rec.get("call_id", "")
            vendor = rec.get("vendor", "unknown")
            rt = int(rec.get("reasoning_tokens") or 0)
            ot = int(rec.get("output_tokens") or 0)
            ans = max(0, ot - rt)
            if rec.get("ok", False):
                calls_by_id[cid] = rec
            if cid.startswith("parent/"):
                parts = cid.split("/")
                step = parts[2] if len(parts) > 2 else "other"
                if step == "step4":
                    stage_rt["T2_Judging"].append(rt / 1000.0)
                    stage_ans["T2_Judging"].append(ans / 1000.0)
                elif step == "step2":
                    stage_rt["T1_Screening"].append(rt / 1000.0)
                    stage_ans["T1_Screening"].append(ans / 1000.0)
                elif step == "step6":
                    stage_rt["Step6_Citations"].append(rt / 1000.0)
                    stage_ans["Step6_Citations"].append(ans / 1000.0)
                elif step in ("step1", "step3"):
                    stage_rt["Step1_3_Ideation"].append(rt / 1000.0)
                    stage_ans["Step1_3_Ideation"].append(ans / 1000.0)
            elif cid.startswith("expB/"):
                parts = cid.split("/")
                if len(parts) > 2 and parts[2] == "stage2":
                    stage_rt["Domain14_Citation"].append(rt / 1000.0)
                    stage_ans["Domain14_Citation"].append(ans / 1000.0)
            elif cid.startswith("expC_v4/"):
                key = "HPO_GLM" if vendor == "glm" else "HPO_DeepSeek"
                stage_rt[key].append(rt / 1000.0)
                stage_ans[key].append(ans / 1000.0)

    runs = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]
    t2_concordant_rt, t2_primacy_rt = [], []
    persona_flips_by_run = defaultdict(lambda: {1: [0, 0], 2: [0, 0], 3: [0, 0]})
    for run_id in runs:
        s4_v = json.load(open(os.path.join(RUNS_DIR, run_id, "step4_verdicts.json"), encoding="utf-8"))["verdicts"]
        for p_idx in range(45):
            for j in [1, 2, 3]:
                ka, kb = f"{p_idx:02d}_a_j{j}", f"{p_idx:02d}_b_j{j}"
                va, vb = s4_v.get(ka), s4_v.get(kb)
                if not va or not vb or va.get("failed") or vb.get("failed"):
                    continue
                wa, wb = va.get("winner_idx"), vb.get("winner_idx")
                sa, sb = va.get("slot_winner"), vb.get("slot_winner")
                if wa is None or wb is None:
                    continue
                persona_flips_by_run[run_id][j][1] += 1
                if wa != wb:
                    persona_flips_by_run[run_id][j][0] += 1
                rec_a = calls_by_id.get(f"parent/{run_id}/step4/{ka}")
                rec_b = calls_by_id.get(f"parent/{run_id}/step4/{kb}")
                if rec_a and rec_b:
                    rta = int(rec_a.get("reasoning_tokens") or 0) / 1000.0
                    rtb = int(rec_b.get("reasoning_tokens") or 0) / 1000.0
                    if wa == wb:
                        t2_concordant_rt.extend([rta, rtb])
                    elif sa == "A" and sb == "A":
                        t2_primacy_rt.extend([rta, rtb])

    expB_arm_rt = defaultdict(list)
    expB_dom_arm_rt = defaultdict(list)
    for d_idx in range(1, 15):
        did = f"B{d_idx:02d}"
        for arm in ["as_discovered", "abstain_probe", "gated"]:
            for h in range(1, 6):
                rec = calls_by_id.get(f"expB/glm/stage2/{arm}/{did}/h{h}")
                if rec:
                    val_k = int(rec.get("reasoning_tokens") or 0) / 1000.0
                    expB_arm_rt[arm].append(val_k)
                    expB_dom_arm_rt[(did, arm)].append(val_k)

    expC_rt_groups = defaultdict(list)
    with open(os.path.join(RUNS_DIR, "expC_v4", "results.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if not r.get("ok", False):
                continue
            rec = calls_by_id.get(r["call_id"])
            if rec:
                expC_rt_groups[(r["vendor"], 1 if r.get("hit10", False) else 0)].append(
                    int(rec.get("reasoning_tokens") or 0) / 1000.0
                )

    raw_bundle = {
        "stage_rt": stage_rt,
        "stage_ans": stage_ans,
        "t2_concordant_rt": np.array(t2_concordant_rt),
        "t2_primacy_rt": np.array(t2_primacy_rt),
        "persona_flips_by_run": persona_flips_by_run,
        "expB_arm_rt": {k: np.array(v) for k, v in expB_arm_rt.items()},
        "expB_dom_arm_rt": expB_dom_arm_rt,
        "expC_rt_groups": {k: np.array(v) for k, v in expC_rt_groups.items()},
    }
    return s1, s2, s3, s4, a1, a2, a6, ex, expB_slots, raw_bundle


def style_ax(ax, grid_axis="y"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.2, colors="#222222")
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.5, color="#E0E0E0", alpha=0.8)
        ax.set_axisbelow(True)


def add_panel_label(ax, label, x=-0.14, y=1.10):
    ax.text(x, y, label, transform=ax.transAxes, fontsize=11, fontweight="bold",
            va="top", ha="left", color="#111111")


def draw_alluvial_ribbon(ax, x0, x1, y0_bot, y0_top, y1_bot, y1_top, color, alpha=0.50):
    t = np.linspace(0, 1, 60)
    ease = 3 * t**2 - 2 * t**3
    xs = x0 + (x1 - x0) * t
    yb = y0_bot + (y1_bot - y0_bot) * ease
    yt = y0_top + (y1_top - y0_top) * ease
    ax.fill_between(xs, yb, yt, color=color, alpha=alpha, edgecolor="none")


def check_panel_collisions(fig, fig_name):
    """Programmatic text-bbox audit inside each Axes before saving."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    n_overlaps = 0
    for ax in fig.axes:
        if getattr(ax, "name", "") == "polar":
            continue
        bbs = []
        for t in ax.texts:
            if not t.get_visible() or not t.get_text().strip():
                continue
            txt_val = t.get_text().strip()
            if len(txt_val) == 1 and txt_val in "ABCDE":
                continue
            bb = t.get_window_extent(renderer=renderer).expanded(0.92, 0.88)
            for prev_txt, prev_bb in bbs:
                if bb.overlaps(prev_bb):
                    n_overlaps += 1
                    print(f"  [WARN collision in {fig_name}] {txt_val!r} <-> {prev_txt!r}")
            bbs.append((txt_val, bb))
    print(f"Collision check [{fig_name}]: {n_overlaps} intra-panel text overlaps")


def save_fig(fig, name):
    check_panel_collisions(fig, name)
    for ext in ["svg", "pdf", "png"]:
        path = os.path.join(FIG_DIR, f"{name}.{ext}")
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {name} (.svg, .pdf, .png)")


# ==============================================================================
# FIGURE 1 (4 panels, 1+3 Asymmetric Hero GridSpec):
#   1A (Top Full-Width Hero): Architectural Pipeline, 6 Sensors & 4 Rectifiers
#   1B (Bottom-Left): Per-Call CoT vs Visible Output Token Violins (N = 9,130)
#   1C (Bottom-Center): Effect-Scaled 6-Member Confirmatory BH-FDR Scorecard
#   1D (Bottom-Right, Polar): 6-Dimension Trustworthiness Radar (54.3% -> 92.4%)
# ==============================================================================
def make_fig1(s1, s2, s3, s4, a6, raw):
    fig = plt.figure(figsize=(14.4, 11.2))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.52, 1.0], hspace=0.26)

    # Panel A: Full-Width Hero Architectural Schematic (aspect='equal' enforced)
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A", x=-0.02, y=1.03)
    hero_path = os.path.join(FIG_DIR, "star_audit_architecture_hero_v3.png")
    schematic_img = plt.imread(hero_path)
    ax_a.imshow(schematic_img, aspect="equal")
    ax_a.axis("off")
    ax_a.set_title(
        "End-to-End Multi-Agent Discovery Workflow, Six External-Truth Audit Sensors, and Four Off-the-Data-Path Rectifiers",
        fontsize=9.4, fontweight="bold", loc="left", pad=8,
    )

    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.18, 1.12, 0.95], wspace=0.44)

    # Panel B: Per-Call Reasoning vs Visible Output Token Violins (Clean Stage Names)
    ax_b = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_b, "B", x=-0.18, y=1.12)
    stage_order = [
        "T1_Screening",
        "T2_Judging",
        "Step1_3_Ideation",
        "Domain14_Citation",
        "Step6_Citations",
        "HPO_GLM",
        "HPO_DeepSeek",
    ]
    stage_labels = [
        "Step 2: Single-Order T1 (n=4,127)",
        "Step 4: Bidirectional T2 (n=3,465)",
        "Steps 1 & 3: Ideation/Dossier (n=193)",
        "14-Domain Citation Trial (n=381)",
        "Step 6: Protocol Citations (n=105)",
        "120-Disease HPO: GLM-5.3 (n=527)",
        "120-Disease HPO: DeepSeek (n=277)",
    ]
    y_pos = np.arange(len(stage_order))
    rt_arrays = [np.array(raw["stage_rt"][k]) for k in stage_order]
    ans_meds = [float(np.median(raw["stage_ans"][k])) for k in stage_order]

    parts = ax_b.violinplot(rt_arrays, positions=y_pos, vert=False, widths=0.72,
                            showmeans=False, showextrema=False, showmedians=False)
    for pc in parts["bodies"]:
        pc.set_facecolor(C_BLUE)
        pc.set_edgecolor(C_NAVY)
        pc.set_alpha(0.45)
        pc.set_linewidth(0.8)

    for idx, arr in enumerate(rt_arrays):
        q25, med, q75 = np.percentile(arr, [25, 50, 75])
        ax_b.plot([q25, q75], [y_pos[idx], y_pos[idx]], color=C_NAVY, linewidth=2.5, zorder=4)
        ax_b.scatter([med], [y_pos[idx]], color="white", edgecolor=C_NAVY, s=26, linewidth=1.2, zorder=5,
                     label="Internal CoT Median & IQR" if idx == 0 else None)
        ax_b.scatter([ans_meds[idx]], [y_pos[idx]], color=C_AMBER, edgecolor="#222222", marker="D", s=24, zorder=6,
                     label="Visible Answer Median" if idx == 0 else None)
        ax_b.text(float(np.max(arr)) + 0.6, y_pos[idx], f"{med:.1f}k", va="center", fontsize=6.4, color=C_NAVY, fontweight="bold")

    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(stage_labels, fontsize=6.6)
    ax_b.set_xlabel("Per-Call Tokens (k; CoT = 35.58M [93.8%])", fontsize=7.8)
    ax_b.set_title("Per-Call CoT vs. Output Token Distributions", fontsize=8.4, fontweight="bold", loc="left")
    ax_b.set_xlim(0.0, 40.5)
    ax_b.set_ylim(-0.7, 7.6)
    style_ax(ax_b, grid_axis="x")
    ax_b.legend(loc="upper right", fontsize=6.1, frameon=False)

    # Panel C: Effect-Scaled 6-Member Confirmatory Hypothesis Scorecard (BH-FDR q = 0.05)
    ax_c = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_c, "C", x=-0.18, y=1.12)
    members = [
        "H5: Cross-Run vs. Bootstrap\nStability (dJ = -0.57)",
        "H1: Epistemic Citation Gate\n(RD = -54.5 pp, Fake 0%)",
        "H6: Confidence Calibration\nSlope != 1.0 (b = 0.655)",
        "H4: Blind vs. Retrieval\nLead-Gene Split (dJ = +0.09)",
        "H2: Pooled HPO Top-IC\nSlope (DS p = 0.026*)",
        "H3: HPO Arm x Dose\nInteraction (Starvation)",
    ]
    raw_p = [0.00020, 0.01032, 0.02004, 0.05605, 0.21906, 0.59481]
    bh_q = [0.00120, 0.03096, 0.04009, 0.08408, 0.26287, 0.59481]
    eff_sizes = [125, 115, 95, 72, 62, 50]
    neg_log_p = [-math.log10(p) for p in raw_p]
    neg_log_q = [-math.log10(q) for q in bh_q]

    y_m = np.arange(len(members))[::-1]
    thresh = -math.log10(0.05)
    ax_c.fill_betweenx([-0.7, 6.2], thresh, 5.3, color=C_TEAL, alpha=0.09, label="FDR Significant Zone (q < 0.05)")
    ax_c.axvline(thresh, color=C_VERM, linestyle="--", linewidth=1.1, label="Threshold (p, q = 0.05)")

    for idx, y in enumerate(y_m):
        ax_c.plot([0, neg_log_q[idx]], [y, y], color="#CCCCCC", linestyle=":", linewidth=1.0, zorder=2)
        ax_c.plot([neg_log_q[idx], neg_log_p[idx]], [y, y], color=C_NAVY, linewidth=2.3, zorder=3)
        ax_c.scatter([neg_log_p[idx]], [y], color=C_BLUE, s=eff_sizes[idx], marker="o", alpha=0.82,
                     edgecolor="#111111", linewidth=0.8, zorder=4, label=r"Raw $-\log_{10}(p)$ (Area = Effect)" if idx == 0 else None)
        ax_c.scatter([neg_log_q[idx]], [y], color=C_TEAL, s=52, marker="D", edgecolor="#111111", linewidth=0.8, zorder=5,
                     label=r"BH-FDR $-\log_{10}(q)$" if idx == 0 else None)
        q_val = bh_q[idx]
        status = f"q={q_val:.4f}*" if q_val < 0.05 else f"q={q_val:.3f}"
        ax_c.text(max(neg_log_p[idx], neg_log_q[idx]) + 0.14, y, status, va="center", fontsize=6.5,
                  fontweight="bold" if q_val < 0.05 else "normal",
                  color=C_VERM if q_val < 0.05 else "#444444")

    ax_c.set_yticks(y_m)
    ax_c.set_yticklabels(members, fontsize=6.5)
    ax_c.set_xlabel(r"Evidence ($-\log_{10} p$ & $-\log_{10} q_{\mathrm{BH}}$)", fontsize=7.8)
    ax_c.set_title("Confirmatory Hypothesis Family (BH-FDR)", fontsize=8.4, fontweight="bold", loc="left")
    ax_c.set_xlim(0, 5.3)
    ax_c.set_ylim(-0.7, 5.8)
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="lower right", fontsize=5.8, frameon=False)

    # Panel D: Six-Dimension Polar Radar Chart
    ax_d = fig.add_subplot(gs_bot[0, 2], projection="polar")
    ax_d.text(-0.22, 1.15, "D", transform=ax_d.transAxes, fontsize=11, fontweight="bold", va="top", ha="left", color="#111111")
    radar_labels = [
        "Dim 1: Verified\nCitations (%)",
        "Dim 2: Pathway\nConcordance (%)",
        "Dim 3: T2 Order\nConsistency (%)",
        "Dim 4: T1 Bucket-3\nParity (%)",
        "Dim 5: Judge NLI\nCoherence (%)",
        "Dim 6: Calibration\nAccuracy (%)",
    ]
    unrect_scores = [42.6, 20.5, 57.0, 40.0, 74.6, 77.8]
    rect_scores = [100.0, 48.3, 100.0, 72.5, 90.0, 97.3]

    angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
    angles += angles[:1]
    u_plot = unrect_scores + unrect_scores[:1]
    r_plot = rect_scores + rect_scores[:1]

    ax_d.set_theta_offset(np.pi / 2)
    ax_d.set_theta_direction(-1)
    ax_d.set_xticks(angles[:-1])
    ax_d.set_xticklabels(radar_labels, fontsize=6.0, fontweight="bold", color="#222222")
    ax_d.tick_params(axis="x", pad=14)
    ax_d.set_rlabel_position(30)
    ax_d.set_yticks([25, 50, 75, 100])
    ax_d.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=5.8, color="#555555")
    ax_d.set_ylim(0, 112)

    ax_d.plot(angles, u_plot, "-o", linewidth=1.9, color=C_VERM, markersize=4.5, label="Unrectified (54.3%)")
    ax_d.fill(angles, u_plot, color=C_VERM, alpha=0.18)
    ax_d.plot(angles, r_plot, "-s", linewidth=2.1, color=C_TEAL, markersize=4.5, label="STAR-Audit (92.4%)")
    ax_d.fill(angles, r_plot, color=C_TEAL, alpha=0.22)
    ax_d.set_title("Six-Dimension Trustworthiness Radar", fontsize=8.3, fontweight="bold", pad=16)
    ax_d.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=6.0, frameon=False)

    save_fig(fig, "Fig1_Audit_Remediation_Architecture")


# ==============================================================================
# FIGURE 2 (5 panels, 2+3 Asymmetric GridSpec):
#   2A: Two-Tier Alluvial Split + 12-Run & 14-Domain Individual Jittered Dots
#   2B: 12-Run Discovery Step-6 Replicate Strip & Boxplot (Blind vs Retrieval)
#   2C: 14-Domain x 3-Arm Randomized Trial Heatmap (Clean Domain Names)
#   2D: Pure GLM-5.3 Citation CoT Phase Plane (Zero Dual-Axis Mixing!)
#   2E: 5-Model Closed-Loop Trajectory (Module 3a Safety -> Module 3b 100% Yield)
# ==============================================================================
def make_fig2(s1, a2, ex, expB_slots, raw):
    fig = plt.figure(figsize=(14.4, 9.8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.0, 1.12], hspace=0.46)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.36)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.02, 1.05, 1.05], wspace=0.40)

    # Panel A: Alluvial Split + 26 Run/Domain Individual Scatter Dots
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A", x=-0.13, y=1.10)
    x_left, x_right = 0.18, 0.82
    bar_w = 0.14

    ax_a.fill_between([x_left - bar_w / 2, x_left + bar_w / 2], 0, 97.56, color=C_SKY, edgecolor="#111111", lw=1.0, zorder=3)
    ax_a.fill_between([x_left - bar_w / 2, x_left + bar_w / 2], 97.56, 100.0, color=C_RED_DARK, edgecolor="#111111", lw=1.0, zorder=3)
    ax_a.fill_between([x_right - bar_w / 2, x_right + bar_w / 2], 0, 42.18, color=C_TEAL, edgecolor="#111111", lw=1.0, zorder=3)
    ax_a.fill_between([x_right - bar_w / 2, x_right + bar_w / 2], 42.18, 97.56, color=C_AMBER, edgecolor="#111111", lw=1.0, zorder=3)
    ax_a.fill_between([x_right - bar_w / 2, x_right + bar_w / 2], 97.56, 100.0, color=C_RED_DARK, edgecolor="#111111", lw=1.0, zorder=3)

    draw_alluvial_ribbon(ax_a, x_left + bar_w / 2, x_right - bar_w / 2, 0, 42.18, 0, 42.18, C_TEAL, alpha=0.35)
    draw_alluvial_ribbon(ax_a, x_left + bar_w / 2, x_right - bar_w / 2, 42.18, 97.56, 42.18, 97.56, C_AMBER, alpha=0.48)
    draw_alluvial_ribbon(ax_a, x_left + bar_w / 2, x_right - bar_w / 2, 97.56, 100.0, 97.56, 100.0, C_RED_DARK, alpha=0.62)

    # Overlay 12 Discovery Runs & 14 Clinical Domains individual Tier-1 valid % and Tier-2 verified %
    rng_a = np.random.default_rng(101)
    p12_t1 = np.array(ex["fig2a_dots"]["parent_12_tier1_valid_pct"])
    p12_t2 = np.array(ex["fig2a_dots"]["parent_12_tier2_verified_pct"])
    b14_t1 = np.array(ex["fig2a_dots"]["expb_14_tier1_valid_pct"])
    b14_t2 = np.array(ex["fig2a_dots"]["expb_14_tier2_verified_pct"])
    ax_a.scatter(x_left - 0.10 + rng_a.uniform(-0.02, 0.02, len(p12_t1)), p12_t1, color=C_NAVY, s=22, alpha=0.75, zorder=5,
                 label="12 Discovery Runs (Step 6)")
    ax_a.scatter(x_right + 0.10 + rng_a.uniform(-0.02, 0.02, len(p12_t2)), p12_t2, color=C_NAVY, s=22, alpha=0.75, zorder=5)
    ax_a.scatter(x_left - 0.10 + rng_a.uniform(-0.02, 0.02, len(b14_t1)), b14_t1, color=C_BLUE, marker="s", s=20, alpha=0.75, zorder=5,
                 label="14 Clinical Domains (Ungated)")
    ax_a.scatter(x_right + 0.10 + rng_a.uniform(-0.02, 0.02, len(b14_t2)), b14_t2, color=C_BLUE, marker="s", s=20, alpha=0.75, zorder=5)

    ax_a.text(x_left, 50.0, "Apparent Valid\n98.3% / 96.9%", ha="center", va="center", fontsize=6.5, fontweight="bold", color="#111111", zorder=6)
    ax_a.text(0.50, 70.0, "Trojan Horse PMIDs\n56.7% (204) / 54.3% (228)", ha="center", va="center", fontsize=6.7, fontweight="bold", color="#7A4900", zorder=6)
    ax_a.text(0.50, 21.0, "Verified On-Topic\n41.7% (150) / 42.6% (179)", ha="center", va="center", fontsize=6.5, fontweight="bold", color="#005A40", zorder=6)
    ax_a.text(0.50, 105.5, "Fake Non-Existent PMID: 1.7% / 3.1% -> Total Ungrounded: 58.3% / 57.4%", ha="center", va="center", fontsize=6.3, fontweight="bold", color=C_RED_DARK)

    ax_a.set_xticks([x_left, x_right])
    ax_a.set_xticklabels(["Tier-1 Check\n(PMID Existence Only)", "Tier-2 Semantic Check\n(Claim-Abstract Match)"], fontsize=7.4, fontweight="bold")
    ax_a.set_ylabel("Share of Emitted Citations (%)", fontsize=8)
    ax_a.set_xlim(0.0, 1.0)
    ax_a.set_ylim(0, 124)
    ax_a.set_title("Two-Tier Entrez Split + Per-Run/Domain Dispersion (n = 780 Slots)", fontsize=8.5, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper left", ncol=2, fontsize=6.0, frameon=False)

    # Panel B: 12-Run Step-6 Replicate Strip & Boxplot
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B", x=-0.14, y=1.10)
    by_run_p = s1["parent_runs_dimension1"]["by_run"]
    cells_order = [
        ("dAMD_blind", "dAMD Blind\n(n=90 slots)"),
        ("dAMD_retrieval", "dAMD Retrieval\n(n=90 slots)"),
        ("ALS_blind", "ALS Blind\n(n=90 slots)"),
        ("ALS_retrieval", "ALS Retrieval\n(n=90 slots)"),
    ]
    x_cells = np.arange(len(cells_order))
    for idx, (prefix, lbl) in enumerate(cells_order):
        r_ung = [by_run_p[f"{prefix}_R{r}"]["ungrounded_rate_all_slots"] * 100.0 for r in [1, 2, 3]]
        r_on = [(1.0 - by_run_p[f"{prefix}_R{r}"]["ungrounded_rate_all_slots"]) * 100.0 for r in [1, 2, 3]]
        r_fake = [by_run_p[f"{prefix}_R{r}"]["fabrication_rate_all_slots"] * 100.0 for r in [1, 2, 3]]
        jit = np.array([-0.07, 0.0, 0.07])

        ax_b.boxplot([r_ung], positions=[idx - 0.14], widths=0.18, showfliers=False, manage_ticks=False,
                     boxprops=dict(color=C_VERM, lw=0.9), medianprops=dict(color=C_VERM, lw=1.4),
                     whiskerprops=dict(color=C_VERM, lw=0.8), capprops=dict(color=C_VERM, lw=0.8))
        ax_b.boxplot([r_on], positions=[idx + 0.14], widths=0.18, showfliers=False, manage_ticks=False,
                     boxprops=dict(color=C_TEAL, lw=0.9), medianprops=dict(color=C_TEAL, lw=1.4),
                     whiskerprops=dict(color=C_TEAL, lw=0.8), capprops=dict(color=C_TEAL, lw=0.8))
        ax_b.scatter(idx + jit - 0.14, r_ung, color=C_VERM, s=36, edgecolor="#111111", lw=0.7, zorder=4,
                     label="Total Ungrounded % (R1-R3)" if idx == 0 else None)
        ax_b.text(idx - 0.14, max(r_ung) + 5.0, f"{np.mean(r_ung):.1f}%", ha="center", fontsize=6.5, fontweight="bold", color=C_VERM)
        ax_b.scatter(idx + jit + 0.14, r_on, color=C_TEAL, s=36, marker="s", edgecolor="#111111", lw=0.7, zorder=4,
                     label="Verified On-Topic % (R1-R3)" if idx == 0 else None)
        ax_b.text(idx + 0.14, min(r_on) - 8.5, f"{np.mean(r_on):.1f}%", ha="center", fontsize=6.5, fontweight="bold", color=C_TEAL)
        ax_b.scatter(idx + jit, r_fake, color=C_RED_DARK, s=28, marker="^", edgecolor="#111111", lw=0.6, zorder=4,
                     label="Non-Existent PMID % (1.7%)" if idx == 0 else None)

    ax_b.set_xticks(x_cells)
    ax_b.set_xticklabels([c[1] for c in cells_order], fontsize=7.1, fontweight="bold")
    ax_b.set_ylabel("Step-6 Protocol Citation Rate (%)", fontsize=8)
    ax_b.set_xlim(-0.5, 3.5)
    ax_b.set_ylim(-8, 118)
    ax_b.set_title("12-Run Discovery Step-6 Grounding (Upstream Retrieval Unprotective)", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper left", fontsize=6.1, frameon=False)

    # Panel C: 14-Domain x 3-Arm Randomized Trial Heatmap (Clean Clinical Names)
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C", x=-0.22, y=1.10)
    clean_dom_names = [
        "Asthma", "Osteoarthritis", "Atrial Fibrillation", "Psoriasis",
        "Sensorineural Hearing", "Sickle Cell Anemia", "Cleft Palate",
        "Cholangiocarcinoma", "Gaucher Disease", "Cornelia de Lange",
        "Nephrogenic DI", "Buruli Ulcer", "Leber Amaurosis",
        "Pelizaeus-Merzbacher", "14-Domain Mean",
    ]
    mat_c = np.zeros((15, 3))
    for i in range(1, 15):
        did = f"B{i:02d}"
        for c_j, arm_k in enumerate(["as_discovered", "abstain_probe", "gated"]):
            sub = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == arm_k]
            mat_c[i - 1, c_j] = sum(1 for r in sub if r["ungrounded"]) / 30.0 * 100.0
    mat_c[14, :] = [57.38, 18.10, 2.86]

    ax_c.imshow(mat_c, cmap="YlOrRd", aspect="auto", vmin=0, vmax=80)
    for r_i in range(15):
        for c_j in range(3):
            val = mat_c[r_i, c_j]
            ax_c.text(c_j, r_i, f"{val:.1f}%", ha="center", va="center", fontsize=5.8,
                      color="white" if val >= 45 else "#111111", fontweight="bold" if r_i == 14 else "normal")
    ax_c.set_xticks([0, 1, 2])
    ax_c.set_xticklabels(["Ungated\n(3.1% Fake)", "Abstain\n(0.5% Fake)", "Module 3a\n(0.0% Fake*)"], fontsize=6.6, fontweight="bold")
    ax_c.set_yticks(np.arange(15))
    ax_c.set_yticklabels(clean_dom_names, fontsize=5.9)
    ax_c.set_title("14-Domain Trial (RD = -54.5 pp, p = 0.00097)", fontsize=8.1, fontweight="bold", loc="left")
    ax_c.spines["top"].set_visible(False)
    ax_c.spines["right"].set_visible(False)

    # Panel D: Pure GLM-5.3 Citation CoT Phase Plane (100% Pure Token X-Axis!)
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D", x=-0.16, y=1.10)
    arm_specs = [
        ("as_discovered", "Ungated (35.8 PMIDs/call)", C_VERM, "o"),
        ("abstain_probe", "Abstain-Probe (25.4/call)", C_AMBER, "s"),
        ("gated", "Module 3a Gate (5.0/call)", C_TEAL, "D"),
    ]
    centroids = []
    ax_d.fill_between([0.0, 3.8], -5.0, 15.0, color=C_TEAL, alpha=0.10, zorder=1, label="Low-Error / Low-Spin Zone")
    for arm_key, arm_lbl, col, mk in arm_specs:
        xs, ys = [], []
        for i in range(1, 15):
            did = f"B{i:02d}"
            sub = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == arm_key]
            xs.append(float(np.median(raw["expB_dom_arm_rt"][(did, arm_key)])))
            ys.append(sum(1 for r in sub if r["ungrounded"]) / 30.0 * 100.0)
        xs, ys = np.array(xs), np.array(ys)
        ax_d.scatter(xs, ys, color=col, alpha=0.45, s=30, marker=mk, edgecolor="none", zorder=3)
        cx, cy = float(np.median(raw["expB_arm_rt"][arm_key])), float(np.mean(ys))
        centroids.append((cx, cy))
        q25_x, q75_x = np.percentile(xs, [25, 75])
        q25_y, q75_y = np.percentile(ys, [25, 75])
        ax_d.errorbar(
            [cx], [cy],
            xerr=[[max(0.0, cx - q25_x)], [max(0.0, q75_x - cx)]],
            yerr=[[max(0.0, cy - q25_y)], [max(0.0, q75_y - cy)]],
            fmt=mk, color=col, ecolor=col, elinewidth=1.8, capsize=2.5, markersize=8.5,
            markeredgecolor="#111111", zorder=5, label=f"{arm_lbl}: {cy:.1f}%",
        )

    ax_d.annotate("", xy=(centroids[1][0] + 0.35, centroids[1][1] + 2.0), xytext=(centroids[0][0] - 0.35, centroids[0][1] - 2.0),
                  arrowprops=dict(arrowstyle="->", lw=1.7, linestyle="--", color=C_NAVY))
    ax_d.annotate("", xy=(centroids[2][0] + 0.45, centroids[2][1] + 1.5), xytext=(centroids[1][0] - 0.45, centroids[1][1] - 1.5),
                  arrowprops=dict(arrowstyle="->", lw=1.7, linestyle="--", color=C_TEAL))
    ax_d.text(7.2, 6.5, "-90.41% Median CoT\n(11.80k -> 1.13k)", fontsize=6.3, fontweight="bold", color=C_TEAL)

    ax_d.set_xlabel("Per-Call Citation CoT Compute (k Tokens)", fontsize=7.8)
    ax_d.set_ylabel("Domain Ungrounded Citation Rate (%)", fontsize=7.8)
    ax_d.set_xlim(-0.5, 16.8)
    ax_d.set_ylim(-5, 114)
    ax_d.set_title("GLM-5.3 Phase Plane: Gating Halts PMID Dredging", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="upper left", fontsize=5.8, frameon=False)

    # Panel E: 5-Model Closed-Loop Safety-to-Yield Closure (Ungated -> Abstain -> 3a -> 3a+3b 100% Yield!)
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E", x=-0.16, y=1.10)
    sp = a2["honest_split_by_model_and_arm"]
    cl84 = a2["closed_loop_5model_matched84"]
    models_5 = [
        ("GLM-5.3 (n=420)", sp["GLM-5.3_ExpB_Full420"], 420, a2["closed_loop_glm_full420"]["closed_loop_verified_grounded_yield_pct"], C_NAVY, "o"),
        ("Gemini-4-Argon (n=84)", sp["Gemini-4-Argon-High"], 84, cl84["Gemini-4-Argon-High"]["post_handoff_verified_yield_pct"], C_BLUE, "^"),
        ("Gemini-3.8-Flash (n=84)", sp["Gemini-3.8-Flash"], 84, cl84["Gemini-3.8-Flash"]["post_handoff_verified_yield_pct"], C_PURPLE, "v"),
        ("Grok-4.7-High (n=84)", sp["Grok-4.7-High"], 84, cl84["Grok-4.7-High"]["post_handoff_verified_yield_pct"], C_AMBER, "P"),
        ("Grok-4.7-Fast (n=84)", sp["Grok-4.7-Fast"], 84, cl84["Grok-4.7-Fast"]["post_handoff_verified_yield_pct"], C_TEAL, "D"),
    ]
    xs_e = np.array([0, 1, 2, 3])
    ax_e.fill_between([2.0, 3.15], 0.0, 100.0, color=C_TEAL, alpha=0.08, zorder=1)
    for lbl, m_d, n_sl, cl_y, col, mk in models_5:
        ys_y = np.array([
            m_d["as_discovered"]["parametric_grounded_yield_pct"],
            m_d["abstain_probe"]["parametric_grounded_yield_pct"],
            m_d["gated"]["parametric_grounded_yield_pct"],
            cl_y,
        ])
        ses_y = np.array([100.0 * math.sqrt(max(0.0, (p / 100.0) * (1.0 - p / 100.0)) / n_sl) for p in ys_y])
        ax_e.errorbar(xs_e, ys_y, yerr=ses_y, fmt=f"-{mk}", color=col, ecolor=col, lw=1.8, elinewidth=1.0,
                      capsize=2.0, markersize=5.2, label=f"{lbl}: {ys_y[0]:.0f}%->{ys_y[2]:.0f}%->{ys_y[3]:.0f}%")

    ax_e.set_xticks(xs_e)
    ax_e.set_xticklabels(["Ungated\n(12-77% Err)", "Abstain\nProbe", "Module 3a\n(Safe Gate)", "Closed-Loop\n3a+3b (0% Err)"], fontsize=6.5, fontweight="bold")
    ax_e.set_ylabel("Verified On-Topic Citation Yield (%)", fontsize=7.8)
    ax_e.set_xlim(-0.25, 3.25)
    ax_e.set_ylim(-6, 136)
    ax_e.set_title("5-Model Closed-Loop Entrez Handoff (100% Yield)", fontsize=8.1, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="y")
    ax_e.legend(loc="upper left", fontsize=5.5, frameon=False)

    save_fig(fig, "Fig2_Dim1_Trojan_Horse_Citations")


# ==============================================================================
# FIGURE 3 (5 panels, 2+3 Asymmetric GridSpec):
#   3A: 12-Run x 12-Axis Pathway Convergence Heatmap (Clean Run Headers)
#   3B: Multi-Granularity Convergence Slopegraph + Boxplots + Pairwise Run Dots
#   3C: 120-Disease HPO Dose-Response + Module 4a Rescue + 4-Family Validation
#   3D: White-Box 2.1% CoT First-Mention Depth ECDF + Lit. Footprint Split
#   3E: Cross-Vendor Syndromic Decoy Attractor Matrix (n = 464 Misses)
# ==============================================================================
def make_fig3(s2, ex):
    fig = plt.figure(figsize=(14.4, 9.9))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.02, 1.12], hspace=0.46)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[1.14, 1.0], wspace=0.38)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.06, 1.04, 1.04], wspace=0.40)

    # Panel A: 12-Run x 12-Axis Pathway Convergence Heatmap
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A", x=-0.18, y=1.10)
    runs_ordered = [
        "dAMD_blind_R1", "dAMD_blind_R2", "dAMD_blind_R3",
        "dAMD_retrieval_R1", "dAMD_retrieval_R2", "dAMD_retrieval_R3",
        "ALS_blind_R1", "ALS_blind_R2", "ALS_blind_R3",
        "ALS_retrieval_R1", "ALS_retrieval_R2", "ALS_retrieval_R3",
    ]
    run_clean = [
        "dAMD\nBlind 1", "dAMD\nBlind 2", "dAMD\nBlind 3",
        "dAMD\nRetr 1", "dAMD\nRetr 2", "dAMD\nRetr 3",
        "ALS\nBlind 1", "ALS\nBlind 2", "ALS\nBlind 3",
        "ALS\nRetr 1", "ALS\nRetr 2", "ALS\nRetr 3",
    ]
    axes_list = [
        ("complement_Bruch_HS", "dAMD: Complement / Bruch HS *"),
        ("iron_ferroptosis_oxidative", "dAMD: Iron / Ferroptosis *"),
        ("parainflam_inflammasome_cell_death", "dAMD: NLRP3 / Pyroptosis *"),
        ("ECM_ARMS2_HTRA1", "dAMD: Bruch ECM / HTRA1 *"),
        ("lipid_cholesterol", "dAMD: Lipid / ABCA1 Efflux *"),
        ("cGAS_STING_Alu_innate", "dAMD: cGAS-STING / Lysosome"),
        ("TDP43_cryptic_splicing_STMN2_UNC13A", "ALS: TDP-43 / STMN2 / UNC13A *"),
        ("autophagy_mitophagy_TBK1_OPTN", "ALS: TBK1 / OPTN Mitophagy *"),
        ("axonal_ER_mito_lipid_NMJ", "ALS: Axonal / ER-Mito / NMJ *"),
        ("RNA_RNP_nucleolar_TDP43", "ALS: RNP / Nucleolar TDP-43 *"),
        ("ADAR2_GRIA2_RNA_editing", "ALS: ADAR2 / SOD1 / Excitotox *"),
        ("neuroinflammation_innate_immune", "ALS: Treg / C1q Neuroimmune"),
    ]
    profiles = s2["dimension_2_reasoning_vs_retrieval"]["per_run_top5_profiles"]
    mat = np.zeros((len(axes_list), len(runs_ordered)))
    for c_idx, r_name in enumerate(runs_ordered):
        ac = Counter(d["axis"] for d in profiles[r_name]["top5_details"])
        ac["cGAS_STING_Alu_innate"] += ac.get("lysosomal_autophagy", 0)
        ac["ADAR2_GRIA2_RNA_editing"] += ac.get("SOD1_proteostasis", 0)
        for r_idx, (ax_key, _) in enumerate(axes_list):
            if (r_idx < 6 and r_name.startswith("dAMD")) or (r_idx >= 6 and r_name.startswith("ALS")):
                mat[r_idx, c_idx] = ac.get(ax_key, 0)

    ax_a.imshow(mat, cmap="YlGnBu", aspect="auto", vmin=0, vmax=3)
    for r_i in range(mat.shape[0]):
        for c_i in range(mat.shape[1]):
            val = int(mat[r_i, c_i])
            if val > 0:
                ax_a.text(c_i, r_i, str(val), ha="center", va="center", fontsize=6.8, fontweight="bold",
                          color="white" if val >= 2 else "#111111")
    ax_a.axvline(5.5, color="#222222", linewidth=1.2)
    ax_a.axhline(5.5, color="#222222", linewidth=1.2)
    ax_a.set_xticks(np.arange(len(run_clean)))
    ax_a.set_xticklabels(run_clean, fontsize=5.6)
    ax_a.set_yticks(np.arange(len(axes_list)))
    ax_a.set_yticklabels([a[1] for a in axes_list], fontsize=6.1)
    ax_a.set_title("Pathway Axis Convergence Across 12 Discovery Runs (* = Gold Axis)", fontsize=8.4, fontweight="bold", loc="left")

    # Panel B: Multi-Granularity Convergence + Individual Pairwise Run Scatter
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B", x=-0.14, y=1.10)
    gran_x = np.array([0, 1, 2])
    gran_labels = ["Lead Target\nGene (HGNC)", "All Dossier\nTarget Genes", "Canonical Pathway\nAxis (Gold)"]
    pw = ex["fig3b_5a_pairwise"]
    als_within = [0.2037, 0.1721, 0.5722]
    als_cross = [0.0741, 0.0897, 0.4005]
    damd_within = [0.0926, 0.1563, 0.3944]
    damd_cross = [0.0370, 0.1502, 0.4725]

    rng_b = np.random.default_rng(202)
    for g_idx, gk in enumerate(["lead_genes", "all_genes", "axes"]):
        all_pts = (pw["ALS"][f"within_{gk}"] + pw["ALS"][f"cross_{gk}"]
                   + pw["dAMD"][f"within_{gk}"] + pw["dAMD"][f"cross_{gk}"])
        ax_b.boxplot([all_pts], positions=[g_idx], widths=0.20, showfliers=False, manage_ticks=False,
                     boxprops=dict(color="#999999", lw=0.8), medianprops=dict(color="#555555", lw=1.0),
                     whiskerprops=dict(color="#999999", lw=0.7), capprops=dict(color="#999999", lw=0.7))
        ax_b.scatter(g_idx - 0.06 + rng_b.uniform(-0.03, 0.03, 6), pw["ALS"][f"within_{gk}"],
                     color=C_NAVY, alpha=0.35, s=18, zorder=2)
        ax_b.scatter(g_idx + 0.06 + rng_b.uniform(-0.03, 0.03, 6), pw["dAMD"][f"within_{gk}"],
                     color=C_TEAL, alpha=0.35, s=18, marker="s", zorder=2)

    ax_b.fill_between(gran_x, als_cross, als_within, color=C_NAVY, alpha=0.10)
    ax_b.plot(gran_x, als_within, "-o", color=C_NAVY, lw=2.3, markersize=6.5, label="ALS Within-Arm (2.81x Surge)")
    ax_b.plot(gran_x, als_cross, "--o", color=C_BLUE, lw=1.7, markersize=5.0, label="ALS Cross-Arm (dJ = +0.130)")
    ax_b.plot(gran_x, damd_within, "-s", color=C_TEAL, lw=2.3, markersize=6.5, label="dAMD Within-Arm (4.26x Surge)")
    ax_b.plot(gran_x, damd_cross, "--s", color=C_VERM, lw=1.7, markersize=5.0, label="dAMD Cross-Arm (dJ = +0.056)")

    ax_b.set_xticks(gran_x)
    ax_b.set_xticklabels(gran_labels, fontsize=7.0, fontweight="bold")
    ax_b.set_ylabel("Pairwise Run Top-5 Jaccard Similarity", fontsize=8)
    ax_b.set_xlim(-0.32, 2.32)
    ax_b.set_ylim(-0.03, 0.92)
    ax_b.set_title("Multi-Scale Convergence Trajectory (Gene -> Module -> Axis)", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="upper left", fontsize=6.0, frameon=False)

    # Panel C: Pure HPO Dose-Response (0%, 25%, 50% IC Deleted) + Module 4a + 4-Family Validation
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C", x=-0.16, y=1.10)
    f3c_ex = ex["fig3c_exact"]
    doses = np.array([0, 25, 50])
    glm_top = np.array([f3c_ex["glm_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    ds_top = np.array([f3c_ex["deepseek_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    ds_srad = np.array([f3c_ex["deepseek_module4a_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    glm_se = np.array([f3c_ex["glm_del_topIC"][str(d)]["binomial_se_pct"] for d in [0, 25, 50]])
    ds_se = np.array([f3c_ex["deepseek_del_topIC"][str(d)]["binomial_se_pct"] for d in [0, 25, 50]])

    ax_c.fill_between(doses, glm_top - glm_se, glm_top + glm_se, color=C_BLUE, alpha=0.12)
    ax_c.fill_between(doses, ds_top - ds_se, ds_top + ds_se, color=C_VERM, alpha=0.14)
    ax_c.errorbar(doses, glm_top, yerr=glm_se, fmt="-o", color=C_BLUE, ecolor=C_BLUE, lw=2.0, elinewidth=0.9, capsize=2.2, markersize=5.0, label="GLM-5.3 Top-IC (34.5->30.6%)")
    ax_c.errorbar(doses, ds_top, yerr=ds_se, fmt="-D", color=C_VERM, ecolor=C_VERM, lw=2.0, elinewidth=0.9, capsize=2.2, markersize=5.0, label="DeepSeek-V4 Top-IC (28.3->14.3%*)")
    ax_c.plot(doses, ds_srad, "-s", color=C_TEAL, lw=2.1, markersize=5.2, label="DeepSeek + Module 4a (20.7->34.3%***)")
    ax_c.plot(doses, [65.0, 70.0, 60.0], "--^", color=C_NAVY, lw=1.6, markersize=4.6, label="Gemini-4-Argon (65.0% overall)")
    ax_c.plot(doses, [30.0, 30.0, 20.0], ":v", color=C_PURPLE, lw=1.5, markersize=4.6, label="Gemini-3.8-Flash (26.7% overall)")
    ax_c.plot(doses, [45.0, 30.0, 20.0], "-.P", color=C_AMBER, lw=1.6, markersize=4.8, label="Grok-4.7-High (31.7% overall)")
    ax_c.plot(doses, [40.0, 35.0, 35.0], ":X", color=C_SLATE, lw=1.5, markersize=4.6, label="Grok-4.7-Fast (36.7% overall)")

    ax_c.set_xticks([0, 25, 50])
    ax_c.set_xlim(-4, 54)
    ax_c.set_ylim(6, 122)
    ax_c.set_xlabel("High-IC HPO Phenotype Deletion Dose (%)", fontsize=7.8)
    ax_c.set_ylabel("Causal Gene Recall@10 (%)", fontsize=7.8)
    ax_c.set_title("120-Disease HPO Dose-Response & Module 4a Rescue", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper left", fontsize=5.3, frameon=False)

    # Panel D: White-Box 2.1% CoT Depth ECDF + High vs Low Literature Footprint
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D", x=-0.16, y=1.10)
    ec = ex["fig3d_cot_depth_ecdf"]
    h_v = np.array(ec["hits_sorted_pct"])
    p_v = np.array(ec["self_pruned_sorted_pct"])
    c_v = np.array(ec["ceiling_ghost_sorted_pct"])

    ax_d.fill_betweenx([0, 1.02], 0, 5.0, color=C_TEAL, alpha=0.11, label="<=5% Instant-Recognition Window")
    ax_d.step(h_v, np.arange(1, len(h_v) + 1) / len(h_v), where="post", color=C_TEAL, lw=2.2,
              label=f"Baseline Hits (n={len(h_v)}, Med=2.1%)")
    ax_d.step(c_v, np.arange(1, len(c_v) + 1) / len(c_v), where="post", color=C_BLUE, linestyle="--", lw=1.9,
              label=f"32k Ceiling Ghosts (n={len(c_v)}, Med={ec['ceiling_ghost_median_pct']:.1f}%)")
    ax_d.step(p_v, np.arange(1, len(p_v) + 1) / len(p_v), where="post", color=C_VERM, linestyle="-.", lw=1.9,
              label=f"Self-Pruned Misses (n={len(p_v)}, 23.3% FN)")

    ax_d.errorbar([62.0, 84.0], [0.382, 0.232], yerr=[0.036, 0.032], fmt="o-", color=C_NAVY, ecolor=C_NAVY,
                  lw=1.6, elinewidth=1.0, capsize=2.2, markersize=5.0, label="GLM High vs. Low Lit. Footprint*")
    ax_d.errorbar([62.0, 84.0], [0.244, 0.169], yerr=[0.037, 0.032], fmt="D:", color=C_AMBER, ecolor=C_AMBER,
                  lw=1.5, elinewidth=1.0, capsize=2.2, markersize=4.8, label="DeepSeek High vs. Low Lit. Footprint")
    ax_d.text(73.0, 0.45, "Lit. Footprint\n(p = 0.011*)", ha="center", fontsize=5.8, fontweight="bold", color=C_NAVY)

    ax_d.set_xlabel("Normalized CoT Depth of 1st Causal Gene (%)", fontsize=7.8)
    ax_d.set_ylabel("Cumulative Fraction / Recall Fraction", fontsize=7.8)
    ax_d.set_xlim(0, 96)
    ax_d.set_ylim(0, 1.42)
    ax_d.set_title("White-Box 2.1% Recognition ECDF & Self-Pruning", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="upper left", fontsize=5.2, frameon=False)

    # Panel E: Top 10 Cross-Vendor Syndromic Decoy Attractors
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E", x=-0.16, y=1.10)
    dec10 = ex["fig3d_decoys"][::-1]
    genes_d = [d["gene"] for d in dec10]
    glm_d = [d["glm_false_calls"] for d in dec10]
    ds_d = [d["deepseek_false_calls"] for d in dec10]
    totals_d = [d["total_false_calls"] for d in dec10]
    n_dis = [d["n_diseases"] for d in dec10]

    y_d = np.arange(len(genes_d))
    ax_e.fill_betweenx([4.5, 9.6], 0, 48, color=C_PURPLE, alpha=0.07, zorder=1)
    mids_d = [0.5 * (ds_d[i] + glm_d[i]) for i in range(len(genes_d))]
    half_d = [0.5 * abs(ds_d[i] - glm_d[i]) for i in range(len(genes_d))]
    ax_e.errorbar(mids_d, y_d, xerr=half_d, fmt="none", ecolor="#888888", elinewidth=1.6, capsize=0, zorder=2)
    for i in range(len(genes_d)):
        ax_e.scatter([glm_d[i]], [y_d[i]], color=C_BLUE, s=40, marker="o", edgecolor="#111111", lw=0.6, zorder=4,
                     label="GLM-5.3 False Calls" if i == 0 else None)
        ax_e.scatter([ds_d[i]], [y_d[i]], color=C_VERM, s=40, marker="D", edgecolor="#111111", lw=0.6, zorder=4,
                     label="DeepSeek-V4 False Calls" if i == 0 else None)
        ax_e.scatter([totals_d[i]], [y_d[i]], color=C_PURPLE, s=totals_d[i] * 3.2, alpha=0.76, edgecolor="#111111", lw=0.8, zorder=5,
                     label="Total (Area = Disease Span)" if i == 0 else None)
        ax_e.text(totals_d[i] + 1.2, y_d[i], f"{totals_d[i]} ({n_dis[i]} dis.)", va="center", fontsize=6.0, fontweight="bold", color="#222222")

    ax_e.set_yticks(y_d)
    ax_e.set_yticklabels(genes_d, fontsize=6.8, fontweight="bold")
    ax_e.set_xlabel("False-Positive Calls in Missed Trials", fontsize=7.8)
    ax_e.set_xlim(0, 46)
    ax_e.set_ylim(-0.8, 11.6)
    ax_e.set_title("Syndromic Decoy Attractors (Hit@10 = 0)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="x")
    ax_e.legend(loc="lower right", fontsize=5.6, frameon=False)

    save_fig(fig, "Fig3_Dim2_Reasoning_vs_Memorization")


# ==============================================================================
# FIGURE 4 (5 panels, 2+3 Asymmetric GridSpec):
#   4A: 12-Run x 3-Persona Bidirectional Flip Forest (Clean Run Names)
#   4B: 3-Stage Bucket-Survival Alluvial + 12-Run Individual Survival Dots
#   4C: White-Box CoT Decile-1 Slot-A Attention Locking (7,592 Traces!)
#   4D: 200-Point Empirical DeBERTa-v3 NLI Contradiction Tail Curve (n = 480)
#   4E: Cross-Stage NLI Phase Space + Speech-Act Polarity Filter Vector
# ==============================================================================
def make_fig4(s2, s4, ex, raw):
    fig = plt.figure(figsize=(14.4, 9.9))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.04, 1.08], hspace=0.46)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[1.08, 1.0], wspace=0.38)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[0.98, 1.06, 1.06], wspace=0.40)

    # Panel A: 12-Run x 3-Persona Flip Forest
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A", x=-0.16, y=1.10)
    t2_runs = s2["dimension_3_position_bias"]["tournament_II_by_run"]
    runs_ord = [
        "dAMD_blind_R1", "dAMD_blind_R2", "dAMD_blind_R3",
        "dAMD_retrieval_R1", "dAMD_retrieval_R2", "dAMD_retrieval_R3",
        "ALS_blind_R1", "ALS_blind_R2", "ALS_blind_R3",
        "ALS_retrieval_R1", "ALS_retrieval_R2", "ALS_retrieval_R3",
    ][::-1]
    labels_ord = [
        r.replace("dAMD_blind_", "dAMD Blind ").replace("dAMD_retrieval_", "dAMD Retrieval ")
         .replace("ALS_blind_", "ALS Blind ").replace("ALS_retrieval_", "ALS Retrieval ")
        for r in runs_ord
    ] + ["Pooled (12 Runs)"]

    y_r = np.arange(len(labels_ord))
    ax_a.fill_betweenx([-0.8, 12.8], 40.0, 46.5, color=C_VERM, alpha=0.08, zorder=1)
    for idx, r_id in enumerate(runs_ord):
        pf = raw["persona_flips_by_run"][r_id]
        p1 = pf[1][0] / max(1, pf[1][1]) * 100.0
        p2 = pf[2][0] / max(1, pf[2][1]) * 100.0
        p3 = pf[3][0] / max(1, pf[3][1]) * 100.0
        p_all = t2_runs[r_id]["pos_bias_rate"] * 100.0
        lo_p, hi_p = min(p1, p2, p3), max(p1, p2, p3)
        ax_a.errorbar([p_all], [idx], xerr=[[p_all - lo_p], [hi_p - p_all]], fmt="none", ecolor="#AAAAAA", elinewidth=1.5, capsize=2.0, zorder=2)
        ax_a.scatter([p1], [idx], color=C_TEAL, s=28, marker="o", zorder=3, label="SCIENCE (40.0%)" if idx == 0 else None)
        ax_a.scatter([p2], [idx], color=C_BLUE, s=28, marker="s", zorder=3, label="METHODS (42.6%)" if idx == 0 else None)
        ax_a.scatter([p3], [idx], color=C_AMBER, s=32, marker="^", zorder=3, label="NOVELTY (46.5%)" if idx == 0 else None)
        ax_a.scatter([p_all], [idx], color=C_VERM, s=48, marker="D", edgecolor="#111111", lw=0.7, zorder=4,
                     label="Run Pooled (97.0% Slot-A)" if idx == 0 else None)

    idx_p = 12
    ax_a.errorbar([43.04], [idx_p], xerr=[[43.04 - 40.04], [46.46 - 43.04]], fmt="D", color=C_VERM,
                  ecolor=C_NAVY, elinewidth=2.2, capsize=2.5, markersize=7.5, markeredgecolor="#111111", zorder=5)
    ax_a.axvline(43.04, color=C_VERM, linestyle="--", linewidth=1.0, alpha=0.7)
    ax_a.text(48.0, idx_p, "43.0% Flipped (p = 4.6e-168)", va="center", fontsize=6.4, fontweight="bold", color=C_VERM)

    ax_a.set_yticks(y_r)
    ax_a.set_yticklabels(labels_ord, fontsize=6.4)
    ax_a.set_xlabel("Bidirectional A/B Verdict Flip Rate (%)", fontsize=8)
    ax_a.set_xlim(10, 84)
    ax_a.set_ylim(-0.8, 15.6)
    ax_a.set_title("Tournament II Flip Rate Across Runs & Personas (n = 1,601 Pairs)", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper right", ncol=2, fontsize=5.9, frameon=False)

    # Panel B: 3-Stage Bucket-Survival Alluvial + 12-Run Individual Bucket-3 Survival Dots
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B", x=-0.14, y=1.10)
    xs_st = [0.15, 0.50, 0.85]
    bw = 0.13
    stages_b = [[33.33, 33.33, 33.34], [65.00, 21.67, 13.33], [50.00, 25.83, 24.17]]
    b_cols = [C_NAVY, C_SKY, C_TEAL]
    b_names = ["Bucket 1 (M00-M09)\nCell-Intrinsic", "Bucket 2 (M10-M19)\nIntercellular", "Bucket 3 (M20-M29)\nECM / Complement"]

    cum_bounds = []
    for st_vals in stages_b:
        b0, bounds = 0.0, []
        for v in st_vals:
            bounds.append((b0, b0 + v))
            b0 += v
        cum_bounds.append(bounds)

    for st_i, x_c in enumerate(xs_st):
        for b_i in range(3):
            yb, yt = cum_bounds[st_i][b_i]
            ax_b.fill_between([x_c - bw / 2, x_c + bw / 2], yb, yt, color=b_cols[b_i], edgecolor="#111111", lw=1.0, zorder=3,
                              label=b_names[b_i] if st_i == 0 else None)
    for st_i in range(2):
        for b_i in range(3):
            y0b, y0t = cum_bounds[st_i][b_i]
            y1b, y1t = cum_bounds[st_i + 1][b_i]
            draw_alluvial_ribbon(ax_b, xs_st[st_i] + bw / 2, xs_st[st_i + 1] - bw / 2, y0b, y0t, y1b, y1t, b_cols[b_i], alpha=0.36)

    t1_adj = s2["audit_guided_rectification"]["tournament_I_order_adjusted_btl"]
    rng_4b = np.random.default_rng(402)
    b1_raw_12 = [t1_adj[r]["raw_top10_decades"][0] * 10.0 for r in runs_ord]
    b1_adj_12 = [t1_adj[r]["adj_top10_decades"][0] * 10.0 for r in runs_ord]
    ax_b.scatter(xs_st[1] + 0.095 + rng_4b.uniform(-0.015, 0.015, 12), b1_raw_12, color=C_VERM, s=18, alpha=0.75, zorder=5)
    ax_b.scatter(xs_st[2] + 0.095 + rng_4b.uniform(-0.015, 0.015, 12), b1_adj_12, color=C_TEAL, s=18, marker="D", alpha=0.75, zorder=5)

    ax_b.text(xs_st[0], 16.5, "33.3%", ha="center", va="center", fontsize=6.2, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[0], 50.0, "33.3%", ha="center", va="center", fontsize=6.2, color="#111111", fontweight="bold", zorder=6)
    ax_b.text(xs_st[0], 83.3, "33.3%", ha="center", va="center", fontsize=6.2, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[1], 32.5, "65.0%\n(78)", ha="center", va="center", fontsize=6.2, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[1], 93.3, "13.3%", ha="center", va="center", fontsize=6.0, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[1], 104.0, "Chi2 = 55.4***", ha="center", fontsize=6.1, fontweight="bold", color=C_VERM)
    ax_b.text(xs_st[2], 25.0, "50.0%\n(60)", ha="center", va="center", fontsize=6.2, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[2], 87.9, "24.2%\n(+81%)", ha="center", va="center", fontsize=6.0, color="white", fontweight="bold", zorder=6)
    ax_b.text(xs_st[2], 104.0, "-72.8% Skew", ha="center", fontsize=6.1, fontweight="bold", color=C_TEAL)

    ax_b.set_xticks(xs_st)
    ax_b.set_xticklabels(["Initial Pool\n(360 Cands)", "Unadjusted BTL\n(71.3% Slot-A)", "Order-Adj BTL\n(Rectified)"], fontsize=7.0, fontweight="bold")
    ax_b.set_ylabel("Surviving Top-10 Share (%)", fontsize=8)
    ax_b.set_xlim(0.0, 1.02)
    ax_b.set_ylim(0, 134)
    ax_b.set_title("Tournament I Bucket Extinction & OA-BTL Rescue", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper left", ncol=3, fontsize=5.7, frameon=False)

    # Panel C: White-Box CoT Decile-by-Decile Slot-A Attention Trajectory
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C", x=-0.16, y=1.10)
    att = ex["fig4c_cot_attention"]
    dec_x = np.arange(1, 11)
    t1_att = np.array(att["t1_deciles_pct"])
    t2_att = np.array(att["t2_deciles_pct"])

    ax_c.fill_between(dec_x, 50.0, np.maximum(50.0, t2_att), color=C_VERM, alpha=0.18, label="Decile-1 Slot-A Attention Spike")
    ax_c.axhline(50.0, color="#555555", linestyle="--", lw=1.1, label="Symmetric Attention (50.0%)")
    ax_c.plot(dec_x, t1_att, "-o", color=C_BLUE, lw=2.1, markersize=5.2, label=f"Tournament I (n={att['t1_n_traces']:,}: D1=88.4%)")
    ax_c.plot(dec_x, t2_att, "-D", color=C_VERM, lw=2.1, markersize=5.2, label=f"Tournament II (n={att['t2_n_traces']:,}: D1=90.6%)")
    ax_c.text(2.2, 88.5, "88.4%-90.6%\nSlot-A Anchor", fontsize=6.2, fontweight="bold", color=C_VERM)

    ax_c.set_xticks([1, 2, 4, 6, 8, 10])
    ax_c.set_xlabel("Reasoning Trace Decile (1 = Start, 10 = End)", fontsize=7.8)
    ax_c.set_ylabel("Slot-A Entity Mention Share (%)", fontsize=7.8)
    ax_c.set_xlim(0.6, 10.4)
    ax_c.set_ylim(25, 118)
    ax_c.set_title("White-Box CoT Slot-A Attention Locking", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper right", fontsize=5.5, frameon=False)

    # Panel D: Exact 200-Point Empirical DeBERTa-v3 NLI Contradiction Tail Curve
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D", x=-0.16, y=1.10)
    f4c_ex = ex["fig4c_exact"]
    tau = np.array(f4c_ex["taus"], dtype=float)
    c_dir = np.array(f4c_ex["cons_dir_pct"], dtype=float)
    b_dir = np.array(f4c_ex["biased_dir_pct"], dtype=float)
    c_bi = np.array(f4c_ex["cons_bidir_pct"], dtype=float)
    b_bi = np.array(f4c_ex["biased_bidir_pct"], dtype=float)

    ax_d.fill_between(tau, c_dir, b_dir, step="post", color=C_PURPLE, alpha=0.22, label="Flipped Rationale Excess Area")
    ax_d.step(tau, b_dir, where="post", color=C_VERM, lw=2.1, label="Flipped: Directional (25.4% at 0.75)")
    ax_d.step(tau, c_dir, where="post", color=C_TEAL, lw=2.0, label="Consistent: Directional (10.0% at 0.75)")
    ax_d.step(tau, b_bi, where="post", linestyle="--", color=C_PURPLE, lw=1.7, label="Flipped: Bidirectional (7.1% at 0.75)")
    ax_d.step(tau, c_bi, where="post", linestyle="--", color=C_BLUE, lw=1.6, label="Consistent: Bidirectional (2.1%)")
    ax_d.plot([0.75, 0.75], [0, 62.0], color="#222222", linestyle=":", lw=1.1)
    ax_d.scatter([0.75, 0.75, 0.75, 0.75], [25.42, 10.00, 7.08, 2.08],
                 color=[C_VERM, C_TEAL, C_PURPLE, C_BLUE], s=42, edgecolor="#111111", zorder=5)
    ax_d.annotate("2.54x (p=1.15e-5)", xy=(0.75, 25.42), xytext=(0.28, 54.0),
                  fontsize=6.2, fontweight="bold", color=C_VERM, arrowprops=dict(arrowstyle="->", lw=0.9, color=C_VERM))

    ax_d.set_xlabel(r"DeBERTa-v3 NLI Threshold $\tau$", fontsize=7.8)
    ax_d.set_ylabel(r"Judge Pairs Exceeding $\tau$ (%)", fontsize=7.8)
    ax_d.set_xlim(0, 1.0)
    ax_d.set_ylim(0, 122)
    ax_d.set_title("Empirical Judge Rationale NLI Curve (n = 480)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="upper right", fontsize=5.4, frameon=False)

    # Panel E: 2D Cross-Stage NLI Phase Space + Speech-Act Polarity Filter Vector
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E", x=-0.16, y=1.10)
    by_run_nli = s4["cross_stage_coherence"]["by_run"]
    group_styles = [
        ("dAMD_blind", "dAMD Blind", C_BLUE, "o"),
        ("dAMD_retrieval", "dAMD Retrieval", C_TEAL, "s"),
        ("ALS_blind", "ALS Blind", C_VERM, "^"),
        ("ALS_retrieval", "ALS Retrieval", C_PURPLE, "D"),
    ]
    for prefix, glbl, col, mk in group_styles:
        for r in [1, 2, 3]:
            rid = f"{prefix}_R{r}"
            nr = by_run_nli[rid]
            xv, yv = nr["dir_contra_per_1k_pairs"], nr["bidir_contra_per_1k_pairs"]
            prop = nr["s13_contra_propagated_to_top5"]
            ax_e.scatter([xv], [yv], s=48 + prop * 32, color=col, alpha=0.78, marker=mk,
                         edgecolor="#111111", lw=0.8, zorder=4, label=glbl if r == 1 else None)

    ax_e.fill_between([0, 60.0], -6, 20.0, color=C_TEAL, alpha=0.09, zorder=1)
    ax_e.scatter([94.56], [28.88], color=C_RED_DARK, marker="X", s=80, edgecolor="#111111", zorder=6, label="Raw Mean (51/1,766)")
    ax_e.scatter([38.9], [11.89], color=C_TEAL, marker="*", s=110, edgecolor="#111111", zorder=6, label="Polarity-Gated (21/1,766)")
    ax_e.annotate("", xy=(43.0, 13.5), xytext=(90.0, 27.5),
                  arrowprops=dict(arrowstyle="->", lw=1.8, linestyle="--", color=C_TEAL))
    ax_e.text(132.0, 74.0, "43.1% Raw Reach Top-5\n-76% Polarity False Flags", fontsize=6.0, fontweight="bold", color=C_NAVY, va="top")

    ax_e.set_xlabel("Directional NLI Flags / 1,000 Pairs", fontsize=7.8)
    ax_e.set_ylabel("Bidirectional NLI Flags / 1,000", fontsize=7.8)
    ax_e.set_xlim(0, 275)
    ax_e.set_ylim(-6, 152)
    ax_e.set_title("Cross-Stage NLI & Speech-Act Gating", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="both")
    ax_e.legend(loc="upper left", ncol=1, fontsize=5.2, frameon=False)

    save_fig(fig, "Fig4_Dim3_Dim5_Primacy_and_NLI")


# ==============================================================================
# FIGURE 5 (4 panels, Asymmetric GridSpec):
#   5A: 10,000-Draw Verdict Bootstrap Violins + Individual Observed Pair Dots
#   5B: Multi-Model Calibration Curve & Selective Gate Centroids
#   5C: Per-Call CoT Violins for Paradoxes 1 & 2 (Clean Scientific Labels)
#   5D: Per-Call CoT Raincloud for Paradox 3 (1.4-1.7x Longer Failed Spin)
# ==============================================================================
def make_fig5(s2, s3, ex, raw):
    fig = plt.figure(figsize=(13.6, 9.4))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.02, 1.06], width_ratios=[1.08, 1.0], hspace=0.52, wspace=0.42)

    # Panel A: Verdict Bootstrap Violins + Individual Cross-Run Pairwise Observed Dots
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A", x=-0.15, y=1.10)
    boot_runs = s2["dimension_4_stability_bootstrap"]
    runs_12 = [
        "dAMD_blind_R1", "dAMD_blind_R2", "dAMD_blind_R3",
        "dAMD_retrieval_R1", "dAMD_retrieval_R2", "dAMD_retrieval_R3",
        "ALS_blind_R1", "ALS_blind_R2", "ALS_blind_R3",
        "ALS_retrieval_R1", "ALS_retrieval_R2", "ALS_retrieval_R3",
    ]
    clean_12 = [
        "dAMD\nB1", "dAMD\nB2", "dAMD\nB3", "dAMD\nR1", "dAMD\nR2", "dAMD\nR3",
        "ALS\nB1", "ALS\nB2", "ALS\nB3", "ALS\nR1", "ALS\nR2", "ALS\nR3",
    ]
    b_means = [boot_runs[r]["boot_pairwise_jaccard_mean"] for r in runs_12]
    b_lo = [boot_runs[r]["boot_pairwise_jaccard_95ci"][0] for r in runs_12]
    b_hi = [boot_runs[r]["boot_pairwise_jaccard_95ci"][1] for r in runs_12]
    boot_samples = [np.array(ex["fig5a_boot"][r]["empirical_jaccard_draws_1000"], dtype=float) for r in runs_12]

    x_12 = np.arange(len(runs_12))
    vparts = ax_a.violinplot(boot_samples, positions=x_12, vert=True, widths=0.65,
                             showmeans=False, showextrema=False, showmedians=False)
    for pc in vparts["bodies"]:
        pc.set_facecolor(C_SKY)
        pc.set_edgecolor(C_BLUE)
        pc.set_alpha(0.45)

    ax_a.errorbar(x_12, b_means, yerr=[[m - l for m, l in zip(b_means, b_lo)], [h - m for m, h in zip(b_means, b_hi)]],
                  fmt="o", color=C_NAVY, ecolor=C_BLUE, elinewidth=1.5, capsize=2.8, markersize=4.5, zorder=5,
                  label="10,000-Draw Verdict Bootstrap Null (Mean & 95% CI)")

    pw_d = ex["fig3b_5a_pairwise"]["dAMD"]["within_lead_genes"]
    pw_a = ex["fig3b_5a_pairwise"]["ALS"]["within_lead_genes"]
    ax_a.scatter([0.5, 1.5, 2.5, 3.5, 4.5, 5.0], pw_d, color=C_RED_DARK, marker="s", s=26, zorder=6,
                 label="Observed dAMD Pairwise Runs (Mean = 0.093)")
    ax_a.scatter([6.5, 7.5, 8.5, 9.5, 10.5, 11.0], pw_a, color=C_VERM, marker="^", s=28, zorder=6,
                 label="Observed ALS Pairwise Runs (Mean = 0.204)")
    ax_a.plot([-0.4, 5.4], [0.0926, 0.0926], color=C_RED_DARK, linestyle="--", lw=1.6)
    ax_a.plot([5.6, 11.4], [0.2037, 0.2037], color=C_VERM, linestyle="-", lw=1.6)
    ax_a.axvline(5.5, color="#888888", linestyle=":", lw=1.0)
    ax_a.text(5.5, 1.03, "Bootstrap p = 0.00020 (q = 0.00120*)", ha="center", fontsize=6.4, fontweight="bold", color=C_NAVY)

    ax_a.set_xticks(x_12)
    ax_a.set_xticklabels(clean_12, fontsize=6.0)
    ax_a.set_ylabel("Pairwise Top-5 Jaccard Similarity", fontsize=8)
    ax_a.set_ylim(-0.04, 1.48)
    ax_a.set_title("Verdict-Bootstrap Null Violins vs. Observed Cross-Run Pairs", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper left", fontsize=5.7, frameon=False)

    # Panel B: Confidence Calibration Reliability Curve
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B", x=-0.15, y=1.10)
    cal_p = s3["dim6_self_knowledge"]["parent_pooled_n480"]
    x_bef = np.array([b["mean_conf"] * 100 for b in cal_p["bins_before"]])
    y_bef = np.array([b["emp_acc"] * 100 for b in cal_p["bins_before"]])
    n_bef = [b["n"] for b in cal_p["bins_before"]]
    x_aft = np.array([b["mean_conf"] * 100 for b in cal_p["bins_after"]])
    y_aft = np.array([b["emp_acc"] * 100 for b in cal_p["bins_after"]])

    ax_b.plot([0, 100], [0, 100], linestyle="--", color="#555555", lw=1.3, label="Perfect Calibration (Slope = 1.0)")
    ax_b.fill_between(x_bef, y_bef, x_bef, color=C_VERM, alpha=0.16, label="Overconfidence Gap (ECE = 0.222)")
    ax_b.plot(x_bef, y_bef, "-o", lw=2.2, color=C_VERM, label=f"GLM-5.3 Raw Confidence (ECE = {cal_p['ece_before']:.3f})")
    ax_b.plot(x_aft, y_aft, "-s", lw=2.2, color=C_TEAL, label=f"Selective Platt Recalibrated (ECE = {cal_p['ece_after_loro_platt']:.3f})")

    ax_b.scatter([69.63, 80.90], [65.00, 26.67], color=C_PURPLE, marker="^", s=48, edgecolor="#111111", zorder=5,
                 label="Gemini Argon/Flash Raw (0.080 / 0.542)")
    ax_b.scatter([69.63, 26.67], [65.00, 26.67], color=C_BLUE, marker="D", s=42, edgecolor="#111111", zorder=5,
                 label="Gemini Selective Gate (0.080 / 0.075)")
    ax_b.scatter([54.58, 47.75], [31.67, 36.67], color=C_AMBER, marker="P", s=50, edgecolor="#111111", zorder=5,
                 label="Grok High/Fast Raw (0.229 / 0.165)")
    ax_b.scatter([31.67, 36.67], [31.67, 36.67], color=C_NAVY, marker="X", s=46, edgecolor="#111111", zorder=5,
                 label="Grok Selective Gate (0.104 / 0.081)")

    for xb_i, yb_i, nb_i in zip(x_bef, y_bef, n_bef):
        ax_b.annotate(f"n={nb_i}", (xb_i, yb_i), textcoords="offset points", xytext=(0, -11),
                      ha="center", fontsize=6.0, color=C_VERM, fontweight="bold")

    ax_b.set_xlabel("Predicted Survival / Recall Probability (%)", fontsize=8)
    ax_b.set_ylabel("Empirical Survival / Recall Rate (%)", fontsize=8)
    ax_b.set_xlim(0, 100)
    ax_b.set_ylim(-8, 130)
    ax_b.set_title("Verbalized Overconfidence & Selective Platt Calibration", fontsize=8.3, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="upper left", fontsize=5.3, frameon=False)

    # Panel C: Paradoxes 1 & 2 Horizontal Violins
    ax_c = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_c, "C", x=-0.18, y=1.10)
    c_arrays = [
        raw["t2_concordant_rt"],
        raw["t2_primacy_rt"],
        raw["expB_arm_rt"]["gated"],
        raw["expB_arm_rt"]["abstain_probe"],
        raw["expB_arm_rt"]["as_discovered"],
    ]
    c_labels = [
        "T2: Order-Consistent\n(n=1,824)",
        "T2: Slot-A Flipped\n(n=1,336)",
        "Citation: Module 3a Gate\n(n=70)",
        "Citation: Abstain-Probe\n(n=70)",
        "Citation: Ungated Baseline\n(n=70)",
    ]
    c_cols = [C_TEAL, C_VERM, C_TEAL, C_AMBER, C_RED_DARK]
    y_c = np.arange(len(c_arrays))

    vp_c = ax_c.violinplot(c_arrays, positions=y_c, vert=False, widths=0.72,
                           showmeans=False, showextrema=False, showmedians=False)
    for idx, pc in enumerate(vp_c["bodies"]):
        pc.set_facecolor(c_cols[idx])
        pc.set_edgecolor("#222222")
        pc.set_alpha(0.45)
        pc.set_linewidth(0.8)

    for idx, arr in enumerate(c_arrays):
        q25, med, q75 = np.percentile(arr, [25, 50, 75])
        ax_c.plot([q25, q75], [y_c[idx], y_c[idx]], color="#111111", lw=2.6, zorder=4,
                  label="Interquartile Range (25th-75th)" if idx == 0 else None)
        ax_c.scatter([med], [y_c[idx]], color="white", edgecolor=c_cols[idx], s=34, lw=1.4, zorder=5,
                     label="Group Median (k Tokens)" if idx == 0 else None)

    ax_c.plot([9.2, 9.8, 9.8, 9.2], [0.0, 0.0, 1.0, 1.0], color="#333333", lw=0.9)
    ax_c.text(10.2, 0.5, "p = 0.0254*", va="center", ha="left", fontsize=6.4, fontweight="bold", color=C_VERM)
    ax_c.axhline(1.5, color="#888888", linestyle="--", lw=0.9)
    ax_c.set_yticks(y_c)
    ax_c.set_yticklabels(c_labels, fontsize=6.8, fontweight="bold")
    ax_c.set_xlabel("Internal Reasoning Tokens per Call (k)", fontsize=8)
    ax_c.set_xlim(-0.5, 26.5)
    ax_c.set_ylim(-0.7, 4.7)
    ax_c.set_title("Paradoxes 1 & 2: CoT Spin in Flips & Citation Dredging", fontsize=8.3, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="lower right", fontsize=6.0, frameon=False)

    # Panel D: Paradox 3 Vertical Raincloud
    ax_d = fig.add_subplot(gs[1, 1])
    add_panel_label(ax_d, "D", x=-0.15, y=1.10)
    d_keys = [("glm", 1), ("glm", 0), ("deepseek", 1), ("deepseek", 0)]
    d_arrays = [raw["expC_rt_groups"][k] for k in d_keys]
    d_labels = ["GLM-5.3\nHit@10 = 1\n(n=110)", "GLM-5.3\nHit@10 = 0\n(n=249)",
                "DeepSeek-V4\nHit@10 = 1\n(n=56)", "DeepSeek-V4\nHit@10 = 0\n(n=215)"]
    d_cols = [C_TEAL, C_VERM, C_BLUE, C_RED_DARK]
    x_d = np.arange(len(d_arrays))

    vp_d = ax_d.violinplot(d_arrays, positions=x_d, vert=True, widths=0.65,
                           showmeans=False, showextrema=False, showmedians=False)
    for idx, pc in enumerate(vp_d["bodies"]):
        pc.set_facecolor(d_cols[idx])
        pc.set_edgecolor("#222222")
        pc.set_alpha(0.38)
        pc.set_linewidth(0.8)

    rng_d = np.random.default_rng(42)
    for idx, arr in enumerate(d_arrays):
        sub = arr if len(arr) <= 80 else rng_d.choice(arr, size=80, replace=False)
        ax_d.scatter(x_d[idx] + rng_d.uniform(-0.14, 0.14, size=len(sub)), sub, color=d_cols[idx], alpha=0.35, s=10, zorder=3)
        q25, med, q75 = np.percentile(arr, [25, 50, 75])
        ax_d.plot([x_d[idx], x_d[idx]], [q25, q75], color="#111111", lw=2.8, zorder=4)
        ax_d.scatter([x_d[idx]], [med], color="white", edgecolor=d_cols[idx], s=40, lw=1.5, zorder=5)
        ax_d.text(x_d[idx], float(np.max(arr)) + 1.2, f"{med:.1f}k", ha="center", fontsize=6.4, fontweight="bold", color=d_cols[idx])

    ax_d.plot([0, 0, 1, 1], [37.0, 40.2, 40.2, 38.0], color="#222222", lw=1.0)
    ax_d.text(0.5, 41.3, "p = 2.0e-16*** (1.70x)", ha="center", fontsize=6.4, fontweight="bold", color=C_VERM)
    ax_d.plot([2, 2, 3, 3], [37.0, 40.2, 40.2, 38.0], color="#222222", lw=1.0)
    ax_d.text(2.5, 41.3, "p = 1.4e-5*** (1.39x)", ha="center", fontsize=6.4, fontweight="bold", color=C_RED_DARK)

    ax_d.set_xticks(x_d)
    ax_d.set_xticklabels(d_labels, fontsize=6.8, fontweight="bold")
    ax_d.set_ylabel("Internal Reasoning Tokens per Call (k)", fontsize=8)
    ax_d.set_xlim(-0.6, 3.6)
    ax_d.set_ylim(0, 47.5)
    ax_d.set_title("Paradox 3: Failed Mendelian Calls Spin 1.4-1.7x Longer", fontsize=8.3, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="y")

    save_fig(fig, "Fig5_Dim4_Dim6_Reasoning_Paradox")


# ==============================================================================
# FIGURE 6 (5 panels, 2+3 Asymmetric GridSpec):
#   6A: Run-Level OA-BTL Primacy Log-Odds Intercepts (T1 & T2)
#   6B: 9 Gold-Standard Biological Pathways Rescued into Surviving Top-10
#   6C: Fair-Share Normalized Four-Pillar Paired Run/Domain Slopegraph + Boxplots
#   6D: Stepwise Cumulative Composite Score Progression (S_norm & S_raw)
#   6E: 2D Trustworthiness vs Citation Reasoning Compute Pareto Frontier
# ==============================================================================
def make_fig6(s2, a1, expB_slots):
    fig = plt.figure(figsize=(14.4, 9.9))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.05, 1.08], hspace=0.48)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[0.95, 1.12], wspace=0.44)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.12, 0.96, 1.02], wspace=0.40)

    # Panel A: OA-BTL Primacy Intercepts Across 12 Discovery Runs
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A", x=-0.16, y=1.10)
    t1_adj = s2["audit_guided_rectification"]["tournament_I_order_adjusted_btl"]
    t2_adj = s2["audit_guided_rectification"]["tournament_II_debiased_btl"]
    runs_12 = [
        "dAMD_blind_R1", "dAMD_blind_R2", "dAMD_blind_R3",
        "dAMD_retrieval_R1", "dAMD_retrieval_R2", "dAMD_retrieval_R3",
        "ALS_blind_R1", "ALS_blind_R2", "ALS_blind_R3",
        "ALS_retrieval_R1", "ALS_retrieval_R2", "ALS_retrieval_R3",
    ][::-1]
    labels_12 = [
        r.replace("dAMD_blind_", "dAMD Blind ").replace("dAMD_retrieval_", "dAMD Retrieval ")
         .replace("ALS_blind_", "ALS Blind ").replace("ALS_retrieval_", "ALS Retrieval ")
        for r in runs_12
    ]
    a1_emp = a1["A1_empirical_by_run"]
    g1 = [a1_emp[r]["gamma_t1_full_oa"] for r in runs_12]
    se1 = [a1_emp[r]["gamma_t1_full_se"] * 1.96 for r in runs_12]
    g2 = [t2_adj[r]["t2_gamma_primacy"] for r in runs_12]

    y_pos = np.arange(len(runs_12))
    ax_a.fill_betweenx([-0.8, 11.8], 0.99, 1.41, color=C_SKY, alpha=0.14, zorder=1)
    ax_a.fill_betweenx([-0.8, 11.8], 1.48, 1.93, color=C_VERM, alpha=0.10, zorder=1)
    ax_a.axvline(0.0, color="#222222", linestyle="--", lw=1.1, label="Fairness Null (gamma = 0)")
    ax_a.errorbar(g1, y_pos + 0.15, xerr=se1, fmt="o", color=C_BLUE, ecolor=C_SKY,
                  elinewidth=1.5, capsize=2.4, markersize=4.8, label=r"Tournament I $\hat{\gamma}_{\mathrm{T1}}$ (OR 1.8x-5.6x)")
    ax_a.scatter(g2, y_pos - 0.15, color=C_VERM, marker="D", s=30, zorder=4,
                 label=r"Tournament II $\hat{\gamma}_{\mathrm{T2}}$ (OR 3.7x-14.0x)")

    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(labels_12, fontsize=6.4)
    ax_a.set_xlabel(r"Estimated Slot-A Primacy Log-Odds Intercept ($\hat{\gamma}$)", fontsize=8)
    ax_a.set_xlim(-0.2, 3.1)
    ax_a.set_ylim(-0.8, 15.2)
    ax_a.set_title("OA-BTL Slot-A Primacy Intercepts Across 12 Runs", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper left", fontsize=5.9, frameon=False)

    # Panel B: 9 Gold-Standard Pathways Rescued into Surviving Top-10
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B", x=-0.16, y=1.10)
    rescued_examples = [
        ("dAMD Retr R1: M23 GAS6/MERTK Phagocytosis*", 11, 7),
        ("dAMD Retr R2: M25 TIMP3/MMP9 ECM Turnover*", 15, 8),
        ("dAMD Retr R3: M25 ABCA1/LIPC Lipid Efflux*", 15, 6),
        ("dAMD Retr R3: M14 CD59 MAC Protection*", 11, 5),
        ("dAMD Blind R1: M22 APOB100 Lipoprotein*", 12, 6),
        ("ALS Blind R1: M18 C1QA/C3 Neurotoxicity*", 13, 10),
        ("ALS Blind R2: M26 MMP9/LAMA1 NMJ Loss*", 13, 6),
        ("ALS Blind R3: M25 MCT1/SLC16A1 Lactate*", 11, 7),
        ("ALS Retr R3: M29 CCS/ATP7A Copper Axis*", 15, 10),
    ][::-1]
    y_res = np.arange(len(rescued_examples))
    raw_ranks = [x[1] for x in rescued_examples]
    adj_ranks = [x[2] for x in rescued_examples]

    ax_b.fill_betweenx([-0.8, 8.8], 0.5, 10.5, color=C_TEAL, alpha=0.11, label="Surviving Top-10 Dossier Cutoff (<=10)")
    ax_b.axvline(10.5, color=C_TEAL, linestyle="--", lw=1.3)
    for idx in range(len(rescued_examples)):
        ax_b.annotate("", xy=(adj_ranks[idx] + 0.32, y_res[idx]), xytext=(raw_ranks[idx] - 0.32, y_res[idx]),
                      arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=1.6))
        ax_b.text(raw_ranks[idx] + 0.55, y_res[idx], f"#{raw_ranks[idx]}", va="center", ha="right", fontsize=6.3, color=C_VERM, fontweight="bold")
        ax_b.text(adj_ranks[idx] - 0.55, y_res[idx], f"#{adj_ranks[idx]}", va="center", ha="left", fontsize=6.3, color=C_TEAL, fontweight="bold")
    ax_b.scatter(raw_ranks, y_res, color=C_VERM, s=52, zorder=4, label="Unadjusted BTL Rank (Eliminated >10)")
    ax_b.scatter(adj_ranks, y_res, color=C_TEAL, s=52, marker="D", zorder=4, label="Order-Adjusted BTL Rank (Rescued <=10)")

    ax_b.set_yticks(y_res)
    ax_b.set_yticklabels([x[0] for x in rescued_examples], fontsize=6.2, fontweight="bold")
    ax_b.set_xlabel("Tournament I Candidate Rank (1 = Best; <=10 Survives)", fontsize=8)
    ax_b.set_xlim(22.0, 2.2)
    ax_b.set_ylim(-0.8, 11.5)
    ax_b.set_title("OA-BTL Rescues 9/9 Gold-Standard Biological Pathways (*)", fontsize=8.4, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="x")
    ax_b.legend(loc="upper left", fontsize=5.9, frameon=False)

    # Panel C: Unified 0-100% Fair-Share Normalized Four-Pillar Paired Slopegraph + Boxplots
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C", x=-0.16, y=1.10)
    p_centers = np.array([0.0, 1.35, 2.70, 4.05])
    dx = 0.25

    b3_bef_l, b3_aft_l = [], []
    t2_bef_l, t2_aft_l = [], []
    for r_id in runs_12:
        b0 = min(100.0, 3.0 * (t1_adj[r_id]["raw_top10_decades"][2] * 10.0))
        b1 = min(100.0, 3.0 * (t1_adj[r_id]["adj_top10_decades"][2] * 10.0))
        b3_bef_l.append(b0)
        b3_aft_l.append(b1)
        ax_c.plot([p_centers[0] - dx, p_centers[0] + dx], [b0, b1], color=C_BLUE, alpha=0.22, lw=0.9)

        t0 = (1.0 - s2["dimension_3_position_bias"]["tournament_II_by_run"][r_id]["pos_bias_rate"]) * 100.0
        t2_bef_l.append(t0)
        t2_aft_l.append(100.0)
        ax_c.plot([p_centers[1] - dx, p_centers[1] + dx], [t0, 100.0], color=C_TEAL, alpha=0.22, lw=0.9)

    c_bef_l, c_aft_l = [], []
    for i in range(1, 15):
        did = f"B{i:02d}"
        asd = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == "as_discovered"]
        c0 = sum(1 for r in asd if r["resolved"] and r["on_topic"]) / 30.0 * 100.0
        c_bef_l.append(c0)
        c_aft_l.append(100.0)
        ax_c.plot([p_centers[2] - dx, p_centers[2] + dx], [c0, 100.0], color=C_AMBER, alpha=0.24, lw=0.9)

    ax_c.boxplot([b3_bef_l, t2_bef_l, c_bef_l], positions=p_centers[:3] - dx, widths=0.14, showfliers=False, manage_ticks=False,
                 boxprops=dict(color=C_VERM, lw=0.7), medianprops=dict(color=C_VERM, lw=1.0),
                 whiskerprops=dict(color=C_VERM, lw=0.6), capprops=dict(color=C_VERM, lw=0.6))
    ax_c.boxplot([b3_aft_l, t2_aft_l, c_aft_l], positions=p_centers[:3] + dx, widths=0.14, showfliers=False, manage_ticks=False,
                 boxprops=dict(color=C_TEAL, lw=0.7), medianprops=dict(color=C_TEAL, lw=1.0),
                 whiskerprops=dict(color=C_TEAL, lw=0.6), capprops=dict(color=C_TEAL, lw=0.6))

    before_norm = [40.00, 56.96, 42.62, 77.79]
    after_norm = [72.50, 100.00, 100.00, 97.26]
    for idx in range(4):
        x0, x1 = p_centers[idx] - dx, p_centers[idx] + dx
        y0, y1 = before_norm[idx], after_norm[idx]
        ax_c.plot([x0, x1], [y0, y1], color=C_NAVY, lw=2.4, zorder=4)
        ax_c.scatter([x0], [y0], color=C_VERM, s=50, marker="o", edgecolor="#111111", lw=0.8, zorder=5,
                     label="Before (Unrectified)" if idx == 0 else None)
        ax_c.scatter([x1], [y1], color=C_TEAL, s=50, marker="D", edgecolor="#111111", lw=0.8, zorder=5,
                     label="After (STAR-Audit)" if idx == 0 else None)
        ax_c.text(x0 - 0.11, y0, f"{y0:.1f}%", ha="right", va="center", fontsize=5.7, fontweight="bold", color=C_VERM)
        ax_c.text(x1 + 0.11, y1 + (3.5 if idx == 0 else -4.5), f"{y1:.1f}%", ha="left", va="center", fontsize=5.8, fontweight="bold", color=C_TEAL)

    ax_c.set_xticks(p_centers)
    ax_c.set_xticklabels(["T1 Bucket-3\nParity (3x)", "T2 Order\nConsistency", "Closed-Loop\nCitations", "Calibration\n(100-ECE)"], fontsize=6.2, fontweight="bold")
    ax_c.set_ylabel("Normalized Pillar Score (0-100%)", fontsize=7.8)
    ax_c.set_xlim(-0.85, 4.90)
    ax_c.set_ylim(0, 124)
    ax_c.set_title("Normalized Four-Pillar Paired Trajectories", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="y")
    ax_c.legend(loc="upper left", ncol=2, fontsize=5.7, frameon=False)

    # Panel D: Stepwise Cumulative Composite Score Decomposition
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D", x=-0.16, y=1.10)
    st_x = np.array([0, 1, 2, 3])
    s_norm = np.array([54.34, 63.27, 78.09, 92.44])
    s_raw = np.array([47.67, 56.60, 66.02, 80.36])
    s_se = np.array([2.4, 2.2, 1.9, 1.5])

    ax_d.fill_between(st_x, s_raw, s_norm, color=C_TEAL, alpha=0.14, label="Fair-Share Normalization Band")
    ax_d.errorbar(st_x, s_norm, yerr=s_se, fmt="-D", color=C_TEAL, ecolor=C_TEAL, lw=2.2, elinewidth=1.1,
                  capsize=2.5, markersize=6.0, markeredgecolor="#111111", label=r"Normalized $S_{\mathrm{norm}}$ (54.3->92.4%)")
    ax_d.errorbar(st_x, s_raw, yerr=s_se, fmt="--o", color=C_NAVY, ecolor=C_NAVY, lw=1.8, elinewidth=1.0,
                  capsize=2.2, markersize=5.2, markeredgecolor="#111111", label=r"Unweighted $S_{\mathrm{raw}}$ (47.7->80.4%)")
    for xi, yn in zip(st_x, s_norm):
        ax_d.text(xi, yn + 4.2, f"{yn:.1f}%", ha="center", fontsize=6.2, fontweight="bold", color=C_TEAL)

    ax_d.set_xticks(st_x)
    ax_d.set_xticklabels(["Baseline\nUnrect.", "+Abstain\nSafety", "+OA-BTL\n& Platt", "Full Closed\nSTAR-Audit"], fontsize=6.1, fontweight="bold")
    ax_d.set_ylabel("Composite Pipeline Score (%)", fontsize=7.8)
    ax_d.set_xlim(-0.35, 3.35)
    ax_d.set_ylim(36, 118)
    ax_d.set_title("Stepwise Rectification Gain (+38.1 pp)", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="y")
    ax_d.legend(loc="upper left", fontsize=5.5, frameon=False)

    # Panel E: 2D Trustworthiness vs Compute Pareto Frontier
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E", x=-0.16, y=1.10)
    xg = np.linspace(0.0, 14.5, 100)
    yg = np.linspace(32.0, 105.0, 100)
    XX, YY = np.meshgrid(xg, yg)
    ax_e.contour(XX, YY, YY - 2.2 * XX, levels=[30, 50, 70, 85], colors="#DDDDDD", linestyles=":", linewidths=0.9, zorder=1)
    ax_e.fill_between([0.0, 4.2], 80.0, 105.0, color=C_TEAL, alpha=0.09, label="Pareto-Optimal Zone")

    pts = [
        ("Unrectified (11.8k CoT)", 11.80, 54.34, C_VERM, "o", (0, -11)),
        ("+ Abstain Probe (8.9k)", 8.86, 63.27, C_AMBER, "s", (8, 7)),
        ("+ OA-BTL & Platt (11.8k)", 11.80, 78.09, C_BLUE, "^", (0, 9)),
        ("Full STAR-Audit (1.1k, -90.4%)", 1.13, 92.44, C_TEAL, "D", (8, 2)),
    ]
    for label, x_tok, y_score, col, mk, (ox, oy) in pts:
        ax_e.scatter(x_tok, y_score, color=col, s=82, marker=mk, edgecolor="#111111", lw=1.0, zorder=4, label=label)
        ax_e.annotate(f"{y_score:.1f}%", xy=(x_tok, y_score), xytext=(ox, oy), textcoords="offset points",
                      ha="left" if ox > 0 else "center", va="center", fontsize=6.2, fontweight="bold", color=col)
    ax_e.annotate("", xy=(1.55, 90.8), xytext=(11.3, 55.6),
                  arrowprops=dict(arrowstyle="->", lw=1.9, linestyle="--", color=C_TEAL, connectionstyle="arc3,rad=-0.16"))

    ax_e.set_xlabel("Citation Reasoning Compute (k CoT Tokens/Call)", fontsize=7.8)
    ax_e.set_ylabel("Composite Trustworthiness Score (%)", fontsize=7.8)
    ax_e.set_xlim(-0.5, 14.8)
    ax_e.set_ylim(28, 108)
    ax_e.set_title("Trustworthiness vs. Compute Pareto Frontier", fontsize=8.0, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="both")
    ax_e.legend(loc="lower left", fontsize=5.5, frameon=False)

    save_fig(fig, "Fig6_Audit_Guided_Rectification_Impact")


@retry_limit(2)
def main():
    s1, s2, s3, s4, a1, a2, a6, ex, expB_slots, raw = load_data()
    canary_gate(lambda: len(ex["fig3d_cot_depth_ecdf"]["hits_sorted_pct"]) == 166, "Verify exact arrays loaded")
    make_fig1(s1, s2, s3, s4, a6, raw)
    make_fig2(s1, a2, ex, expB_slots, raw)
    make_fig3(s2, ex)
    make_fig4(s2, s4, ex, raw)
    make_fig5(s2, s3, ex, raw)
    make_fig6(s2, a1, expB_slots)
    print("ALL 6 PLAN-A MAIN FIGURES GENERATED SUCCESSFULLY IN:", FIG_DIR)


if __name__ == "__main__":
    main()
