#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nc_v2_make_main_figs_canonical.py -- Generate all 6 Nature Communications canonical
Main Figures (Figs. 1-6; [4, 5, 6, 5, 4, 5] = 29 panels) for STAR-Audit (v2.2 Canonical).

Every panel strictly adopts published Nature / Nature Communications (Agentic AI Systems)
competitor chart grammars:
  - Fig. 1A: 3-column vector architecture (Robin Fig. 1a / Co-Scientist Fig. 1a / NC04 Fig. 1)
  - Fig. 1B: Vertically dodged CoT vs Answer token violins & IQRs (NC02 Hyper-RAG Fig. 6a-c)
  - Fig. 1C: Standardized z-effect +/- 95% CI forest + q_BH column (NC01 Brockers Fig. 4a)
  - Fig. 1D: 6-dimension trustworthiness polar radar (NC02 Fig. 4 / NC05 iDesignGPT Fig. 5a)
  - Fig. 2A: Grouped bar +/- SEM + 26 individual run/domain dots (Robin ED Fig. 4a / NC05 Fig. 6)
  - Fig. 2B: R=3 replicate dots + Mean +/- SEM point-intervals (Robin Fig. 2f / ED Fig. 5c)
  - Fig. 2C: 14-domain x 3-arm quantitative heatmap (Co-Scientist Fig. 4c)
  - Fig. 2D: GLM-5.3 2D CoT token vs error phase plane + 2D IQR crosshairs (NC01 Fig. 3/8)
  - Fig. 2E: 5-LLM x-axis grouped point-intervals across 4 modes (NC02 Hyper-RAG Fig. 2)
  - Fig. 3A-F: Heatmap (3A), grouped box+dots (3B, Co-Scientist ED Fig. 2), HPO dose curve (3C),
    pure CoT-depth ECDF (3D), dedicated High/Low Lit. Footprint point-intervals (3E, NC04 Fig. 2),
    and horizontal 2-vendor stacked bar for Top-10 decoy attractors (3F, SuperARC Fig. 6).
  - Fig. 4A-E: Flip forest (4A), grouped bucket box+12-run dots vs 33.3% null (4B, NC05 Fig. 4g),
    decile attention curve (4C), 200-pt NLI tail curve (4D, Farquhar Nature Fig. 3), 2D NLI shift (4E).
  - Fig. 5A-D: 4-cell paired bootstrap-null violin vs observed cross-run dots (5A, Robin ED Fig. 4c),
    reliability diagram (5B), CoT violins & rainclouds (5C, 5D).
  - Fig. 6A-E: T1/T2 Hessian 95%-CI primacy forest (6A, NC01 Fig. 4a), 9-pathway rank migration (6B),
    horizontal paired 4-pillar point-intervals + run/domain dots (6C, NC04 Fig. 2), incremental
    module-addition curves with per-curve 95% CI bands (6D, NC01 Fig. 6), empirical 2D Pareto (6E).
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
from matplotlib.transforms import Bbox

gate(__file__)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["axes.edgecolor"] = "#2B2B2B"
plt.rcParams["axes.linewidth"] = 0.9
plt.rcParams["axes.labelpad"] = 6.5
plt.rcParams["axes.titlepad"] = 8.5
plt.rcParams["xtick.major.pad"] = 4.2
plt.rcParams["ytick.major.pad"] = 4.2
plt.rcParams["legend.frameon"] = False
plt.rcParams["legend.labelspacing"] = 0.50

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
EXEC_DIR = os.path.join(BASE, "GEN2_exec")
ANAL_DIR = os.path.join(EXEC_DIR, "analysis")
DATA_DIR = os.path.join(EXEC_DIR, "data")
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
FIG_DIR = os.path.join(EXEC_DIR, "figures_NC_v2_aligned")
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
    ax.tick_params(labelsize=8.3, colors="#1F1F1F", width=0.85, length=3.5)
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.55, color="#DCDCDC", alpha=0.85)
        ax.set_axisbelow(True)


def add_panel_label(ax, label, x=-0.14, y=1.10):
    # Tag axis for deterministic post-layout row/column alignment
    ax._panel_letter = label


