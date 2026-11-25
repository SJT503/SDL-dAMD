#!/usr/bin/env python3
"""
run_expC_v4.py -- Experiment C-v4 perturbation driver (gen-2, prereg v2 §7).

Reasoning-vs-memorisation perturbation on the F14-redrawn stimulus set
(expC_v4_pairs_120_f14.csv, n=123, pair ids V001..V123). Each pair's blinded
single-gene-disorder prompt (gen-1 verbatim structure, rebuilt from the CSV
rows) has phenotype terms deleted in information-content units:

  del_topIC           delete highest-IC terms until the cumulative removed
                      fraction of the pair's total phenotype IC reaches the
                      dose target (removes discriminative signal);
  del_lowIC_matched   delete lowest-IC terms until the SAME realised fraction
                      as del_topIC for that pair+dose (matched, removes equal
                      information, non-discriminative -- interpretability
                      control).

Doses {0, 25, 50} percent (§7.2). Dose 0 is the intact prompt; both arms use
the byte-identical intact prompt at dose 0 (call arithmetic
2 arms x 3 doses x 123 pairs x R=3 x 2 vendors = 4,428 calls, §7.3).
Deleted terms leave the "Phenotypic features" block only; inheritance and
onset lines stay verbatim; the stated count N updates to the survivors.

FROZEN IC MACHINERY (reproduced exactly from power_family6.py lines 59-90):
document frequency over the 4,958-pair candidate pool, IC(t) = -log2(df_t/N),
df_t = number of pool pairs whose hpo_terms set contains t, N = pool row
count, unseen terms take maxIC = -log2(1/N). The realised doses are asserted
against the frozen power table each invocation: the del_topIC arm's median
realised fraction must be 0.276 (dose 25) and 0.520 (dose 50) within 0.01;
a violation is a build failure and blocks all model calls.

DETERMINISM: deletion order breaks IC ties by ascending term id, so every
(pair, arm, dose) prompt is byte-identical across reruns and machines;
surviving terms keep their CSV column order.

CALL LAYER: gen2_call.call (glm-5.3 / deepseek-v4-pro; §1.3 frozen constants;
max_tokens = 1024 for C gene lists). GEN2_MOCK=1 runs fully offline with
canned text. Result rows are appended to runs/expC_v4/results.jsonl only for
transport-completed calls (ok=true): a refusal or unparseable answer is model
behaviour and IS recorded (predictions=[], parse_tier set); a transport
failure stays in gen2_call's calls_log.jsonl and is retried by the next
invocation (no row, no double count).

RESUME: a job is skipped iff its call_id is done-and-ok in gen2_call's log
AND a row for it already exists. Mock and live results never mix: a live run
re-executes anything whose last recorded call was mock; a mock run never
re-executes a completed live call. Execution order is the seeded interleaving
shuffle (PERM_SEED = 20260101, §10.1) over the canonical job list for the
requested vendor, so no condition ever runs as a contiguous block.

The 30-pair held-out reserve is not used, not read, and not referenced by any
code path in this driver.

Usage:
  python run_expC_v4.py --selftest                        # offline unit checks
  python run_expC_v4.py --build-only --vendor glm         # prompts + frozen check
  GEN2_MOCK=1 python run_expC_v4.py --vendor glm --limit 2   # offline end-to-end
  python run_expC_v4.py --vendor glm --limit 3            # smoke (18 calls)
  python run_expC_v4.py --vendor glm                      # full (2,214 calls)
  python run_expC_v4.py --vendor glm --chunk 200          # resumable batches
"""

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time
from collections import Counter

import pandas as pd

import gen2_call

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
RUN_DIR = os.path.join(HERE, "runs", "expC_v4")
# Mock runs write results into the isolated mock root so they can never
# pollute the live results file (post-incident hardening 2026-09-05).
RESULTS_PATH = os.path.join(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_mock")
    if os.environ.get("GEN2_MOCK") else RUN_DIR, "results.jsonl")
AUDIT_PATH = os.path.join(RUN_DIR, "prompt_audit.json")
MANIFEST_PATH = os.path.join(RUN_DIR, "manifest.json")
HPO_CACHE_PATH = os.path.join(DATA_DIR, "hpo_labels_cache.json")
IC_CACHE_PATH = os.path.join(DATA_DIR, "expC_ic_pool_cache.json")

MAIN_CSV = (r"D:/Papers/Robin_Nature_2026/BiB_work_2026-09-02/"
            r"GEN2_prereg/expC_v4_pairs_120_f14.csv")
POOL_CSV = (r"D:/Papers/Robin_Nature_2026/BiB_work_2026-09-02/"
            r"REDO_REVIEW_PACK_2026-09-02/expC_candidate_pool.csv")
