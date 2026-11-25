# STAR-Audit (v2.3 Aligned): Off-the-Data-Path Auditing and Zero-Call Algorithmic Rectification for Multi-Agent AI Discovery

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](https://opensource.org/licenses/MIT)

Official code, frozen protocol manifests, blinded human domain-expert calibration datasets, and offline verification suite for:

> **Auditing and rectifying reasoning, ranking, and grounding biases in agentic scientific discovery**  
> Jiangtao Sheng\*, Xueer Liu, Runmin Lin, Qiaochu Sun, Xiaoxuan Chen, Kangsheng Li, and Weiqiang Chen\*  
> *Department of Microbiology and Immunology & First Affiliated Hospital, Shantou University Medical College*

---

## Quickstart (`< 0.1 s`, Zero API Keys Required)

Verify all four deterministic **STAR-Audit** post-processing operators (`Module 1: Order-Adjusted BTL`, `Module 2: Selective LORO/LODO Platt Gate`, `Module 3: Epistemic Abstention + Closed-Loop Entrez Handoff`, and `Module 4: CoT-SRAD Stream Harvesting`) offline in `< 0.1 s` using only Python `>= 3.10`, `numpy`, and `scipy`:

```bash
python BiB_work_2026-09-02/GEN2_exec/star_audit_demo.py
```

Expected output:
- **`[Module 1 | OA-BTL]`**: Estimates Slot-A primacy intercept $\hat{\gamma} = +0.985$ (`OR = 2.68x`) on `ALS_retrieval_R3` (`n = 300` matches) and rescues `M29` (`CCS/ATP7A` copper axis) from `#15` into the surviving Top-10 (`#10`).
- **`[Module 2 | Selective Calibration Gate]`**: Preserves natively well-calibrated `Gemini-4-Argon-High` (`ECE = 0.0797`, `0/20` folds triggered at $\tau_{\text{ECE}} = 0.12$) while cutting `Gemini-3.8-Flash` (`0.5423 -> 0.0749`) and `Grok-4.7-Fast` (`0.1652 -> 0.0814`).
- **`[Module 3 | Epistemic Gate + Entrez Handoff]`**: Restores verified on-topic citation yield from `1.90%` (`Module 3a` alone) to **`100.00%`** (`420/420` slots) at **`0.00%`** ungrounded error and **`-90.41%`** median CoT tokens (`0` extra LLM calls).
- **`[Module 4 | CoT-SRAD]`**: Non-destructive `Module 4a` on the external `3,871`-gene Mendelian HGNC vocabulary rescues **`+48` net diagnoses** (`26.35% -> 33.97%`, `0` lost hits, exact McNemar $p = 7.11 \times 10^{-15}$).

---

## Repository Structure (`BiB_work_2026-09-02/GEN2_exec/`)

- `star_audit_demo.py` — Self-contained `< 0.1 s` offline verification script (works both inside the repository and as a standalone single file).
- `gen2_call.py`, `gen2_blind.py`, `gen2_pubmed.py`, `btl.py`, `gen2_canary.py` — Core deterministic execution harness, forbidden-token lexical scanner, NCBI Entrez client, Hunter-MM BTL solver, and `temperature = 0` canary monitor.
- `run_parent.py`, `run_expB_gen2.py`, `run_expC_v4.py`, `run_grok_cross_ecosystem.py` — Multi-block evaluation runners (`11,818` live invocations, `37.18M` reasoning and output tokens).
- `analysis/nc_upgrade_A1_A4_btl_validation.py` — Intra-bucket primacy proof (`68.21%`, $p = 1.51 \times 10^{-33}$), 400-simulation Monte Carlo identifiability & confounded-null verification, $\lambda \in [10^{-4}, 1.0]$ sweep, and Tournament II algebraic decomposition.
- `analysis/nc_upgrade_A2_module3_handoff.py` — Closed-loop `Module 3a + 3b` deterministic NCBI Entrez Boolean handoff (`1,049` cached candidate PMIDs in `nc_upgrade_entrez_handoff_cache.json`).
- `analysis/nc_upgrade_A3_A7_expc_calibration.py` — STROBE `804 -> 630` call accounting, HPO term-count starvation proof ($p = 4.18 \times 10^{-31}$), 5-way external `3,871`-HGNC `CoT-SRAD` ablation, and multi-cohort calibration benchmark.
- `analysis/nc_upgrade_A5_part1_tier2_and_cot_boxes.py` & `analysis/nc_upgrade_A5_part2_nli_audit.py` — Blinded `200`-item dual-expert audits (`expert_audit_tier2_100_annotated.csv`, `expert_audit_nli_100_annotated.csv`).
- `analysis/nc_v2_make_main_figs_canonical.py`, `analysis/nc_v2_make_supp_figs_canonical.py`, `analysis/nc_v2_export_source_data_canonical.py` — Deterministic 6-Main-Figure (`28`-panel), 4-Supplementary-Figure (`13`-panel), and `Source_Data_NC_v2.0.xlsx` (`11`-worksheet) generators.

## License

Released under the **MIT License**. Source data (`Source_Data_NC_v2.0.xlsx`), frozen protocol manifests, PubMed Entrez verification caches, and 200-item blinded domain-expert calibration datasets are included directly in this repository.
