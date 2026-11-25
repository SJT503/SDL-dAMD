#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pass 2:
1. Build the flagship Nature Machine Intelligence (NMI) Slimmed Primary Edition:
   - MANUSCRIPT_NMI_v1.0.md & .docx (~185-word Abstract, ~4,250-word Main Text, 6 Main Figures + Extended Data Fig. 1 & Extended Data Tables 1-2, comprehensive Methods, 69 verified references [1..69])
   - STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md & .docx (1:1 paragraph-matched unabridged Chinese Review Edition, also synced to STAR-Audit_手稿全文中文版_审核稿.md/.docx and Desktop)
   - COVER_LETTER_NMI_v1.0.md & .docx (Pure English Cover Letter tailored to Nature Machine Intelligence)
   - STAR-Audit_投稿信_NMI_中英对照版.md & .docx (Bilingual Review Cover Letter for NMI)
2. Render all updated .docx files (NMI Primary, npj Digital Medicine Full-Length Backup, Cell Press Patterns Backup, Supplementary Information, and all Cover Letters) enforcing user's locked-in submission DOCX format (Times New Roman 12pt, line_spacing=2.0, JUSTIFY, native three-line tables, zero raw LaTeX/MD/TAB).
"""

import os
import re
import shutil
from pathlib import Path

import sys
sys.path.insert(0, r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\GEN2_exec\analysis")
from generate_nature_and_zh_desktop import (
    create_base_doc,
    add_heading_para,
    add_body_para,
    add_three_line_table,
)
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
FIG_DIR = BASE / "GEN2_exec" / "figures"
DESKTOP = Path(r"C:\Users\sheng\Desktop")


def render_md_to_docx_custom(md_path: Path, docx_path: Path, mode: str = "npj_en") -> None:
    """
    mode:
      - 'nmi_en': embeds Main Figures 1-6 + Extended Data Figure 1
      - 'nmi_zh': embeds Main Figures 1-6 + Extended Data Figure 1 (Chinese captions)
      - 'npj_en': embeds Main Figures 1-7
      - 'npj_zh': embeds Main Figures 1-7 (Chinese captions)
      - 'plain': no embedded figure gallery (Supplementary / Cover Letters / Patterns)
    """
    zh_mode = mode.endswith("_zh")
    doc = create_base_doc()
    lines = md_path.read_text(encoding="utf-8").splitlines()
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
            add_body_para(doc, ln.strip("$"), justify=True)
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

    if mode in ("nmi_en", "nmi_zh"):
        add_heading_para(doc, "附图（Figures 1–6 高清主图与扩展数据图 1）" if zh_mode else "Main and Extended Data Figures", level=1)
        fig_files = [
            ("图 1 (Figure 1)" if zh_mode else "Figure 1", "Fig1_Audit_Remediation_Architecture.png"),
            ("图 2 (Figure 2)" if zh_mode else "Figure 2", "Fig2_Dim1_Trojan_Horse_Citations.png"),
            ("图 3 (Figure 3)" if zh_mode else "Figure 3", "Fig3_Dim2_Reasoning_vs_Memorization.png"),
            ("图 4 (Figure 4)" if zh_mode else "Figure 4", "Fig4_Dim3_Dim5_Primacy_and_NLI.png"),
            ("图 5 (Figure 5)" if zh_mode else "Figure 5", "Fig5_Dim4_Dim6_Reasoning_Paradox.png"),
            ("图 6 (Figure 6)" if zh_mode else "Figure 6", "Fig6_Audit_Guided_Rectification_Impact.png"),
            ("扩展数据图 1 (Extended Data Fig. 1)" if zh_mode else "Extended Data Figure 1", "Fig7_STAR_Audit_Working_Model.png"),
        ]
        for fig_label, fname in fig_files:
            fpath = FIG_DIR / fname
            if fpath.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_img.paragraph_format.line_spacing = 2.0
                r_img = p_img.add_run()
                r_img.font.name = "Times New Roman"
                r_img.add_picture(str(fpath), width=Inches(6.4))
                cap = (
                    f"**{fig_label}.** 高清图表预览（完整图注见上文“图注”及“扩展数据”章节）。"
                    if zh_mode
                    else f"**{fig_label}.** High-resolution display item (see Figure Legends and Extended Data for full description)."
                )
                add_body_para(doc, cap, justify=True)
    elif mode in ("npj_en", "npj_zh"):
        add_heading_para(doc, "附图（Figures 1–7 高清主图）" if zh_mode else "Figures", level=1)
        fig_files = [
            ("图 1 (Figure 1)" if zh_mode else "Figure 1", "Fig1_Audit_Remediation_Architecture.png"),
            ("图 2 (Figure 2)" if zh_mode else "Figure 2", "Fig2_Dim1_Trojan_Horse_Citations.png"),
            ("图 3 (Figure 3)" if zh_mode else "Figure 3", "Fig3_Dim2_Reasoning_vs_Memorization.png"),
            ("图 4 (Figure 4)" if zh_mode else "Figure 4", "Fig4_Dim3_Dim5_Primacy_and_NLI.png"),
            ("图 5 (Figure 5)" if zh_mode else "Figure 5", "Fig5_Dim4_Dim6_Reasoning_Paradox.png"),
            ("图 6 (Figure 6)" if zh_mode else "Figure 6", "Fig6_Audit_Guided_Rectification_Impact.png"),
            ("图 7 (Figure 7)" if zh_mode else "Figure 7", "Fig7_STAR_Audit_Working_Model.png"),
        ]
        for fig_label, fname in fig_files:
            fpath = FIG_DIR / fname
            if fpath.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_img.paragraph_format.line_spacing = 2.0
                r_img = p_img.add_run()
                r_img.font.name = "Times New Roman"
                r_img.add_picture(str(fpath), width=Inches(6.4))
                cap = (
                    f"**{fig_label}.** 多面板高清主图（完整图注见上文“图注”一节）。"
                    if zh_mode
                    else f"**{fig_label}.** Multi-panel main figure (see Figure Legends for full description)."
                )
                add_body_para(doc, cap, justify=True)

    doc.save(str(docx_path))
    print(f"[OK] Rendered DOCX: {docx_path.name} ({docx_path.stat().st_size:,} B)")


def extract_npj_sections():
    npj_en = (BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md").read_text(encoding="utf-8")
    npj_zh = (BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md").read_text(encoding="utf-8")

    # Extract Methods .. before Figure Legends, Figure Legends (1..6 vs 7), Tables (1..2), and References
    en_methods_to_legends = re.search(r"(## Methods\n.*?)(?=## Figure Legends\n)", npj_en, flags=re.S).group(1)
    en_fig1_6 = re.search(r"## Figure Legends\n\n(\*\*Figure 1\..*?)(?=\n\*\*Figure 7\.)", npj_en, flags=re.S).group(1).strip()
    en_fig7_body = re.search(r"\*\*Figure 7\.[^\n]+\n(.*?)(?=\n## Tables\n)", npj_en, flags=re.S).group(1).strip()
    en_tables_block = re.search(r"## Tables\n\n(.*?)(?=\n## References\n)", npj_en, flags=re.S).group(1).strip()
    en_refs = re.search(r"(## References\n.*)$", npj_en, flags=re.S).group(1).strip()

    zh_methods_to_legends = re.search(r"(## 方法\n.*?)(?=## 图注\n)", npj_zh, flags=re.S).group(1)
    zh_fig1_6 = re.search(r"## 图注\n\n(\*\*图 1（Figure 1）\..*?)(?=\n\*\*图 7（Figure 7）\.)", npj_zh, flags=re.S).group(1).strip()
    zh_fig7_body = re.search(r"\*\*图 7（Figure 7）\.[^\n]+\n(.*?)(?=\n+## 表格\n)", npj_zh, flags=re.S).group(1).strip()
    zh_tables_block = re.search(r"## 表格\n\n(.*?)(?=\n+## 参考文献\n)", npj_zh, flags=re.S).group(1).strip()
    zh_refs = re.search(r"(## 参考文献\n.*)$", npj_zh, flags=re.S).group(1).strip()

    return (
        en_methods_to_legends,
        en_fig1_6,
        en_fig7_body,
        en_tables_block,
        en_refs,
        zh_methods_to_legends,
        zh_fig1_6,
        zh_fig7_body,
        zh_tables_block,
        zh_refs,
    )


def build_nmi_manuscripts() -> None:
    (
        en_methods_to_legends,
        en_fig1_6,
        en_fig7_body,
        en_tables_block,
        en_refs,
        zh_methods_to_legends,
        zh_fig1_6,
        zh_fig7_body,
        zh_tables_block,
        zh_refs,
    ) = extract_npj_sections()

    # Enrich Methods -> Dimension 3 & Module 1 with the exact per-run Slot-B exposure telemetry so zero detail is lost when Main Text is slimmed
    en_slotb_note = (
        " Across the 12 Parent runs, representative Tournament I rescues anchored against orthogonal genetic and preclinical benchmarks included "
        "`M23` (`GAS6/PROS1–MERTK` in `dAMD_retrieval_R1`, placed in Slot B in 14/16 [87.5%] comparisons, Rank 11 to Rank 7), "
        "`M25` (`TIMP3/MMP2/MMP9` in `dAMD_retrieval_R2`, 15/19 [78.9%] Slot B, Rank 15 to Rank 8), "
        "`M25` (`ABCA1/LIPC/CETP` in `dAMD_retrieval_R3`, 15/19 [78.9%] Slot B, Rank 15 to Rank 6), "
        "`M14` (`CD59` in `dAMD_retrieval_R3`, 9/9 Slot-A vs 3/9 Slot-B wins, Rank 11 to Rank 5), "
        "`M22` (`MTTP/APOB100/SOAT1` in `dAMD_blind_R1`, 15/21 [71.4%] Slot B, Rank 12 to Rank 6), "
        "`M26` (`MMP9/MMP2` in `ALS_blind_R2`, 17/19 [89.5%] Slot B, Rank 13 to Rank 6), "
        "`M29` (`CCS/ATP7A` in `ALS_retrieval_R3`, 23/23 [100.0%] Slot B, winning 13/23 entirely from Slot B, Rank 15 to Rank 10), "
        "`M25` (`MCT1/SLC16A1` in `ALS_blind_R3`, 15/19 [78.9%] Slot B, Rank 11 to Rank 7), and "
        "`M18` (`C1QA/C3` in `ALS_blind_R1`, 13/23 [56.5%] Slot B, Rank 13 to Rank 10; complete ledger in Supplementary Table S2)."
    )
    en_methods_nmi = en_methods_to_legends.replace(
        "ensuring that only order-invariant preferences drive final Top-5 BTL selection.",
        "ensuring that only order-invariant preferences drive final Top-5 BTL selection." + en_slotb_note,
        1,
    )

    zh_slotb_note = (
        "在 12 次主运行的 Tournament I 初筛中，锚定正交遗传学与临床前金标准的代表性拯救案例包括："
        "`dAMD_retrieval_R1` 的 `M23`（`GAS6/PROS1–MERTK`，14/16 [87.5%] 居 B 槽位，第 11 名升至第 7 名）、"
        "`dAMD_retrieval_R2` 的 `M25`（`TIMP3/MMP2/MMP9`，15/19 [78.9%] 居 B 槽位，第 15 名升至第 8 名）、"
        "`dAMD_retrieval_R3` 的 `M25`（`ABCA1/LIPC/CETP`，15/19 [78.9%] 居 B 槽位，第 15 名升至第 6 名）与 `M14`（`CD59`，A 槽位 9/9 胜对比 B 槽位 3/9 胜，第 11 名升至第 5 名）、"
        "`dAMD_blind_R1` 的 `M22`（`MTTP/APOB100/SOAT1`，15/21 [71.4%] 居 B 槽位，第 12 名升至第 6 名）、"
        "`ALS_blind_R2` 的 `M26`（`MMP9/MMP2`，17/19 [89.5%] 居 B 槽位，第 13 名升至第 6 名）、"
        "`ALS_retrieval_R3` 的 `M29`（`CCS/ATP7A`，23/23 [100.0%] 居 B 槽位且全在 B 槽位赢下 13/23 场，第 15 名升至第 10 名）、"
        "`ALS_blind_R3` 的 `M25`（`MCT1/SLC16A1`，15/19 [78.9%] 居 B 槽位，第 11 名升至第 7 名）以及 "
        "`ALS_blind_R1` 的 `M18`（`C1QA/C3`，13/23 [56.5%] 居 B 槽位，第 13 名升至第 10 名；完整台账见补充表 S2）。"
    )
    zh_methods_nmi = zh_methods_to_legends.replace(
        "确保仅跨顺序一致偏好驱动 Top-5 遴选。",
        "确保仅跨顺序一致偏好驱动 Top-5 遴选。" + zh_slotb_note,
        1,
    )

    en_ext_tables = (
        en_tables_block.replace(
            "**Table 1. Comparison of the STAR-Audit framework against representative autonomous discovery and AI reliability studies.**",
            "**Extended Data Table 1. Comparison of the STAR-Audit framework against representative autonomous discovery and AI reliability studies.**",
        ).replace(
            "**Table 2. Pre-specified six-member confirmatory hypothesis family and headline STAR-Audit outcomes.**",
            "**Extended Data Table 2. Pre-specified six-member confirmatory hypothesis family and headline STAR-Audit outcomes.**",
        )
    )
    zh_ext_tables = (
        zh_tables_block.replace(
            "**表 1（Table 1）. STAR-Audit 框架与代表性自主科学发现及人工智能可靠性研究的系统对比。**",
            "**扩展数据表 1（Extended Data Table 1）. STAR-Audit 框架与代表性自主科学发现及人工智能可靠性研究的系统对比。**",
        ).replace(
            "**表 2（Table 2）. 预先设定的 6 成员验证性假设族与 STAR-Audit 核心审计及纠偏结果汇总。**",
            "**扩展数据表 2（Extended Data Table 2）. 预先设定的 6 成员验证性假设族与 STAR-Audit 核心审计及纠偏结果汇总。**",
        )
    )

    nmi_en_core = f"""# Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery

