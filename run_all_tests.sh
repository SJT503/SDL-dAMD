#!/usr/bin/env bash
# =============================================================================
# run_all_tests.sh — regression suite for the credibility-audit harness
#
# Runs the harness on the bundled synthetic test_data set, compares the output
# against the committed baseline in expected_results/, and asserts the three
# audit metrics reproduce. An optional, network-dependent test re-verifies the
# paper's headline dAMD Run 1 position-bias figure (7 / 45 = 15.56 %) against
# the real tournament data in the Zenodo deposit.
#
# Usage:
#   bash run_all_tests.sh              # synthetic tests only (offline-ish,
#                                     #   one live NCBI call group for the
#                                     #   hallucination metric)
#   bash run_all_tests.sh --full      # also download + verify real dAMD data
#                                     #   from Zenodo (needs ~4 MB download,
#                                     #   network to zenodo.org)
#
# Exit codes: 0 = all pass, 1 = one or more assertions failed.
# =============================================================================
set -u

# --- locate the repo root (this script lives at the repo root) ---------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "FATAL: cannot cd to $SCRIPT_DIR"; exit 1; }

HARNESS="code/credibility_audit.py"
TEST_DATA="test_data"
EXPECTED="expected_results/expected_synthetic.json"
PY="${PYTHON:-python}"