OBO_GZ = (r"D:/Papers/Robin_Nature_2026/HANDOFF_2026-09-02/"
          r"HANDOFF_2026-09-02/04_prereg_B_C/source_snapshots/hp.obo.gz")

# §9.2 frozen constants.
PERM_SEED = 20260101
DOSES = (0, 25, 50)
ARMS = ("del_topIC", "del_lowIC_matched")
REPS = 3
MAX_TOKENS = 32768  # D2-006 (16384 still truncated worst-case recall)
CALL_SLEEP_S = 0.3                   # politeness pacing; not pre-registered

# §7.3 frozen power-table targets for the del_topIC arm's realised medians.
FROZEN_MEDIAN_25 = 0.276
FROZEN_MEDIAN_50 = 0.520
FROZEN_MEDIAN_TOL = 0.01

# Gen-1 verbatim fixed paragraphs (structure frozen; content rebuilt from CSV).
INTRO_SENTENCE = ("A single-gene disorder is described below only by its "
                  "clinical and laboratory features. The disease name, any "
                  "eponym, any OMIM or MONDO identifier, the causal gene and "
                  "all of its aliases have been removed.")
CLOSER_SENTENCE = ("Name the ten human genes most likely to harbour the "
                   "causal variant, ranked from most to least likely. Output "
                   "only a numbered list of HGNC gene symbols, one per line, "
                   "with no explanation.")
# Canonical scaffold hashed into the manifest so any template drift is
# detectable against a frozen sha256.
TEMPLATE_SHA_INPUT = (INTRO_SENTENCE + "\n\n<<Inheritance / Age of onset "
                     "lines>>\n\nPhenotypic features (Human Phenotype "
                     "Ontology terms, <<N>>):\n<<  - label lines>>\n\n" +
                     CLOSER_SENTENCE)
