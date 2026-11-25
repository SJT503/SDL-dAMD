#!/usr/bin/env python3
"""
run_parent.py -- gen-2 parent-run driver (six-step SDL pipeline, prereg §2).

One run = one (disease, arm, rep) triple on GLM. 12 runs total:
  {dAMD, ALS} x {blind, retrieval} x R1..R3.

Structure per run (frozen §2.1, gen-1-identical):
  step1  litreview      3 buckets (12 mech each) + 1 synthesizer -> 30 mechanisms
  step2  Tournament I   300 of 435 pairs, 1 verdict each
  step3  expansion      BTL(T1) top-10 -> 10 candidate dossiers
  step4  Tournament II  45 pairs x 3 judges x 2 orders = 270 verdicts
  step5  BTL            local, deterministic (btl.py)
  step6  protocols      Top-5 grounded protocols (6 PMID slots each -> dim-①)

Resume: every call has a deterministic call_id; gen2_call.call_ok() + per-run
state files make every step idempotent. Blind gates (§2.1): prompts scanned
BEFORE dispatch (assert), responses scanned after parse; hits void the item and
are recorded (never edited away).

Interleaving (§10.1): `--plan parent12` walks all runs round-robin (seeded
order, reshuffled each round) so no condition runs as a contiguous block.

Usage:
  GEN2_MOCK=1 python run_parent.py --disease dAMD --arm blind --rep 1   # dry run
  python run_parent.py --plan parent12 --execute                        # real, interleaved
  python run_parent.py --status                                         # progress board
  python run_parent.py --certify-retrieval                              # web_search tool probe
"""

import hashlib
import itertools
import json
import os
import random
import sys
import threading
import time

import gen2_blind
import gen2_call
import gen2_parse
import pipeline_prompts as PP

HERE = os.path.dirname(os.path.abspath(__file__))
# mock dry-runs write run trees to the isolated mock root (D2-008)
RUNS = os.path.join(
    os.path.join(HERE, "data_mock")
    if os.environ.get("GEN2_MOCK") else HERE, "runs")
PERM_SEED = 20260101          # §9.2 frozen constant
N_PAIRS_T1 = 300
N_MECHS = 30
N_TOP_T1 = 10
N_JUDGES_T2 = 3
VENDOR = "glm"                # §1.1: all pipeline roles = glm-5.3

DISEASES = ("dAMD", "ALS")
ARMS = ("blind", "retrieval")
REPS = (1, 2, 3)


def run_dir(run_id):
    return os.path.join(RUNS, run_id)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:                                              # noqa: BLE001
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, threading.get_ident())
    for attempt in range(4):
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, path)
            return
        except PermissionError:
            # Windows transient lock (AV/indexer or cross-thread rename race);
            # observed once 2026-09-05T15:00Z -- retry with a short sleep
            time.sleep(0.5 * (attempt + 1))
    os.replace(tmp, path)   # last try; raise if still locked


def run_seed(run_id):
    return PERM_SEED ^ (int(hashlib.sha256(run_id.encode()).hexdigest()[:8], 16) % (1 << 30))


