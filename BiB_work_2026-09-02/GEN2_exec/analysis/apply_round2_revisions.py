from pathlib import Path
import re

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
MS_PATH = BASE / "MANUSCRIPT_GEN2_v1.0.md"
SUPP_PATH = BASE / "SUPPLEMENTARY_GEN2_v1.0.md"
CL_PATH = BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md"

ms = MS_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
supp = SUPP_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
cl = CL_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")

def must_replace(text, old, new, label):
    assert old in text, f"FAILED to find target for {label}:\n{old[:120]}"
    return text.replace(old, new, 1)

# 1. P0-1: Summary tightening (<= 240 words) + remove 'systematically' in The bigger picture
old_bp = "exhibit severe Slot-A primacy bias that systematically extinguishes late-indexed biological pathways"
new_bp = "exhibit severe Slot-A primacy bias that extinguishes late-indexed biological pathways"
ms = must_replace(ms, old_bp, new_bp, "Bigger picture 'systematically'")

old_summary = """## Summary
Autonomous multi-agent systems increasingly adopt a canonical generate, pairwise-tournament, and literature-grounding workflow to propose therapeutic targets. However, whether test-time reasoning makes these pipelines trustworthy, and whether their failure modes can be algorithmically rectified, remains unresolved. Here we present **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost algorithmic remediation framework covering faithfulness, mechanistic reasoning versus retrieval, positional fairness, cross-run stability, cross-agent logical coherence, and confidence calibration. Across 9,130 live calls (35.58 million internal reasoning tokens; 93.83% of all generated tokens) spanning two frontier reasoning architectures (GLM-5.3 and DeepSeek-V4-Pro) and 136 disease contexts (12 end-to-end discovery runs in dry age-related macular degeneration and amyotrophic lateral sclerosis, a 14-domain randomized citation trial of 1,260 slots, and a 120-disease Mendelian phenotype-perturbation benchmark), we uncover a test-time reasoning paradox: deeper chain-of-thought does not self-correct structural pipeline vulnerabilities. First, naive identifier checks overestimate citation faithfulness (98.3% existent PMIDs), whereas two-tier semantic verification reveals that 58.3% of protocol citations are Trojan horse citations (real PMIDs misattributed to unsupported claims). In our 14-domain randomized trial, an epistemic grounding gate reduces ungrounded citations by 54.5 percentage points ($p = 0.00097$), eliminates fabricated PMIDs ($3.10\\%$ to $0.00\\%$, Wilcoxon $p = 0.0103$, Benjamini–Hochberg $q = 0.0310$), and cuts citation reasoning tokens by 86.2%. Second, single-order Tournament I judging exhibits a 71.3% Slot-A win rate ($p = 4.37 \\times 10^{-148}$), causing severe pathway extinction of Bucket-3 extracellular/complement mechanisms ($\\chi^2 = 55.40, p = 9.33 \\times 10^{-13}$), while 43.0% of Tournament II pairs flip under A/B reversal ($97.0\\%$ toward Slot A) accompanied by a 2.5-fold surge in DeBERTa-v3 natural language inference (NLI) self-contradiction. Third, a 10,000-draw verdict-table bootstrap proves that cross-run divergence stems from upstream generation and Tournament I order bias rather than Tournament II judging noise ($p = 0.0002, q = 0.0012$). Introducing Order-Adjusted Bradley–Terry–Luce (BTL) ranking with NLI-discordance neutralization reduces Bucket-3 pathway distortion by 72.8% and rescues causally validated disease pathways, while Leave-One-Run-Out Platt scaling reduces expected calibration error by 87.8% (0.222 to 0.027). **STAR-Audit** provides a portable methodological standard that both diagnoses and repairs autonomous discovery pipelines prior to wet-lab commitment."""