PROMPT_TEMPLATE_SHA256 = hashlib.sha256(
    TEMPLATE_SHA_INPUT.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------- helpers ----
def wjson(path, obj):
    """Atomic JSON dump (tmp file + os.replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hp_ids(value):
    """Pipe-separated cell -> list of HP: ids (frozen `terms()` filter)."""
    if value is None or pd.isna(value):
        return []
    return [t for t in str(value).split("|") if t.startswith("HP:")]


def alias_list(value):
    if value is None or pd.isna(value):
        return []
    return [a.strip() for a in str(value).split("|") if a.strip()]


# ----------------------------------------------------------- HPO labels ------
def load_hpo_labels():
    """id -> preferred name from the frozen hp.obo.gz snapshot.

    Cached to data/hpo_labels_cache.json on first run; rebuilt automatically
    if the snapshot's sha256 changes. Unknown ids keep the raw HP: id as the
    label at call sites (rule: never drop a term for lack of a label)."""
    src_sha = sha256_file(OBO_GZ)
    if os.path.exists(HPO_CACHE_PATH):
        try:
            cache = json.load(open(HPO_CACHE_PATH, encoding="utf-8"))
            if cache.get("source_sha256") == src_sha:
                return cache["names"]
        except Exception:                                            # noqa: BLE001
            pass
    names, version = {}, None
    in_term, cur = False, None
    with gzip.open(OBO_GZ, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "[Term]":
                in_term, cur = True, None
            elif line.startswith("["):
                in_term = False
            elif in_term:
                if line.startswith("id: HP:"):
                    cur = line[4:].strip()
                elif line.startswith("name: ") and cur:
                    names[cur] = line[6:].strip()
            elif line.startswith("data-version: "):
                version = line[len("data-version: "):].strip()
    wjson(HPO_CACHE_PATH, {"source": OBO_GZ, "source_sha256": src_sha,
                           "data_version": version, "n_names": len(names),
                           "names": names})
    print("hpo labels: parsed %d names (%s) -> %s"
          % (len(names), version, HPO_CACHE_PATH))
    return names


# ------------------------------------------------------------- frozen IC -----
class FrozenIC:
    """Document-frequency IC over the candidate pool.

    Formula frozen in power_family6.py (lines 59-90):
      df_t  = number of pool pairs whose hpo_terms SET contains t
      IC(t) = -log2(df_t / N),  N = pool row count
      maxIC = -log2(1 / N)  (substituted for terms never seen in the pool)
    """

    def __init__(self, df_counts, n_pool):
        self.n = n_pool
        self.ic = {t: -math.log2(v / n_pool) for t, v in df_counts.items()}
        self.max_ic = -math.log2(1 / n_pool)

    def of(self, term):
        return self.ic.get(term, self.max_ic)

    def dose_at(self, term_list, x_percent):
        """Realised removed fraction under the frozen accumulation loop:
        delete by descending IC until the cumulative removed fraction reaches
        x_percent. Verbatim from power_family6.py `dose_at`."""
        ics = sorted((self.of(t) for t in term_list), reverse=True)
        tot = sum(ics) or 1e-9
        acc = 0.0
        for v in ics:
            if acc / tot >= x_percent / 100:
                break
            acc += v
        return acc / tot

    def select_deleted(self, term_list, arm, target_fraction):
        """Deterministic deletion plan for one (pair, arm, target).

        Deletes one occurrence at a time in IC order -- descending for
        del_topIC, ascending for del_lowIC_matched -- until the cumulative
        removed IC fraction reaches target_fraction. IC ties are broken by
        ascending term id, so the plan is identical across reruns. Returns
        (deleted occurrences in deletion order, realised fraction)."""
        key = (lambda t: (-self.of(t), t)) if arm == "del_topIC" \
            else (lambda t: (self.of(t), t))
        order = sorted(term_list, key=key)
        tot = sum(self.of(t) for t in term_list) or 1e-9
        acc, deleted = 0.0, []
        for t in order:
            if acc / tot >= target_fraction:
                break
            acc += self.of(t)
            deleted.append(t)
        return deleted, acc / tot


def load_frozen_ic():
    """Pool df counts -> FrozenIC, cached to data/expC_ic_pool_cache.json
    (rebuilt automatically when the pool CSV's sha256 changes)."""
    pool_sha = sha256_file(POOL_CSV)
    if os.path.exists(IC_CACHE_PATH):
        try:
            cache = json.load(open(IC_CACHE_PATH, encoding="utf-8"))
            if cache.get("pool_sha256") == pool_sha:
                return FrozenIC(cache["df_counts"], cache["n_pool"])
        except Exception:                                            # noqa: BLE001
            pass
    pool = pd.read_csv(POOL_CSV, low_memory=False)
    n_pool = len(pool)
    df_counts = Counter()
    for cell in pool["hpo_terms"]:
        for t in set(hp_ids(cell)):
            df_counts[t] += 1
    df_counts = dict(df_counts)
    wjson(IC_CACHE_PATH, {"pool": POOL_CSV, "pool_sha256": pool_sha,
                          "n_pool": n_pool, "df_counts": df_counts})
    print("ic cache: %d pool pairs, %d distinct terms -> %s"
          % (n_pool, len(df_counts), IC_CACHE_PATH))
    return FrozenIC(df_counts, n_pool)


# ------------------------------------------------------------- stimulus ------
def load_pairs():
    """Main stimulus set -> list of row dicts sorted by pair_id."""
    df = pd.read_csv(MAIN_CSV)
    rows = [{"pair_id": str(r["pair_id"]).strip(),
             "gene_symbol": str(r["gene_symbol"]).strip(),
             "aliases": alias_list(r["aliases"]),
             "terms": hp_ids(r["hpo_terms"]),
             "inheritance": hp_ids(r["inheritance"]),
             "onset": hp_ids(r["onset_terms"])}
            for _, r in df.iterrows()]
    rows.sort(key=lambda r: r["pair_id"])
    if len(rows) != 123 or len({r["pair_id"] for r in rows}) != len(rows):
        sys.exit("stimulus integrity fail: %d rows / duplicate pair_id in %s"
                 % (len(rows), MAIN_CSV))
    if any(not r["terms"] for r in rows):
        sys.exit("stimulus integrity fail: pair with zero phenotype terms")
    return rows


def build_prompt(inh_labels, onset_labels, kept_labels):
    """Gen-1 verbatim prompt scaffold. Header lines with no terms are
    omitted (nothing may be fabricated); feature labels fall back to the
    raw HP: id when the snapshot has no name."""
    lines = [INTRO_SENTENCE, ""]
    if inh_labels:
        lines.append("Inheritance: " + "; ".join(inh_labels))
    if onset_labels:
        lines.append("Age of onset: " + "; ".join(onset_labels))
    lines.append("")
    lines.append("Phenotypic features (Human Phenotype Ontology terms, %d):"
                 % len(kept_labels))
    lines.extend("  - " + lab for lab in kept_labels)
    lines.append("")
    lines.append(CLOSER_SENTENCE)
    return "\n".join(lines)


def build_variants(rows, names, fic):
    """Every (pair, arm, dose) prompt variant. One pass, fully deterministic.

    del_topIC plans against the dose target; del_lowIC_matched plans against
    del_topIC's realised fraction for the same pair+dose (matched control).
    Deleted occurrences are removed from the features block only; survivors
    keep their CSV order."""
    variants = {}
    for row in rows:
        inh = [names.get(t, t) for t in row["inheritance"]]
        onset = [names.get(t, t) for t in row["onset"]]
        terms = row["terms"]
        for dose in DOSES:
            top_del, top_real = fic.select_deleted(terms, "del_topIC",
                                                   dose / 100.0)
            low_del, low_real = fic.select_deleted(terms, "del_lowIC_matched",
                                                   top_real)
            for arm in ARMS:
                deleted, realized = ((top_del, top_real) if arm == "del_topIC"
                                     else (low_del, low_real))
                remaining = Counter(deleted)
                kept = []
                for t in terms:
                    if remaining.get(t, 0) > 0:
                        remaining[t] -= 1
                    else:
                        kept.append(t)
                prompt = build_prompt(inh, onset,
                                      [names.get(t, t) for t in kept])
                variants[(row["pair_id"], arm, dose)] = {
                    "prompt": prompt,
                    "prompt_sha256": hashlib.sha256(
                        prompt.encode("utf-8")).hexdigest(),
                    "gene_symbol": row["gene_symbol"],
                    "aliases": row["aliases"],
                    "n_intact": len(terms),
                    "n_kept": len(kept),
                    "n_deleted": len(deleted),
                    "deleted_terms": sorted(deleted),
                    "dose_target": dose,
                    "dose_realized": realized,
                }
    return variants


def frozen_crosscheck(variants):
    """§7 frozen-value check: the del_topIC arm's median realised fraction
    must reproduce the frozen power-table values (0.276 at dose 25, 0.520 at
    dose 50) within 0.01. Returns (passed, {arm_dose: median})."""
    medians = {}
    for arm in ARMS:
        for dose in DOSES:
            fr = [v["dose_realized"] for (pid, a, d), v in variants.items()
                  if a == arm and d == dose]
            medians["%s_d%d" % (arm, dose)] = round(statistics.median(fr), 4)
    ok = (abs(medians["del_topIC_d25"] - FROZEN_MEDIAN_25) < FROZEN_MEDIAN_TOL
          and abs(medians["del_topIC_d50"] - FROZEN_MEDIAN_50)
          < FROZEN_MEDIAN_TOL)
    return ok, medians


# ---------------------------------------------------------- gene parsing -----
# Gen-1 elicit_exp_c.py parsing, retained: JSON array of strings preferred,
# then numbered-list line parsing with the GENE_OK symbol filter.
FENCE = re.compile(r"^\s*```(?:json|JSON|text)?\s*(.*?)\s*```\s*$", re.S)
NUMBERING = re.compile(r"^\s*(?:\(?\d{1,3}[\.\)\:]|[-*\u2022\u2013])\s*")
GENE_OK = re.compile(r"^[A-Za-z][A-Za-z0-9\-@_.]{0,19}$")
SPLIT_TAIL = re.compile(r"\s+[-\u2013\u2014(:,]|\t")


def parse_genes(text):
    """Ordered gene symbols from a model answer. (genes, tier, notes)."""
    t = (text or "").strip()
    if not t:
        return [], "empty_response", ["empty"]
    m = FENCE.match(t)
    if m:
        t = m.group(1).strip()

    # A JSON array of strings is unambiguous; take it as given.
    try:
        o = json.loads(t)
        if isinstance(o, list) and all(isinstance(x, str) for x in o):
            g = [x.strip() for x in o if x.strip()]
            return g, "json_list", []
    except Exception:                                                # noqa: BLE001
        pass

    genes, notes, numbered = [], [], 0
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        stripped = NUMBERING.sub("", s)
        if stripped != s:
            numbered += 1
        head = SPLIT_TAIL.split(stripped, 1)[0].strip().strip('"\'`.,;')
        if not head:
            continue
        if GENE_OK.match(head):
            genes.append(head)
        else:
            notes.append("unparsed_line:" + s[:60])
    tier = "numbered_list" if numbered >= max(1, len(genes) // 2) \
        else "bare_lines"
    return genes, tier, notes


# ---------------------------------------------------------------- hit10 ------
def hit10(predictions, gene_symbol, aliases):
    """True iff the causal symbol or any alias appears in the prediction list
    as a case-insensitive WHOLE WORD (so alias MER does not match MERTK;
    word characters are [A-Za-z0-9], so MER does not match MER2 either)."""
    targets = [t for t in [gene_symbol] + list(aliases) if t]
    patterns = [(t, re.compile(r"(?<![A-Za-z0-9])" + re.escape(t)
                               + r"(?![A-Za-z0-9])", re.IGNORECASE))
                for t in targets]
    for pred in predictions:
        for _, pat in patterns:
            if pat.search(pred):
                return True
    return False


# -------------------------------------------------------------- selftest -----
def run_selftest():
    """Offline unit sanity: hit10 word semantics, parse tiers, determinism,
    and machinery equivalence with the frozen power script."""
    checks = []

    def check(name, cond):
        checks.append(cond)
        print("%-4s %s" % ("PASS" if cond else "FAIL", name))

    # --- hit10: whole-word, case-insensitive, symbol-or-alias ---
    check("hit10: symbol exact match",
          hit10(["ABCA4", "CFH"], "CFH", []) is True)
    check("hit10: alias MER must NOT match prediction MERTK",
          hit10(["MERTK"], "SOMEOTHERGENE", ["MER"]) is False)
    check("hit10: alias MER must NOT match embedded AMER2/CD3MER/MER2",
          hit10(["AMER2", "CD3MER", "MER2"], "SOMEOTHERGENE", ["MER"]) is False)
    check("hit10: alias MER matches bare prediction MER",
          hit10(["XYZ", "MER"], "SOMEOTHERGENE", ["MER"]) is True)
    check("hit10: case-insensitive (tardbp ~ TARDBP)",
          hit10(["tardbp"], "TARDBP", []) is True)
    check("hit10: TARDBP matches via TDP-43-style alias",
          hit10(["TDP-43"], "TARDBP", ["TDP-43"]) is True)
    check("hit10: hyphenated alias is word-bounded (TDP-43 != TDP43)",
          hit10(["TDP43"], "TARDBP", ["TDP-43"]) is False)
    check("hit10: empty predictions -> False",
          hit10([], "TARDBP", ["TDP-43"]) is False)
    check("hit10: extra context around symbol does not block match",
          hit10(["1. MERTK"], "MERTK", []) is True)

    # --- parse_genes tiers ---
    numbered = "\n".join("%d. GENE%d" % (i, i) for i in range(1, 11))
    genes, tier, _ = parse_genes(numbered)
    check("parse: numbered list of 10 -> tier numbered_list, 10 genes",
          tier == "numbered_list" and len(genes) == 10)
    genes, tier, _ = parse_genes('["CFH", "ARMS2", "C2"]')
    check("parse: JSON string array -> tier json_list",
          tier == "json_list" and genes == ["CFH", "ARMS2", "C2"])
    genes, tier, notes = parse_genes("1. TARDBP (TDP-43)\n2. FUS\njunk line !!")
    check("parse: head-split keeps symbol, flags junk",
          genes == ["TARDBP", "FUS"] and len(notes) == 1)
    genes, tier, _ = parse_genes("")
    check("parse: empty response tier",
          tier == "empty_response" and genes == [])

    # --- frozen machinery + full build ---
    names = load_hpo_labels()
    fic = load_frozen_ic()
    rows = load_pairs()

    equiv = True
    for row in rows:
        for dose in (25, 50):
            _, real = fic.select_deleted(row["terms"], "del_topIC", dose / 100)
            if abs(real - fic.dose_at(row["terms"], dose)) > 1e-12:
                equiv = False
    check("machinery: select_deleted(del_topIC) == frozen dose_at "
          "(all 123 pairs x doses 25/50)", equiv)

    v1 = build_variants(rows, names, fic)
    v2 = build_variants(rows, names, fic)
    check("determinism: rebuilding all 738 prompts reproduces every sha256",
          all(v1[k]["prompt_sha256"] == v2[k]["prompt_sha256"]
              for k in v1) and len(v1) == 738)

    check("dose 0: both arms share the byte-identical intact prompt",
          all(v1[(pid, "del_topIC", 0)]["prompt"]
              == v1[(pid, "del_lowIC_matched", 0)]["prompt"]
              for pid in {pid for pid, _, _ in v1}))
    check("deletion accounting: n_kept + n_deleted == n_intact everywhere",
          all(v["n_kept"] + v["n_deleted"] == v["n_intact"]
              for v in v1.values()))
    ok_lines = True
    for pid in {pid for pid, _, _ in v1}:
        head0 = v1[(pid, "del_topIC", 0)]["prompt"].split("\n\n")[1]
        head25 = v1[(pid, "del_topIC", 25)]["prompt"].split("\n\n")[1]
        if head0 != head25:
            ok_lines = False
    check("scope: inheritance/onset header untouched by deletion (all pairs)",
          ok_lines)

    ok, medians = frozen_crosscheck(v1)
    check("frozen cross-check: del_topIC medians 25%%->%.3f 50%%->%.3f "
          "(targets 0.276/0.520, tol 0.01)"
          % (medians["del_topIC_d25"], medians["del_topIC_d50"]), ok)

    n_pass = sum(checks)
    print("\nselftest: %d/%d passed" % (n_pass, len(checks)))
    return 0 if n_pass == len(checks) else 1


# ------------------------------------------------------------------ main -----
def ensure_key(vendor):
    """Clear, early failure when the vendor key file is absent (live runs)."""
    env = os.environ.get("GEN2_GLM_KEY_FILE" if vendor == "glm"
                         else "GEN2_DS_KEY_FILE")
    path = env or gen2_call.VENDORS[vendor]["key_file"]
    if not os.path.exists(path):
        sys.exit("ERROR: %s key file not found: %s\n"
                 "  Create that file containing only the API key, or point "
                 "%s at it.\n  No calls were made."
                 % (vendor, path,
                    "GEN2_GLM_KEY_FILE" if vendor == "glm"
                    else "GEN2_DS_KEY_FILE"))
    with open(path, encoding="utf-8") as fh:
        if not fh.read().strip():
            sys.exit("ERROR: %s key file is empty: %s -- no calls were made."
                     % (vendor, path))


def existing_row_call_ids(path):
    """call_ids already present in results.jsonl (resume checkpoint)."""
    out = set()
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.add(json.loads(line)["call_id"])
            except Exception:                                        # noqa: BLE001
                continue
    return out


def call_states():
    """call_id -> (ok, mock) from the LAST record per id in gen2_call's log.
    Used so mock and live results never mix: a live run re-executes anything
    whose last recorded call was mock; a mock run never re-executes a
    completed live call."""
    states = {}
    if not os.path.exists(gen2_call.LOG_PATH):
        return states
    with open(gen2_call.LOG_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:                                        # noqa: BLE001
                continue
            if "call_id" in rec:
                states[rec["call_id"]] = (bool(rec.get("ok")),
                                          bool(rec.get("mock")))
    return states


def call_id_of(vendor, job):
    """Deterministic call id: expC_v4/<vendor>/<arm>/d<dose>/<pair>/r<rep>.

    Reconstructed 2026-09-05 after an editing accident removed the original
    one-line definition; format matches every call_id already recorded in
    data/calls_log.jsonl and runs/expC_v4/results.jsonl byte-for-byte
    (verified against expC_v4/glm/del_topIC/d25/V001/r1 &c.), so resume
    indices are unaffected.
    """
    arm, dose, pid, rep = job
    return "expC_v4/%s/%s/d%d/%s/r%d" % (vendor, arm, dose, pid, rep)


def write_manifest(args, *, variants, medians, crosscheck_ok, mock,
                   n_calls_new, n_failures, n_jobs, n_skipped):
    """runs/expC_v4/manifest.json, rewritten at the end of every invocation."""
    counts = {}
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:                                    # noqa: BLE001
                    continue
                c = counts.setdefault(r["vendor"], {}).setdefault(
                    r["arm"], {})
                c[str(r["dose_target"])] = c.get(str(r["dose_target"]), 0) + 1
    n_rows = sum(sum(d.values()) for a in counts.values()
                 for d in a.values())
    manifest = {
        "experiment": "C-v4",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prereg": "PREREG_v2_FROZEN_v1.1 §7 (§1.3, §7.2, §7.3, §9.2, §10.1)",
        "vendor": args.vendor,
        "build_only": bool(args.build_only),
        "mock": mock,
        "limit": args.limit,
        "chunk": args.chunk,
        "frozen_constants": {
            "perm_seed": PERM_SEED, "doses_percent": list(DOSES),
            "arms": list(ARMS), "reps": REPS, "max_tokens": MAX_TOKENS,
            "temperature": 1.0, "top_p": 0.95, "thinking_effort": "high",
        },
        "stimulus_csv": MAIN_CSV,
        "stimulus_sha256": sha256_file(MAIN_CSV),
        "n_pairs": len(variants) // (len(ARMS) * len(DOSES)),
        "pool_csv": POOL_CSV,
        "pool_sha256": sha256_file(POOL_CSV),
        "prompt_template_sha256": PROMPT_TEMPLATE_SHA256,
        "hpo_labels_cache": {"path": HPO_CACHE_PATH,
                             "sha256": sha256_file(HPO_CACHE_PATH)},
        "ic_cache": {"path": IC_CACHE_PATH,
                     "sha256": sha256_file(IC_CACHE_PATH)},
        "n_calls_new": n_calls_new,
        "n_call_failures": n_failures,
        "n_jobs_this_scope": n_jobs,
        "n_jobs_skipped_resumed": n_skipped,
        "n_rows_results": n_rows,
        "counts_by_vendor_arm_dose": counts,
        "dose_realization_median": medians,
        "frozen_crosscheck": {
            "targets": {"del_topIC_d25": FROZEN_MEDIAN_25,
                        "del_topIC_d50": FROZEN_MEDIAN_50},
            "tolerance": FROZEN_MEDIAN_TOL,
            "passed": crosscheck_ok,
        },
        "expected_calls": {"per_vendor": len(ARMS) * len(DOSES) * 123 * REPS,
                           "both_vendors": len(ARMS) * len(DOSES) * 123 * REPS
                           * 2},
    }
    wjson(MANIFEST_PATH, manifest)
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Experiment C-v4 perturbation driver (prereg v2 §7)")
    ap.add_argument("--vendor", default="glm", choices=sorted(gen2_call.VENDORS),
                    help="vendor to run (one per invocation)")
    ap.add_argument("--limit", type=int, default=None, metavar="N",
                    help="smoke mode: first N pairs by pair_id, rep 1 only")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent dispatch workers (calls are stateless; ledger/log appends are locked)")
    ap.add_argument("--chunk", type=int, default=None, metavar="N",
                    help="cap on NEW calls this invocation (resume with more)")
    ap.add_argument("--build-only", action="store_true",
                    help="build all prompts + frozen cross-check; no calls")
    ap.add_argument("--selftest", action="store_true",
                    help="offline unit sanity checks; no calls")
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()

    # ---------------- data, caches, deterministic prompt build ----------------
    names = load_hpo_labels()
    fic = load_frozen_ic()
    rows = load_pairs()
    variants = build_variants(rows, names, fic)

    audit = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "n_pairs": len(rows), "arms": list(ARMS),
             "doses_percent": list(DOSES),
             "prompt_template_sha256": PROMPT_TEMPLATE_SHA256,
             "stimulus_sha256": sha256_file(MAIN_CSV),
             "variants": {pid: {arm: {str(dose):
                                      {"prompt_sha256":
                                       variants[(pid, arm, dose)]["prompt_sha256"],
                                       "n_kept":
                                       variants[(pid, arm, dose)]["n_kept"],
                                       "n_deleted":
                                       variants[(pid, arm, dose)]["n_deleted"],
                                       "dose_target": dose,
                                       "dose_realized": round(
                                           variants[(pid, arm, dose)]
                                           ["dose_realized"], 6)}
                                      for dose in DOSES}
                               for arm in ARMS}
                          for pid in (r["pair_id"] for r in rows)}}
    wjson(AUDIT_PATH, audit)

    crosscheck_ok, medians = frozen_crosscheck(variants)
    print("\nfrozen-value cross-check (del_topIC realised medians, n=123):")
    print("  dose 25: median=%.4f  |x-%.3f|=%.4f  -> %s"
          % (medians["del_topIC_d25"], FROZEN_MEDIAN_25,
             abs(medians["del_topIC_d25"] - FROZEN_MEDIAN_25),
             "PASS" if abs(medians["del_topIC_d25"] - FROZEN_MEDIAN_25)
             < FROZEN_MEDIAN_TOL else "FAIL"))
    print("  dose 50: median=%.4f  |x-%.3f|=%.4f  -> %s"
          % (medians["del_topIC_d50"], FROZEN_MEDIAN_50,
             abs(medians["del_topIC_d50"] - FROZEN_MEDIAN_50),
             "PASS" if abs(medians["del_topIC_d50"] - FROZEN_MEDIAN_50)
             < FROZEN_MEDIAN_TOL else "FAIL"))
    print("  all arm x dose medians: %s" % json.dumps(medians, sort_keys=True))

    mock = bool(os.environ.get("GEN2_MOCK"))

    if args.build_only:
        man = write_manifest(args, variants=variants, medians=medians,
                             crosscheck_ok=crosscheck_ok, mock=mock,
                             n_calls_new=0, n_failures=0, n_jobs=0, n_skipped=0)
        print("\nbuild-only complete: %d prompt variants, 0 calls" % len(variants))
        print("audit    : %s" % AUDIT_PATH)
        print("manifest : %s" % MANIFEST_PATH)
        print("CROSS-CHECK %s" % ("PASS" if crosscheck_ok else "FAIL"))
        return 0 if crosscheck_ok else 2

    if not crosscheck_ok:
        write_manifest(args, variants=variants, medians=medians,
                       crosscheck_ok=False, mock=mock, n_calls_new=0,
                       n_failures=0, n_jobs=0, n_skipped=0)
        sys.exit("\nFROZEN-VALUE CROSS-CHECK FAILED -- refusing to dispatch "
                 "any model call. Inspect %s and the IC cache before "
                 "re-running." % AUDIT_PATH)

    if not mock:
        ensure_key(args.vendor)

    # ---------------- interleaved job list (§10.1) ----------------
    pairs = rows if args.limit is None else rows[:max(0, args.limit)]
    reps = range(1, REPS + 1) if args.limit is None else [1]
    jobs = [(arm, dose, r["pair_id"], rep)
            for arm in ARMS
            for dose in DOSES
            for r in pairs
            for rep in reps]
    random.Random(PERM_SEED).shuffle(jobs)

    states = call_states()
    have_rows = existing_row_call_ids(RESULTS_PATH)
    # Resume rule: skip iff the last recorded call for that id is done-and-ok
    # AND a result row already exists -- with mock/live isolation: a live run
    # additionally requires the last call to be non-mock (anything last called
    # in mock is re-executed live); a mock run skips any completed call
    # (never supplementing real results with mock output).
    completed = {cid for cid in have_rows
                 if states.get(cid, (False, False))[0]
                 and (not states.get(cid, (False, False))[1] or mock)}
    todo = [j for j in jobs if call_id_of(args.vendor, j) not in completed]
    print("\nexecution: vendor=%s mock=%s jobs=%d skipped(resumed)=%d "
          "todo=%d%s" % (args.vendor, mock, len(jobs), len(jobs) - len(todo),
                         len(todo),
                         "" if args.chunk is None
                         else " chunk-cap=%d" % args.chunk))

    os.makedirs(RUN_DIR, exist_ok=True)
    n_new, n_fail = 0, 0
    t0 = time.time()
    # chunk cap bounds how many NEW dispatches this invocation makes; in
    # concurrent mode it bounds the submitted batch
    batch = todo if args.chunk is None else todo[:args.chunk]
    if args.chunk is not None and len(batch) < len(todo):
        print("chunk cap %d reached -- submitting %d (re-run to resume)"
              % (args.chunk, len(batch)))

    import threading as _th
    _rlock = _th.Lock()

    def process(job):
        """One independent dispatch -> row appended under lock. Calls are
        stateless (per-call session ids), so any execution order -- including
        concurrent -- satisfies the §10.1 interleaved-order requirement (the
        order itself was seeded by the shuffle above)."""
        nonlocal n_new, n_fail
        arm, dose, pid, rep = job
        v = variants[(pid, arm, dose)]
        call_id = call_id_of(args.vendor, job)
        rec = gen2_call.call(args.vendor, v["prompt"], MAX_TOKENS,
                             call_id=call_id,
                             about={"task_class": "gene_list",
                                    "experiment": "C-v4", "arm": arm,
                                    "dose_target": dose, "pair_id": pid,
                                    "rep": rep})
        if not rec.get("ok"):
            with _rlock:
                n_fail += 1
                print("FAIL  %s  status=%s attempts=%s (recorded in "
                      "calls_log; next invocation retries)"
                      % (call_id, rec.get("status"), rec.get("attempts")))
            return "fail", call_id
        genes, tier, notes = parse_genes(rec.get("text"))
        row = {
            "call_id": call_id,
            "vendor": args.vendor,
            "arm": arm,
            "dose_target": dose,
            "dose_realized": round(v["dose_realized"], 6),
            "pair_id": pid,
            "gene_symbol": v["gene_symbol"],
            "aliases": v["aliases"],
            "rep": rep,
            "predictions": genes[:10],
            "n_pheno_terms_intact": v["n_intact"],
            "n_pheno_terms_kept": v["n_kept"],
            "deleted_terms": v["deleted_terms"],
            "parse_tier": tier,
            "ok": True,
            "hit10": hit10(genes[:10], v["gene_symbol"], v["aliases"]),
            "utc": rec.get("utc"),
        }
        with _rlock:
            with open(RESULTS_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_new += 1
            print("ok    %-38s n=%-3d tier=%-13s hit10=%-5s%s"
                  % (call_id.split("/", 1)[1], len(genes), tier, row["hit10"],
                     "  notes=%d" % len(notes) if notes else ""))
        return "ok", call_id

    if args.workers <= 1:
        for job in batch:
            process(job)
            if not mock:
                time.sleep(CALL_SLEEP_S)
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(process, j) for j in batch]
            for _f in as_completed(futs):
                _f.result()   # propagate unexpected worker errors loudly

    man = write_manifest(args, variants=variants, medians=medians,
                         crosscheck_ok=crosscheck_ok, mock=mock,
                         n_calls_new=n_new, n_failures=n_fail,
                         n_jobs=len(jobs), n_skipped=len(jobs) - len(todo))
    print("\ndone in %.1fs: new=%d failures=%d rows=%d/%d (per-vendor)"
          % (time.time() - t0, n_new, n_fail,
             n_new + (len(jobs) - len(todo)), len(jobs)))
    print("results  : %s" % RESULTS_PATH)
    print("manifest : %s" % MANIFEST_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())

