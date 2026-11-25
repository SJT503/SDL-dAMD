#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministically synchronizes all English manuscripts, supplementary materials,
cover letters, and Chinese Desktop review files with the complete 4-family
(GLM-5.3, DeepSeek-V4-Pro, Google Gemini-Pro/Flash, xAI Grok-4.7/Fast),
11,818-evaluation (36.03M reasoning tokens) results.
"""

import os
import shutil

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
DESKTOP = r"C:\Users\sheng\Desktop"


def read_lf(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def write_lf(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def replace_exact(text, old, new, label=""):
    if old not in text:
        raise ValueError(f"Missing target in {label}:\n{old[:200]}...")
    return text.replace(old, new, 1)


def update_nature_manuscript():
    path = os.path.join(BASE, "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md")
    s = read_lf(path)

    # 1. Abstract (< 200 words)
    old_abs = (
        "## Abstract\n"
        "Autonomous multi-agent systems combine hypothesis generation, pairwise tournaments, and literature grounding for therapeutic discovery, yet whether test-time reasoning ensures pipeline trustworthiness remains unknown. Here we present **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost remediation framework covering faithfulness, reasoning versus memorization, positional fairness, stability, coherence, and calibration. Auditing 9,130 primary API calls (35.58 million reasoning tokens; 93.83% of output) on GLM-5.3 and DeepSeek-V4-Pro plus 1,344 cross-ecosystem evaluations on Google Gemini (Pro and Flash) across 136 diseases uncovers a test-time reasoning paradox: deeper chain-of-thought fails to self-correct pipeline biases. Naive checks score 96.9–100.0% of protocol PubMed identifiers as existent, whereas two-tier verification exposes 54.3–73.8% Trojan horse citations driven by 35.8 candidate identifiers dredged per call in chain-of-thought. Epistemic gating cuts ungrounded citations by 50.0–73.8 percentage points ($p \\le 0.00097$), eliminates fabricated identifiers ($q_{\\text{BH}} = 0.03096$), and reduces citation reasoning tokens by 86.2%. Furthermore, Tournament I exhibits a 71.3% Slot-A win rate suppressing Bucket-3 pathways ($\\chi^2 = 55.40$), while 17.8–43.0% of Tournament II pairs flip under A/B reversal and 23.3% of failed Mendelian inferences self-prune causal genes activated at 2.1% chain-of-thought depth. Four zero-call modules—Order-Adjusted Bradley–Terry–Luce ranking, Platt scaling, epistemic gating, and CoT-SRAD—rescue validated targets, cut calibration error by 74.1–89.5%, and boost Mendelian recall by 57.1% ($p = 9.43 \\times 10^{-7}$)."
    )
    new_abs = (
        "## Abstract\n"
        "Autonomous multi-agent systems combine hypothesis generation, pairwise tournaments, and literature grounding for therapeutic discovery, yet whether test-time reasoning ensures pipeline trustworthiness remains unknown. Here we present **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost remediation framework covering faithfulness, reasoning versus memorization, positional fairness, stability, coherence, and calibration. Auditing 9,130 primary calls (35.58 million reasoning tokens; 93.83% of output) on GLM-5.3 and DeepSeek-V4-Pro plus 2,688 cross-ecosystem evaluations on Google Gemini (Pro/Flash) and xAI Grok (Grok-4.7/Fast) across 136 diseases uncovers a test-time reasoning paradox: deeper chain-of-thought fails to self-correct pipeline biases. Naive checks score 96.9–100.0% of protocol PubMed identifiers as existent, whereas two-tier verification exposes 32.1–73.8% Trojan horse citations driven by 35.8 candidate identifiers dredged per call. Epistemic gating cuts ungrounded citations by 32.1–73.8 percentage points ($p \\le 0.00097$), eliminates fabricated identifiers ($q_{\\text{BH}} = 0.03096$), and reduces citation reasoning tokens by 86.2–97.3%. Tournament I exhibits a 71.3% Slot-A win rate suppressing Bucket-3 pathways ($\\chi^2 = 55.40$), while 8.9–43.0% of Tournament II pairs flip under A/B reversal and 23.3% of failed Mendelian inferences self-prune causal genes activated at 2.1% chain-of-thought depth. Four zero-call modules—Order-Adjusted Bradley–Terry–Luce ranking, Platt scaling, epistemic gating, and CoT-SRAD—rescue validated targets, cut calibration error by 50.7–89.5%, and boost Mendelian recall by 57.1% ($p = 9.43 \\times 10^{-7}$)."
    )
    s = replace_exact(s, old_abs, new_abs, "Nature Abstract")

    # 2. Introduction paragraphs 4 & 5
    s = replace_exact(
        s,
        "followed by a 1,344-evaluation cross-ecosystem validation suite on US frontier Google Gemini models (Gemini-Pro High-Thinking and Gemini-Flash Low-Thinking) across 136 distinct biomedical disease contexts (Figure 1A–D).",
        "followed by a 2,688-evaluation cross-ecosystem validation suite across two independent US commercial frontier ecosystems—Google Gemini (Gemini-Pro High-Thinking and Gemini-Flash Low-Thinking; 1,344 evaluations) and xAI Grok (Grok-4.7 and Grok-4.7-Fast; 1,344 evaluations, 450,879 native reasoning tokens)—spanning 136 distinct biomedical disease contexts (Figure 1A–D).",
        "Intro para 4",
    )
    s = replace_exact(
        s,
        "quantifying how upstream biases propagate into downstream experimental protocols across four distinct frontier model families (`GLM-5.3`, `DeepSeek-V4-Pro`, `Gemini-Pro`, and `Gemini-Flash`).",
        "quantifying how upstream biases propagate into downstream experimental protocols across four distinct sovereign frontier model families and six reasoning tiers (`GLM-5.3`, `DeepSeek-V4-Pro`, Google `Gemini-Pro` and `Gemini-Flash`, and xAI `Grok-4.7` and `Grok-4.7-Fast`).",
        "Intro para 5",
    )
    s = replace_exact(
        s,
        "cut citation reasoning compute by 86.2% without requiring a single additional LLM call.",
        "cut citation reasoning compute by 86.2–97.3% without requiring a single additional LLM call.",
        "Intro para 5 end",
    )

    # 3. Section R7 (expand to cover both Google Gemini and xAI Grok-4.7)
    old_r7 = """### R7. Cross-ecosystem generalization across US frontier Google Gemini models (Pro High-Thinking vs. Flash Low-Thinking)
To verify that the **STAR-Audit** failure taxonomy and zero-cost rectification modules generalize beyond `GLM-5.3` and `DeepSeek-V4-Pro` to US commercial frontier architectures and across high- versus low-thinking compute tiers, we executed a 1,344-evaluation cross-ecosystem validation suite on **Google Gemini-Pro (High-Thinking)** and **Google Gemini-Flash (Low-Thinking)** across three matched experimental arenas (Figures 2D, 3C, 5B; Supplementary Table S7):