new_summary = """## Summary
Autonomous multi-agent systems combine candidate generation, pairwise tournaments, and literature grounding to propose therapeutic targets, yet whether extended test-time reasoning makes these pipelines trustworthy remains unresolved. Here we present **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost remediation framework covering faithfulness, reasoning versus retrieval, positional fairness, cross-run stability, logical coherence, and confidence calibration. Auditing 9,130 live calls (35.58 million internal reasoning tokens; 93.83% of output) across GLM-5.3 and DeepSeek-V4-Pro over 136 disease contexts (12 discovery runs in dry age-related macular degeneration and amyotrophic lateral sclerosis, a 14-domain randomized citation trial of 1,260 slots, and a 120-disease Mendelian phenotype-deletion benchmark) reveals a test-time reasoning paradox: deeper chain-of-thought fails to self-correct pipeline biases. First, naive identifier checks score 98.3% of protocol PMIDs as existent, whereas two-tier semantic verification exposes 58.3% Trojan horse citations (real PMIDs attached to unsupported claims). Across 14 domains, an epistemic grounding gate cuts ungrounded citations by 54.5 percentage points ($p = 0.00097$), eliminates fabricated PMIDs ($3.10\\%$ to $0.00\\%, p = 0.0103, q = 0.0310$), and reduces citation reasoning tokens by 86.2%. Second, single-order Tournament I judging exhibits a 71.3% Slot-A win rate ($p = 4.37 \\times 10^{-148}$) that suppresses Bucket-3 extracellular/complement pathways ($\\chi^2 = 55.40, p = 9.33 \\times 10^{-13}$), while 43.0% of Tournament II pairs flip under A/B reversal ($97.0\\%$ toward Slot A) with a 2.5-fold surge in natural language inference (NLI) contradiction. Third, a 10,000-draw verdict-table bootstrap proves that cross-run divergence arises upstream of Tournament II ($p = 0.0002, q = 0.0012$). Order-Adjusted Bradley–Terry–Luce ranking with NLI neutralization cuts Bucket-3 distortion by 72.8% and rescues validated targets, while Leave-One-Run-Out Platt scaling reduces calibration error by 87.8% (0.222 to 0.027)."""

ms = must_replace(ms, old_summary, new_summary, "Summary tightening")

# 2. Introduction edits: remove 'corrected', 'systematically', 'rigorous', split Para 4 (303w -> 2 paras)
ms = must_replace(ms, "how can structural failure modes be corrected before committing experimental resources?", "how can structural failure modes be resolved before committing experimental resources?", "Intro 'corrected'")
ms = must_replace(ms, "presentation order could systematically distort BTL tournament survival. Third, language models struggle to separate genuine mechanistic deduction from memorized literature associations [9, 17] and systematically overstate verbalized confidence", "presentation order could structurally distort BTL tournament survival. Third, language models struggle to separate genuine mechanistic deduction from memorized literature associations [9, 17] and consistently overstate verbalized confidence", "Intro 'systematically'")
ms = must_replace(ms, "or general reproducibility recommendations for on-the-data-path LLM provenance [27].", "or general reproducibility recommendations distinguishing on-the-data-path LLM calls from off-the-data-path deterministic code [27].", "Intro Dunn [27] integration")
ms = must_replace(ms, "To establish a rigorous, generalizable standard for autonomous biomedical discovery, we developed **STAR-Audit**", "To establish a quantitative, generalizable standard for autonomous biomedical discovery, we developed **STAR-Audit**", "Intro 'rigorous'")
ms = must_replace(ms, "and 136 distinct biomedical disease contexts (Figure 1A–D). **STAR-Audit** advances beyond prior evaluation benchmarks in three fundamental respects.", "and 136 distinct biomedical disease contexts (Figure 1A–D).\n\n**STAR-Audit** advances beyond prior evaluation benchmarks in three fundamental respects.", "Intro Para 4 split")

