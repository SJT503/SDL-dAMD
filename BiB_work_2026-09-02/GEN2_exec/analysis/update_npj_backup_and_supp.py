#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pass 1:
1. Purge all occurrences of 'without external API confounds' / '为在无外部付费 API 干扰下' (and '.db/.db-wal' internal phrasing).
2. Purge all occurrences of 'OSF' / '10.17605/OSF.IO/KF2G8' / 'preregistered' / 'pre-registered' / '预注册' across:
   - Full-length npj Digital Medicine Backup Edition (EN + ZH)
   - Cell Press Patterns Backup Edition (EN + Cover Letter)
   - Supplementary Information (SUPPLEMENTARY_GEN2_v1.0.md)
   - Dedicated npj Digital Medicine Backup Cover Letter (EN + Bilingual Review)
3. Upgrade the bibliography [1..69] by removing OSF boilerplate refs [31, 32] (Nosek 2018, Errington 2021),
   inserting 5 live-Entrez-verified 2025-2026 Nature Machine Intelligence & npj Digital Medicine papers at [31..35],
   and shifting old [33..66] cleanly by +3 to [36..69] while preserving 100% strict monotonic citation order.
"""

from pathlib import Path
import re

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")

NEW_REFS_31_35 = [
    "31. Wang Z, Chen Z, Yang Z, Wang X, Jin Q, Peng Y, et al. Empowering biomedical evidence exploration and synthesis with deep knowledge graph research. *Nat Mach Intell* 8, 1142-1156 (2026). DOI:10.1038/s42256-026-01266-0. PMID:42569156",
    "32. Graber D, Stockinger P, Meyer F, Mishra S, Horn C, Buller R. Resolving data bias improves generalization in binding affinity prediction. *Nat Mach Intell* 7, 1713-1725 (2025). DOI:10.1038/s42256-025-01124-5. PMID:41143208",
    "33. Kenaston MW, Ayub U, Parmar M, Kumar P, Anjum MU, Naqvi SAA, et al. Structured reasoning failures compromise LLM interpretation of clinical oncology notes. *NPJ Digit Med* 9, 802 (2026). DOI:10.1038/s41746-026-02951-5. PMID:42380231",
    "34. Stifini D, Della Penna A, Mihaljevic AL, Bitzer M, Eickhoff C, Capobianco I. Role prompting modulates linguistic style but not clinical decision structure in GPT-5 tumour board simulation. *NPJ Digit Med* 9, 626 (2026). DOI:10.1038/s41746-026-03069-4. PMID:42595794",
    "35. Zhu Y, Wang Z, Qi Y, Gu L, Sui D, Hu H, et al. HealthFlow: automating electronic health record analysis via a strategically self-evolving multi-agent framework. *NPJ Digit Med* 9, 660 (2026). DOI:10.1038/s41746-026-03097-0. PMID:42660985",
]


def shift_citations_gt32(body: str) -> str:
    """Shift any numeric citation index >= 33 by +3 inside bracket citations [..]."""
    def repl_bracket(m: re.Match) -> str:
        token = m.group(1)
        if token in ("0, 1", "1, 10, 50"):
            return m.group(0)
        parts = [p.strip() for p in token.split(",")]
        out_parts = []
        for p in parts:
            if "–" in p or "-" in p:
                sep = "–" if "–" in p else "-"
                s_a, s_b = [x.strip() for x in p.split(sep)]
                if not (s_a.isdigit() and s_b.isdigit()):
                    return m.group(0)
                a, b = int(s_a), int(s_b)
                if b - a > 25 or b > 70:
                    return m.group(0)
                na = a + 3 if a >= 33 else a
                nb = b + 3 if b >= 33 else b
                out_parts.append(f"{na}{sep}{nb}")
            else:
                if not p.isdigit():
                    return m.group(0)
                v = int(p)
                if v > 70 or v == 0:
                    return m.group(0)
                nv = v + 3 if v >= 33 else v
                out_parts.append(str(nv))
        return "[" + ", ".join(out_parts) + "]"

    return re.sub(r"\[(\d+(?:[–\-,\s]+\d+)*)\]", repl_bracket, body)


def upgrade_ref_section(ref_block: str) -> str:
    lines = ref_block.strip().splitlines()
    out = []
    inserted = False
    for ln in lines:
        m = re.match(r"^(\d+)\.\s+(.*)$", ln.strip())
        if not m:
            out.append(ln)
            continue
        idx = int(m.group(1))
        rest = m.group(2)
        if idx <= 30:
            out.append(f"{idx}. {rest}")
        elif idx in (31, 32):
            if not inserted:
                out.extend(NEW_REFS_31_35)
                inserted = True
        else:
            out.append(f"{idx + 3}. {rest}")
    return "\n".join(out) + "\n"


def update_supplementary() -> None:
    supp_path = BASE / "SUPPLEMENTARY_GEN2_v1.0.md"
    txt = supp_path.read_text(encoding="utf-8")
    txt = txt.replace(
        "**OSF Preregistration:** DOI 10.17605/OSF.IO/KF2G8",
        "**Code & Frozen Protocol Repository:** https://github.com/SJT503/SDL-dAMD | **Zenodo Telemetry Archive:** DOI 10.5281/zenodo.20574265",
    )
    txt = txt.replace(
        "Complete pre-registered deviation ledger (D2-001 through D2-012, SHA-256 sealed)",
        "Complete operational parameter governance ledger (D2-001 through D2-012, SHA-256 sealed)",
    )
    txt = txt.replace(
        "On our pre-registered 200-pair self-calibration benchmark",
        "On our frozen 200-pair self-calibration benchmark",
    )
    supp_path.write_text(txt, encoding="utf-8")
    print("[OK] Updated SUPPLEMENTARY_GEN2_v1.0.md")


def update_npj_en_and_patterns() -> None:
    src_path = BASE / "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md"
    txt = src_path.read_text(encoding="utf-8")

    # Split before References so we shift citations >=33 cleanly first
    body, refs = txt.split("## References\n", 1)

    # First remove [31, 32] OSF citation before shifting >=33
    body = body.replace(
        "and executed an OSF-preregistered Generation-2 (Gen-2) study (DOI: 10.17605/OSF.IO/KF2G8 [31, 32]).",
        "and executed a multi-block, multi-ecosystem empirical evaluation locked under cryptographic SHA-256 protocol governance.",
    )

    # Shift existing [33..66] -> [36..69]
    body = shift_citations_gt32(body)
    new_refs = upgrade_ref_section(refs)

    # Now weave [31-35] into Introduction para 3 (right after [30]) and Discussion
    old_intro_p3_tail = (
        "and Gaussian-process fine-tuning of LLM representations for uncertainty-calibrated experimental optimization [30]. "
        "However, no study has integrated external-truth auditing with zero-training algorithmic pipeline rectification across the complete multi-stage discovery loop (Table 1)."
    )
    new_intro_p3_tail = (
        "and Gaussian-process fine-tuning of LLM representations for uncertainty-calibrated experimental optimization [30]. "
        "Concurrent 2025–2026 benchmarks have further highlighted unresolved evidence conflicts in knowledge-graph research agents [31], pretraining data-leakage illusions in molecular generalization [32], structured chain-of-thought anchoring in clinical oncology notes [33], rhetorical rather than structural persona shifts in multi-agent boards [34], and plausible invalidity in autonomous biomedical workflows [35]. "
        "However, no study has integrated external-truth auditing with zero-training algorithmic pipeline rectification across the complete multi-stage discovery loop (Table 1)."
    )
    assert old_intro_p3_tail in body, "Could not match EN Intro P3 tail!"
    body = body.replace(old_intro_p3_tail, new_intro_p3_tail, 1)

    # Weave [31-35] into Discussion mechanistic & positioning sections
    old_disc_tourn = (
        "Flipped `GLM-5.3` verdicts spend significantly *more* reasoning tokens ($p = 0.0254$) with a 2.5- to 3.4-fold surge in DeBERTa-v3 NLI self-contradiction ($p = 1.15 \\times 10^{-5}$), and flagship `Grok-4.7` exhibits higher flip and subscore-verdict override rates (`10.0%` vs. `6.7%`) than `Grok-4.7-Fast`, showing that chain-of-thought acts as a motivated advocate."
    )
    new_disc_tourn = (
        "Flipped `GLM-5.3` verdicts spend significantly *more* reasoning tokens ($p = 0.0254$) with a 2.5- to 3.4-fold surge in DeBERTa-v3 NLI self-contradiction ($p = 1.15 \\times 10^{-5}$), and flagship `Grok-4.7` exhibits higher flip and subscore-verdict override rates (`10.0%` vs. `6.7%`) than `Grok-4.7-Fast`. Paralleling clinical oncology evaluations where prompt-only debiasing fails to override chain-of-thought anchoring [33] and persona prompting alters linguistic style rather than decision structure [34], internal deliberation here acts as a motivated advocate."
    )
    assert old_disc_tourn in body, "Could not match EN Discussion tournament sentence!"
    body = body.replace(old_disc_tourn, new_disc_tourn, 1)

    old_disc_pos = (
        "domain-specific agents such as GeneAgent [23], MRAgent [24], and clinical multi-agent boards such as EvoMDT [29] introduced tool- or guideline-assisted deliberation, and optimizers such as GOLLuM [30] fine-tuned LLM representations via Gaussian processes to curb overconfident experimental proposals. "
        "Parallel AI reliability studies introduced semantic entropy [20], SelfCheck-Eval [22], clinical summarization abstention frameworks [28], cross-signature cellular state validation [50], mathematical interaction benchmarks [53], and reproducibility guidelines separating *on-the-data-path* LLM inference from *off-the-data-path* deterministic code (the 'rerun-without-LLM test' [26, 27])."
    )
    new_disc_pos = (
        "domain-specific agents such as GeneAgent [23], MRAgent [24], knowledge-graph research explorers such as DeepEvidence [31], self-evolving workflow engines such as HealthFlow [35], and clinical multi-agent boards such as EvoMDT [29] introduced tool- or memory-assisted deliberation, while optimizers such as GOLLuM [30] fine-tuned LLM representations via Gaussian processes to curb overconfident experimental proposals. "
        "Parallel AI reliability studies exposed benchmark memorization biases via CleanSplit [32] and introduced semantic entropy [20], SelfCheck-Eval [22], clinical summarization abstention frameworks [28], cross-signature cellular state validation [50], mathematical interaction benchmarks [53], and reproducibility guidelines separating *on-the-data-path* LLM inference from *off-the-data-path* deterministic code (the 'rerun-without-LLM test' [26, 27])."
    )
    assert old_disc_pos in body, "Could not match EN Discussion positioning paragraph!"
    body = body.replace(old_disc_pos, new_disc_pos, 1)

    # Add DeepEvidence [31] and HealthFlow [35] rows to Table 1 and remove OSF from Table 1 & Table 2
    old_t1_header = "| Study / System | Primary Scope | End-to-End Discovery Pipeline Audited | Two-Tier Semantic Citation Grounding & Gate | Anti-Retrieval & 120-Disease IC Perturbation | Order-Adjusted BTL & Pathway Rescue | Cross-Stage & Judge NLI Coherence | Bootstrap Stability & LORO Calibration | Preregistered Confirmatory Governance |"
    new_t1_header = "| Study / System | Primary Scope | End-to-End Discovery Pipeline Audited | Two-Tier Semantic Citation Grounding & Gate | Anti-Retrieval & 120-Disease IC Perturbation | Order-Adjusted BTL & Pathway Rescue | Cross-Stage & Judge NLI Coherence | Bootstrap Stability & LORO Calibration | Pre-Specified Confirmatory Governance |"
    assert old_t1_header in body
    body = body.replace(old_t1_header, new_t1_header, 1)

    old_t1_geneagent = "| **GeneAgent** [23] | Self-verifying agent for gene-set analysis | Single-stage gene set | Domain database query | No | Not applicable | Self-verification step | No | No |"
    new_t1_geneagent = (
        "| **DeepEvidence** [31] | Knowledge-graph biomedical evidence exploration | Multi-agent retrieval & synthesis | Graph-bounded search, no two-tier abstention gate | No | Not applicable | Notes unresolved evidence conflict | Notes lack of calibrated confidence | No |\n"
        "| **HealthFlow** [35] | Self-evolving multi-agent EHR research workflow | Autonomous code & analysis execution | Sandboxed execution, exposes plausible invalidity | No | Not applicable | Rubric evaluator only | No | No |\n"
        + old_t1_geneagent
    )
    assert old_t1_geneagent in body
    body = body.replace(old_t1_geneagent, new_t1_geneagent, 1)

    body = body.replace(
        "| **Yes (OSF: 10.17605/OSF.IO/KF2G8; BH-FDR $q = 0.05$)** |",
        "| **Yes (SHA-256 protocol lock; BH-FDR $q = 0.05$)** |",
    )

    # Clean all remaining OSF / preregistered / external API confounds / .db-wal occurrences in EN body
    replacements_en = [
        (
            "an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost remediation framework",
            "a quantitative six-dimension evaluation and zero-cost algorithmic remediation framework",
        ),
        (
            "under preregistered Benjamini–Hochberg false discovery rate governance ($q = 0.05$) [36]",
            "under pre-specified Benjamini–Hochberg false discovery rate governance ($q = 0.05$) [36]",
        ),
        (
            "### R1. Study architecture, compute ledger, and preregistered confirmatory family",
            "### R1. Study architecture, compute ledger, and pre-specified confirmatory family",
        ),
        (
            "controlled at Benjamini–Hochberg false discovery rate $q = 0.05$ [36]) on the Open Science Framework prior to data analysis (DOI: 10.17605/OSF.IO/KF2G8).",
            "controlled at Benjamini–Hochberg false discovery rate $q = 0.05$ [36]) under cryptographic SHA-256 configuration locking prior to data analysis.",
        ),
        (
            "three of the six preregistered confirmatory null hypotheses",
            "three of the six pre-specified confirmatory null hypotheses",
        ),
        (
            "On a preregistered 200-pair self-calibration benchmark",
            "On a frozen 200-pair self-calibration benchmark",
        ),
        (
            "in our preregistered HPO stimulus table",
            "in our frozen HPO stimulus table",
        ),
        (
            "we performed a preregistered **10,000-draw parametric bootstrap",
            "we performed a **10,000-draw parametric bootstrap",
        ),
        (
            "We executed the preregistered **STAR-Audit** framework",
            "We executed the **STAR-Audit** framework",
        ),
        (
            "under preregistered statistical governance without requiring weight fine-tuning",
            "under pre-specified BH-FDR statistical governance without requiring weight fine-tuning",
        ),
        (
            "The complete preregistration specification, frozen gold-standard definitions,",
            "The frozen protocol specification, cryptographic SHA-256 freeze manifest, disease gold-standard definitions,",
        ),
        (
            "are publicly accessible on the Open Science Framework (DOI: 10.17605/OSF.IO/KF2G8) and archived on Zenodo (DOI: 10.5281/zenodo.20574265, CC BY 4.0; held under pre-publication anti-contamination embargo during peer review to prevent LLM pretraining crawl leakage of masked HPO benchmarks, with reviewer access available upon request and automatic public release upon publication)",
            "are publicly accessible on GitHub (https://github.com/SJT503/SDL-dAMD) and archived on Zenodo (DOI: 10.5281/zenodo.20574265, CC BY 4.0; held under pre-publication anti-contamination embargo during peer review to prevent LLM pretraining crawl leakage of masked HPO benchmarks, with private reviewer access provided and automatic public release upon publication)",
        ),
        (
            "#### Preregistration, deviation governance, and compute harness",
            "#### Protocol locking, operational governance, and compute harness",
        ),
        (
            "Prior to executing the Generation-2 study, the complete experimental protocol (`PREREG_v2_FROZEN_v1.0.md`), frozen disease pathway gold standards and NLI specifications (`APPENDIX_A_B_C_frozen_prep.md`), 120-disease HPO stimulus table (`expC_v4_pairs_120_f14.csv`), and daily canary prompts (`canary_prompts.json`) were cryptographic-hash-locked (`FREEZE_MANIFEST_v1.1.json`) and registered on OSF (DOI: 10.17605/OSF.IO/KF2G8).",
            "Prior to executing the multi-block evaluation, the complete experimental protocol specification, frozen disease pathway gold standards and NLI specifications (`APPENDIX_A_B_C_frozen_prep.md`), 120-disease HPO stimulus table (`expC_v4_pairs_120_f14.csv`), and daily canary prompts (`canary_prompts.json`) were sealed via SHA-256 cryptographic hashing (`FREEZE_MANIFEST_v1.1.json`).",
        ),
        (
            "To evaluate cross-ecosystem generalization across US commercial frontier architectures and versioned high- versus low-thinking compute tiers without external API confounds, we executed a matched 2,688-evaluation validation suite across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`], forensically verified via runtime `.db`/`.db-wal` binary model signatures and `transcript_full.jsonl` white-box reasoning logs;",
            "To evaluate cross-ecosystem generalization across US commercial frontier architectures and versioned high- versus low-thinking compute tiers, we executed a matched 2,688-evaluation validation suite across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`], with deterministic session telemetry and complete `transcript_full.jsonl` white-box reasoning logs;",
        ),
        (
            "Multiplicity across the pre-registered six-member confirmatory hypothesis family",
            "Multiplicity across the pre-specified six-member confirmatory hypothesis family",
        ),
        (
            "unless one-sided directional tests were explicitly pre-registered (Members 1, 2, 4, and 5).",
            "unless one-sided directional tests were pre-specified in the frozen statistical protocol (Members 1, 2, 4, and 5).",
        ),
        (
            "The preregistered protocol, cryptographic freeze manifest, disease pathway gold standards, 120-disease HPO stimulus dataset, PubMed verification caches (956 primary, 162 Google Gemini, and 136 xAI Grok distinct PMIDs), and aggregated statistical summary JSON files are publicly available on the Open Science Framework (https://doi.org/10.17605/OSF.IO/KF2G8) and in the GitHub repository (https://github.com/SJT503/SDL-dAMD). The complete raw per-call JSONL telemetry archive spanning all 11,818 evaluations (37.18 million reasoning/output tokens) is deposited on Zenodo (https://doi.org/10.5281/zenodo.20574265, CC BY 4.0); per our preregistered anti-contamination governance,",
            "The frozen protocol specification, cryptographic SHA-256 freeze manifest, disease pathway gold standards, 120-disease HPO stimulus dataset, PubMed verification caches (956 primary, 162 Google Gemini, and 136 xAI Grok distinct PMIDs), and aggregated statistical summary JSON files are publicly available in the GitHub repository (https://github.com/SJT503/SDL-dAMD). The complete raw per-call JSONL telemetry archive spanning all 11,818 evaluations (37.18 million reasoning/output tokens) is deposited on Zenodo (https://doi.org/10.5281/zenodo.20574265, CC BY 4.0); per our benchmark anti-contamination governance,",
        ),
        (
            "J.S. conceived and designed the study, preregistered the protocol, developed the **STAR-Audit**",
            "J.S. conceived and designed the study, established the frozen protocol specification, developed the **STAR-Audit**",
        ),
        (
            "**(A)** Two-dimensional log-scale bubble matrix of the preregistered four-block experimental design",
            "**(A)** Two-dimensional log-scale bubble matrix of the four-block multi-disease experimental design",
        ),
        (
            "**(C)** Paired Cleveland dumbbell scorecard for the pre-registered six-member confirmatory hypothesis family (OSF: 10.17605/OSF.IO/KF2G8),",
            "**(C)** Paired Cleveland dumbbell scorecard for the pre-specified six-member confirmatory hypothesis family (controlled at BH-FDR $q = 0.05$),",
        ),
        (
            "**Table 2. Pre-registered six-member confirmatory hypothesis family and headline STAR-Audit outcomes.**",
            "**Table 2. Pre-specified six-member confirmatory hypothesis family and headline STAR-Audit outcomes.**",
        ),
    ]
    for old_s, new_s in replacements_en:
        assert old_s in body, f"Missing expected EN target:\n  {old_s}"
        body = body.replace(old_s, new_s)

    full_npj_en = body + "## References\n" + new_refs
    src_path.write_text(full_npj_en, encoding="utf-8")
    (BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md").write_text(full_npj_en, encoding="utf-8")
    print("[OK] Updated MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md & MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md")

    # Sync Cell Press Patterns Backup Edition (MANUSCRIPT_GEN2_v1.0.md)
    idx_intro = full_npj_en.index("## Introduction")
    pat_body = full_npj_en[idx_intro:]
    pat_body = pat_body.replace("### Methodological scope boundaries and operational governance", "## Limitations of the Study")
    pat_body = pat_body.replace("## Methods", "## STAR Methods")
    pat_body = re.sub(r"\n## Data availability\n.*?\n(?=## Acknowledgments\n)", "\n", pat_body, flags=re.S)
    pat_body = pat_body.replace("## Competing interests", "## Declaration of Interests")

    m_abs = re.search(r"## Abstract\n(.+?)\n\n\*\*Keywords:\*\*", full_npj_en, flags=re.S)
    abs_clean = m_abs.group(1).strip()

    pat_front = f"""# Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery

**Jiangtao Sheng$^{{1,\\#,\\*}}$, Xueer Liu$^{{1}}$, Runmin Lin$^{{1}}$, Qiaochu Sun$^{{1}}$, Xiaoxuan Chen$^{{1}}$, Kangsheng Li$^{{1}}$, and Weiqiang Chen$^{{2,\\*}}$**

$^{{1}}$Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China

$^{{2}}$Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China

$^{{\\text{{#}}}}$Lead contact: Jiangtao Sheng (jtsheng@stu.edu.cn)

$^{{\\text{{*}}}}$Correspondence: Jiangtao Sheng (jtsheng@stu.edu.cn; ORCID: 0000-0003-2438-7345); Weiqiang Chen (wqchen@stu.edu.cn; ORCID: 0000-0002-2612-0890)

## Highlights
- **STAR-Audit** evaluates 9,130 primary calls + 2,688 Gemini/Grok evaluations (11,818 total) across 136 diseases
- White-box CoT trajectory dynamics uncover the Test-Time Reasoning Paradox and enable zero-cost **CoT-SRAD**
- Real-PMID Trojan horse citations (11.9%–76.2%) and positional flips (8.9%–43.0%) generalize across 4 model families
- Four zero-cost rectification modules rescue suppressed pathways, boost Mendelian recall by 57.1%, and cut compute by 86.2%–97.3%

## The bigger picture
Autonomous artificial intelligence (AI) systems now generate therapeutic hypotheses, rank candidate mechanisms through multi-agent tournaments, and synthesize experimental protocols for wet-lab execution. While these architectures scale hypothesis generation, their internal decision reliability has remained largely unmeasured. A widespread assumption in current agentic design is that scaling test-time reasoning tokens allows frontier models to self-correct citation errors, evaluation biases, and overconfidence. Across 136 disease contexts under cryptographic SHA-256 protocol locking, we audited 9,130 primary live model invocations (35.58 million internal reasoning tokens across 8,973 white-box traces) on GLM-5.3 and DeepSeek-V4-Pro alongside 2,688 cross-ecosystem evaluations across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]; 1.15 million output/reasoning tokens) and xAI Grok (`Grok-4.7` and `Grok-4.7-Fast`; 450,879 native reasoning tokens), totaling 11,818 live evaluations and 37.18 million reasoning/output tokens across four sovereign frontier model families and six versioned compute tiers. Test-time chain-of-thought frequently rationalizes rather than corrects failure modes: models trial 35.8 candidate PMIDs per call to cite real PubMed identifiers that do not support their claims (11.9%–76.2% Trojan horse citations), focus 88.4%–90.6% of Decile-1 attention on Slot A to extinguish late-indexed biological pathways, and self-prune valid causal genes activated at 2.1% reasoning depth in favor of textbook syndromic attractors. Within our **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification) framework, we convert these six audit dimensions into four lightweight mathematical and architectural rectifications: Order-Adjusted Bradley–Terry–Luce ranking with Natural Language Inference contradiction filtering, Leave-One-Run-Out Platt recalibration, two-tier epistemic citation gating, and Chain-of-Thought Stream Recovery and Attractor Deconfounding (`CoT-SRAD`). Together, these deterministic operators repair ranking distortion, rescue +36 self-pruned Mendelian gene discoveries (+57.1% relative recall gain on DeepSeek-V4-Pro), restore calibration across all four model families ($\\text{{ECE}} \\le 0.115$ across all six models), and eliminate fabricated citations without a single extra language-model call. Embedding measurable audit-and-rectification layers into autonomous discovery pipelines ensures that experimental resources and preclinical investments rest on verified evidence rather than uncalibrated model assertions.

## Summary
{abs_clean}

**Keywords:** autonomous scientific discovery; large language models; test-time reasoning; Bradley–Terry–Luce tournament; citation faithfulness; confidence calibration; algorithmic rectification

"""
    (BASE / "MANUSCRIPT_GEN2_v1.0.md").write_text(pat_front + pat_body, encoding="utf-8")
    print("[OK] Synced MANUSCRIPT_GEN2_v1.0.md (Patterns Backup)")


def update_npj_zh_backup() -> None:
    zh_src = BASE / "STAR-Audit_手稿全文中文版_审核稿.md"
    txt = zh_src.read_text(encoding="utf-8")

    # Strip Highlights & Bigger Picture from Nature Portfolio ZH review edition so it matches Nature Portfolio clean structure
    txt = re.sub(r"## 核心亮点\n.*?(?=## 摘要\n)", "", txt, flags=re.S)

    body, refs = txt.split("## 参考文献\n", 1)

    body = body.replace(
        "并执行了在 OSF 预注册的第二代（Gen-2）系统研究（DOI: 10.17605/OSF.IO/KF2G8 [31, 32]）。",
        "并在 SHA-256 密码学协议锁定下执行了跨模块、跨生态系统的实证评估研究。",
    )
    body = shift_citations_gt32(body)
    new_refs = upgrade_ref_section(refs)

    old_zh_intro_p3 = (
        "以及利用高斯过程微调语言模型表征以实现不确定性校准的实验优化 [30]。"
        "然而，目前尚无研究将外部真实性锚定审计与零训练成本的算法级管线纠偏整合到完整的多阶段科学发现闭环之中（表 1）。"
    )
    new_zh_intro_p3 = (
        "以及利用高斯过程微调语言模型表征以实现不确定性校准的实验优化 [30]。"
        "2025–2026 年最新发表的系列基准研究亦相继指出了知识图谱科研智能体中悬而未决的证据冲突调和与置信度校准难题 [31]、分子泛化预测中的预训练数据泄露假象 [32]、临床肿瘤病历解读中的结构化思维链锚定失效 [33]、多智能体肿瘤委员会中角色提示仅改变修辞风格而非决策结构 [34]，以及自主生物医学工作流中普遍存在的“貌似合理性谬误（plausible invalidity）” [35]。"
        "然而，目前尚无研究将外部真实性锚定审计与零训练成本的算法级管线纠偏整合到完整的多阶段科学发现闭环之中（表 1）。"
    )
    assert old_zh_intro_p3 in body, "Could not match ZH Intro P3!"
    body = body.replace(old_zh_intro_p3, new_zh_intro_p3, 1)

    old_zh_disc_tourn = (
        "发生翻转的 `GLM-5.3` 裁决消耗显著更多推理 Token（$p = 0.0254$）且 DeBERTa-v3 NLI 自相矛盾率激增 2.5–3.4 倍（$p = 1.15 \\times 10^{-5}$），旗舰推理 `Grok-4.7` 的翻转率与分项-裁决倒挂率（10.0% 对比 6.7%）亦高于 `Grok-4.7-Fast`，证实思维链充当了动机性辩护者。"
    )
    new_zh_disc_tourn = (
        "发生翻转的 `GLM-5.3` 裁决消耗显著更多推理 Token（$p = 0.0254$）且 DeBERTa-v3 NLI 自相矛盾率激增 2.5–3.4 倍（$p = 1.15 \\times 10^{-5}$），旗舰推理 `Grok-4.7` 的翻转率与分项-裁决倒挂率（10.0% 对比 6.7%）亦高于 `Grok-4.7-Fast`。这与近期临床肿瘤学评估中单纯提示词纠偏无法克服思维链锚定 [33]、且角色提示仅修饰语言风格而无法改变底层决策结构 [34] 的结论一致，证实内部长思维链在此充当了动机性辩护者。"
    )
    assert old_zh_disc_tourn in body
    body = body.replace(old_zh_disc_tourn, new_zh_disc_tourn, 1)

    old_zh_disc_pos = (
        "GeneAgent [23]、MRAgent [24] 以及肿瘤多学科决策系统 EvoMDT [29] 引入了工具或指南辅助审议，实验优化器 GOLLuM [30] 则通过高斯过程微调语言模型表征以抑制过度自信的实验提议。另一方面，AI 可靠性研究提出了语义熵 [20]、SelfCheck-Eval [22]、临床摘要弃权评估框架 [28]、跨特征空间细胞状态验证 [50]、生物互作数学基准 [53]，以及区分“数据路径上”LLM 推理与“数据路径外”确定性代码的可重复性原则（“移除 LLM 重跑测试” [26, 27]）。"
    )
    new_zh_disc_pos = (
        "GeneAgent [23]、MRAgent [24]、知识图谱证据探索系统 DeepEvidence [31]、自演化工作流引擎 HealthFlow [35] 以及肿瘤多学科决策系统 EvoMDT [29] 引入了工具或记忆辅助审议，实验优化器 GOLLuM [30] 则通过高斯过程微调语言模型表征以抑制过度自信的实验提议。另一方面，AI 可靠性研究通过 CleanSplit 揭示了基准记忆偏倚 [32]，并提出了语义熵 [20]、SelfCheck-Eval [22]、临床摘要弃权评估框架 [28]、跨特征空间细胞状态验证 [50]、生物互作数学基准 [53]，以及区分“数据路径上”LLM 推理与“数据路径外”确定性代码的可重复性原则（“移除 LLM 重跑测试” [26, 27]）。"
    )
    assert old_zh_disc_pos in body
    body = body.replace(old_zh_disc_pos, new_zh_disc_pos, 1)

    # Update Table 1 in ZH
    old_zh_t1_hdr = "| 研究 / 系统 | 核心研究范围 | 是否审计端到端多步发现管线 | 双层语义引文锚定与认识论门控 | 抗检索与 120 种疾病 IC 梯度扰动 | 顺位校正 BTL 与致病通路拯救 | 跨阶段及裁判 NLI 逻辑连贯性审计 | 判词表 Bootstrap 稳定性与 LORO 校准 | 预注册验证性统计治理 |"
    new_zh_t1_hdr = "| 研究 / 系统 | 核心研究范围 | 是否审计端到端多步发现管线 | 双层语义引文锚定与认识论门控 | 抗检索与 120 种疾病 IC 梯度扰动 | 顺位校正 BTL 与致病通路拯救 | 跨阶段及裁判 NLI 逻辑连贯性审计 | 判词表 Bootstrap 稳定性与 LORO 校准 | 预先设定验证性统计治理 |"
    assert old_zh_t1_hdr in body
    body = body.replace(old_zh_t1_hdr, new_zh_t1_hdr, 1)

    old_zh_t1_ga = "| **GeneAgent** [23] | 基因集分析自校验智能体 | 单阶段基因集注释 | 领域数据库查询 | 无 | 不适用 | 单步自校验步骤 | 无 | 无 |"
    new_zh_t1_ga = (
        "| **DeepEvidence** [31] | 知识图谱生物医学证据探索与合成 | 多智能体检索与综述合成 | 图谱边界检索，无双层弃权门控 | 无 | 不适用 | 指出多源证据冲突尚未解决 | 指出缺乏校准后置信度建模 | 无 |\n"
        "| **HealthFlow** [35] | 自演化多智能体电子病历科研工作流 | 自主代码与分析执行 | 沙箱执行，揭示“貌似合理性谬误” | 无 | 不适用 | 仅评分量表评估 | 无 | 无 |\n"
        + old_zh_t1_ga
    )
    assert old_zh_t1_ga in body
    body = body.replace(old_zh_t1_ga, new_zh_t1_ga, 1)

    body = body.replace(
        "| **是（OSF: 10.17605/OSF.IO/KF2G8；BH-FDR $q = 0.05$）** |",
        "| **是（SHA-256 协议哈希锁定；BH-FDR $q = 0.05$）** |",
    )

    replacements_zh = [
        (
            "本文提出在 OSF 预注册（DOI: 10.17605/OSF.IO/KF2G8）的六维可信度审计与零成本纠偏框架 **STAR-Audit**",
            "本文提出定量化的六维可信度审计与零成本算法纠偏框架 **STAR-Audit**",
        ),
        (
            "在预注册 Benjamini–Hochberg 错误发现率控制（$q = 0.05$）[36] 下",
            "在预先设定的 Benjamini–Hochberg 错误发现率控制（$q = 0.05$）[36] 下",
        ),
        (
            "### R1. 研究架构、算力账本与预注册验证性假设族",
            "### R1. 研究架构、算力账本与预先设定验证性假设族",
        ),
        (
            "全部锁定并预注册于开放科学框架（OSF DOI: 10.17605/OSF.IO/KF2G8）。",
            "通过 SHA-256 密码学哈希清单全部前置锁定。",
        ),
        (
            "6 个预注册验证性零假设中仍有 3 个",
            "6 个预先设定验证性零假设中仍有 3 个",
        ),
        (
            "在预注册的 200 对自校准基准集",
            "在冻结的 200 对自校准基准集",
        ),
        (
            "预注册附录 A 金标准定义的",
            "冻结版附录 A 金标准定义的",
        ),
        (
            "按预注册 HPO 刺激词表中的",
            "按冻结版 HPO 刺激词表中的",
        ),
        (
            "执行了预注册的 10,000 次参数化自助重采样（Bootstrap）**",
            "执行了 10,000 次参数化自助重采样（Bootstrap）**",
        ),
        (
            "评估上执行了预注册 **STAR-Audit** 框架。",
            "评估上执行了 **STAR-Audit** 框架。",
        ),
        (
            "在预注册统计治理下无需微调模型权重",
            "在预先设定的 BH-FDR 统计治理下无需微调模型权重",
        ),
        (
            "完整的预注册方案说明、冻结版疾病金标准定义、",
            "冻结版实验协议规范、密码学 SHA-256 锁定清单、疾病金标准定义、",
        ),
        (
            "公开注册于开放科学框架（OSF DOI: 10.17605/OSF.IO/KF2G8）并归档于 Zenodo（DOI: 10.5281/zenodo.20574265，CC BY 4.0 协议；在同行评审期间按预注册防污染规范处于预发表防爬虫封存状态",
            "公开托管于 GitHub（https://github.com/SJT503/SDL-dAMD）并归档于 Zenodo（DOI: 10.5281/zenodo.20574265，CC BY 4.0 协议；在同行评审期间按基准防污染规范处于预发表防爬虫封存状态",
        ),
        (
            "#### 预注册、偏离治理与计算执行框架",
            "#### 协议锁定、运行治理与计算执行框架",
        ),
        (
            "在启动第二代（Gen-2）实验之前，完整的实验协议（`PREREG_v2_FROZEN_v1.0.md`）、冻结版疾病通路金标准与 NLI 审计规范（`APPENDIX_A_B_C_frozen_prep.md`）、120 种疾病 HPO 刺激词表（`expC_v4_pairs_120_f14.csv`）以及每日漂移金丝雀提示词（`canary_prompts.json`）均通过密码学哈希锁定（`FREEZE_MANIFEST_v1.1.json`）并正式注册于 OSF（DOI: 10.17605/OSF.IO/KF2G8）。",
            "在启动多模块评估实验之前，完整的实验协议规范、冻结版疾病通路金标准与 NLI 审计规范（`APPENDIX_A_B_C_frozen_prep.md`）、120 种疾病 HPO 刺激词表（`expC_v4_pairs_120_f14.csv`）以及每日漂移金丝雀提示词（`canary_prompts.json`）均通过 SHA-256 密码学哈希清单前置锁定（`FREEZE_MANIFEST_v1.1.json`）。",
        ),
        (
            "为在无外部付费 API 干扰下评估美国主流商业前沿架构及同家族高低推理预算层级的跨生态泛化性，我们在 Google Gemini（旗舰高推理 `Gemini-4-Argon-High` [`gemini-4-argon-high`] 与轻量分层 `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]，经底层会话 SQLite `.db`/`.db-wal` 二进制模型签名与 `transcript_full.jsonl` 白盒推理日志双重溯源核验，",
            "为评估美国主流商业前沿架构及同家族高低推理预算层级的跨生态泛化性，我们在 Google Gemini（旗舰高推理 `Gemini-4-Argon-High` [`gemini-4-argon-high`] 与轻量分层 `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]，完整记录确定性会话遥测与 `transcript_full.jsonl` 白盒推理轨迹，",
        ),
        (
            "针对预注册 6 成员验证性假设族的多重检验",
            "针对预先设定的 6 成员验证性假设族的多重检验",
        ),
        (
            "除非预注册明确指定单侧方向性检验（成员 1、2、4 和 5），",
            "除非冻结版统计协议明确指定单侧方向性检验（成员 1、2、4 和 5），",
        ),
        (
            "预注册协议、密码学哈希锁定清单、疾病通路金标准、120 种疾病 HPO 刺激数据集、PubMed 核验缓存（主运行/实验 B 956 个、Google Gemini 162 个及 xAI Grok 136 个独立 PMID）及汇总统计结果 JSON 文件已公开托管于开放科学框架（https://doi.org/10.17605/OSF.IO/KF2G8）与 GitHub 仓库（https://github.com/SJT503/SDL-dAMD）。涵盖全部 11,818 次评估（3,718 万个推理/输出 Token）的完整逐调用原始 JSONL 遥测归档已存缴于 Zenodo（https://doi.org/10.5281/zenodo.20574265，CC BY 4.0 协议）；依据预注册防污染治理条款，",
            "冻结版实验协议、密码学 SHA-256 哈希锁定清单、疾病通路金标准、120 种疾病 HPO 刺激数据集、PubMed 核验缓存（主运行/实验 B 956 个、Google Gemini 162 个及 xAI Grok 136 个独立 PMID）及汇总统计结果 JSON 文件已公开托管于 GitHub 仓库（https://github.com/SJT503/SDL-dAMD）。涵盖全部 11,818 次评估（3,718 万个推理/输出 Token）的完整逐调用原始 JSONL 遥测归档已存缴于 Zenodo（https://doi.org/10.5281/zenodo.20574265，CC BY 4.0 协议）；依据基准防污染治理条款，",
        ),
        (
            "完成了实验协议预注册，开发了 **STAR-Audit**",
            "制定了冻结版实验协议规范，开发了 **STAR-Audit**",
        ),
        (
            "**(A)** 预注册四模块实验设计的二维对数尺度气泡矩阵",
            "**(A)** 四模块多疾病实验设计的二维对数尺度气泡矩阵",
        ),
        (
            "**(C)** 预注册 6 成员验证性假设族（OSF: 10.17605/OSF.IO/KF2G8）的配对克利夫兰哑铃记分卡",
            "**(C)** 预先设定的 6 成员验证性假设族（BH-FDR $q = 0.05$ 控制）配对克利夫兰哑铃记分卡",
        ),
        (
            "**表 2（Table 2）. 预注册 6 成员验证性假设族与 STAR-Audit 核心审计及纠偏结果汇总。**",
            "**表 2（Table 2）. 预先设定的 6 成员验证性假设族与 STAR-Audit 核心审计及纠偏结果汇总。**",
        ),
    ]
    for old_s, new_s in replacements_zh:
        assert old_s in body, f"Missing expected ZH target:\n  {old_s}"
        body = body.replace(old_s, new_s)

    full_npj_zh = body + "## 参考文献\n" + new_refs
    (BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md").write_text(full_npj_zh, encoding="utf-8")
    print("[OK] Saved STAR-Audit_npj备选版_手稿全文中文版_审核稿.md")


def update_backup_cover_letters() -> None:
    # 1. Dedicated npj Digital Medicine Backup Cover Letter (Pure EN + Bilingual Review)
    cl_npj_en = """# Cover Letter — *npj Digital Medicine*

**Date:** October 29, 2026
**To:** Prof. Joseph C. Kvedar, Editor-in-Chief, and the Editorial Team, *npj Digital Medicine* (Nature Portfolio)
**Manuscript Title:** Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery
**Article Type:** Article
**Zenodo Telemetry Archive:** DOI 10.5281/zenodo.20574265 | **Code Repository:** https://github.com/SJT503/SDL-dAMD

Dear Prof. Kvedar and Editorial Team of *npj Digital Medicine*,

Please find enclosed our manuscript entitled **"Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery"** for consideration as an original **Article** in *npj Digital Medicine*.

Autonomous multi-agent artificial intelligence systems increasingly pair large language model (LLM) hypothesis ideation with Bradley–Terry–Luce (BTL) pairwise tournaments and automated protocol synthesis to nominate therapeutic targets and clinical research hypotheses. Recent studies in *npj Digital Medicine* have demonstrated that unanchored chain-of-thought reasoning can amplify hallucinations in medical text summarization (Asgari et al., 2025), suffer structured anchoring failures in oncology notes (Kenaston et al., 2026), modulate rhetorical style rather than clinical decision structure under persona prompting (Stifini et al., 2026), and produce plausible invalidity in self-evolving multi-agent EHR workflows (Zhu et al., 2026). Yet no framework has united end-to-end multi-stage discovery auditing with zero-training algorithmic rectification before wet-lab or clinical resources are committed.

To address this gap, we developed **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification) and executed **11,818 live evaluations (37.18 million reasoning/output tokens)** across **136 biomedical disease contexts**, spanning four sovereign frontier model families and six versioned reasoning tiers (`GLM-5.3`, `DeepSeek-V4-Pro`, Google `Gemini-4-Argon-High` [`gemini-4-argon-high`], Google `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`], xAI `Grok-4.7`, and xAI `Grok-4.7-Fast`) under pre-specified Benjamini–Hochberg false discovery rate governance ($q = 0.05$). Our study establishes three principal advances:

1. **White-Box Discovery of the Test-Time Reasoning Paradox Across Four Model Ecosystems:** Analyzing 8,973 primary white-box `reasoning_content` traces (93.83% of all primary output tokens) alongside multi-tier Google Gemini and xAI Grok reasoning logs demonstrates that unanchored test-time compute rationalizes rather than self-corrects pipeline biases. Specifically, models dredge an average of **35.8 candidate PMIDs per call** to emit real but off-topic **Trojan horse citations** (`11.9%–76.2%` across all four ecosystems despite `96.9%–100.0%` naive identifier validity), anchor **88.4%–90.6% of Decile-1 attention on Slot A** to drive **71.3% Tournament I primacy bias** (`8.9%–43.0%` blinded reversal flips in Tournament II accompanied by a $2.5\\times$ surge in DeBERTa-v3 NLI self-contradiction), and **self-prune valid Mendelian causal genes** activated at **2.1% chain-of-thought depth** in **23.3% of failed inferences** in favor of textbook syndromic attractors.
2. **Four Zero-Call Algorithmic Rectification Operators:** Moving quality control off the generative LLM data path into deterministic mathematical operators repairs all three failure modes without weight fine-tuning or extra API calls. **Order-Adjusted BTL** with NLI-discordance neutralization cuts Tournament I bucket skew by **72.8%** (`+81.3%` Bucket-3 survival) and rescues targets validated by human genetics, animal models, and clinical trials (`GAS6/MERTK`, `TIMP3`, `ABCA1`, `CD59`, `MMP9`). **Leave-One-Run-Out Platt scaling** reduces expected calibration error by **50.7%–89.5%** across miscalibrated models ($\\text{ECE} \\le 0.115$ across all six models). **Two-tier NCBI epistemic gating** cuts ungrounded citations by **11.9–54.8 percentage points** ($p \\le 0.00147$), eliminates fabricated PMIDs ($q_{\\text{BH}} = 0.0310$), and reduces citation reasoning compute by **86.2%–97.3%**.
3. **Zero-Cost White-Box Trajectory Self-Rescue (`CoT-SRAD`):** Leveraging Leave-One-Disease-Out attractor deconfounding and early reasoning-stream extraction without ground-truth label leakage, **`CoT-SRAD`** rescues **+36 lost Mendelian causal gene discoveries** ($p = 7.07 \\times 10^{-6}$), boosting DeepSeek-V4-Pro recall by **+57.1%** ($20.7\\% \\to 32.5\\%, p = 9.43 \\times 10^{-7}$) at zero marginal compute cost.

All frozen protocol specifications, SHA-256 manifests, disease gold standards, PubMed verification caches, and analysis scripts are openly available on GitHub (https://github.com/SJT503/SDL-dAMD, MIT License), and the complete per-call JSONL telemetry archive is deposited on Zenodo (DOI: 10.5281/zenodo.20574265, CC BY 4.0, with private reviewer access provided during peer review under benchmark anti-contamination governance). This manuscript is original, is not under consideration elsewhere, and has been approved by all authors with no competing interests.

Thank you very much for considering our work for *npj Digital Medicine*.

Sincerely,

**Jiangtao Sheng, Ph.D.** (Lead Contact & Co-Corresponding Author)
Department of Microbiology and Immunology, Shantou University Medical College
22 Xinling Road, Shantou 515041, Guangdong, China | Email: jtsheng@stu.edu.cn | ORCID: 0000-0003-2438-7345

**Weiqiang Chen, M.D., Ph.D.** (Co-Corresponding Author)
Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College
57 Changping Road, Shantou 515041, Guangdong, China | Email: wqchen@stu.edu.cn | ORCID: 0000-0002-2612-0890
"""
    (BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.md").write_text(cl_npj_en, encoding="utf-8")
    (BASE / "COVER_LETTER_GEN2_NaturePortfolio_v1.0.md").write_text(cl_npj_en, encoding="utf-8")

    # 2. Clean Patterns Backup Cover Letter (remove OSF / preregistered)
    pat_cl_path = BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md"
    if pat_cl_path.exists():
        pcl = pat_cl_path.read_text(encoding="utf-8")
        pcl = re.sub(r"\*\*OSF Preregistration:\*\*[^\n]*\n", "**Code Repository:** https://github.com/SJT503/SDL-dAMD | **Zenodo Archive:** DOI 10.5281/zenodo.20574265\n", pcl)
        pcl = pcl.replace("an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) six-dimension", "a cryptographically protocol-locked six-dimension")
        pcl = pcl.replace("on OSF (DOI: 10.17605/OSF.IO/KF2G8) and GitHub", "on Zenodo (DOI: 10.5281/zenodo.20574265) and GitHub")
        pcl = pcl.replace("OSF-preregistered", "SHA-256 protocol-locked")
        pcl = pcl.replace("preregistered", "pre-specified")
        pcl = pcl.replace("pre-registered", "pre-specified")
        pcl = pcl.replace("OSF (DOI: 10.17605/OSF.IO/KF2G8)", "Zenodo (DOI: 10.5281/zenodo.20574265)")
        pcl = pcl.replace("10.17605/OSF.IO/KF2G8", "10.5281/zenodo.20574265")
        pcl = pcl.replace("OSF", "Zenodo/GitHub")
        pat_cl_path.write_text(pcl, encoding="utf-8")
    print("[OK] Updated Backup Cover Letters (npj Digital Medicine & Cell Press Patterns)")


if __name__ == "__main__":
    update_supplementary()
    update_npj_en_and_patterns()
    update_npj_zh_backup()
    update_backup_cover_letters()
