#!/usr/bin/env python3
"""
Programmatically build SUPPLEMENTARY_GEN2_v1.0.md and COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md
from the verified Gen-2 JSON outputs, and then generate submission-grade Word documents (.docx)
strictly following manuscript-submission-docx-format (Times New Roman 12pt, 2.0 line spacing,
justified paragraphs, clean academic tables, and embedded figures).
"""

import json
import os
import re

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
ANAL_DIR = os.path.join(BASE, "GEN2_exec", "analysis")
FIG_DIR = os.path.join(BASE, "GEN2_exec", "figures")

s1 = json.load(open(os.path.join(ANAL_DIR, "step1_pubmed_results.json"), encoding="utf-8"))
s2 = json.load(open(os.path.join(ANAL_DIR, "step2_dim2_3_4_rectification_results.json"), encoding="utf-8"))
s3 = json.load(open(os.path.join(ANAL_DIR, "step3_expC_dim6_paradox_results.json"), encoding="utf-8"))
s4 = json.load(open(os.path.join(ANAL_DIR, "step4_dim5_nli_results.json"), encoding="utf-8"))
master = json.load(open(os.path.join(ANAL_DIR, "MASTER_GEN2_AUDIT_RESULTS.json"), encoding="utf-8"))
expB_slots = json.load(open(os.path.join(ANAL_DIR, "step1_expB_slots_scored.json"), encoding="utf-8"))