# 3. Results R1: split Block 1, Block 2, Block 3 with blank lines; move [INSERT TABLE 2 ABOUT HERE] right after R1
old_r1_blocks = """1. **Block 1 (Replicated Multi-Arm End-to-End Parent Discovery Runs, $N = 12$ complete runs, 7,890 live calls):** A $2 \\times 2 \\times 3$ factorial design crossing two complex neurodegenerative disorders with distinct genetic architectures, dry age-related macular degeneration (dAMD; multi-axis complement, extracellular matrix, lipid, and retinal pigment epithelium [RPE] phagocytic pathology [31–38]) and amyotrophic lateral sclerosis (ALS; dominated by TDP-43 nuclear depletion and cryptic exon splicing alongside SOD1/autophagy axes [39–42]), across two epistemic arms (strictly Blind mechanism-first generation with automated forbidden-token redrafting [Supplementary Note 1] versus PubMed Abstract-Injected Retrieval) with $R = 3$ independent end-to-end replicates per cell. Each run executes all six canonical stages: Step 1 (30 candidate mechanisms across three functional buckets), Step 2 (Tournament I: 300 single-order pairwise comparisons aggregated via Hunter minorization-maximization BTL to select the Top 10), Step 3 (10 detailed target dossiers), Step 4 (Tournament II: all 45 candidate pairs evaluated by three specialized judges [SCIENCE, METHODS, NOVELTY] in both A-then-B and B-then-A presentation orders, yielding 270 verdicts per run), Step 5 (BTL Top-5 selection; complete 60-target dossier inventory in Supplementary Table S1 and run-by-run tournament audit in Supplementary Table S2), and Step 6 (experimental protocol synthesis with 30 structured PubMed citation slots per run; 360 slots across all 12 runs).
2. **Block 2 (Experiment B Randomized Citation-Gating Trial, 14 clinical disease domains, 1,260 citation slots, 396 live calls):** Across 14 diverse disease domains spanning respiratory, musculoskeletal, cardiovascular, dermatologic, neurosensory, hematologic, craniofacial, oncologic, lysosomal, syndromic, renal, infectious, retinal, and leukodystrophy disorders (70 generated hypotheses; domain breakdown in Supplementary Table S3), we randomized Stage-2 literature grounding into three arms (420 citation slots per arm): `as_discovered` (standard unguarded citation generation), `abstain_probe` (gentle prompt permission to emit `NO_CITATION` if uncertain), and `gated` (an epistemic grounding gate requiring verifiable identifier-claim alignment or mandatory abstention).
3. **Block 3 (Experiment C-v4 Multi-Vendor Phenotype Information-Content Deletion Benchmark, 120 Mendelian diseases, 804 logged perturbation calls [630 non-truncated valid calls analyzed in GLMM] across GLM-5.3 and DeepSeek-V4-Pro):** Using 120 rare Mendelian disease-gene pairs from the Human Phenotype Ontology (HPO [43]) strictly disjoint from dAMD and ALS, we masked all disease names and OMIM identifiers and deleted 0%, 25% (realized mean 28.4% in `del_topIC`; 29.1% pooled across arms), or 50% (realized mean 52.6% in `del_topIC`; 54.8% pooled across arms) of total phenotype information content (IC) under two contrast arms: `del_topIC` (removing the most specific, diagnostic HPO terms) versus `del_lowIC_matched` (removing IC-sum-matched low-specificity terms; cell-by-cell outcomes in Supplementary Table S4)."""

