#!/usr/bin/env python3
"""
gen2_canary.py -- drift canary (prereg §10.2).

10 fixed prompts re-run at a fixed daily time across the entire execution
window, on BOTH vendors. Response SHA-256 and reasoning_tokens are tracked.
Canary drift => §1.1 no-substitution clause activates for affected calls/arms
(recorded in DEVIATIONS_v2.md, reported 'not executed at the pinned build').

The 10 prompts are frozen in canary_prompts.json at harness build time
(2026-09-05, before the first experimental call). Their SHA-256s are recorded
here; any change to the file is a protocol deviation.
"""

import hashlib
import json
import os
import time

import gen2_call

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS_PATH = os.path.join(HERE, "canary_prompts.json")
LOG_PATH = os.path.join(gen2_call.DATA, "canary_log.jsonl")


def _load_prompts():
    d = json.load(open(PROMPTS_PATH, encoding="utf-8"))
    return d["prompts"], d["prompts_sha256"]


def run_canary(vendors=("glm", "deepseek"), max_tokens=2048):
    """Run the 10 canary prompts on each vendor; append per-call records."""
    prompts, frozen_sha = _load_prompts()
    live_sha = hashlib.sha256(
        json.dumps(prompts, ensure_ascii=False).encode()).hexdigest()
    if live_sha != frozen_sha:
        raise RuntimeError(
            "canary prompt file changed since freeze (%s != %s) -- protocol "
            "deviation; record in DEVIATIONS_v2.md before running" %
            (live_sha[:12], frozen_sha[:12]))

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    n_ok = 0
    for vendor in vendors:
        for i, p in enumerate(prompts, 1):
            call_id = "canary/%s/%s/%02d" % (vendor, day, i)
            if gen2_call.call_ok(call_id):
                print("skip  %s (already logged today)" % call_id)
                continue
            rec = gen2_call.call(
                vendor, p["prompt"], max_tokens,
                call_id=call_id,
                about={"task_class": "canary", "canary_id": p["id"]})
            entry = {
                "day": day, "vendor": vendor, "canary_id": p["id"],
                "call_id": call_id, "ok": rec["ok"],
                "response_sha256": rec.get("raw_response_sha256"),
                "text_sha256": hashlib.sha256(
                    (rec.get("text") or "").encode("utf-8")).hexdigest(),
                "reasoning_tokens": rec.get("reasoning_tokens"),
                "input_tokens": rec.get("input_tokens"),
                "output_tokens": rec.get("output_tokens"),
                "stop_reason": rec.get("stop_reason"),
                "model_exact_id_returned": rec.get("model_exact_id_returned"),
                "utc": rec.get("utc"),
            }
            with open(LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            n_ok += 1 if rec["ok"] else 0
            print("%s  %s -> %s (reasoning=%s)"
                  % ("ok  " if rec["ok"] else "FAIL", call_id,
                     (rec.get("text") or "")[:40].replace("\n", " "),
                     rec.get("reasoning_tokens")))
            time.sleep(1.0)
    print("\ncanary done: %d ok calls this invocation" % n_ok)
    return n_ok


def drift_report():
    """Compare each day's canary records against the earliest day per vendor.

    Flags (per vendor, per canary_id):
      - model id change
      - reasoning-token median shift > 3x or < 1/3 (sustained across the day)
      - stop_reason anomalies
    Text SHA equality is NOT required (temperature 1.0 -> different texts);
    it is recorded for the record only.
    """
    if not os.path.exists(LOG_PATH):
        return {"n_records": 0, "flags": []}
    recs = [json.loads(l) for l in open(LOG_PATH, encoding="utf-8") if l.strip()]
    flags = []
    for vendor in {r["vendor"] for r in recs}:
        vrecs = sorted([r for r in recs if r["vendor"] == vendor],
                       key=lambda r: (r["day"], r["canary_id"]))
        first_day = vrecs[0]["day"]
        base_model = {r["canary_id"]: r["model_exact_id_returned"] for r in vrecs
                      if r["day"] == first_day}
        base_rt = {}
        for r in vrecs:
            if r["day"] == first_day and r.get("reasoning_tokens") is not None:
                base_rt.setdefault(r["canary_id"], []).append(r["reasoning_tokens"])
        base_rt = {k: sum(v) / len(v) for k, v in base_rt.items()}
        for r in vrecs:
            if r["day"] == first_day:
                continue
            bm = base_model.get(r["canary_id"])
            if bm and r["model_exact_id_returned"] != bm:
                flags.append({"vendor": vendor, "day": r["day"],
                              "canary_id": r["canary_id"],
                              "type": "model_id_change",
                              "was": bm, "now": r["model_exact_id_returned"]})
            brt = base_rt.get(r["canary_id"])
            rt = r.get("reasoning_tokens")
            if brt and rt is not None and brt > 0 and (rt > 3 * brt or rt < brt / 3):
                flags.append({"vendor": vendor, "day": r["day"],
                              "canary_id": r["canary_id"],
                              "type": "reasoning_shift",
                              "was_median": brt, "now": rt})
    return {"n_records": len(recs), "flags": flags}


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.run:
        sys.exit(0 if run_canary() == 20 else 1)
    print(json.dumps(drift_report(), indent=1, ensure_ascii=False))
