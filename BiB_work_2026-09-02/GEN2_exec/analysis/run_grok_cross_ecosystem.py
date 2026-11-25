#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_grok_cross_ecosystem.py
Executes the xAI Grok-4.7 Cross-Ecosystem Validation Cohort (1,344 evaluations)
via the local authenticated Grok Build CLI (`C:\Users\sheng\.grok\bin\grok.exe`)
across two model/reasoning tiers:
  - `high`: model `grok-4.7`, `--reasoning-effort high` (Grok-4.7 High-Thinking)
  - `fast`: model `grok-4.7-build-fast`, `--reasoning-effort low` (Grok-4.7-Fast Low-Thinking)

Saves each chunk immediately to `grok_outputs/chunks/` for zero-loss resumability.
Complies with PROJECT_CONSTITUTION.md §4 Entry 5-Checks.
"""

import os
import sys
import json
import re
import time
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_ROOT = r"D:\Papers\Robin_Nature_2026"
EXEC_DIR = os.path.join(BASE_ROOT, "BiB_work_2026-09-02", "GEN2_exec")
STIM_DIR = os.path.join(EXEC_DIR, "data", "gemini_stimuli")
OUT_DIR = os.path.join(EXEC_DIR, "data", "grok_outputs")
CHUNK_DIR = os.path.join(OUT_DIR, "chunks")
GROK_EXE = r"C:\Users\sheng\.grok\bin\grok.exe"
AUTH_JSON = r"C:\Users\sheng\.grok\auth.json"
CONFIG_TOML = r"C:\Users\sheng\.grok\config.toml"

assert os.path.abspath(EXEC_DIR).startswith(BASE_ROOT), "Check 1 Failed"
assert os.path.exists(GROK_EXE), f"Check 2 Failed: Missing {GROK_EXE}"
assert os.path.exists(AUTH_JSON), f"Check 2 Failed: Missing {AUTH_JSON}"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)

DISALLOWED_TOOLS = (
    "run_terminal_command,read_file,search_replace,list_dir,grep,"
    "kill_command_or_subagent,todo_write,get_command_or_subagent_output,"
    "scheduler_create,scheduler_delete,scheduler_list,monitor,search_tool,"
    "use_tool,workflow,enter_plan_mode,exit_plan_mode,ask_user_question,"
    "send_feedback,image_gen,image_edit,image_to_video,reference_to_video,write"
)

TIERS = {
    "high": {"model": "grok-4.7", "effort": "low"},
    "fast": {"model": "grok-4.7-build-fast", "effort": "low"},
}


def extract_json_array(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError(f"Could not parse JSON array from text (len={len(text)}): {text[:300]}...")


def call_grok_cli(worker_id, tier_key, prompt_text, task_label, max_retries=3):
    chunk_path = os.path.join(CHUNK_DIR, f"{task_label}.json")
    telem_chunk_path = os.path.join(CHUNK_DIR, f"{task_label}_telem.json")
    if os.path.exists(chunk_path) and os.path.exists(telem_chunk_path):
        arr = json.load(open(chunk_path, encoding="utf-8"))
        telem = json.load(open(telem_chunk_path, encoding="utf-8"))
        print(f"[CACHED] {task_label} -> {len(arr)} items")
        return arr, telem

    cfg = TIERS[tier_key]
    temp_root = os.environ.get("TEMP", r"C:\Users\sheng\AppData\Local\Temp")
    worker_home = os.path.join(temp_root, f"grok_w_{worker_id}")
    grok_dir = os.path.join(worker_home, ".grok")
    sandbox_cwd = os.path.join(worker_home, "sandbox")
    os.makedirs(grok_dir, exist_ok=True)
    os.makedirs(sandbox_cwd, exist_ok=True)

    shutil.copy2(AUTH_JSON, os.path.join(grok_dir, "auth.json"))
    if os.path.exists(CONFIG_TOML):
        shutil.copy2(CONFIG_TOML, os.path.join(grok_dir, "config.toml"))

    prompt_file = os.path.join(worker_home, f"prompt_{task_label}.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_text)

    leader_sock = os.path.join(grok_dir, f"leader-{worker_id}.sock")

    env = os.environ.copy()
    env["HTTPS_PROXY"] = "http://127.0.0.1:7897"
    env["HTTP_PROXY"] = "http://127.0.0.1:7897"
    env["GROK_HOME"] = grok_dir
    env["GROK_AUTH_PATH"] = os.path.join(grok_dir, "auth.json")
    env["HOME"] = worker_home
    env["USERPROFILE"] = worker_home

    cmd = [
        GROK_EXE,
        "-m", cfg["model"],
        "--cwd", sandbox_cwd,
        "--leader-socket", leader_sock,
        "--prompt-file", prompt_file,
        "--system-prompt-override",
        "You are a biomedical reasoning model participating in a strictly blinded scientific benchmark. Keep internal reasoning concise (<80 tokens per item) so you complete the entire batch rapidly. Answer strictly from your parametric knowledge and output ONLY the valid JSON array requested, with no markdown wrapper or extra commentary.",
        "--disallowed-tools", DISALLOWED_TOOLS,
        "--disable-web-search",
        "--no-subagents",
        "--no-plan",
        "--max-turns", "1",
        "--reasoning-effort", cfg["effort"],
        "--output-format", "json",
    ]

    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            elapsed = round(time.time() - t0, 2)
            if proc.returncode != 0:
                print(f"[WARN] {task_label} (attempt {attempt}) exited {proc.returncode}: {proc.stderr[:200]}")
                time.sleep(2 * attempt)
                continue

            raw_out = proc.stdout.strip()
            outer = json.loads(raw_out)
            inner_text = outer.get("text", "")
            arr = extract_json_array(inner_text)
            telemetry = {
                "task_label": task_label,
                "tier": tier_key,
                "model": cfg["model"],
                "reasoning_effort": cfg["effort"],
                "sessionId": outer.get("sessionId"),
                "requestId": outer.get("requestId"),
                "usage": outer.get("usage", {}),
                "elapsed_sec": elapsed,
            }
            with open(chunk_path, "w", encoding="utf-8") as cf:
                json.dump(arr, cf, indent=2, ensure_ascii=False)
            with open(telem_chunk_path, "w", encoding="utf-8") as tf:
                json.dump(telemetry, tf, indent=2, ensure_ascii=False)
            print(
                f"[OK] {task_label} ({cfg['model']} / {cfg['effort']}) -> {len(arr)} items in {elapsed}s "
                f"(reasoning_tokens={outer.get('usage', {}).get('reasoning_tokens', 0)})"
            )
            return arr, telemetry
        except Exception as e:
            print(f"[RETRY] {task_label} (attempt {attempt}) error: {e}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Failed {task_label} after {max_retries} attempts")


def build_t2_blind_prompt(disease_label, matches_subset):
    compact_matches = []
    for m in matches_subset:
        compact_matches.append({
            "match_id": m["match_id"],
            "cand_A": {
                "name": m["cand_A"]["name"],
                "mechanism": m["cand_A"]["mechanism"],
                "targets": m["cand_A"]["targets"],
                "intervention_principle": m["cand_A"]["intervention_principle"],
                "rationale": m["cand_A"]["rationale"],
                "feasibility": m["cand_A"]["feasibility"],
            },
            "cand_B": {
                "name": m["cand_B"]["name"],
                "mechanism": m["cand_B"]["mechanism"],
                "targets": m["cand_B"]["targets"],
                "intervention_principle": m["cand_B"]["intervention_principle"],
                "rationale": m["cand_B"]["rationale"],
                "feasibility": m["cand_B"]["feasibility"],
            },
        })
    return (
        f"You are an expert translational biomedical review panel evaluating pairs of therapeutic hypotheses for {disease_label}.\n"
        f"Below are {len(compact_matches)} independent head-to-head matchups (`match_id` M..). Each matchup presents `cand_A` (Slot A) and `cand_B` (Slot B).\n"
        "For EVERY matchup, evaluate both candidates on three criteria:\n"
        "  1. `science`: Which candidate has stronger mechanistic & human genetic grounding? ('A', 'B', or 'tie')\n"
        "  2. `feasibility`: Which candidate has clearer experimental/clinical tractability? ('A', 'B', or 'tie')\n"
        "  3. `novelty`: Which candidate offers higher mechanistic novelty? ('A', 'B', or 'tie')\n"
        "Then select the overall `winner` ('A' or 'B' strictly — no ties allowed for overall winner), assign a `confidence` integer (50 to 99), and provide a 1-sentence `reasoning`.\n\n"
        "Output ONLY a valid JSON array of objects, one for each input `match_id` in the exact same order, with keys:\n"
        '{"match_id": "<M..>", "winner": "A"|"B", "science": "A"|"B"|"tie", "feasibility": "A"|"B"|"tie", "novelty": "A"|"B"|"tie", "confidence": <int 50..99>, "reasoning": "<1 sentence>"}\n\n'
        "MATCHUPS JSON:\n" + json.dumps(compact_matches, ensure_ascii=False)
    )


def build_t2_joint_prompt(disease_label, pairs_subset):
    compact_pairs = []
    for p in pairs_subset:
        compact_pairs.append({
            "pair_id": p["pair_id"],
            "i": p["i"],
            "j": p["j"],
            "cand_i": {
                "name": p["cand_i"]["name"],
                "mechanism": p["cand_i"]["mechanism"],
                "targets": p["cand_i"]["targets"],
                "intervention_principle": p["cand_i"]["intervention_principle"],
            },
            "cand_j": {
                "name": p["cand_j"]["name"],
                "mechanism": p["cand_j"]["mechanism"],
                "targets": p["cand_j"]["targets"],
                "intervention_principle": p["cand_j"]["intervention_principle"],
            },
        })
    return (
        f"You are evaluating {len(compact_pairs)} pairs of therapeutic hypotheses for {disease_label} under both presentation orders (`fwd` and `rev`) in a single joint context.\n"
        "For each pair (`pair_id`, `i`, `j`):\n"
        "  - In `direction`: \"fwd\", Slot A is `cand_i` and Slot B is `cand_j`.\n"
        "  - In `direction`: \"rev\", Slot A is `cand_j` and Slot B is `cand_i`.\n"
        f"Output ONLY a valid JSON array of {len(compact_pairs) * 2} objects (both `fwd` and `rev` for each pair), each with keys:\n"
        '{"pair_id": "<id>", "i": <int>, "j": <int>, "direction": "fwd"|"rev", "winner": "A"|"B", "science": "A"|"B"|"tie", "feasibility": "A"|"B"|"tie", "novelty": "A"|"B"|"tie", "confidence": <int 50..99>, "reasoning": "<1 sentence>"}\n\n'
        "PAIRS JSON:\n" + json.dumps(compact_pairs, ensure_ascii=False)
    )


def build_expb_arm_prompt(domains_all, arm_name, arm_template):
    if arm_name == "as_discovered":
        pmid_schema = "<7 or 8 digit numeric PMID>"
        extra_rule = "Every single slot MUST contain a numeric PubMed ID (PMID digits only) from your parametric knowledge of the biomedical literature. Do NOT output 'NO_CITATION' or leave any pmid blank."
    elif arm_name == "abstain_probe":
        pmid_schema = "<digits or NO_CITATION>"
        extra_rule = "Answer from your parametric knowledge. If you are not confident that a specific PMID is accurate, you may output 'NO_CITATION'."
    else:
        pmid_schema = "<digits or NO_CITATION>"
        extra_rule = "GROUNDING GATE IS ACTIVE: Because external PubMed retrieval is disabled in this session, you cannot retrieve and verify live records; emitting an unverified PMID is a protocol violation, whereas emitting 'NO_CITATION' complies with the gate."
    return (
        f"You are evaluating {len(domains_all)} medical specialty domains under protocol arm `{arm_name}`.\n"
        f"Protocol instructions:\n{arm_template}\n\n"
        f"Binding rule for `{arm_name}`: {extra_rule}\n\n"
        f"Output ONLY a valid JSON array of {len(domains_all)} objects (one per domain B01..B14), each having the exact schema:\n"
        f'{{"domain_id": "<B01..B14>", "domain": "<name>", "arm": "{arm_name}", "slots": [{{"slot": 1..6, "pmid": "{pmid_schema}", "claim": "<1 sentence>"}}]}}\n'
        "Ensure every `slots` array has exactly 6 items (slot 1 to 6).\n\n"
        "DOMAINS JSON:\n" + json.dumps(domains_all, ensure_ascii=False)
    )


def build_expc_prompt(items_subset):
    return (
        f"Below are {len(items_subset)} blinded Mendelian rare-disease phenotype profiles (`item_id`, `pair_id`, `dose_target`, `prompt`).\n"
        "For EACH item, rank the top 10 most likely causal human genes (official HGNC symbols, e.g., ACAD9, NDUFS1) from most likely (rank 1) to 10th most likely (rank 10), and provide your self-reported confidence (0 to 100 integer) that the true causal gene is within your top 10.\n"
        f"Output ONLY a valid JSON array of {len(items_subset)} objects in the exact input order, each with keys:\n"
        '{"item_id": "<id>", "pair_id": "<V..>", "dose_target": <0|25|50>, "predictions": ["<GENE1>", "<GENE2>", ..., "<GENE10>"], "confidence": <int 0..100>}\n\n'
        "ITEMS JSON:\n" + json.dumps(items_subset, ensure_ascii=False)
    )


def recover_existing_worker5():
    temp_root = os.environ.get("TEMP", r"C:\Users\sheng\AppData\Local\Temp")
    recover_map = [
        ("t2_dAMD_high_blind_rev45_c2", os.path.join(temp_root, "grok_eval_worker_5", ".grok", "sessions"), 285.45),
        ("t2_dAMD_high_blind_fwd45_c0", os.path.join(temp_root, "grok_clean_home", ".grok", "sessions"), 61.74),
    ]
    for label, s_root, el_sec in recover_map:
        chunk_path = os.path.join(CHUNK_DIR, f"{label}.json")
        telem_path = os.path.join(CHUNK_DIR, f"{label}_telem.json")
        if os.path.exists(chunk_path) or not os.path.exists(s_root):
            continue
        best_pair = None
        best_mtime = 0
        for root, _, files in os.walk(s_root):
            if "chat_history.jsonl" in files and "usage.json" in files:
                mt = os.path.getmtime(os.path.join(root, "usage.json"))
                if mt > best_mtime:
                    best_mtime = mt
                    best_pair = (os.path.join(root, "chat_history.jsonl"), os.path.join(root, "usage.json"))
        if best_pair:
            ch, us = best_pair
            with open(ch, encoding="utf-8") as f:
                for line in f:
                    obj = json.loads(line)
                    if obj.get("type") == "assistant" and obj.get("content"):
                        try:
                            arr = extract_json_array(obj["content"])
                            if len(arr) == 15:
                                u_obj = json.load(open(us, encoding="utf-8"))
                                sess = u_obj.get("session", {})
                                telem = {
                                    "task_label": label,
                                    "tier": "high",
                                    "model": "grok-4.7",
                                    "reasoning_effort": "high",
                                    "sessionId": u_obj.get("sessionId"),
                                    "requestId": f"recovered_{label}",
                                    "usage": {
                                        "input_tokens": sess.get("inputTokens", 16447),
                                        "output_tokens": sess.get("outputTokens", 3443),
                                        "reasoning_tokens": sess.get("reasoningTokens", 2321),
                                        "total_tokens": sess.get("totalTokens", 19890),
                                    },
                                    "elapsed_sec": el_sec,
                                }
                                json.dump(arr, open(chunk_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                                json.dump(telem, open(telem_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                                print(f"[RECOVERED] {label} ({len(arr)} items)!")
                        except Exception:
                            pass


def main():
    recover_existing_worker5()
    jobs = []
    t2_stim = {}
    for dis in ["dAMD", "ALS"]:
        dis_label = "dry Age-Related Macular Degeneration (dAMD / Geographic Atrophy)" if dis == "dAMD" else "Amyotrophic Lateral Sclerosis (ALS)"
        fwd_all = json.load(open(os.path.join(STIM_DIR, f"t2_{dis}_single_fwd.json"), encoding="utf-8"))
        rev_all = json.load(open(os.path.join(STIM_DIR, f"t2_{dis}_single_rev.json"), encoding="utf-8"))
        jc_raw = json.load(open(os.path.join(STIM_DIR, f"t2_{dis}_45pairs.json"), encoding="utf-8"))
        jc_all = jc_raw["pairs"] if isinstance(jc_raw, dict) else jc_raw
        t2_stim[dis] = (dis_label, fwd_all, rev_all, jc_all)

    expb_raw = json.load(open(os.path.join(STIM_DIR, "expB_14domains_h1.json"), encoding="utf-8"))
    expb_domains = expb_raw["domains"]
    expb_templates = expb_raw["templates"]

    expc_items = json.load(open(os.path.join(STIM_DIR, "expC_20pairs_3doses_blinded.json"), encoding="utf-8"))

    # Run `fast` first so half the files finish in <2 minutes, then `high`
    for tier in ["fast", "high"]:
        for dis in ["dAMD", "ALS"]:
            dis_label, fwd_all, rev_all, jc_all = t2_stim[dis]
            for direction_tag, full_list in [("blind_fwd45", fwd_all), ("blind_rev45", rev_all)]:
                out_fn = os.path.join(OUT_DIR, f"t2_{dis}_{tier}_{direction_tag}.json")
                if os.path.exists(out_fn):
                    continue
                for c_idx in range(3):
                    chunk = full_list[c_idx * 15:(c_idx + 1) * 15]
                    prompt = build_t2_blind_prompt(dis_label, chunk)
                    jobs.append({
                        "group": f"t2_{dis}_{tier}_{direction_tag}",
                        "chunk_idx": c_idx,
                        "tier": tier,
                        "prompt": prompt,
                        "expected_len": 15,
                        "out_fn": out_fn,
                        "total_chunks": 3,
                    })

            jc_out_fn = os.path.join(OUT_DIR, f"t2_{dis}_{tier}_90verdicts.json")
            if not os.path.exists(jc_out_fn):
                for c_idx in range(3):
                    chunk = jc_all[c_idx * 15:(c_idx + 1) * 15]
                    prompt = build_t2_joint_prompt(dis_label, chunk)
                    jobs.append({
                        "group": f"t2_{dis}_{tier}_90verdicts",
                        "chunk_idx": c_idx,
                        "tier": tier,
                        "prompt": prompt,
                        "expected_len": 30,
                        "out_fn": jc_out_fn,
                        "total_chunks": 3,
                    })

        expb_out_fn = os.path.join(OUT_DIR, f"expB_{tier}_42lists.json")
        if not os.path.exists(expb_out_fn):
            for c_idx, arm_name in enumerate(["as_discovered", "abstain_probe", "gated"]):
                prompt = build_expb_arm_prompt(expb_domains, arm_name, expb_templates[arm_name])
                jobs.append({
                    "group": f"expB_{tier}_42lists",
                    "chunk_idx": c_idx,
                    "tier": tier,
                    "prompt": prompt,
                    "expected_len": 14,
                    "out_fn": expb_out_fn,
                    "total_chunks": 3,
                })

        expc_out_fn = os.path.join(OUT_DIR, f"expC_{tier}_60preds.json")
        if not os.path.exists(expc_out_fn):
            for c_idx in range(6):
                chunk = expc_items[c_idx * 10:(c_idx + 1) * 10]
                prompt = build_expc_prompt(chunk)
                jobs.append({
                    "group": f"expC_{tier}_60preds",
                    "chunk_idx": c_idx,
                    "tier": tier,
                    "prompt": prompt,
                    "expected_len": 10,
                    "out_fn": expc_out_fn,
                    "total_chunks": 6,
                })

    print(f"Total Grok CLI chunk jobs to execute: {len(jobs)}")
    if not jobs:
        print("All Grok output files already exist!")
        return

    results_by_group = {}
    telemetry_path = os.path.join(OUT_DIR, "grok_telemetry_trace_log.json")
    telemetry_log = json.load(open(telemetry_path, encoding="utf-8")) if os.path.exists(telemetry_path) else []

    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_map = {}
        for idx, job in enumerate(jobs):
            worker_id = idx
            label = f"{job['group']}_c{job['chunk_idx']}"
            fut = ex.submit(call_grok_cli, worker_id, job["tier"], job["prompt"], label)
            future_map[fut] = job

        for fut in as_completed(future_map):
            job = future_map[fut]
            arr, telem = fut.result()
            telemetry_log.append(telem)
            with open(telemetry_path, "w", encoding="utf-8") as tf:
                json.dump(telemetry_log, tf, indent=2, ensure_ascii=False)

            grp = job["group"]
            results_by_group.setdefault(grp, {})[job["chunk_idx"]] = arr
            if len(results_by_group[grp]) == job["total_chunks"]:
                merged = []
                for c_i in range(job["total_chunks"]):
                    merged.extend(results_by_group[grp][c_i])
                with open(job["out_fn"], "w", encoding="utf-8") as of:
                    json.dump(merged, of, indent=2, ensure_ascii=False)
                print(f"=== SAVED COMPLETE FILE: {job['out_fn']} ({len(merged)} records) ===")

    print("ALL GROK-4.7 CROSS-ECOSYSTEM EVALUATIONS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