new_r1_blocks = """1. **Block 1 (Replicated Multi-Arm End-to-End Parent Discovery Runs, $N = 12$ complete runs, 7,890 live calls):** A $2 \\times 2 \\times 3$ factorial design crossing two complex neurodegenerative disorders with distinct genetic architectures, dry age-related macular degeneration (dAMD; multi-axis complement, extracellular matrix, lipid, and retinal pigment epithelium [RPE] phagocytic pathology [31–38]) and amyotrophic lateral sclerosis (ALS; dominated by TDP-43 nuclear depletion and cryptic exon splicing alongside SOD1/autophagy axes [39–42]), across two epistemic arms (strictly Blind mechanism-first generation with automated forbidden-token redrafting [Supplementary Note 1] versus PubMed Abstract-Injected Retrieval) with $R = 3$ independent end-to-end replicates per cell. Each run executes all six canonical stages: Step-1 ideation (30 candidate mechanisms across three functional buckets), Step-2 Tournament I screening (300 single-order pairwise comparisons aggregated via Hunter minorization-maximization BTL to select the Top 10), Step-3 target dossier expansion (10 detailed dossiers), Step-4 Tournament II judging (all 45 candidate pairs evaluated by three specialized judges [SCIENCE, METHODS, NOVELTY] in both A-then-B and B-then-A presentation orders, yielding 270 verdicts per run), Step-5 BTL Top-5 selection (complete 60-target dossier inventory in Supplementary Table S1 and run-by-run tournament breakdown in Supplementary Table S2), and Step-6 experimental protocol synthesis (30 structured PubMed citation slots per run; 360 slots across all 12 runs).

2. **Block 2 (Experiment B Randomized Citation-Gating Trial, 14 clinical disease domains, 1,260 citation slots, 396 live calls):** Across 14 diverse disease domains spanning respiratory, musculoskeletal, cardiovascular, dermatologic, neurosensory, hematologic, craniofacial, oncologic, lysosomal, syndromic, renal, infectious, retinal, and leukodystrophy disorders (70 generated hypotheses; domain breakdown in Supplementary Table S3), we randomized Stage-2 literature grounding into three arms (420 citation slots per arm): `as_discovered` (standard unguarded citation generation), `abstain_probe` (gentle prompt permission to emit `NO_CITATION` if uncertain), and `gated` (an epistemic grounding gate requiring verifiable identifier-claim alignment or mandatory abstention).

3. **Block 3 (Experiment C-v4 Multi-Vendor Phenotype Information-Content Deletion Benchmark, 120 Mendelian diseases, 804 logged perturbation calls [630 non-truncated valid calls analyzed in GLMM] across GLM-5.3 and DeepSeek-V4-Pro):** Using 120 rare Mendelian disease-gene pairs from the Human Phenotype Ontology (HPO [43]) strictly disjoint from dAMD and ALS, we masked all disease names and OMIM identifiers and deleted 0%, 25% (realized mean 28.4% in `del_topIC`; 29.1% pooled across arms), or 50% (realized mean 52.6% in `del_topIC`; 54.8% pooled across arms) of total phenotype information content (IC) under two contrast arms: `del_topIC` (removing the most specific, diagnostic HPO terms) versus `del_lowIC_matched` (removing IC-sum-matched low-specificity terms; cell-by-cell outcomes in Supplementary Table S4)."""

ms = must_replace(ms, old_r1_blocks, new_r1_blocks, "R1 blocks split")

# Move [INSERT TABLE 2 ABOUT HERE] to right after R1
ms = must_replace(ms, "alongside a dominant literature-footprint effect across both vendors (Figure 1C, D; Table 2).\n\n### R2.", "alongside a dominant literature-footprint effect across both vendors (Figure 1C, D; Table 2).\n\n[INSERT TABLE 2 ABOUT HERE]\n\n### R2.", "Insert Table 2 after R1")
ms = must_replace(ms, "with **zero additional LLM API calls** (Figure 6D).\n\n[INSERT TABLE 2 ABOUT HERE]\n\n## Discussion", "with **zero additional LLM API calls** (Figure 6D).\n\n## Discussion", "Remove duplicate Table 2 placeholder")

# 4. Results R3: split 481w block into 3 paragraphs (<225w each)
ms = must_replace(ms, "hierarchy revealed a **2.8- to 4.3-fold convergence surge**, governed by the underlying genetic architecture of each disorder:\n- **ALS exhibits", "hierarchy revealed a **2.8- to 4.3-fold convergence surge**, governed by the underlying genetic architecture of each disorder:\n\n- **ALS exhibits", "R3 split 1")
ms = must_replace(ms, "over lead-gene Jaccard; cross-arm $J_{\\text{axis}} = 0.4963$).\n- **dAMD exhibits", "over lead-gene Jaccard; cross-arm $J_{\\text{axis}} = 0.4963$).\n\n- **dAMD exhibits", "R3 split 2")
ms = must_replace(ms, "two deeper mechanistic findings emerged from Experiment C-v4:\n1. **Pretraining", "two deeper mechanistic findings emerged from Experiment C-v4:\n\n1. **Pretraining", "R3 C-v4 split 1")
ms = must_replace(ms, "on GLM-5.3; Figure 3C).\n2. **Degraded", "on GLM-5.3; Figure 3C).\n\n2. **Degraded", "R3 C-v4 split 2")