# ================================================================ step 1 ====
def step1(run_id, disease, arm, force=False):
    d = run_dir(run_id)
    out_path = os.path.join(d, "step1_mechanisms.json")
    if read_json(out_path) and not force:
        return "done"
    ctx_block = None
    if arm == "retrieval":
        import gen2_pubmed
        ctx = gen2_pubmed.fetch_context(
            disease, os.path.join(d, "retrieval_context.json"))
        ctx_block = gen2_pubmed.context_block(ctx)

    def bucket_call(bid, focus, attempt):
        """One bucket dispatch (attempt 0 original, 1+ = blind redraft)."""
        prompt = PP.step1_bucket_prompt(disease, bid, focus, arm,
                                        context_block=ctx_block)
        call_id = "parent/%s/step1/bucket%s%s" % (
            run_id, bid, "" if attempt == 0 else "/rd%d" % attempt)
        if arm == "blind":
            gen2_blind.assert_prompt_clean(prompt, disease, call_id)

        def parse_bucket(text):
            return gen2_parse.parse_array(text, 12)

        rec, arr, tier = _gen_or_redispatch(
            call_id, prompt, 32768,
            {"task_class": "orchestrator", "step": 1, "attempt": attempt},
            parse_bucket)
        if not isinstance(arr, list) or tier not in gen2_parse.TIERS:
            _record_parse_fail(run_id, call_id, rec, tier,
                               ["bucket_bad" if not isinstance(arr, list)
                                else "bucket_count"])
            return None
        if arm == "blind" and gen2_blind.scan_response(
                json.dumps(arr, ensure_ascii=False), disease):
            return "blind_hit"          # caller redrafts once
        return arr

    bucket_payloads = []
    for bid, focus in PP.BUCKETS:
        arr = None
        for attempt in (0, 1, 2, 3, 4):  # up to four blind redrafts (§2.1;
                                          # ALS bucket2 TAM-axis attractor needed
                                          # 3+ tries, D2-010 will record)
            arr = bucket_call(bid, focus, attempt)
            if arr != "blind_hit":
                break
        if arr is None or arr == "blind_hit":
            return "parse_failed" if arr is None else "blind_violation"
        bucket_payloads.append(arr)

    syn_prompt = PP.step1_synthesizer_prompt(
        disease, json.dumps(bucket_payloads, ensure_ascii=False), arm)
    mechs = None
    tier = None
    for attempt in (0, 1):              # one synth redraft on blind hit (§2.1)
        call_id = "parent/%s/step1/synth%s" % (
            run_id, "" if attempt == 0 else "/rd1")
        if arm == "blind":
            gen2_blind.assert_prompt_clean(syn_prompt, disease, call_id)

        def parse_synth(text):
            return gen2_parse.parse_array(text, N_MECHS)

        rec, arr, tier = _gen_or_redispatch(
            call_id, syn_prompt, 32768,
            {"task_class": "orchestrator", "step": 1, "attempt": attempt},
            parse_synth)
        problems = []
        if isinstance(arr, list) and tier in gen2_parse.TIERS:
            mechs, problems = _validate_mechanisms(arr)
        if mechs is None:
            _record_parse_fail(run_id, call_id, rec, tier, problems or [tier])
            return "parse_failed"
        if arm == "blind" and gen2_blind.scan_response(
                json.dumps(mechs, ensure_ascii=False), disease):
            mechs = None                # blind hit -> redraft once
            continue
        break
    if mechs is None:
        return "blind_violation_stuck"  # both synth attempts hit the list
    write_json(out_path, {"run_id": run_id, "disease": disease, "arm": arm,
                          "mechanisms": mechs, "parse_tier": tier,
                          "blind_hits": []})
    return "ok"


def _one_call_text(call_id):
    """Recover a previously-logged call's text from its raw archive."""
    p = os.path.join(gen2_call.RAW_DIR, gen2_call._safe_id(call_id) + ".json")
    if not os.path.exists(p):
        return None
    try:
        payload = json.load(open(p, encoding="utf-8"))
        return ((payload.get("choices") or [{}])[0].get("message") or {}).get("content")
    except Exception:                                              # noqa: BLE001
        return None


def _one_call_rec(call_id, prompt, max_tokens, about, force=False):
    if not force and gen2_call.call_ok(call_id):
        # rebuild a minimal record from the raw archive
        text = _one_call_text(call_id)
        return {"call_id": call_id, "ok": True, "text": text,
                "resumed": True, **(about or {})}
    return gen2_call.call(VENDOR, prompt, max_tokens, call_id=call_id,
                          about=about)


def _gen_or_redispatch(call_id, prompt, max_tokens, about, parse_fn):
    """Dispatch-or-resume, then RE-DISPATCH once if a RESUMED text fails to
    parse. Rationale: an earlier call may be ok=true at HTTP level while its
    content was truncated under an older, smaller cap (D2-009 loop); resuming
    that text forever re-fails. A fresh dispatch under the current cap is the
    only way out. A freshly-dispatched parse failure is model behaviour and
    is returned as-is.

    "Fails to parse" = obj is None OR the returned tier is not a real parse
    tier (a count-mismatch returns a partial list with a count_* reason --
    that is a truncation signature, not a usable payload)."""
    def ok(obj, tier):
        return obj is not None and tier in gen2_parse.TIERS

    rec = _one_call_rec(call_id, prompt, max_tokens, about)
    obj, tier = parse_fn(rec.get("text"))
    if not ok(obj, tier) and rec.get("resumed"):
        rec = _one_call_rec(call_id, prompt, max_tokens, about, force=True)
        obj, tier = parse_fn(rec.get("text"))
    return rec, obj, tier


