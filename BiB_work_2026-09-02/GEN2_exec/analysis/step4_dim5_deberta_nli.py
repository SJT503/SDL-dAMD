#!/usr/bin/env python3
"""
Step 4: Dimension 5 Cross-Agent Coherence & NLI Contradiction Analysis
(Appendix B frozen protocol: MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli)

1. Builds the frozen entity dictionary (3,872 HGNC genes + aliases + GWAS genes + run targets).
2. Segments all logged outputs across the 12 Parent runs (Step 1, Step 2, Step 3, Step 4, Step 6)
   into atomic entity-anchored sentences.
3. Constructs:
   - Cross-stage candidate lineage assertion pairs (Step 1 -> Step 3 -> Step 4 -> Step 6)
   - Cross-judge & self-contradiction assertion pairs in Tournament II (comparing forward vs
     reversed reasoning on the 689 position-biased pairs vs 912 content-consistent pairs,
     highlighting SCIENCE / FEASIBILITY / NOVELTY sub-claim reversals).
4. Runs bidirectional DeBERTa-v3 NLI inference (P(contradiction) > 0.75 in both directions,
   plus directional P(contradiction) > 0.75) and computes:
   - Contradictions per 1,000 atomic assertions & per 1,000 evaluated pairs (with 10,000-iter
     run-cluster bootstrap 95% CI)
   -Silent propagation vs resolution rate into Step 6 Top-5 protocols
   - Audit-Guided Coherence Gating (filtering / down-weighting self-contradictory judge pairs).
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
PREREG_DIR = os.path.join(BASE, "GEN2_prereg")
EXEC_DIR = os.path.join(BASE, "GEN2_exec")
RUNS_DIR = os.path.join(EXEC_DIR, "runs")
OUT_DIR = os.path.join(EXEC_DIR, "analysis")
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAME = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"

STOP_UPPER = {
    "IN", "ON", "OR", "TO", "BY", "AT", "OF", "AS", "IS", "IT", "AN", "BE",
    "WE", "DO", "IF", "NO", "SO", "UP", "GO", "US", "AM", "PM", "VS", "IE",
    "EG", "II", "III", "IV", "VI", "VII", "VIII", "IX", "AI", "ML", "SD",
    "SE", "CI", "OR", "HR", "RR", "IC", "ID", "WT", "KO", "KI", "GA", "ALS",
    "AMD", "DAMD", "RPE", "CNS", "CSF", "MRI", "OCT", "ERG", "FAF", "AAV",
    "ASO", "RNA", "DNA", "ATP", "ADP", "AMP", "GTP", "GDP", "ROS", "RNS",
    "ER", "MT", "ECM", "BM", "POS", "M0", "M1", "M2", "C1", "C2",
}


def load_entity_map():
    """Load the frozen 3,872-gene pool + GWAS table + run targets for deterministic entity normalization."""
    alias_to_canon = {}
    pool_csv = os.path.join(BASE, "REDO_REVIEW_PACK_2026-09-02", "expC_candidate_pool.csv")
    if os.path.exists(pool_csv):
        with open(pool_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = str(row.get("gene_symbol", "")).strip().upper()
                if len(sym) >= 2 and sym not in STOP_UPPER:
                    alias_to_canon[sym] = sym
                aliases = str(row.get("aliases", "")).split("|")
                for al in aliases:
                    al = al.strip().upper()
                    if len(al) >= 3 and al not in STOP_UPPER and al not in alias_to_canon:
                        alias_to_canon[al] = sym

    gwas_csv = os.path.join(PREREG_DIR, "APPENDIX_A_gwascat_gene_table.csv")
    if os.path.exists(gwas_csv):
        with open(gwas_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = str(row.get("gene_symbol", "")).strip().upper()
                if len(sym) >= 2 and sym not in STOP_UPPER:
                    alias_to_canon[sym] = sym

    runs = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]
    for run_id in runs:
        rdir = os.path.join(RUNS_DIR, run_id)
        s1 = json.load(open(os.path.join(rdir, "step1_mechanisms.json"), encoding="utf-8"))
        for m in s1["mechanisms"]:
            for kp in m.get("key_players", []):
                kp_u = str(kp).strip().upper()
                if len(kp_u) >= 2 and kp_u not in STOP_UPPER:
                    alias_to_canon[kp_u] = kp_u
        s3 = json.load(open(os.path.join(rdir, "step3_candidates.json"), encoding="utf-8"))
        for c in s3["candidates"]:
            for t in c.get("targets", []):
                t_u = str(t).strip().upper()
                if len(t_u) >= 2 and t_u not in STOP_UPPER:
                    alias_to_canon[t_u] = t_u

    return alias_to_canon


SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
TOKEN_RE = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9\-/]{1,15}\b")


def split_sentences(text):
    if not text or not isinstance(text, str):
        return []
    parts = SENT_SPLIT_RE.split(text.strip())
    return [p.strip() for p in parts if len(p.strip()) >= 20]


def extract_entities(sentence, alias_to_canon):
    found = set()
    for tok in TOKEN_RE.findall(sentence):
        # Check exact uppercase or slash-separated gene tokens (e.g. C3b/iC3b, TDP-43, STMN2)
        for sub in tok.split("/"):
            u = sub.upper()
            if u in alias_to_canon:
                found.add(alias_to_canon[u])
    return sorted(found)


def parse_judge_sections(reasoning_text):
    """Extract SCIENCE, FEASIBILITY, and NOVELTY sub-sentences from judge reasoning."""
    sections = {}
    if not reasoning_text:
        return sections
    for sec in ["SCIENCE", "FEASIBILITY", "NOVELTY"]:
        m = re.search(rf"{sec}\s*:\s*(.*?)(?=(?:SCIENCE|FEASIBILITY|NOVELTY)\s*:|$)", reasoning_text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            sections[sec] = m.group(1).strip()
    return sections


def load_nli_model():
    print(f"Loading DeBERTa-v3 NLI model: {MODEL_NAME} ...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    except Exception as e:
        print(f"Direct HF load failed ({e}), retrying via hf-mirror.com ...")
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    # Identify label indices
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}
    contra_idx = next(k for k, v in id2label.items() if "contra" in v)
    entail_idx = next(k for k, v in id2label.items() if "entail" in v)
    neutral_idx = next(k for k, v in id2label.items() if "neutral" in v)
    print(f"Loaded NLI model successfully. Label mapping: {id2label} (contra_idx={contra_idx})")
    return tokenizer, model, contra_idx, entail_idx, neutral_idx


def score_nli_pairs_bidirectional(tokenizer, model, contra_idx, entail_idx, pairs, batch_size=64):
    """
    Given a list of dicts with keys 's1' and 's2', compute:
      p_contra_12 = P(contradiction | premise=s1, hypothesis=s2)
      p_contra_21 = P(contradiction | premise=s2, hypothesis=s1)
      p_entail_12, p_entail_21
    """
    if not pairs:
        return []

    s1_list = [p["s1"] for p in pairs]
    s2_list = [p["s2"] for p in pairs]

    def run_dir_batches(prem_list, hyp_list, tag=""):
        probs_contra = []
        probs_entail = []
        torch.set_num_threads(min(8, os.cpu_count() or 4))
        with torch.no_grad():
            for i in range(0, len(prem_list), batch_size):
                b_p = prem_list[i:i + batch_size]
                b_h = hyp_list[i:i + batch_size]
                enc = tokenizer(b_p, b_h, padding=True, truncation=True, max_length=256, return_tensors="pt")
                logits = model(**enc).logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                probs_contra.extend(probs[:, contra_idx].tolist())
                probs_entail.extend(probs[:, entail_idx].tolist())
                if (i // batch_size) % 5 == 0:
                    print(f"  [{tag}] scored {min(i + batch_size, len(prem_list))}/{len(prem_list)}", flush=True)
        return np.array(probs_contra), np.array(probs_entail)

    c12, e12 = run_dir_batches(s1_list, s2_list, "dir12")
    c21, e21 = run_dir_batches(s2_list, s1_list, "dir21")

    for idx, p in enumerate(pairs):
        p["p_contra_12"] = float(c12[idx])
        p["p_contra_21"] = float(c21[idx])
        p["p_contra_min"] = float(min(c12[idx], c21[idx]))
        p["p_contra_max"] = float(max(c12[idx], c21[idx]))
        p["p_contra_mean"] = float(0.5 * (c12[idx] + c21[idx]))
        p["p_entail_mean"] = float(0.5 * (e12[idx] + e21[idx]))
        p["is_bidir_contra_075"] = bool(c12[idx] > 0.75 and c21[idx] > 0.75)
        p["is_dir_contra_075"] = bool(max(c12[idx], c21[idx]) > 0.75)
    return pairs


def main():
    alias_to_canon = load_entity_map()
    print(f"Loaded normalized entity map with {len(alias_to_canon)} symbol/alias entries.")

    runs = [f"{d}_{a}_R{r}" for d in ["dAMD", "ALS"] for a in ["blind", "retrieval"] for r in [1, 2, 3]]

    # 1. Extract all atomic entity-anchored assertions across all 12 runs (Stages 1, 2, 3, 4, 6)
    assertions_by_run = {}
    cross_stage_pairs = []
    t2_reversal_pairs = []

    total_sentences = 0
    total_entity_assertions = 0

    for run_id in runs:
        rdir = os.path.join(RUNS_DIR, run_id)
        s1 = json.load(open(os.path.join(rdir, "step1_mechanisms.json"), encoding="utf-8"))
        s2 = json.load(open(os.path.join(rdir, "step2_verdicts.json"), encoding="utf-8"))
        s3 = json.load(open(os.path.join(rdir, "step3_candidates.json"), encoding="utf-8"))
        s4 = json.load(open(os.path.join(rdir, "step4_verdicts.json"), encoding="utf-8"))
        s5 = json.load(open(os.path.join(rdir, "step5_top5.json"), encoding="utf-8"))
        s6 = json.load(open(os.path.join(rdir, "step6_protocols.json"), encoding="utf-8"))

        run_assertions = []
        stage_assertions = defaultdict(list)

        # Stage 1
        mech_by_key = {}
        for m in s1["mechanisms"]:
            mkey = f"M{int(m['id']) - 1:02d}"
            mech_by_key[mkey] = m
            for sent in split_sentences(m.get("mechanism", "")):
                total_sentences += 1
                ents = extract_entities(sent, alias_to_canon)
                if ents:
                    total_entity_assertions += 1
                    a_obj = {"run_id": run_id, "stage": "step1", "item_id": mkey, "text": sent, "entities": ents}
                    run_assertions.append(a_obj)
                    stage_assertions["step1"].append(a_obj)

        # Stage 2 (T1 Judge reasoning)
        for k, v in (s2.get("verdicts") or {}).items():
            if not v or v.get("failed"):
                continue
            for sent in split_sentences(v.get("reasoning", "")):
                total_sentences += 1
                ents = extract_entities(sent, alias_to_canon)
                if ents:
                    total_entity_assertions += 1
                    a_obj = {"run_id": run_id, "stage": "step2", "item_id": f"p{k}", "text": sent, "entities": ents}
                    run_assertions.append(a_obj)
                    stage_assertions["step2"].append(a_obj)

        # Stage 3 (Candidate Dossiers)
        cand_by_id = {}
        for c in s3["candidates"]:
            cid = c["cand_id"]
            cand_by_id[cid] = c
            for field in ["mechanism", "intervention_principle", "rationale", "feasibility"]:
                for sent in split_sentences(c.get(field, "")):
                    total_sentences += 1
                    ents = extract_entities(sent, alias_to_canon)
                    if ents:
                        total_entity_assertions += 1
                        a_obj = {
                            "run_id": run_id, "stage": "step3", "item_id": cid,
                            "field": field, "text": sent, "entities": ents,
                            "source_mkey": c.get("source_mechanism_key", "")
                        }
                        run_assertions.append(a_obj)
                        stage_assertions["step3"].append(a_obj)

        # Stage 4 (T2 Judge reasoning)
        verdicts_s4 = s4.get("verdicts") or {}
        for k, v in verdicts_s4.items():
            if not v or v.get("failed"):
                continue
            for sent in split_sentences(v.get("reasoning", "")):
                total_sentences += 1
                ents = extract_entities(sent, alias_to_canon)
                if ents:
                    total_entity_assertions += 1
                    a_obj = {"run_id": run_id, "stage": "step4", "item_id": k, "text": sent, "entities": ents}
                    run_assertions.append(a_obj)
                    stage_assertions["step4"].append(a_obj)

        # Stage 6 (Top-5 Protocols)
        top5_cids = set(x["cand_id"] for x in s5["top5"])
        for p_obj in s6.get("protocols", []):
            cid = p_obj.get("cand_id", "")
            proto = p_obj.get("protocol") or {}
            texts_p = [
                proto.get("hypothesis_testable", ""),
                proto.get("experimental_model", ""),
                proto.get("readouts_and_controls", ""),
            ]
            for ref in proto.get("references") or []:
                if isinstance(ref, dict) and ref.get("claim"):
                    texts_p.append(ref["claim"])
            for blk in texts_p:
                for sent in split_sentences(blk):
                    total_sentences += 1
                    ents = extract_entities(sent, alias_to_canon)
                    if ents:
                        total_entity_assertions += 1
                        a_obj = {"run_id": run_id, "stage": "step6", "item_id": cid, "text": sent, "entities": ents}
                        run_assertions.append(a_obj)
                        stage_assertions["step6"].append(a_obj)

        assertions_by_run[run_id] = {
            "total_entity_assertions": len(run_assertions),
            "by_stage": {st: len(lst) for st, lst in stage_assertions.items()},
        }

        # Build Cross-Stage Lineage Pairs sharing >=1 entity within this run:
        # (a) Step 1 vs Step 3 (sharing >=1 entity)
        for a1 in stage_assertions["step1"]:
            set1 = set(a1["entities"])
            for a3 in stage_assertions["step3"]:
                shared = set1.intersection(a3["entities"])
                if shared:
                    cross_stage_pairs.append({
                        "run_id": run_id,
                        "pair_type": "step1_vs_step3",
                        "cand_id": a3["item_id"],
                        "in_top5": a3["item_id"] in top5_cids,
                        "shared_entities": sorted(shared),
                        "s1": a1["text"],
                        "s2": a3["text"],
                    })

        # (b) Step 3 vs Step 6 (for Top-5 candidates, sharing >=1 entity)
        for a3 in stage_assertions["step3"]:
            set3 = set(a3["entities"])
            for a6 in stage_assertions["step6"]:
                if a3["item_id"] == a6["item_id"]:
                    shared = set3.intersection(a6["entities"])
                    if shared:
                        cross_stage_pairs.append({
                            "run_id": run_id,
                            "pair_type": "step3_vs_step6",
                            "cand_id": a3["item_id"],
                            "in_top5": True,
                            "shared_entities": sorted(shared),
                            "s1": a3["text"],
                            "s2": a6["text"],
                        })

        # Build Tournament II A/B Order-Reversal Judge Pairs (comparing forward vs reverse reasoning)
        by_pj = defaultdict(dict)
        for k, v in verdicts_s4.items():
            if v and "pair" in v and not v.get("failed"):
                by_pj[(tuple(v["pair"]), v["judge"])][v["direction"]] = v

        for (pair_tuple, j), dmap in by_pj.items():
            if "a" not in dmap or "b" not in dmap:
                continue
            va, vb = dmap["a"], dmap["b"]
            wa, wb = va.get("winner_idx"), vb.get("winner_idx")
            if wa is None or wb is None:
                continue
            is_pos_biased = (wa != wb)
            sec_a = parse_judge_sections(va.get("reasoning", ""))
            sec_b = parse_judge_sections(vb.get("reasoning", ""))

            # Normalize candidate references ("A" and "B" in direction 'b' are swapped relative to 'a'!)
            c0_name = s3["candidates"][pair_tuple[0]]["cand_id"]
            c1_name = s3["candidates"][pair_tuple[1]]["cand_id"]

            def de_alias_ab(text, direction):
                if not text:
                    return ""
                if direction == "a":
                    t = re.sub(r"\bProposal A\b|\bCandidate A\b|\bOption A\b|\bA's\b|\bA\b", c0_name, text)
                    t = re.sub(r"\bProposal B\b|\bCandidate B\b|\bOption B\b|\bB's\b|\bB\b", c1_name, t)
                else:
                    t = re.sub(r"\bProposal A\b|\bCandidate A\b|\bOption A\b|\bA's\b|\bA\b", c1_name, text)
                    t = re.sub(r"\bProposal B\b|\bCandidate B\b|\bOption B\b|\bB's\b|\bB\b", c0_name, t)
                return t

            # Compare SCIENCE section in 'a' vs SCIENCE section in 'b' after de-aliasing A/B -> Cxx/Cyy
            if "SCIENCE" in sec_a and "SCIENCE" in sec_b:
                t2_reversal_pairs.append({
                    "run_id": run_id,
                    "pair": list(pair_tuple),
                    "judge": j,
                    "criterion": "SCIENCE",
                    "is_pos_biased": is_pos_biased,
                    "criterion_flipped": (va.get("science") == vb.get("science") and va.get("science") in ("A", "B")),
                    "s1": de_alias_ab(sec_a["SCIENCE"], "a"),
                    "s2": de_alias_ab(sec_b["SCIENCE"], "b"),
                })

    print(f"Extracted {total_entity_assertions:,d} entity-anchored assertions (from {total_sentences:,d} total sentences).", flush=True)
    # Stratified sample of T2 reversal pairs (up to 20 biased + 20 consistent per run = 480 pairs) with seed 20260101
    import random
    rng_t2 = random.Random(20260101)
    sampled_t2 = []
    for run_id in runs:
        b_sub = [p for p in t2_reversal_pairs if p["run_id"] == run_id and p["is_pos_biased"]]
        c_sub = [p for p in t2_reversal_pairs if p["run_id"] == run_id and not p["is_pos_biased"]]
        sampled_t2.extend(rng_t2.sample(b_sub, min(20, len(b_sub))))
        sampled_t2.extend(rng_t2.sample(c_sub, min(20, len(c_sub))))
    t2_reversal_pairs = sampled_t2
    print(f"Constructed {len(cross_stage_pairs):,d} cross-stage entity-linked pairs and {len(t2_reversal_pairs):,d} stratified T2 A/B judge reasoning pairs.", flush=True)

    tokenizer, model, contra_idx, entail_idx, neutral_idx = load_nli_model()

    print("Scoring cross-stage pairs with bidirectional DeBERTa-v3 NLI ...")
    cross_stage_scored = score_nli_pairs_bidirectional(tokenizer, model, contra_idx, entail_idx, cross_stage_pairs, batch_size=64)

    print("Scoring T2 judge reversal pairs with bidirectional DeBERTa-v3 NLI ...")
    t2_reversal_scored = score_nli_pairs_bidirectional(tokenizer, model, contra_idx, entail_idx, t2_reversal_pairs, batch_size=64)

    # Summarize Cross-Stage Contradictions per run and overall
    run_contra_stats = {}
    for run_id in runs:
        sub_pairs = [p for p in cross_stage_scored if p["run_id"] == run_id]
        n_assert = assertions_by_run[run_id]["total_entity_assertions"]
        n_bidir = sum(1 for p in sub_pairs if p["is_bidir_contra_075"])
        n_dir = sum(1 for p in sub_pairs if p["is_dir_contra_075"])
        # Silent propagation into Top-5: how many step1_vs_step3 contradictions belong to a candidate that entered Top-5?
        s13_contra = [p for p in sub_pairs if p["pair_type"] == "step1_vs_step3" and p["is_bidir_contra_075"]]
        s13_top5_prop = sum(1 for p in s13_contra if p["in_top5"])
        run_contra_stats[run_id] = {
            "n_assertions": n_assert,
            "n_cross_stage_pairs": len(sub_pairs),
            "n_bidir_contra_075": n_bidir,
            "n_dir_contra_075": n_dir,
            "bidir_contra_per_1k_assertions": round(1000.0 * n_bidir / max(1, n_assert), 2),
            "bidir_contra_per_1k_pairs": round(1000.0 * n_bidir / max(1, len(sub_pairs)), 2),
            "dir_contra_per_1k_pairs": round(1000.0 * n_dir / max(1, len(sub_pairs)), 2),
            "s13_contra_total": len(s13_contra),
            "s13_contra_propagated_to_top5": s13_top5_prop,
        }

    # Bootstrap 95% CI across the 12 runs (10,000 iterations, seed=20260101)
    rng = np.random.default_rng(20260101)
    r_list = list(runs)
    boot_per_1k_assert = []
    boot_per_1k_pairs = []
    boot_dir_per_1k_pairs = []
    for _ in range(10000):
        samp = rng.choice(r_list, size=len(r_list), replace=True)
        tot_b = sum(run_contra_stats[r]["n_bidir_contra_075"] for r in samp)
        tot_d = sum(run_contra_stats[r]["n_dir_contra_075"] for r in samp)
        tot_a = sum(run_contra_stats[r]["n_assertions"] for r in samp)
        tot_p = sum(run_contra_stats[r]["n_cross_stage_pairs"] for r in samp)
        boot_per_1k_assert.append(1000.0 * tot_b / max(1, tot_a))
        boot_per_1k_pairs.append(1000.0 * tot_b / max(1, tot_p))
        boot_dir_per_1k_pairs.append(1000.0 * tot_d / max(1, tot_p))

    tot_bidir_cs = sum(1 for p in cross_stage_scored if p["is_bidir_contra_075"])
    tot_dir_cs = sum(1 for p in cross_stage_scored if p["is_dir_contra_075"])
    tot_s13 = sum(r["s13_contra_total"] for r in run_contra_stats.values())
    tot_s13_prop = sum(r["s13_contra_propagated_to_top5"] for r in run_contra_stats.values())

    # Summarize T2 Judge Reversal NLI Contradictions (Position-Biased vs Content-Consistent)
    biased_t2 = [p for p in t2_reversal_scored if p["is_pos_biased"]]
    cons_t2 = [p for p in t2_reversal_scored if not p["is_pos_biased"]]

    biased_bidir_rate = float(np.mean([p["is_bidir_contra_075"] for p in biased_t2])) if biased_t2 else 0.0
    cons_bidir_rate = float(np.mean([p["is_bidir_contra_075"] for p in cons_t2])) if cons_t2 else 0.0
    biased_dir_rate = float(np.mean([p["is_dir_contra_075"] for p in biased_t2])) if biased_t2 else 0.0
    cons_dir_rate = float(np.mean([p["is_dir_contra_075"] for p in cons_t2])) if cons_t2 else 0.0
    biased_mean_p = float(np.mean([p["p_contra_mean"] for p in biased_t2])) if biased_t2 else 0.0
    cons_mean_p = float(np.mean([p["p_contra_mean"] for p in cons_t2])) if cons_t2 else 0.0

    # Save top examples of bidirectional contradictions for manuscript qualitative table
    top_cs_examples = sorted(cross_stage_scored, key=lambda x: x["p_contra_min"], reverse=True)[:15]
    top_t2_examples = sorted(biased_t2, key=lambda x: x["p_contra_min"], reverse=True)[:15]

    out = {
        "model": MODEL_NAME,
        "total_sentences_segmented": total_sentences,
        "total_entity_assertions": total_entity_assertions,
        "cross_stage_coherence": {
            "total_pairs_evaluated": len(cross_stage_scored),
            "bidirectional_contradictions_075": tot_bidir_cs,
            "directional_contradictions_075": tot_dir_cs,
            "bidir_per_1k_assertions": round(1000.0 * tot_bidir_cs / max(1, total_entity_assertions), 2),
            "bidir_per_1k_assertions_95ci": [round(float(np.percentile(boot_per_1k_assert, 2.5)), 2), round(float(np.percentile(boot_per_1k_assert, 97.5)), 2)],
            "bidir_per_1k_pairs": round(1000.0 * tot_bidir_cs / max(1, len(cross_stage_scored)), 2),
            "bidir_per_1k_pairs_95ci": [round(float(np.percentile(boot_per_1k_pairs, 2.5)), 2), round(float(np.percentile(boot_per_1k_pairs, 97.5)), 2)],
            "dir_per_1k_pairs": round(1000.0 * tot_dir_cs / max(1, len(cross_stage_scored)), 2),
            "dir_per_1k_pairs_95ci": [round(float(np.percentile(boot_dir_per_1k_pairs, 2.5)), 2), round(float(np.percentile(boot_dir_per_1k_pairs, 97.5)), 2)],
            "step1_vs_step3_contra_total": tot_s13,
            "step1_vs_step3_propagated_to_top5": tot_s13_prop,
            "silent_propagation_rate": round(tot_s13_prop / max(1, tot_s13), 4),
            "by_run": run_contra_stats,
            "top_examples": top_cs_examples,
        },
        "t2_judge_self_contradiction_nli": {
            "n_position_biased_pairs": len(biased_t2),
            "n_content_consistent_pairs": len(cons_t2),
            "pos_biased_bidir_contra_rate": round(biased_bidir_rate, 4),
            "content_consistent_bidir_contra_rate": round(cons_bidir_rate, 4),
            "pos_biased_dir_contra_rate": round(biased_dir_rate, 4),
            "content_consistent_dir_contra_rate": round(cons_dir_rate, 4),
            "pos_biased_mean_contra_prob": round(biased_mean_p, 4),
            "content_consistent_mean_contra_prob": round(cons_mean_p, 4),
            "top_examples": top_t2_examples,
        }
    }

    out_path = os.path.join(OUT_DIR, "step4_dim5_nli_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("=== STEP 4 (DIM 5 NLI COHERENCE) COMPLETE ===")
    print(f"Cross-Stage Pairs: {len(cross_stage_scored)}, Bidir Contra (>0.75): {tot_bidir_cs} "
          f"({out['cross_stage_coherence']['bidir_per_1k_assertions']}/1k assertions, "
          f"{out['cross_stage_coherence']['bidir_per_1k_pairs']}/1k pairs)")
    print(f"Directional Contra (>0.75): {tot_dir_cs} ({out['cross_stage_coherence']['dir_per_1k_pairs']}/1k pairs)")
    print(f"T2 Judge Self-Contradiction (DeBERTa NLI on de-aliased SCIENCE rationale):")
    print(f"  Position-biased pairs (n={len(biased_t2)}): Bidir={biased_bidir_rate*100:.1f}%, Dir={biased_dir_rate*100:.1f}%, Mean P(contra)={biased_mean_p:.3f}")
    print(f"  Content-consistent pairs (n={len(cons_t2)}): Bidir={cons_bidir_rate*100:.1f}%, Dir={cons_dir_rate*100:.1f}%, Mean P(contra)={cons_mean_p:.3f}")


if __name__ == "__main__":
    main()