# 5. Results R4: split 267w Tournament I paragraph into 2 paragraphs (<150w each) and remove 'systematically'
old_r4_t1 = "As a direct consequence of 71.3% Slot-A primacy bias, **standard unadjusted BTL ranking caused severe index-order pathway extinction** (Figure 4B): across all 120 Top-10 slots in the 12 runs (expected uniform distribution: $40 : 40 : 40$), `Bucket 1` captured **78 slots (65.0%)**, `Bucket 2` captured **26 slots (21.7%)**, and `Bucket 3` was compressed to just **16 slots (13.3%)** ($\\chi^2 = 55.40, \\text{df} = 2, p = 9.33 \\times 10^{-13}$). In dAMD and ALS, this positional artifact systematically eliminated validated extracellular matrix"
new_r4_t1 = "\n\nAs a direct consequence of 71.3% Slot-A primacy bias, **standard unadjusted BTL ranking caused severe index-order pathway extinction** (Figure 4B): across all 120 Top-10 slots in the 12 runs (expected uniform distribution: $40 : 40 : 40$), `Bucket 1` captured **78 slots (65.0%)**, `Bucket 2` captured **26 slots (21.7%)**, and `Bucket 3` was compressed to just **16 slots (13.3%)** ($\\chi^2 = 55.40, \\text{df} = 2, p = 9.33 \\times 10^{-13}$). In dAMD and ALS, this positional artifact eliminated validated extracellular matrix"
ms = must_replace(ms, old_r4_t1, new_r4_t1, "R4 T1 split & 'systematically'")

# 6. Results R5: replace 'cluster-robust' & 'systematic', and split Paradox 1-3 list with blank lines
ms = must_replace(ms, "the cluster-robust logistic calibration slope was $\\hat{\\beta}_{\\text{cal}} = 0.655$", "the run-clustered sandwich logistic calibration slope was $\\hat{\\beta}_{\\text{cal}} = 0.655$", "R5 'cluster-robust'")
ms = must_replace(ms, "revealed severe systematic overconfidence: mean predicted confidence", "revealed pronounced directional overconfidence: mean predicted confidence", "R5 'systematic'")
ms = must_replace(ms, "correlates with *worse* bias and *higher* error rates rather than self-correction (Figure 5C, D):\n1. **Paradox 1", "correlates with *worse* bias and *higher* error rates rather than self-correction (Figure 5C, D):\n\n1. **Paradox 1", "R5 Paradox split 1")
ms = must_replace(ms, "rationalizations for position-flipped verdicts.\n2. **Paradox 2", "rationalizations for position-flipped verdicts.\n\n2. **Paradox 2", "R5 Paradox split 2")
ms = must_replace(ms, "to attach to unsupported claims.\n3. **Paradox 3", "to attach to unsupported claims.\n\n3. **Paradox 3", "R5 Paradox split 3")

# 7. Results R6: split 757w rescued pathways block into 5 clean paragraphs (<235w each) & replace 'strikingly'
ms = must_replace(ms, "Applying Order-Adjusted BTL to Tournament I across all 12 runs produced an immediate structural and biological correction:\n- **72.8% reduction", "Applying Order-Adjusted BTL to Tournament I across all 12 runs produced an immediate structural and biological correction:\n\n- **72.8% reduction", "R6 split 1")
ms = must_replace(ms, "slots; Figure 4B, Figure 6C).\n- **Direct algorithmic rescue", "slots; Figure 4B, Figure 6C).\n\n- **Direct algorithmic rescue", "R6 split 2")
ms = must_replace(ms, "Supplementary Table S2):\n  - **Rescue of `GAS6/MERTK`", "Supplementary Table S2):\n\n  - **Rescue of `GAS6/MERTK`", "R6 split 3")
ms = must_replace(ms, "MERTK inhibition [33, 48–51].\n  - **Rescue of `TIMP3/MMP9`", "MERTK inhibition [33, 48–51].\n\n  - **Rescue of `TIMP3/MMP9`", "R6 split 4")
ms = must_replace(ms, "gene therapy (`AAVCAGsCD59` [34, 54]).\n  - **Rescue of `MTTP/APOB100/SOAT1`", "gene therapy (`AAVCAGsCD59` [34, 54]).\n\n  - **Rescue of `MTTP/APOB100/SOAT1`", "R6 split 5")
ms = must_replace(ms, "*Mttp*-ablation models [36, 55].\n  - **Rescue of `MMP9/LAMA1`", "*Mttp*-ablation models [36, 55].\n\n  - **Rescue of `MMP9/LAMA1`", "R6 split 6")
ms = must_replace(ms, "Even more strikingly, in `ALS_retrieval_R3`", "In parallel, in `ALS_retrieval_R3`", "R6 'strikingly'")