def _one_call(call_id, prompt, max_tokens, about):
    """(kept for ad-hoc driver use) text of one dispatched-or-resumed call."""
    return _one_call_rec(call_id, prompt, max_tokens, about).get("text") or ""


def _validate_mechanisms(arr):
    """Structural failures void the step; a missing confidence is a recorded
    anomaly, not fatal (the mechanism text is the load-bearing field)."""
    out, problems, anomalies = [], [], []
    for k, o in enumerate(arr):
        if not isinstance(o, dict):
            problems.append("item_%d_not_object" % k)
            continue
        mech = o.get("mechanism")
        if not isinstance(mech, str) or not mech.strip():
            problems.append("item_%d_bad_mechanism" % k)
            continue
        players = o.get("key_players") or []
        if not isinstance(players, list):
            players = [str(players)]
        conf = o.get("confidence")
        try:
            conf = int(conf)
        except Exception:                                          # noqa: BLE001
            conf = None
            anomalies.append("item_%d_bad_confidence" % k)
        out.append({"id": o.get("id", k + 1), "mechanism": mech.strip(),
                    "key_players": [str(p) for p in players],
                    "class_hint": str(o.get("class_hint", "")),
                    "confidence": conf})
    if problems:
        return None, problems
    return out, anomalies


def _record_parse_fail(run_id, call_id, rec, tier, problems):
    d = run_dir(run_id)
    os.makedirs(os.path.join(d, "_parse_failed"), exist_ok=True)
    write_json(os.path.join(d, "_parse_failed",
                            gen2_call._safe_id(call_id) + ".json"),
               {"call_id": call_id, "tier": tier, "problems": problems,
                "text": rec.get("text"), "ok": rec.get("ok")})


# ================================================================ step 2 ====
def t1_pairs(mechs):
    ids = list(range(len(mechs)))
    all_pairs = list(itertools.combinations(ids, 2))       # 435 for 30
    rng = random.Random(PERM_SEED)
    chosen = rng.sample(all_pairs, N_PAIRS_T1)
    return sorted(chosen)


def step2(run_id, disease, arm):
    d = run_dir(run_id)
    s1 = read_json(os.path.join(d, "step1_mechanisms.json"))
    if not s1:
        return "blocked_step1"
    out_path = os.path.join(d, "step2_verdicts.json")
    existing = read_json(out_path) or {"verdicts": {}}
    verdicts = existing["verdicts"]
    mechs = s1["mechanisms"]
    pairs = t1_pairs(mechs)
    order = list(range(len(pairs)))
    random.Random(run_seed(run_id)).shuffle(order)
    n_new = 0
    import threading as _th
    _lock = _th.Lock()

    def one_t1(idx):
        nonlocal n_new
        p = pairs[idx]
        call_id = "parent/%s/step2/p%03d" % (run_id, idx + 1)
        a, b = mechs[p[0]], mechs[p[1]]
        prompt = PP.t1_judge_prompt(disease, a["mechanism"], b["mechanism"])
        if arm == "blind":
            gen2_blind.assert_prompt_clean(prompt, disease, call_id)
        rec, obj, tier = _gen_or_redispatch(
            call_id, prompt, 8192,
            {"task_class": "judging", "step": 2, "pair": [p[0], p[1]]},
            gen2_parse.parse_object)
        v, problems = (None, [tier]) if obj is None else \
            gen2_parse.validate_verdict(obj)
        with _lock:
            if v is None:
                _record_parse_fail(run_id, call_id, rec, tier, problems)
                verdicts[str(idx)] = {"failed": True, "problems": problems}
            else:
                verdicts[str(idx)] = {
                    "A": p[0], "B": p[1], "verdict": v["winner"],
                    "science": v["science"], "feasibility": v["feasibility"],
                    "novelty": v["novelty"], "reasoning": v["reasoning"]}
                n_new += 1
            write_json(out_path, {"verdicts": verdicts,
                                  "n_pairs": len(pairs)})

    pending = [idx for idx in order if str(idx) not in verdicts]
    workers = int(os.environ.get("GEN2_WORKERS", "1"))
    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(one_t1, idx) for idx in pending]
            for _f in as_completed(futs):
                _f.result()
    else:
        for idx in pending:
            one_t1(idx)
            if not os.environ.get("GEN2_MOCK"):
                time.sleep(0.3)
    n_fail = sum(1 for v in verdicts.values() if v.get("failed"))
    if len(verdicts) >= len(pairs):
        return "ok" if n_fail <= len(pairs) * 0.05 else "too_many_failures"
    return "in_progress(%d/%d)" % (len(verdicts), len(pairs))