1. **Arena 1 (Tournament II Bidirectional Pairwise Judging on dAMD & ALS, 360 independent-session blinded verdicts + 360 joint-context control verdicts):** Evaluating all 45 candidate mechanism pairs in dAMD and 45 pairs in ALS under strictly blinded independent-session forward (`M01`–`M45`) and reverse-shuffled (`R01`–`R45`) runs revealed that **17.78% (16/90 pairs: 13.33% [6/45] in dAMD and 22.22% [10/45] in ALS) flipped on `Gemini-Pro`** and **26.67% (24/90 pairs: 24.44% [11/45] in dAMD and 28.89% [13/45] in ALS) flipped on `Gemini-Flash`**, accompanied by subscore-verdict NLI discordance (where the judge's own science, feasibility, and novelty subscores favored the losing candidate) in 5.00% (9/180) of `Gemini-Pro` verdicts and 1.67% (3/180) of `Gemini-Flash` verdicts. Notably, whereas `GLM-5.3` and `DeepSeek-V4-Pro` exhibited strong Slot-A primacy bias, `Gemini-Flash` exhibited mild **Slot-B recency bias** (45.56% Slot-A / 54.44% Slot-B wins overall; 42.22% Slot-A / 57.78% Slot-B in dAMD, where 9 of 11 flipped pairs favored Slot B in both orientations), while `Gemini-Pro` exhibited symmetric orientation instability (51.11% Slot-A wins; 9 both-Slot-A and 7 both-Slot-B flips). Crucially, a diagnostic control presenting forward and reverse pairs within the *same* context window (`Joint-Context`, 360 verdicts) artificially suppressed flips to 0.00% via within-session memory matching, proving that true tournament auditing requires independent-session counterbalancing. Applying **Order-Adjusted BTL** ($\\tau = 0.8667$ and $0.7778$ on `Gemini-Pro`; $\\tau = 0.6444$ and $0.7333$ on `Gemini-Flash`) corrected both recency and symmetric orientation flips, rescuing Top-3 ranking for validated complement/autophagy candidates (`C06` in dAMD and `C10` in ALS).

2. **Arena 2 (Experiment B Three-Arm Clinical Citation Gating across 14 Specialties, 504 citation slots verified via live NCBI Entrez):** In the unguarded `as_discovered` arm (84 slots per model across `B01`–`B14`), **100.0% (84/84) of `Gemini-Pro` PMIDs and 98.81% (83/84) of `Gemini-Flash` PMIDs resolved to real PubMed records**, yet Tier-2 semantic verification exposed **73.81% (62/84) on `Gemini-Pro` and 70.24% (59/84; 71.43% total ungrounded including 1.19% fabricated) on `Gemini-Flash` as Trojan horse off-topic citations**—even higher than the 57.38% baseline on `GLM-5.3` (Figure 2D). Under `abstain_probe`, ungrounded citation rates fell to 13.10% (77.38% abstention) on `Gemini-Pro` and 38.10% (46.43% abstention) on `Gemini-Flash`. Enforcing the **Epistemic Grounding Gate (`gated`)** reduced total ungrounded citations from **73.81% to 0.00% ($-73.81\\text{ pp}$, two-sided Fisher's exact $p = 3.1 \\times 10^{-27}$) on `Gemini-Pro`** and from **71.43% to 21.43% ($-50.00\\text{ pp}$, $p = 6.2 \\times 10^{-11}$) on `Gemini-Flash`** (Figure 2D).

3. **Arena 3 (Experiment C Mendelian HPO Perturbation and LORO Platt Calibration, 120 evaluations):** Across 20 stratified Mendelian diseases evaluated at 0%, 25%, and 50% `del_topIC` deletion (60 evaluations per model), causal gene `hit@10` declined from **35.0% (0% and 25% dose) to 30.0% (50% dose; 33.33% overall) on `Gemini-Pro`** and from **30.0% (0% and 25% dose) to 20.0% (50% dose; 26.67% overall) on `Gemini-Flash`** (Figure 3C), with failed calls collapsing onto canonical textbook ciliopathy and mitochondrial attractors (`POLG` [9–10 false calls], `NDUFS1`, `NDUFV1`, `TBC1D24`, `CEP290`, `TMEM67`, `AHI1`, and `CC2D2A`). Both Gemini tiers exhibited severe verbalized overconfidence: mean confidence was **79.18% vs. 33.33% empirical accuracy ($\\text{raw ECE} = 0.4585$) on `Gemini-Pro`** and **80.90% vs. 26.67% accuracy ($\\text{raw ECE} = 0.5423$) on `Gemini-Flash`**. Out-of-sample Leave-One-Disease-Out **Platt scaling reduced $\\text{ECE}$ by 74.13% ($0.4585 \\to 0.1186$) on `Gemini-Pro` and by 86.20% ($0.5423 \\to 0.0749$) on `Gemini-Flash`** (Figure 5B)."""

    new_r7 = """### R7. Cross-ecosystem generalization across US frontier Google Gemini and xAI Grok-4.7 architectures
To verify that the **STAR-Audit** failure taxonomy and zero-cost rectification modules generalize beyond `GLM-5.3` and `DeepSeek-V4-Pro` to US commercial frontier architectures and across high- versus low-thinking compute tiers, we executed a 2,688-evaluation cross-ecosystem validation suite across **Google Gemini (`Gemini-Pro` High-Thinking and `Gemini-Flash` Low-Thinking; 1,344 evaluations)** and **xAI Grok (`Grok-4.7` Full-Thinking and `Grok-4.7-Fast` Rapid-Thinking; 1,344 evaluations logging 450,879 native reasoning tokens and 1,185,113 total tokens)** across three matched experimental arenas (Figures 2D, 3C, 5B; Supplementary Table S7):

1. **Arena 1 (Tournament II Bidirectional Pairwise Judging on dAMD & ALS, 720 independent-session blinded verdicts + 720 joint-context control verdicts):** Evaluating all 45 candidate mechanism pairs in dAMD and 45 pairs in ALS under strictly blinded independent-session forward (`M01`–`M45`) and reverse-shuffled (`R01`–`R45`) runs revealed orientation flip rates of **17.78% (16/90 pairs: 13.33% [6/45] in dAMD and 22.22% [10/45] in ALS) on `Gemini-Pro`**, **26.67% (24/90 pairs: 24.44% [11/45] in dAMD and 28.89% [13/45] in ALS) on `Gemini-Flash`**, **13.33% (12/90 pairs: 11.11% [5/45] in dAMD and 15.56% [7/45] in ALS) on `Grok-4.7`**, and **8.89% (8/90 pairs: 6.67% [3/45] in dAMD and 11.11% [5/45] in ALS) on `Grok-4.7-Fast`**, accompanied by subscore-verdict NLI discordance (where the judge's own science, feasibility, and novelty subscores favored the losing candidate) in 5.00% (9/180) of `Gemini-Pro`, 1.67% (3/180) of `Gemini-Flash`, **10.00% (18/180) of `Grok-4.7`**, and **6.67% (12/180) of `Grok-4.7-Fast`** verdicts. Strikingly, `Grok-4.7` (full reasoning) exhibited a higher orientation flip rate (`13.33%` vs. `8.89%`) and higher criterion-verdict discordance (`10.00%` vs. `6.67%`) than `Grok-4.7-Fast`, independently confirming that deeper unanchored deliberation amplifies motivated rationalization of flipped judgments. Whereas `GLM-5.3` exhibited strong Slot-A primacy bias (`96.95%` toward Slot A), `Gemini-Flash` exhibited mild **Slot-B recency bias** (45.56% Slot-A / 54.44% Slot-B wins overall; 42.22% Slot-A in dAMD), while `Gemini-Pro` (51.11% Slot-A wins), `Grok-4.7` (48.89% [88/180] Slot-A wins, $p = 0.823$), and `Grok-4.7-Fast` (48.89% [88/180] Slot-A wins, $p = 0.823$) exhibited symmetric orientation instability. Crucially, a diagnostic control presenting forward and reverse pairs within the *same* context window (`Joint-Context`, 720 verdicts across all four tiers) artificially suppressed flips to **0.00%** across both Google Gemini and xAI Grok via within-session memory matching, proving that valid tournament auditing requires independent-session counterbalancing. Applying **Order-Adjusted BTL** ($\\tau = 0.8667\\text{--}0.9556$ on `Grok-4.7`; $\\tau = 0.7778\\text{--}0.8667$ on `Gemini-Pro`; $\\tau = 0.6444\\text{--}0.7333$ on `Gemini-Flash`) corrected primacy, recency, and symmetric orientation flips alike, rescuing Top-3 ranking for validated complement and neuroprotective candidates (`C06` in dAMD and `C10`/`C02` in ALS).

2. **Arena 2 (Experiment B Three-Arm Clinical Citation Gating across 14 Specialties, 1,008 cross-ecosystem citation slots verified via live NCBI Entrez):** In the unguarded `as_discovered` arm (84 slots per model across `B01`–`B14`), **100.0% (84/84) of `Gemini-Pro` PMIDs, 98.81% (83/84) of `Gemini-Flash` PMIDs, 100.0% (84/84) of `Grok-4.7` PMIDs, and 98.81% (83/84) of `Grok-4.7-Fast` PMIDs resolved to real PubMed records**, yet Tier-2 semantic verification exposed **73.81% (62/84) on `Gemini-Pro`, 70.24% (59/84; 71.43% total ungrounded) on `Gemini-Flash`, 32.14% (27/84) on `Grok-4.7`, and 39.29% (33/84; 40.48% total ungrounded) on `Grok-4.7-Fast` as Trojan horse off-topic citations** (Figure 2D). Under `abstain_probe`, ungrounded citation rates fell to 13.10% (77.38% abstention) on `Gemini-Pro`, 38.10% (46.43% abstention) on `Gemini-Flash`, and **0.00% (100.0% abstention) on both `Grok-4.7` and `Grok-4.7-Fast`**. Enforcing the **Epistemic Grounding Gate (`gated`)** reduced total ungrounded citations to **0.00% ($-73.81\\text{ pp}, p = 3.1 \\times 10^{-27}$) on `Gemini-Pro`**, **21.43% ($-50.00\\text{ pp}, p = 6.2 \\times 10^{-11}$) on `Gemini-Flash`**, **0.00% ($-32.14\\text{ pp}, p = 1.23 \\times 10^{-9}$) on `Grok-4.7`**, and **0.00% ($-40.48\\text{ pp}, p = 1.72 \\times 10^{-12}$) on `Grok-4.7-Fast`** (Figure 2D). Native reasoning-token telemetry from the xAI Grok CLI directly confirmed Paradox 2 in a US commercial reasoning model: under `as_discovered`, `Grok-4.7` and `Grok-4.7-Fast` expended **10,072 and 12,284 reasoning tokens** (187–242s) dredging internal memory for candidate PMIDs, whereas under `gated`, reasoning tokens collapsed **30-fold to 332 and 330 tokens** (26–43s; a **96.7%–97.3% reduction** in citation reasoning compute).

3. **Arena 3 (Experiment C Mendelian HPO Perturbation and LORO Platt Calibration, 240 cross-ecosystem evaluations):** Across 20 stratified Mendelian diseases evaluated at 0%, 25%, and 50% `del_topIC` deletion (60 evaluations per model), causal gene `hit@10` declined from **35.0% to 30.0% (33.33% overall) on `Gemini-Pro`**, from **30.0% to 20.0% (26.67% overall) on `Gemini-Flash`**, from **45.0% (0% dose) to 30.0% (25% dose) to 20.0% (50% dose; 31.67% overall) on `Grok-4.7`**, and from **40.0% (0% dose) to 35.0% (25% and 50% dose; 36.67% overall) on `Grok-4.7-Fast`** (Figure 3C). Notably, at 50% phenotype IC deletion, full-thinking `Grok-4.7` (expending 17,616–26,613 native reasoning tokens per 10-case batch) underperformed rapid-thinking `Grok-4.7-Fast` (`20.0%` vs. `35.0%`), as prolonged deliberation under sparse phenotypes drove self-pruning toward textbook mitochondrial and ciliopathy attractors (`FBXL4` [10 false calls], `POLG` [9–10 false calls], `CEP290` [7], `CUL7` [6], `OBSL1` [6], `TMEM67` [6], `CC2D2A` [6], and `CPLANE1` [6]). All four US frontier tiers exhibited directional verbalized overconfidence: mean confidence was **79.18% vs. 33.33% accuracy ($\\text{raw ECE} = 0.4585$) on `Gemini-Pro`**, **80.90% vs. 26.67% accuracy ($\\text{raw ECE} = 0.5423$) on `Gemini-Flash`**, **54.58% vs. 31.67% accuracy ($\\text{raw ECE} = 0.2292$) on `Grok-4.7`**, and **47.75% vs. 36.67% accuracy ($\\text{raw ECE} = 0.1652$) on `Grok-4.7-Fast`**. Out-of-sample Leave-One-Disease-Out **Platt scaling reduced $\\text{ECE}$ by 74.13% ($0.4585 \\to 0.1186$) on `Gemini-Pro`, by 86.20% ($0.5423 \\to 0.0749$) on `Gemini-Flash`, by 54.78% ($0.2292 \\to 0.1036$) on `Grok-4.7`, and by 50.72% ($0.1652 \\to 0.0814$) on `Grok-4.7-Fast`** (Figure 5B)."""
    s = replace_exact(s, old_r7, new_r7, "Section R7")

    # 4. Discussion updates
    s = replace_exact(
        s,
        "By executing our preregistered **STAR-Audit** framework across 9,130 primary live API calls (35.58 million internal reasoning tokens across 8,973 white-box traces on GLM-5.3 and DeepSeek-V4-Pro), 1,344 cross-ecosystem evaluations on Google Gemini (Pro High-Thinking and Flash Low-Thinking), and 136 disease contexts, this study establishes two principal conclusions (Figure 7).",
        "By executing our preregistered **STAR-Audit** framework across 9,130 primary live API calls (35.58 million internal reasoning tokens across 8,973 white-box traces on GLM-5.3 and DeepSeek-V4-Pro) plus 2,688 cross-ecosystem evaluations across Google Gemini (Pro High-Thinking and Flash Low-Thinking) and xAI Grok (Grok-4.7 and Grok-4.7-Fast; 450,879 native reasoning tokens)—totaling 11,818 live evaluations (36.03 million reasoning tokens) across four sovereign frontier model families and 136 disease contexts—this study establishes two principal conclusions (Figure 7).",
        "Discussion intro",
    )
    s = replace_exact(
        s,
        "(`CHD7`, `KMT2D`, `FOXG1`, `CEP290` on GLM/DeepSeek; `POLG`, `CEP290`, `TMEM67`, `AHI1` on Gemini).",
        "(`CHD7`, `KMT2D`, `FOXG1`, `CEP290` on GLM/DeepSeek; `POLG`, `FBXL4`, `CEP290`, `TMEM67`, `CUL7`, `AHI1` on Gemini and Grok-4.7).",
        "Discussion Paradox 3",
    )

    # 5. Methods updates
    s = replace_exact(
        s,
        "per-call JSONL telemetry logs (9,130 primary calls across 8,973 white-box CoT traces plus 1,344 cross-ecosystem Google Gemini evaluations; 10,474 total evaluations), raw model responses, PubMed verification caches (956 primary + 183 Gemini distinct PMIDs), and master statistical outputs",
        "per-call JSONL telemetry logs (9,130 primary calls across 8,973 white-box CoT traces plus 2,688 cross-ecosystem Google Gemini and xAI Grok-4.7 evaluations; 11,818 total evaluations, 36.03M reasoning tokens), raw model responses, PubMed verification caches (956 primary + 183 Gemini + 137 Grok distinct PMIDs), and master statistical outputs",
        "Data availability",
    )
    s = replace_exact(
        s,
        "statistical and white-box/cross-ecosystem audit scripts (`step1` to `step5`, `analyze_cot_trajectory_dynamics.py`, `analyze_gemini_cross_ecosystem.py`),",
        "statistical and white-box/cross-ecosystem audit scripts (`step1` to `step5`, `analyze_cot_trajectory_dynamics.py`, `analyze_gemini_cross_ecosystem.py`, `run_grok_cross_ecosystem.py`, `analyze_grok_cross_ecosystem.py`),",
        "Code availability",
    )
    s = replace_exact(
        s,
        "To evaluate cross-ecosystem generalization across US frontier architectures and compute tiers without external API confounds, we executed a matched 1,344-evaluation validation suite on Google Gemini-Pro (High-Thinking) and Google Gemini-Flash (Low-Thinking) across Arena 1 (360 independent-session blinded single-direction Tournament II verdicts on `M01`–`M45` forward and seed-20260101 shuffled `R01`–`R45` reverse pairs + 360 joint-context paired control verdicts across dAMD and ALS), Arena 2 (504 Experiment B citation slots across all 14 clinical domains and 3 arms verified via live NCBI Entrez `esummary`/`efetch`), and Arena 3 (120 Experiment C masked HPO evaluations across 20 stratified Mendelian diseases at 0%, 25%, and 50% `del_topIC` deletion; Supplementary Table S7).",
        "To evaluate cross-ecosystem generalization across US frontier architectures and compute tiers without external API confounds, we executed a matched 2,688-evaluation validation suite across Google Gemini (`Gemini-Pro` High-Thinking and `Gemini-Flash` Low-Thinking; 1,344 evaluations) and xAI Grok (`Grok-4.7` Full-Thinking and `Grok-4.7-Fast` Rapid-Thinking via official Grok Build CLI `v1.0.70`; 1,344 evaluations, 450,879 native reasoning tokens) across Arena 1 (720 independent-session blinded single-direction Tournament II verdicts on `M01`–`M45` forward and seed-20260101 shuffled `R01`–`R45` reverse pairs + 720 joint-context paired control verdicts across dAMD and ALS), Arena 2 (1,008 Experiment B citation slots across all 14 clinical domains and 3 arms verified via live NCBI Entrez `esummary`/`efetch`), and Arena 3 (240 Experiment C masked HPO evaluations across 20 stratified Mendelian diseases at 0%, 25%, and 50% `del_topIC` deletion; Supplementary Table S7).",
        "Methods Block 3",
    )
    s = replace_exact(
        s,
        "During the preparation of this work, the authors audited large language models (GLM-5.3, DeepSeek-V4-Pro, Google Gemini-Pro, and Google Gemini-Flash) as the primary experimental subjects",
        "During the preparation of this work, the authors audited large language models (GLM-5.3, DeepSeek-V4-Pro, Google Gemini-Pro, Google Gemini-Flash, xAI Grok-4.7, and xAI Grok-4.7-Fast) as the primary experimental subjects",
        "Declaration of AI",
    )

    # 6. Figure Legends (Fig 2D, Fig 3C, Fig 5B, Fig 7)
    s = replace_exact(
        s,
        "paired on the right with cross-ecosystem 3-arm trajectories on `Gemini-Pro` ($73.8\\% \\to 13.1\\% \\to 0.0\\%$, $p = 3.1 \\times 10^{-27}$) and `Gemini-Flash` ($71.4\\% \\to 38.1\\% \\to 21.4\\%$, $p = 6.2 \\times 10^{-11}$).",
        "paired on the right with cross-ecosystem 3-arm trajectories on `Gemini-Pro` ($73.8\\% \\to 13.1\\% \\to 0.0\\%$, $p = 3.1 \\times 10^{-27}$), `Gemini-Flash` ($71.4\\% \\to 38.1\\% \\to 21.4\\%$, $p = 6.2 \\times 10^{-11}$), `Grok-4.7` ($32.1\\% \\to 0.0\\% \\to 0.0\\%$, $p = 1.23 \\times 10^{-9}$, $10.07\\text{k} \\to 0.33\\text{k}$ native CoT tokens), and `Grok-4.7-Fast` ($40.5\\% \\to 0.0\\% \\to 0.0\\%$, $p = 1.72 \\times 10^{-12}$, $12.28\\text{k} \\to 0.33\\text{k}$ native CoT tokens).",
        "Fig 2D legend",
    )
    s = replace_exact(
        s,
        "cross-ecosystem `Gemini-Pro` ($35.0\\% \\to 30.0\\%$) and `Gemini-Flash` ($30.0\\% \\to 20.0\\%$) trajectories, and vertical dumbbell markers comparing `High` versus `Low` pretraining PubMed literature footprint ($p = 0.0110$).",
        "cross-ecosystem trajectories on `Gemini-Pro` ($35.0\\% \\to 35.0\\% \\to 30.0\\%$), `Gemini-Flash` ($30.0\\% \\to 30.0\\% \\to 20.0\\%$), `Grok-4.7` ($45.0\\% \\to 30.0\\% \\to 20.0\\%$), and `Grok-4.7-Fast` ($40.0\\% \\to 35.0\\% \\to 35.0\\%$), and vertical dumbbell markers comparing `High` versus `Low` pretraining PubMed literature footprint ($p = 0.0110$).",
        "Fig 3C legend",
    )
    s = replace_exact(
        s,
        "and cross-ecosystem `Gemini-Pro` / `Gemini-Flash` raw ($\\text{ECE} = 0.459 / 0.542$, purple triangles) versus LORO Platt-recalibrated ($\\text{ECE} = 0.119 / 0.075$, $-74.1\\% / -86.2\\%$, blue diamonds) centroids.",
        "and cross-ecosystem raw versus LORO Platt-recalibrated centroids on `Gemini-Pro` ($\\text{ECE } 0.459 \\to 0.119, -74.1\\%$), `Gemini-Flash` ($0.542 \\to 0.075, -86.2\\%$), `Grok-4.7` ($0.229 \\to 0.104, -54.8\\%$), and `Grok-4.7-Fast` ($0.165 \\to 0.081, -50.7\\%$).",
        "Fig 5B legend",
    )
    s = replace_exact(
        s,
        "Trojan horse citation misattribution ($54.3\\%\\text{--}73.8\\%$ off-topic real PMIDs), Slot-A primacy extinction ($71.3\\%$ Tournament I and $97.0\\%$ Tournament II first-slot bias), and motivated chain-of-thought spin ($2.54\\times$ surge in judge self-contradiction and $23.3\\%$ Mendelian false-negative self-pruning). **Stage 2 (Center):** Six external-truth diagnostic sensors audit $N = 9,130$ primary live API invocations ($35.58\\text{M}$ CoT tokens across $8,973$ white-box traces) plus $1,344$ cross-ecosystem Google Gemini evaluations across live NCBI Entrez verification ($1,620 + 504$ citation slots), $120$-disease HPO information-content masking ($804 + 120$ multi-vendor calls), counterbalanced A/B reversal probing ($1,601 + 180$ bidirectional pairs), $10,000$-draw verdict-table bootstrap resampling, DeBERTa-v3 bidirectional NLI contradiction classification ($18,470$ claim pairs), and out-of-sample confidence calibration telemetry. **Stage 3 (Right):** Four zero-marginal-cost algorithmic rectification modules (Order-Adjusted BTL with NLI discordance filtering [$100\\%$ slot-bias purge and $+81.3\\%$ Bucket-3 pathway survival], Leave-One-Run-Out [LORO] Platt scaling [$74.1\\%\\text{--}89.5\\%$ ECE reduction], the Two-Tier Epistemic Grounding Gate [$95.0\\%\\text{--}100.0\\%$ ungrounded error purge and $-86.2\\%$ citation CoT compute],",
        "Trojan horse citation misattribution ($32.1\\%\\text{--}73.8\\%$ off-topic real PMIDs), Slot-A primacy extinction ($71.3\\%$ Tournament I and $97.0\\%$ Tournament II first-slot bias), and motivated chain-of-thought spin ($2.54\\times$ surge in judge self-contradiction and $23.3\\%$ Mendelian false-negative self-pruning). **Stage 2 (Center):** Six external-truth diagnostic sensors audit $N = 9,130$ primary live API invocations ($35.58\\text{M}$ CoT tokens across $8,973$ white-box traces) plus $2,688$ cross-ecosystem Google Gemini and xAI Grok-4.7 evaluations ($11,818$ total evaluations, $36.03\\text{M}$ reasoning tokens) across live NCBI Entrez verification ($1,620 + 1,008$ citation slots), $120$-disease HPO information-content masking ($804 + 240$ multi-vendor calls), counterbalanced A/B reversal probing ($1,601 + 360$ bidirectional pairs), $10,000$-draw verdict-table bootstrap resampling, DeBERTa-v3 bidirectional NLI contradiction classification ($18,470$ claim pairs), and out-of-sample confidence calibration telemetry. **Stage 3 (Right):** Four zero-marginal-cost algorithmic rectification modules (Order-Adjusted BTL with NLI discordance filtering [$100\\%$ slot-bias purge and $+81.3\\%$ Bucket-3 pathway survival], Leave-One-Run-Out [LORO] Platt scaling [$50.7\\%\\text{--}89.5\\%$ ECE reduction], the Two-Tier Epistemic Grounding Gate [$95.0\\%\\text{--}100.0\\%$ ungrounded error purge and $-86.2\\%\\text{ to }-97.3\\%$ citation CoT compute],",
        "Fig 7 legend",
    )

    # 7. Tables 1 and 2
    old_t1_row = "| **STAR-Audit (This Study)** | **Six-dimension audit & 4-module zero-cost rectification (136 diseases, 9,130 + 1,344 evals, 4 frontier models)** | **Yes (12 full 6-step runs + Exp B + Exp C-v4 + Gemini Pro/Flash suite)** | **Yes (Exposes 54.3–73.8% Trojan refs & 35.8 CoT PMIDs/call; $-50.0\\text{ to }-73.8\\text{ pp}$ via Gate)** | **Yes (dAMD/ALS + 120 HPO Mendelian diseases + `CoT-SRAD` $+57.1\\%$ recall)** | **Yes ($\\hat{\\gamma}$ correction cuts Bucket-3 skew by 72.8% & corrects primacy/recency)** | **Yes (DeBERTa-v3 on 17,990 claims; $2.5\\times$ flip surge)** | **Yes (10k bootstrap null + LORO Platt ECE $-74.1\\text{ to }-89.5\\%$)** | **Yes (OSF: 10.17605/OSF.IO/KF2G8; BH-FDR $q=0.05$)** |"
    new_t1_row = "| **STAR-Audit (This Study)** | **Six-dimension audit & 4-module zero-cost rectification (136 diseases, 9,130 + 2,688 = 11,818 evals, 4 frontier families / 6 tiers)** | **Yes (12 full 6-step runs + Exp B + Exp C-v4 + Gemini Pro/Flash & Grok-4.7/Fast suites)** | **Yes (Exposes 32.1–73.8% Trojan refs & 35.8 CoT PMIDs/call; $-32.1\\text{ to }-73.8\\text{ pp}$ via Gate)** | **Yes (dAMD/ALS + 120 HPO Mendelian diseases + `CoT-SRAD` $+57.1\\%$ recall)** | **Yes ($\\hat{\\gamma}$ correction cuts Bucket-3 skew by 72.8% & corrects primacy/recency/symmetric flips)** | **Yes (DeBERTa-v3 on 17,990 claims; $2.5\\times$ flip surge)** | **Yes (10k bootstrap null + LORO Platt ECE $-50.7\\text{ to }-89.5\\%$)** | **Yes (OSF: 10.17605/OSF.IO/KF2G8; BH-FDR $q=0.05$)** |"
    s = replace_exact(s, old_t1_row, new_t1_row, "Table 1 row")

    old_t2_dim1 = "| **Dim 1: Faithfulness** (Confirmatory Member 1) | Exp B Randomized Trial (14 domains, 1,260 GLM + 504 Gemini slots) + Parent Step 6 (360 slots) | Naive check: 96.9–100.0% valid; Tier-2 exposes **58.33%** (Parent), **57.38%** (GLM Exp B; 35.8 CoT PMIDs/call), **73.81%** (Gemini-Pro) & **70.24%** (Gemini-Flash) Trojan horse PMIDs | Fake PMID RD $+3.10\\%$ ($p = 0.01032$, **$q_{\\text{BH}} = 0.03096^*$**); Ungrounded RD $+54.52\\%$ ($p = 0.00097$); CoT PMID dredging $p = 2.07 \\times 10^{-44}$ | **Module 3:** Two-Tier Semantic Grounding & Epistemic Abstention Gate | Fake PMIDs **0.00%**; ungrounded rate **2.86%** ($-54.52\\text{ pp}$ on GLM) & **0.00%** ($-73.81\\text{ pp}$ on Gemini-Pro); CoT PMIDs **5.0/call**; **86.2% fewer CoT tokens** |"
    new_t2_dim1 = "| **Dim 1: Faithfulness** (Confirmatory Member 1) | Exp B Randomized Trial (14 domains, 1,260 GLM + 504 Gemini + 504 Grok slots) + Parent Step 6 (360 slots) | Naive check: 96.9–100.0% valid; Tier-2 exposes **58.33%** (Parent), **54.29%** (GLM Exp B; 35.8 CoT PMIDs/call), **73.81%/70.24%** (Gemini Pro/Flash) & **32.14%/39.29%** (Grok-4.7/Fast) Trojan PMIDs | Fake PMID RD $+3.10\\%$ ($p = 0.01032$, **$q_{\\text{BH}} = 0.03096^*$**); Ungrounded RD $+54.52\\%$ ($p = 0.00097$); CoT PMID dredging $p = 2.07 \\times 10^{-44}$ | **Module 3:** Two-Tier Semantic Grounding & Epistemic Abstention Gate | Fake PMIDs **0.00%**; ungrounded rate **2.86%** (GLM) & **0.00%** (Gemini-Pro, Grok-4.7, Grok-Fast); CoT PMIDs **5.0/call**; **86.2–97.3% fewer CoT tokens** |"
    s = replace_exact(s, old_t2_dim1, new_t2_dim1, "Table 2 Dim 1")

    old_t2_dim2c = "| **Dim 2: HPO IC Deletion** (Confirmatory Members 2 & 3) | Exp C-v4 (120 Mendelian diseases, $n=630$ GLM/DeepSeek + $n=120$ Gemini Pro/Flash) | DeepSeek `del_topIC` recall@10 drops $28.3\\% \\to 22.6\\% \\to 14.3\\%$ ($p=0.0259$); true gene activated at **2.1% CoT depth**, but **23.3%** of false negatives self-prune & **33.3%** of truncated calls already found true gene | Pooled $\\beta_1 = -0.573$ ($p = 0.2191, q_{\\text{BH}} = 0.2629$); `CoT-SRAD` McNemar $p = 7.07 \\times 10^{-6}$ (pooled) & $p = 9.43 \\times 10^{-7}$ (DeepSeek) | **Module 4 (`CoT-SRAD`):** LODO Attractor Deconfounding (`CHD7`, `KMT2D`, `FOXG1`, `POLG`) & CoT Stream Recovery | Rescues **+36 causal gene discoveries** ($26.35\\% \\to 32.06\\%$ pooled); boosts DeepSeek recall by **+57.1%** ($20.66\\% \\to 32.47\\%$, +32 calls) at zero LLM cost |"
    new_t2_dim2c = "| **Dim 2: HPO IC Deletion** (Confirmatory Members 2 & 3) | Exp C-v4 (120 Mendelian diseases, $n=630$ GLM/DeepSeek + $n=240$ Gemini & Grok) | DeepSeek `del_topIC` drops $28.3\\% \\to 22.6\\% \\to 14.3\\%$ ($p=0.0259$) & Grok-4.7 drops $45.0\\% \\to 30.0\\% \\to 20.0\\%$; true gene activated at **2.1% CoT depth**, but **23.3%** of FNs self-prune | Pooled $\\beta_1 = -0.573$ ($p = 0.2191, q_{\\text{BH}} = 0.2629$); `CoT-SRAD` McNemar $p = 7.07 \\times 10^{-6}$ (pooled) & $p = 9.43 \\times 10^{-7}$ (DeepSeek) | **Module 4 (`CoT-SRAD`):** LODO Attractor Deconfounding (`CHD7`, `KMT2D`, `FOXG1`, `POLG`, `FBXL4`) & CoT Stream Recovery | Rescues **+36 causal gene discoveries** ($26.35\\% \\to 32.06\\%$ pooled); boosts DeepSeek recall by **+57.1%** ($20.66\\% \\to 32.47\\%$, +32 calls) at zero LLM cost |"
    s = replace_exact(s, old_t2_dim2c, new_t2_dim2c, "Table 2 Dim 2c")

    old_t2_dim3 = "| **Dim 3: Positional Fairness** (Diagnostic & Remediation Core) | Tournament I (3,594 calls) & Tournament II (1,601 GLM pairs + 180 blinded Gemini pairs) | T1 Slot A wins **71.29%** ($p = 4.37 \\times 10^{-148}$; **88.4% Decile-1 Slot-A CoT focus**), causing Bucket 1:2:3 skew `78:26:16` ($\\chi^2 = 55.40$); T2 flips **43.04%** on GLM, **17.78%** on Gemini-Pro & **26.67%** on Gemini-Flash | T1 $\\chi^2 p = 9.33 \\times 10^{-13}$; T2 primacy binomial $p = 4.63 \\times 10^{-168}$ | **Module 1:** Order-Adjusted BTL ($\\hat{\\gamma}$ intercept removal) + T2 NLI-Discordance Neutralization | Bucket skew reduced by **72.8%** (`60:31:29`, $\\chi^2 = 15.05$); Bucket-3 survival **+81.3%**; rescues `MERTK`, `TIMP3`, `ABCA1`, `CD59`, `C06`, `C10` |"
    new_t2_dim3 = "| **Dim 3: Positional Fairness** (Diagnostic & Remediation Core) | Tournament I (3,594 calls) & Tournament II (1,601 GLM pairs + 360 blinded Gemini & Grok pairs) | T1 Slot A wins **71.29%** ($p = 4.37 \\times 10^{-148}$; **88.4% Decile-1 Slot-A CoT focus**), causing Bucket 1:2:3 skew `78:26:16` ($\\chi^2 = 55.40$); T2 flips **43.04%** (GLM), **17.8%/26.7%** (Gemini Pro/Flash) & **13.3%/8.9%** (Grok-4.7/Fast) | T1 $\\chi^2 p = 9.33 \\times 10^{-13}$; T2 primacy binomial $p = 4.63 \\times 10^{-168}$ | **Module 1:** Order-Adjusted BTL ($\\hat{\\gamma}$ intercept removal) + T2 NLI-Discordance Neutralization | Bucket skew reduced by **72.8%** (`60:31:29`, $\\chi^2 = 15.05$); Bucket-3 survival **+81.3%**; rescues `MERTK`, `TIMP3`, `ABCA1`, `CD59`, `C06`, `C10`, `C02` |"
    s = replace_exact(s, old_t2_dim3, new_t2_dim3, "Table 2 Dim 3")

    old_t2_dim6 = "| **Dim 6: Self-Knowledge** (Confirmatory Member 6) | Parent Step 1 ($n=360$) & Pooled ($n=480$); Exp C-v4 ($n=630$ GLM/DS + $n=120$ Gemini) | Step 1 calibration slope $\\hat{\\beta}_{\\text{cal}} = 0.655 \\neq 1.0$; Parent $\\text{ECE} = 0.222$; Exp C raw $\\text{ECE} = 0.351$ (GLM), $0.244$ (DS), $0.459$ (Gemini-Pro) & $0.542$ (Gemini-Flash) | Wald test vs slope 1.0: $p = 0.02004$, **$q_{\\text{BH}} = 0.04009^*$** | **Module 2:** Leave-One-Run-Out (LORO) Cross-Validated Platt Scaling | Parent $\\text{ECE}$ reduced by **87.8%** ($0.222 \\to 0.027$, 87.64% exact); C-v4 $\\text{ECE}$ reduced by **82.8–89.5%** (GLM/DS) and **74.1–86.2%** (Gemini Pro/Flash) |"
    new_t2_dim6 = "| **Dim 6: Self-Knowledge** (Confirmatory Member 6) | Parent Step 1 ($n=360$) & Pooled ($n=480$); Exp C-v4 ($n=630$ GLM/DS + $n=240$ Gemini & Grok) | Step 1 calibration slope $\\hat{\\beta}_{\\text{cal}} = 0.655 \\neq 1.0$; Parent $\\text{ECE} = 0.222$; Exp C raw $\\text{ECE} = 0.351$ (GLM), $0.244$ (DS), $0.459/0.542$ (Gemini) & $0.229/0.165$ (Grok) | Wald test vs slope 1.0: $p = 0.02004$, **$q_{\\text{BH}} = 0.04009^*$** | **Module 2:** Leave-One-Run-Out (LORO) Cross-Validated Platt Scaling | Parent $\\text{ECE}$ reduced by **87.8%** ($0.222 \\to 0.027$, 87.64% exact); C-v4 $\\text{ECE}$ reduced by **82.8–89.5%** (GLM/DS), **74.1–86.2%** (Gemini) & **50.7–54.8%** (Grok) |"
    s = replace_exact(s, old_t2_dim6, new_t2_dim6, "Table 2 Dim 6")

    write_lf(path, s)
    print("Updated:", path)


def update_supplementary():
    path = os.path.join(BASE, "SUPPLEMENTARY_GEN2_v1.0.md")
    s = read_lf(path)
    idx = s.index("## Supplementary Table S7.")
    prefix = s[:idx]

    s7 = """## Supplementary Table S7. White-box chain-of-thought (CoT) trajectory dynamics and 4-family cross-ecosystem validation suite (`GLM-5.3`, `DeepSeek-V4-Pro`, Google `Gemini-Pro`/`Flash`, and xAI `Grok-4.7`/`Fast`; 11,818 total evaluations)

| Arena & Audit Metric | `GLM-5.3` (Primary White-Box High-CoT) | `DeepSeek-V4-Pro` (Primary White-Box High-CoT) | `Gemini-Pro` (US Frontier High-Thinking) | `Gemini-Flash` (US Frontier Low-Thinking) | `Grok-4.7` (xAI Frontier Full-Thinking) | `Grok-4.7-Fast` (xAI Frontier Rapid-Thinking) | Zero-Cost Algorithmic Rectification Outcome |
|---|---|---|---|---|---|---|---|
| **Arena 1 (Tournament II Blinded Pairwise Evaluation):** Orientation Flip Rate ($1 - K_{\\text{orient}}$) | **43.04%** (689/1,601 pairs across 12 runs; dAMD & ALS) | Evaluated in Arena 3 (Exp C-v4) | **17.78%** (16/90 blinded pairs: 13.33% [6/45] dAMD, 22.22% [10/45] ALS; 0.00% in Joint-Context) | **26.67%** (24/90 blinded pairs: 24.44% [11/45] dAMD, 28.89% [13/45] ALS; 0.00% in Joint-Context) | **13.33%** (12/90 blinded pairs: 11.11% [5/45] dAMD, 15.56% [7/45] ALS; 0.00% in Joint-Context) | **8.89%** (8/90 blinded pairs: 6.67% [3/45] dAMD, 11.11% [5/45] ALS; 0.00% in Joint-Context) | **Module 1 (OA-BTL + NLI Tie-Override):** Purges 100% of flipped pairs; rescues `MERTK`, `TIMP3`, `ABCA1`, `CD59`, `C06` (dAMD) & `MMP9`, `CCS`, `C10`, `C02` (ALS) |
| **Arena 1 (Positional Polarity & White-Box CoT Framing):** Slot-A Win Rate & NLI Discordance | **71.29%** (T1) & **96.95%** of T2 flips toward Slot A (**88.41% T1 / 90.59% T2** Decile-1 Slot-A CoT mentions) | — | **51.11%** Slot-A wins (92/180; symmetric flips; **5.00%** subscore NLI discordance) | **45.56%** Slot-A / **54.44%** Slot-B wins (82/180; 9/11 both-Slot-B recency flips in dAMD; **1.67%** NLI discordance) | **48.89%** Slot-A wins (88/180, $p=0.823$; symmetric flips; **10.00%** [18/180] subscore NLI discordance) | **48.89%** Slot-A wins (88/180, $p=0.823$; symmetric flips; **6.67%** [12/180] subscore NLI discordance) | **OA-BTL Position-Intercept ($\\hat{\\gamma}$) Removal:** Simultaneously corrects primacy (`GLM`), recency (`Gemini-Flash`), and symmetric flips (`Gemini-Pro`, `Grok-4.7`, `Grok-Fast`) |
| **Arena 2 (Experiment B Citation Trial — `as_discovered`):** Apparent Valid vs. Trojan Horse Rate | **96.90%** existent PMIDs (407/420), but **54.29%** (228/420) Trojan horse + **3.10%** fake = **57.38%** ungrounded | — | **100.00%** existent PMIDs (84/84), but **73.81%** (62/84) Trojan horse + **0.00%** fake = **73.81%** ungrounded | **98.81%** existent PMIDs (83/84), but **70.24%** (59/84) Trojan horse + **1.19%** fake = **71.43%** ungrounded | **100.00%** existent PMIDs (84/84), but **32.14%** (27/84) Trojan horse + **0.00%** fake = **32.14%** ungrounded | **98.81%** existent PMIDs (83/84), but **39.29%** (33/84) Trojan horse + **1.19%** fake = **40.48%** ungrounded | Exposes universal Trojan horse citation pathology (32.1%–73.8%) across all 4 model families missed by Tier-1 existence checks |
| **Arena 2 (Experiment B Citation Trial — `abstain_probe` vs. `gated`):** Ungrounded Citation Rate | `abstain_probe`: **18.10%** (63.81% abst.); `gated`: **2.86%** (95.24% abst.; **0.00%** fake, $p = 0.00097$) | — | `abstain_probe`: **13.10%** (77.38% abst.); `gated`: **0.00%** (100.0% abst.; $-73.81\\text{ pp}, p = 3.1 \\times 10^{-27}$) | `abstain_probe`: **38.10%** (46.43% abst.); `gated`: **21.43%** (69.05% abst.; $-50.00\\text{ pp}, p = 6.2 \\times 10^{-11}$) | `abstain_probe`: **0.00%** (100.0% abst.); `gated`: **0.00%** (100.0% abst.; $-32.14\\text{ pp}, p = 1.23 \\times 10^{-9}$) | `abstain_probe`: **0.00%** (100.0% abst.); `gated`: **0.00%** (100.0% abst.; $-40.48\\text{ pp}, p = 1.72 \\times 10^{-12}$) | **Module 3 (Two-Tier Epistemic Gate):** Cuts ungrounded citations by **32.1 to 73.8 pp** across all models and eliminates fabricated PMIDs |
| **Arena 2 (White-Box CoT PMID Dredging & Token Telemetry):** Candidate PMIDs & Reasoning Tokens | `as_discovered`: **35.82** unique PMIDs/call ($11.80\\text{k}$ CoT tokens); `abstain_probe`: **25.37** ($8.86\\text{k}$); `gated`: **5.00** ($1.13\\text{k}, -86.2\\%, p = 2.07 \\times 10^{-44}$) | — | Parametric year-prefix recall drives 73.81% real off-topic PMID collisions in `as_discovered` | Parametric year-prefix recall drives 70.24% real off-topic PMID collisions in `as_discovered` | Native reasoning tokens collapse **30.3-fold** from **10,072** (`as_discovered`, 187s) to **332** (`gated`, 43s; **$-96.7\\%$**) | Native reasoning tokens collapse **37.2-fold** from **12,284** (`as_discovered`, 242s) to **330** (`gated`, 26s; **$-97.3\\%$**) | Epistemic gating halts chronological integer dredging in CoT and cuts citation reasoning tokens by **86.2%–97.3%** |
| **Arena 3 (Experiment C HPO Perturbation):** `del_topIC` Recall@10 ($0\\% \\to 25\\% \\to 50\\%$) | **34.55% $\\to$ 31.51% $\\to$ 30.61%** (overall 30.64% [110/359]; first hit at **2.14% CoT depth**; **23.84%** FN self-pruning) | **28.26% $\\to$ 22.58% $\\to$ 14.29%** ($p=0.0259$; overall 20.66% [56/271]; first hit at **2.06% CoT**; **22.35%** FN self-pruning) | **35.00% $\\to$ 35.00% $\\to$ 30.00%** (overall 33.33% [20/60]; attractors: `POLG`, `NDUFS1`, `NDUFV1`, `CEP290`, `TMEM67`) | **30.00% $\\to$ 30.00% $\\to$ 20.00%** (overall 26.67% [16/60]; attractors: `POLG`, `TBC1D24`, `RECQL4`, `CPLANE1`, `CC2D2A`) | **45.00% $\\to$ 30.00% $\\to$ 20.00%** (overall 31.67% [19/60]; 17.6k–26.6k CoT/batch; attractors: `FBXL4`, `POLG`, `CEP290`, `CUL7`) | **40.00% $\\to$ 35.00% $\\to$ 35.00%** (overall 36.67% [22/60]; outperforms `Grok-4.7` at 50% noise by avoiding overthinking pruning) | **Module 4 (`CoT-SRAD`):** Rescues **+36 true causal gene discoveries** ($26.35\\% \\to 32.06\\%, p = 7.07 \\times 10^{-6}$; DeepSeek **+57.1%** relative gain [$20.66\\% \\to 32.47\\%, p = 9.43 \\times 10^{-7}$]) |
| **Arena 3 (Dimension 6 Self-Knowledge & Calibration):** Raw vs. LORO Platt-Scaled $\\text{ECE}$ | Raw $\\text{ECE} = \\mathbf{0.3510} \\to$ Platt $\\mathbf{0.0370}$ (**$-89.46\\%$**; Parent runs: $0.2221 \\to 0.0274$, **$-87.64\\%$**) | Raw $\\text{ECE} = \\mathbf{0.2440} \\to$ Platt $\\mathbf{0.0420}$ (**$-82.79\\%$**) | Mean conf **79.18%** vs. **33.33%** hit: Raw $\\text{ECE} = \\mathbf{0.4585} \\to$ LORO Platt $\\mathbf{0.1186}$ (**$-74.13\\%$**) | Mean conf **80.90%** vs. **26.67%** hit: Raw $\\text{ECE} = \\mathbf{0.5423} \\to$ LORO Platt $\\mathbf{0.0749}$ (**$-86.20\\%$**) | Mean conf **54.58%** vs. **31.67%** hit: Raw $\\text{ECE} = \\mathbf{0.2292} \\to$ LORO Platt $\\mathbf{0.1036}$ (**$-54.78\\%$**) | Mean conf **47.75%** vs. **36.67%** hit: Raw $\\text{ECE} = \\mathbf{0.1652} \\to$ LORO Platt $\\mathbf{0.0814}$ (**$-50.72\\%$**) | **Module 2 (LORO Platt Scaling):** Reduces Expected Calibration Error by **50.7% to 89.5%** across all four frontier model families |
"""
    write_lf(path, prefix + s7)
    print("Updated:", path)


def update_cover_letter():
    path = os.path.join(BASE, "COVER_LETTER_GEN2_NaturePortfolio_v1.0.md")
    cl = """# Cover Letter for Nature Portfolio Submission (npj Digital Medicine / Nature Machine Intelligence)

**Date:** October 29, 2026
**Manuscript Title:** Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery
**Target Journals (Route B Priority):** *npj Digital Medicine* / *Nature Machine Intelligence*
**Corresponding Authors:** Prof. Jiangtao Sheng (jtsheng@stu.edu.cn; Lead Contact) and Prof. Weiqiang Chen (wqchen@stu.edu.cn), Shantou University Medical College
**OSF Preregistration:** DOI 10.17605/OSF.IO/KF2G8 | **Zenodo Archive:** DOI 10.5281/zenodo.20574265

Dear Editors,

We are pleased to submit our Article entitled "Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery" for consideration for publication.

Autonomous multi-agent AI systems have recently demonstrated the capacity to generate therapeutic hypotheses, rank candidate mechanisms through pairwise tournaments, and synthesize experimental protocols for clinical and preclinical translation (e.g., Ghareeb et al., *Nature* 2026, DOI: 10.1038/s41586-026-10652-y; Gottweis et al., *Nature* 2026, DOI: 10.1038/s41586-026-10644-y). A central assumption driving current agentic AI deployment in biomedicine is that scaling test-time chain-of-thought reasoning allows frontier language models to self-correct citation hallucinations, evaluation biases, and overconfidence. However, the digital medicine and machine intelligence communities currently lack an end-to-end, externally anchored methodological standard to audit whether these discovery pipelines are trustworthy or to algorithmically rectify their structural failure modes before scarce experimental and clinical resources are committed.

To address this gap, we designed and executed **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) audit and zero-cost algorithmic remediation study across **9,130 primary live LLM invocations (35.58 million internal reasoning tokens across 8,973 white-box traces; 93.83% of all generated output tokens)** on **GLM-5.3 and DeepSeek-V4-Pro** plus a **2,688-evaluation cross-ecosystem validation suite across two US commercial frontier model families—Google Gemini (`Gemini-Pro` High-Thinking and `Gemini-Flash` Low-Thinking; 1,344 evaluations) and xAI Grok (`Grok-4.7` Full-Thinking and `Grok-4.7-Fast` Rapid-Thinking; 1,344 evaluations, 450,879 native reasoning tokens)**—totaling **11,818 live evaluations (36.03M reasoning tokens) across four sovereign frontier model families and 136 distinct biomedical disease contexts** (12 replicated end-to-end discovery runs in dry age-related macular degeneration and amyotrophic lateral sclerosis, a 14-specialty clinical citation-gating trial of 1,260 primary + 1,008 cross-ecosystem citation slots, and a 120-disease Mendelian Human Phenotype Ontology perturbation benchmark).

Our study reports three major methodological and empirical advances:

1. **White-Box Discovery of the Test-Time Reasoning Paradox Across Four Sovereign Frontier Model Families:** By tracking white-box `reasoning_content` trajectories across 8,973 raw CoT traces alongside 2,688 Google Gemini and xAI Grok-4.7 cross-ecosystem evaluations, we demonstrate quantitatively that allocating tens of thousands of internal reasoning tokens per call fails to self-correct structural pipeline vulnerabilities. Instead, unanchored chain-of-thought anchors **88.4–90.6% of Decile-1 attention on Slot A** and rationalizes positional flips ($p = 0.0254$, burning 3.60M reasoning tokens; `Grok-4.7` full thinking flips **13.3%** of pairs with **10.0%** subscore-verdict discordance vs. **8.9%** and **6.7%** on `Grok-4.7-Fast`), trials **35.82 candidate 7–8 digit PubMed identifiers per call** (129.4 total mentions and 390.3 hesitation markers/call) by prefix-guessing publication years until colliding with real off-topic papers, and obeys a **2.1% Instant-Recognition Law** in Mendelian gene inference where **23.3% of completed false-negative lists self-prune the true causal gene** after activating it early in CoT (`t = 2.1%` median depth in successful calls) in favor of canonical textbook syndromic attractors (`CHD7`, `KMT2D`, `FOXG1`, `POLG`, `FBXL4`).
2. **Cross-Ecosystem Identification of 'Trojan Horse Citations' and 'Index-Order Pathway Extinction':** We show that naive identifier existence checks score protocols as 96.9% to 100.0% valid across GLM-5.3, Google Gemini, and xAI Grok-4.7, whereas two-tier semantic verification reveals that **58.3% of Parent protocol citations, 54.3% of GLM-5.3 Experiment B citations, 73.8% of `Gemini-Pro` citations, 70.2% of `Gemini-Flash` citations, 32.1% of `Grok-4.7` citations, and 39.3% of `Grok-4.7-Fast` citations are Trojan horse citations** (real PubMed articles misattributed to unsupported clinical/biological claims). Simultaneously, we uncover a **71.3% Slot-A win rate** in single-order Tournament I screening ($p = 4.37 \\times 10^{-148}$) that interacts with bucket-indexed candidate generation to extinguish Bucket-3 extracellular matrix and complement pathways by 60% ($\\chi^2 = 55.40, p = 9.33 \\times 10^{-13}$), while **43.0% of Tournament II pairs on GLM-5.3, 17.8%/26.7% on `Gemini-Pro`/`Flash`, and 13.3%/8.9% on `Grok-4.7`/`Fast` flip under blinded independent-session A/B reversal** accompanied by a **$2.5\\times$ to $3.4\\times$ surge in DeBERTa-v3 NLI self-contradiction** ($p = 1.15 \\times 10^{-5}$).
3. **Four Zero-Cost Algorithmic Pipeline Rectification Modules ('Audit-to-Remediation'):** Moving beyond passive diagnosis, we introduce four lightweight mathematical and architectural rectification modules that require **zero additional LLM calls**: (i) **Order-Adjusted BTL Ranking with NLI-Discordance Neutralization**, which removes positional intercepts $\\hat{\\gamma}$ across primacy-biased (`GLM-5.3`), recency-biased (`Gemini-Flash`), and symmetric (`Gemini-Pro`, `Grok-4.7`) judges, reduces Bucket-3 pathway distortion by **72.8%**, and directly rescues causally validated human-genetic and clinical-stage disease pathways (`GAS6/MERTK` efferocytosis, `TIMP3/MMP9` ECM turnover, `ABCA1/LIPC` cholesterol efflux, and `CD59` MAC protection in dAMD; `MMP9/LAMA1`, `MCT1/SLC16A1`, and `CCS/ATP7A` in ALS); (ii) **Leave-One-Run-Out (LORO) Platt Scaling**, which reduces Expected Calibration Error by **50.7% to 89.5%** across all four frontier model families ($0.222 \\to 0.027$ in Parent runs; $0.459 \\to 0.119$ on `Gemini-Pro`; $0.542 \\to 0.075$ on `Gemini-Flash`; $0.229 \\to 0.104$ on `Grok-4.7`; $0.165 \\to 0.081$ on `Grok-4.7-Fast`); (iii) **Two-Tier Epistemic Citation Gating**, which halts CoT PMID dredging ($35.8 \\to 5.0$ candidate PMIDs/call, $p = 2.07 \\times 10^{-44}$), eliminates fabricated PMIDs ($q_{\\text{BH}} = 0.0310$), cuts ungrounded citations by **32.1 to 73.8 percentage points** ($p \\le 0.00097$), and reduces citation reasoning compute by **86.2% on GLM-5.3 and 96.7%–97.3% (30-fold native CoT token reduction) on Grok-4.7**; and (iv) **Chain-of-Thought Stream Recovery and Attractor Deconfounding (`CoT-SRAD`)**, which filters Leave-One-Disease-Out syndromic attractors and harvests self-pruned CoT candidates to rescue **+36 true Mendelian gene discoveries** ($p = 7.07 \\times 10^{-6}$; **+57.1% relative recall gain** on DeepSeek-V4-Pro, $p = 9.43 \\times 10^{-7}$).

All data, raw JSONL telemetry logs, verification caches, and analysis scripts are openly available under OSF DOI 10.17605/OSF.IO/KF2G8, Zenodo DOI 10.5281/zenodo.20574265, and GitHub (MIT License). This manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the manuscript and declare no competing interests.

Sincerely,

**Jiangtao Sheng, PhD** (Lead Contact)
Professor, Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China
Email: jtsheng@stu.edu.cn | ORCID: 0000-0003-2438-7345

**Weiqiang Chen, MD, PhD** (Co-Corresponding Author)
Professor, Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China
Email: wqchen@stu.edu.cn | ORCID: 0000-0002-2612-0890
"""
    write_lf(path, cl)
    print("Updated:", path)


def update_zh_manuscript():
    path = os.path.join(BASE, "STAR-Audit_手稿全文中文版_审核稿.md")
    s = read_lf(path)

    # 1. Highlights, Bigger Picture, Abstract
    s = replace_exact(
        s,
        "- **STAR-Audit** 在 136 种疾病背景下跨四大前沿模型（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro 与 Gemini-Flash）对 10,474 次真实模型评估（3,558 万个白盒思维链推理 Token）进行了系统审计\n- 白盒思维链轨迹动力学揭示了测试时推理为何及在哪个分位点发生失效，并催生零成本自救算法 **CoT-SRAD**\n- 真实 PMID 的语义张冠李戴（特洛伊木马引文，58.3%–73.8%）与位置偏倚（71.3% 首因偏倚及 17.8%–26.7% 盲法翻转）跨中美生态系统普遍存在\n- 四大零额外调用成本的算法纠偏模块救回了被压制的致病通路，将因果基因召回率相对提升 +57.1%（净挽救 +36 个基因发现，$p = 9.43 \\times 10^{-7}$），并将引文推理算力降低了 86.2%",
        "- **STAR-Audit** 在 136 种疾病背景下跨中美四大主权前沿模型家族、六个推理层级（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro/Flash 与 xAI Grok-4.7/Fast）对 11,818 次真实模型评估（3,603 万个内部推理 Token）进行了系统审计\n- 白盒思维链轨迹动力学揭示了测试时推理为何及在哪个分位点发生失效，并催生零成本自救算法 **CoT-SRAD**\n- 真实 PMID 的语义张冠李戴（特洛伊木马引文，32.1%–73.8%）与位置偏倚（71.3% 首因偏倚及 8.9%–43.0% 盲法翻转）跨四大模型家族普遍存在\n- 四大零额外调用成本的算法纠偏模块救回了被压制的致病通路，将因果基因召回率相对提升 +57.1%（净挽救 +36 个基因发现，$p = 9.43 \\times 10^{-7}$），并将引文推理算力降低了 86.2%–97.3%",
        "ZH Highlights",
    )

    s = replace_exact(
        s,
        "本研究在预注册协议下对涵盖 136 种疾病背景、跨越中美四大前沿模型（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro 与 Gemini-Flash）的 10,474 次真实模型评估（含 8,973 条完整白盒思维链轨迹、共 3,558 万个内部推理 Token）进行了审计，证明测试时思维链（Chain-of-Thought, CoT）往往是在“合理化”而非“纠正”失效模式：模型会在思维链中打捞多达 35.8 个候选 PMID 并引用真实的 PubMed 标识符来挂靠其并不支持的科学断言（特洛伊木马引文高达 54.3%–73.8%），在思维链前十分之一阶段（Decile-1）将 88.4%–90.6% 的注意力集中于 A 槽位从而导致排在后面的生物学通路被系统性淘汰（71.3% A 槽位胜率及 Gemini 上 17.8%–26.7% 的盲法翻转），",
        "本研究在预注册协议下对涵盖 136 种疾病背景、跨越中美四大主权前沿模型家族（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro/Flash 与 xAI Grok-4.7/Fast）的 11,818 次真实模型评估（含 8,973 条完整白盒思维链轨迹及 Grok 原生推理遥测、共 3,603 万个内部推理 Token）进行了审计，证明测试时思维链（Chain-of-Thought, CoT）往往是在“合理化”而非“纠正”失效模式：模型会在思维链中打捞多达 35.8 个候选 PMID 并引用真实的 PubMed 标识符来挂靠其并不支持的科学断言（特洛伊木马引文达 32.1%–73.8%），在思维链前十分之一阶段（Decile-1）将 88.4%–90.6% 的注意力集中于 A 槽位从而导致排在后面的生物学通路被系统性淘汰（71.3% A 槽位胜率及跨生态 8.9%–43.0% 的盲法翻转），",
        "ZH Bigger Picture",
    )

    s = replace_exact(
        s,
        "我们在涵盖 136 种疾病的三大实验场景中，跨中美四大前沿模型家族（GLM-5.3、DeepSeek-V4-Pro、高推理预算的 Google Gemini-Pro 以及低推理预算的 Google Gemini-Flash）对 9,130 次主框架 API 调用（共产生 3,558 万个白盒内部推理 Token，占全部输出 Token 的 93.83%）及 1,344 次跨生态系统 Google Gemini 验证评估进行了全面审计，揭示了“**测试时推理悖论（Test-Time Reasoning Paradox）**”：更深层的思维链推理未能自我纠正管线偏倚。朴素的存在性检查将 96.9%–100.0% 的实验方案 PubMed 标识符（PMID）判定为真实存在，而双层语义核验则揭露出其中 **54.3%–73.8% 为“特洛伊木马引文”（即真实存在但完全偏离主题的 PMID）**，其根源在于无防护推理每次调用在思维链中平均打捞 35.8 个候选 PMID。引入认识论引文门控将内部候选打捞截断至 5.0 个 PMID/次（$p = 2.07 \\times 10^{-44}$），将无根据引文比例降低了 50.0 至 73.8 个百分点（$p \\le 0.00097$），彻底消除了虚构 PMID（$q_{\\text{BH}} = 0.03096$），并将引文阶段推理 Token 消耗降低了 86.2%。此外，第一轮锦标赛（Tournament I）表现出高达 71.3% 的 A 槽位胜率（$p = 4.37 \\times 10^{-148}$），压制了第 3 分桶（Bucket-3，细胞外基质与补体系统）通路（$\\chi^2 = 55.40$），同时第二轮锦标赛（Tournament II）在 A/B 呈现顺序反转后发生 17.8%–43.0% 的判词翻转并伴随自然语言推理（NLI）自相矛盾率 2.5 倍的激增，而 23.3% 的孟德尔表型假阴性推断会将早在 2.1% 思维链深度激活的真正致病基因自我剪除。四个零额外调用的算法纠偏模块——顺位校正 Bradley–Terry–Luce 排序、留一运行 Platt 缩放、认识论引文门控与思维链流恢复及吸引子去混杂（`CoT-SRAD`）——救回了经验证的致病靶点，将校准误差降低了 74.1%–89.5%，并将孟德尔致病基因召回率相对提升了 57.1%（$p = 9.43 \\times 10^{-7}$）。",
        "我们在涵盖 136 种疾病的三大实验场景中，跨中美四大主权前沿模型家族、六个推理层级（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro/Flash 以及 xAI Grok-4.7/Fast）对 9,130 次主框架 API 调用（共产生 3,558 万个白盒内部推理 Token，占全部输出 Token 的 93.83%）及 2,688 次跨生态系统美国前沿模型（Google Gemini 与 xAI Grok-4.7，共 11,818 次真实评估、3,603 万个推理 Token）验证评估进行了全面审计，揭示了“**测试时推理悖论（Test-Time Reasoning Paradox）**”：更深层的思维链推理未能自我纠正管线偏倚。朴素的存在性检查将 96.9%–100.0% 的实验方案 PubMed 标识符（PMID）判定为真实存在，而双层语义核验则揭露出其中 **32.1%–73.8% 为“特洛伊木马引文”（即真实存在但完全偏离主题的 PMID）**，其根源在于无防护推理每次调用在思维链中平均打捞 35.8 个候选 PMID。引入认识论引文门控将内部候选打捞截断至 5.0 个 PMID/次（$p = 2.07 \\times 10^{-44}$），将无根据引文比例降低了 32.1 至 73.8 个百分点（$p \\le 0.00097$），彻底消除了虚构 PMID（$q_{\\text{BH}} = 0.03096$），并将引文阶段推理 Token 消耗降低了 86.2%–97.3%。此外，第一轮锦标赛（Tournament I）表现出高达 71.3% 的 A 槽位胜率（$p = 4.37 \\times 10^{-148}$），压制了第 3 分桶（Bucket-3，细胞外基质与补体系统）通路（$\\chi^2 = 55.40$），同时第二轮锦标赛（Tournament II）在 A/B 呈现顺序反转后发生 8.9%–43.0% 的判词翻转并伴随自然语言推理（NLI）自相矛盾率 2.5 倍的激增，而 23.3% 的孟德尔表型假阴性推断会将早在 2.1% 思维链深度激活的真正致病基因自我剪除。四个零额外调用的算法纠偏模块——顺位校正 Bradley–Terry–Luce 排序、留一运行 Platt 缩放、认识论引文门控与思维链流恢复及吸引子去混杂（`CoT-SRAD`）——救回了经验证的致病靶点，将校准误差降低了 50.7%–89.5%，并将孟德尔致病基因召回率相对提升了 57.1%（$p = 9.43 \\times 10^{-7}$）。",
        "ZH Abstract",
    )

    # 2. Intro & R1
    s = replace_exact(
        s,
        "我们在跨越中美两大生态系统的四个独立前沿模型（具备完整白盒思维链轨迹的 GLM-5.3 与 DeepSeek-V4-Pro，以及作为跨生态系统黑盒推理对比的 Google Gemini-Pro [高推理预算] 与 Google Gemini-Flash [低推理预算]）及 136 种不同的生物医学疾病背景下，通过 10,474 次真实模型评估（含 9,130 次主框架调用 [共产生 3,792 万个总输出 Token，其中 3,558 万个 (93.83%) 为内部推理 Token] 及 1,344 次跨生态系统 Google Gemini 验证评估）全面运行并验证了该框架（图 1A–D）。",
        "我们在跨越中美两大生态系统的四大主权前沿模型家族、六个推理层级（具备完整白盒思维链轨迹的 GLM-5.3 与 DeepSeek-V4-Pro，以及美国主流商业前沿架构 Google Gemini-Pro/Flash 与 xAI Grok-4.7/Fast）及 136 种不同的生物医学疾病背景下，通过 11,818 次真实模型评估（含 9,130 次主框架调用 [3,558 万个白盒推理 Token] 及 2,688 次跨生态系统 Google Gemini 与 xAI Grok-4.7 验证评估 [含 Grok 原生 45.09 万个推理 Token，全研究共 3,603 万个推理 Token]）全面运行并验证了该框架（图 1A–D）。",
        "ZH Intro para 4",
    )
    s = replace_exact(
        s,
        "跨四大前沿模型家族（`GLM-5.3`、`DeepSeek-V4-Pro`、`Gemini-Pro` 与 `Gemini-Flash`）定量揭示上游偏倚如何向下游实验方案传递并放大。",
        "跨四大主权前沿模型家族、六个推理层级（`GLM-5.3`、`DeepSeek-V4-Pro`、Google `Gemini-Pro`/`Flash` 与 xAI `Grok-4.7`/`Fast`）定量揭示上游偏倚如何向下游实验方案传递并放大。",
        "ZH Intro para 5",
    )
    s = replace_exact(
        s,
        "外加在第 R7 节中跨三大场景开展的 1,344 次跨生态系统 Google Gemini-Pro 与 Gemini-Flash 评估，全研究总计 **10,474 次真实模型评估**",
        "外加在第 R7 节中跨三大场景开展的 2,688 次跨生态系统 Google Gemini-Pro/Flash 与 xAI Grok-4.7/Fast 评估，全研究总计 **11,818 次真实模型评估、3,603 万个内部推理 Token**",
        "ZH R1",
    )

    # 3. Section R7 in Chinese
    old_zh_r7 = """### R7. 跨生态系统泛化验证：美国前沿模型 Google Gemini-Pro（高推理预算）与 Gemini-Flash（低推理预算）
一个关键的审稿与方法学问题是：**STAR-Audit** 揭露的三大失效模式（特洛伊木马引文、锦标赛位置偏倚与自相矛盾、罕见病过度自信与诱饵坍缩）究竟是中文开源/商用推理架构（GLM-5.3 与 DeepSeek-V4-Pro）所特有的局部现象，还是跨越中美不同训练语料与架构生态系统的普适规律？此外，在同一个模型家族内部，高测试时推理预算（High-thinking）与低测试时推理预算（Low-thinking）的配对比较能否进一步验证“测试时推理悖论”？为了回答这一问题，我们在不调用任何外部付费 API 的前提下，通过独立隔离的子智能体会话对美国主流前沿模型家族 **Google Gemini** 的两个配对推理层级——高推理预算的 **Gemini-Pro（High-Thinking）** 与低推理预算的 **Gemini-Flash（Low-Thinking）**——跨越全部三大核心实验场景开展了 **1,344 次严格受控的跨生态系统验证评估**（完整跨模型矩阵见补充表 S7）：

1. **场景 1（第二轮锦标赛 [Tournament II] 独立会话单向盲法配对评估 vs. 同会话联合上下文对照，共 720 次裁决）：** 为了严格区分“独立单次调用下的真实位置偏倚”与“同一上下文窗口内的记忆对齐伪影”，我们在 dAMD 和 ALS 的全部 45 个靶点档案对（共 90 个配对）上，首先使用 **180 次物理隔离的独立单向盲法会话**（正向 45 对与反向 45 对分别在完全互不知情的独立会话中评估，严格复现真实多智能体管线中逐次独立调用的运行环境）对 Gemini-Pro 与 Gemini-Flash 进行了测试（共 360 次盲法裁决），并与在同一会话中同时呈现正反配对的 **联合上下文对照（Joint-context control，360 次裁决）** 进行对比。在严格盲法的独立会话评估下，**高推理预算的 Gemini-Pro 在 17.78%（16/90 对：dAMD 中 13.33% [6/45]，ALS 中 22.22% [10/45]）的候选对上发生了 A/B 顺序反转判词翻转**，而 **低推理预算的 Gemini-Flash 则在高达 26.67%（24/90 对：dAMD 中 24.44% [11/45]，ALS 中 28.89% [13/45]）的候选对上发生了顺序翻转**（补充表 S7）。更为有趣的是，与表现出极端 A 槽位首因偏倚的 GLM-5.3（97.0% 倒向 A 槽位）不同，Gemini-Pro 的盲法翻转呈现出对称的双向位置震荡（A 槽位总胜率 51.11% [92/180]，16 个翻转对中 9 对双双判 A 胜、7 对双双判 B 胜），而 **Gemini-Flash 则表现出轻度的 B 槽位近因偏倚（Recency bias）**（B 槽位总胜率 54.44% [98/180]，在 dAMD 中 B 槽位胜率达 57.78% [52/90]，其中 11 个翻转对中有 9 对双双判后出现的 B 槽位获胜）。此外，我们在独立盲法裁决中还发现了一种跨生态系统的内部自相矛盾现象——**“分项打分与最终胜负倒挂（Subscore-verdict NLI discordance）”**：Gemini-Pro 在 5.00%（9/180）的裁决中、Gemini-Flash 在 1.67%（3/180）的裁决中，给某一个候选方案打出了更高的科学性/可行性/创新性平均分，却在最终 `winner` 字段将对方判为获胜者。应用 **模块 1（顺位校正 BTL 结合 NLI 不一致中性化）** 后，算法自动同时校正了首因偏倚、近因偏倚与对称翻转（调整后与未校正前单向排名的 Kendall $\\tau$ 在 Gemini-Pro 上为 $0.867$ [dAMD] 与 $0.778$ [ALS]，在 Gemini-Flash 上为 $0.644$ [dAMD] 与 $0.733$ [ALS]），并在两个模型上均成功将 dAMD 的核心靶点档案 `C06` 和 ALS 的核心靶点档案 `C10` 救回至 Top 3。相比之下，当正反配对被放入同一个联合上下文会话中评估时，两个模型均利用上下文窗口记忆实现了 0.00% 的表面翻转率——这从方法学上证明：**任何有效的锦标赛位置公平性审计都必须在严格物理隔离的独立会话中执行正反平衡测试**。

2. **场景 2（实验 B 跨 14 个临床专科领域的三臂引文门控试验，共 504 个引文槽位，并通过 NCBI Entrez 实时核验 183 个独立 PMID）：** 在 14 个临床疾病领域（每模型每臂 84 个引文槽位，共 504 个槽位）中，**高推理预算的 Gemini-Pro 在无防护 `as_discovered` 臂中表现出了高达 100.0%（84/84）的 Tier-1 表面 PMID 存在率（虚构假 PMID 为 0.00%），然而 Tier-2 语义核验揭露其中 73.81%（62/84）全都是真实但偏离主题的“特洛伊木马引文”**（仅有 26.19% [22/84] 为真正切题的引文；图 2D；补充表 S7）。同样地，**Gemini-Flash 在 `as_discovered` 臂中表现出 98.81%（83/84）的表面 PMID 存在率（1.19% [1/84] 假 PMID），但其中 70.24%（59/84）为特洛伊木马引文，总无根据引文率高达 71.43%（60/84）**。这一结果强有力地证实：“特洛伊木马引文”绝非单一厂商模型的偶然缺陷，而是所有前沿大语言模型在强制引文槽位压力下的普适性失效模式——且推理能力越强的模型（Gemini-Pro 100.0% 真实 PMID，73.81% 特洛伊木马）越擅长从参数记忆中检索真实存在的顶刊 PMID 来包装无文献支撑的科学断言。引入 `abstain_probe`（温和弃权探针）后，Gemini-Pro 与 Gemini-Flash 的总无根据引文率分别降至 **13.10%**（11/84，弃权率 77.38%）和 **38.10%**（32/84，弃权率 46.43%）。而部署 **模块 3（`gated` 认识论引文门控）** 后，**Gemini-Pro 的总无根据引文率从 73.81% 彻底清零至 0.00%（0/84，净降幅 $-73.81$ 个百分点，双侧 Fisher 精确检验 $p = 3.1 \\times 10^{-27}$）**，**Gemini-Flash 的总无根据引文率也从 71.43% 大幅降至 21.43%（18/84，净降幅 $-50.00$ 个百分点，$p = 6.2 \\times 10^{-11}$，假 PMID 清零至 0.00%；图 2D）**。

3. **场景 3（实验 C-v4 掩码孟德尔病 HPO 信息量梯度删减、诱饵吸引子与 LORO Platt 校准，共 120 次预测评估）：** 在 20 种分层抽样的孟德尔疾病上跨越 0%、25% 与 50% `del_topIC` 表型信息量删减梯度（每模型 60 次评估），高推理预算的 **Gemini-Pro 总体 `Hit@10` 致病基因召回率为 33.33%（20/60：随删减剂量从 `35.0% [0% 与 25% 剂量] 降至 30.0% [50% 剂量]`）**，高于低推理预算的 **Gemini-Flash（总体 `Hit@10` 为 26.67% [16/60]：随删减剂量从 `30.0% [0% 与 25% 剂量] 降至 20.0% [50% 剂量]`；图 3C）**。与 GLM-5.3 和 DeepSeek-V4-Pro 一致，两个 Google Gemini 模型在预测失败时同样系统性地坍缩至经典的纤毛病与线粒体综合征诱饵吸引子（`POLG` [9–10 次假阳性调用]、`NDUFS1`、`NDUFV1`、`TBC1D24`、`CEP290`、`TMEM67`、`AHI1` 与 `CC2D2A`），并且表现出更为剧烈的口头过度自信：**Gemini-Pro 平均报告置信度高达 79.18%（对比实际 33.33% 命中率，未校准前 $\\text{ECE} = 0.4585$，Brier $= 0.4328$）**，**Gemini-Flash 平均报告置信度更高达 80.90%（对比实际 26.67% 命中率，未校准前 $\\text{ECE} = 0.5423$，Brier $= 0.4932$；图 5B）**。应用 **模块 2（留一疾病交叉验证 Platt 缩放）** 后，**Gemini-Pro 的期望校准误差（ECE）从 0.4585 骤降至 0.1186（降幅达 $-74.13\\%$，Brier 降至 $0.2225$）**，**Gemini-Flash 的 ECE 从 0.5423 骤降至 0.0749（降幅达 $-86.20\\%$，Brier 降至 $0.1955$；图 5B；补充表 S7）**。这证明 **STAR-Audit** 的诊断与零成本算法纠偏模块在中美四大前沿模型架构上均具有卓越的普适性与鲁棒性。"""

    new_zh_r7 = """### R7. 跨生态系统泛化验证：美国主流前沿架构 Google Gemini（Pro/Flash）与 xAI Grok-4.7（Full/Fast）
一个关键的审稿与方法学问题是：**STAR-Audit** 揭露的三大失效模式（特洛伊木马引文、锦标赛位置偏倚与自相矛盾、罕见病过度自信与诱饵坍缩）究竟是中文开源/商用推理架构（GLM-5.3 与 DeepSeek-V4-Pro）所特有的局部现象，还是跨越中美不同训练语料与架构生态系统的普适规律？此外，在同一个模型家族内部，高测试时推理预算（High/Full-thinking）与低/快测试时推理预算（Low/Fast-thinking）的配对比较能否进一步验证“测试时推理悖论”？为了回答这一问题，我们在零外部付费 API 调用的前提下，对美国两大主流商业前沿模型家族——**Google Gemini（高推理预算的 `Gemini-Pro` 与低推理预算的 `Gemini-Flash`，1,344 次评估）** 以及 **xAI Grok（完整推理的 `Grok-4.7` 与快速推理的 `Grok-4.7-Fast`，通过官方 Grok Build CLI `v1.0.70` 执行 1,344 次评估，完整记录 450,879 个原生思维链推理 Token 与 1,185,113 个总 Token）**——跨越全部三大核心实验场景开展了 **2,688 次严格受控的跨生态系统验证评估**（完整四大家族、六大层级矩阵见补充表 S7）：

1. **场景 1（第二轮锦标赛 [Tournament II] 独立会话单向盲法配对评估 vs. 同会话联合上下文对照，共 1,440 次裁决）：** 为了严格区分“独立单次调用下的真实位置偏倚”与“同一上下文窗口内的记忆对齐伪影”，我们在 dAMD 和 ALS 的全部 45 个靶点档案对（共 90 个配对）上，首先使用物理隔离的独立单向盲法会话对四个美国前沿模型层级进行了测试（720 次盲法裁决），并与在同一会话中同时呈现正反配对的 **联合上下文对照（Joint-context control，720 次裁决）** 进行对比。在严格盲法的独立会话评估下，**`Gemini-Pro` 在 17.78%（16/90 对：dAMD 13.33% [6/45]，ALS 22.22% [10/45]）的候选对上发生顺序翻转**，**`Gemini-Flash` 在 26.67%（24/90 对：dAMD 24.44% [11/45]，ALS 28.89% [13/45]）的候选对上发生翻转**，**`Grok-4.7` 在 13.33%（12/90 对：dAMD 11.11% [5/45]，ALS 15.56% [7/45]）的候选对上发生翻转**，而 **`Grok-4.7-Fast` 在 8.89%（8/90 对：dAMD 6.67% [3/45]，ALS 11.11% [5/45]）的候选对上发生翻转**（补充表 S7）。尤为引人注目的是，在 xAI Grok 家族内部，分配更高推理预算的 `Grok-4.7` 反而在盲法顺序翻转率（13.33% 对比 8.89%）和“分项打分与最终胜负倒挂（Subscore-verdict NLI discordance）”率（**10.00% [18/180]** 对比 **6.67% [12/180]**；`Gemini-Pro` 与 `Gemini-Flash` 分别为 5.00% 与 1.67%）上均高于快速推理的 `Grok-4.7-Fast`，独立印证了“更深层的无锚定推理会加剧动机性合理化”的推理悖论。在位置极性上，不同于表现极端 A 槽位首因偏倚的 `GLM-5.3`（97.0% 倒向 A 槽位），`Gemini-Flash` 表现出轻度 **B 槽位近因偏倚**（B 槽位总胜率 54.44%，dAMD 中达 57.78%），而 `Gemini-Pro`（A 槽位胜率 51.11%）、`Grok-4.7`（A 槽位胜率 48.89% [88/180]，二项检验 $p = 0.823$）与 `Grok-4.7-Fast`（A 槽位胜率 48.89% [88/180]，$p = 0.823$）均表现为对称的双向翻转震荡。相比之下，在联合上下文对照（720 次裁决）中，全部四个美国模型层级均利用上下文窗口记忆表现出 **0.00%** 的表面翻转率，从方法学上证明了独立会话正反平衡审计的必要性。应用 **模块 1（顺位校正 BTL 结合 NLI 不一致中性化）** 后，算法自动同时校正了首因偏倚、近因偏倚与对称翻转（Kendall $\\tau$ 在 `Grok-4.7` 上为 $0.867\\text{--}0.956$，在 `Gemini-Pro` 上为 $0.778\\text{--}0.867$，在 `Gemini-Flash` 上为 $0.644\\text{--}0.733$），成功救回了 dAMD 的 `C06` 与 ALS 的 `C10`/`C02` 核心靶点排名。

2. **场景 2（实验 B 跨 14 个临床专科领域的三臂引文门控试验，共 1,008 个跨生态引文槽位，经 NCBI Entrez 实时核验）：** 在 14 个临床疾病领域的无防护 `as_discovered` 臂（每模型 84 个槽位）中，**`Gemini-Pro`（100.0% [84/84]）、`Gemini-Flash`（98.81% [83/84]）、`Grok-4.7`（100.0% [84/84]）与 `Grok-4.7-Fast`（98.81% [83/84]）输出的 PMID 几乎全部在 PubMed 中真实存在**（虚构假 PMID 仅为 0.00%–1.19%）；然而 Tier-2 语义核验揭露：**`Gemini-Pro` 中高达 73.81%（62/84）、`Gemini-Flash` 中 70.24%（59/84；总无根据率 71.43%）、`Grok-4.7` 中 32.14%（27/84）以及 `Grok-4.7-Fast` 中 39.29%（33/84；总无根据率 40.48%）全都是偏离主题的“特洛伊木马引文”**（图 2D；补充表 S7）。引入 `abstain_probe` 后，`Gemini-Pro` 与 `Gemini-Flash` 的无根据引文率降至 13.10% 与 38.10%，而 **`Grok-4.7` 与 `Grok-4.7-Fast` 在 `abstain_probe` 和 `gated`（认识论引文门控）下均实现了 100.0%（84/84）的认识论弃权，将无根据引文率彻底清零至 0.00%**（`Grok-4.7` 净降幅 **$-32.14$ 个百分点，Fisher 精确检验 $p = 1.23 \\times 10^{-9}$**；`Grok-4.7-Fast` 净降幅 **$-40.48$ 个百分点，$p = 1.72 \\times 10^{-12}$**；`Gemini-Pro` 降至 **0.00%，$-73.81\\text{ pp}, p = 3.1 \\times 10^{-27}$**；`Gemini-Flash` 降至 **21.43%，$-50.00\\text{ pp}, p = 6.2 \\times 10^{-11}$**；图 2D）。尤为关键的是，xAI Grok CLI 的原生推理 Token 遥测直接在美国商业模型上复现并证实了“悖论 2”：在 `as_discovered` 臂下，`Grok-4.7` 与 `Grok-4.7-Fast` 分别消耗了 **10,072 个和 12,284 个原生推理 Token**（耗时 187–242 秒）在参数记忆中搜寻候选 PMID；而在 `gated` 门控下，原生推理 Token 骤降 **30 倍以上，仅需 332 个和 330 个推理 Token**（耗时 26–43 秒，引文推理算力削减达 **96.7%–97.3%**）。

3. **场景 3（实验 C-v4 掩码孟德尔病 HPO 信息量梯度删减、诱饵吸引子与 LORO Platt 校准，共 240 次跨生态评估）：** 在 20 种分层抽样的孟德尔疾病上跨越 0%、25% 与 50% `del_topIC` 删减梯度（每模型 60 次评估），致病基因 `Hit@10` 在 **`Gemini-Pro` 上从 `35.0% -> 35.0% -> 30.0%`（总体 33.33% [20/60]）**，在 **`Gemini-Flash` 上从 `30.0% -> 30.0% -> 20.0%`（总体 26.67% [16/60]）**，在 **`Grok-4.7` 上从 `45.0% -> 30.0% -> 20.0%`（总体 31.67% [19/60]）**，在 **`Grok-4.7-Fast` 上从 `40.0% -> 35.0% -> 35.0%`（总体 36.67% [22/60]；图 3C）**。值得注意的是，在 50% 高信息量表型删减下，深度长推理的 `Grok-4.7`（每 10 例批次消耗 17,616–26,613 个原生推理 Token）的准确率（20.0%）反而低于快速推理的 `Grok-4.7-Fast`（35.0%），因为表型残缺下的长思维链过度推敲将候选基因引向了经典的线粒体与纤毛病综合征吸引子（`FBXL4` [10 次假阳性]、`POLG` [9–10 次]、`CEP290` [7 次]、`CUL7` [6 次]、`OBSL1` [6 次]、`TMEM67` [6 次]、`CC2D2A` [6 次] 与 `CPLANE1` [6 次]），独立验证了思维链过度思考的自我剪除效应。全部四个美国模型层级均表现出显著的口头过度自信（未校准前 $\\text{ECE}$：`Gemini-Pro` 为 $0.4585$，`Gemini-Flash` 为 $0.5423$，`Grok-4.7` 为 $0.2292$ [平均置信度 54.58% vs. 命中率 31.67%]，`Grok-4.7-Fast` 为 $0.1652$ [平均置信度 47.75% vs. 命中率 36.67%]）。应用 **模块 2（留一疾病交叉验证 Platt 缩放）** 后，期望校准误差（ECE）在 **`Gemini-Pro` 上降低 74.13%（$0.4585 \\to 0.1186$）**、在 **`Gemini-Flash` 上降低 86.20%（$0.5423 \\to 0.0749$）**、在 **`Grok-4.7` 上降低 54.78%（$0.2292 \\to 0.1036$）**、在 **`Grok-4.7-Fast` 上降低 50.72%（$0.1652 \\to 0.0814$；图 5B；补充表 S7）**。这证明 **STAR-Audit** 的六维审计与四大零成本纠偏模块在中美四大主权模型家族、六个推理层级上均具有高度一致的普适性与鲁棒性。"""
    s = replace_exact(s, old_zh_r7, new_zh_r7, "ZH R7")

    # 4. Discussion, Methods, Legends, Tables in Chinese
    s = replace_exact(
        s,
        "本研究在 9,130 次具备完整白盒思维链轨迹的主 API 调用（3,558 万个内部推理 Token，涵盖 GLM-5.3 与 DeepSeek-V4-Pro）、1,344 次跨生态系统 Google Gemini 评估（Pro 高推理预算与 Flash 低推理预算）及 136 种疾病背景下执行了预注册的 **STAR-Audit** 框架，确立了两条核心结论（图 7）。",
        "本研究在 9,130 次具备完整白盒思维链轨迹的主 API 调用（3,558 万个内部推理 Token，涵盖 GLM-5.3 与 DeepSeek-V4-Pro）、2,688 次跨生态系统 Google Gemini（Pro/Flash）与 xAI Grok（Grok-4.7/Fast，45.09 万个原生推理 Token）评估（全研究总计 11,818 次真实评估、3,603 万个推理 Token，横跨四大主权前沿模型家族、六个推理层级）及 136 种疾病背景下执行了预注册的 **STAR-Audit** 框架，确立了两条核心结论（图 7）。",
        "ZH Discussion intro",
    )
    s = replace_exact(
        s,
        "（GLM/DeepSeek 上的 `CHD7`、`KMT2D`、`FOXG1`、`CEP290`；Gemini 上的 `POLG`、`CEP290`、`TMEM67`、`AHI1`）。",
        "（GLM/DeepSeek 上的 `CHD7`、`KMT2D`、`FOXG1`、`CEP290`；Gemini 与 Grok-4.7 上的 `POLG`、`FBXL4`、`CEP290`、`TMEM67`、`CUL7`、`AHI1`）。",
        "ZH Discussion Paradox 3",
    )
    s = replace_exact(
        s,
        "逐次调用 JSONL 遥测日志（9,130 次主框架调用及 8,973 条完整白盒思维链轨迹，外加 1,344 次跨生态系统 Google Gemini 评估日志，总计 10,474 次模型评估）、模型原始响应文本、PubMed 核验缓存（主运行与实验 B 956 个独立 PMID + Gemini 验证集 183 个独立 PMID）",
        "逐次调用 JSONL 遥测日志（9,130 次主框架调用及 8,973 条完整白盒思维链轨迹，外加 2,688 次跨生态系统 Google Gemini 与 xAI Grok-4.7 评估日志，总计 11,818 次模型评估、3,603 万个推理 Token）、模型原始响应文本、PubMed 核验缓存（主运行与实验 B 956 个独立 PMID + Gemini 验证集 183 个独立 PMID + Grok 验证集 137 个独立 PMID）",
        "ZH Data availability",
    )
    s = replace_exact(
        s,
        "统计审计与白盒轨迹/跨生态验证脚本（`step1` 至 `step5`、`analyze_cot_trajectory_dynamics.py`、`analyze_gemini_cross_ecosystem.py`）",
        "统计审计与白盒轨迹/跨生态验证脚本（`step1` 至 `step5`、`analyze_cot_trajectory_dynamics.py`、`analyze_gemini_cross_ecosystem.py`、`run_grok_cross_ecosystem.py`、`analyze_grok_cross_ecosystem.py`）",
        "ZH Code availability",
    )
    s = replace_exact(
        s,
        "在 **跨生态系统 Google Gemini 验证（第 R7 节）** 中，我们在物理隔离的子智能体会话下对高推理预算的 **Gemini-Pro（High-Thinking）** 与低推理预算的 **Gemini-Flash（Low-Thinking）** 执行了 1,344 次标准化评估（`analyze_gemini_cross_ecosystem.py`）：涵盖场景 1（Tournament II 独立会话单向盲法配对评估 360 次裁决 + 联合上下文对照 360 次裁决）、场景 2（实验 B 跨 14 个临床专科领域三臂引文试验 504 个引文槽位，全部非弃权 PMID 经 NCBI Entrez 实时核验并缓存于 `pubmed_verification_cache.json`）以及场景 3（实验 C-v4 在 0%、25%、50% `del_topIC` 下的 120 次致病基因预测与留一疾病交叉验证 Platt 重校准；完整结果见补充表 S7）。",
        "在 **跨生态系统 Google Gemini 与 xAI Grok-4.7 验证（第 R7 节）** 中，我们对 **Google Gemini（`Gemini-Pro` 高推理预算与 `Gemini-Flash` 低推理预算，1,344 次评估）** 及 **xAI Grok（`Grok-4.7` 完整推理与 `Grok-4.7-Fast` 快速推理，通过官方 Grok Build CLI `v1.0.70` 执行 1,344 次评估，记录 450,879 个原生推理 Token）** 共计执行了 2,688 次标准化跨生态评估（`analyze_gemini_cross_ecosystem.py`、`run_grok_cross_ecosystem.py`、`analyze_grok_cross_ecosystem.py`）：涵盖场景 1（Tournament II 独立会话单向盲法配对评估 720 次裁决 + 联合上下文对照 720 次裁决）、场景 2（实验 B 跨 14 个临床专科领域三臂引文试验 1,008 个引文槽位，全部非弃权 PMID 经 NCBI Entrez 实时核验）以及场景 3（实验 C-v4 在 0%、25%、50% `del_topIC` 下的 240 次致病基因预测与留一疾病交叉验证 Platt 重校准；完整结果见补充表 S7）。",
        "ZH Methods item 7",
    )
    s = replace_exact(
        s,
        "在本工作的开展过程中，作者将大语言模型（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro 与 Google Gemini-Flash）作为被审计的核心实验研究对象",
        "在本工作的开展过程中，作者将大语言模型（GLM-5.3、DeepSeek-V4-Pro、Google Gemini-Pro、Google Gemini-Flash、xAI Grok-4.7 与 xAI Grok-4.7-Fast）作为被审计的核心实验研究对象",
        "ZH AI declaration",
    )

    # Legends & Tables in ZH
    s = replace_exact(
        s,
        "以及右侧叠加展示的美国前沿模型 **Google Gemini-Pro**（无根据引文率从 $73.8\\% \\to 13.1\\% \\to 0.0\\%$）与 **Google Gemini-Flash**（$71.4\\% \\to 38.1\\% \\to 21.4\\%$）跨生态系统三臂门控轨迹。",
        "以及右侧叠加展示的美国前沿模型 **Google Gemini-Pro**（$73.8\\% \\to 13.1\\% \\to 0.0\\%$）、**Google Gemini-Flash**（$71.4\\% \\to 38.1\\% \\to 21.4\\%$）、**xAI Grok-4.7**（$32.1\\% \\to 0.0\\% \\to 0.0\\%$，原生 CoT 从 $10.07\\text{k} \\to 0.33\\text{k}$）与 **Grok-4.7-Fast**（$40.5\\% \\to 0.0\\% \\to 0.0\\%$，原生 CoT 从 $12.28\\text{k} \\to 0.33\\text{k}$）跨生态系统三臂门控轨迹。",
        "ZH Fig 2D legend",
    )
    s = replace_exact(
        s,
        "跨生态系统 **Google Gemini-Pro**（$35.0\\% \\to 30.0\\%$）与 **Google Gemini-Flash**（$30.0\\% \\to 20.0\\%$）轨迹，",
        "跨生态系统 **Google Gemini-Pro**（$35.0\\% \\to 35.0\\% \\to 30.0\\%$）、**Gemini-Flash**（$30.0\\% \\to 30.0\\% \\to 20.0\\%$）、**xAI Grok-4.7**（$45.0\\% \\to 30.0\\% \\to 20.0\\%$）与 **Grok-4.7-Fast**（$40.0\\% \\to 35.0\\% \\to 35.0\\%$）轨迹，",
        "ZH Fig 3C legend",
    )
    s = replace_exact(
        s,
        "以及叠加展示的跨生态系统 **Google Gemini-Pro**（未校准前 $\\text{ECE} = 0.459 \\to$ Platt 校准后 $\\text{ECE} = 0.119$，降幅 $-74.1\\%$）与 **Google Gemini-Flash**（未校准前 $\\text{ECE} = 0.542 \\to$ Platt 校准后 $\\text{ECE} = 0.075$，降幅 $-86.2\\%$）重校准迁移轨迹。",
        "以及叠加展示的跨生态系统 **Google Gemini-Pro**（$\\text{ECE } 0.459 \\to 0.119, -74.1\\%$）、**Gemini-Flash**（$0.542 \\to 0.075, -86.2\\%$）、**xAI Grok-4.7**（$0.229 \\to 0.104, -54.8\\%$）与 **Grok-4.7-Fast**（$0.165 \\to 0.081, -50.7\\%$）重校准迁移轨迹。",
        "ZH Fig 5B legend",
    )
    s = replace_exact(
        s,
        "**第 2 阶段（中间，六维外部真值诊断传感器）：** 六个外部真值传感器对 $N = 9,130$ 次主框架真实 API 调用（跨越 $8,973$ 条白盒轨迹，共 $3,558$ 万个 CoT tokens）及 $1,344$ 次跨生态系统 Google Gemini 评估进行全面审计，涵盖实时 NCBI Entrez 双层核验（$1,620 + 504$ 个引文槽位）、$120$ 种孟德尔病 HPO 信息量掩码扰动（$804 + 120$ 次多厂商调用）、正反平衡 A/B 顺序反转探针（$1,601 + 180$ 个双向候选对）、$10,000$ 次判词表自助重采样（Bootstrap）、DeBERTa-v3 双向 NLI 矛盾分类（$18,470$ 对断言配对）以及样本外置信度校准遥测。**第 3 阶段（右侧，四大零成本算法纠偏模块与生物学拯救效应）：** 四个零边际成本算法纠偏模块——顺位校正 BTL 结合 NLI 不一致过滤（$100\\%$ 清除位置偏倚，第 3 分桶通路存活率提升 $+81.3\\%$）、留一运行（LORO）Platt 缩放（ECE 降低 $74.1\\%\\text{--}89.5\\%$）、双层认识论引文门控（清除 $95.0\\%\\text{--}100.0\\%$ 无根据引文错误，节省 $-86.2\\%$ 引文 CoT 算力）",
        "**第 2 阶段（中间，六维外部真值诊断传感器）：** 六个外部真值传感器对 $N = 9,130$ 次主框架真实 API 调用（跨越 $8,973$ 条白盒轨迹，共 $3,558$ 万个 CoT tokens）及 $2,688$ 次跨生态系统 Google Gemini 与 xAI Grok-4.7 评估（全研究共 $11,818$ 次评估、$3,603$ 万个推理 Token）进行全面审计，涵盖实时 NCBI Entrez 双层核验（$1,620 + 1,008$ 个引文槽位）、$120$ 种孟德尔病 HPO 信息量掩码扰动（$804 + 240$ 次多厂商调用）、正反平衡 A/B 顺序反转探针（$1,601 + 360$ 个双向候选对）、$10,000$ 次判词表自助重采样（Bootstrap）、DeBERTa-v3 双向 NLI 矛盾分类（$18,470$ 对断言配对）以及样本外置信度校准遥测。**第 3 阶段（右侧，四大零成本算法纠偏模块与生物学拯救效应）：** 四个零边际成本算法纠偏模块——顺位校正 BTL 结合 NLI 不一致过滤（$100\\%$ 清除位置偏倚，第 3 分桶通路存活率提升 $+81.3\\%$）、留一运行（LORO）Platt 缩放（ECE 降低 $50.7\\%\\text{--}89.5\\%$）、双层认识论引文门控（清除 $95.0\\%\\text{--}100.0\\%$ 无根据引文错误，节省 $-86.2\\%\\text{ 至 }-97.3\\%$ 引文 CoT 算力）",
        "ZH Fig 7 legend",
    )

    old_zh_t1 = "| **STAR-Audit（本研究）** | **六维审计与 4 模块零成本算法纠偏（136 种疾病，9,130 + 1,344 次评估，中美 4 大前沿模型）** | **是（12 次完整 6 步运行 + 实验 B + 实验 C-v4 + Gemini Pro/Flash 验证套件）** | **是（揭露 54.3%–73.8% 特洛伊木马引文及 35.8 个 CoT PMID/次；门控降低 $-50.0\\text{ 至 }-73.8\\text{ pp}$）** | **是（dAMD/ALS 盲法 + 120 种孟德尔病 HPO 扰动 + `CoT-SRAD` 相对提升 $+57.1\\%$ 召回率）** | **是（$\\hat{\\gamma}$ 校正削减 72.8% 分桶偏斜并救回实证靶点；同时校正首因/近因/对称翻转）** | **是（DeBERTa-v3 审计 17,990 条断言；翻转矛盾激增 $2.5\\times$）** | **是（10,000 次 Bootstrap 零分布 + LORO Platt 在 4 模型上降低 74.1%–89.5% ECE）** | **是（OSF: 10.17605/OSF.IO/KF2G8；BH-FDR $q=0.05$）** |"
    new_zh_t1 = "| **STAR-Audit（本研究）** | **六维审计与 4 模块零成本算法纠偏（136 种疾病，9,130 + 2,688 = 11,818 次评估，中美 4 大主权模型家族 / 6 层级）** | **是（12 次完整 6 步运行 + 实验 B + 实验 C-v4 + Gemini Pro/Flash 与 Grok-4.7/Fast 验证套件）** | **是（揭露 32.1%–73.8% 特洛伊木马引文及 35.8 个 CoT PMID/次；门控降低 $-32.1\\text{ 至 }-73.8\\text{ pp}$）** | **是（dAMD/ALS 盲法 + 120 种孟德尔病 HPO 扰动 + `CoT-SRAD` 相对提升 $+57.1\\%$ 召回率）** | **是（$\\hat{\\gamma}$ 校正削减 72.8% 分桶偏斜并救回实证靶点；同时校正首因/近因/对称翻转）** | **是（DeBERTa-v3 审计 17,990 条断言；翻转矛盾激增 $2.5\\times$）** | **是（10,000 次 Bootstrap 零分布 + LORO Platt 在 4 大家族上降低 50.7%–89.5% ECE）** | **是（OSF: 10.17605/OSF.IO/KF2G8；BH-FDR $q=0.05$）** |"
    s = replace_exact(s, old_zh_t1, new_zh_t1, "ZH Table 1")

    old_zh_t2_1 = "| **维度 1：忠实度**（验证性成员 1） | 实验 B 随机试验（14 临床领域，1,260 GLM + 504 Gemini 槽位）+ 主运行第 6 步（360 槽位） | 朴素检查：96.9%–100.0% 存在；Tier-2 揭露 **58.33%**（主运行）、**57.38%**（GLM 实验 B；35.8 个 CoT PMID/次）、**73.81%**（Gemini-Pro）与 **70.24%**（Gemini-Flash）特洛伊木马 PMID | 假 PMID 风险差 $+3.10\\%$（$p = 0.01032$，**$q_{\\text{BH}} = 0.03096^*$**）；无根据风险差 $+54.52\\%$（$p = 0.00097$）；CoT PMID 打捞 $p = 2.07 \\times 10^{-44}$ | **模块 3：** 双层语义锚定与认识论弃权门控 | 假 PMID **0.00%**；无根据引文率降至 **2.86%**（GLM $-54.52\\text{ pp}$）与 **0.00%**（Gemini-Pro $-73.81\\text{ pp}$）；CoT PMID **5.0/次**；**节省 86.2% CoT 推理 Token** |"
    new_zh_t2_1 = "| **维度 1：忠实度**（验证性成员 1） | 实验 B 随机试验（14 临床领域，1,260 GLM + 504 Gemini + 504 Grok 槽位）+ 主运行第 6 步（360 槽位） | 朴素检查：96.9%–100.0% 存在；Tier-2 揭露 **58.33%**（主运行）、**54.29%**（GLM 实验 B；35.8 个 CoT PMID/次）、**73.81%/70.24%**（Gemini）与 **32.14%/39.29%**（Grok-4.7/Fast）特洛伊木马 PMID | 假 PMID 风险差 $+3.10\\%$（$p = 0.01032$，**$q_{\\text{BH}} = 0.03096^*$**）；无根据风险差 $+54.52\\%$（$p = 0.00097$）；CoT PMID 打捞 $p = 2.07 \\times 10^{-44}$ | **模块 3：** 双层语义锚定与认识论弃权门控 | 假 PMID **0.00%**；无根据引文率降至 **2.86%**（GLM）与 **0.00%**（Gemini-Pro、Grok-4.7、Grok-Fast）；CoT PMID **5.0/次**；**节省 86.2%–97.3% CoT 推理 Token** |"
    s = replace_exact(s, old_zh_t2_1, new_zh_t2_1, "ZH Table 2 Dim 1")

    old_zh_t2_2c = "| **维度 2：HPO 信息量删减**（验证性成员 2 & 3） | 实验 C-v4（120 种孟德尔病，GLM/DeepSeek 共 $n=630$ + Gemini Pro/Flash $n=120$） | DeepSeek `del_topIC` recall@10 呈剂量坍缩 $28.3\\% \\to 22.6\\% \\to 14.3\\%$（$p=0.0259$）；真基因在 **2.1% CoT 深度** 激活，但 **23.3%** 假阴性自我剪除且 **33.3%** 截断调用已找到真基因 | 双模型合并 $\\beta_1 = -0.573$（$p = 0.2191, q_{\\text{BH}} = 0.2629$）；`CoT-SRAD` McNemar $p = 7.07 \\times 10^{-6}$（合并）与 $p = 9.43 \\times 10^{-7}$（DeepSeek） | **模块 4（`CoT-SRAD`）：** LODO 吸引子去混杂（`CHD7`, `KMT2D`, `FOXG1`, `POLG`）与思维链流恢复 | 零额外调用挽救 **+36 个致病基因发现**（合并 $26.35\\% \\to 32.06\\%$）；将 DeepSeek 召回率相对提升 **+57.1%**（$20.66\\% \\to 32.47\\%$，净增 +32 次调用） |"
    new_zh_t2_2c = "| **维度 2：HPO 信息量删减**（验证性成员 2 & 3） | 实验 C-v4（120 种孟德尔病，GLM/DeepSeek 共 $n=630$ + Gemini & Grok $n=240$） | DeepSeek `del_topIC` 呈剂量坍缩 $28.3\\% \\to 22.6\\% \\to 14.3\\%$（$p=0.0259$），Grok-4.7 坍缩 $45.0\\% \\to 30.0\\% \\to 20.0\\%$；真基因在 **2.1% CoT 深度** 激活，但 **23.3%** 假阴性自我剪除 | 双模型合并 $\\beta_1 = -0.573$（$p = 0.2191, q_{\\text{BH}} = 0.2629$）；`CoT-SRAD` McNemar $p = 7.07 \\times 10^{-6}$（合并）与 $p = 9.43 \\times 10^{-7}$（DeepSeek） | **模块 4（`CoT-SRAD`）：** LODO 吸引子去混杂（`CHD7`, `KMT2D`, `FOXG1`, `POLG`, `FBXL4`）与思维链流恢复 | 零额外调用挽救 **+36 个致病基因发现**（合并 $26.35\\% \\to 32.06\\%$）；将 DeepSeek 召回率相对提升 **+57.1%**（$20.66\\% \\to 32.47\\%$，净增 +32 次调用） |"
    s = replace_exact(s, old_zh_t2_2c, new_zh_t2_2c, "ZH Table 2 Dim 2c")

    old_zh_t2_3 = "| **维度 3：位置公平性**（诊断与纠偏核心） | 第一轮锦标赛（3,594 次调用）& 第二轮锦标赛（1,601 对 GLM + 180 对盲法 Gemini） | T1 A 槽位胜率 **71.29%**（$p = 4.37 \\times 10^{-148}$；**前十分之一阶段 88.4% 注意力聚焦 A 槽位**），导致分桶偏斜 `78:26:16`（$\\chi^2 = 55.40$）；T2 翻转率 **43.04%**（GLM）、**17.78%**（Gemini-Pro）与 **26.67%**（Gemini-Flash） | T1 分桶 $\\chi^2 p = 9.33 \\times 10^{-13}$；T2 首因二项检验 $p = 4.63 \\times 10^{-168}$ | **模块 1：** 顺位校正 BTL（剥离 $\\hat{\\gamma}$ 截距）+ T2 NLI 不一致平局中性化 | 分桶偏斜失真削减 **72.8%**（`60:31:29`，$\\chi^2 = 15.05$）；第 3 分桶存活率 **+81.3%**；成功救回 `MERTK`, `TIMP3`, `ABCA1`, `CD59`, `C06`, `C10` |"
    new_zh_t2_3 = "| **维度 3：位置公平性**（诊断与纠偏核心） | 第一轮锦标赛（3,594 次调用）& 第二轮锦标赛（1,601 对 GLM + 360 对盲法 Gemini & Grok） | T1 A 槽位胜率 **71.29%**（$p = 4.37 \\times 10^{-148}$；**前十分之一阶段 88.4% 注意力聚焦 A 槽位**），导致分桶偏斜 `78:26:16`（$\\chi^2 = 55.40$）；T2 翻转率 **43.04%**（GLM）、**17.8%/26.7%**（Gemini）与 **13.3%/8.9%**（Grok-4.7/Fast） | T1 分桶 $\\chi^2 p = 9.33 \\times 10^{-13}$；T2 首因二项检验 $p = 4.63 \\times 10^{-168}$ | **模块 1：** 顺位校正 BTL（剥离 $\\hat{\\gamma}$ 截距）+ T2 NLI 不一致平局中性化 | 分桶偏斜失真削减 **72.8%**（`60:31:29`，$\\chi^2 = 15.05$）；第 3 分桶存活率 **+81.3%**；成功救回 `MERTK`, `TIMP3`, `ABCA1`, `CD59`, `C06`, `C10`, `C02` |"
    s = replace_exact(s, old_zh_t2_3, new_zh_t2_3, "ZH Table 2 Dim 3")

    old_zh_t2_6 = "| **维度 6：自我认知校准**（验证性成员 6） | 主运行第 1 步（$n=360$）与汇总（$n=480$）；实验 C-v4（$n=630$ GLM/DS + $n=120$ Gemini） | 第 1 步校准斜率 $\\hat{\\beta}_{\\text{cal}} = 0.655 \\neq 1.0$；主运行 $\\text{ECE} = 0.222$；实验 C 未校准 $\\text{ECE} = 0.351$ (GLM)、$0.244$ (DS)、$0.459$ (Gemini-Pro) 与 $0.542$ (Gemini-Flash) | 针对斜率 1.0 的 Wald 检验：$p = 0.02004$，**$q_{\\text{BH}} = 0.04009^*$** | **模块 2：** 留一运行交叉验证（LORO）Platt 缩放重校准 | 主运行 $\\text{ECE}$ 降低 **87.8%**（$0.222 \\to 0.027$，精确值 87.64%）；实验 C-v4 $\\text{ECE}$ 降低 **82.8%–89.5%**（GLM/DS）与 **74.1%–86.2%**（Gemini Pro/Flash） |"
    new_zh_t2_6 = "| **维度 6：自我认知校准**（验证性成员 6） | 主运行第 1 步（$n=360$）与汇总（$n=480$）；实验 C-v4（$n=630$ GLM/DS + $n=240$ Gemini & Grok） | 第 1 步校准斜率 $\\hat{\\beta}_{\\text{cal}} = 0.655 \\neq 1.0$；主运行 $\\text{ECE} = 0.222$；实验 C 未校准 $\\text{ECE} = 0.351$ (GLM)、$0.244$ (DS)、$0.459/0.542$ (Gemini) 与 $0.229/0.165$ (Grok) | 针对斜率 1.0 的 Wald 检验：$p = 0.02004$，**$q_{\\text{BH}} = 0.04009^*$** | **模块 2：** 留一运行交叉验证（LORO）Platt 缩放重校准 | 主运行 $\\text{ECE}$ 降低 **87.8%**（$0.222 \\to 0.027$，精确值 87.64%）；实验 C-v4 $\\text{ECE}$ 降低 **82.8%–89.5%**（GLM/DS）、**74.1%–86.2%**（Gemini）与 **50.7%–54.8%**（Grok） |"
    s = replace_exact(s, old_zh_t2_6, new_zh_t2_6, "ZH Table 2 Dim 6")

    write_lf(path, s)
    shutil.copy2(path, os.path.join(DESKTOP, "STAR-Audit_手稿全文中文版_审核稿.md"))
    print("Updated:", path, "and Desktop copy")


if __name__ == "__main__":
    update_nature_manuscript()
    update_supplementary()
    update_cover_letter()
    update_zh_manuscript()