# 8. Discussion: split numbered/bulleted items with blank lines & enrich Dunn et al. [27] dialogue (P0-3)
ms = must_replace(ms, "extended reasoning exacerbates failure across three distinct surfaces:\n1. **In literature grounding", "extended reasoning exacerbates failure across three distinct surfaces:\n\n1. **In literature grounding", "Disc split 1")
ms = must_replace(ms, "unproductive memory dredging early.\n2. **In pairwise tournaments", "unproductive memory dredging early.\n\n2. **In pairwise tournaments", "Disc split 2")
ms = must_replace(ms, "candidate is placed in Slot A.\n3. **In phenotype-driven", "candidate is placed in Slot A.\n\n3. **In phenotype-driven", "Disc split 3")
ms = must_replace(ms, "that the other five cannot detect:\n- A pipeline can achieve", "that the other five cannot detect:\n\n- A pipeline can achieve", "Disc split 4")
ms = must_replace(ms, "calibration error (Dimension 6)**.\n- Conversely, applying", "calibration error (Dimension 6)**.\n\n- Conversely, applying", "Disc split 5")
ms = must_replace(ms, "completely untouched.\n- Finally, **Tournament II", "completely untouched.\n\n- Finally, **Tournament II", "Disc split 6")

old_disc_dunn = "and provenance frameworks for reproducible LLM-assisted analyses [26, 27]. **STAR-Audit** advances this landscape by operating at the **end-to-end discovery workflow level** under preregistered statistical governance, demonstrating that:"
new_disc_dunn = "and reproducibility frameworks distinguishing *on-the-data-path* LLM inference from *off-the-data-path* deterministic code execution (the 'rerun-without-LLM test' [26, 27]). **STAR-Audit** operationalizes and extends this architectural principle across the **end-to-end discovery workflow** under preregistered statistical governance: while hypothesis generation and pairwise judging necessarily operate *on the data path*, our rectification modules move tournament debiasing, NLI discordance filtering, probability recalibration, and two-tier bibliographic verification *off the data path* into deterministic mathematical operators. Specifically, we demonstrate that:"
ms = must_replace(ms, old_disc_dunn, new_disc_dunn, "Disc Dunn [27] enrichment")

# 9. Limitations of the Study: split items 1..5 into distinct paragraphs & replace 'unique' with 'distinct'
ms = must_replace(ms, "required to extend each boundary:\n1. **Orthogonal", "required to extend each boundary:\n\n1. **Orthogonal", "Lim split 1")
ms = must_replace(ms, "hit-rate gains.]\n2. **Discrete", "hit-rate gains.]\n\n2. **Discrete", "Lim split 2")
ms = must_replace(ms, "permutation $p < 0.01$.]\n3. **Budget-governed", "permutation $p < 0.01$.]\n\n3. **Budget-governed", "Lim split 3")
ms = must_replace(ms, "interaction testing.]\n4. **Automated", "interaction testing.]\n\n4. **Automated", "Lim split 4")
ms = must_replace(ms, "across 956 unique cached PMIDs)", "across 956 distinct cached PMIDs)", "Lim 'unique'")
ms = must_replace(ms, "invariant across arms.]\n5. **Lexical", "invariant across arms.]\n\n5. **Lexical", "Lim split 5")