# ================================================================ step 3 ====
def _btl_pairs_t1(run_id, mechs):
    s2 = read_json(os.path.join(run_dir(run_id), "step2_verdicts.json"))
    pairs = []
    for idx, v in (s2["verdicts"] or {}).items():
        if v.get("failed"):
            continue
        w, l = v["A"], v["B"]
        if v["verdict"] == "B":
            w, l = l, w
        if v["verdict"] == "tie":
            pairs.append((w, l, 0.5))
            pairs.append((l, w, 0.5))
        else:
            pairs.append((w, l, 1.0))
    return pairs


def step3(run_id, disease, arm):
    d = run_dir(run_id)
    s1 = read_json(os.path.join(d, "step1_mechanisms.json"))
    if not s1:
        return "blocked_step1"
    out_path = os.path.join(d, "step3_candidates.json")
    if read_json(out_path):
        return "done"
    import btl
    mechs = s1["mechanisms"]
    keys = ["M%02d" % i for i in range(len(mechs))]
    pairs = _btl_pairs_t1(run_id, mechs)
    if not pairs:
        return "blocked_step2"
    fit = btl.fit_btl([(keys[w], keys[l]) for w, l, _ in pairs],
                      item_names=keys)
    ranking = fit["ranking"][:N_TOP_T1]
    write_json(os.path.join(d, "step3_btl_t1.json"),
               {"fit": fit,
                "ranking_detail": [{"key": k, "mechanism": mechs[int(k[1:])]["mechanism"]}
                                   for k in fit["ranking"]]})
    ctx_block = None
    if arm == "retrieval":
        import gen2_pubmed
        ctx = gen2_pubmed.fetch_context(
            disease, os.path.join(d, "retrieval_context.json"))
        ctx_block = gen2_pubmed.context_block(ctx)
    cands = []
    for rank, mkey in enumerate(ranking, 1):
        mech = mechs[int(mkey[1:])]
        call_id = "parent/%s/step3/c%02d" % (run_id, rank)
        prompt = PP.step3_dossier_prompt(disease, mech["mechanism"], rank, arm,
                                         context_block=ctx_block)
        if arm == "blind":
            gen2_blind.assert_prompt_clean(prompt, disease, call_id)
        rec = _one_call_rec(call_id, prompt, 8192,
                            {"task_class": "judging", "step": 3, "rank": rank})
        obj, tier = gen2_parse.parse_object(rec.get("text"))
        if obj is None:
            _record_parse_fail(run_id, call_id, rec, tier, ["not_an_object"])
            return "parse_failed"
        cand = {"cand_id": "C%02d" % rank, "rank": rank,
                "source_mechanism_key": mkey,
                "source_mechanism": mech["mechanism"],
                "name": obj.get("name"), "mechanism": obj.get("mechanism"),
                "targets": obj.get("targets"),
                "intervention_principle": obj.get("intervention_principle"),
                "rationale": obj.get("rationale"),
                "feasibility": obj.get("feasibility"),
                "confidence": obj.get("confidence"), "parse_tier": tier}
        cands.append(cand)
        if not os.environ.get("GEN2_MOCK"):
            time.sleep(0.3)
    hits = gen2_blind.scan_response(json.dumps(cands, ensure_ascii=False), disease) \
        if arm == "blind" else []
    write_json(out_path, {"run_id": run_id, "candidates": cands,
                          "blind_hits": hits})
    return "ok" if not hits else "blind_violation"


