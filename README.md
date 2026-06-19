# SDL-dAMD

Companion code for: **A measurable trustworthiness audit for AI-driven
scientific discovery** (Sheng et al., 2026).

This repository ships the open **credibility-audit harness** — a small,
dependency-light tool that computes the three *measurable* trustworthiness
metrics reported in the paper for the output of any autonomous
scientific-discovery pipeline. It does not score "intelligence" or "novelty";
it answers three concrete, checkable questions about a discovery run:

1. **Are the citations real and on-topic?** (hallucination rate, external PubMed round-trip)
2. **Did the system reason, or just look up a database?** (anti-retrieval separation)
3. **Did the LLM judge decide by content, or by where a candidate was printed?** (position-bias rate)

The harness reproduces the paper's headline dAMD Run 1 position-bias figure
exactly: **7 of 45 pairs flagged = 15.56 %** against the real tournament data.

---

## Repository contents

```
SDL-dAMD/
├── code/
│   ├── credibility_audit.py     # the harness (stdlib-first; SciPy optional)
│   ├── README.md                # harness documentation (the three metrics, CLI, schemas)
│   ├── REPORTING_TEMPLATE.md    # one-page fillable audit-triple report form
│   └── examples/                # synthetic demo inputs + expected output + NOTES
├── test_data/                   # stable synthetic inputs for the regression suite
├── expected_results/            # committed baseline for run_all_tests.sh
├── run_all_tests.sh             # regression suite (synthetic + optional real-data check)
├── requirements.txt             # Python dependencies (pip)
├── environment.yml              # Python dependencies (conda)
└── LICENSE                      # MIT
```

The audit harness in `code/` is the released, reproducible component. The
Bradley–Terry–Luce / Hunter-MM ranking implementation, the figure-generation
scripts, and the full sub-agent dispatch orchestration that produced the
paper's results are part of the audit trail deposited at Zenodo
(DOI [10.5281/zenodo.20574265](https://doi.org/10.5281/zenodo.20574265));
the harness here reads that data's schema and recomputes the three audit
metrics from it.

---

## Quick start

Python **3.8+**. The core harness needs no third-party packages; SciPy is
optional (used only for the exact Mann–Whitney U in metric 2; a stdlib
normal-approximation fallback is used otherwise).

```bash
# optional, for exact Mann–Whitney U
pip install -r requirements.txt    # or: conda env create -f environment.yml

# run the regression suite on the bundled synthetic data
bash run_all_tests.sh
# expected: 3 passed, 0 failed
```

To run the harness directly on its synthetic demo set:

```bash
python code/credibility_audit.py \
  --verdicts test_data/verdicts \
  --citations test_data/test_citations.json \
  --sdl-genes MECHA1,MECHA2,MECHA3,MECHA4,MECHA5,SHARED1 \
  --retrieval-genes LOOKUP1,LOOKUP2,LOOKUP3,LOOKUP4,LOOKUP5,SHARED1 \
  --ot-scores test_data/test_ot_scores.json \
  --out report.md
```

Every metric is optional; supply whichever input group you have. Full CLI,
input schemas, and per-metric interpretation are in
[`code/README.md`](code/README.md).

---

## Reproducing the paper's dAMD Run 1 position-bias result (7 / 45)

The real 45-pair × 6-verdict tournament data is in the Zenodo deposit, not
shipped here. To reproduce the headline figure:

1. Download `audit_data_for_zenodo.zip` from
   [doi.org/10.5281/zenodo.20574265](https://doi.org/10.5281/zenodo.20574265).
2. Extract the `tournament2_verdicts/` directory (270 JSON files,
   `pair_<NN>_<a|b>_judge<R>.json`; schema documented in
   [`code/examples/NOTES.md`](code/examples/NOTES.md)).
3. Run:
   ```bash
   python code/credibility_audit.py --verdicts /path/to/tournament2_verdicts/
   ```
   Expected: `Pairs scored: 45`, `Flagged: 7`, `Position-bias rate = 15.56 %`,
   flagged pairs `pair_04, pair_07, pair_12, pair_19, pair_22, pair_25, pair_38`.

---

## Data & code availability

- **Audit-trail data** (all sub-agent JSON outputs, tournament checkpoints, BTL
  input matrices, blind-scan logs, citation pools, position-bias decision log,
  cross-seed and cross-model replications, ALS Run 2 data): openly deposited at
  Zenodo, [10.5281/zenodo.20574265](https://doi.org/10.5281/zenodo.20574265)
  (CC BY 4.0).
- **Code** (this repository): MIT-licensed. The study used only public data
  sources (PubMed and the Open Targets Platform).

---

## Citation

If you use this harness, please cite:

> Sheng J. et al. **A measurable trustworthiness audit for AI-driven
> scientific discovery.** (2026).

---

## Contact

Jiangtao Sheng — Department of Microbiology and Immunology, Shantou University
Medical College — jtsheng@stu.edu.cn