def place_aligned_panel_letters(fig, rows_spec):
    """Align panel letters (A-F) onto exact horizontal row baselines and vertical column lines."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()

    row_bbs = []
    for row in rows_spec:
        r_list = []
        for ax, lbl in row:
            bb = ax.get_tightbbox(renderer).transformed(inv)
            r_list.append((ax, lbl, bb))
        row_bbs.append(r_list)

    same_cols = len({len(r) for r in row_bbs}) == 1 and len(row_bbs) > 1
    col_x = {}
    if same_cols:
        ncols = len(row_bbs[0])
        for c in range(ncols):
            col_x[c] = min(row_bbs[r][c][2].x0 for r in range(len(row_bbs))) - 0.008
    else:
        col0_min = min(r[0][2].x0 for r in row_bbs) - 0.008

    for r_idx, r_list in enumerate(row_bbs):
        y_top = max(item[2].y1 for item in r_list) + 0.004
        for c_idx, (ax, lbl, bb) in enumerate(r_list):
            if same_cols:
                x_pos = col_x[c_idx]
            elif c_idx == 0:
                x_pos = col0_min
            else:
                x_pos = bb.x0 - 0.008
            fig.text(x_pos, y_top, lbl, fontsize=13.5, fontweight="bold",
                     va="top", ha="right", color="#111111")


def check_panel_collisions(fig, fig_name):
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
            if len(txt_val) == 1 and txt_val in "ABCDEF":
                continue
            bb = t.get_window_extent(renderer=renderer).expanded(0.92, 0.88)
            for prev_txt, prev_bb in bbs:
                if bb.overlaps(prev_bb):
                    n_overlaps += 1
                    print(f"  [WARN collision in {fig_name}] {txt_val!r} <-> {prev_txt!r}")
            bbs.append((txt_val, bb))
    # Cross-panel check: panel letters (fig.texts) vs axes titles & tick labels
    other_bbs = []
    for ax in fig.axes:
        if ax.title and ax.title.get_text().strip():
            other_bbs.append((f"title:{ax.title.get_text().strip()}", ax.title.get_window_extent(renderer=renderer).expanded(0.96, 0.92)))
        for tl in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
            if tl.get_visible() and tl.get_text().strip():
                other_bbs.append((f"tick:{tl.get_text().strip()}", tl.get_window_extent(renderer=renderer).expanded(0.94, 0.90)))
    for ft in fig.texts:
        ft_txt = ft.get_text().strip()
        if not ft_txt:
            continue
        fbb = ft.get_window_extent(renderer=renderer).expanded(0.94, 0.90)
        for o_lbl, o_bb in other_bbs:
            if fbb.overlaps(o_bb):
                n_overlaps += 1
                print(f"  [WARN cross-panel letter collision in {fig_name}] {ft_txt!r} <-> {o_lbl!r}")
    print(f"Collision check [{fig_name}]: {n_overlaps} intra/cross-panel text overlaps")


def save_fig(fig, name, rows_spec=None):
    if rows_spec is not None:
        place_aligned_panel_letters(fig, rows_spec)
    check_panel_collisions(fig, name)
    for ext in ["svg", "pdf", "png"]:
        path = os.path.join(FIG_DIR, f"{name}.{ext}")
        fig.savefig(path, dpi=350, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print(f"Saved {name} (.svg, .pdf, .png)")


# ==============================================================================
# FIGURE 1 (4 panels, 1+3 Asymmetric Hero GridSpec -- Exact Flush Left/Right!):
# ==============================================================================
def make_fig1(ex, raw):
    fig_w, fig_h = 14.4, 10.6
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs_bot = gridspec.GridSpec(1, 3, figure=fig, left=0.185, right=0.955, bottom=0.075, top=0.445,
                               width_ratios=[1.10, 1.12, 0.96], wspace=0.58)

    # Panel B: Dodged CoT Violins (y + 0.14) vs Visible Answer IQR & Median (y - 0.22)
    ax_b = fig.add_subplot(gs_bot[0, 0])
    stage_order = [
        "T1_Screening", "T2_Judging", "Step1_3_Ideation",
        "Domain14_Citation", "Step6_Citations", "HPO_GLM", "HPO_DeepSeek",
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
    ans_arrays = [np.array(raw["stage_ans"][k]) for k in stage_order]

    parts = ax_b.violinplot(rt_arrays, positions=y_pos + 0.14, vert=False, widths=0.58,
                            showmeans=False, showextrema=False, showmedians=False)
    for pc in parts["bodies"]:
        pc.set_facecolor(C_BLUE)
        pc.set_edgecolor(C_NAVY)
        pc.set_alpha(0.46)
        pc.set_linewidth(0.85)

    for idx, (arr_rt, arr_ans) in enumerate(zip(rt_arrays, ans_arrays)):
        q25, med, q75 = np.percentile(arr_rt, [25, 50, 75])
        ax_b.plot([q25, q75], [y_pos[idx] + 0.14, y_pos[idx] + 0.14], color=C_NAVY, lw=2.5, zorder=4)
        ax_b.scatter([med], [y_pos[idx] + 0.14], color="white", edgecolor=C_NAVY, s=30, lw=1.3, zorder=5,
                     label="Internal CoT Median & IQR" if idx == 0 else None)
        aq25, amed, aq75 = np.percentile(arr_ans, [25, 50, 75])
        ax_b.plot([aq25, aq75], [y_pos[idx] - 0.22, y_pos[idx] - 0.22], color=C_AMBER, lw=2.0, zorder=4)
        ax_b.scatter([amed], [y_pos[idx] - 0.22], color=C_AMBER, edgecolor="#222222", marker="D", s=24, zorder=6,
                     label="Visible Answer Median & IQR" if idx == 0 else None)
        ax_b.text(float(np.max(arr_rt)) + 0.7, y_pos[idx] + 0.14, f"{med:.1f}k", va="center",
                  fontsize=7.9, color=C_NAVY, fontweight="bold")

    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(stage_labels, fontsize=8.0, fontweight="bold")
    ax_b.set_xlabel("Per-Call Tokens (k; CoT = 35.58M [93.8%])", fontsize=9.1, fontweight="bold")
    ax_b.set_title("Per-Call CoT vs. Answer Tokens", fontsize=9.6, fontweight="bold", loc="left")
    ax_b.set_xlim(0.0, 43.0)
    ax_b.set_ylim(-0.75, 7.95)
    style_ax(ax_b, grid_axis="x")
    ax_b.legend(loc="upper right", fontsize=7.4, frameon=False)

    # Panel C: Canonical NC01 Brockers Fig. 4a Standardized Effect (|z| +/- 95% CI) Forest + q_BH
    ax_c = fig.add_subplot(gs_bot[0, 1])
    h_spec = [
        ("H5", "H5: Cross-Run vs. Bootstrap\nStability (dJ = -0.57)"),
        ("H1", "H1: Epistemic Citation Gate\n(RD = -54.5 pp, Fake 0%)"),
        ("H6", "H6: Confidence Calibration\nSlope != 1.0 (b = 0.655)"),
        ("H4", "H4: Blind vs. Retrieval\nLead-Gene Split (dJ = +0.09)"),
        ("H2", "H2: Pooled HPO Top-IC\nSlope (DS p = 0.026*)"),
        ("H3", "H3: HPO Arm x Dose\nInteraction (Starvation)"),
    ]
    z_map = ex["fig1c_standardized_z"]
    y_m = np.arange(len(h_spec))[::-1]

    ax_c.fill_betweenx([-1.85, 6.2], 2.16, 9.6, color=C_TEAL, alpha=0.09, label="BH-FDR Significant (q < 0.05)")
    ax_c.axvline(0.0, color="#666666", linestyle=":", lw=1.1, label="Null Effect (z = 0)")
    ax_c.axvline(1.96, color=C_VERM, linestyle="--", lw=1.2, label="Nominal 2-Sided z = 1.96")

    for idx, (hk, h_lbl) in enumerate(h_spec):
        zv = z_map[hk]["z_stat"]
        qv = z_map[hk]["bh_q"]
        sig = qv < 0.05
        col = C_TEAL if sig else C_SLATE
        mk = "D" if sig else "o"
        ax_c.errorbar([zv], [y_m[idx]], xerr=[1.96], fmt=mk, color=col, ecolor=col,
                      elinewidth=2.0, capsize=3.0, markersize=6.6, markeredgecolor="#111111", zorder=4,
                      label="Standardized |z| +/- 95% CI" if idx == 0 else None)
        q_str = f"q={qv:.4f}*" if sig else f"q={qv:.3f}"
        ax_c.text(zv + 1.96 + 0.22, y_m[idx], q_str, va="center", fontsize=7.8,
                  fontweight="bold" if sig else "normal", color=C_TEAL if sig else "#333333")

    ax_c.set_yticks(y_m)
    ax_c.set_yticklabels([x[1] for x in h_spec], fontsize=7.8, fontweight="bold")
    ax_c.set_xlabel("Standardized Test Effect Size (|z| +/- 95% CI)", fontsize=9.2, fontweight="bold")
    ax_c.set_title("Confirmatory Hypothesis Forest (BH-FDR)", fontsize=9.8, fontweight="bold", loc="left")
    ax_c.set_xlim(-2.2, 9.6)
    ax_c.set_ylim(-1.85, 5.95)
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="lower right", fontsize=7.2, frameon=False)

    # Panel D: Six-Dimension Polar Radar Chart
    ax_d = fig.add_subplot(gs_bot[0, 2], projection="polar")
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
    ax_d.set_xticklabels(radar_labels, fontsize=7.6, fontweight="bold", color="#1F1F1F")
    ax_d.tick_params(axis="x", pad=15)
    ax_d.set_rlabel_position(30)
    ax_d.set_yticks([25, 50, 75, 100])
    ax_d.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7.2, color="#444444")
    ax_d.set_ylim(0, 112)

    ax_d.plot(angles, u_plot, "-o", lw=2.2, color=C_VERM, markersize=5.2, label="Unrectified (54.3%)")
    ax_d.fill(angles, u_plot, color=C_VERM, alpha=0.18)
    ax_d.plot(angles, r_plot, "-s", lw=2.4, color=C_TEAL, markersize=5.2, label="STAR-Audit (92.4%)")
    ax_d.fill(angles, r_plot, color=C_TEAL, alpha=0.22)
    ax_d.set_title("Six-Dimension Trustworthiness Radar", fontsize=9.8, fontweight="bold", pad=18)
    ax_d.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=7.5, frameon=False)

    # Measure exact visual span [x0..x1] of B-C-D and align Panel A FLUSH left-to-right!
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    bb_bot = Bbox.union([ax.get_tightbbox(renderer) for ax in (ax_b, ax_c, ax_d)]).transformed(inv)

    hero_path = os.path.join(FIG_DIR, "star_audit_architecture_hero_v3.png")
    raw_img = plt.imread(hero_path)
    rgb = raw_img[..., :3]
    mask = (rgb.min(axis=2) < 0.965) if rgb.max() <= 1.01 else (rgb.min(axis=2) < 246)
    ys_nz, xs_nz = np.where(mask)
    pad_px = 10
    schematic_img = raw_img[
        max(0, int(ys_nz.min()) - pad_px):min(raw_img.shape[0], int(ys_nz.max()) + pad_px),
        max(0, int(xs_nz.min()) - pad_px):min(raw_img.shape[1], int(xs_nz.max()) + pad_px),
    ]
    img_ar = schematic_img.shape[0] / float(schematic_img.shape[1])
    w_fig = bb_bot.x1 - bb_bot.x0
    h_fig = w_fig * (fig_w / fig_h) * img_ar
    y0_a = bb_bot.y1 + 0.030

    ax_a = fig.add_axes([bb_bot.x0, y0_a, w_fig, h_fig])
    ax_a.imshow(schematic_img, aspect="equal", extent=[0, schematic_img.shape[1], schematic_img.shape[0], 0])
    ax_a.set_xlim(0, schematic_img.shape[1])
    ax_a.set_ylim(schematic_img.shape[0], 0)
    ax_a.set_xticks([])
    ax_a.set_yticks([])
    ax_a.axis("off")

    save_fig(fig, "Fig1_Audit_Remediation_Architecture", rows_spec=[
        [(ax_a, "A")],
        [(ax_b, "B"), (ax_c, "C"), (ax_d, "D")],
    ])


# ==============================================================================
# FIGURE 2 (5 panels, 2+3 Asymmetric GridSpec):
#   2A: Grouped Bar +/- SEM + 26 Run/Domain Dots (Robin ED Fig. 4a / NC05 Fig. 6)
#   2B: R=3 Replicate Dots + Mean +/- SEM Point-Intervals (Robin Fig. 2f)
#   2C: 14-Domain x 3-Arm Quantitative Heatmap
#   2D: Pure GLM-5.3 Citation CoT Phase Plane + 2D IQR Crosshairs
#   2E: 5-LLM X-Axis Grouped Point-Intervals Across 4 Modes (NC02 Hyper-RAG Fig. 2)
# ==============================================================================
def make_fig2(s1, a2, ex, expB_slots, raw):
    fig = plt.figure(figsize=(14.4, 10.1))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.02, 1.14], hspace=0.50)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[1.06, 1.0], wspace=0.40)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.02, 1.04, 1.08], wspace=0.44)

    # Panel A: Canonical Grouped Bar +/- SEM + All 26 Individual Run/Domain Dots (Bar #1 of 2!)
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A")
    c4 = ex["fig2a_4cats"]
    cat_keys = ["tier1_valid", "trojan_offtopic", "fake_nonexistent", "tier2_verified"]
    cat_lbls = [
        "Tier-1 Existent\n(Apparent Valid)",
        "Tier-2 Off-Topic\n(Trojan PMIDs)",
        "Non-Existent\n(Fake PMIDs)",
        "Tier-2 On-Topic\n(True Grounded)",
    ]
    x_c = np.arange(4)
    bw = 0.34
    p_means = [float(np.mean(c4["parent_12runs"][k])) for k in cat_keys]
    p_sems = [float(np.std(c4["parent_12runs"][k], ddof=1) / math.sqrt(12)) for k in cat_keys]
    b_means = [float(np.mean(c4["expb_14domains"][k])) for k in cat_keys]
    b_sems = [float(np.std(c4["expb_14domains"][k], ddof=1) / math.sqrt(14)) for k in cat_keys]

    ax_a.bar(x_c - bw / 2, p_means, width=bw, yerr=p_sems, capsize=3.0, color=C_BLUE, alpha=0.68,
             edgecolor="#111111", lw=0.85, error_kw=dict(lw=1.3, ecolor="#111111"),
             label="12 Discovery Runs (Step 6, 360 slots)")
    ax_a.bar(x_c + bw / 2, b_means, width=bw, yerr=b_sems, capsize=3.0, color=C_AMBER, alpha=0.72,
             edgecolor="#111111", lw=0.85, error_kw=dict(lw=1.3, ecolor="#111111"),
             label="14 Clinical Domains (Ungated, 420 slots)")

    rng_a = np.random.default_rng(101)
    for i, ck in enumerate(cat_keys):
        vp = np.array(c4["parent_12runs"][ck])
        vb = np.array(c4["expb_14domains"][ck])
        ax_a.scatter(x_c[i] - bw / 2 + rng_a.uniform(-0.07, 0.07, len(vp)), vp,
                     color=C_NAVY, s=18, alpha=0.72, zorder=4)
        ax_a.scatter(x_c[i] + bw / 2 + rng_a.uniform(-0.07, 0.07, len(vb)), vb,
                     color=C_VERM, marker="s", s=17, alpha=0.72, zorder=4)
        top_y = max(float(np.max(vp)), float(np.max(vb)), p_means[i] + p_sems[i], b_means[i] + b_sems[i])
        ax_a.text(x_c[i], top_y + 4.2, f"{p_means[i]:.1f}% / {b_means[i]:.1f}%",
                  ha="center", fontsize=7.3, fontweight="bold", color="#222222")

    ax_a.set_xticks(x_c)
    ax_a.set_xticklabels(cat_lbls, fontsize=7.8, fontweight="bold")
    ax_a.set_ylabel("Share of Citation Slots (%)", fontsize=9.0, fontweight="bold")
    ax_a.set_xlim(-0.58, 3.58)
    ax_a.set_ylim(0, 136)
    ax_a.set_title("Two-Tier Audit Exposes 54-57% Trojan Citations (n = 780)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper right", fontsize=7.3, frameon=False)

    # Panel B: Canonical Robin Fig. 2f R=3 Replicate Dots + Mean +/- SEM Point-Intervals
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B")
    by_run_p = s1["parent_runs_dimension1"]["by_run"]
    cells_order = [
        ("dAMD_blind", "dAMD Blind\n(n=90 slots)"),
        ("dAMD_retrieval", "dAMD Retrieval\n(n=90 slots)"),
        ("ALS_blind", "ALS Blind\n(n=90 slots)"),
        ("ALS_retrieval", "ALS Retrieval\n(n=90 slots)"),
    ]
    x_cells = np.arange(len(cells_order))
    ax_b.fill_between([-0.5, 3.5], 50.0, 100.0, color=C_VERM, alpha=0.06, zorder=1, label=">50% Ungrounded Majority Zone")
    ax_b.axhline(50.0, color="#888888", linestyle=":", lw=1.0)

    for idx, (prefix, lbl) in enumerate(cells_order):
        r_ung = np.array([by_run_p[f"{prefix}_R{r}"]["ungrounded_rate_all_slots"] * 100.0 for r in [1, 2, 3]])
        r_on = np.array([(1.0 - by_run_p[f"{prefix}_R{r}"]["ungrounded_rate_all_slots"]) * 100.0 for r in [1, 2, 3]])
        m_u, se_u = float(np.mean(r_ung)), float(np.std(r_ung, ddof=1) / math.sqrt(3))
        m_o, se_o = float(np.mean(r_on)), float(np.std(r_on, ddof=1) / math.sqrt(3))
        jit = np.array([-0.05, 0.0, 0.05])

        ax_b.errorbar([idx - 0.15], [m_u], yerr=[se_u], fmt="o", color=C_VERM, ecolor=C_VERM,
                      elinewidth=2.0, capsize=3.2, markersize=6.8, markeredgecolor="#111111", zorder=5,
                      label="Total Ungrounded (Mean +/- SEM)" if idx == 0 else None)
        ax_b.scatter(idx - 0.15 + jit, r_ung, color=C_VERM, alpha=0.50, s=26, zorder=3)
        ax_b.text(idx - 0.15, max(float(np.max(r_ung)), m_u + se_u) + 4.8, f"{m_u:.1f}%",
                  ha="center", fontsize=7.6, fontweight="bold", color=C_VERM)

        ax_b.errorbar([idx + 0.15], [m_o], yerr=[se_o], fmt="s", color=C_TEAL, ecolor=C_TEAL,
                      elinewidth=2.0, capsize=3.2, markersize=6.6, markeredgecolor="#111111", zorder=5,
                      label="Verified On-Topic (Mean +/- SEM)" if idx == 0 else None)
        ax_b.scatter(idx + 0.15 + jit, r_on, color=C_TEAL, marker="s", alpha=0.50, s=26, zorder=3)
        ax_b.text(idx + 0.15, min(float(np.min(r_on)), m_o - se_o) - 9.5, f"{m_o:.1f}%",
                  ha="center", fontsize=7.6, fontweight="bold", color=C_TEAL)

    ax_b.set_xticks(x_cells)
    ax_b.set_xticklabels([c[1] for c in cells_order], fontsize=7.8, fontweight="bold")
    ax_b.set_ylabel("Step-6 Protocol Citation Rate (%)", fontsize=9.0, fontweight="bold")
    ax_b.set_xlim(-0.52, 3.52)
    ax_b.set_ylim(-2, 126)
    ax_b.set_title("12-Run Step-6 Grounding (Step-1 Retrieval Unprotective)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper left", fontsize=7.2, frameon=False)

    # Panel C: 14-Domain x 3-Arm Randomized Trial Heatmap
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C")
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
            ax_c.text(c_j, r_i, f"{val:.1f}%", ha="center", va="center", fontsize=7.2,
                      color="white" if val >= 45 else "#111111", fontweight="bold")
    ax_c.set_xticks([0, 1, 2])
    ax_c.set_xticklabels(["Ungated\n(3.1% Fake)", "Abstain\n(0.5% Fake)", "Module 3a\n(0.0% Fake*)"], fontsize=7.5, fontweight="bold")
    ax_c.set_yticks(np.arange(15))
    ax_c.set_yticklabels(clean_dom_names, fontsize=7.3, fontweight="bold")
    ax_c.set_title("14-Domain Trial (RD = -54.5 pp***)", fontsize=9.4, fontweight="bold", loc="left")
    ax_c.spines["top"].set_visible(False)
    ax_c.spines["right"].set_visible(False)

    # Panel D: Pure GLM-5.3 Citation CoT Phase Plane
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D")
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
        ax_d.scatter(xs, ys, color=col, alpha=0.45, s=32, marker=mk, edgecolor="none", zorder=3)
        cx, cy = float(np.median(raw["expB_arm_rt"][arm_key])), float(np.mean(ys))
        centroids.append((cx, cy))
        q25_x, q75_x = np.percentile(xs, [25, 75])
        q25_y, q75_y = np.percentile(ys, [25, 75])
        ax_d.errorbar(
            [cx], [cy],
            xerr=[[max(0.0, cx - q25_x)], [max(0.0, q75_x - cx)]],
            yerr=[[max(0.0, cy - q25_y)], [max(0.0, q75_y - cy)]],
            fmt=mk, color=col, ecolor=col, elinewidth=2.0, capsize=2.8, markersize=8.4,
            markeredgecolor="#111111", zorder=5, label=f"{arm_lbl}: {cy:.1f}%",
        )

    ax_d.annotate("", xy=(centroids[1][0] + 0.35, centroids[1][1] + 2.0), xytext=(centroids[0][0] - 0.35, centroids[0][1] - 2.0),
                  arrowprops=dict(arrowstyle="->", lw=1.8, linestyle="--", color=C_NAVY))
    ax_d.annotate("", xy=(centroids[2][0] + 0.45, centroids[2][1] + 1.5), xytext=(centroids[1][0] - 0.45, centroids[1][1] - 1.5),
                  arrowprops=dict(arrowstyle="->", lw=1.8, linestyle="--", color=C_TEAL))
    ax_d.text(9.0, 84.0, "-90.41% Median CoT\n(11.80k -> 1.13k)", fontsize=7.5, fontweight="bold", color=C_TEAL)

    ax_d.set_xlabel("Per-Call Citation CoT Compute (k Tokens)", fontsize=8.9, fontweight="bold")
    ax_d.set_ylabel("Domain Ungrounded Citation Rate (%)", fontsize=8.9, fontweight="bold")
    ax_d.set_xlim(-0.5, 16.8)
    ax_d.set_ylim(-6, 126)
    ax_d.set_title("GLM-5.3 Phase Plane: Gating Halts Spin", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="upper left", fontsize=7.0, frameon=False)

    # Panel E: Canonical NC02 Hyper-RAG Fig. 2 Multi-LLM Grouped Point-Interval (5 LLMs on X-Axis!)
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E")
    sp = a2["honest_split_by_model_and_arm"]
    cl84 = a2["closed_loop_5model_matched84"]
    llm_rows = [
        ("GLM-5.3\n(n=420)", sp["GLM-5.3_ExpB_Full420"], 420, a2["closed_loop_glm_full420"]["closed_loop_verified_grounded_yield_pct"]),
        ("Gemini-4\nArgon", sp["Gemini-4-Argon-High"], 84, cl84["Gemini-4-Argon-High"]["post_handoff_verified_yield_pct"]),
        ("Gemini-3.8\nFlash", sp["Gemini-3.8-Flash"], 84, cl84["Gemini-3.8-Flash"]["post_handoff_verified_yield_pct"]),
        ("Grok-4.7\nHigh", sp["Grok-4.7-High"], 84, cl84["Grok-4.7-High"]["post_handoff_verified_yield_pct"]),
        ("Grok-4.7\nFast", sp["Grok-4.7-Fast"], 84, cl84["Grok-4.7-Fast"]["post_handoff_verified_yield_pct"]),
    ]
    x_m = np.arange(len(llm_rows))
    mode_defs = [
        (-0.24, "as_discovered", "Ungated Baseline (12-77% Error)", C_VERM, "o"),
        (-0.08, "abstain_probe", "Abstain-Probe", C_AMBER, "s"),
        (0.08, "gated", "Module 3a Alone (Safe Abstain)", C_BLUE, "^"),
        (0.24, "closed_loop", "Closed-Loop 3a+3b (100%, 0% Err)", C_TEAL, "D"),
    ]
    ax_e.fill_between([-0.5, 4.5], 95.0, 103.0, color=C_TEAL, alpha=0.09, zorder=1)
    ax_e.axhline(100.0, color=C_TEAL, linestyle=":", lw=1.1)

    for dx, m_key, m_lbl, col, mk in mode_defs:
        ys_m, ses_m = [], []
        for _, md, n_sl, cl_y in llm_rows:
            val = cl_y if m_key == "closed_loop" else md[m_key]["parametric_grounded_yield_pct"]
            se = 100.0 * math.sqrt(max(0.0, (val / 100.0) * (1.0 - val / 100.0)) / n_sl)
            ys_m.append(val)
            ses_m.append(se)
        ax_e.errorbar(x_m + dx, ys_m, yerr=ses_m, fmt=mk, color=col, ecolor=col,
                      elinewidth=1.7, capsize=2.5, markersize=6.2, markeredgecolor="#111111", zorder=4, label=m_lbl)

    ax_e.set_xticks(x_m)
    ax_e.set_xticklabels([r[0] for r in llm_rows], fontsize=7.5, fontweight="bold")
    ax_e.set_ylabel("Verified On-Topic Citation Yield (%)", fontsize=8.9, fontweight="bold")
    ax_e.set_xlim(-0.52, 4.52)
    ax_e.set_ylim(-6, 148)
    ax_e.set_title("5-Model Closed-Loop Restores 100% Yield", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="y")
    ax_e.legend(loc="upper left", fontsize=6.9, frameon=False)

    save_fig(fig, "Fig2_Dim1_Trojan_Horse_Citations", rows_spec=[
        [(ax_a, "A"), (ax_b, "B")],
        [(ax_c, "C"), (ax_d, "D"), (ax_e, "E")],
    ])


# ==============================================================================
# FIGURE 3 (6 panels, 3x2 Asymmetric GridSpec -- Zero Dual-Axis Franken-Plots!):
#   3A: 12-Run x 12-Axis Pathway Convergence Heatmap
#   3B: Grouped Boxplot + Individual Pairwise Dots (Co-Scientist ED Fig. 2)
#   3C: 120-Disease HPO Deletion Dose-Response (0%, 25%, 50% IC Removed)
#   3D: Pure White-Box 2.1% CoT First-Mention Depth ECDF (0-100% CoT Depth)
#   3E: Dedicated High vs. Low PubMed Literature Footprint Point-Intervals (NC04 Fig. 2)
#   3F: Horizontal 2-Vendor Stacked Bar for Top-10 Decoy Attractors (SuperARC Fig. 6)
# ==============================================================================
def make_fig3(s2, ex):
    fig = plt.figure(figsize=(14.4, 12.6))
    gs = gridspec.GridSpec(3, 2, height_ratios=[1.10, 1.02, 1.02], width_ratios=[1.05, 1.01], hspace=0.48, wspace=0.44)

    # Panel A: 12-Run x 12-Axis Pathway Convergence Heatmap
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A")
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
                ax_a.text(c_i, r_i, str(val), ha="center", va="center", fontsize=7.8, fontweight="bold",
                          color="white" if val >= 2 else "#111111")
    ax_a.axvline(5.5, color="#222222", linewidth=1.3)
    ax_a.axhline(5.5, color="#222222", linewidth=1.3)
    ax_a.set_xticks(np.arange(len(run_clean)))
    ax_a.set_xticklabels(run_clean, fontsize=6.9, fontweight="bold")
    ax_a.set_yticks(np.arange(len(axes_list)))
    ax_a.set_yticklabels([a[1] for a in axes_list], fontsize=7.4, fontweight="bold")
    ax_a.set_title("Pathway Convergence Across 12 Runs (* = Gold Axis)", fontsize=9.5, fontweight="bold", loc="left")

    # Panel B: Canonical Co-Scientist ED Fig. 2 Grouped Boxplots + Pairwise Run Dots (Zero Zigzag!)
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B")
    gran_x = np.array([0, 1, 2])
    gran_labels = ["Lead Target\nGene (HGNC)", "All Dossier\nTarget Genes", "Canonical Pathway\nAxis (Gold)"]
    pw = ex["fig3b_5a_pairwise"]
    grp_specs = [
        (-0.27, "ALS", "within", C_NAVY, "o", "ALS Within-Arm (n=6 pairs: 0.204->0.572)"),
        (-0.09, "ALS", "cross", C_SKY, "o", "ALS Cross-Arm (n=9 pairs: 0.074->0.401)"),
        (0.09, "dAMD", "within", C_TEAL, "s", "dAMD Within-Arm (n=6 pairs: 0.093->0.394)"),
        (0.27, "dAMD", "cross", C_AMBER, "s", "dAMD Cross-Arm (n=9 pairs: 0.037->0.473)"),
    ]
    rng_b = np.random.default_rng(202)
    for dx, dis_k, arm_k, col, mk, glbl in grp_specs:
        for g_idx, gk in enumerate(["lead_genes", "all_genes", "axes"]):
            vals = np.array(pw[dis_k][f"{arm_k}_{gk}"], dtype=float)
            ax_b.boxplot([vals], positions=[g_idx + dx], widths=0.13, patch_artist=True,
                         showfliers=False, manage_ticks=False,
                         boxprops=dict(facecolor=col, alpha=0.32, edgecolor=col, lw=1.0),
                         medianprops=dict(color="#111111", lw=1.4),
                         whiskerprops=dict(color=col, lw=0.9), capprops=dict(color=col, lw=0.9))
            ax_b.scatter(g_idx + dx + rng_b.uniform(-0.025, 0.025, len(vals)), vals,
                         color=col, marker=mk, s=18, alpha=0.72, edgecolor="#111111", lw=0.45, zorder=4)
            ax_b.scatter([g_idx + dx], [float(np.mean(vals))], color="white", edgecolor=col, marker="D", s=24, lw=1.2, zorder=5,
                         label=glbl if g_idx == 0 else None)

    ax_b.text(2.0 - 0.27, 0.85, "2.81x", ha="center", fontsize=7.6, fontweight="bold", color=C_NAVY)
    ax_b.text(2.0 + 0.09, 0.57, "4.26x", ha="center", fontsize=7.6, fontweight="bold", color=C_TEAL)
    ax_b.set_xticks(gran_x)
    ax_b.set_xticklabels(gran_labels, fontsize=7.9, fontweight="bold")
    ax_b.set_ylabel("Pairwise Run Top-5 Jaccard Similarity", fontsize=9.0, fontweight="bold")
    ax_b.set_xlim(-0.52, 2.52)
    ax_b.set_ylim(-0.04, 1.12)
    ax_b.set_title("Multi-Scale Convergence Across Granularity Levels", fontsize=9.5, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper left", fontsize=7.0, frameon=False)

    # Panel C: Pure HPO Dose-Response (0%, 25%, 50% IC Deleted)
    ax_c = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_c, "C")
    f3c_ex = ex["fig3c_exact"]
    doses = np.array([0, 25, 50])
    glm_top = np.array([f3c_ex["glm_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    ds_top = np.array([f3c_ex["deepseek_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    ds_srad = np.array([f3c_ex["deepseek_module4a_del_topIC"][str(d)]["hit10_pct"] for d in [0, 25, 50]])
    glm_se = np.array([f3c_ex["glm_del_topIC"][str(d)]["binomial_se_pct"] for d in [0, 25, 50]])
    ds_se = np.array([f3c_ex["deepseek_del_topIC"][str(d)]["binomial_se_pct"] for d in [0, 25, 50]])

    ax_c.fill_between(doses, glm_top - glm_se, glm_top + glm_se, color=C_BLUE, alpha=0.12)
    ax_c.fill_between(doses, ds_top - ds_se, ds_top + ds_se, color=C_VERM, alpha=0.14)
    ax_c.errorbar(doses, glm_top, yerr=glm_se, fmt="-o", color=C_BLUE, ecolor=C_BLUE, lw=2.1, elinewidth=1.0, capsize=2.4, markersize=5.6, label="GLM-5.3 Top-IC (34.5->30.6%)")
    ax_c.errorbar(doses, ds_top, yerr=ds_se, fmt="-D", color=C_VERM, ecolor=C_VERM, lw=2.1, elinewidth=1.0, capsize=2.4, markersize=5.6, label="DeepSeek-V4 Top-IC (28.3->14.3%*)")
    ax_c.plot(doses, ds_srad, "-s", color=C_TEAL, lw=2.2, markersize=5.8, label="DeepSeek + Module 4a (20.7->34.3%***)")
    ax_c.plot(doses, [65.0, 70.0, 60.0], "--^", color=C_NAVY, lw=1.7, markersize=5.2, label="Gemini-4-Argon (65.0%)")
    ax_c.plot(doses, [30.0, 30.0, 20.0], ":v", color=C_PURPLE, lw=1.6, markersize=5.2, label="Gemini-3.8-Flash (26.7%)")
    ax_c.plot(doses, [45.0, 30.0, 20.0], "-.P", color=C_AMBER, lw=1.7, markersize=5.4, label="Grok-4.7-High (31.7%)")
    ax_c.plot(doses, [40.0, 35.0, 35.0], ":X", color=C_SLATE, lw=1.6, markersize=5.2, label="Grok-4.7-Fast (36.7%)")

    ax_c.set_xticks([0, 25, 50])
    ax_c.set_xlim(-4, 54)
    ax_c.set_ylim(4, 108)
    ax_c.set_xlabel("High-IC HPO Phenotype Deletion Dose (%)", fontsize=8.9, fontweight="bold")
    ax_c.set_ylabel("Causal Gene Recall@10 (%)", fontsize=8.9, fontweight="bold")
    ax_c.set_title("120-Disease HPO Dose-Response & Module 4a Rescue", fontsize=9.5, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper right", ncol=2, fontsize=6.7, frameon=False)

    # Panel D: 100% Pure White-Box 2.1% CoT Depth ECDF
    ax_d = fig.add_subplot(gs[1, 1])
    add_panel_label(ax_d, "D")
    ec = ex["fig3d_cot_depth_ecdf"]
    h_v = np.array(ec["hits_sorted_pct"])
    p_v = np.array(ec["self_pruned_sorted_pct"])
    c_v = np.array(ec["ceiling_ghost_sorted_pct"])

    ax_d.fill_betweenx([0, 1.02], 0, 5.0, color=C_TEAL, alpha=0.12, label="<=5% Instant-Recognition Window")
    ax_d.step(h_v, np.arange(1, len(h_v) + 1) / len(h_v), where="post", color=C_TEAL, lw=2.4,
              label=f"Baseline Hits (n={len(h_v)}, Median = 2.1%)")
    ax_d.step(c_v, np.arange(1, len(c_v) + 1) / len(c_v), where="post", color=C_BLUE, linestyle="--", lw=2.1,
              label=f"32k Ceiling Ghosts (n={len(c_v)}, Median = {ec['ceiling_ghost_median_pct']:.1f}%)")
    ax_d.step(p_v, np.arange(1, len(p_v) + 1) / len(p_v), where="post", color=C_VERM, linestyle="-.", lw=2.1,
              label=f"Self-Pruned Misses (n={len(p_v)}, 23.3% FN, Med = 10.8%)")
    ax_d.axhline(0.50, color="#888888", linestyle=":", lw=1.0)
    ax_d.annotate("Median = 2.08%\nCoT Depth", xy=(2.08, 0.50), xytext=(18.5, 0.44),
                  fontsize=7.5, fontweight="bold", color=C_TEAL, arrowprops=dict(arrowstyle="->", lw=1.1, color=C_TEAL))

    ax_d.set_xlabel("Normalized CoT Depth of First True Causal Gene (%)", fontsize=8.9, fontweight="bold")
    ax_d.set_ylabel("Empirical Cumulative Fraction", fontsize=8.9, fontweight="bold")
    ax_d.set_xlim(0, 96)
    ax_d.set_ylim(0, 1.30)
    ax_d.set_title("White-Box 2.1% Instant-Recognition Law & Self-Pruning", fontsize=9.5, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="lower right", fontsize=6.9, frameon=False)

    # Panel E: Dedicated Canonical NC04 Fig. 2 Pretraining Literature Footprint Recall (+/- SE)
    ax_e = fig.add_subplot(gs[2, 0])
    add_panel_label(ax_e, "E")
    fp = ex["fig3e_lit_footprint"]
    cohorts_fp = [
        ("GLM-5.3\n(n=359)", fp["glm"], "p = 0.011*"),
        ("DeepSeek-V4\n(n=271)", fp["deepseek"], "ns"),
        ("Pooled 32k\n(n=630)", fp["pooled"], "p = 0.0008***"),
    ]
    xf = np.arange(3)
    hi_vals = [c[1]["high"]["pct"] for c in cohorts_fp]
    hi_ses = [c[1]["high"]["se"] for c in cohorts_fp]
    lo_vals = [c[1]["low"]["pct"] for c in cohorts_fp]
    lo_ses = [c[1]["low"]["se"] for c in cohorts_fp]

    ax_e.fill_between([-0.45, 2.45], 20.5, 32.3, color=C_NAVY, alpha=0.06, zorder=1)
    ax_e.errorbar(xf - 0.16, hi_vals, yerr=hi_ses, fmt="o", color=C_NAVY, ecolor=C_NAVY,
                  elinewidth=2.0, capsize=3.2, markersize=6.8, markeredgecolor="#111111", zorder=4,
                  label="High Literature Footprint (>155 PubMed Papers)")
    ax_e.errorbar(xf + 0.16, lo_vals, yerr=lo_ses, fmt="s", color=C_AMBER, ecolor=C_AMBER,
                  elinewidth=2.0, capsize=3.2, markersize=6.6, markeredgecolor="#111111", zorder=4,
                  label="Low Literature Footprint (<=155 PubMed Papers)")
    for i, (_, rec_f, ptag) in enumerate(cohorts_fp):
        ax_e.text(xf[i] - 0.16, hi_vals[i] + hi_ses[i] + 2.5, f"{hi_vals[i]:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color=C_NAVY)
        ax_e.text(xf[i] + 0.16, lo_vals[i] + lo_ses[i] + 2.5, f"{lo_vals[i]:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color="#9A6700")
        top_br = max(hi_vals[i] + hi_ses[i], lo_vals[i] + lo_ses[i]) + 8.5
        ax_e.plot([xf[i] - 0.16, xf[i] - 0.16, xf[i] + 0.16, xf[i] + 0.16],
                  [top_br - 1.8, top_br, top_br, top_br - 1.8], color="#333333", lw=1.0)
        ax_e.text(xf[i], top_br + 1.4, ptag, ha="center", fontsize=7.4,
                  fontweight="bold" if "*" in ptag else "normal", color=C_VERM if "*" in ptag else "#555555")

    ax_e.set_xticks(xf)
    ax_e.set_xticklabels([c[0] for c in cohorts_fp], fontsize=7.9, fontweight="bold")
    ax_e.set_ylabel("Causal Gene Recall@10 (% +/- SE)", fontsize=9.0, fontweight="bold")
    ax_e.set_xlim(-0.50, 2.50)
    ax_e.set_ylim(6, 70)
    ax_e.set_title("Pretraining PubMed Literature Footprint Stratification", fontsize=9.5, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="y")
    ax_e.legend(loc="upper right", fontsize=7.0, frameon=False)

    # Panel F: Canonical SuperARC Fig. 6 Horizontal 2-Vendor Stacked Bar (Bar #2 of 2!)
    ax_f = fig.add_subplot(gs[2, 1])
    add_panel_label(ax_f, "F")
    dec10 = ex["fig3d_decoys"][::-1]
    genes_d = [d["gene"] for d in dec10]
    glm_d = np.array([d["glm_false_calls"] for d in dec10], dtype=float)
    ds_d = np.array([d["deepseek_false_calls"] for d in dec10], dtype=float)
    totals_d = glm_d + ds_d
    n_dis = [d["n_diseases"] for d in dec10]
    y_d = np.arange(len(genes_d))

    ax_f.barh(y_d, glm_d, height=0.66, color=C_BLUE, alpha=0.84, edgecolor="#111111", lw=0.75, label="GLM-5.3 False Calls")
    ax_f.barh(y_d, ds_d, left=glm_d, height=0.66, color=C_VERM, alpha=0.84, edgecolor="#111111", lw=0.75, label="DeepSeek-V4 False Calls")
    for i in range(len(genes_d)):
        ax_f.text(totals_d[i] + 0.8, y_d[i], f"{int(totals_d[i])} ({n_dis[i]} diseases)", va="center", fontsize=7.4, fontweight="bold", color="#222222")

    ax_f.set_yticks(y_d)
    ax_f.set_yticklabels(genes_d, fontsize=7.9, fontweight="bold")
    ax_f.set_xlabel("False-Positive Calls in Missed Mendelian Trials (Hit@10 = 0)", fontsize=8.9, fontweight="bold")
    ax_f.set_xlim(0, 45)
    ax_f.set_ylim(-0.7, 11.2)
    ax_f.set_title("Cross-Vendor Syndromic Decoy Attractors", fontsize=9.5, fontweight="bold", loc="left")
    style_ax(ax_f, grid_axis="x")
    ax_f.legend(loc="lower right", fontsize=7.2, frameon=False)

    save_fig(fig, "Fig3_Dim2_Reasoning_vs_Memorization", rows_spec=[
        [(ax_a, "A"), (ax_b, "B")],
        [(ax_c, "C"), (ax_d, "D")],
        [(ax_e, "E"), (ax_f, "F")],
    ])


# ==============================================================================
# FIGURE 4 (5 panels, 2+3 Asymmetric GridSpec):
#   4A: 12-Run x 3-Persona Bidirectional Flip Forest (NC01 Fig. 4a)
#   4B: Grouped Boxplot + 12-Run Dots Across Buckets 1-3 (NC05 iDesignGPT Fig. 4g)
#   4C: White-Box CoT Decile-1 Slot-A Attention Locking (NC01 Fig. 2a)
#   4D: Empirical 200-Point DeBERTa-v3 NLI Tail Curve (Farquhar Nature Fig. 3)
#   4E: Cross-Stage NLI Phase Space + Speech-Act Polarity Filter Shift
# ==============================================================================
def make_fig4(s2, s4, ex, raw):
    fig = plt.figure(figsize=(14.4, 10.2))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.04, 1.10], hspace=0.50)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[1.06, 1.02], wspace=0.42)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[0.98, 1.06, 1.06], wspace=0.44)

    # Panel A: 12-Run x 3-Persona Flip Forest
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A")
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
        ax_a.errorbar([p_all], [idx], xerr=[[p_all - lo_p], [hi_p - p_all]], fmt="none", ecolor="#AAAAAA", elinewidth=1.6, capsize=2.2, zorder=2)
        ax_a.scatter([p1], [idx], color=C_TEAL, s=30, marker="o", zorder=3, label="SCIENCE (40.0%)" if idx == 0 else None)
        ax_a.scatter([p2], [idx], color=C_BLUE, s=30, marker="s", zorder=3, label="METHODS (42.6%)" if idx == 0 else None)
        ax_a.scatter([p3], [idx], color=C_AMBER, s=34, marker="^", zorder=3, label="NOVELTY (46.5%)" if idx == 0 else None)
        ax_a.scatter([p_all], [idx], color=C_VERM, s=50, marker="D", edgecolor="#111111", lw=0.75, zorder=4,
                     label="Run Pooled (97.0% Slot-A)" if idx == 0 else None)

    idx_p = 12
    ax_a.errorbar([43.04], [idx_p], xerr=[[43.04 - 40.04], [46.46 - 43.04]], fmt="D", color=C_VERM,
                  ecolor=C_NAVY, elinewidth=2.3, capsize=2.8, markersize=7.8, markeredgecolor="#111111", zorder=5)
    ax_a.axvline(43.04, color=C_VERM, linestyle="--", lw=1.1, alpha=0.7)
    ax_a.text(48.2, idx_p, "43.0% Flipped (p = 4.6e-168)", va="center", fontsize=7.5, fontweight="bold", color=C_VERM)

    ax_a.set_yticks(y_r)
    ax_a.set_yticklabels(labels_ord, fontsize=7.5, fontweight="bold")
    ax_a.set_xlabel("Bidirectional A/B Verdict Flip Rate (%)", fontsize=9.0, fontweight="bold")
    ax_a.set_xlim(10, 88)
    ax_a.set_ylim(-0.8, 16.2)
    ax_a.set_title("Tournament II Flip Rate Across Runs & Personas (n = 1,601)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper right", ncol=2, fontsize=7.1, frameon=False)

    # Panel B: Canonical NC05 iDesignGPT Fig. 4g Grouped Boxplot + 12-Run Dots Across Buckets 1-3!
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B")
    t1_adj = s2["audit_guided_rectification"]["tournament_I_order_adjusted_btl"]
    b_x = np.arange(3)
    b_lbls = [
        "Bucket 1 (M00-M09)\nCell-Intrinsic",
        "Bucket 2 (M10-M19)\nIntercellular",
        "Bucket 3 (M20-M29)\nECM / Complement",
    ]
    ax_b.fill_between([-0.48, 2.48], 29.0, 37.6, color=C_NAVY, alpha=0.07, zorder=1)
    ax_b.axhline(33.33, color=C_NAVY, linestyle="--", lw=1.2, label="Uniform Initial Pool Parity (33.3%)")

    rng_4b = np.random.default_rng(402)
    raw_means = [65.00, 21.67, 13.33]
    adj_means = [50.00, 25.83, 24.17]
    for bi in range(3):
        v_raw = np.array([t1_adj[r]["raw_top10_decades"][bi] * 10.0 for r in runs_ord], dtype=float)
        v_adj = np.array([t1_adj[r]["adj_top10_decades"][bi] * 10.0 for r in runs_ord], dtype=float)

        ax_b.boxplot([v_raw], positions=[bi - 0.18], widths=0.23, patch_artist=True, showfliers=False, manage_ticks=False,
                     boxprops=dict(facecolor=C_VERM, alpha=0.28, edgecolor=C_VERM, lw=1.1),
                     medianprops=dict(color=C_VERM, lw=1.6),
                     whiskerprops=dict(color=C_VERM, lw=1.0), capprops=dict(color=C_VERM, lw=1.0))
        ax_b.boxplot([v_adj], positions=[bi + 0.18], widths=0.23, patch_artist=True, showfliers=False, manage_ticks=False,
                     boxprops=dict(facecolor=C_TEAL, alpha=0.28, edgecolor=C_TEAL, lw=1.1),
                     medianprops=dict(color=C_TEAL, lw=1.6),
                     whiskerprops=dict(color=C_TEAL, lw=1.0), capprops=dict(color=C_TEAL, lw=1.0))

        ax_b.scatter(bi - 0.18 + rng_4b.uniform(-0.045, 0.045, 12), v_raw, color=C_VERM, s=24, alpha=0.72, edgecolor="#111111", lw=0.45, zorder=4)
        ax_b.scatter(bi + 0.18 + rng_4b.uniform(-0.045, 0.045, 12), v_adj, color=C_TEAL, marker="D", s=22, alpha=0.72, edgecolor="#111111", lw=0.45, zorder=4)
        ax_b.scatter([bi - 0.18], [raw_means[bi]], color="white", edgecolor=C_VERM, s=36, lw=1.4, zorder=5,
                     label="Unadjusted BTL (Chi2 = 55.4***)" if bi == 0 else None)
        ax_b.scatter([bi + 0.18], [adj_means[bi]], color="white", edgecolor=C_TEAL, marker="D", s=34, lw=1.4, zorder=5,
                     label="Order-Adjusted BTL (-72.8% Skew)" if bi == 0 else None)

        ax_b.text(bi - 0.19, float(np.max(v_raw)) + 4.8, f"{raw_means[bi]:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color=C_VERM)
        ax_b.text(bi + 0.19, float(np.max(v_adj)) + 4.8, f"{adj_means[bi]:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color=C_TEAL)

    ax_b.text(2.0, 69.5, "+81.3% Bucket-3\nRescue", ha="center", fontsize=7.6, fontweight="bold", color=C_TEAL)
    ax_b.set_xticks(b_x)
    ax_b.set_xticklabels(b_lbls, fontsize=7.8, fontweight="bold")
    ax_b.set_ylabel("Surviving Top-10 Share Across 12 Runs (%)", fontsize=9.0, fontweight="bold")
    ax_b.set_xlim(-0.54, 2.54)
    ax_b.set_ylim(-4, 126)
    ax_b.set_title("Tournament I Bucket Extinction & OA-BTL Rescue (n = 12 Runs)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="y")
    ax_b.legend(loc="upper right", fontsize=7.1, frameon=False)

    # Panel C: White-Box CoT Decile-by-Decile Slot-A Attention Trajectory
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C")
    att = ex["fig4c_cot_attention"]
    dec_x = np.arange(1, 11)
    t1_att = np.array(att["t1_deciles_pct"])
    t2_att = np.array(att["t2_deciles_pct"])

    ax_c.fill_between(dec_x, 50.0, np.maximum(50.0, t2_att), color=C_VERM, alpha=0.18, label="Decile-1 Slot-A Attention Spike")
    ax_c.axhline(50.0, color="#555555", linestyle="--", lw=1.2, label="Symmetric Attention (50.0%)")
    ax_c.plot(dec_x, t1_att, "-o", color=C_BLUE, lw=2.2, markersize=5.6, label=f"Tournament I (n={att['t1_n_traces']:,}: D1=88.4%)")
    ax_c.plot(dec_x, t2_att, "-D", color=C_VERM, lw=2.2, markersize=5.6, label=f"Tournament II (n={att['t2_n_traces']:,}: D1=90.6%)")
    ax_c.text(2.3, 86.0, "88.4%-90.6%\nSlot-A Anchor", fontsize=7.5, fontweight="bold", color=C_VERM)

    ax_c.set_xticks([1, 2, 4, 6, 8, 10])
    ax_c.set_xlabel("Reasoning Trace Decile (1 = Start, 10 = End)", fontsize=8.9, fontweight="bold")
    ax_c.set_ylabel("Slot-A Entity Mention Share (%)", fontsize=8.9, fontweight="bold")
    ax_c.set_xlim(0.6, 10.4)
    ax_c.set_ylim(25, 126)
    ax_c.set_title("White-Box CoT Slot-A Attention Locking", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="both")
    ax_c.legend(loc="upper right", fontsize=6.9, frameon=False)

    # Panel D: Exact 200-Point Empirical DeBERTa-v3 NLI Contradiction Tail Curve
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D")
    f4c_ex = ex["fig4c_exact"]
    tau = np.array(f4c_ex["taus"], dtype=float)
    c_dir = np.array(f4c_ex["cons_dir_pct"], dtype=float)
    b_dir = np.array(f4c_ex["biased_dir_pct"], dtype=float)
    c_bi = np.array(f4c_ex["cons_bidir_pct"], dtype=float)
    b_bi = np.array(f4c_ex["biased_bidir_pct"], dtype=float)

    ax_d.fill_between(tau, c_dir, b_dir, step="post", color=C_PURPLE, alpha=0.22, label="Flipped Rationale Excess Area")
    ax_d.step(tau, b_dir, where="post", color=C_VERM, lw=2.2, label="Flipped: Directional (25.4% at 0.75)")
    ax_d.step(tau, c_dir, where="post", color=C_TEAL, lw=2.1, label="Consistent: Directional (10.0% at 0.75)")
    ax_d.step(tau, b_bi, where="post", linestyle="--", color=C_PURPLE, lw=1.8, label="Flipped: Bidirectional (7.1% at 0.75)")
    ax_d.step(tau, c_bi, where="post", linestyle="--", color=C_BLUE, lw=1.7, label="Consistent: Bidirectional (2.1%)")
    ax_d.plot([0.75, 0.75], [0, 62.0], color="#222222", linestyle=":", lw=1.2)
    ax_d.scatter([0.75, 0.75, 0.75, 0.75], [25.42, 10.00, 7.08, 2.08],
                 color=[C_VERM, C_TEAL, C_PURPLE, C_BLUE], s=46, edgecolor="#111111", zorder=5)
    ax_d.annotate("2.54x (p=1.15e-5)", xy=(0.75, 25.42), xytext=(0.38, 60.0),
                  fontsize=7.5, fontweight="bold", color=C_VERM, arrowprops=dict(arrowstyle="->", lw=1.1, color=C_VERM))

    ax_d.set_xlabel(r"DeBERTa-v3 NLI Threshold $\tau$", fontsize=8.9, fontweight="bold")
    ax_d.set_ylabel(r"Judge Pairs Exceeding $\tau$ (%)", fontsize=8.9, fontweight="bold")
    ax_d.set_xlim(0, 1.0)
    ax_d.set_ylim(0, 132)
    ax_d.set_title("Empirical Judge Rationale NLI Curve (n = 480)", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="both")
    ax_d.legend(loc="upper right", fontsize=6.8, frameon=False)

    # Panel E: 2D Cross-Stage NLI Phase Space + Speech-Act Polarity Filter Vector
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E")
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
            ax_e.scatter([xv], [yv], s=50 + prop * 34, color=col, alpha=0.78, marker=mk,
                         edgecolor="#111111", lw=0.85, zorder=4, label=glbl if r == 1 else None)

    ax_e.fill_between([0, 60.0], -6, 20.0, color=C_TEAL, alpha=0.09, zorder=1)
    ax_e.scatter([94.56], [28.88], color=C_RED_DARK, marker="X", s=86, edgecolor="#111111", zorder=6, label="Raw Mean (51/1,766)")
    ax_e.scatter([38.9], [11.89], color=C_TEAL, marker="*", s=118, edgecolor="#111111", zorder=6, label="Polarity-Gated (21/1,766)")
    ax_e.annotate("", xy=(43.0, 13.5), xytext=(90.0, 27.5),
                  arrowprops=dict(arrowstyle="->", lw=1.9, linestyle="--", color=C_TEAL))
    ax_e.text(112.0, 76.0, "43.1% Raw Reach Top-5\n-76% Polarity False Flags", fontsize=7.3, fontweight="bold", color=C_NAVY, va="top")

    ax_e.set_xlabel("Directional NLI Flags / 1,000 Pairs", fontsize=8.9, fontweight="bold")
    ax_e.set_ylabel("Bidirectional NLI Flags / 1,000", fontsize=8.9, fontweight="bold")
    ax_e.set_xlim(0, 285)
    ax_e.set_ylim(-8, 166)
    ax_e.set_title("Cross-Stage NLI & Speech-Act Gating", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="both")
    ax_e.legend(loc="upper left", ncol=1, fontsize=6.8, frameon=False)

    save_fig(fig, "Fig4_Dim3_Dim5_Primacy_and_NLI", rows_spec=[
        [(ax_a, "A"), (ax_b, "B")],
        [(ax_c, "C"), (ax_d, "D"), (ax_e, "E")],
    ])


# ==============================================================================
# FIGURE 5 (4 panels, Asymmetric GridSpec):
#   5A: 4-Cell Paired Verdict-Bootstrap Null Violin vs Observed Cross-Run Dots
#       (Canonical Robin Nature 2026 ED Fig. 4c Null-vs-Observed Grammar!)
#   5B: Clean Confidence Calibration Reliability Curve (GLM-5.3 + Argon/Flash)
#   5C: Horizontal Violins + IQR for Paradoxes 1 & 2 (NC02 Fig. 6a-c)
#   5D: Vertical Raincloud for Paradox 3 (1.4-1.7x Longer Failed Spin)
# ==============================================================================
def make_fig5(s2, s3, ex, raw):
    fig = plt.figure(figsize=(14.2, 9.9))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.03, 1.07], width_ratios=[1.08, 1.0], hspace=0.52, wspace=0.42)

    # Panel A: Canonical Robin ED Fig. 4c Paired Null Violin vs Observed Cross-Run Dots Across 4 Cells!
    ax_a = fig.add_subplot(gs[0, 0])
    add_panel_label(ax_a, "A")
    boot_runs = s2["dimension_4_stability_bootstrap"]
    pw = ex["fig3b_5a_pairwise"]
    cells_5a = [
        ("dAMD_blind", "dAMD Blind\n(R1-R3)", pw["dAMD"]["within_lead_genes"][:3]),
        ("dAMD_retrieval", "dAMD Retrieval\n(R1-R3)", pw["dAMD"]["within_lead_genes"][3:]),
        ("ALS_blind", "ALS Blind\n(R1-R3)", pw["ALS"]["within_lead_genes"][:3]),
        ("ALS_retrieval", "ALS Retrieval\n(R1-R3)", pw["ALS"]["within_lead_genes"][3:]),
    ]
    xc = np.arange(len(cells_5a))
    cell_boot_arrays = []
    cell_boot_means, cell_boot_lo, cell_boot_hi = [], [], []
    for prefix, _, _ in cells_5a:
        pooled_draws = np.concatenate([
            np.array(ex["fig5a_boot"][f"{prefix}_R{r}"]["empirical_jaccard_draws_1000"], dtype=float)
            for r in [1, 2, 3]
        ])
        cell_boot_arrays.append(pooled_draws)
        cell_boot_means.append(float(np.mean([boot_runs[f"{prefix}_R{r}"]["boot_pairwise_jaccard_mean"] for r in [1, 2, 3]])))
        cell_boot_lo.append(float(np.mean([boot_runs[f"{prefix}_R{r}"]["boot_pairwise_jaccard_95ci"][0] for r in [1, 2, 3]])))
        cell_boot_hi.append(float(np.mean([boot_runs[f"{prefix}_R{r}"]["boot_pairwise_jaccard_95ci"][1] for r in [1, 2, 3]])))

    vparts = ax_a.violinplot(cell_boot_arrays, positions=xc - 0.16, vert=True, widths=0.30,
                             showmeans=False, showextrema=False, showmedians=False)
    for pc in vparts["bodies"]:
        pc.set_facecolor(C_SKY)
        pc.set_edgecolor(C_BLUE)
        pc.set_alpha(0.45)

    ax_a.errorbar(xc - 0.16, cell_boot_means,
                  yerr=[[m - l for m, l in zip(cell_boot_means, cell_boot_lo)],
                        [h - m for m, h in zip(cell_boot_means, cell_boot_hi)]],
                  fmt="o", color=C_NAVY, ecolor=C_BLUE, elinewidth=1.9, capsize=3.2, markersize=5.8, zorder=5,
                  label="Within-Run Verdict Bootstrap Null (Mean & 95% CI)")

    for i, (_, _, obs_3) in enumerate(cells_5a):
        obs_arr = np.array(obs_3, dtype=float)
        m_obs = float(np.mean(obs_arr))
        se_obs = float(np.std(obs_arr, ddof=1) / math.sqrt(3)) if len(obs_arr) > 1 else 0.0
        jit = np.array([-0.045, 0.0, 0.045])
        ax_a.errorbar([xc[i] + 0.16], [m_obs], yerr=[se_obs], fmt="D", color=C_VERM, ecolor=C_VERM,
                      elinewidth=2.0, capsize=3.2, markersize=6.4, markeredgecolor="#111111", zorder=6,
                      label="Observed Cross-Run Replicates (Mean +/- SEM)" if i == 0 else None)
        ax_a.scatter(xc[i] + 0.16 + jit, obs_arr, color=C_RED_DARK, s=24, alpha=0.68, zorder=4)
        ax_a.plot([xc[i] - 0.16, xc[i] - 0.16, xc[i] + 0.16, xc[i] + 0.16],
                  [1.03, 1.08, 1.08, 1.03], color="#333333", lw=1.0)
        ax_a.text(xc[i], 1.11, "p = 0.0002***", ha="center", fontsize=7.3, fontweight="bold", color=C_NAVY)

    ax_a.axvline(1.5, color="#999999", linestyle=":", lw=1.1)
    ax_a.set_xticks(xc)
    ax_a.set_xticklabels([c[1] for c in cells_5a], fontsize=7.9, fontweight="bold")
    ax_a.set_ylabel("Pairwise Top-5 Lead-Gene Jaccard", fontsize=9.0, fontweight="bold")
    ax_a.set_xlim(-0.54, 3.54)
    ax_a.set_ylim(-0.05, 1.50)
    ax_a.set_title("Verdict-Bootstrap Null vs. Observed Stability (q = 0.0012*)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="y")
    ax_a.legend(loc="upper left", fontsize=7.1, frameon=False)

    # Panel B: Clean ML Reliability / Calibration Diagram
    ax_b = fig.add_subplot(gs[0, 1])
    add_panel_label(ax_b, "B")
    cal_p = s3["dim6_self_knowledge"]["parent_pooled_n480"]
    x_bef = np.array([b["mean_conf"] * 100 for b in cal_p["bins_before"]])
    y_bef = np.array([b["emp_acc"] * 100 for b in cal_p["bins_before"]])
    n_bef = [b["n"] for b in cal_p["bins_before"]]
    x_aft = np.array([b["mean_conf"] * 100 for b in cal_p["bins_after"]])
    y_aft = np.array([b["emp_acc"] * 100 for b in cal_p["bins_after"]])

    ax_b.plot([0, 100], [0, 100], linestyle="--", color="#555555", lw=1.3, label="Perfect Calibration (Slope = 1.0)")
    ax_b.fill_between(x_bef, y_bef, x_bef, color=C_VERM, alpha=0.16, label="Overconfidence Gap (ECE = 0.222)")
    ax_b.plot(x_bef, y_bef, "-o", lw=2.3, color=C_VERM, markersize=5.8, label=f"GLM-5.3 Raw Confidence (ECE = {cal_p['ece_before']:.3f})")
    ax_b.plot(x_aft, y_aft, "-s", lw=2.3, color=C_TEAL, markersize=5.8, label=f"Selective Platt Recalibrated (ECE = {cal_p['ece_after_loro_platt']:.3f})")

    ax_b.scatter([69.63], [65.00], color=C_NAVY, marker="D", s=58, edgecolor="#111111", zorder=6,
                 label="Gemini-4-Argon Native Preserved (ECE = 0.080)")
    ax_b.scatter([80.90], [26.67], color=C_PURPLE, marker="^", s=56, edgecolor="#111111", zorder=5,
                 label="Gemini-3.8-Flash Raw -> Gate (0.542 -> 0.075)")
    ax_b.annotate("", xy=(28.5, 26.67), xytext=(78.5, 26.67),
                  arrowprops=dict(arrowstyle="->", lw=1.5, linestyle=":", color=C_PURPLE))

    for xb_i, yb_i, nb_i in zip(x_bef, y_bef, n_bef):
        if 60.0 <= xb_i <= 70.0:
            dx_pt, dy_pt = -15, 7
        else:
            dx_pt, dy_pt = 0, -13
        ax_b.annotate(f"n={nb_i}", (xb_i, yb_i), textcoords="offset points", xytext=(dx_pt, dy_pt),
                      ha="center", fontsize=7.3, color=C_VERM, fontweight="bold")

    ax_b.set_xlabel("Predicted Survival / Recall Probability (%)", fontsize=9.0, fontweight="bold")
    ax_b.set_ylabel("Empirical Survival / Recall Rate (%)", fontsize=9.0, fontweight="bold")
    ax_b.set_xlim(0, 100)
    ax_b.set_ylim(-10, 134)
    ax_b.set_title("Verbalized Overconfidence & Selective Platt Gate", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="both")
    ax_b.legend(loc="upper left", fontsize=6.9, frameon=False)

    # Panel C: Paradoxes 1 & 2 Horizontal Violins
    ax_c = fig.add_subplot(gs[1, 0])
    add_panel_label(ax_c, "C")
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
        pc.set_linewidth(0.85)

    for idx, arr in enumerate(c_arrays):
        q25, med, q75 = np.percentile(arr, [25, 50, 75])
        ax_c.plot([q25, q75], [y_c[idx], y_c[idx]], color="#111111", lw=2.8, zorder=4,
                  label="Interquartile Range (25th-75th)" if idx == 0 else None)
        ax_c.scatter([med], [y_c[idx]], color="white", edgecolor=c_cols[idx], s=38, lw=1.5, zorder=5,
                     label="Group Median (k Tokens)" if idx == 0 else None)

    ax_c.plot([9.2, 9.8, 9.8, 9.2], [0.0, 0.0, 1.0, 1.0], color="#333333", lw=1.0)
    ax_c.text(10.3, 0.5, "p = 0.0254*", va="center", ha="left", fontsize=7.8, fontweight="bold", color=C_VERM)
    ax_c.axhline(1.5, color="#888888", linestyle="--", lw=1.0)
    ax_c.set_yticks(y_c)
    ax_c.set_yticklabels(c_labels, fontsize=7.8, fontweight="bold")
    ax_c.set_xlabel("Internal Reasoning Tokens per Call (k)", fontsize=9.0, fontweight="bold")
    ax_c.set_xlim(-0.5, 27.0)
    ax_c.set_ylim(-0.7, 4.7)
    ax_c.set_title("Paradoxes 1 & 2: CoT Spin in Flips & Citation Dredging", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="lower right", fontsize=7.3, frameon=False)

    # Panel D: Paradox 3 Vertical Raincloud
    ax_d = fig.add_subplot(gs[1, 1])
    add_panel_label(ax_d, "D")
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
        pc.set_linewidth(0.85)

    rng_d = np.random.default_rng(42)
    for idx, arr in enumerate(d_arrays):
        sub = arr if len(arr) <= 80 else rng_d.choice(arr, size=80, replace=False)
        ax_d.scatter(x_d[idx] + rng_d.uniform(-0.14, 0.14, size=len(sub)), sub, color=d_cols[idx], alpha=0.35, s=12, zorder=3)
        q25, med, q75 = np.percentile(arr, [25, 50, 75])
        ax_d.plot([x_d[idx], x_d[idx]], [q25, q75], color="#111111", lw=2.9, zorder=4)
        ax_d.scatter([x_d[idx]], [med], color="white", edgecolor=d_cols[idx], s=42, lw=1.6, zorder=5)
        ax_d.text(x_d[idx], float(np.max(arr)) + 1.4, f"{med:.1f}k", ha="center", fontsize=7.6, fontweight="bold", color=d_cols[idx])

    ax_d.plot([0, 0, 1, 1], [37.5, 41.2, 41.2, 38.5], color="#222222", lw=1.0)
    ax_d.text(0.5, 42.5, "p = 2.0e-16*** (1.70x)", ha="center", fontsize=7.4, fontweight="bold", color=C_VERM)
    ax_d.plot([2, 2, 3, 3], [37.5, 41.2, 41.2, 38.5], color="#222222", lw=1.0)
    ax_d.text(2.5, 42.5, "p = 1.4e-5*** (1.39x)", ha="center", fontsize=7.4, fontweight="bold", color=C_RED_DARK)

    ax_d.set_xticks(x_d)
    ax_d.set_xticklabels(d_labels, fontsize=7.7, fontweight="bold")
    ax_d.set_ylabel("Internal Reasoning Tokens per Call (k)", fontsize=9.0, fontweight="bold")
    ax_d.set_xlim(-0.6, 3.6)
    ax_d.set_ylim(0, 49.5)
    ax_d.set_title("Paradox 3: Failed Mendelian Calls Spin 1.4-1.7x Longer", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="y")

    save_fig(fig, "Fig5_Dim4_Dim6_Reasoning_Paradox", rows_spec=[
        [(ax_a, "A"), (ax_b, "B")],
        [(ax_c, "C"), (ax_d, "D")],
    ])


# ==============================================================================
# FIGURE 6 (5 panels, 2+3 Asymmetric GridSpec):
#   6A: T1 & T2 Primacy Log-Odds Intercepts with Symmetric Hessian 95% CIs
#   6B: 9 Gold-Standard Biological Pathways Rescued into Surviving Top-10
#   6C: Horizontal Paired 4-Pillar Point-Intervals + Run/Domain Dots (NC04 Fig. 2)
#   6D: Incremental Module-Addition Curves with Per-Curve 95% CI Bands (NC01 Fig. 6)
#   6E: Empirical 2D Pareto Frontier with Token IQR & Score 95% CI Crosshairs
# ==============================================================================
def make_fig6(s2, a1, ex, expB_slots, raw):
    fig = plt.figure(figsize=(14.4, 10.2))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.05, 1.10], hspace=0.50)
    gs_top = gs[0, 0].subgridspec(1, 2, width_ratios=[0.98, 1.08], wspace=0.52)
    gs_bot = gs[1, 0].subgridspec(1, 3, width_ratios=[1.12, 0.96, 1.04], wspace=0.44)

    # Panel A: OA-BTL Primacy Intercepts with Hessian 95% CIs on BOTH T1 and T2!
    ax_a = fig.add_subplot(gs_top[0, 0])
    add_panel_label(ax_a, "A")
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
    t2_h = ex["fig6a_t2_hessian"]
    g1 = [a1_emp[r]["gamma_t1_full_oa"] for r in runs_12]
    ci1 = [a1_emp[r]["gamma_t1_full_se"] * 1.96 for r in runs_12]
    g2 = [t2_adj[r]["t2_gamma_primacy"] for r in runs_12]
    ci2 = [t2_h[r]["se_t2"] * 1.96 for r in runs_12]

    y_pos = np.arange(len(runs_12))
    ax_a.fill_betweenx([-0.8, 11.8], 0.99, 1.41, color=C_SKY, alpha=0.12, zorder=1)
    ax_a.fill_betweenx([-0.8, 11.8], 1.48, 1.93, color=C_VERM, alpha=0.09, zorder=1)
    ax_a.axvline(0.0, color="#222222", linestyle="--", lw=1.1, label="Fairness Null (gamma = 0)")
    ax_a.errorbar(g1, y_pos + 0.16, xerr=ci1, fmt="o", color=C_BLUE, ecolor=C_SKY,
                  elinewidth=1.6, capsize=2.4, markersize=5.2, label=r"Tournament I $\hat{\gamma}_{\mathrm{T1}}$ +/- 95% CI")
    ax_a.errorbar(g2, y_pos - 0.16, xerr=ci2, fmt="D", color=C_VERM, ecolor=C_AMBER,
                  elinewidth=1.6, capsize=2.4, markersize=5.0, label=r"Tournament II $\hat{\gamma}_{\mathrm{T2}}$ +/- 95% CI")

    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(labels_12, fontsize=7.5, fontweight="bold")
    ax_a.set_xlabel(r"Estimated Slot-A Primacy Log-Odds Intercept ($\hat{\gamma}$)", fontsize=9.0, fontweight="bold")
    ax_a.set_xlim(-0.25, 3.70)
    ax_a.set_ylim(-0.8, 15.6)
    ax_a.set_title("OA-BTL Slot-A Primacy Intercepts Across 12 Runs", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_a, grid_axis="x")
    ax_a.legend(loc="upper left", fontsize=7.1, frameon=False)

    # Panel B: 9 Gold-Standard Pathways Rescued into Surviving Top-10
    ax_b = fig.add_subplot(gs_top[0, 1])
    add_panel_label(ax_b, "B")
    rescued_examples = [
        ("dAMD Retr 1: M23 GAS6/MERTK*", 11, 7),
        ("dAMD Retr 2: M25 TIMP3/MMP9*", 15, 8),
        ("dAMD Retr 3: M25 ABCA1/LIPC*", 15, 6),
        ("dAMD Retr 3: M14 CD59 MAC*", 11, 5),
        ("dAMD Blind 1: M22 APOB100*", 12, 6),
        ("ALS Blind 1: M18 C1QA/C3*", 13, 10),
        ("ALS Blind 2: M26 MMP9/LAMA1*", 13, 6),
        ("ALS Blind 3: M25 MCT1/SLC16A1*", 11, 7),
        ("ALS Retr 3: M29 CCS/ATP7A*", 15, 10),
    ][::-1]
    y_res = np.arange(len(rescued_examples))
    raw_ranks = [x[1] for x in rescued_examples]
    adj_ranks = [x[2] for x in rescued_examples]

    ax_b.fill_betweenx([-0.8, 8.8], 0.5, 10.5, color=C_TEAL, alpha=0.11, label="Surviving Top-10 Dossier Cutoff (<=10)")
    ax_b.axvline(10.5, color=C_TEAL, linestyle="--", lw=1.4)
    for idx in range(len(rescued_examples)):
        ax_b.annotate("", xy=(adj_ranks[idx] + 0.34, y_res[idx]), xytext=(raw_ranks[idx] - 0.34, y_res[idx]),
                      arrowprops=dict(arrowstyle="->", color=C_TEAL, lw=1.8))
        ax_b.text(raw_ranks[idx] + 0.65, y_res[idx], f"#{raw_ranks[idx]}", va="center", ha="right", fontsize=7.5, color=C_VERM, fontweight="bold")
        ax_b.text(adj_ranks[idx] - 0.65, y_res[idx], f"#{adj_ranks[idx]}", va="center", ha="left", fontsize=7.5, color=C_TEAL, fontweight="bold")
    ax_b.scatter(raw_ranks, y_res, color=C_VERM, s=56, zorder=4, label="Unadjusted BTL Rank (Eliminated >10)")
    ax_b.scatter(adj_ranks, y_res, color=C_TEAL, s=56, marker="D", zorder=4, label="Order-Adjusted BTL Rank (Rescued <=10)")

    ax_b.set_yticks(y_res)
    ax_b.set_yticklabels([x[0] for x in rescued_examples], fontsize=7.5, fontweight="bold")
    ax_b.set_xlabel("Tournament I Candidate Rank (1 = Best; <=10 Survives)", fontsize=9.0, fontweight="bold")
    ax_b.set_xlim(22.8, 1.8)
    ax_b.set_ylim(-0.8, 11.9)
    ax_b.set_title("OA-BTL Rescues 9/9 Gold-Standard Pathways (*)", fontsize=9.6, fontweight="bold", loc="left")
    style_ax(ax_b, grid_axis="x")
    ax_b.legend(loc="upper left", fontsize=7.0, frameon=False)

    # Panel C: Canonical Horizontal Paired Point-Intervals + Run/Domain Dots Across 4 Pillars!
    ax_c = fig.add_subplot(gs_bot[0, 0])
    add_panel_label(ax_c, "C")
    b3_bef = np.array([min(100.0, 30.0 * t1_adj[r]["raw_top10_decades"][2]) for r in runs_12])
    b3_aft = np.array([min(100.0, 30.0 * t1_adj[r]["adj_top10_decades"][2]) for r in runs_12])
    t2_bef = np.array([(1.0 - s2["dimension_3_position_bias"]["tournament_II_by_run"][r]["pos_bias_rate"]) * 100.0 for r in runs_12])
    t2_aft = np.full(12, 100.0)
    cit_bef = np.array([
        sum(1 for r in expB_slots if r["domain_id"] == f"B{i:02d}" and r["arm"] == "as_discovered" and r["resolved"] and r["on_topic"]) / 30.0 * 100.0
        for i in range(1, 15)
    ])
    cit_aft = np.full(14, 100.0)

    pillars = [
        ("Calibration\n(100 - ECE)", 77.79, 3.6, 97.26, 1.5, None, None),
        ("Closed-Loop\nCitations", 42.62, float(1.96 * np.std(cit_bef, ddof=1) / math.sqrt(14)), 100.00, 0.0, cit_bef, cit_aft),
        ("T2 Order\nConsistency", 56.96, float(1.96 * np.std(t2_bef, ddof=1) / math.sqrt(12)), 100.00, 0.0, t2_bef, t2_aft),
        ("T1 Bucket-3\nParity (3x)", 40.00, float(1.96 * np.std(b3_bef, ddof=1) / math.sqrt(12)), 72.50, float(1.96 * np.std(b3_aft, ddof=1) / math.sqrt(12)), b3_bef, b3_aft),
    ]
    yp = np.arange(4)
    rng_6c = np.random.default_rng(603)
    ax_c.fill_betweenx([-0.65, 3.85], 90.0, 102.0, color=C_TEAL, alpha=0.08, zorder=1)

    for idx, (plbl, m0, ci0, m1, ci1, pts0, pts1) in enumerate(pillars):
        if pts0 is not None:
            ax_c.scatter(pts0, yp[idx] + 0.18 + rng_6c.uniform(-0.03, 0.03, len(pts0)), color=C_VERM, alpha=0.35, s=17, zorder=2)
            ax_c.scatter(pts1, yp[idx] - 0.18 + rng_6c.uniform(-0.03, 0.03, len(pts1)), color=C_TEAL, marker="D", alpha=0.35, s=16, zorder=2)
        ax_c.errorbar([m0], [yp[idx] + 0.18], xerr=[[min(m0, ci0)], [min(100.0 - m0, ci0)]], fmt="o",
                      color=C_VERM, ecolor=C_VERM, elinewidth=2.0, capsize=2.8, markersize=6.4, markeredgecolor="#111111", zorder=5,
                      label="Before: Unrectified (+/- 95% CI)" if idx == 0 else None)
        ax_c.errorbar([m1], [yp[idx] - 0.18], xerr=[[min(m1, ci1)], [min(100.0 - m1, ci1)]], fmt="D",
                      color=C_TEAL, ecolor=C_TEAL, elinewidth=2.0, capsize=2.8, markersize=6.2, markeredgecolor="#111111", zorder=5,
                      label="After: STAR-Audit (+/- 95% CI)" if idx == 0 else None)
        ax_c.text(m0, yp[idx] + 0.29, f"{m0:.1f}%", va="bottom", ha="center", fontsize=7.2, fontweight="bold", color=C_VERM)
        ax_c.text(m1, yp[idx] - 0.29, f"{m1:.1f}%", va="top", ha="center", fontsize=7.2, fontweight="bold", color=C_TEAL)

    ax_c.set_yticks(yp)
    ax_c.set_yticklabels([p[0] for p in pillars], fontsize=7.6, fontweight="bold")
    ax_c.set_xlabel("Normalized Pillar Score (0-100%)", fontsize=8.9, fontweight="bold")
    ax_c.set_xlim(-6, 116)
    ax_c.set_ylim(-0.84, 4.72)
    ax_c.set_title("Normalized Four-Pillar Paired Comparison", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_c, grid_axis="x")
    ax_c.legend(loc="upper left", fontsize=6.9, frameon=False)

    # Panel D: Canonical NC01 Brockers Fig. 6 Incremental Module Addition with Per-Curve 95% CI Bands!
    ax_d = fig.add_subplot(gs_bot[0, 1])
    add_panel_label(ax_d, "D")
    st_x = np.array([0, 1, 2, 3])
    s_norm = np.array([54.34, 63.27, 78.09, 92.44])
    s_raw = np.array([47.67, 56.60, 66.02, 80.36])
    b6 = ex["fig6de_bootstrap"]
    ci_norm = np.array(b6["s_norm_ci95_half"])
    ci_raw = np.array(b6["s_raw_ci95_half"])

    ax_d.fill_between(st_x, s_norm - ci_norm, np.minimum(100.0, s_norm + ci_norm), color=C_TEAL, alpha=0.16)
    ax_d.fill_between(st_x, s_raw - ci_raw, s_raw + ci_raw, color=C_NAVY, alpha=0.12)
    ax_d.errorbar(st_x, s_norm, yerr=b6["s_norm_se"], fmt="-D", color=C_TEAL, ecolor=C_TEAL, lw=2.3, elinewidth=1.2,
                  capsize=2.6, markersize=6.2, markeredgecolor="#111111", label=r"Normalized $S_{\mathrm{norm}}$ (+/- 95% CI)")
    ax_d.errorbar(st_x, s_raw, yerr=b6["s_raw_se"], fmt="--o", color=C_NAVY, ecolor=C_NAVY, lw=1.9, elinewidth=1.1,
                  capsize=2.4, markersize=5.4, markeredgecolor="#111111", label=r"Unweighted $S_{\mathrm{raw}}$ (+/- 95% CI)")
    for xi, yn, cn in zip(st_x, s_norm, ci_norm):
        ax_d.text(xi, min(100.0, yn + cn) + 2.8, f"{yn:.1f}%", ha="center", fontsize=7.4, fontweight="bold", color=C_TEAL)

    ax_d.set_xticks(st_x)
    ax_d.set_xticklabels(["Baseline\nUnrect.", "+Abstain\nSafety", "+OA-BTL\n& Platt", "Full Closed\nSTAR-Audit"], fontsize=7.3, fontweight="bold")
    ax_d.set_ylabel("Composite Pipeline Score (%)", fontsize=8.9, fontweight="bold")
    ax_d.set_xlim(-0.38, 3.38)
    ax_d.set_ylim(36, 124)
    ax_d.set_title("Incremental Module Gain (+38.1 pp)", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_d, grid_axis="y")
    ax_d.legend(loc="upper left", fontsize=7.0, frameon=False)

    # Panel E: Empirical 2D Pareto Frontier with Token IQR & Bootstrap 95% CI Crosshairs
    ax_e = fig.add_subplot(gs_bot[0, 2])
    add_panel_label(ax_e, "E")
    ax_e.fill_between([0.0, 4.2], 82.0, 103.0, color=C_TEAL, alpha=0.09, label="Pareto-Optimal Zone")

    q_asd = np.percentile(raw["expB_arm_rt"]["as_discovered"], [25, 50, 75])
    q_abs = np.percentile(raw["expB_arm_rt"]["abstain_probe"], [25, 50, 75])
    q_gat = np.percentile(raw["expB_arm_rt"]["gated"], [25, 50, 75])

    pts = [
        ("Unrectified (11.8k CoT)", q_asd, 54.34, ci_norm[0], C_VERM, "o", (0, -3.2), "top", "center"),
        ("+ Abstain Probe (8.9k)", q_abs, 63.27, ci_norm[1], C_AMBER, "s", (-0.6, 2.8), "bottom", "right"),
        ("+ OA-BTL & Platt (11.8k)", q_asd, 78.09, ci_norm[2], C_BLUE, "^", (0, 2.8), "bottom", "center"),
        ("Full STAR-Audit (1.1k, -90.4%)", q_gat, 92.44, ci_norm[3], C_TEAL, "D", (0.5, 2.8), "bottom", "left"),
    ]
    for label, (q25, med_x, q75), y_sc, y_ci, col, mk, (dx_d, dy_d), va_m, ha_m in pts:
        y_lo = y_ci
        y_hi = min(100.0 - y_sc, y_ci)
        ax_e.errorbar([med_x], [y_sc],
                      xerr=[[max(0.0, med_x - q25)], [max(0.0, q75 - med_x)]],
                      yerr=[[y_lo], [y_hi]],
                      fmt=mk, color=col, ecolor=col, elinewidth=1.6, capsize=2.6,
                      markersize=8.2, markeredgecolor="#111111", zorder=4, label=label)
        y_txt = (y_sc - y_lo + dy_d) if dy_d < 0 else (y_sc + y_hi + dy_d)
        ax_e.text(med_x + dx_d, y_txt, f"{y_sc:.1f}%", ha=ha_m, va=va_m,
                  fontsize=7.4, fontweight="bold", color=col)
    ax_e.annotate("", xy=(1.65, 90.8), xytext=(11.2, 55.8),
                  arrowprops=dict(arrowstyle="->", lw=1.9, linestyle="--", color=C_TEAL, connectionstyle="arc3,rad=-0.16"))

    ax_e.set_xlabel("Citation CoT Compute (k Tokens/Call, Median & IQR)", fontsize=8.8, fontweight="bold")
    ax_e.set_ylabel("Composite Trustworthiness Score (%)", fontsize=8.9, fontweight="bold")
    ax_e.set_xlim(-0.8, 16.8)
    ax_e.set_ylim(22, 110)
    ax_e.set_title("Trustworthiness vs. Compute Pareto Frontier", fontsize=9.4, fontweight="bold", loc="left")
    style_ax(ax_e, grid_axis="both")
    ax_e.legend(loc="lower left", fontsize=6.7, frameon=False)

    save_fig(fig, "Fig6_Audit_Guided_Rectification_Impact", rows_spec=[
        [(ax_a, "A"), (ax_b, "B")],
        [(ax_c, "C"), (ax_d, "D"), (ax_e, "E")],
    ])


@retry_limit(2)
def main():
    s1, s2, s3, s4, a1, a2, a6, ex, expB_slots, raw = load_data()
    canary_gate(lambda: "fig3e_lit_footprint" in ex, "Verify canonical arrays loaded")
    make_fig1(ex, raw)
    make_fig2(s1, a2, ex, expB_slots, raw)
    make_fig3(s2, ex)
    make_fig4(s2, s4, ex, raw)
    make_fig5(s2, s3, ex, raw)
    make_fig6(s2, a1, ex, expB_slots, raw)
    print("ALL 6 CANONICAL MAIN FIGURES GENERATED SUCCESSFULLY IN:", FIG_DIR)


if __name__ == "__main__":
    main()