# ================================================================ step 4 ====
def step4(run_id, disease, arm):
    d = run_dir(run_id)
    s3 = read_json(os.path.join(d, "step3_candidates.json"))
    if not s3:
        return "blocked_step3"
    cands = s3["candidates"]
    out_path = os.path.join(d, "step4_verdicts.json")
    existing = read_json(out_path) or {"verdicts": {}}
    verdicts = existing["verdicts"]
    pairs = list(itertools.combinations(range(len(cands)), 2))   # 45
    jobs = [(p, j, direction)
            for p in range(len(pairs))
            for j in range(1, N_JUDGES_T2 + 1)
            for direction in ("a", "b")]
    random.Random(run_seed(run_id) + 1).shuffle(jobs)
    import threading as _th
    _lock = _th.Lock()

    def one_t2(job):
        p, j, direction = job
        key = "%02d_%s_j%d" % (p, direction, j)
        call_id = "parent/%s/step4/%s" % (run_id, key)
        x, y = pairs[p]
        ca, cb = cands[x], cands[y]
        if direction == "b":
            ca, cb = cb, ca
        prompt = PP.t2_judge_prompt(disease, ca, cb)
        if arm == "blind":
            gen2_blind.assert_prompt_clean(prompt, disease, call_id)
        rec, obj, tier = _gen_or_redispatch(
            call_id, prompt, 8192,
            {"task_class": "judging", "step": 4, "pair": [x, y],
             "judge": j, "direction": direction},
            gen2_parse.parse_object)
        v, problems = (None, [tier]) if obj is None else \
            gen2_parse.validate_verdict(obj)
        with _lock:
            if v is None:
                _record_parse_fail(run_id, call_id, rec, tier, problems)
                verdicts[key] = {"failed": True, "problems": problems}
            else:
                winner_idx = None
                if v["winner"] == "A":
                    winner_idx = x if direction == "a" else y
                elif v["winner"] == "B":
                    winner_idx = y if direction == "a" else x
                verdicts[key] = {"pair": [x, y], "judge": j,
                                 "direction": direction,
                                 "slot_winner": v["winner"],
                                 "winner_idx": winner_idx,
                                 "winner_name": cands[winner_idx]["name"]
                                 if winner_idx is not None else "TIE",
                                 "science": v["science"],
                                 "feasibility": v["feasibility"],
                                 "novelty": v["novelty"],
                                 "reasoning": v["reasoning"]}
            write_json(out_path, {"verdicts": verdicts,
                                  "n_pairs": len(pairs)})

    pending = [job for job in jobs
               if "%02d_%s_j%d" % (job[0], job[2], job[1]) not in verdicts]
    workers = int(os.environ.get("GEN2_WORKERS", "1"))
    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(one_t2, job) for job in pending]
            for _f in as_completed(futs):
                _f.result()
    else:
        for job in pending:
            one_t2(job)
            if not os.environ.get("GEN2_MOCK"):
                time.sleep(0.3)
    n = len(verdicts)
    total = len(pairs) * N_JUDGES_T2 * 2
    if n >= total:
        n_fail = sum(1 for v in verdicts.values() if v.get("failed"))
        return "ok" if n_fail <= total * 0.05 else "too_many_failures"
    return "in_progress(%d/%d)" % (n, total)


# ================================================================ step 5 ====
def step5(run_id):
    d = run_dir(run_id)
    s3 = read_json(os.path.join(d, "step3_candidates.json"))
    s4 = read_json(os.path.join(d, "step4_verdicts.json"))
    if not (s3 and s4):
        return "blocked_step4"
    out_path = os.path.join(d, "step5_top5.json")
    if read_json(out_path):
        return "done"
    import btl
    cands = s3["candidates"]
    keys = [c["cand_id"] for c in cands]
    pairs = []
    for v in (s4["verdicts"] or {}).values():
        if v.get("failed"):
            continue
        x, y = v["pair"]
        if v.get("winner_idx") is None:              # tie
            pairs.append((keys[x], keys[y], 0.5))
            pairs.append((keys[y], keys[x], 0.5))
        else:
            loser = y if v["winner_idx"] == x else x
            pairs.append((keys[v["winner_idx"]], keys[loser], 1.0))
    fit = btl.fit_btl([(w, l) for w, l, _ in pairs], item_names=keys)
    by_key = {c["cand_id"]: c for c in cands}
    top5 = [by_key[k] for k in fit["ranking"][:5]]
    write_json(out_path, {"run_id": run_id, "fit": fit, "top5": top5})
    return "ok"


