# Appendices A–C — freeze-preparation package (2026-09-03)

Companion to `PREREG_v2_draft_v0.2.md` §13 (freezing protocol). All data
produced locally / from public APIs on 2026-09-03; zero model calls.

---

## APPENDIX A — Multi-axis gold standard: sources and gene table

### A.1 Verified anchor citations (PubMed five-field checked 2026-09-03)

| Role | Citation (verified) |
|---|---|
| Primary AMD GWAS locus source (52-locus era) | Fritsche LG, et al. **A large genome-wide association study of age-related macular degeneration highlights contributions of rare and common variants.** *Nature Genetics* 2016 Feb;48(2). PMID **26691988**; doi:10.1038/ng.3448 |
| Most recent large AMD GWAS meta-analysis | He W, et al. **Genome-wide meta-analysis identifies risk loci and improves disease prediction of age-related macular degeneration.** *Ophthalmology* 2024 Jan. PMID **37634759**; doi:10.1016/j.ophtha.2023.08.023 |
| GA clinical-validation source (complement drugs, functional-endpoint caveat) | **Drug approval for the treatment of geographic atrophy: how we got here and where we need to go.** *American Journal of Ophthalmology* 2024 Jul. PMID **38387826**; doi:10.1016/j.ajo.2024.02.021 |
| Regulatory facts | SYFOVRE (pegcetacoplan, C3) DailyMed NDA217171, marketing start 2023-02-17; IZERVAY (avacincaptad pegol, C5) DailyMed, initial approval 2023; access dates to be stamped at freeze |

### A.2 Genetics evidence table (constructed 2026-09-03, live sources)

**File**: `APPENDIX_A_gwascat_gene_table.csv` (52 rows)

Construction rule (frozen): GWAS Catalog REST API (`www.ebi.ac.uk/gwas/rest/api`),
studies with disease trait "Age-related macular degeneration" (28 studies,
accessions GCST000001–GCST90559242, full list in pull artefacts), all
published associations; retain those with **p < 5×10⁻⁸** (176 associations);
author-reported genes aggregated per symbol (raw pull: `gwas_amd_sig_genes.json`).

- **Genetics grade** (deterministic from the pull): strong = reported in ≥3
  significant associations; moderate = 2; weak = 1.
- Overall Open Targets association score + rank for each gene joined from the
  live OT API pull (MONDO_0005150, 3,951 associated targets, 2026-09-03) —
  descriptive annotation only, **never a selection criterion** (the
  genetic-evidence selection is satisfied by construction via GWAS Catalog).
- Headlines of the table: CFH (12 hits, strong), ARMS2/HTRA1 (9, strong),
  CFB (7), C3 (5), C2 (5), TIMP3 (4), CFI/LIPC (3) … plus single-hit loci
  (RAD51B, COL8A1, TGFBR1, REST, VEGFA, CETP, TNFRSF10A, …).

### A.3 Three-column axis annotation (rule)

Per axis: genetics grade (mode of member genes from A.2); clinical validation
status (from A.1 regulatory facts: complement = two approved drugs on
anatomical endpoints; mitochondrial-mechanism device approved; others none);
functional-endpoint status (complement drugs = no visual-function benefit in
phase 3, per PMID 38387826).

### A.4 Axis grouping — EXECUTED 2026-09-03 (author sign-off day)

**Output**: `APPENDIX_A_reactome_axis_mapping.csv` (57 rows: 52 GWAS genes +
gen-1 Top-5). Reactome Analysis Service (identifiers/projection, per-symbol
queries, access date 2026-09-03), top-8 pathways per gene, frozen keyword
rules mapping pathway names to the seven pre-registered axes, conflicts
resolved by lowest FDR.

**Dual axis-assignment mechanism (binding)**:
(a) GWAS-significant genes assigned mechanically via Reactome keyword match —
28/52 mapped (complement 11, ECM 7, lipid/cholesterol 4, angiogenesis 2,
oxidative/mitochondrial 1, parainflammation 1); 24 genes match no
pre-registered axis and are reported verbatim with top pathways, never
forced into an axis.
(b) The POS-phagocytic-clearance axis is defined by **curated membership**
(known engulfment machinery: MERTK, MFGE8, ITGB5, GAS6, PTK2, TAM family)
because Reactome's coverage of outer-segment clearance is thin — the keyword
rule mis-assigns MERTK to "angiogenesis" (via "vascular wall"), a documented
overmatch; the curated definition stands, the mechanical result retained as
evidence of the rule's limits.

**Not executed** (honest): Fritsche 2016 / He 2024 locus-table transcription
cross-check; GWAS Catalog remains primary, cross-check may be added before
OSF freeze or reported as a limitation.

---

## APPENDIX B — Dimension ⑤ (coherence) machinery

### B.1 Pinned NLI checkpoint (HuggingFace API, 2026-09-03)

| Role | Model | Revision SHA | Last modified | Downloads |
|---|---|---|---|---|
| **Primary (deterministic)** | `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | `6f5cf0a2b59cabb106aca4c287eed12e357e90eb` | 2024-04-11 | 600k+ |
| Secondary (optional stability check) | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` | `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7` | 2024-04-11 | — |