**Jiangtao Sheng$^{{1,\\#,\\*}}$, Xueer Liu$^{{1}}$, Runmin Lin$^{{1}}$, Qiaochu Sun$^{{1}}$, Xiaoxuan Chen$^{{1}}$, Kangsheng Li$^{{1}}$, and Weiqiang Chen$^{{2,\\*}}$**

$^{{1}}$Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China

$^{{2}}$Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China

$^{{\\text{{#}}}}$Lead contact: Jiangtao Sheng (jtsheng@stu.edu.cn)

$^{{\\text{{*}}}}$Correspondence: Jiangtao Sheng (jtsheng@stu.edu.cn; ORCID: 0000-0003-2438-7345); Weiqiang Chen (wqchen@stu.edu.cn; ORCID: 0000-0002-2612-0890)

## Abstract
Autonomous multi-agent systems combine hypothesis ideation, pairwise tournaments, and literature grounding for scientific discovery, yet whether test-time reasoning ensures pipeline trustworthiness remains unknown. Here we present **STAR-Audit**, a six-dimension audit and zero-cost algorithmic rectification framework spanning faithfulness, reasoning versus memorization, positional fairness, stability, coherence, and calibration. Auditing 11,818 live evaluations (37.18 million reasoning and output tokens) across GLM-5.3, DeepSeek-V4-Pro, Gemini-4-Argon-High, Gemini-3.8-Flash, Grok-4.7, and Grok-4.7-Fast over 136 diseases uncovers a test-time reasoning paradox: deeper chain-of-thought fails to self-correct pipeline biases. Surface checks score 96.9–100.0% of PubMed identifiers valid, whereas semantic verification exposes 11.9–76.2% Trojan horse citations driven by 35.8 candidate identifiers dredged per call. Single-order Tournament I exhibits a 71.3% Slot-A win rate suppressing late-indexed pathways ($\\chi^2 = 55.40$), 8.9–43.0% of Tournament II pairs flip under reversal, and 23.3% of failed Mendelian inferences self-prune causal genes activated at 2.1% reasoning depth. Four zero-call deterministic modules (Order-Adjusted BTL, Platt scaling, epistemic gating, and CoT-SRAD) rescue validated targets, cut ungrounded citations by 11.9–54.8 percentage points and citation tokens by 86.2–97.3%, calibrate all six models ($\\text{{ECE}} \\le 0.115$), and boost Mendelian recall by 57.1%.

**Keywords:** autonomous scientific discovery; large language models; test-time reasoning; Bradley–Terry–Luce tournament; citation faithfulness; confidence calibration; algorithmic rectification

## Introduction
Autonomous scientific discovery systems powered by large language models (LLMs) have evolved from single-step reaction planners [1, 2] into multi-agent architectures that formulate mechanistic hypotheses, rank candidates through pairwise tournaments, and synthesize experimental protocols [3–5]. Across biomedical domains, leading discovery engines share a three-stage computational backbone: multi-bucket candidate ideation, pairwise judging aggregated via Bradley–Terry–Luce (BTL) or Elo strength estimation [6, 7], and literature-grounded protocol generation [8–10]. Isolated wet-lab hits demonstrate the promise of this architecture [3], yet a foundational methodological question remains unresolved: before committing experimental capital, how can researchers verify whether an agentic pipeline's internal reasoning, tournament ranking, and evidentiary citations are trustworthy?

Current agentic artificial intelligence (AI) design widely assumes that scaling test-time reasoning tokens enables frontier models to self-verify factual claims, resist prompt framing, and calibrate uncertainty. Separate machine learning and clinical informatics studies indicate, however, that unguarded language models remain vulnerable to reference fabrication (21–100% in medical generation [11–15]), pairwise positional bias [7, 16], pretraining memorization [9, 17], and verbalized overconfidence [18–20]. Existing reliability tools examine isolated surfaces, including statement-level confabulation [20–22], single-task gene-set or causal agents [23–25], reproducibility rules separating on-the-data-path LLM calls from off-the-data-path deterministic code [26, 27], clinical summarization abstention [28], multi-agent oncology consensus [29], and Gaussian-process representation fine-tuning [30]. Recent 2025–2026 benchmarks have further exposed unresolved evidence conflicts in knowledge-graph explorers [31], memorization leakage in molecular benchmarks [32], structured chain-of-thought anchoring [33], rhetorical rather than structural persona shifts [34], and plausible invalidity in autonomous multi-agent workflows [35]. No framework, however, integrates external-truth auditing with zero-training algorithmic rectification across the complete multi-stage discovery loop (Extended Data Table 1).

To establish a generalizable methodology for trustworthy autonomous discovery, we developed **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification) under cryptographic SHA-256 protocol locking and pre-specified Benjamini–Hochberg false discovery rate governance ($q = 0.05$) [36]. **STAR-Audit** instruments six orthogonal dimensions across the canonical discovery cascade: two-tier NCBI PubMed semantic grounding (Dimension 1), blind versus retrieval pathway separation and phenotype information-content perturbation (Dimension 2), Tournament I single-order skew and Tournament II bidirectional reversal (Dimension 3), replicated Top-5 stability against a 10,000-draw verdict-table bootstrap null (Dimension 4), DeBERTa-v3 natural language inference (NLI) contradiction auditing (Dimension 5), and out-of-sample confidence calibration (Dimension 6). We exercise **STAR-Audit** across 9,130 primary invocations on GLM-5.3 and DeepSeek-V4-Pro (35.58 million internal reasoning tokens across 8,973 white-box traces; 93.83% of primary output) plus 2,688 cross-ecosystem evaluations across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]) and xAI Grok (`Grok-4.7` and `Grok-4.7-Fast`), totaling 11,818 live evaluations and 37.18 million reasoning and output tokens over 136 diseases (Figure 1A–D).

Pairing white-box chain-of-thought trajectory dynamics with controlled perturbations uncovers the **Test-Time Reasoning Paradox**: unanchored deliberation dredges 35.8 candidate PMIDs per call to emit off-topic Trojan horse citations, anchors 88.4–90.6% of Decile-1 attention on Slot A to extinguish late-indexed pathways, and self-prunes valid causal genes activated at 2.1% reasoning depth in favor of textbook syndromic attractors. Moving from diagnosis to zero-call remediation, we formulate four off-the-data-path deterministic operators: Order-Adjusted BTL (`OA-BTL`) with NLI-discordance neutralization, Leave-One-Run-Out (`LORO`) Platt scaling, two-tier epistemic citation gating, and Chain-of-Thought Stream Recovery and Attractor Deconfounding (`CoT-SRAD`). Together, these modules rescue validated biological targets, calibrate all six frontier models, boost Mendelian gene recall by up to 57.1%, and cut citation reasoning compute by 86.2–97.3% without a single additional LLM call.

[INSERT FIGURE 1 ABOUT HERE]

## Results

### Multi-block architecture, compute ledger, and confirmatory scorecard
We locked all prompts, blind-word lists, disease pathway gold standards, and a six-member confirmatory hypothesis family ($q = 0.05$) via SHA-256 hashing prior to analysis (Figure 1A). Block 1 executed 12 end-to-end six-stage Parent discovery runs (7,890 calls) in a $2 \\times 2 \\times 3$ factorial crossing dry age-related macular degeneration (dAMD; multi-axis complement, matrix, lipid, and retinal pigment epithelium [RPE] phagocytic pathology [37–44]) and amyotrophic lateral sclerosis (ALS; TDP-43 cryptic splicing alongside SOD1 and autophagy axes [45–48]) against strictly Blind ideation (Supplementary Note 1) versus PubMed Abstract-Injected Retrieval ($R = 3$ replicates per cell). Each run progressed through 30-candidate multi-bucket ideation (Step 1), 300-pair single-order Tournament I BTL screening to Top 10 (Step 2), dossier expansion (Step 3), 270-verdict bidirectional three-persona (`SCIENCE`, `METHODS`, `NOVELTY`) Tournament II judging across all 45 pairs (Step 4), Top-5 selection (Step 5; Supplementary Table S1 and Supplementary Table S2), and 30-slot protocol citation synthesis (Step 6; 360 total slots). Block 2 (Experiment B; 396 calls, 1,260 slots across 14 clinical domains; Supplementary Table S3) randomized citation generation across `as_discovered`, `abstain_probe`, and `gated` arms. Block 3 (Experiment C-v4; 804 logged calls, 630 non-truncated generalized linear mixed model [GLMM] calls across GLM-5.3 and DeepSeek-V4-Pro; Supplementary Table S4) masked 120 Human Phenotype Ontology (HPO [49]) Mendelian diseases at 0%, 25%, and 50% information-content (IC) deletion under `del_topIC` versus `del_lowIC_matched` arms.

Across the primary study (including 40 temperature-0 drift-canary calls confirming $\\text{{drift}} = 0.000$), 9,130 live API invocations consumed 5.74 million input and 37.92 million output tokens, with internal chain-of-thought accounting for 35.58 million tokens (**93.83%**) versus 2.34 million answer tokens (Figure 1B). Combined with 2,688 Google Gemini (1.15 million output/reasoning tokens; 12.05 million total tokens including cache) and xAI Grok (0.45 million native reasoning tokens) evaluations, the study spans **11,818 evaluations and 37.18 million reasoning and output tokens**. Despite `effort=high` budgets (`max_tokens=32,768`), three confirmatory null hypotheses were rejected after BH-FDR correction (Member 1 Citation Gating $q = 0.0310$, Member 5 Cross-Run Instability vs Verdict Bootstrap Null $q = 0.0012$, and Member 6 Calibration Slope $q = 0.0401$). Member 4 (Blind vs Retrieval Lead-Gene Separation) reached the exact discrete permutation floor ($p = 0.10$ per disease; combined $p = 0.0561, q = 0.0841$), and Members 2–3 revealed steep high-IC deletion sensitivity on DeepSeek-V4-Pro ($p = 0.0259$) alongside a dominant literature-footprint effect across vendors (Figure 1C, D; Extended Data Table 2).

### Two-tier grounding exposes Trojan horse citations and validates epistemic gating
Standard pipeline checks verify only whether an emitted PMID exists in NCBI Entrez [11, 14]. We deployed a two-tier live NCBI E-utilities verifier (`esummary`/`efetch`; 100.0% sensitivity and 100.0% specificity on a frozen 200-pair calibration benchmark; Supplementary Note 2) checking Tier-1 identifier existence and Tier-2 semantic claim overlap against official titles, abstracts, and Medical Subject Headings (MeSH). Across 360 Parent Step-6 slots and 420 unguarded Experiment B `as_discovered` slots on GLM-5.3, fabricated non-existent PMIDs were rare (**1.67%** [6/360] and **3.10%** [13/420]), yielding 98.33% and 96.90% apparent Tier-1 validity (Figure 2A). Tier-2 semantic auditing exposed **56.67%** (204/360) of Parent citations and **54.29%** (228/420) of Experiment B `as_discovered` citations as **Trojan horse citations**: real, high-citation PubMed papers from unrelated diseases attached to unsupported dAMD, ALS, or clinical claims, bringing total ungrounded rates to **58.33%** and **57.38%** (Figure 2A). Step-1 PubMed abstract injection (`retrieval` arm) failed to protect Step-6 protocol synthesis when citation slots remained mandatory (`54.44%` ungrounded in dAMD retrieval and `66.67%` in ALS retrieval vs `47.78%` and `64.44%` in blind runs; Figure 2B).

[INSERT FIGURE 2 ABOUT HERE]

Randomized Experiment B across 14 clinical domains demonstrated that architectural gating resolves Trojan horse misattribution while halting internal memory dredging (Figure 2C, D). Relative to `as_discovered` (0% abstention, 57.38% ungrounded) and `abstain_probe` (63.81% abstention, 18.10% ungrounded), strict epistemic gating (`gated`, 95.24% parametric abstention) eliminated fabricated PMIDs (**0.00%**, 0/420; Confirmatory Member 1 paired risk difference $\\text{{RD}} = +3.10\\%$, 95% CI $[1.43\\%, 4.76\\%]$, Wilcoxon $p = 0.01032, q_{{\\text{{BH}}}} = 0.03096$) and reduced ungrounded citations to **2.86%** (12/420; $-54.52\\text{{ pp}}$, 95% CI $[45.00\\%, 62.86\\%]$, $p = 0.00097$, 14/14 domains improved; Figure 2C). White-box inspection of all 380 Experiment B `reasoning_content` traces revealed why: under `as_discovered`, GLM-5.3 trials **35.82 distinct 7–8 digit candidate PMIDs per call** (median 32.0) alongside **390.32 hesitation markers** and **198.53 publication-year anchors**, colliding with unrelated real papers sharing chronological PubMed prefixes. Whereas `abstain_probe` still dredged **25.37 candidate PMIDs per call**, `gated` collapsed candidate dredging to **5.00 PMIDs per call** (median 3.0; Kruskal–Wallis $H = 201.17, p = 2.07 \\times 10^{{-44}}$) and cut hesitation spin 10.5-fold (`390.32 -> 37.16`; Figure 2D).

### Multi-scale biological convergence and 120-disease HPO perturbation
Just as token-level entropy conflates semantically equivalent phrasings [20] and distinct transcriptomic senescence modules (`SenMayo`, `Fridman`, `CellAge`) exhibit minimal single-gene overlap while capturing shared cellular states [50], exact HUGO Gene Nomenclature Committee (HGNC) symbol intersection mistakes co-pathway effector diversity for instability. Evaluating our 12 Parent runs across Lead Target Genes, All-Target Dossier Modules, and Appendix A Canonical Biological Pathway Axes showed that **100.0% (12/12) of runs recovered 2 to 4 gold-standard disease axes in their Top-5** (48/60 [80.0%] primary gold-axis dossiers, 12/60 [20.0%] conserved innate-immune/autophagy dossiers, zero non-biological decoys; Figure 3A). Aggregating across **Gene $\\to$ Module $\\to$ Pathway Axis** produced a **2.8- to 4.3-fold convergence surge**. In single-attractor ALS, 6/6 runs converged on TDP-43 cryptic splicing (`STMN2/UNC13A` [45–48], reconstructed from first principles across 7 automatic forbidden-token redrafts in blind runs), while retrieval runs selectively added trial-adjacent `IL-2/FOXP3` and `C1QA/C3` axes ($\\Delta J_{{\\text{{lead}}}} = +0.1296$, exact permutation $p = 0.10$), lifting within-arm similarity from $J_{{\\text{{lead}}}} = 0.2037$ to $J_{{\\text{{axis}}}} = 0.5722$ (**$2.81\\times$**; Figure 3B). In multi-axis dAMD [37, 38, 51], runs sampled distinct druggable effectors (`CFH`, `C3`, `MASP1/2`, `SERPING1`, `SULF2`) within shared complement/Bruch's membrane, inflammasome, ferroptosis, and cGAS-STING axes, lifting within-arm similarity from $J_{{\\text{{lead}}}} = 0.0926$ ($\\Delta J = +0.0556, p = 0.10$; combined two-disease $p = 0.0561, q_{{\\text{{BH}}}} = 0.0841$) to $J_{{\\text{{axis}}}} = 0.3944$ (**$4.26\\times$**; Figure 3B).

[INSERT FIGURE 3 ABOUT HERE]

In Experiment C-v4 across 630 masked HPO calls on 120 rare Mendelian diseases (359 GLM-5.3, 271 DeepSeek-V4-Pro; Figure 3C, D), intact (0% deletion) Top-10 causal gene recall (`hit@10`) was 31.75% (40/126) on GLM-5.3 and 25.51% (25/98) on DeepSeek-V4-Pro. Deleting high-IC diagnostic phenotypes (`del_topIC` at 0%, 25%, 50%) caused a steep recall collapse on DeepSeek-V4-Pro (**28.3% $\\to$ 22.6% $\\to$ 14.3%**, footprint-adjusted $\\hat{{\\beta}}_{{\\text{{dose}}}} = -5.560, p = 0.0259$) versus a flatter trajectory on GLM-5.3 (`34.5% -> 31.5% -> 30.6%`; pooled $\\hat{{\\beta}}_1 = -0.573, p = 0.2191, q_{{\\text{{BH}}}} = 0.2629$; interaction $p = 0.5948$). Pretraining PubMed literature footprint strongly governed recall across both models (**38.2% vs 23.2%** high vs low footprint on GLM-5.3, $p = 0.0110$; **24.4% vs 16.9%** on DeepSeek-V4-Pro; pooled **32.3% vs 20.5%**; Figure 3C). Under degraded phenotypic specificity, missed predictions (`hit@10 = 0`) repeatedly collapsed onto canonical textbook syndromic attractors across unrelated diseases, led by `CHD7` (35 total false calls; 28 across 10 non-CHARGE diseases in missed trials), `KMT2D` (31 total), `FOXG1` (28 total), `ZEB2` (24 total), `CEP290` (24 total), `LMNA` (22 total), `KANSL1` (19 total), and `TCF4` (18 total; Figure 3D).

White-box tracking across all 630 `reasoning_content` streams uncovered a **2.1% Instant-Recognition Law**. In successful trials (`hit@10 = 1`), the true causal gene was first activated at a median reasoning depth of **$t = 0.0214$ (2.14%, IQR $1.23\\%\\text{{--}}6.69\\%$)** on GLM-5.3 and **$t = 0.0206$ (2.06%, IQR $1.35\\%\\text{{--}}3.64\\%$)** on DeepSeek-V4-Pro. Crucially, among completed false-negative trials ($n = 236$), **23.31% (55/236: 23.84% [36/151] on GLM-5.3 and 22.35% [19/85] on DeepSeek-V4-Pro)** activated the true causal gene early in chain-of-thought (median $t = 0.113$ and $0.105$) before **self-pruning** it during prolonged deliberation in favor of syndromic attractors (`CHD7`, `KMT2D`, `FOXG1`, `ANKRD11`, `ZEB2`). Among 32,768-token-truncated calls ($n = 228$), **33.33% (76/228; 43.08% [56/130] on DeepSeek-V4-Pro at median $t = 0.0268$)** had likewise already identified the true gene inside `reasoning_content`.

### Positional tournament bias drives pathway extinction and motivated rationalization
Auditing 3,202 bidirectional Tournament II verdicts (1,601 candidate pairs across 12 runs) showed that **43.04%** (689/1,601; run range 25.2–63.9%) flipped winners when presentation order was reversed, with **96.95%** (668/689) favoring whichever mechanism occupied Slot A (two-sided binomial $p = 4.63 \\times 10^{{-168}}$; `NOVELTY` 46.46%, `METHODS` 42.59%, `SCIENCE` 40.04%; Figure 4A). In single-order Tournament I screening (3,594 valid calls), **Slot A won 71.29% (2,562/3,594)** of comparisons ($p = 4.37 \\times 10^{{-148}}$). Because Step-1 ideation indexes candidates sequentially across `Bucket 1 [M00–M09]` (cell-intrinsic), `Bucket 2 [M10–M19]` (intercellular), and `Bucket 3 [M20–M29]` (extracellular matrix, complement, vascular) and formats pairs $(M_a, M_b)$ with $a < b$, standard unadjusted BTL caused severe **index-order pathway extinction** (Figure 4B). Specifically, Top-10 survival skewed from uniform `40 : 40 : 40` to **`78 : 26 : 16`** (`65.0% : 21.7% : 13.3%`, $\\chi^2 = 55.40, p = 9.33 \\times 10^{{-13}}$), discarding validated `TIMP3/MMP9`, `ABCA1/LIPC`, `CD59`, and `GAS6/MERTK` pathways before dossier expansion.

[INSERT FIGURE 4 ABOUT HERE]

Applying a DeBERTa-v3 NLI cross-encoder [52] to 480 de-aliased `SCIENCE` judge rationale pairs (Dimension 5) revealed that primacy-flipped pairs ($n = 240$) exhibited a **2.5-fold surge in directional self-contradiction** ($P_{{\\text{{contra}}}} > 0.75$: **25.42% vs 10.00%**, Fisher's exact $p = 1.15 \\times 10^{{-5}}$) and a **3.4-fold surge in strict bidirectional contradiction** (**7.08% vs 2.08%**, $p = 0.0142$; Figure 4C) relative to consistent pairs, praising whichever candidate occupied Slot A via motivated chain-of-thought. Across all 17,990 entity-anchored biological claims from Steps 1, 3, 4, and 6 (1,766 cross-stage pairs; Supplementary Table S5), DeBERTa-v3 identified **167 directional (94.56 per 1,000 pairs)** and **51 strict bidirectional contradictions (28.88 per 1,000 pairs)**, of which **43.14% (22/51)** silently entered final Top-5 experimental protocols (Figure 4D).

### Verdict-table stability, miscalibration, and the Test-Time Reasoning Paradox
To pinpoint the origin of cross-run Top-5 gene divergence (Dimension 4), a 10,000-draw parametric bootstrap of each run's 270-verdict Tournament II table (120,000 Hunter-MM BTL fits) demonstrated high internal aggregation stability (mean Jaccard **0.7389** in dAMD and **0.7783** in ALS), rejecting the verdict-noise null across every cell (**Confirmatory Member 5**: $p = 0.00020, q_{{\\text{{BH}}}} = 0.00120$; Figure 5A) and localizing divergence upstream to Step-1 ideation and single-order Tournament I screening. Under Dimension 6, verbalized confidence scores were significantly miscalibrated against tournament survival (**Confirmatory Member 6**: Step-1 calibration slope $\\hat{{\\beta}}_{{\\text{{cal}}}} = 0.655, \\text{{SE}} = 0.148, p = 0.02004, q_{{\\text{{BH}}}} = 0.04009$; pooled Parent predicted confidence **47.2%** vs **25.0%** survival, $\\text{{ECE}} = 0.222$, Brier $0.216$; Experiment C-v4 $\\text{{ECE}} = 0.351$ on GLM-5.3 and $0.244$ on DeepSeek-V4-Pro; Figure 5B).

[INSERT FIGURE 5 ABOUT HERE]

Per-call telemetry across all 9,130 primary invocations synthesized **three manifestations of the Test-Time Reasoning Paradox**, where longer chain-of-thought correlates with heightened bias and error (Figure 5C, D). In **Paradox 1**, white-box profiling of 7,592 tournament traces showed that **88.41% (Tournament I) and 90.59% (Tournament II)** of Decile-1 ($t \\in [0, 0.1]$) candidate mentions focused exclusively on Slot A; primacy-flipped Tournament II calls burned significantly *more* reasoning tokens than consistent calls (**median 2,410.5 vs 2,336.0 tokens**, Mann–Whitney $p = 0.0254$; **3.60 million tokens** spent rationalizing flips). In **Paradox 2**, unguarded `as_discovered` citation calls expended **11,798.5 median reasoning tokens** dredging candidate PMIDs, versus **8,862.0** in `abstain_probe` and **1,132.0** in `gated` (Figure 5C). In **Paradox 3**, failed Mendelian inferences (`hit@10 = 0`) consumed **1.70-fold more reasoning tokens on GLM-5.3** (**28,959.0 vs 17,071.5**, $p = 2.02 \\times 10^{{-16}}$) and **1.39-fold more on DeepSeek-V4-Pro** (**27,398.0 vs 19,671.0**, $p = 1.43 \\times 10^{{-5}}$; Figure 5D; operational ceiling ledger in Supplementary Table S6), rising monotonically (`23,040 -> 25,650 -> 26,809` tokens) as HPO information degraded.

### Four zero-cost algorithmic operators rectify ranking, grounding, calibration, and self-pruning
We converted our six diagnostic sensors into four deterministic, zero-LLM-call rectification operators (Figure 6A–D; Extended Data Table 2). **Module 1 (`Order-Adjusted BTL` + `NLI-Discordance Neutralization`)** models pairwise win probabilities as $P(i \\text{{ beats }} j \\mid A=i, B=j) = \\sigma(\\theta_i - \\theta_j + \\gamma)$ under $L_2$-penalized likelihood ($\\lambda = 0.01$; Supplementary Note 3), estimating strictly positive Slot-A primacy intercepts across all 12 runs ($\\hat{{\\gamma}}_{{\\text{{T1}}}} \\in [0.592, 1.724]$, odds ratio $1.81\\text{{--}}5.61\\times$; $\\hat{{\\gamma}}_{{\\text{{T2}}}} \\in [1.296, 2.640]$, odds ratio $3.66\\text{{--}}14.02\\times$; Figure 6A). Removing $\\hat{{\\gamma}}_{{\\text{{T1}}}}$ cut Tournament I bucket $\\chi^2$ distortion by **72.83%** (`78 : 26 : 16` $\\to$ **`60 : 31 : 29`**, $\\chi^2 = 55.40 \\to 15.05$) and boosted **Bucket-3 pathway survival by +81.25%** (Figure 4B, Figure 6C). Anchoring rescued candidates against orthogonal human-genetic, animal-model, and clinical-trial truth [53] confirmed recovery of nine canonical pathways suppressed by Slot-B assignment (71.4–100.0% Slot-B placement; per-run exposure ledger in Methods and Supplementary Table S2). In dAMD, `OA-BTL` rescued `GAS6/PROS1–MERTK` RPE efferocytosis (`Rank 11 -> 7` [39, 54–57]), `TIMP3/MMP2/MMP9` matrix turnover (`Rank 15 -> 8` [37, 58, 59]), `ABCA1/LIPC/CETP` cholesterol efflux (`Rank 15 -> 6` [37, 58]), `CD59` membrane-attack-complex inhibition (`Rank 11 -> 5` [40, 60]), and `MTTP/APOB100` lipoprotein drusen biogenesis (`Rank 12 -> 6` [42, 61]). In ALS, `OA-BTL` recovered `MMP9/LAMA1` denervation (`Rank 13 -> 6` [62]), `CCS/ATP7A` apo-SOD1 maturation (`Rank 15 -> 10` despite 23/23 Slot-B placement [63]), `MCT1/SLC16A1` oligodendrocyte lactate shuttle (`Rank 11 -> 7` [64]), and `C1QA/C3` complement synapse pruning (`Rank 13 -> 10` [65]; Figure 6B). Neutralizing the 689 order-flipped Tournament II pairs (100% position-bias purge) updated Top-5 rankings in 7/12 runs.

[INSERT FIGURE 6 ABOUT HERE]

**Module 2 (`LORO Platt Scaling`)** [18, 66] fitted out-of-sample two-parameter logistic maps across held-in runs, cutting Parent $\\text{{ECE}}$ by **87.64%** ($0.2221 \\to 0.0274$ [$0.222 \\to 0.027$, $-87.8\\%$], **97.3%** calibration accuracy; Brier $0.216 \\to 0.161$) and Experiment C-v4 $\\text{{ECE}}$ by **89.46%** on GLM-5.3 ($0.351 \\to 0.037$) and **82.79%** on DeepSeek-V4-Pro ($0.244 \\to 0.042$; Figure 5B). Combining Modules 1 and 2 with **Module 3 (`Two-Tier Epistemic Grounding Gate`)** shifted the four-pillar composite trustworthiness score across the Pareto frontier from **47.7%** (`11.80k` median CoT tokens/call) to **89.6% (+41.9 percentage points)** at **1.13k tokens/call (-86.2% citation compute)** with zero extra calls (Figure 6C, D). Finally, **Module 4 (`CoT-SRAD`)** flagged ubiquitous non-specific syndromic attractors via zero-leakage Leave-One-Disease-Out prediction frequency ($\\text{{df}}_{{\\text{{LODO}}}} \\ge 12$) and backfilled slots from each call's earliest non-attractor `reasoning_content` activations, rescuing **+36 net causal gene discoveries** across all 630 Experiment C-v4 calls (`26.35% -> 32.06%`, exact McNemar $p = 7.07 \\times 10^{{-6}}$) and boosting DeepSeek-V4-Pro recall by **+57.14%** (`20.66% [56/271] -> 32.47% [88/271]`, net +32 discoveries, $p = 9.43 \\times 10^{{-7}}$; GLM-5.3 `30.64% -> 31.75%`; Figure 3C).

### Cross-ecosystem generalization across US frontier Google Gemini and xAI Grok tiers
To verify generalization across US commercial architectures and within-family thinking tiers, we executed 2,688 matched evaluations across Google **`Gemini-4-Argon-High`** (`gemini-4-argon-high`) and **`Gemini-3.8-Flash`** (`gemini-3.8-flash-tiered`; 1,344 evaluations, 1,149,908 output/reasoning tokens) and xAI **`Grok-4.7`** (`grok-4.7`, adaptive high reasoning) and **`Grok-4.7-Fast`** (`grok-4.7-build-fast`, rapid low reasoning; 1,344 evaluations, 450,879 native reasoning tokens; Supplementary Table S7). In Arena 1 (Tournament II dAMD/ALS pairwise judging; 720 independent-session blinded verdicts plus 720 joint-context controls), blinded reversal flipped **11.11%** (10/90) of pairs on `Gemini-4-Argon-High`, **26.67%** (24/90; $2.4\\times$ higher, with 54.44% Slot-B recency) on `Gemini-3.8-Flash`, **13.33%** (12/90) on `Grok-4.7`, and **8.89%** (8/90) on `Grok-4.7-Fast` (Figure 4A). Reinforcing Paradox 1, flagship `Grok-4.7` exceeded `Grok-4.7-Fast` in both flips (`13.33% vs 8.89%`) and subscore-verdict discordance (`10.00% vs 6.67%`), joint-context presentation artificially masked flips to **0.00%** across all four models, and `OA-BTL` ($\\tau = 0.644\\text{{--}}0.956$) corrected primacy, recency, and symmetric flips simultaneously to rescue Top-3 dAMD (`C08`/`C06`) and ALS (`C02`) targets.

In Arena 2 (Experiment B across 14 clinical domains; 1,008 slots), unguarded `as_discovered` PMIDs achieved **98.81–100.0% Tier-1 existence** across all four US tiers, yet Tier-2 verification exposed **11.90%** (10/84) on `Gemini-4-Argon-High`, **76.19%** (64/84; 77.38% total ungrounded) on `Gemini-3.8-Flash`, **29.76%** (25/84) on `Grok-4.7`, and **33.33%** (28/84; 34.52% ungrounded) on `Grok-4.7-Fast` as Trojan horse citations (Figure 2D). Enforcing `gated` reduced ungrounded citations to **0.00%** ($-11.90\\text{{ pp}}, p = 0.00147$) on `Gemini-4-Argon-High`, **22.62%** ($-54.76\\text{{ pp}}, p = 1.03 \\times 10^{{-12}}$) on `Gemini-3.8-Flash`, **0.00%** ($-29.76\\text{{ pp}}, p = 7.29 \\times 10^{{-9}}$) on `Grok-4.7`, and **0.00%** ($-34.52\\text{{ pp}}, p = 1.99 \\times 10^{{-10}}$) on `Grok-4.7-Fast`, while collapsing native Grok citation reasoning tokens **30-fold** (`10,072/12,284 -> 332/330` tokens; **-96.7% to -97.3%**).

In Arena 3 (240 masked HPO evaluations across 20 Mendelian diseases at 0%, 25%, and 50% `del_topIC`), `Gemini-4-Argon-High` achieved **65.00%** (39/60) overall `hit@10` ($2.4\\times$ `Gemini-3.8-Flash` at **26.67%** [16/60]), while `Grok-4.7` (`45.0% -> 30.0% -> 20.0%`; 31.67% overall) dropped below `Grok-4.7-Fast` (`40.0% -> 35.0% -> 35.0%`; 36.67%) at 50% deletion amid shared attractor capture (`VARS2`, `POLG`, `FBXL4`, `CEP290`; Figure 3C). Out-of-sample LODO Platt scaling cut $\\text{{ECE}}$ by **86.20%** ($0.5423 \\to 0.0749$) on `Gemini-3.8-Flash`, **54.78%** ($0.2292 \\to 0.1036$) on `Grok-4.7`, and **50.72%** ($0.1652 \\to 0.0814$) on `Grok-4.7-Fast`, while keeping natively calibrated `Gemini-4-Argon-High` ($\\text{{raw ECE}} = 0.0797$; Platt mean probability **65.36% vs 65.00%** accuracy, $\\text{{ECE}} = 0.1145$) within $\\text{{ECE}} \\le 0.115$ across all six models (Figure 5B).

## Discussion
Across 11,818 live evaluations (37.18 million reasoning and output tokens) spanning four sovereign frontier model families, six versioned compute tiers, and 136 diseases, **STAR-Audit** establishes two principles for autonomous scientific discovery (Extended Data Fig. 1). First, scaling test-time chain-of-thought compute does not self-correct structural pipeline vulnerabilities; when prompts enforce unverified citation slots, uncounterbalanced pairwise slots, or sparse phenotypic inputs, extended reasoning dredges 35.8 candidate PMIDs per call, locks 88.4–90.6% of initial attention onto Slot A, and self-prunes valid causal genes activated at 2.1% reasoning depth. Second, placing lightweight mathematical sensors at stage transitions enables four zero-call deterministic rectifications (`OA-BTL`, `LORO Platt`, `Epistemic Gate`, and `CoT-SRAD`) to repair tournament ranking, rescue suppressed biological pathways and self-pruned Mendelian genes, unify probability calibration, and eliminate fabricated references at zero marginal LLM cost.

Mechanistically, internal chain-of-thought (93.83% of primary output tokens) acts as a double-edged amplifier. Under well-specified constraints (such as reconstructing ALS `TDP-43/STMN2/UNC13A` splicing or intact high-footprint HPO profiles), reasoning converges briskly (`17.1k–19.7k` tokens). Under under-constrained or position-skewed regimes, however, reasoning acts as a parametric search engine and motivated advocate across all four ecosystems. Rather than inventing fake numbers like earlier non-reasoning models [11–13], reasoning models dredge chronological PubMed prefixes to attach real off-topic papers (`11.9–76.2%` Trojan horse rates), mirroring clinical summarization findings where unanchored reasoning amplified hallucinations unless governed by abstention gates [28]. Similarly, our finding that flipped verdicts consume *more* reasoning tokens ($p = 0.0254$) with $2.5\\text{{--}}3.4\\times$ higher NLI self-contradiction ($p = 1.15 \\times 10^{{-5}}$) and higher criterion override on flagship `Grok-4.7` than `Grok-4.7-Fast` extends recent oncology observations that prompt-only mitigation cannot override chain-of-thought anchoring [33] and persona prompting alters rhetorical style rather than decision structure [34]. Under 50% HPO deletion, prolonged deliberation overwrites early 2.1%-depth causal activations with high-prior textbook attractors, explaining why `CoT-SRAD` recovers +36 true discoveries (+57.1% relative recall on DeepSeek-V4-Pro) directly from raw reasoning traces.

Each of the six **STAR-Audit** dimensions captures a non-overlapping failure surface: 100% pathway-axis precision (Dimension 2) and stable Tournament II BTL aggregation (Dimension 4) coexist with 58.3% Trojan horse citations (Dimension 1) and 22.2% overconfidence error (Dimension 6), while epistemic citation gating fixes grounding without preventing Tournament I Bucket-3 extinction (Dimension 3) or cross-stage NLI contradictions (Dimension 5). Architecturally, **STAR-Audit** bridges multi-agent discovery platforms (`Robin` [3], `Co-Scientist` [4], `DeepEvidence` [31], `HealthFlow` [35], `EvoMDT` [29], and Gaussian-process-tuned `GOLLuM` [30]) with bias-deconfounded benchmarking (`CleanSplit` [32], semantic entropy [20], `SelfCheck-Eval` [22], and off-the-data-path determinism [26, 27]). Keeping ideation and scientific judging *on the data path* while moving debiasing, NLI filtering, calibration, bibliographic verification, and trajectory recovery *off the data path* resolves multi-agent plausible invalidity [35] without weight fine-tuning, establishing a reporting standard analogous to `TRIPOD+AI` [67] prior to preclinical investment.

Five methodological scope boundaries, linked to SHA-256-sealed governance records (`D2-001`–`D2-012`; Supplementary Table S6), define prospective extensions with explicit bias directions. First, we benchmarked pathway rescue against orthogonal human-genetic (GWAS/OMIM), animal-model, and clinical-trial truth across dAMD, ALS, and 120 Mendelian diseases (`D2-001`, `D2-009`, `D2-011`) rather than executing new wet-lab assays; this measures causal recall without assay noise, and embedding `OA-BTL` before Step-3 dossier expansion will quantify prospective dark-genome hit rates. Second, $R = 3$ physical replicates per Parent cell (`D2-002`, `D2-008`) eliminated item-level pseudo-replication and revealed $2.8\\text{{--}}4.3\\times$ pathway convergence, while bounding single-disease exact permutation resolution at $2/\\binom{{6}}{{3}} = 0.10$ (strictly conservative Type II bias; $R \\ge 5$ enables $p < 0.01$). Third, 17k–32k per-call reasoning lengths under masked HPO profiles (`D2-004`–`D2-007`, `D2-012`) governed Experiment C-v4 at 630 non-truncated primary calls plus 240 Gemini/Grok evaluations; smaller sample size conservatively widens intervals on the subtle Arm $\\times$ Dose interaction ($p = 0.5948$) while preserving high power for DeepSeek dose collapse ($p = 0.0259$), literature footprint ($p = 0.0110$), and reasoning spin ($p = 2.02 \\times 10^{{-16}}$).

Fourth, automated Tier-2 grounding (`D2-003`, `D2-004`) queries official PubMed titles, abstracts, and MeSH across 1,254 cached PMIDs (2,628 slots) rather than paywalled full-text supplements; this errs conservatively on absolute ungrounded rates while remaining invariant across randomized Experiment B arms ($-11.9\\text{{ to }}-54.8\\text{{ pp}}, p \\le 0.00147$). Fifth, automated scanning of 11 dAMD and 24 ALS forbidden tokens (`D2-009`, `D2-010`) prevents explicit drug or gene recitation in blind runs but cannot erase unlabeled pretrained pathway priors, conservatively narrowing blind-versus-retrieval separation ($\\Delta J = +0.0556$ to $+0.1296$) and motivating our complementary 120-disease masked HPO perturbation benchmark. Embedding measurable audit sensors and zero-call deterministic rectifiers into agentic scientific pipelines ensures that autonomous discovery scales on verified evidence rather than uncalibrated reasoning spin.

{en_methods_nmi}## Figure Legends

{en_fig1_6}

## Extended Data

**Extended Data Figure 1. Working model and three-stage operational architecture of the STAR-Audit framework.**
{en_fig7_body}

{en_ext_tables}

{en_refs}
"""

    nmi_zh_core = f"""# 审计与纠偏自主人工智能科学发现中的推理、锦标赛与文献锚定失效
**(Nature Machine Intelligence 瘦身主投版 · 全文逐段对应中文审阅稿 | 英文原标题：Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery)**

**盛江涛 (Jiangtao Sheng)$^{{1,\\#,\\*}}$，刘雪儿 (Xueer Liu)$^{{1}}$, 林润敏 (Runmin Lin)$^{{1}}$, 孙翘楚 (Qiaochu Sun)$^{{1}}$, 陈晓璇 (Xiaoxuan Chen)$^{{1}}$, 李康生 (Kangsheng Li)$^{{1}}$, 陈伟强 (Weiqiang Chen)$^{{2,\\*}}$**

$^{{1}}$汕头大学医学院微生物学与免疫学教研室，中国广东省汕头市新陵路22号，邮编 515041

$^{{2}}$汕头大学医学院第一附属医院神经外科，中国广东省汕头市长平路57号，邮编 515041

$^{{\\text{{#}}}}$主要联系人（Lead contact）：盛江涛 (jtsheng@stu.edu.cn)

$^{{\\text{{*}}}}$通讯作者（Correspondence）：盛江涛 (jtsheng@stu.edu.cn; ORCID: 0000-0003-2438-7345)；陈伟强 (wqchen@stu.edu.cn; ORCID: 0000-0002-2612-0890)

## 摘要
自主多智能体系统结合假说生成、成对锦标赛与文献锚定推进科学发现，但测试时推理能否保障管线可信度仍未明确。本文提出六维可信度审计与零成本算法纠偏框架 **STAR-Audit**，覆盖忠实度、推理与记忆、位置公平性、稳定性、连贯性及校准。跨 136 种疾病对 GLM-5.3、DeepSeek-V4-Pro、Google Gemini-4-Argon-High 与 Gemini-3.8-Flash 以及 xAI Grok-4.7 与 Grok-4.7-Fast 的 11,818 次真实评估（3,718 万推理与输出 Token）审计揭示了测试时推理悖论：更深的思维链未能自我纠正管线偏倚。表面标识符检查判定 96.9%–100.0% 的方案 PubMed 编号有效，而语义核验揭露 11.9%–76.2% 为偏题“特洛伊木马引文”（源于单次打捞 35.8 个候选编号）。单向第一轮锦标赛 71.3% 的 A 槽位胜率压制了后置分桶通路（$\\chi^2 = 55.40$），第二轮锦标赛反转产生 8.9%–43.0% 翻转，且 23.3% 的失败孟德尔推断将 2.1% 深度激活的致病基因自我剪除。顺位校正 BTL、Platt 缩放、认识论门控与 `CoT-SRAD` 四大零调用确定性模块救回了实证靶点，削减无根据引文 11.9–54.8 个百分点并节省 86.2%–97.3% 引文推理算力，统一校准全部六款模型（$\\text{{ECE}} \\le 0.115$），并将孟德尔召回率相对提升 57.1%。

**关键词：** 自主科学发现；大语言模型；测试时推理；Bradley–Terry–Luce 锦标赛；引文忠实度；置信度校准；算法纠偏

## 引言
由大语言模型（LLMs）驱动的自主科学发现系统已从单步化学反应规划器 [1, 2]，演进为能够提出机制假说、通过成对锦标赛对候选方案排序并自动合成实验方案的多智能体架构 [3–5]。跨不同生物医学领域，主流发现引擎共享一套三阶段计算主干：多分桶候选构思、基于 Bradley–Terry–Luce（BTL）或 Elo 强度估计聚合的成对裁决 [6, 7]，以及文献锚定的实验方案生成 [8–10]。个别案例的湿实验命中展示了该架构的潜力 [3]，但一个根本性方法学问题仍悬而未决：在投入实验资源前，研究者如何核验智能体管线的内部推理、锦标赛排序与文献引证是否可信？

当前智能体人工智能（AI）设计普遍假设，扩展测试时推理 Token 能使前沿模型自我核验事实断言、抵御提示词框架干扰并校准不确定性。然而，机器学习与临床信息学的独立研究表明，无外部防护的语言模型仍易发生参考文献虚构（医学生成中达 21%–100% [11–15]）、成对位置偏倚 [7, 16]、预训练记忆背诵 [9, 17] 及口头过度自信 [18–20]。既有可靠性工具仅检查孤立表面，涵盖单句虚构检测 [20–22]、单任务基因集或因果智能体 [23–25]、区分数据路径上 LLM 调用与数据路径外确定性代码的可重复性准则 [26, 27]、临床摘要弃权框架 [28]、多智能体肿瘤共识 [29] 及高斯过程表征微调 [30]。2025–2026 年最新基准亦相继揭示了知识图谱探索智能体中未解决的证据冲突 [31]、分子泛化基准中的记忆泄露假象 [32]、结构化思维链锚定失效 [33]、角色提示仅改变修辞风格而非决策结构 [34]，以及自主多智能体工作流中的“貌似合理性谬误” [35]。但目前尚无框架将外部真值审计与零训练成本算法纠偏整合至完整的多阶段发现闭环（扩展数据表 1）。

为建立可泛化的可信自主发现方法学，我们在 SHA-256 密码学协议锁定与预先设定的 Benjamini–Hochberg 错误发现率控制（$q = 0.05$）[36] 下开发了 **STAR-Audit**（六维可信度审计与纠偏框架）。**STAR-Audit** 对六步发现级联全程部署六个正交审计维度：双层 NCBI PubMed 语义锚定（维度 1）、盲法与检索通路分离度及表型信息量（IC）扰动（维度 2）、第一轮锦标赛单向偏斜与第二轮锦标赛双向反转（维度 3）、重复运行 Top-5 稳定性对比 10,000 次判词表 Bootstrap 零分布（维度 4）、DeBERTa-v3 自然语言推理（NLI）矛盾审计（维度 5）以及样本外置信度校准（维度 6）。我们先在 GLM-5.3 与 DeepSeek-V4-Pro 上执行 9,130 次主调用（8,973 条白盒轨迹共 3,558 万内部推理 Token，占主输出 93.83%），继而在 Google Gemini（`Gemini-4-Argon-High` [`gemini-4-argon-high`] 与 `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]）与 xAI Grok（`Grok-4.7` 与 `Grok-4.7-Fast`）上开展 2,688 次跨生态评估，跨越 136 种疾病累计完成 11,818 次真实评估与 3,718 万推理及输出 Token（图 1A–D）。

将白盒思维链轨迹动力学与受控实验扰动相结合，本研究揭示了“**测试时推理悖论**”：无外部锚定的深度推敲单次打捞 35.8 个候选 PMID 以拼凑偏题特洛伊木马引文，在初始十分位将 88.4%–90.6% 注意力锚定于 A 槽位从而淘汰后置通路，并将早在 2.1% 推理深度激活的真致病基因自我剪除而替换为教科书综合征吸引子。从诊断迈向零调用修复，我们构建了四个数据路径外的确定性算子：顺位校正 BTL（`OA-BTL`）结合 NLI 不一致中性化、留一运行（`LORO`）Platt 缩放、双层认识论引文门控以及思维链流恢复与吸引子去混杂（`CoT-SRAD`）。四大模块在不增加任何一次 LLM 调用的前提下救回实证生物学靶点、统一校准六款前沿模型、将孟德尔基因召回率相对提升达 57.1%，并将引文推理算力削减 86.2%–97.3%。

[INSERT FIGURE 1 ABOUT HERE]

## 结果

### 多模块实验架构、算力账本与验证性记分卡
我们在分析前通过 SHA-256 哈希锁定了全部提示词、盲法禁用词表、疾病通路金标准及 6 成员验证性假设族（$q = 0.05$；图 1A）。模块 1 采用 $2 \\times 2 \\times 3$ 析因设计执行了 12 次六步端到端主发现运行（7,890 次调用），将干性年龄相关性黄斑变性（dAMD；横跨补体、基质、脂质与视网膜色素上皮 [RPE] 吞噬清除多轴病理 [37–44]）和肌萎缩侧索硬化症（ALS；TDP-43 隐蔽剪接主导并伴 SOD1 与自噬异常 [45–48]）交叉配对严格盲法构思（补充说明 Note 1）与注入真实 PubMed 摘要的检索增强模式（每单元格 $R = 3$ 次重复）。每次运行依次完成 30 候选多分桶构思（第 1 步）、300 对单向第一轮锦标赛 BTL 初筛至 Top 10（第 2 步）、靶点档案扩写（第 3 步）、45 对候选由三类裁判（`SCIENCE`、`METHODS`、`NOVELTY`）正反双向评估 270 份裁决的第二轮锦标赛（第 4 步）、Top-5 终选（第 5 步；补充表 S1 与补充表 S2）及 30 槽位实验方案引文合成（第 6 步；共 360 槽位）。模块 2（实验 B；跨 14 个临床专科共 396 次调用、1,260 槽位；补充表 S3）将引文生成随机分入 `as_discovered`、`abstain_probe` 与 `gated` 三臂。模块 3（实验 C-v4；GLM-5.3 与 DeepSeek-V4-Pro 记录 804 次调用，630 次未截断调用纳入广义线性混合模型 GLMM；补充表 S4）对 120 种掩码人类表型本体库（HPO [49]）孟德尔病施加 0%、25%、50% 信息量（IC）删减（对比 `del_topIC` 与 `del_lowIC_matched`）。

主框架研究（含 40 次证实 $\\text{{drift}} = 0.000$ 的温度-0 漂移金丝雀调用）共执行 9,130 次真实调用，消耗 574 万输入与 3,792 万输出 Token，其中内部思维链占 3,558 万 Token（**93.83%**），可见回答占 234 万 Token（图 1B）。结合 Google Gemini（114.99 万输出/推理 Token，含缓存总计 1,205 万 Token）与 xAI Grok（45.09 万原生推理 Token）的 2,688 次跨生态评估，全研究涵盖 **11,818 次评估与 3,718 万推理及输出 Token**。尽管开启 `effort=high`（`max_tokens=32,768`），6 个预先设定验证性零假设中仍有 3 个经 BH-FDR 校正后被拒绝（成员 1 引文门控 $q = 0.0310$，成员 5 跨运行不稳定性对比判词表 Bootstrap 零分布 $q = 0.0012$，成员 6 校准斜率 $q = 0.0401$）；成员 4（盲法与检索首位基因分离度）达离散置换理论下界（单疾病 $p = 0.10$，合并 $p = 0.0561, q = 0.0841$），成员 2–3 则揭示了 DeepSeek-V4-Pro 对高 IC 删减的显著敏感性（$p = 0.0259$）及双厂商一致的预训练文献丰度效应（图 1C, D；扩展数据表 2）。

### 双层锚定核验揭露特洛伊木马引文并验证认识论门控
常规管线检查仅核实输出 PMID 是否存在于 NCBI Entrez [11, 14]。我们构建了实时双层 NCBI E-utilities 核验器（`esummary`/`efetch`；在冻结的 200 对自校准基准上灵敏度与特异度均为 100.0%；补充说明 Note 2），依次核验第一层（Tier-1）编号存在性与第二层（Tier-2）断言同官方标题、摘要及医学主题词（MeSH）的语义重叠。在 GLM-5.3 的 360 个主运行第 6 步槽位与 420 个实验 B 无防护 `as_discovered` 槽位中，虚构假 PMID 极少（**1.67%** [6/360] 与 **3.10%** [13/420]），表面 Tier-1 合格率达 98.33% 与 96.90%（图 2A）。然而 Tier-2 语义审计揭露，主运行 **56.67%**（204/360）与实验 B `as_discovered` **54.29%**（228/420）的引文实为“**特洛伊木马引文**”，即将无关疾病的高被引真实 PubMed 论文挂靠至无支撑的 dAMD、ALS 或临床断言，使总无根据引文率高达 **58.33%** 与 **57.38%**（图 2A）。当第 6 步引文槽位仍强制输出时，第 1 步注入 PubMed 摘要（`retrieval` 臂）无法阻止下游张冠李戴（dAMD 与 ALS 检索臂无根据率为 `54.44%` 与 `66.67%`，盲法臂为 `47.78%` 与 `64.44%`；图 2B）。

[INSERT FIGURE 2 ABOUT HERE]

跨 14 个临床专科的随机对照实验 B 证明，架构级门控在消解木马引文的同时截断了内部记忆打捞（图 2C, D）。相比 `as_discovered`（0% 弃权，57.38% 无根据）与 `abstain_probe`（63.81% 弃权，18.10% 无根据），严格认识论门控（`gated`，参数弃权率 95.24%）彻底清零了虚构 PMID（**0.00%**，0/420；验证性成员 1 配对风险差 $\\text{{RD}} = +3.10\\%$，95% CI $[1.43\\%, 4.76\\%]$，Wilcoxon $p = 0.01032, q_{{\\text{{BH}}}} = 0.03096$），并将无根据引文率降至 **2.86%**（12/420；$-54.52\\text{{ pp}}$，95% CI $[45.00\\%, 62.86\\%]$，$p = 0.00097$，14/14 领域一致改善；图 2C）。对全部 380 条实验 B `reasoning_content` 白盒轨迹的剖析揭示了根因：`as_discovered` 下模型单次平均尝试 **35.82 个不同 7–8 位候选 PMID**（中位数 32.0），伴随 **390.32 次犹豫标记** 与 **198.53 次年份锚点**，按年代前缀猜测必然碰撞同年发表的无关真论文。`abstain_probe` 单次仍打捞 **25.37 个候选 PMID**，而 `gated` 将打捞截断至 **5.00 个/次**（中位数 3.0；Kruskal–Wallis $H = 201.17, p = 2.07 \\times 10^{{-44}}$），犹豫空转降低 10.5 倍（`390.32 -> 37.16`；图 2D）。

### 多尺度生物学等价收敛与 120 种疾病 HPO 梯度扰动
正如词元级熵会混淆同义不同词的表述 [20]，且精确基因重叠不足 $<1\\%$ 的衰老转录组模块（`SenMayo`、`Fridman`、`CellAge`）实则捕获同一细胞状态 [50] 一样，仅靠精确人类基因组组织基因命名委员会（HGNC）基因交集会将同通路效应分子的多样性误判为不稳定。跨首位靶基因、档案全基因模块与附录 A 经典通路轴评估 12 次主运行表明，**100.0%（12/12）的运行在 Top-5 中恢复了 2 至 4 条疾病金标准通路轴**（48/60 [80.0%] 直接命中核心金标准轴，12/60 [20.0%] 命中保守固有免疫/自噬轴，非生物诱饵为 0；图 3A）。沿 **基因 $\\to$ 模块 $\\to$ 通路轴** 聚合带来 **2.8 倍至 4.3 倍收敛度跃升**。在单吸引子 ALS 中，6/6 次运行一致收敛于 TDP-43 隐蔽外显子剪接轴（`STMN2/UNC13A` [45–48]，盲法运行经 7 次禁用词自动重写从第一性原理重构该轴），检索臂则特异吸纳临床试验毗邻的 `IL-2/FOXP3` 与 `C1QA/C3` 轴（$\\Delta J_{{\\text{{lead}}}} = +0.1296$，精确置换 $p = 0.10$），使臂内相似度从 $J_{{\\text{{lead}}}} = 0.2037$ 跃升至 $J_{{\\text{{axis}}}} = 0.5722$（**$2.81\\times$**；图 3B）。在多轴辐射的 dAMD [37, 38, 51] 中，各运行在补体/Bruch 膜、炎症小体、铁死亡与 cGAS-STING 等价类内采样不同效应节点（`CFH`、`C3`、`MASP1/2`、`SERPING1`、`SULF2`），使臂内相似度从 $J_{{\\text{{lead}}}} = 0.0926$（$\\Delta J = +0.0556, p = 0.10$；双疾病合并 $p = 0.0561, q_{{\\text{{BH}}}} = 0.0841$）跃升至 $J_{{\\text{{axis}}}} = 0.3944$（**$4.26\\times$**；图 3B）。

[INSERT FIGURE 3 ABOUT HERE]

在涵盖 120 种罕见孟德尔病、630 次掩码 HPO 调用的实验 C-v4（GLM-5.3 359 次，DeepSeek-V4-Pro 271 次；图 3C, D）中，0% 删减基线 Top-10 致病基因召回率（`hit@10`）在 GLM-5.3 上为 31.75%（40/126），DeepSeek-V4-Pro 上为 25.51%（25/98）。删减高 IC 诊断表型（`del_topIC` 0%、25%、50%）使 DeepSeek-V4-Pro 呈剂量依赖坍缩（**28.3% $\\to$ 22.6% $\\to$ 14.3%**，校正文献丰度 $\\hat{{\\beta}}_{{\\text{{dose}}}} = -5.560, p = 0.0259$），GLM-5.3 较平坦（`34.5% -> 31.5% -> 30.6%`；合并 $\\hat{{\\beta}}_1 = -0.573, p = 0.2191, q_{{\\text{{BH}}}} = 0.2629$；交互项 $p = 0.5948$）。预训练 PubMed 文献丰度在双模型上均显著主导召回率（高对比低丰度：GLM-5.3 **38.2% 对比 23.2%**，$p = 0.0110$；DeepSeek-V4-Pro **24.4% 对比 16.9%**；合并 **32.3% 对比 20.5%**；图 3C）。表型特异性降级且预测失败（`hit@10 = 0`）时，两款模型跨无关疾病反复回退至教科书高频综合征吸引子，依次为 `CHD7`（全调用 35 次假阳性；失败试验中跨 10 种非 CHARGE 病出现 28 次）、`KMT2D`（31 次）、`FOXG1`（28 次）、`ZEB2`（24 次）、`CEP290`（24 次）、`LMNA`（22 次）、`KANSL1`（19 次）与 `TCF4`（18 次；图 3D）。

对全部 630 条 `reasoning_content` 流的白盒追踪揭示了 **“2.1% 瞬时识别定律”**。在命中调用（`hit@10 = 1`）中，真致病基因在 GLM-5.3 上于思维链相对深度中位数 **$t = 0.0214$（2.14%，IQR $1.23\\%\\text{{--}}6.69\\%$）**、在 DeepSeek-V4-Pro 上于 **$t = 0.0206$（2.06%，IQR $1.35\\%\\text{{--}}3.64\\%$）** 即被首次激活。在已完成推理的假阴性调用（$n = 236$）中，高达 **23.31%（55/236：GLM-5.3 为 23.84% [36/151]，DeepSeek-V4-Pro 为 22.35% [19/85]）** 早已在思维链前段激活真基因（中位 $t = 0.113$ 与 $0.105$），却在后续长推敲中将其**自我剪除**并替换为综合征吸引子（`CHD7`、`KMT2D`、`FOXG1`、`ANKRD11`、`ZEB2`）。在触及 32,768 Token 截断的调用（$n = 228$）中，亦有 **33.33%（76/228；DeepSeek-V4-Pro 达 43.08% [56/130]，中位 $t = 0.0268$）** 在耗尽预算前已识别出真基因。

### 锦标赛位置偏倚驱动通路灭绝与动机性推理合理化
对 3,202 次双向第二轮锦标赛裁决（12 次运行共 1,601 个候选对）的审计显示，**43.04%**（689/1,601；各运行 25.2%–63.9%）在顺序反转时发生胜者翻转，其中 **96.95%**（668/689）属于倒向 A 槽位的首因翻转（双侧二项检验 $p = 4.63 \\times 10^{{-168}}$；`NOVELTY` 46.46%，`METHODS` 42.59%，`SCIENCE` 40.04%；图 4A）。在单向第一轮锦标赛初筛（3,594 次有效调用）中，**A 槽位赢下 71.29%（2,562/3,594）** 的比较（$p = 4.37 \\times 10^{{-148}}$）。由于第 1 步按 `第 1 分桶 [M00–M09]`（细胞内源）、`第 2 分桶 [M10–M19]`（细胞间信号）与 `第 3 分桶 [M20–M29]`（细胞外基质、补体、血管屏障）顺序编号并以 $a < b$ 排列配对 $(M_a, M_b)$，标准未校正 BTL 造成了严重的 **索引顺位通路灭绝**（图 4B）：Top-10 晋级席位从均匀期望 `40 : 40 : 40` 扭曲为 **`78 : 26 : 16`**（`65.0% : 21.7% : 13.3%`，$\\chi^2 = 55.40, p = 9.33 \\times 10^{{-13}}$），在进入档案扩写前便淘汰了 `TIMP3/MMP9`、`ABCA1/LIPC`、`CD59` 与 `GAS6/MERTK` 等实证通路。

[INSERT FIGURE 4 ABOUT HERE]

将 DeBERTa-v3 NLI 交叉编码器 [52] 应用于 480 对去别名化 `SCIENCE` 裁判推理依据对（维度 5）发现，首因翻转配对（$n = 240$）较一致配对的 **方向性自相矛盾率激增 2.5 倍**（$P_{{\\text{{contra}}}} > 0.75$：**25.42% 对比 10.00%**，Fisher 精确检验 $p = 1.15 \\times 10^{{-5}}$），**严格双向矛盾率激增 3.4 倍**（**7.08% 对比 2.08%**，$p = 0.0142$；图 4C），通过动机性思维链盛赞任何居于 A 槽位的方案。跨第 1、3、4、6 步全部 17,990 条生物实体断言（1,766 对跨阶段配对；补充表 S5），DeBERTa-v3 检出 **167 对方向性矛盾（94.56/千对）** 与 **51 对严格双向矛盾（28.88/千对）**，其中 **43.14%（22/51）** 静默写入了最终 Top-5 实验方案（图 4D）。

### 判词表稳定性、置信度失准与测试时推理悖论
为定位跨运行 Top-5 靶基因分歧的根源（维度 4），对每次运行 270 份第二轮锦标赛判词表执行 10,000 次参数化 Bootstrap 重采样（共 120,000 次 Hunter-MM BTL 拟合）证实判词聚合内部高度稳定（dAMD 均值 **0.7389**，ALS **0.7783**），在所有单元格显著拒绝裁决噪声零假设（**验证性成员 5**：$p = 0.00020, q_{{\\text{{BH}}}} = 0.00120$；图 5A），将分歧定位于上游第 1 步构思与单向第一轮初筛。在维度 6 下，口头置信度相对于锦标赛存活显著失准（**验证性成员 6**：第 1 步校准斜率 $\\hat{{\\beta}}_{{\\text{{cal}}}} = 0.655, \\text{{SE}} = 0.148, p = 0.02004, q_{{\\text{{BH}}}} = 0.04009$；主运行汇总平均预测置信度 **47.2%** 对比实际存活率 **25.0%**，$\\text{{ECE}} = 0.222$，Brier $0.216$；实验 C-v4 在 GLM-5.3 与 DeepSeek-V4-Pro 上的 $\\text{{ECE}}$ 达 $0.351$ 与 $0.244$；图 5B）。

[INSERT FIGURE 5 ABOUT HERE]

全部 9,130 次主调用的逐次遥测综合揭示了 **“测试时推理悖论”的三种表现形式**，即更长的思维链反而伴随更严重的偏倚与错误（图 5C, D）。在 **悖论 1** 中，7,592 条锦标赛轨迹剖析显示前十分之一阶段（$t \\in [0, 0.1]$）**88.41%（Tournament I）与 90.59%（Tournament II）** 的候选提及完全聚焦于 A 槽位；首因翻转的第二轮锦标赛调用比一致调用消耗显著 *更多* 推理 Token（**中位数 2,410.5 对比 2,336.0 tokens**，Mann–Whitney $p = 0.0254$；累计烧掉 **360 万个推理 Token** 合理化翻转）。在 **悖论 2** 中，无防护 `as_discovered` 引文调用耗费 **中位数 11,798.5 个推理 Token** 打捞候选 PMID，远超 `abstain_probe` 的 **8,862.0** 与 `gated` 的 **1,132.0**（图 5C）。在 **悖论 3** 中，失败的孟德尔推断（`hit@10 = 0`）在 GLM-5.3 上多消耗 **1.70 倍推理 Token**（**28,959.0 对比 17,071.5**，$p = 2.02 \\times 10^{{-16}}$），在 DeepSeek-V4-Pro 上多消耗 **1.39 倍**（**27,398.0 对比 19,671.0**，$p = 1.43 \\times 10^{{-5}}$；图 5D；运行上限台账见补充表 S6），且随 HPO 信息删减单调上升（`23,040 -> 25,650 -> 26,809` tokens）。

### 四大零成本算法算子修复排序、文献锚定、概率校准与自我剪除
我们将六维诊断传感器转化为四个确定性、零额外 LLM 调用的纠偏算子（图 6A–D；扩展数据表 2）。**模块 1（`顺位校正 BTL` + `NLI 不一致中性化`）** 基于 $L_2$ 惩罚似然（$\\lambda = 0.01$；补充说明 Note 3）建立 $P(i \\text{{ 击败 }} j \\mid A=i, B=j) = \\sigma(\\theta_i - \\theta_j + \\gamma)$，在全部 12 次运行中估计出严格为正的 A 槽位首因截距（$\\hat{{\\gamma}}_{{\\text{{T1}}}} \\in [0.592, 1.724]$，优势比 $1.81\\text{{--}}5.61\\times$；$\\hat{{\\gamma}}_{{\\text{{T2}}}} \\in [1.296, 2.640]$，优势比 $3.66\\text{{--}}14.02\\times$；图 6A）。剥离 $\\hat{{\\gamma}}_{{\\text{{T1}}}}$ 将第一轮锦标赛分桶 $\\chi^2$ 失真削减 **72.83%**（`78 : 26 : 16` $\\to$ **`60 : 31 : 29`**，$\\chi^2 = 55.40 \\to 15.05$），使 **第 3 分桶通路存活率提升 +81.25%**（图 4B，图 6C）。锚定正交人类遗传学、动物模型与临床试验金标准 [53] 证实，顺位校正 BTL 救回了九条因高比例落入 B 槽位（71.4%–100.0% 居 B 槽位；逐运行暴露明细见方法与补充表 S2）而被淘汰的核心致病通路：dAMD 中的 `GAS6/PROS1–MERTK` RPE 胞葬吞噬（`第 11 -> 第 7 名` [39, 54–57]）、`TIMP3/MMP2/MMP9` 基质周转（`第 15 -> 第 8 名`）、`ABCA1/LIPC/CETP` 胆固醇外流（`第 15 -> 第 6 名`）、`CD59` 膜攻击复合物抑制（`第 11 -> 第 5 名` [37, 40, 58–60]）与 `MTTP/APOB100` 脂蛋白玻璃膜疣生物发生（`第 12 -> 第 6 名` [42, 61]），以及 ALS 中的 `MMP9/LAMA1` 去神经易损性（`第 13 -> 第 6 名` [62]）、`CCS/ATP7A` apo-SOD1 铜装载（23/23 次全居 B 槽位仍从 `第 15 -> 第 10 名` [63]）、`MCT1/SLC16A1` 少突胶质乳酸穿梭（`第 11 -> 第 7 名` [64]）与 `C1QA/C3` 补体突触修剪（`第 13 -> 第 10 名` [65]；图 6B）。对 689 对翻转的第二轮锦标赛配对执行平局中性化（100% 清除位置偏倚）更新了 7/12 次运行的 Top-5 排序。

[INSERT FIGURE 6 ABOUT HERE]

**模块 2（`LORO Platt 缩放`）** [18, 66] 在留入运行上拟合样本外双参数逻辑映射，将主运行 $\\text{{ECE}}$ 降低 **87.64%**（$0.2221 \\to 0.0274$ [$0.222 \\to 0.027$，$-87.8\\%$]，校准准确度 **97.3%**；Brier $0.216 \\to 0.161$），并将实验 C-v4 $\\text{{ECE}}$ 在 GLM-5.3 上降低 **89.46%**（$0.351 \\to 0.037$）、在 DeepSeek-V4-Pro 上降低 **82.79%**（$0.244 \\to 0.042$；图 5B）。将模块 1、2 与 **模块 3（`双层认识论引文门控`）** 整合，在零额外调用下将四支柱综合可信度得分沿帕累托前沿从 **47.7%**（单次引文 `11.80k` 中位 CoT tokens）推升至 **89.6%（+41.9 个百分点）**，同时将引文算力降至 **1.13k tokens/次（节省 86.2%）**（图 6C, D）。**模块 4（`CoT-SRAD`）** 基于零标签泄露的留一疾病预测频次（$\\text{{df}}_{{\\text{{LODO}}}} \\ge 12$）识别泛滥综合征吸引子，并从当次调用 `reasoning_content` 最早激活的非吸引子候选中回填槽位，在全部 630 次实验 C-v4 调用中净挽救 **+36 个真致病基因发现**（`26.35% -> 32.06%`，精确 McNemar $p = 7.07 \\times 10^{{-6}}$），将 DeepSeek-V4-Pro 召回率相对提升 **+57.14%**（`20.66% [56/271] -> 32.47% [88/271]`，净增 +32 次，$p = 9.43 \\times 10^{{-7}}$；GLM-5.3 `30.64% -> 31.75%`；图 3C）。

### 跨生态系统泛化验证：美国前沿 Google Gemini 与 xAI Grok 多层级审计
为验证跨美国商业架构及同家族高低推理层级的泛化性，我们在 Google **`Gemini-4-Argon-High`**（`gemini-4-argon-high`）与 **`Gemini-3.8-Flash`**（`gemini-3.8-flash-tiered`；1,344 次评估，1,149,908 输出/推理 Token）及 xAI **`Grok-4.7`**（`grok-4.7`，自适应高推理）与 **`Grok-4.7-Fast`**（`grok-4.7-build-fast`，快速低推理；1,344 次评估，450,879 原生推理 Token；补充表 S7）上执行了 2,688 次匹配评估。在场景 1（第二轮锦标赛 dAMD/ALS 配对裁决；720 次独立会话盲法裁决加 720 次联合上下文对照）中，盲法反转在 `Gemini-4-Argon-High` 上翻转 **11.11%**（10/90），在 `Gemini-3.8-Flash` 上达 **26.67%**（24/90；高出 $2.4\\times$，呈 54.44% B 槽位近因偏倚），在 `Grok-4.7` 上为 **13.33%**（12/90），在 `Grok-4.7-Fast` 上为 **8.89%**（8/90；图 4A）。印证悖论 1 的是，旗舰 `Grok-4.7` 的翻转率（`13.33% 对比 8.89%`）与分项-胜负倒挂率（`10.00% 对比 6.67%`）均高于 `Grok-4.7-Fast`；同会话联合上下文对照将四模型翻转人为掩盖至 **0.00%**；而 `OA-BTL`（$\\tau = 0.644\\text{{--}}0.956$）同时校正了首因、近因与对称翻转，救回了 dAMD（`C08`/`C06`）与 ALS（`C02`）前三靶点。

在场景 2（跨 14 个临床专科实验 B；1,008 槽位）中，四款美国模型在无防护 `as_discovered` 下的 PMID 均具 **98.81%–100.0% Tier-1 真实存在率**，但 Tier-2 核验揭露 `Gemini-4-Argon-High` 中 **11.90%**（10/84）、`Gemini-3.8-Flash` 中 **76.19%**（64/84；总无根据率 77.38%）、`Grok-4.7` 中 **29.76%**（25/84）及 `Grok-4.7-Fast` 中 **33.33%**（28/84；总无根据率 34.52%）均为特洛伊木马引文（图 2D）。强制 `gated` 门控将无根据引文率降至 `Gemini-4-Argon-High` 的 **0.00%**（$-11.90\\text{{ pp}}, p = 0.00147$）、`Gemini-3.8-Flash` 的 **22.62%**（$-54.76\\text{{ pp}}, p = 1.03 \\times 10^{{-12}}$）、`Grok-4.7` 的 **0.00%**（$-29.76\\text{{ pp}}, p = 7.29 \\times 10^{{-9}}$）与 `Grok-4.7-Fast` 的 **0.00%**（$-34.52\\text{{ pp}}, p = 1.99 \\times 10^{{-10}}$），并使 Grok 原生引文推理 Token 骤降 **30 倍以上**（`10,072/12,284 -> 332/330` tokens；**削减 96.7%–97.3%**）。

在场景 3（20 种孟德尔病在 0%、25%、50% `del_topIC` 下共 240 次掩码 HPO 评估）中，`Gemini-4-Argon-High` 总体 `hit@10` 达 **65.00%**（39/60，较 `Gemini-3.8-Flash` 的 **26.67%** [16/60] 高出 $2.4\\times$），而 `Grok-4.7`（`45.0% -> 30.0% -> 20.0%`；总体 31.67%）在 50% 删减下因共享吸引子捕获（`VARS2`、`POLG`、`FBXL4`、`CEP290`）反而低于 `Grok-4.7-Fast`（`40.0% -> 35.0% -> 35.0%`；总体 36.67%；图 3C）。样本外 LODO Platt 缩放在 `Gemini-3.8-Flash`、`Grok-4.7` 与 `Grok-4.7-Fast` 上分别将 $\\text{{ECE}}$ 降低 **86.20%**（$0.5423 \\to 0.0749$）、**54.78%**（$0.2292 \\to 0.1036$）与 **50.72%**（$0.1652 \\to 0.0814$），并将原生近似校准的 `Gemini-4-Argon-High`（原始 $\\text{{ECE}} = 0.0797$；Platt 平均概率 **65.36% 对比 65.00%** 准确率，$\\text{{ECE}} = 0.1145$）连同全部六款模型统一收敛于 $\\text{{ECE}} \\le 0.115$ 带内（图 5B）。

## 讨论
跨越四大主权前沿模型家族、六个版本化算力层级与 136 种疾病共 11,818 次真实评估（3,718 万推理及输出 Token），**STAR-Audit** 为自主科学发现确立了两条核心准则（扩展数据图 1）。第一，扩展测试时思维链算力无法自动纠正结构性管线脆弱性；当提示词强制要求无核验引文槽位、单向未平衡成对槽位或残缺表型输入时，长推理单次打捞 35.8 个候选 PMID、将 88.4%–90.6% 初始注意力锁定于 A 槽位，并将早在 2.1% 深度激活的真致病基因自我剪除。第二，在阶段跃迁处部署轻量级数学审计传感器后，四个零调用确定性纠偏算子（`OA-BTL`、`LORO Platt`、`认识论引文门控` 与 `CoT-SRAD`）即可在零边际 LLM 成本下修复锦标赛排序、救回受压制通路与被剪除的孟德尔基因、统一概率校准并消除虚构文献。

从机制上看，占主输出 93.83% 的内部思维链是一把双刃放大器。当任务受充分约束锚定时（如重构 ALS `TDP-43/STMN2/UNC13A` 隐蔽剪接或完整高丰度 HPO 表型），推理快速收敛（`17.1k–19.7k` tokens）；但在约束不足或位置偏斜状态下，推理跨四大生态系统异化为参数搜索引擎与动机性辩护者。不同于早期捏造假编号的非推理模型 [11–13]，前沿推理模型按发表年代前缀打捞真实偏题论文（`11.9%–76.2%` 木马引文率），呼应了临床摘要中无锚定推理放大幻觉而弃权门控遏制编造的规律 [28]。同样，翻转裁决消耗 *更多* 推理 Token（$p = 0.0254$）、伴随 $2.5\\text{{--}}3.4\\times$ NLI 自相矛盾激增（$p = 1.15 \\times 10^{{-5}}$）且旗舰 `Grok-4.7` 分项倒挂高于 `Grok-4.7-Fast` 的现象，进一步拓展了近期肿瘤学评估中单纯提示词无法克服思维链锚定 [33] 且角色提示仅改变修辞风格而非决策结构 [34] 的结论。在 50% HPO 删减下，冗长推敲用高先验教科书吸引子覆盖了 2.1% 深度的早期正确激活，解释了为何 `CoT-SRAD` 能直接从原始推理流中夺回 +36 个真基因发现（DeepSeek-V4-Pro 相对提升 +57.1%）。

**STAR-Audit** 的六个维度各自捕获互不重叠的失效表面：100% 通路轴精度（维度 2）与高内部判词表稳定性（维度 4）可与 58.3% 木马引文（维度 1）及 22.2% 过度自信误差（维度 6）并存，而引文门控虽能修复忠实度却无法阻止第一轮锦标赛第 3 分桶灭绝（维度 3）或跨阶段 NLI 矛盾（维度 5）。在架构定位上，**STAR-Audit** 弥合了多智能体发现平台（`Robin` [3]、`Co-Scientist` [4]、`DeepEvidence` [31]、`HealthFlow` [35]、`EvoMDT` [29] 及高斯过程微调优化器 `GOLLuM` [30]）与去偏倚可靠性基准（`CleanSplit` [32]、语义熵 [20]、`SelfCheck-Eval` [22] 及数据路径外确定性准则 [26, 27]）。将假说构思与科学裁决保留在 *数据路径上*，同时将排序去偏倚、NLI 过滤、校准、文献核验与轨迹恢复剥离至 *数据路径外*，无需微调模型权重即化解了多智能体“貌似合理性谬误” [35]，为临床前投入前提供了类似 `TRIPOD+AI` [67] 的定量治理标准。

五项方法学边界（挂钩 SHA-256 治理台账 `D2-001`–`D2-012`；补充表 S6）界定了潜在偏倚方向与前瞻拓展路径。第一，本研究在 dAMD、ALS 与 120 种孟德尔病中以正交人类遗传学（GWAS/OMIM）、动物模型与临床试验真值验证通路拯救（`D2-001`、`D2-009`、`D2-011`），未开展新湿实验；这在免受实验体系噪声干扰下测量了因果召回率，未来在第 3 步档案扩写前嵌入 `OA-BTL` 可直接量化未知暗基因组靶点的湿实验命中增益。第二，主运行每单元格 $R = 3$ 次物理隔离重复（`D2-002`、`D2-008`）消除了条目级伪重复并揭示 $2.8\\text{{--}}4.3\\times$ 通路收敛，但单疾病精确置换分辨率受限于 $2/\\binom{{6}}{{3}} = 0.10$（严格偏向保守第二类错误；扩展至 $R \\ge 5$ 可达 $p < 0.01$）。第三，掩码 HPO 单次 17k–32k 推理长度（`D2-004`–`D2-007`、`D2-012`）使实验 C-v4 治理于 630 次未截断主调用加 240 次 Gemini/Grok 评估；样本量缩减保守拓宽了微弱“臂 $\\times$ 剂量”交互项区间（$p = 0.5948$），但仍具充足把握度检出 DeepSeek 剂量坍缩（$p = 0.0259$）、文献丰度效应（$p = 0.0110$）与推理空转（$p = 2.02 \\times 10^{{-16}}$）。

第四，自动化 Tier-2 核验（`D2-003`、`D2-004`）跨 1,254 个缓存 PMID（2,628 槽位）检索官方 PubMed 标题、摘要与 MeSH 而非付费墙补充全文；该标准在绝对无根据率上偏向保守严格，但对随机对照实验 B 各臂完全对称，不影响配对风险降幅（$-11.9\\text{{ 至 }}-54.8\\text{{ pp}}, p \\le 0.00147$）。第五，对 11 个 dAMD 与 24 个 ALS 禁用词的自动扫描重写（`D2-009`、`D2-010`）消除了盲法运行中的显式药物与基因背诵，但无法抹除预训练权重编码的无标签通路先验，保守收窄了常见病盲法与检索分离度（$\\Delta J = +0.0556$ 至 $+0.1296$），这也正是我们配对 120 种掩码罕见病 HPO 扰动基准的原因。将可测量的审计传感器与零调用确定性纠偏算子嵌入智能体科研管线，能够确保自主科学发现在经核验的证据而非未经校准的推理空转之上稳健扩展。

{zh_methods_nmi}## 图注

{zh_fig1_6}

## 扩展数据

**扩展数据图 1（Extended Data Figure 1）. STAR-Audit 框架的工作模型与三阶段运行架构示意图。**
{zh_fig7_body}

{zh_ext_tables}

{zh_refs}
"""

    (BASE / "MANUSCRIPT_NMI_v1.0.md").write_text(nmi_en_core, encoding="utf-8")
    (BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md").write_text(nmi_zh_core, encoding="utf-8")
    (BASE / "STAR-Audit_手稿全文中文版_审核稿.md").write_text(nmi_zh_core, encoding="utf-8")
    print("[OK] Wrote MANUSCRIPT_NMI_v1.0.md & STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md")


def build_nmi_cover_letters() -> None:
    cl_nmi_en = """# Cover Letter — *Nature Machine Intelligence*

**Date:** October 29, 2026
**To:** Dr. Liesbeth Venema, Chief Editor, and the Editorial Team, *Nature Machine Intelligence*
**Manuscript Title:** Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery
**Article Type:** Article (4,000-word Main Text; 6 Main Figures; 1 Extended Data Figure; 2 Extended Data Tables)
**Code & Frozen Protocol Repository:** https://github.com/SJT503/SDL-dAMD | **Zenodo Telemetry Archive:** DOI 10.5281/zenodo.20574265

Dear Dr. Venema and Editorial Team of *Nature Machine Intelligence*,

Please find enclosed our manuscript entitled **"Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery"** for consideration as an original **Article** in *Nature Machine Intelligence*.

Autonomous multi-agent AI systems increasingly couple large language model (LLM) ideation with pairwise Bradley–Terry–Luce (BTL) tournaments and literature synthesis to automate scientific hypothesis generation (*Nature* 2026; *Nat. Mach. Intell.* 2024, 2026). Recent studies in *Nature Machine Intelligence* have advanced knowledge-graph-guided multi-agent evidence synthesis (Wang et al., `DeepEvidence`, 2026), Gaussian-process representation fine-tuning for calibrated experimental optimization (Ranković et al., `GOLLuM`, 2026), and bias-deconfounded benchmarking to separate memorization from generalization (Graber et al., `CleanSplit`, 2025). Yet a fundamental machine-intelligence question remains open: **does scaling test-time chain-of-thought reasoning make multi-agent scientific discovery pipelines self-verifying, or does unanchored test-time compute amplify structural ranking, grounding, and calibration failures—and can those failures be rectified algorithmically at zero inference cost?**

Here we introduce **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification) and audit **11,818 live evaluations (37.18 million reasoning and output tokens)** across **136 biomedical disease contexts**, spanning four sovereign frontier model ecosystems and six versioned reasoning tiers (`GLM-5.3`, `DeepSeek-V4-Pro`, Google `Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`], and xAI `Grok-4.7` and `Grok-4.7-Fast`) under SHA-256 protocol locking and Benjamini–Hochberg false discovery rate control ($q = 0.05$). Our work contributes three advances directly aligned with the core scope of *Nature Machine Intelligence*:

1. **Mechanistic Law of the Test-Time Reasoning Paradox:** White-box trajectory analysis across 8,973 primary `reasoning_content` streams (35.58 million reasoning tokens; 93.83% of primary output) and multi-tier Gemini/Grok reasoning logs reveals why deeper unanchored deliberation fails to self-correct. Under mandatory citation slots, reasoning models dredge **35.8 candidate PMIDs per call** by chronological prefix to attach real, unrelated papers to unsupported claims (**11.9%–76.2% Trojan horse citations** across all four ecosystems despite **96.9%–100.0%** surface identifier validity). In pairwise judging, **88.4%–90.6%** of Decile-1 attention locks onto Slot A, driving a **71.3%** Tournament I Slot-A win rate ($p = 4.37 \\times 10^{-148}$) that extinguishes late-indexed biological pathways ($\\chi^2 = 55.40$) and causes **8.9%–43.0%** blinded reversal flips in Tournament II accompanied by a **$2.5\\times$ surge** in DeBERTa-v3 NLI self-contradiction. Under masked Mendelian phenotypes, models obey a **2.1% Instant-Recognition Law** yet **self-prune the true causal gene in 23.3% of failed inferences** during prolonged deliberation in favor of high-prior textbook attractors.
2. **Off-the-Data-Path Zero-Call Algorithmic Rectification:** Without weight fine-tuning or a single additional LLM call, four deterministic operators rectify all three failure surfaces. **Order-Adjusted BTL** with NLI-discordance neutralization simultaneously removes primacy, recency, and symmetric positional biases, cuts Tournament I bucket skew by **72.8%** (`+81.3%` Bucket-3 pathway survival), and rescues human-genetics-validated targets (`GAS6/MERTK`, `TIMP3`, `ABCA1`, `CD59`, `MMP9`). **Leave-One-Run-Out Platt scaling** cuts expected calibration error by **50.7%–89.5%** in miscalibrated models, unifying all six models within $\\text{ECE} \\le 0.115$. **Two-tier NCBI epistemic gating** cuts ungrounded citations by **11.9–54.8 percentage points** ($p \\le 0.00147$), eliminates fabricated PMIDs ($q_{\\text{BH}} = 0.0310$), and reduces citation reasoning tokens by **86.2%–97.3%**.
3. **White-Box Trajectory Self-Rescue (`CoT-SRAD`):** Operating strictly without ground-truth label leakage via Leave-One-Disease-Out attractor deconfounding and early reasoning-stream recovery, **`CoT-SRAD`** rescues **+36 self-pruned Mendelian causal gene discoveries** ($p = 7.07 \\times 10^{-6}$), boosting DeepSeek-V4-Pro recall by **+57.1%** ($20.7\\% \\to 32.5\\%, p = 9.43 \\times 10^{-7}$) at zero marginal compute cost.

All execution harnesses, SHA-256 freeze manifests, verification caches, and rectification operators are openly available under the MIT License at https://github.com/SJT503/SDL-dAMD, and the full per-call JSONL telemetry archive is deposited on Zenodo (DOI: 10.5281/zenodo.20574265, CC BY 4.0, held under pre-publication anti-contamination embargo during peer review with immediate private reviewer access provided). This manuscript has been specifically formatted to *Nature Machine Intelligence* Article specifications (~4,000-word Main Text, 6 Main Figures, 1 Extended Data Figure, and 2 Extended Data Tables), is original, is not under consideration elsewhere, and has been approved by all authors with no competing interests.

Thank you for considering our manuscript for *Nature Machine Intelligence*.

Sincerely,

**Jiangtao Sheng, Ph.D.** (Lead Contact & Co-Corresponding Author)
Department of Microbiology and Immunology, Shantou University Medical College
22 Xinling Road, Shantou 515041, Guangdong, China | Email: jtsheng@stu.edu.cn | ORCID: 0000-0003-2438-7345

**Weiqiang Chen, M.D., Ph.D.** (Co-Corresponding Author)
Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College
57 Changping Road, Shantou 515041, Guangdong, China | Email: wqchen@stu.edu.cn | ORCID: 0000-0002-2612-0890
"""

    cl_nmi_bilingual = cl_nmi_en + """
---

# 中文审阅对照译文（仅供作者团队内部审阅，正式投稿请上传纯英文 `Cover_Letter_NMI_v1.0_submission_EN.docx`）

**致：** *Nature Machine Intelligence* 主编 Liesbeth Venema 博士及编辑团队
**手稿标题：** 审计与纠偏自主人工智能科学发现中的推理、锦标赛与文献锚定失效（Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery）
**文章类型：** 原创研究论文（Article：正文约 4,000 英文词；6 张主图；1 张扩展数据图；2 张扩展数据表）
**代码与冻结协议仓库：** https://github.com/SJT503/SDL-dAMD | **Zenodo 遥测数据归档：** DOI 10.5281/zenodo.20574265

尊敬的 Venema 博士及 *Nature Machine Intelligence* 编辑团队：

兹附上我们的原创研究手稿 **《Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery》**，谨申请在 *Nature Machine Intelligence* 作为 **Article** 发表。

自主多智能体 AI 系统正日益将大语言模型（LLM）假说构思与成对 Bradley–Terry–Luce（BTL）锦标赛及文献合成相耦合，以自动化推进科学假说生成（*Nature* 2026；*Nat. Mach. Intell.* 2024, 2026）。近期发表于 *Nature Machine Intelligence* 的系列工作先后推进了知识图谱引导的多智能体证据合成（Wang 等，`DeepEvidence`, 2026）、面向不确定性校准实验优化的高斯过程表征微调（Ranković 等，`GOLLuM`, 2026）以及剥离预训练记忆与真实泛化的去偏倚基准设计（Graber 等，`CleanSplit`, 2025）。然而，一个核心机器智能科学问题仍悬而未决：**扩展测试时思维链（Test-time CoT）算力究竟能否使多智能体科学发现管线实现自我核验，还是会在缺乏外部锚定时放大结构性的排序、文献锚定与概率校准失效？这些失效又能否在不增加任何推理调用成本的前提下通过确定性算法加以修复？**

为此，我们提出了 **STAR-Audit**（六维可信度审计与纠偏框架），在 SHA-256 协议哈希锁定与 Benjamini–Hochberg 错误发现率控制（$q = 0.05$）下，跨 **136 种生物医学疾病背景**、中美四大主权前沿模型家族及六个精确版本化推理层级（`GLM-5.3`、`DeepSeek-V4-Pro`、Google `Gemini-4-Argon-High` [`gemini-4-argon-high`] 与 `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]、以及 xAI `Grok-4.7` 与 `Grok-4.7-Fast`）完成了 **11,818 次真实评估（3,718 万个推理与输出 Token）**，确立了三项核心贡献：

1. **揭示“测试时推理悖论”的白盒动力学定律：** 对 8,973 条主框架白盒 `reasoning_content` 轨迹（3,558 万推理 Token，占主输出 93.83%）及多层级 Gemini/Grok 推理日志的定量剖析揭示了无锚定长推理无法自我纠错的机制。在强制引文槽位下，模型单次按年代前缀打捞 **35.8 个候选 PMID**，将无关真实论文挂靠至无支撑断言（尽管表面存在率达 **96.9%–100.0%**，四大家族仍存在 **11.9%–76.2% 的特洛伊木马引文**）。在成对裁决中，初始十分位 **88.4%–90.6%** 的注意力锁定于 A 槽位，驱动第一轮锦标赛 **71.3%** 的 A 槽位胜率（$p = 4.37 \\times 10^{-148}$）灭绝后置分桶通路（$\\chi^2 = 55.40$），并在第二轮锦标赛盲法反转中产生 **8.9%–43.0%** 的胜负翻转与 **$2.5\\times$** 的 DeBERTa-v3 NLI 自相矛盾激增。在掩码孟德尔表型推断中，模型遵循 **“2.1% 瞬时识别定律”**，却在 **23.3% 的失败推断** 中于冗长推敲内将早期已激活的真致病基因自我剪除并替换为教科书综合征吸引子。
2. **数据路径外的四大零调用确定性纠偏算子：** 无需权重微调或额外调用，**顺位校正 BTL** 结合 NLI 不一致中性化同时消除了首因、近因与对称位置偏倚，削减 72.8% 分桶失真（第 3 分桶存活率提升 +81.3%）并救回人类遗传学实证靶点（`GAS6/MERTK`、`TIMP3`、`ABCA1`、`CD59`、`MMP9`）；**留一运行 Platt 缩放** 将失准模型校准误差降低 **50.7%–89.5%**（六款模型全部 $\\text{ECE} \\le 0.115$）；**双层 NCBI 认识论门控** 削减无根据引文 **11.9–54.8 个百分点**（$p \\le 0.00147$）、清零虚构 PMID（$q_{\\text{BH}} = 0.0310$）并节省 **86.2%–97.3%** 引文推理算力。
3. **零成本白盒轨迹自救算法（`CoT-SRAD`）：** 在严格零真实标签泄露下结合留一疾病吸引子去混杂与早期推理流提取，**`CoT-SRAD`** 在零边际算力下净挽救 **+36 个被剪除的孟德尔致病基因发现**（$p = 7.07 \\times 10^{-6}$），将 DeepSeek-V4-Pro 召回率相对提升 **+57.1%**（$20.7\\% \\to 32.5\\%, p = 9.43 \\times 10^{-7}$）。

全部执行驱动代码、SHA-256 锁定清单、核验缓存与纠偏算子均已基于 MIT 协议开源于 https://github.com/SJT503/SDL-dAMD，完整逐调用 JSONL 遥测归档已存缴于 Zenodo（DOI: 10.5281/zenodo.20574265，CC BY 4.0，审稿期间提供私密审阅访问链接以防预训练爬虫污染）。本手稿已严格按 *Nature Machine Intelligence* Article 规范精炼排版（正文约 4,000 词、6 张主图、1 张扩展数据图及 2 张扩展数据表），系原创成果且未一稿多投，全体作者均已审阅同意且无利益冲突。

诚挚感谢您与编辑团队审阅本稿！
"""
    (BASE / "COVER_LETTER_NMI_v1.0.md").write_text(cl_nmi_en, encoding="utf-8")
    (BASE / "STAR-Audit_投稿信_NMI_中英对照版.md").write_text(cl_nmi_bilingual, encoding="utf-8")
    (BASE / "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.md").write_text(cl_nmi_bilingual, encoding="utf-8")
    print("[OK] Wrote COVER_LETTER_NMI_v1.0.md & STAR-Audit_投稿信_NMI_中英对照版.md")


def render_all_docx_suite() -> None:
    # 1. NMI Primary EN + ZH
    render_md_to_docx_custom(BASE / "MANUSCRIPT_NMI_v1.0.md", BASE / "MANUSCRIPT_NMI_v1.0.docx", mode="nmi_en")
    render_md_to_docx_custom(BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md", BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx", mode="nmi_zh")
    shutil.copy2(BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx", BASE / "STAR-Audit_手稿全文中文版_审核稿.docx")

    render_md_to_docx_custom(BASE / "COVER_LETTER_NMI_v1.0.md", BASE / "COVER_LETTER_NMI_v1.0.docx", mode="plain")
    render_md_to_docx_custom(BASE / "STAR-Audit_投稿信_NMI_中英对照版.md", BASE / "STAR-Audit_投稿信_NMI_中英对照版.docx", mode="plain")
    shutil.copy2(BASE / "STAR-Audit_投稿信_NMI_中英对照版.docx", BASE / "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx")

    # 2. npj Digital Medicine Backup EN + ZH + Cover Letter
    render_md_to_docx_custom(BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md", BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.docx", mode="npj_en")
    shutil.copy2(BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.docx", BASE / "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.docx")
    render_md_to_docx_custom(BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md", BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.docx", mode="npj_zh")
    render_md_to_docx_custom(BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.md", BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.docx", mode="plain")
    shutil.copy2(BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.docx", BASE / "COVER_LETTER_GEN2_NaturePortfolio_v1.0.docx")

    # 3. Supplementary Information & Patterns Backup
    render_md_to_docx_custom(BASE / "SUPPLEMENTARY_GEN2_v1.0.md", BASE / "SUPPLEMENTARY_GEN2_v1.0.docx", mode="plain")
    render_md_to_docx_custom(BASE / "MANUSCRIPT_GEN2_v1.0.md", BASE / "MANUSCRIPT_GEN2_v1.0.docx", mode="plain")
    render_md_to_docx_custom(BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md", BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.docx", mode="plain")

    # 4. Sync Desktop loose review files gracefully (without leaving any loose .md on Desktop)
    desktop_syncs = [
        (BASE / "STAR-Audit_手稿全文中文版_审核稿.docx", DESKTOP / "STAR-Audit_手稿全文中文版_审核稿.docx"),
        (BASE / "MANUSCRIPT_NMI_v1.0.docx", DESKTOP / "STAR-Audit_Manuscript_NaturePortfolio_v1.0.docx"),
        (BASE / "SUPPLEMENTARY_GEN2_v1.0.docx", DESKTOP / "STAR-Audit_Supplementary_Information_v1.0.docx"),
        (BASE / "STAR-Audit_投稿信_NMI_中英对照版.docx", DESKTOP / "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx"),
    ]
    for src, dst in desktop_syncs:
        try:
            shutil.copy2(src, dst)
            print(f"[OK] Synced Desktop file: {dst.name}")
        except PermissionError:
            alt = dst.with_name(dst.stem + "_NMI最新瘦身版.docx")
            shutil.copy2(src, alt)
            print(f"[WARN] {dst.name} is open in Word; saved updated Desktop copy to {alt.name}")


if __name__ == "__main__":
    build_nmi_manuscripts()
    build_nmi_cover_letters()
    render_all_docx_suite()