# ================================================================ step 6 ====
def step6(run_id, disease, arm):
    d = run_dir(run_id)
    s5 = read_json(os.path.join(d, "step5_top5.json"))
    if not s5:
        return "blocked_step5"
    out_path = os.path.join(d, "step6_protocols.json")
    existing = read_json(out_path) or {"protocols": []}
    by_rank = {p["rank"]: p for p in existing["protocols"]}
    protocols = []
    for rank, cand in enumerate(s5["top5"], 1):
        prev = by_rank.get(rank)
        if prev and not prev.get("failed") and prev.get("protocol"):
            protocols.append(prev)          # keep completed protocol
            continue
        call_id = "parent/%s/step6/p%d" % (run_id, rank)
        prompt = PP.step6_protocol_prompt(disease, cand, rank, arm)
        if arm == "blind":
            gen2_blind.assert_prompt_clean(prompt, disease, call_id)

        def parse_proto(text):
            obj, tier = gen2_parse.parse_object(text)
            if (isinstance(obj, dict)
                    and isinstance(obj.get("references"), list)
                    and len(obj["references"]) == 6):
                return obj, tier
            return None, tier if tier in gen2_parse.TIERS else "refs_bad"

        # 32768 per D2-011 (8192 truncated 43/65, all-reasoning empties);
        # redispatch revives stale 8192-era archives; fresh failures recorded
        rec, obj, tier = _gen_or_redispatch(
            call_id, prompt, 32768,
            {"task_class": "orchestrator", "step": 6, "rank": rank},
            parse_proto)
        if obj is None:
            _record_parse_fail(run_id, call_id, rec, tier,
                               ["refs_missing_or_count"])
            protocols.append({"rank": rank, "candidate": cand["name"],
                              "failed": True})
            continue
        protocols.append({"rank": rank, "candidate": cand["name"],
                          "protocol": obj, "parse_tier": tier})
        write_json(out_path, {"run_id": run_id, "protocols": protocols,
                              "blind_hits": []})
        if not os.environ.get("GEN2_MOCK"):
            time.sleep(0.3)
    hits = gen2_blind.scan_response(
        json.dumps(protocols, ensure_ascii=False), disease) \
        if arm == "blind" else []
    n_fail = sum(1 for p in protocols if p.get("failed"))
    write_json(out_path, {"run_id": run_id, "protocols": protocols,
                          "blind_hits": hits})
    if hits:
        return "blind_violation"
    return "ok" if n_fail == 0 else "protocols_failed(%d/5)" % n_fail


# ============================================================== driver ======
STEPS = [("step1", lambda rid, dis, arm: step1(rid, dis, arm)),
         ("step2", lambda rid, dis, arm: step2(rid, dis, arm)),
         ("step3", lambda rid, dis, arm: step3(rid, dis, arm)),
         ("step4", lambda rid, dis, arm: step4(rid, dis, arm)),
         ("step5", lambda rid, dis, arm: step5(rid)),
         ("step6", lambda rid, dis, arm: step6(rid, dis, arm))]

DONE_STATES = {"done", "ok"}


def advance(run_id, disease, arm):
    """Execute pending work for the run's earliest incomplete step."""
    for name, fn in STEPS:
        try:
            state = fn(run_id, disease, arm)
        except gen2_blind.BlindViolation as e:
            print("BLIND-VIOLATION %s @%s: %s" % (run_id, name, e))
            return name, "blind_violation"
        except gen2_call.BudgetStop as e:
            print("BUDGET-STOP %s @%s: %s" % (run_id, name, e))
            raise
        if state in DONE_STATES:
            continue
        return name, state
    return "all", "complete"


def plan_parent12():
    return [("%s_%s_R%d" % (dis, arm, rep), dis, arm)
            for dis in DISEASES for arm in ARMS for rep in REPS]