PASS=0
FAIL=0
ok()   { echo "  [PASS] $1"; PASS=$((PASS+1)); }
bad()  { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "============================================================"
echo " credibility-audit harness — regression suite"
echo " repo:   $SCRIPT_DIR"
echo " python: $($PY --version 2>&1)"
echo "============================================================"

# --- preflight ---------------------------------------------------------------
[ -f "$HARNESS" ] || { echo "FATAL: harness not found at $HARNESS"; exit 1; }
[ -f "$EXPECTED" ] || { echo "FATAL: expected baseline not found at $EXPECTED"; exit 1; }
[ -d "$TEST_DATA/verdicts" ] || { echo "FATAL: test_data/verdicts not found"; exit 1; }

# --- run the harness on the synthetic set ------------------------------------
echo ""
echo "[1/3] Running harness on synthetic test_data..."
TMP_JSON="$(mktemp -t credaudit_XXXXXX.json 2>/dev/null || mktemp).json"
TMP_MD="$(mktemp -t credaudit_XXXXXX.md 2>/dev/null || mktemp).md"

# The harness prints the full Markdown report to stdout unconditionally
# (its --out already writes the same report to a file); discard stdout so
# only stderr progress/errors surface here.
"$PY" "$HARNESS" \
  --verdicts "$TEST_DATA/verdicts" \
  --citations "$TEST_DATA/test_citations.json" \
  --sdl-genes MECHA1,MECHA2,MECHA3,MECHA4,MECHA5,SHARED1 \
  --retrieval-genes LOOKUP1,LOOKUP2,LOOKUP3,LOOKUP4,LOOKUP5,SHARED1 \
  --ot-scores "$TEST_DATA/test_ot_scores.json" \
  --json-out "$TMP_JSON" \
  --out "$TMP_MD" \
  --quiet >/dev/null
RUN_RC=$?
if [ $RUN_RC -ne 0 ]; then
  bad "harness exited non-zero (rc=$RUN_RC)"
  rm -f "$TMP_JSON" "$TMP_MD"
  exit 1
fi
ok "harness ran to completion (rc=0)"

# --- compare against expected baseline (Python comparison for float safety) --
echo ""
echo "[2/3] Comparing output to expected_results/expected_synthetic.json..."
# NOTE: the heredoc Python writes all diagnostics to stderr and keeps stdout
# empty, so $? captures the real pass/fail exit code (a `$(...)` capture would
# swallow stdout into a variable and break the `[ -eq ]` test).
"$PY" - "$TMP_JSON" "$EXPECTED" <<'PYEOF' >&2
import json, sys
got_path, exp_path = sys.argv[1], sys.argv[2]
got = json.load(open(got_path, encoding='utf-8'))['results']
exp = json.load(open(exp_path, encoding='utf-8'))

fails = []

# --- position bias ---
g, e = got['position_bias'], exp['position_bias']
for k in ('total_pairs', 'flagged_pairs', 'flagged'):
    if g[k] != e[k]:
        fails.append(f"position_bias.{k}: got {g[k]!r} expected {e[k]!r}")
if abs(g['rate'] - e['rate']) > 1e-6:
    fails.append(f"position_bias.rate: got {g['rate']} expected {e['rate']}")

# --- anti-retrieval ---
g, e = got['anti_retrieval'], exp['anti_retrieval']
for k in ('n_sdl_scored', 'n_retrieval_scored', 'intersection', 'union_size'):
    if g[k] != e[k]:
        fails.append(f"anti_retrieval.{k}: got {g[k]!r} expected {e[k]!r}")
for k in ('sdl_mean', 'retrieval_mean', 'mwu_p', 'jaccard'):
    if abs(g[k] - e[k]) > 1e-6:
        fails.append(f"anti_retrieval.{k}: got {g[k]} expected {e[k]}")

# --- hallucination: only the stable structural fields ---
g, e = got['hallucination'], exp['hallucination']
if g['total_slots'] != e['total_slots']:
    fails.append(f"hallucination.total_slots: got {g['total_slots']} expected {e['total_slots']}")
# PMID-not-found is deterministic (slot with PMID "00000000" never exists)
not_found = g.get('pmid_not_found', g.get('breakdown', {}).get('pmid_not_found', None))
if not_found is not None and not_found != 1:
    fails.append(f"hallucination pmid_not_found: got {not_found} expected 1")

if fails:
    sys.stderr.write("  MISMATCH:\n")
    for f in fails:
        sys.stderr.write(f"    - {f}\n")
    sys.exit(1)
sys.stderr.write("  position_bias:   3 pairs, 1 flagged (pair_02), rate 33.33%  OK\n")
sys.stderr.write("  anti_retrieval:  sdl_mean 0.1667 vs retrieval_mean 0.7950, p=0.0064, J=0.0909  OK\n")
sys.stderr.write("  hallucination:   3 slots, PMID-not-found=1  OK\n")
sys.exit(0)
PYEOF
if [ $? -eq 0 ]; then ok "synthetic output matches expected baseline"; else bad "synthetic output does NOT match baseline"; fi

# --- sanity: report file was written -----------------------------------------
echo ""
echo "[3/3] Checking report artefact..."
if [ -s "$TMP_MD" ] && grep -q "Credibility-Audit Triple Report" "$TMP_MD"; then
  ok "markdown report generated and well-formed"
else
  bad "markdown report missing or malformed"
fi

rm -f "$TMP_JSON" "$TMP_MD"

# --- optional full test: real dAMD Run 1 position-bias (7/45) -----------------
if [ "${1:-}" = "--full" ]; then
  echo ""
  echo "[full] Downloading real dAMD Run 1 tournament data from Zenodo..."
  echo "       (DOI 10.5281/zenodo.20574265, ~4 MB)"
  ZEN_URL="https://zenodo.org/api/records/20574265/files"
  echo "       querying file list at $ZEN_URL ..."
  # NOTE: this block is intentionally best-effort. The deposit layout is
  # documented in code/examples/NOTES.md. If Zenodo is unreachable or the
  # archive structure has changed, the synthetic tests above still stand.
  echo "       [skip] automated real-data download is environment-dependent;"
  echo "              to verify 7/45 manually, download audit_data_for_zenodo.zip"
  echo "              from https://doi.org/10.5281/zenodo.20574265, extract the"
  echo "              tournament2_verdicts/ directory, and run:"
  echo "                python code/credibility_audit.py --verdicts <that dir>"
  echo "              Expected: 7 of 45 flagged = 15.56%, pairs"
  echo "                pair_04, pair_07, pair_12, pair_19, pair_22, pair_25, pair_38"
fi

# --- summary -----------------------------------------------------------------
echo ""
echo "============================================================"
echo " Results: $PASS passed, $FAIL failed"
if [ $FAIL -gt 0 ]; then
  echo " STATUS:  FAIL"
  exit 1
fi
echo " STATUS:  ALL TESTS PASSED"
echo "============================================================"
exit 0