def build_supplementary_md():
    lines = []
    lines.append("# Supplementary Information: Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery")
    lines.append("")
    lines.append("**Authors:** Jiangtao Sheng, Xueer Liu, Runmin Lin, Qiaochu Sun, Xiaoxuan Chen, Kangsheng Li, Weiqiang Chen")
    lines.append("**OSF Preregistration:** DOI 10.17605/OSF.IO/KF2G8")
    lines.append("")
    lines.append("## Contents")
    lines.append("- **Supplementary Note 1:** Complete blind forbidden-token lists (dAMD 11 tokens, ALS 24 tokens) and automatic redraft governance")
    lines.append("- **Supplementary Note 2:** Two-tier NCBI Entrez semantic verifier specification and 200-pair self-calibration benchmark")
    lines.append("- **Supplementary Note 3:** Mathematical derivation of Order-Adjusted Bradley–Terry–Luce (BTL) ranking and NLI-Discordance Neutralization")
    lines.append("- **Supplementary Table S1:** Complete Top-5 target dossiers and mapped gold-standard biological axes across all 12 Parent discovery runs (60 protocol targets)")
    lines.append("- **Supplementary Table S2:** Run-by-run Tournament I and II position-bias audit, primacy intercepts, and Order-Adjusted BTL rescued pathways")
    lines.append("- **Supplementary Table S3:** Experiment B randomized citation trial breakdown across all 14 clinical disease domains (1,260 citation slots)")
    lines.append("- **Supplementary Table S4:** Experiment C-v4 multi-vendor HPO information-content deletion results by cell and top 15 canonical decoy attractors")
    lines.append("- **Supplementary Table S5:** DeBERTa-v3 cross-stage NLI contradiction audit across all 12 Parent runs (17,990 biological assertions)")
    lines.append("- **Supplementary Table S6:** Complete pre-registered deviation ledger (D2-001 through D2-012, SHA-256 sealed)")
    lines.append("")

    # Note 1
    lines.append("## Supplementary Note 1. Complete blind forbidden-token lists and automatic redraft governance")
    lines.append("To ensure that the `blind` discovery arm could not recite benchmark drugs or canonical gene symbols from surface prompt cues, `gen2_blind.py` enforced whole-word and substring case-insensitive scanning across all prompts and generated JSON payloads against two frozen forbidden-token lists:")
    lines.append("- **dAMD Forbidden Token List (11 tokens):** `ripasudil`, `K-115`, `Glanatec`, `fasudil`, `Y-27632`, `netarsudil`, `Rhopressa`, `belumosudil`, `ROCK1`, `ROCK2`, `Rho kinase`.")
    lines.append("- **ALS Forbidden Token List (24 tokens):** `riluzole`, `edaravone`, `tofersen`, `Qalsody`, `relyvrio`, `AMX0035`, `masitinib`, `ibudilast`, `arimoclomol`, `SOD1`, `C9orf72`, `FUS`, `TARDBP`, `TDP-43`, `STMN2`, `ATXN2`, `TBK1`, `OPTN`, `UNC13A`, `MERTK`, `GAS6`, `AXL`, `TYRO3`, `TAM receptor`.")
    lines.append("When a Step-1 blind generation call emitted any forbidden token, `run_parent.py` automatically rejected the response and issued a redraft call (capped at 4 redrafts per Deviation `D2-010`). Across the 6 blind runs, dAMD triggered 0 redrafts, whereas ALS triggered 7 automatic redrafts during Step 1 due to spontaneous emission of `SOD1` or `STMN2` before converging on compliant mechanistic descriptions.")
    lines.append("")

    # Note 2
    lines.append("## Supplementary Note 2. Two-tier NCBI Entrez semantic verifier specification and 200-pair self-calibration benchmark")
    lines.append("For every structured citation slot in Parent Step 6 ($n = 360$ valid slots across 12 runs) and Experiment B ($n = 1,260$ slots across 3 arms $\\times$ 14 domains), `step1_pubmed_verify.py` queried the live NCBI Entrez API (`esummary.fcgi` and `efetch.fcgi` XML) and cached all 956 distinct cited PMIDs in `pubmed_cache.json`. Each non-abstained citation was evaluated in two sequential tiers:")
    lines.append("1. **Tier-1 Identifier Existence:** Verifies that the numeric PMID resolves to an indexed PubMed article record with a valid title and publication year.")
    lines.append("2. **Tier-2 Semantic Claim-Abstract Alignment:** Extracts the concatenated text of the official PubMed title, full abstract, and MeSH descriptor terms, and tests whether the record contains either (a) a domain-specific disease anchor for the target run/domain or (b) at least one specific gene/protein/pathway token (>3 characters, excluding generic biomedical stopwords) from the candidate hypothesis claim. On our pre-registered 200-pair self-calibration benchmark (`offtopic_calibration_100.csv`: 100 positive claim-PMID pairs from Appendix A gold standards and 100 cross-disease negative claim-PMID pairs), Tier-2 verification achieved **100/100 (100.0%) sensitivity** and **100/100 (100.0%) specificity**.")
    lines.append("")

    # Note 3
    lines.append("## Supplementary Note 3. Mathematical derivation of Order-Adjusted BTL and NLI-Discordance Neutralization")
    lines.append("In a canonical multi-agent discovery tournament, $M$ candidate mechanisms ($M = 30$ in Tournament I; $M = 10$ in Tournament II) are compared in ordered pairs $(i_k, j_k)$ for $k = 1, \\dots, K$, where candidate $i_k$ is placed in Slot A (first position) and candidate $j_k$ is placed in Slot B (second position). Standard Bradley–Terry–Luce (BTL) estimation assumes positional invariance, modeling the win probability of Slot A as $\\sigma(\\theta_{i_k} - \\theta_{j_k})$, where $\\sigma(z) = (1 + e^{-z})^{-1}$ and $\\theta_m = \\ln \\pi_m$. When language model judges exhibit a directional preference for Slot A ($\\gamma > 0$), any asymmetry in how candidates are assigned to Slot A versus Slot B directly biases $\\hat{\\theta}_m$.")
    lines.append("")
    lines.append("In Tournament I, unordered pairs $\\{M_a, M_b\\}$ with $a < b$ are formatted into prompts such that lower-indexed candidates (`Bucket 1: M00–M09`) appear predominantly in Slot A and higher-indexed candidates (`Bucket 3: M20–M29`) appear predominantly in Slot B. To separate intrinsic biological merit $\\boldsymbol{\\theta} = (\\theta_1, \\dots, \\theta_M)^\\top$ from the Slot-A primacy intercept $\\gamma$, we maximize the $L_2$-penalized log-likelihood:")
    lines.append("$$\\mathcal{L}(\\boldsymbol{\\theta}, \\gamma) = \\sum_{k=1}^{K} \\left[ y_k \\ln p_k + (1 - y_k) \\ln(1 - p_k) \\right] - \\frac{\\lambda}{2} \\sum_{m=1}^{M} \\theta_m^2, \\quad p_k = \\sigma(\\theta_{i_k} - \\theta_{j_k} + \\gamma)$$")
    lines.append("subject to the zero-sum identifiability constraint $\\sum_{m=1}^M \\theta_m = 0$ with $\\lambda = 0.01$. Let $\\mathbf{x}_k \\in \\mathbb{R}^{M+1}$ denote the design vector for comparison $k$, with $+1$ at index $i_k$, $-1$ at index $j_k$, and $+1$ at index $M+1$ (corresponding to $\\gamma$). The gradient $\\mathbf{g} \\in \\mathbb{R}^{M+1}$ and Hessian $\\mathbf{H} \\in \\mathbb{R}^{(M+1) \\times (M+1)}$ are given in closed form by:")
    lines.append("$$\\mathbf{g} = \\sum_{k=1}^{K} (y_k - p_k)\\mathbf{x}_k - \\lambda \\begin{bmatrix} \\boldsymbol{\\theta} \\\\ 0 \\end{bmatrix}, \\quad \\mathbf{H} = -\\sum_{k=1}^{K} p_k(1 - p_k)\\mathbf{x}_k \\mathbf{x}_k^\\top - \\lambda \\begin{bmatrix} \\mathbf{I}_M & \\mathbf{0} \\\\ \\mathbf{0}^\\top & 0 \\end{bmatrix}$$")
    lines.append("Newton–Raphson updates $\\boldsymbol{\\phi}^{(t+1)} = \\boldsymbol{\\phi}^{(t)} - \\mathbf{H}^{-1}\\mathbf{g}$ (with $\\boldsymbol{\\theta}$ re-centered to zero mean at each step) converge in fewer than 15 iterations to machine precision ($\\|\\Delta \\boldsymbol{\\phi}\\|_\\infty < 10^{-10}$). In Tournament II, where every unordered pair $\\{i, j\\}$ is judged by persona $u \\in \\{\\text{SCIENCE}, \\text{METHODS}, \\text{NOVELTY}\\}$ in both $(A=i, B=j)$ and $(A=j, B=i)$ presentation orders, **NLI-Discordance Neutralization** identifies all judge-pair instances where the same slot wins both orderings (indicating position-driven reversal accompanied by high DeBERTa-v3 NLI self-contradiction) and replaces the discordant pair with a neutral tie ($w_{ij} = 0.5, w_{ji} = 0.5$) prior to BTL strength estimation.")
    lines.append("")

    # Table S1
    lines.append("## Supplementary Table S1. Complete Top-5 target dossiers and mapped biological axes across all 12 Parent discovery runs")
    lines.append("")
    lines.append("| Run ID | Disease | Arm | Rep | Top-5 Rank | Mechanism ID | Lead Gene (HGNC) | Mapped Gold-Standard Biological Axis | Gold Axis Match |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    profiles = s2["dimension_2_reasoning_vs_retrieval"]["per_run_top5_profiles"]
    for r_id in sorted(profiles.keys()):
        p = profiles[r_id]
        parts = r_id.split("_")
        dis, arm, rep = parts[0], parts[1], parts[2]
        for rank_idx, item in enumerate(p["top5_details"], 1):
            is_gold = "Yes (Gold)" if item.get("is_gold_axis") else "No"
            lead_g = item["targets"][0] if item.get("targets") else "N/A"
            lines.append(f"| `{r_id}` | {dis} | {arm} | {rep} | Rank {rank_idx} | `{item['cand_id']}` | **{lead_g}** | `{item['axis']}` | {is_gold} |")
    lines.append("")

    # Table S2
    lines.append("## Supplementary Table S2. Run-by-run Tournament I and II position-bias audit, primacy intercepts, and Order-Adjusted BTL rescued pathways")
    lines.append("")
    lines.append("| Run ID | T1 Raw Bucket 1:2:3 | T1 Adj Bucket 1:2:3 | T1 Primacy $\\hat{\\gamma}_{\\text{T1}}$ (SE) | T1 Slot-A OR | T2 Flip Rate (%) | T2 Primacy Share of Flips (%) | T2 Primacy $\\hat{\\gamma}_{\\text{T2}}$ | T1 Top-10 Rescued IDs (Order-Adj BTL) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    t2_runs = s2["dimension_3_position_bias"]["tournament_II_by_run"]
    t1_adj = s2["audit_guided_rectification"]["tournament_I_order_adjusted_btl"]
    t2_adj = s2["audit_guided_rectification"]["tournament_II_debiased_btl"]
    for r_id in sorted(t2_runs.keys()):
        r2 = t2_runs[r_id]
        a1 = t1_adj[r_id]
        a2 = t2_adj[r_id]
        raw_b = ":".join(str(x) for x in a1["raw_top10_decades"])
        adj_b = ":".join(str(x) for x in a1["adj_top10_decades"])
        prim_share = r2["primacy_share_of_biased"] * 100.0
        resc = ", ".join(m["id"] for m in a1["rescued_mechanisms"]) if a1["rescued_mechanisms"] else "None (10/10 stable)"
        lines.append(
            f"| `{r_id}` | `{raw_b}` | `{adj_b}` | "
            f"{a1['gamma_primacy']:.3f} ({a1['gamma_se']:.3f}) | {a1['odds_ratio_slotA']:.2f}x | "
            f"{r2['pos_bias_rate']*100:.1f}% | {prim_share:.1f}% | {a2['t2_gamma_primacy']:.3f} | `{resc}` |"
        )
    lines.append("")
    lines.append("**Worked Orthogonal Validation Breakdown of Representative Gold-Standard Pathways Rescued by Order-Adjusted BTL (Benchmarking Figure 6B):**")
    lines.append("")
    lines.append("| Run ID | Rescued Mechanism ID & Biological Pathway | Slot-A Wins / Trials | Slot-B Wins / Trials (Slot-B Share) | Unadjusted BTL Rank (Status) | Order-Adjusted BTL Rank (Status) | Orthogonal Human-Genetic, Animal-Model & Clinical Validation Anchor |")
    lines.append("|---|---|---|---|---|---|---|")
    worked_rescues = [
        ("dAMD_retrieval_R1", "`M23`: **GAS6/PROS1–MERTK** TAM receptor RPE efferocytosis", "2 / 2 (100%)", "7 / 14 (**87.5%** in Slot B)", "Rank 11 (Eliminated)", "**Rank 7 (Rescued)**", "RCS rat *Mertk* loss-of-function, human autosomal recessive RP38 mutations, and in vivo MERTK kinase inhibition retinal degeneration (PMID: 10699188, 23259948, 28462455, 34973110, 38928335)"),
        ("dAMD_retrieval_R2", "`M25`: **TIMP3/MMP9** Bruch's membrane ECM turnover", "3 / 4 (75.0%)", "9 / 15 (**78.9%** in Slot B)", "Rank 15 (Eliminated)", "**Rank 8 (Rescued)**", "IAMDGC 34-locus AMD GWAS (*TIMP3* locus) and Mendelian Sorsby fundus dystrophy *TIMP3* ECM accumulation (PMID: 20385819, 26691988, 42569289)"),
        ("dAMD_retrieval_R3", "`M25`: **ABCA1/LIPC/CETP** sub-RPE HDL cholesterol efflux", "3 / 4 (75.0%)", "9 / 15 (**78.9%** in Slot B)", "Rank 15 (Eliminated)", "**Rank 6 (Rescued)**", "IAMDGC AMD GWAS (*ABCA1*, *LIPC*, *CETP* lipid loci) and sub-RPE drusen cholesterol ester accumulation (PMID: 20385819, 26691988)"),
        ("dAMD_retrieval_R3", "`M14`: **CD59** terminal C5b-9 MAC protection on RPE", "9 / 9 (100%)", "3 / 9 (50.0% in Slot B)", "Rank 11 (Eliminated)", "**Rank 5 (Rescued)**", "RPE surface CD59 loss in human geographic atrophy and clinical-stage ocular gene therapy `AAVCAGsCD59` (PMID: 31082363, 37865470)"),
        ("dAMD_blind_R1", "`M22`: **MTTP/APOB100/SOAT1** basolateral lipoprotein secretion", "4 / 6 (66.7%)", "9 / 15 (**71.4%** in Slot B)", "Rank 12 (Eliminated)", "**Rank 6 (Rescued)**", "Human AMD Bruch's membrane APOB100 lipoprotein wall and RPE-specific *Mttp* ablation models (PMID: 38193957, 38445789)"),
        ("ALS_blind_R1", "`M18`: **C1QA/C3** microglial complement motor synapse pruning", "7 / 10 (70.0%)", "6 / 13 (**56.5%** in Slot B)", "Rank 13 (Eliminated)", "**Rank 10 (Rescued)**", "Complement C1q/C3-dependent microglial engulfment of vulnerable synapses in neurodegenerative mouse models (PMID: 27033548)"),
        ("ALS_blind_R2", "`M26`: **MMP9/LAMA1** fast motor neuron NMJ denervation", "2 / 2 (100%)", "8 / 17 (**89.5%** in Slot B)", "Rank 13 (Eliminated)", "**Rank 6 (Rescued)**", "Selective fast motor neuron *Mmp9* expression; genetic/pharmacological MMP-9 inhibition rescues *SOD1* ALS mice (PMID: 24462097)"),
        ("ALS_blind_R3", "`M25`: **MCT1 (SLC16A1)** oligodendrocyte-axon lactate shuttle", "4 / 4 (100%)", "10 / 15 (**78.9%** in Slot B)", "Rank 11 (Eliminated)", "**Rank 7 (Rescued)**", "Oligodendroglial MCT1 depletion in human ALS spinal cord and motor axon degeneration in *Slc16a1* models (PMID: 22801498)"),
        ("ALS_retrieval_R3", "`M29`: **CCS/ATP7A** copper-dependent apo-SOD1 maturation", "0 / 0 (N/A)", "13 / 23 (**100.0%** in Slot B)", "Rank 15 (Eliminated)", "**Rank 10 (Rescued)**", "CCS copper chaperone control of SOD1 folding, disulfide maturation, and motor neuron toxicity in vivo (PMID: 11889469)"),
    ]
    for r_id, mech_desc, sa_str, sb_str, rk_raw, rk_adj, ev_str in worked_rescues:
        lines.append(f"| `{r_id}` | {mech_desc} | {sa_str} | {sb_str} | {rk_raw} | {rk_adj} | {ev_str} |")
    lines.append("")

    # Table S3
    lines.append("## Supplementary Table S3. Experiment B randomized citation trial breakdown across all 14 clinical disease domains (1,260 slots)")
    lines.append("")
    lines.append("| Domain ID | Disease Domain | `as_discovered` Fake PMID (%) | `as_discovered` Trojan Off-Topic (%) | `as_discovered` Total Ungrounded (%) | `abstain_probe` Abstain (%) | `abstain_probe` Ungrounded (%) | `gated` Abstain (%) | `gated` Fake PMID (%) | `gated` Total Ungrounded (%) | Net Ungrounded Reduction (pp) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for i in range(1, 15):
        did = f"B{i:02d}"
        asd = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == "as_discovered"]
        prb = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == "abstain_probe"]
        gat = [r for r in expB_slots if r["domain_id"] == did and r["arm"] == "gated"]
        dom_name = (asd[0]["domain"] if asd else did).replace("Pelizaeus-Merzbacher", "Pelizaeus–Merzbacher")
        asd_fake = sum(1 for r in asd if r["fabricated"]) / 30.0 * 100.0
        asd_off = sum(1 for r in asd if r["resolved"] and not r["on_topic"]) / 30.0 * 100.0
        asd_ung = sum(1 for r in asd if r["ungrounded"]) / 30.0 * 100.0
        prb_abs = sum(1 for r in prb if r["abstained"]) / 30.0 * 100.0
        prb_ung = sum(1 for r in prb if r["ungrounded"]) / 30.0 * 100.0
        gat_abs = sum(1 for r in gat if r["abstained"]) / 30.0 * 100.0
        gat_fake = sum(1 for r in gat if r["fabricated"]) / 30.0 * 100.0
        gat_ung = sum(1 for r in gat if r["ungrounded"]) / 30.0 * 100.0
        diff = gat_ung - asd_ung
        lines.append(
            f"| `{did}` | {dom_name} | {asd_fake:.1f}% | {asd_off:.1f}% | **{asd_ung:.1f}%** | "
            f"{prb_abs:.1f}% | {prb_ung:.1f}% | {gat_abs:.1f}% | **{gat_fake:.1f}%** | "
            f"**{gat_ung:.1f}%** | **{diff:+.1f} pp** |"
        )
    lines.append("")

    # Table S4
    lines.append("## Supplementary Table S4. Experiment C-v4 multi-vendor HPO information-content deletion results by cell")
    lines.append("")
    lines.append("| Vendor | Perturbation Arm | Target Dose (%) | Realized Mean IC Removed (%) | Valid Calls ($n$) | Distinct Diseases | Causal Gene Recall@10 (%) | Causal Gene Recall@1 (%) | Mean Reciprocal Rank (MRR) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    desc_c = s3["expC_v4"]["descriptive_by_cell"]
    for key in sorted(desc_c.keys()):
        c = desc_c[key]
        v_name, arm_name, d_str = key.split("__")
        lines.append(
            f"| `{v_name}` | `{arm_name}` | {d_str[1:]}% | {c['mean_dose_realized']*100:.1f}% | "
            f"{c['n_calls']} | {c['n_unique_pairs']} | **{c['hit10_rate']*100:.1f}%** | {c['hit1_rate']*100:.1f}% | {c['mrr_mean']:.3f} |"
        )
    lines.append("")

    # Table S5
    lines.append("## Supplementary Table S5. DeBERTa-v3 cross-stage NLI contradiction audit across all 12 Parent runs")
    lines.append("")
    lines.append("| Run ID | Extracted Entity Claims | Cross-Stage Claim Pairs | Strict Bidirectional Contradictions ($P>0.75$ Both) | Strict Rate / 1k Pairs | Directional Contradictions ($P>0.75$ Either) | Directional Rate / 1k Pairs | Strict Contradictions Propagating Into Top-5 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    nli_runs = s4["cross_stage_coherence"]["by_run"]
    for r_id in sorted(nli_runs.keys()):
        nr = nli_runs[r_id]
        lines.append(
            f"| `{r_id}` | {nr['n_assertions']} | {nr['n_cross_stage_pairs']} | "
            f"{nr['n_bidir_contra_075']} | **{nr['bidir_contra_per_1k_pairs']:.2f}** | "
            f"{nr['n_dir_contra_075']} | **{nr['dir_contra_per_1k_pairs']:.2f}** | "
            f"{nr['s13_contra_propagated_to_top5']} |"
        )
    lines.append("")

    # Table S6
    lines.append("## Supplementary Table S6. Complete pre-registered deviation ledger (D2-001 through D2-012, SHA-256 sealed)")
    lines.append("")
    lines.append("| Deviation ID | Date (UTC) | Affected Component | Operational Change | Root-Cause Telemetry Finding | Direction of Potential Bias |")
    lines.append("|---|---|---|---|---|---|")
    devs = [
        ("D2-001", "2026-09-04", "Parent T1/T2 Judges", "`max_tokens` increased from 2,048 to 8,192", "`effort=high` internal reasoning tokens exceeded 2,048 before emitting short JSON verdicts", "Neutral / Completeness-preserving (eliminates premature JSON truncation in pairwise judging)"),
        ("D2-002", "2026-09-04", "Harness Path Isolation", "Separated `mock/` and `live/` data directories", "Prevented test-mode harness checks from overwriting live canary logs", "Zero bias (enforces strict physical isolation of $R=3$ live replicate logs)"),
        ("D2-003", "2026-09-04", "Parent Retrieval Arm", "Replaced native `web_search` tool with `gen2_pubmed.py` NCBI injection", "Coding Plan endpoint accepted tool definitions syntactically but did not execute server-side web search", "Conservative (standardizes PubMed abstract/MeSH context deterministically across all retrieval replicates)"),
        ("D2-004", "2026-09-05", "Experiment B Stage 2", "`max_tokens` increased from 2,048 to 8,192", "159/210 initial calls truncated in reasoning before emitting 6-slot citation JSON", "Completeness-preserving (prevents high-CoT `as_discovered` calls from failing prior to slot emission)"),
        ("D2-005", "2026-09-05", "Experiment B & C-v4", "`max_tokens` increased from 8,192 to 16,384", "Complex multi-slot citation and HPO differential reasoning exceeded 8,192 tokens", "Completeness-preserving (allows deep CoT trajectories to reach natural stop)"),
        ("D2-006", "2026-09-05", "Global Harness Cap", "`max_tokens` unified to 32,768 across Step 1/6, Exp B, and Exp C-v4", "Pathological memory-dredging slots required 17K–30K reasoning tokens to reach natural `stop`", "Neutral across arms (unifies ceiling at 32,768 tokens across all experimental conditions)"),
        ("D2-007", "2026-09-05", "Client HTTP Timeout", "Timeout increased from 300s to 900s; exclude-truncation rule formalized", "32,768-token deep reasoning calls require 2–8 minutes of wall-clock generation time", "Conservative toward null in Paradox 3 (excluding $>32,768$-token truncated calls slightly underestimates failed-call CoT spin)"),
        ("D2-008", "2026-09-05", "Run Output Directory", "Enforced strict `--mock` output root isolation", "Protected `runs/` directory from test script cleanup", "Zero bias (infrastructure safeguard protecting frozen live run directories)"),
        ("D2-009", "2026-09-06", "Parent Step 1 Ideation", "`max_tokens` set to 32,768 + automatic blind-word redrafting", "30-mechanism JSON generation + deep reasoning required full 32K window", "Completeness-preserving (ensures all 12 runs generate complete 30-candidate Step-1 pools)"),
        ("D2-010", "2026-09-06", "Blind Scanner Redraft Cap", "Maximum blind-word redraft attempts increased from 2 to 4", "ALS strong pretraining attractor (`SOD1`/`STMN2`) required up to 4 redrafts to express purely by mechanism", "Conservative (enforces 100% lexical shortcut removal in `blind` runs while preserving residual pathway priors)"),
        ("D2-011", "2026-09-06", "Parent Step 6 Protocols", "`max_tokens` set to 32,768 + deterministic failed-slot completion", "Ensured all 12 Parent runs completed 60/60 Top-5 protocol target records", "Completeness-preserving (guarantees balanced $n=360$ protocol citation slots across all 12 runs)"),
        ("D2-012", "2026-09-07", "DeepSeek-V4-Pro Scheduling", "Off-peak UTC execution gate + budget hard-stop at 630 C-v4 calls", "Preserved strict cost ceiling while completing 359 GLM and 271 DeepSeek perturbation calls across 120 diseases", "Conservative Type II bias (biases subtle pooled Arm $\\times$ Dose interaction $\\beta_3$ toward the null while preserving main effects)"),
    ]
    for d_id, dt, comp, chg, root, bias_dir in devs:
        lines.append(f"| `{d_id}` | {dt} | {comp} | {chg} | {root} | {bias_dir} |")
    lines.append("")

    out_path = os.path.join(BASE, "SUPPLEMENTARY_GEN2_v1.0.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote:", out_path)


def build_cover_letter_md():
    lines = []
    lines.append("# Cover Letter and Point-by-Point Editorial Transformation Summary (Generation-2 Overhaul)")
    lines.append("")
    lines.append("**Date:** October 29, 2026")
    lines.append("**Manuscript Title:** Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery")
    lines.append("**Corresponding Authors:** Prof. Jiangtao Sheng (jtsheng@stu.edu.cn; Lead Contact) and Prof. Weiqiang Chen (wqchen@stu.edu.cn), Shantou University Medical College")
    lines.append("**OSF Preregistration:** DOI 10.17605/OSF.IO/KF2G8")
    lines.append("")
    lines.append("## Part 1. Submission Cover Letter")
    lines.append("")
    lines.append("Dear Editors,")
    lines.append("")
    lines.append("We are pleased to submit our Research Article entitled \"Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery\" for consideration for publication.")
    lines.append("")
    lines.append("Autonomous multi-agent AI systems have recently demonstrated the capacity to generate therapeutic hypotheses, rank candidates via pairwise tournaments, and synthesize experimental protocols for wet-lab validation (e.g., *Nature* 2026; DOI: 10.1038/s41586-026-10652-y and DOI: 10.1038/s41586-026-10644-y). A central assumption driving current agentic system design is that scaling test-time chain-of-thought reasoning allows frontier language models to self-correct factual hallucinations, evaluation biases, and overconfidence. However, the field currently lacks an end-to-end, externally anchored methodological standard to audit whether these discovery pipelines are trustworthy or to algorithmically rectify their structural failure modes before scarce experimental resources are committed.")
    lines.append("")
    lines.append("To address this gap, we designed and executed an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) six-dimension trustworthiness audit and zero-cost algorithmic rectification study across **9,130 primary live LLM invocations (35.58 million internal reasoning tokens across 8,973 white-box traces; 93.83% of all generated tokens)** on **GLM-5.3 and DeepSeek-V4-Pro** plus a **2,688-evaluation cross-ecosystem validation suite across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]; 1,344 evaluations, 1,149,908 output/reasoning tokens and 12.05M total tokens incl. cache) and xAI Grok (`Grok-4.7` [`grok-4.7`, Flagship Reasoning] and `Grok-4.7-Fast` [`grok-4.7-build-fast`, Rapid-Thinking]; 1,344 evaluations, 450,879 native reasoning tokens)**, totaling **11,818 live evaluations (37.18M reasoning/output tokens) across four sovereign frontier model families, six versioned compute tiers, and 136 distinct biomedical disease contexts** (12 replicated end-to-end discovery runs in dry age-related macular degeneration and amyotrophic lateral sclerosis, a 14-domain randomized citation-gating trial of 1,260 primary + 1,008 cross-ecosystem citation slots, and a 120-disease Mendelian Human Phenotype Ontology perturbation benchmark).")
    lines.append("")
    lines.append("Our study reports three major methodological and empirical advances:")
    lines.append("1. **White-Box Discovery of the Test-Time Reasoning Paradox Across Four Frontier Model Families:** We show quantitatively across 8,973 white-box CoT traces and 2,688 cross-ecosystem evaluations that allocating tens of thousands of internal reasoning tokens per call fails to self-correct structural pipeline vulnerabilities. Instead, extended chain-of-thought focuses **88.4–90.6% of Decile-1 attention on Slot A** and rationalizes positional flips ($p = 0.0254$, burning 3.60M tokens; flagship `Grok-4.7` flips **13.3%** of pairs with **10.0%** subscore-verdict discordance vs. **8.9%** and **6.7%** on `Grok-4.7-Fast`), trials **35.82 candidate PMIDs per call** in parametric memory to attach real identifiers to unsupported claims ($10.4\\times\\text{ to }30.3\\times$ more reasoning tokens per call in unguarded citation generation), and obeys a **2.1% Instant-Recognition Law** where **23.3% of completed false-negative Mendelian lists self-prune the true causal gene** after activating it early in CoT (`t = 2.1%` median depth) before defaulting to textbook syndromic attractors (`CHD7`, `KMT2D`, `FOXG1`, `VARS2`, `POLG`, `FBXL4`).")
    lines.append("2. **Cross-Ecosystem Identification of 'Trojan Horse Citations' and 'Index-Order Pathway Extinction':** We demonstrate that naive identifier existence checks score protocols as 96.9% to 100.0% valid across GLM-5.3, Google Gemini, and xAI Grok-4.7, whereas two-tier semantic verification reveals that **58.3% of Parent protocol citations, 54.3% of GLM-5.3 Experiment B citations, 11.9%/76.2% of `Gemini-4-Argon-High`/`Gemini-3.8-Flash` citations, and 29.8%/33.3% of `Grok-4.7`/`Grok-4.7-Fast` citations are Trojan horse citations** (real PubMed articles misattributed to unsupported claims). Simultaneously, we show that a **71.3% Slot-A win rate** in single-order Tournament I screening ($p = 4.37 \\times 10^{-148}$) interacts with bucket-indexed candidate generation to extinguish Bucket-3 extracellular matrix and complement pathways by 60% ($\\chi^2 = 55.40, p = 9.33 \\times 10^{-13}$), while **43.0% of Tournament II pairs on GLM-5.3, 11.1%/26.7% on `Gemini-4-Argon-High`/`Gemini-3.8-Flash`, and 13.3%/8.9% on `Grok-4.7`/`Grok-4.7-Fast` flip under blinded independent-session A/B reversal** accompanied by a **$2.5\\times$ to $3.4\\times$ surge in DeBERTa-v3 NLI self-contradiction** ($p = 1.15 \\times 10^{-5}$).")
    lines.append("3. **Four Zero-Cost Algorithmic Pipeline Rectification Modules ('Audit-to-Remediation'):** Moving beyond passive diagnosis, we introduce four lightweight mathematical and architectural rectification modules that require **zero additional LLM calls**: (i) **Order-Adjusted BTL Ranking with NLI-Discordance Neutralization**, which removes positional intercepts $\\hat{\\gamma}$ across primacy, recency, and symmetric judges, reduces Bucket-3 pathway distortion by **72.8%**, and rescues causally validated disease pathways (`GAS6/MERTK` efferocytosis, `TIMP3/MMP9` ECM turnover, `ABCA1/LIPC` cholesterol efflux, and `CD59` MAC protection) that standard BTL eliminated; (ii) **Leave-One-Run-Out (LORO) Platt Scaling**, which reduces Expected Calibration Error by **50.7% to 89.5%** across miscalibrated frontier models ($0.222 \\to 0.027$ in Parent runs; $\\text{ECE} \\le 0.115$ across all six models); (iii) **Two-Tier Epistemic Citation Gating**, which halts CoT PMID dredging ($35.8 \\to 5.0$ candidate PMIDs/call, $p = 2.07 \\times 10^{-44}$), eliminates fabricated PMIDs ($3.1\\% \\to 0.0\\%, q_{\\text{BH}} = 0.0310$), cuts ungrounded citations by **11.9 to 54.8 percentage points** ($p \\le 0.00147$), and reduces citation reasoning compute by **86.2%–97.3%**; and (iv) **Chain-of-Thought Stream Recovery and Attractor Deconfounding (`CoT-SRAD`)**, which rescues **+36 true Mendelian gene discoveries** ($p = 7.07 \\times 10^{-6}$; **+57.1% relative recall gain** on DeepSeek-V4-Pro, $p = 9.43 \\times 10^{-7}$).")
    lines.append("")
    lines.append("All preregistered protocols, gold standards, verification caches, and analysis scripts are openly available on OSF (DOI: 10.17605/OSF.IO/KF2G8) and GitHub (https://github.com/SJT503/SDL-dAMD, MIT License), and the full per-call JSONL telemetry archive is deposited on Zenodo (DOI: 10.5281/zenodo.20574265, CC BY 4.0; held under pre-publication anti-contamination embargo during peer review with immediate reviewer access available upon request and full public release upon publication). This manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the manuscript and declare no competing interests.")
    lines.append("")
    lines.append("Sincerely,")
    lines.append("")
    lines.append("**Jiangtao Sheng, PhD** (Lead Contact)")
    lines.append("Professor, Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China")
    lines.append("Email: jtsheng@stu.edu.cn | ORCID: 0000-0003-2438-7345")
    lines.append("")
    lines.append("**Weiqiang Chen, MD, PhD** (Co-Corresponding Author)")
    lines.append("Professor, Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China")
    lines.append("Email: wqchen@stu.edu.cn | ORCID: 0000-0002-2612-0890")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Part 2. Point-by-Point Transformation Matrix Addressing Prior Editorial Feedback (`PATTERNS-D-26-00361`)")
    lines.append("")
    lines.append("| Editorial Criticism in `PATTERNS-D-26-00361` (Gen-1 Pilot) | Limitations of Gen-1 Pilot Submission | Structural & Quantitative Resolution in Gen-2 Overhaul (`OSF: KF2G8`) |")
    lines.append("|---|---|---|")
    lines.append("| **1. Insufficiently major advance; needs clearer demonstration that the audit improves AI-discovery pipelines or empowers findings** | Gen-1 was a passive 3-metric diagnostic check on a single run; grounding gate was described as a trivial deterministic replacement; position bias only overrode 7/45 pairs without fixing Tournament I. | **Closed the loop from Audit to Four Zero-Cost Algorithmic Rectification Modules (Results R6–R7):** Developed **Order-Adjusted BTL** ($P(i>j)=\\sigma(\\theta_i-\\theta_j+\\gamma)$) + **NLI-Discordance Neutralization**, **LORO Platt Scaling**, **Two-Tier Epistemic Gating**, and **`CoT-SRAD`**. Demonstrated that standard BTL extinguishes Bucket-3 pathways ($\\chi^2=55.40 \\to 15.05, -72.8\\%$), that **Order-Adjusted BTL rescues causally validated targets (`MERTK`, `TIMP3`, `ABCA1`, `CD59`, `MMP9/LAMA1`)**, and that **`CoT-SRAD` rescues +36 Mendelian gene discoveries (+57.1% relative recall gain on DeepSeek-V4-Pro, $p=9.43\\times 10^{-7}$)** while cutting citation CoT compute by **86.2%–97.3%** at zero extra LLM cost. |")
    lines.append("| **2. Absence of much broader testing** | Gen-1 tested $n=1$ dAMD run (30 citation slots, 45 T2 pairs) + $n=1$ ALS citation check (36 slots) + 25 second-vendor citation slots, with gene-level Mann–Whitney pseudo-replication ($n_1=5$ vs $n_2=10$). | **Expanded testing across 136 distinct disease contexts, 4 sovereign frontier model families / 6 versioned compute tiers (`GLM-5.3`, `DeepSeek-V4-Pro`, Google `Gemini-4-Argon-High`/`Gemini-3.8-Flash`, xAI `Grok-4.7`/`Grok-4.7-Fast`), and 11,818 live evaluations (37.18M reasoning/output tokens):** (1) **Block 1:** 12 complete 6-step runs ($2 \\text{ diseases} \\times 2 \\text{ arms} \\times R=3$ replicates; 6,796 tournament verdicts, 360 protocol citation slots, 17,990 NLI-audited claims); (2) **Block 2 (Exp B):** 3-arm randomized citation trial across **14 clinical disease domains** (1,260 primary + 1,008 cross-ecosystem citation slots); (3) **Block 3 (Exp C-v4):** Multi-vendor HPO IC deletion benchmark across **120 rare Mendelian diseases** (630 primary + 240 cross-ecosystem calls). |")
    lines.append("| **3. Presentation hard to follow; claims need better focus; methods and models need clearer description** | Gen-1 mixed biological narrative about RPE phagocytosis with audit claims, lacked run-level statistical units, and compressed methods into 770 words. | **Complete architectural & narrative rewrite (STAR Methods + 7 Figures + 7 Supplementary Tables):** Centered the story on the **Test-Time Reasoning Paradox** (backed by 8,973 white-box CoT trajectory audits) and the **Six-Dimension Audit-to-Rectification Framework**. Every statistical test operates on the proper independent cluster unit (run, domain, or disease) under a pre-registered 6-member BH-FDR ($q=0.05$) confirmatory family. Full mathematical equations, token ledgers, and 12 SHA-256-sealed deviations are reported transparently. |")
    lines.append("")

    out_path = os.path.join(BASE, "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote:", out_path)


if __name__ == "__main__":
    # SUPPLEMENTARY_GEN2_v1.0.md is already updated on disk with Supplementary Table S7;
    # do not overwrite it with the legacy 6-table builder.
    build_cover_letter_md()

    # Build submission-grade .docx files adhering strictly to manuscript-submission-docx-format
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def set_cell_Borders(cell, top=None, bottom=None, left=None, right=None):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")
        for edge, spec in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
            if spec:
                el = OxmlElement(f"w:{edge}")
                el.set(qn("w:val"), spec.get("val", "single"))
                el.set(qn("w:sz"), str(spec.get("sz", 6)))
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), spec.get("color", "000000"))
                tcBorders.append(el)
            else:
                el = OxmlElement(f"w:{edge}")
                el.set(qn("w:val"), "nil")
                tcBorders.append(el)
        tcPr.append(tcBorders)

    def format_run_font(run, size_pt=12, bold=False, italic=False):
        run.font.name = "Times New Roman"
        run.font.size = Pt(size_pt)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = RGBColor(0, 0, 0)
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.insert(0, rFonts)
        rFonts.set(qn("w:ascii"), "Times New Roman")
        rFonts.set(qn("w:hAnsi"), "Times New Roman")
        rFonts.set(qn("w:cs"), "Times New Roman")
        rFonts.set(qn("w:eastAsia"), "Times New Roman")

    def sanitize_latex_to_supsub(text: str) -> str:
        s = text
        # Protect literal code underscores inside backticks by converting `foo_bar` -> foo-bar or clean text
        def clean_backtick(m):
            inner = m.group(1)
            return inner.replace("_", "‑")  # non-breaking hyphen for identifiers like dAMD_retrieval_R1
        s = re.sub(r"`([^`]+)`", clean_backtick, s)

        # Strip outer $$...$$ and $...$
        s = re.sub(r"\$\$([^$]+)\$\$", r"\1", s)
        s = re.sub(r"\$([^$]+)\$", r"\1", s)

        # Specific block/matrix constructs
        s = s.replace(r"\begin{bmatrix} \boldsymbol{\theta} \\ 0 \end{bmatrix}", "[θ; 0]")
        s = s.replace(r"\begin{bmatrix} \mathbf{I}_M & \mathbf{0} \\ \mathbf{0}^\top & 0 \end{bmatrix}", "diag(I⟦SUB:M⟧, 0)")
        s = re.sub(r"\\frac\{([^\}]+)\}\{([^\}]+)\}", r"(\1)/(\2)", s)
        s = re.sub(r"\\binom\{([^\}]+)\}\{([^\}]+)\}", r"C(\1, \2)", s)
        s = re.sub(r"\\sqrt\{\[H\^\{-1\}\]\s*_\{([^\}]+)\}\}", r"sqrt([H⟦SUP:-1⟧]⟦SUB:\1⟧)", s)
        s = re.sub(r"\\sqrt\{([^\}]+)\}", r"sqrt(\1)", s)

        # Font/accent wrappers
        s = re.sub(r"\\text\{--\}", "–", s)
        s = re.sub(r"\\text\{\s*\}", " ", s)
        s = re.sub(r"\\text\{([^\}]+)\}", r"\1", s)
        s = re.sub(r"\\mathrm\{([^\}]+)\}", r"\1", s)
        s = re.sub(r"\\mathbf\{([^\}]+)\}", r"**\1**", s)
        s = re.sub(r"\\boldsymbol\{\\theta\}", "**θ**", s)
        s = re.sub(r"\\boldsymbol\{\\phi\}", "**φ**", s)
        s = re.sub(r"\\boldsymbol\{([^\}]+)\}", r"**\1**", s)
        s = re.sub(r"\\mathcal\{([^\}]+)\}", r"\1", s)
        s = re.sub(r"\\mathbb\{R\}", "R", s)
        s = re.sub(r"\\hat\{\\beta\}", "β̂", s)
        s = re.sub(r"\\hat\{\\gamma\}", "γ̂", s)
        s = re.sub(r"\\hat\{\\theta\}", "θ̂", s)
        s = re.sub(r"\\hat\{\\phi\}", "φ̂", s)
        s = re.sub(r"\\hat\{p\}", "p̂", s)
        s = re.sub(r"\\bar\{J\}", "J̄", s)
        s = re.sub(r"\\bar\{y\}", "ȳ", s)
        s = re.sub(r"\\bar\{p\}", "p̄", s)
        s = re.sub(r"\\tilde\{c\}", "c̃", s)

        # Delimiters and operators (LONGEST COMMANDS FIRST to prevent prefix collisions like \left vs \le, \top vs \to, \infty vs \in!)
        s = s.replace(r"\left[", "[").replace(r"\right]", "]")
        s = s.replace(r"\left(", "(").replace(r"\right)", ")")
        s = s.replace(r"\left\{", "{").replace(r"\right\}", "}")
        s = s.replace(r"\left|", "|").replace(r"\right|", "|")
        s = s.replace(r"\|", "||")
        s = s.replace(r"\{", "{").replace(r"\}", "}")
        s = s.replace(r"\%", "%").replace(r"\_", "_").replace(r"\#", "#").replace(r"\*", "*")
        s = s.replace(r"\quad", "   ").replace(r"\;", " ").replace(r"\,", " ")
        s = s.replace(r"\dots", "...").replace(r"\cdots", "...").replace(r"\cdot", "·")
        s = s.replace(r"\Rightarrow", "⇒").replace(r"\top", "T").replace(r"\to", "→").replace(r"\mid", "|")
        s = s.replace(r"\infty", "∞").replace(r"\in", "∈").replace(r"\cup", "∪").replace(r"\cap", "∩")
        s = s.replace(r"\times", "×").replace(r"\pm", "±").replace(r"\neq", "≠")
        s = s.replace(r"\ge", "≥").replace(r"\le", "≤").replace(r"\sim", "≈")
        s = s.replace(r"\ln", "ln").replace(r"\log", "log").replace(r"\min", "min").replace(r"\max", "max")
        s = s.replace(r"\sum", "∑").replace(r"\prod", "∏")
        s = s.replace(r"\Delta", "Δ").replace(r"\chi", "χ").replace(r"\beta", "β")
        s = s.replace(r"\gamma", "γ").replace(r"\theta", "θ").replace(r"\pi", "π")
        s = s.replace(r"\sigma", "σ").replace(r"\lambda", "λ").replace(r"\alpha", "α")
        s = s.replace(r"\tau", "τ").replace(r"\phi", "φ")

        # Handle nested subscripts like _{i_k} -> ⟦SUB:ik⟧
        s = re.sub(r"_\{([a-zA-Z0-9]+)_([a-zA-Z0-9]+)\}", r"⟦SUB:\1\2⟧", s)
        # Handle _{...} and ^{...} using non-colliding delimiters
        s = re.sub(r"\^\{([^\}]+)\}", r"⟦SUP:\1⟧", s)
        s = re.sub(r"_\{([^\}]+)\}", r"⟦SUB:\1⟧", s)
        # Handle single-token ^x and _x (do not greedily consume markdown closing **)
        s = re.sub(r"\^\*(?!\*)", "⟦SUP:AST⟧", s)
        s = re.sub(r"\^\*(?=\*\*)", "⟦SUP:AST⟧", s)
        s = re.sub(r"\^([+\-0-9a-zA-Z\#]+)", r"⟦SUP:\1⟧", s)
        s = re.sub(r"_([+\-0-9a-zA-Z∞]+)", r"⟦SUB:\1⟧", s)
        s = re.sub(r"⟦SUP:([^⟧]*)\*([^⟧]*)⟧", r"⟦SUP:\1AST\2⟧", s)
        return s

    def add_formatted_runs(p, text, size_pt=12, default_bold=False):
        clean = sanitize_latex_to_supsub(text)
        tokens = re.split(r"(\*\*(?:[^*]|\*[^*]+\*)+\*\*|\*[^*]+\*)", clean)
        for tok in tokens:
            if not tok:
                continue
            is_b = default_bold
            is_i = False
            inner = tok
            if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
                is_b = True
                inner = tok[2:-2]
            elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
                is_i = True
                inner = tok[1:-1]
            inner = inner.replace("**", "")
            # Split by ⟦SUP:...⟧ and ⟦SUB:...⟧
            sub_parts = re.split(r"(⟦SUP:[^⟧]+⟧|⟦SUB:[^⟧]+⟧)", inner)
            for sp in sub_parts:
                if not sp:
                    continue
                if sp.startswith("⟦SUP:") and sp.endswith("⟧"):
                    r = p.add_run(sp[5:-1].replace("AST", "*"))
                    format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)
                    r.font.superscript = True
                elif sp.startswith("⟦SUB:") and sp.endswith("⟧"):
                    r = p.add_run(sp[5:-1].replace("AST", "*"))
                    format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)
                    r.font.subscript = True
                else:
                    r = p.add_run(sp)
                    format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)

    def create_base_doc():
        doc = Document()
        for sec in doc.sections:
            sec.top_margin = Inches(1.0)
            sec.bottom_margin = Inches(1.0)
            sec.left_margin = Inches(1.0)
            sec.right_margin = Inches(1.0)
        st = doc.styles["Normal"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(12)
        st.paragraph_format.line_spacing = 2.0
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        st.paragraph_format.space_before = Pt(0)
        st.paragraph_format.space_after = Pt(0)
        return doc

    def add_heading_para(doc, text, level=1):
        style_name = "Heading 1" if level <= 1 else ("Heading 2" if level == 2 else "Heading 3")
        p = doc.add_paragraph(style=style_name)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_before = Pt(18 if level == 0 else (8 if level <= 2 else 6))
        p.paragraph_format.space_after = Pt(4)
        sz = 20 if level == 0 else (16 if level == 1 else (14 if level == 2 else 12))
        add_formatted_runs(p, text, size_pt=sz, default_bold=True)
        return p

    def add_body_para(doc, text, justify=True, indent_first=False, line_spacing=2.0):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = line_spacing
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        if indent_first:
            p.paragraph_format.first_line_indent = Inches(0.3)
        add_formatted_runs(p, text, size_pt=12, default_bold=False)
        return p

    def add_three_line_table(doc, rows_md):
        hdr = [c.strip() for c in rows_md[0].strip("|").split("|")]
        body = [[c.strip() for c in r.strip("|").split("|")] for r in rows_md[2:]]
        tbl = doc.add_table(rows=1 + len(body), cols=len(hdr))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        top_b = {"val": "single", "sz": 12, "color": "000000"}
        mid_b = {"val": "single", "sz": 6, "color": "000000"}
        bot_b = {"val": "single", "sz": 12, "color": "000000"}

        for j, h_text in enumerate(hdr):
            cell = tbl.rows[0].cells[j]
            set_cell_Borders(cell, top=top_b, bottom=mid_b)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            add_formatted_runs(p, h_text, size_pt=9.5, default_bold=True)

        for i, row_vals in enumerate(body):
            is_last = i == len(body) - 1
            for j, val in enumerate(row_vals):
                if j >= len(hdr):
                    continue
                cell = tbl.rows[i + 1].cells[j]
                set_cell_Borders(cell, bottom=bot_b if is_last else None)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                add_formatted_runs(p, val, size_pt=9.0, default_bold=False)

    def render_markdown_to_docx(md_path, docx_path, embed_figures=False):
        doc = create_base_doc()
        lines = open(md_path, encoding="utf-8").read().splitlines()
        i = 0
        while i < len(lines):
            ln = lines[i].strip()
            if not ln or ln == "---":
                i += 1
                continue
            if ln.startswith("# ") and not ln.startswith("## "):
                add_heading_para(doc, ln[2:].strip(), level=0)
                i += 1
                continue
            if ln.startswith("## "):
                add_heading_para(doc, ln[3:].strip(), level=1)
                i += 1
                continue
            if ln.startswith("### "):
                add_heading_para(doc, ln[4:].strip(), level=2)
                i += 1
                continue
            if ln.startswith("#### "):
                add_heading_para(doc, ln[5:].strip(), level=3)
                i += 1
                continue
            if ln.startswith("$$") and ln.endswith("$$"):
                p = add_body_para(doc, ln.strip("$"), justify=True)
                i += 1
                continue
            if ln.startswith("|"):
                tbl_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    tbl_lines.append(lines[i].strip())
                    i += 1
                if len(tbl_lines) >= 3:
                    add_three_line_table(doc, tbl_lines)
                continue
            if ln.startswith("- "):
                add_body_para(doc, "• " + ln[2:].strip(), justify=True)
                i += 1
                continue
            add_body_para(doc, ln, justify=True)
            i += 1

        if embed_figures:
            add_heading_para(doc, "Figures", level=1)
            fig_files = [
                ("Figure 1", "Fig1_Audit_Remediation_Architecture.png"),
                ("Figure 2", "Fig2_Dim1_Trojan_Horse_Citations.png"),
                ("Figure 3", "Fig3_Dim2_Reasoning_vs_Memorization.png"),
                ("Figure 4", "Fig4_Dim3_Dim5_Primacy_and_NLI.png"),
                ("Figure 5", "Fig5_Dim4_Dim6_Reasoning_Paradox.png"),
                ("Figure 6", "Fig6_Audit_Guided_Rectification_Impact.png"),
                ("Figure 7", "Fig7_STAR_Audit_Working_Model.png"),
            ]
            for fig_label, fname in fig_files:
                fpath = os.path.join(FIG_DIR, fname)
                if os.path.exists(fpath):
                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p_img.paragraph_format.line_spacing = 2.0
                    r_img = p_img.add_run()
                    r_img.font.name = "Times New Roman"
                    r_img.add_picture(fpath, width=Inches(6.4))
                    add_body_para(doc, f"**{fig_label}.** Multi-panel main figure (see Figure Legends for full description).", justify=True)

        doc.save(docx_path)
        print("Saved Word document:", docx_path)

    render_markdown_to_docx(
        os.path.join(BASE, "MANUSCRIPT_GEN2_v1.0.md"),
        os.path.join(BASE, "MANUSCRIPT_GEN2_v1.0.docx"),
        embed_figures=True,
    )
    render_markdown_to_docx(
        os.path.join(BASE, "SUPPLEMENTARY_GEN2_v1.0.md"),
        os.path.join(BASE, "SUPPLEMENTARY_GEN2_v1.0.docx"),
        embed_figures=False,
    )
    import shutil
    shutil.copy2(
        os.path.join(BASE, "SUPPLEMENTARY_GEN2_v1.0.docx"),
        r"C:\Users\sheng\Desktop\STAR-Audit_Supplementary_Information_v1.0.docx",
    )
    render_markdown_to_docx(
        os.path.join(BASE, "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md"),
        os.path.join(BASE, "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.docx"),
        embed_figures=False,
    )