# 10. STAR Methods: split lists with blank lines & replace 'unique' and 'robust'
ms = must_replace(ms, "PubMed verification cache (956 unique PMIDs)", "PubMed verification cache (956 distinct PMIDs)", "Methods 'unique'")
ms = must_replace(ms, "`hit@10` was modeled via cluster-robust logistic regression (clustered by `disease_id`)", "`hit@10` was modeled via disease-clustered sandwich logistic regression (clustered by `disease_id`)", "Methods 'cluster-robust'")
ms = must_replace(ms, "with run-clustered robust standard errors.", "with run-clustered sandwich standard errors.", "Methods 'robust'")
ms = must_replace(ms, "factorial design:\n- **Step 1", "factorial design:\n\n- **Step 1", "Methods Step 1 split")
ms = must_replace(ms, "upon any lexical hit.\n- **Step 2", "upon any lexical hit.\n\n- **Step 2", "Methods Step 2 split")
ms = must_replace(ms, "advance to Step 3.\n- **Step 3", "advance to Step 3.\n\n- **Step 3", "Methods Step 3 split")
ms = must_replace(ms, "confidence ($0\\text{--}100$).\n- **Step 4", "confidence ($0\\text{--}100$).\n\n- **Step 4", "Methods Step 4 split")
ms = must_replace(ms, "(Supplementary Table S1).\n- **Step 6", "(Supplementary Table S1).\n\n- **Step 6", "Methods Step 6 split")

ms = must_replace(ms, "rectification formulas\n1. **Dimension 1", "rectification formulas\n\n1. **Dimension 1", "Methods Dim 1 split")
ms = must_replace(ms, "semantic overlap).\n2. **Dimension 2", "semantic overlap).\n\n2. **Dimension 2", "Methods Dim 2 split")
ms = must_replace(ms, "literature footprint.\n3. **Dimension 3", "literature footprint.\n\n3. **Dimension 3", "Methods Dim 3 split")
ms = must_replace(ms, "Top-5 BTL selection.\n4. **Dimension 4", "Top-5 BTL selection.\n\n4. **Dimension 4", "Methods Dim 4 split")
ms = must_replace(ms, "sampling noise.\n5. **Dimension 5", "sampling noise.\n\n5. **Dimension 5", "Methods Dim 5 split")
ms = must_replace(ms, "(Supplementary Table S5).\n6. **Dimension 6", "(Supplementary Table S5).\n\n6. **Dimension 6", "Methods Dim 6 split")

# 11. Supplementary edits: 'unique' -> 'distinct', unify en-dashes
supp = must_replace(supp, "cached all 956 unique cited PMIDs", "cached all 956 distinct cited PMIDs", "Supp 'unique' 1")
supp = must_replace(supp, "| Unique Diseases |", "| Distinct Diseases |", "Supp 'Unique' 2")
supp = supp.replace("Bradley-Terry-Luce", "Bradley–Terry–Luce")
supp = supp.replace("Newton-Raphson", "Newton–Raphson")
supp = supp.replace("Pelizaeus-Merzbacher", "Pelizaeus–Merzbacher")
supp = supp.replace("17K-30K", "17K–30K")
supp = supp.replace("2-8 minutes", "2–8 minutes")

# 12. Cover Letter edits: 6 Multi-Panel Figures -> 7 Figures, Mann-Whitney -> Mann–Whitney
cl = must_replace(cl, "Mann-Whitney pseudo-replication", "Mann–Whitney pseudo-replication", "CL Mann–Whitney")
cl = must_replace(cl, "(STAR Methods + 6 Multi-Panel Figures + 6 Supplementary Tables):", "(STAR Methods + 7 Figures + 6 Supplementary Tables):", "CL 7 Figures")

MS_PATH.write_text(ms, encoding="utf-8")
SUPP_PATH.write_text(supp, encoding="utf-8")
CL_PATH.write_text(cl, encoding="utf-8")
print("SUCCESS: Applied all Round-2 revisions cleanly to MANUSCRIPT, SUPPLEMENTARY, and COVER_LETTER.")