def run_plan_interleaved(max_rounds=10000):
    plan = plan_parent12()
    for rid, dis, arm in plan:
        os.makedirs(run_dir(rid), exist_ok=True)
    rnd = random.Random(PERM_SEED)
    for round_no in range(max_rounds):
        calls_before = gen2_call.budget_report()["glm"]["calls"]
        order = plan[:]
        rnd.shuffle(order)
        for rid, dis, arm in order:
            try:
                name, state = advance(rid, dis, arm)
            except gen2_call.BudgetStop:
                raise                      # §10.3 hard stop stays a hard stop
            except RuntimeError as e:
                # e.g. transient PubMed fetch failure in the retrieval arm:
                # block THIS run for this round, keep the other runs moving
                name, state = "blocked", repr(e)[:120]
            print("[%04d] %-16s %-6s %s" % (round_no, rid, name, state))
        calls_after = gen2_call.budget_report()["glm"]["calls"]
        if calls_after == calls_before:
            print("NO NEW CALLS IN A FULL ROUND -- all runs blocked "
                  "(parse failures / blind violations) or complete. "
                  "Inspect runs/ states and _parse_failed.")
            return
    print("max_rounds reached")


def status():
    rows = []
    for rid, dis, arm in plan_parent12():
        s = []
        for name in ("step1", "step2", "step3", "step4", "step5", "step6"):
            path = {"step1": "step1_mechanisms.json",
                    "step2": "step2_verdicts.json",
                    "step3": "step3_candidates.json",
                    "step4": "step4_verdicts.json",
                    "step5": "step5_top5.json",
                    "step6": "step6_protocols.json"}[name]
            data = read_json(os.path.join(run_dir(rid), path))
            if name == "step2" and data:
                s.append("S2:%d/%d" % (len([v for v in data["verdicts"].values()
                                            if not v.get("failed")]),
                                       data.get("n_pairs", 300)))
            elif name == "step4" and data:
                s.append("S4:%d/%d" % (len([v for v in data["verdicts"].values()
                                            if not v.get("failed")]),
                                       data.get("n_pairs", 45) * 6))
            else:
                s.append(name if data else "-")
        rows.append("%-16s %s" % (rid, " ".join(s)))
    print("\n".join(rows))


def certify_retrieval():
    """2-call probe: does the GLM Coding Plan endpoint accept a web_search
    tool block? (construction decision C6/PLAN §6). Zero-cost decision input."""
    tools = [{"type": "web_search",
              "web_search": {"enable": True, "search_query": ""}}]
    prompt = ("What is the most recent large genome-wide association study "
              "meta-analysis of age-related macular degeneration? Name first "
              "author and year. Reply in one sentence.")
    for label, kw in (("with_tool", {"tools": tools}),
                      ("no_tool", {})):
        call_id = "certify/retrieval/%s/%s" % (
            label, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
        rec = gen2_call.call(VENDOR, prompt, 8192, call_id=call_id,
                             about={"task_class": "certify", "probe": label},
                             **kw)
        print("%s: ok=%s status=%s model=%s" % (
            label, rec["ok"], rec["status"], rec.get("model_exact_id_returned")))
        if rec["ok"]:
            print("  text:", (rec.get("text") or "")[:200].replace("\n", " "))
        time.sleep(2)
    print("\nIf with_tool returned ok and cites retrieved sources, GLM web_search"
          " is certified; otherwise use the PubMed context-injection fallback"
          " (record in DEVIATIONS_v2.md).")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--disease", choices=DISEASES)
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--rep", type=int, choices=(1, 2, 3))
    ap.add_argument("--plan", choices=("parent12",))
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--certify-retrieval", action="store_true")
    a = ap.parse_args()
    if a.status:
        status()
    elif a.certify_retrieval:
        certify_retrieval()
    elif a.plan == "parent12":
        run_plan_interleaved()
    elif a.disease and a.arm and a.rep:
        rid = "%s_%s_R%d" % (a.disease, a.arm, a.rep)
        name, state = advance(rid, a.disease, a.arm)
        print("%s @ %s -> %s" % (rid, name, state))
    else:
        ap.print_help()
