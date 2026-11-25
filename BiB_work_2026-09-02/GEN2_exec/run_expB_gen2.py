#!/usr/bin/env python3
"""
run_expB_gen2.py -- Experiment B driver (gen-2, prereg §6).

Gen-1 frozen design retained: 14 domains x 3 arms x 5 hypotheses x 6 slots =
1,260 slots; stage-1 elicited once (14 calls, shared across arms) + 210
stage-2 calls = 224 calls on glm-5.3. Stimulus set = gen-1 freeze verbatim
(expB_prompts.json, sha256 45f25128... verified against deposit MANIFEST).

Changes per prereg §6 (the prereg supersedes gen-1's prompt on exactly this):
  - stage-1 prompts append the §5.6 confidence line VERBATIM; the output
    object spec gains "confidence": <integer 0-100> (construction decision C2).
  - stage-2 arm templates unchanged verbatim.
Interleaving (§10.1): the 210 stage-2 (arm x domain x hypothesis) jobs run in
a seeded shuffle (PERM_SEED 20260101) -- no arm runs as a contiguous block.

Output tree is byte-compatible with the frozen gen-1 scorer run_exp_b.py
(stage-1 files gain a "confidence" key -- the scorer ignores unknown keys).
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

import gen2_call
import gen2_parse

HERE = os.path.dirname(os.path.abspath(__file__))
PERM_SEED = 20260101
VENDOR = "glm"
FROZEN_PROMPTS_SHA = ("45f2512823774024ab68a49db715902b55c30cb2"
                      "09889fd3e86025991d3e34a0")
CONFIDENCE_LINE = ("State your confidence that this candidate will rank in "
                   "the top five, as an integer between 0 and 100.")
ARMS = ("as_discovered", "gated", "abstain_probe")
DIGITS = re.compile(r"^\d+$")
PMID_IN_TEXT = re.compile(r"\d{4,9}")


def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if sha != FROZEN_PROMPTS_SHA:
        sys.exit("expB_prompts.json sha256 %s != frozen %s -- do not run"
                 % (sha[:16], FROZEN_PROMPTS_SHA[:16]))
    return spec


def stage1_prompt(frozen_stage1_prompt):
    """Frozen per-domain stage-1 prompt + §5.6 line + confidence field.

    Two surgical edits only (prereg §6 supersedes the gen-1 freeze exactly
    here); everything else byte-identical to the frozen stimulus:
      1. output object spec gains "confidence": <integer 0-100>
      2. the §5.6 confidence line inserted verbatim before the closing
         output instruction
    """
    t = frozen_stage1_prompt
    old_obj = ('{"id": 1..5, "mechanism": "<one sentence naming the entities '
               'and the direction>"}')
    new_obj = ('{"id": 1..5, "mechanism": "<one sentence naming the entities '
               'and the direction>", "confidence": <integer 0-100>}')
    if old_obj not in t:
        sys.exit("frozen stage-1 prompt shape changed -- refusing to edit")
    t = t.replace(old_obj, new_obj)
    closer = "- Output the JSON array and nothing else."
    if closer not in t:
        sys.exit("frozen stage-1 closer missing -- refusing to edit")
    t = t.replace(closer, "- " + CONFIDENCE_LINE + "\n" + closer)
    return t


def validate_stage1(arr, n_expected):
    out, problems, anomalies = [], [], []
    if not isinstance(arr, list) or len(arr) != n_expected:
        return None, ["count_%s" % (len(arr) if isinstance(arr, list)
                                    else "not_a_list")], anomalies
    for k, o in enumerate(arr):
        if not isinstance(o, dict):
            problems.append("item_%d_not_object" % k)
            continue
        try:
            i = int(o["id"])
        except Exception:                                          # noqa: BLE001
            problems.append("item_%d_bad_id" % k)
            continue
        mech = o.get("mechanism")
        if not isinstance(mech, str) or not mech.strip():
            problems.append("item_%d_bad_mechanism" % k)
            continue
        try:
            conf = int(o.get("confidence"))
        except Exception:                                          # noqa: BLE001
            conf = None
            anomalies.append("item_%d_bad_confidence" % k)
        out.append({"id": i, "mechanism": mech.strip(), "confidence": conf})
    ids = sorted(x["id"] for x in out)
    if ids != list(range(1, n_expected + 1)):
        problems.append("ids_%s" % ids)
    return (out if not problems else None), problems, anomalies


def validate_stage2(arr, n_expected):
    out, problems, fmt = [], [], []
    if not isinstance(arr, list) or len(arr) != n_expected:
        return None, ["count_%s" % (len(arr) if isinstance(arr, list)
                                    else "not_a_list")], fmt
    for k, o in enumerate(arr):
        if not isinstance(o, dict):
            problems.append("item_%d_not_object" % k)
            continue
        try:
            s = int(o["slot"])
        except Exception:                                          # noqa: BLE001
            problems.append("item_%d_bad_slot" % k)
            continue
        pmid = str(o.get("pmid", "")).strip()
        claim = o.get("claim")
        if not isinstance(claim, str):
            claim = "" if claim is None else str(claim)
        if not (DIGITS.match(pmid) or pmid.upper() == "NO_CITATION"):
            cand = PMID_IN_TEXT.search(pmid)
            fmt.append({"slot": s, "pmid_verbatim": pmid,
                        "normalised_candidate": cand.group(0) if cand else None})
        out.append({"slot": s, "pmid": pmid, "claim": claim.strip(),
                    "_SYNTHETIC": "SYNTHETIC — hallucination benchmark "
                                  "stimuli, NOT citable references."})
    slots = sorted(x["slot"] for x in out)
    if slots != list(range(1, n_expected + 1)):
        problems.append("slots_%s" % slots)
    return (out if not problems else None), problems, fmt


def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=(1, 2), required=True)
    ap.add_argument("--arm", default=None, help="stage 2: one arm or 'all'")
    ap.add_argument("--out", default=os.path.join(
        os.path.join(HERE, "data_mock")
        if os.environ.get("GEN2_MOCK") else HERE, "runs", "expB"))
    ap.add_argument("--max-tokens", type=int, default=32768,
                    help="stage-2 cap; 32768 per D2-006 (8192 still "
                         "truncated on genuine PMID-recall reasoning)")
    a = ap.parse_args()

    spec = load_spec(os.path.join(HERE, "expB_prompts.json"))
    root = a.out
    shared = os.path.join(root, "_shared_stage1")
    tiers, anomalies, fmt_all = {}, [], []

    if a.stage == 1:
        for d in spec["domains"]:
            did = d["domain_id"]
            dst = os.path.join(shared, "%s_stage1.json" % did)
            if os.path.exists(dst):
                print("skip  %s" % did)
                continue
            prompt = stage1_prompt(d["stage1_prompt"])
            rec = gen2_call.call(VENDOR, prompt, a.max_tokens,
                                 call_id="expB/glm/stage1/%s" % did,
                                 about={"task_class": "judging",
                                        "experiment": "B", "stage": 1})
            obj, tier = gen2_parse.parse_json(rec.get("text"))
            arr = obj if isinstance(obj, list) else None
            tiers[tier] = tiers.get(tier, 0) + 1
            parsed, problems, anom = (None, [tier or "no_list"], []) \
                if arr is None else validate_stage1(
                    arr, spec["hypotheses_per_domain"])
            anomalies += anom
            if parsed is None:
                wjson(os.path.join(root, "_parse_failed",
                                   "stage1_%s.json" % did),
                      {"tier": tier, "problems": problems,
                       "text": rec.get("text")})
                print("FAIL  %s  %s" % (did, problems))
                continue
            wjson(dst, parsed)
            print("ok    %s  tier=%s conf=%s" %
                  (did, tier, [x["confidence"] for x in parsed]))
            if not os.environ.get("GEN2_MOCK"):
                time.sleep(0.3)
        # fan out to the three arms (scorer reads per-arm)
        for arm in ARMS:
            for d in spec["domains"]:
                src = os.path.join(shared, "%s_stage1.json" % d["domain_id"])
                if os.path.exists(src):
                    wjson(os.path.join(root, arm,
                                       "%s_stage1.json" % d["domain_id"]),
                          json.load(open(src, encoding="utf-8")))
        print("stage 1 complete")

    else:
        if not a.arm:
            sys.exit("--arm required (or 'all')")
        arms = list(ARMS) if a.arm == "all" else [a.arm]
        jobs = [(arm, d["domain_id"], h)
                for arm in arms
                for d in spec["domains"]
                for h in range(1, spec["hypotheses_per_domain"] + 1)]
        random.Random(PERM_SEED).shuffle(jobs)

        import threading as _th
        _rlock = _th.Lock()

        def one_slot(job):
            arm, did, h = job
            dst = os.path.join(root, arm, "%s_h%d.json" % (did, h))
            if os.path.exists(dst):
                return
            s1 = os.path.join(root, arm, "%s_stage1.json" % did)
            if not os.path.exists(s1):
                print("SKIP  %s/%s h%d: no stage-1" % (arm, did, h))
                return
            mechs = {int(m["id"]): m["mechanism"]
                     for m in json.load(open(s1, encoding="utf-8"))}
            d = next(x for x in spec["domains"] if x["domain_id"] == did)
            prompt = spec["stage2_templates"][arm].format(
                disease=d["domain"], mechanism=mechs[h])
            call_id = "expB/glm/stage2/%s/%s/h%d" % (arm, did, h)
            rec = gen2_call.call(VENDOR, prompt, a.max_tokens, call_id=call_id,
                                 about={"task_class": "judging",
                                        "experiment": "B", "stage": 2,
                                        "arm": arm})
            obj, tier = gen2_parse.parse_json(rec.get("text"))
            arr = obj if isinstance(obj, list) else None
            parsed, problems, fmt = (None, [tier or "no_list"], []) \
                if arr is None else validate_stage2(
                    arr, spec["slots_per_hypothesis"])
            with _rlock:
                tiers[tier] = tiers.get(tier, 0) + 1
                fmt_all.extend(fmt)
                if parsed is None:
                    wjson(os.path.join(root, "_parse_failed",
                                       "%s_%s_h%d.json" % (arm, did, h)),
                          {"tier": tier, "problems": problems,
                           "text": rec.get("text")})
                    print("FAIL  %s/%s h%d  %s" % (arm, did, h, problems))
                    return
                wjson(dst, parsed)
                n_ab = sum(1 for x in parsed
                           if x["pmid"].upper() == "NO_CITATION")
                print("ok    %-14s %-4s h%-2d tier=%-12s abstain=%d"
                      % (arm, did, h, tier, n_ab))

        workers = int(os.environ.get("GEN2_WORKERS", "1"))
        if workers > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(one_slot, j) for j in jobs]
                for _f in as_completed(futs):
                    _f.result()
        else:
            for j in jobs:
                one_slot(j)
                if not os.environ.get("GEN2_MOCK"):
                    time.sleep(0.3)
        print("stage 2 pass complete (re-run to resume failed/missing)")


if __name__ == "__main__":
    main()