Weights downloaded at freeze; full file-level SHA-256 manifest of the
checkpoint directory recorded in the deposit. Contradiction threshold
**P(contradiction) > 0.75** in both premise/hypothesis orderings (frozen).

### B.2 Atomic-assertion extraction (deterministic, no LLM)

1. Unit = sentence (frozen splitter: whitespace sentence segmentation on
   logged agent outputs; tables serialised cell-by-cell).
2. An assertion is any sentence containing ≥1 **normalised entity**:
   entity normalisation via the pool's own `gene_symbol` + `aliases` +
   `hgnc_id` columns (frozen map, 3,872 genes) and HPO term IDs (text label
   matched against the pool's 8,342 distinct HPO labels, exact match,
   case-insensitive).
3. Assertion pair = two assertions from **different agents/stages** sharing
   ≥1 normalised entity.
4. Contradiction = NLI(primary model) contradiction-probability > 0.75 in
   both orderings.
5. Reported: contradictions per 1,000 assertions; resolution rate (share of
   contradictions that later-stage logs explicitly address vs silently
   propagate). Descriptive, bootstrap CI, no confirmatory test.
6. LLM judge (deepseek-v4-pro) rates a 10% subsample; reported only as NLI
   agreement check, never as the primary measurement.

---

## APPENDIX C — Six-member confirmatory family: power tables

Simulation: `scripts/power_family6.py` (seed 20260101, NSIM = 1,500,
β-binomial replicates with ICC). C-v4 doses are the **realised IC fractions
of the F14-redrawn 123-pair set** (median 25%-arm dose 0.276 [IQR
0.261–0.292], 50%-arm 0.520 — re-run against `_f14` after supersession;
dose homogeneity essentially unchanged from the first redraw, both far
tighter than the old 40).

| Member | Scenario → power | Reading |
|---|---|---|
| 1. B arm contrast (RD, 14 domains × 30 slots) | Δ = 0.10–0.30 → **1.00** at all p0 tested | amply powered |
| 2. C-v4 dose slope β₁ (n=120, R=3, ICC .5) | true slope 0.3 → **0.93**; ≥0.5 → **1.00** | well powered |
| 3. C-v4 arm×dose β₃ | slope diff 0.2 → **0.29**; 0.35 → 0.71; 0.5 → 0.96 | **honest weak spot**: only large interactions detectable; pre-registered as such |
| 4. Dim-② cross-vs-within-arm Jaccard (R=3/arm) | Jw=0.7→0.8, Jc=0.3→0.4 → **0.77–0.80**; collapses to 0.10 if Jw=0.6 | conditional on within-arm stability; if Jw itself is low the test cannot separate — pre-registered reading rule already handles this (report "no separation signal") |
| 5. Dim-④ observed vs bootstrap null | null-mean − true-gap ≥0.3 → **0.86–0.99**; 0.67 at gap 0.3 with noisy null | good discrimination when gap exists |
| 6. Dim-⑥ calibration slope (n=250 statements) | true slope = 1.0 → 0.05 (valid size); 0.8 → 0.37; 0.6 → **0.90**; ≤0.4 → **1.00** | literature places verbalised-confidence slopes at ≈0–0.4 → near-certain detection if reality is typical |

**Family-level note**: with 6 BH-FDR-corrected members, members 1, 2 and 6
carry the confirmatory weight; member 3 is powered only for large
interactions and member 4 is conditional — both facts are stated in the
preregistration rather than discovered post hoc.

---

## Freeze-prep status after this package (§13 mapping)

| §13 step | Status |
|---|---|
| 1. Appendices A–B populated | ✅ this file + gene table CSV (A.4 sub-tasks: Reactome grouping script at freeze) |
| 2. C-v4 redraw executed and frozen | ✅ **F14-ORIGINAL**: `expC_v4_pairs_120_f14.csv` (sha256 `91dd96b1…`) + `expC_v4_heldout_30_f14.csv` (`e3db7837…`, never-published reserve) + `expC_v4_redraw_manifest_f14.json`; n=123, frozen-40 nested ✓; era×footprint ρ = **−0.166 (p=0.067, ns)** vs old-40 −0.516 — F14 confound eliminated by design; footprint fetched for ALL 3,872 pool genes (zero failures after retry pass); first substituted-design files quarantined in `superseded/` |
| 3. Appendix C power tables | ✅ this file + `scripts/power_family6.py` |
| 4. Author sign-off | ⬜ next |
| 5. OSF registration + hash seal | ⬜ after sign-off |
| 6. Probe v2 → first experimental call | ⬜ after 5 |

**Design-deviation flag RESOLVED** (2026-09-03): the author ordered the
footprint column supplemented ("该补充的补充"); all 3,872 pool-gene PubMed
counts were then fetched (frozen query, single date, 497 transient failures
all recovered in a retry pass, zero missing), and the redraw was re-executed
under the gate-review F14 **original** stratification (footprint quartile ×
era). The substituted design (era × ClinGen × organ) is quarantined in
`superseded/` with a README. No deviation remains for author approval.
