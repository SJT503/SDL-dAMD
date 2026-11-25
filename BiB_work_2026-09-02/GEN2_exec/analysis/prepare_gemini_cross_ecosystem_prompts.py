#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
prepare_gemini_cross_ecosystem_prompts.py
Extracts exact frozen stimuli from dAMD_blind_R1, ALS_blind_R1, expB, and expC_v4
for the Google Gemini (Pro High-Reasoning vs Flash Low-Reasoning) Cross-Ecosystem Validation Cohort.
"""

import os
import json
import itertools

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\GEN2_exec"
OUT_DIR = os.path.join(BASE, "data", "gemini_stimuli")
os.makedirs(OUT_DIR, exist_ok=True)


def build_stimuli():
    # 1. dAMD and ALS Top-10 candidates from dAMD_blind_R1 and ALS_blind_R1
    for dis, folder in [("dAMD", "dAMD_blind_R1"), ("ALS", "ALS_blind_R1")]:
        cpath = os.path.join(BASE, "runs", folder, "step3_candidates.json")
        cands = json.load(open(cpath, encoding="utf-8"))["candidates"]
        # 45 pairs
        pairs = []
        for idx, (ca, cb) in enumerate(itertools.combinations(cands, 2), 1):
            pairs.append({
                "pair_id": f"{dis}_P{idx:02d}",
                "i": ca["rank"],
                "j": cb["rank"],
                "cand_i": {
                    "cand_id": ca["cand_id"],
                    "name": ca["name"],
                    "source_mechanism_key": ca["source_mechanism_key"],
                    "mechanism": ca["mechanism"],
                    "targets": ca["targets"],
                    "intervention_principle": ca["intervention_principle"],
                    "rationale": ca["rationale"],
                    "feasibility": ca["feasibility"],
                },
                "cand_j": {
                    "cand_id": cb["cand_id"],
                    "name": cb["name"],
                    "source_mechanism_key": cb["source_mechanism_key"],
                    "mechanism": cb["mechanism"],
                    "targets": cb["targets"],
                    "intervention_principle": cb["intervention_principle"],
                    "rationale": cb["rationale"],
                    "feasibility": cb["feasibility"],
                },
            })
        with open(os.path.join(OUT_DIR, f"t2_{dis}_45pairs.json"), "w", encoding="utf-8") as fh:
            json.dump(pairs, fh, indent=2, ensure_ascii=False)

    # 2. Experiment B: 14 domains (h1 mechanism from _shared_stage1) across 3 arms
    spec = json.load(open(os.path.join(BASE, "expB_prompts.json"), encoding="utf-8"))
    expb_items = []
    for d in spec["domains"]:
        did = d["domain_id"]
        s1_path = os.path.join(BASE, "runs", "expB", "_shared_stage1", f"{did}_stage1.json")
        s1 = json.load(open(s1_path, encoding="utf-8"))
        # take h1
        h1_mech = next(x["mechanism"] for x in s1 if int(x["id"]) == 1)
        expb_items.append({
            "domain_id": did,
            "domain": d["domain"],
            "mesh_term": d["mesh_term"],
            "tier": d["tier"],
            "h1_mechanism": h1_mech,
        })
    with open(os.path.join(OUT_DIR, "expB_14domains_h1.json"), "w", encoding="utf-8") as fh:
        json.dump({"templates": spec["stage2_templates"], "domains": expb_items}, fh, indent=2, ensure_ascii=False)

    # 3. Experiment C: 30 stratified Mendelian diseases across 0%, 25%, 50% del_topIC
    # Extract exact prompts used in calls_log.jsonl or rebuild via run_expC_v4
    res_c = [json.loads(l) for l in open(os.path.join(BASE, "runs", "expC_v4", "results.jsonl"), encoding="utf-8")]
    # Find pair_ids that have all 3 doses (0, 25, 50) in del_topIC
    by_pair = {}
    for r in res_c:
        if r["arm"] == "del_topIC":
            by_pair.setdefault(r["pair_id"], {})[r["dose_target"]] = {
                "pair_id": r["pair_id"],
                "gene_symbol": r["gene_symbol"],
                "aliases": r.get("aliases") or [],
                "dose_target": r["dose_target"],
                "n_pheno_terms_kept": r["n_pheno_terms_kept"],
            }
    complete_pairs = sorted([pid for pid, dmap in by_pair.items() if {0, 25, 50}.issubset(set(dmap.keys()))])
    print(f"Complete 3-dose del_topIC pairs in results.jsonl: {len(complete_pairs)}")
    with open(os.path.join(OUT_DIR, "expC_complete_pairs.json"), "w", encoding="utf-8") as fh:
        json.dump({pid: by_pair[pid] for pid in complete_pairs[:40]}, fh, indent=2, ensure_ascii=False)
    print("Prepared stimuli in:", OUT_DIR)


if __name__ == "__main__":
    build_stimuli()
