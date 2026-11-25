#!/usr/bin/env python3
"""Rebuild runs/expB canonical files from the raw-call archives (2026-09-05).

After an accidental `rm -rf runs` (D2-008), every completed Experiment-B slot
is recoverable: data/raw/ holds each call_id's LAST response archive (same-name
overwrite on re-dispatch -- which is exactly the newest cap/attempt). This
script re-parses every archive and rewrites the canonical slot files; slots
whose latest archive is truncated/unparseable are simply not written, so the
driver's resume logic re-dispatches only those.

Zero model calls. Idempotent.
"""
import json
import os
import re

import gen2_parse
import run_expB_gen2 as RB

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
ROOT = os.path.join(HERE, "runs", "expB")

spec = RB.load_spec(os.path.join(HERE, "expB_prompts.json"))
n_domains = len(spec["domains"])
hyp = spec["hypotheses_per_domain"]

n_s1 = n_s2 = 0
for did in [d["domain_id"] for d in spec["domains"]]:
    # ---- stage 1 ----
    p = os.path.join(RAW, "expB__glm__stage1__%s.json" % did)
    if os.path.exists(p):
        msg = (json.load(open(p, encoding="utf-8"))
               .get("choices", [{}])[0].get("message", {}))
        obj, tier = gen2_parse.parse_json(msg.get("content"))
        arr = obj if isinstance(obj, list) else None
        parsed, problems, anom = (None, [tier], []) if arr is None \
            else RB.validate_stage1(arr, hyp)
        if parsed is not None:
            dst = os.path.join(ROOT, "_shared_stage1", "%s_stage1.json" % did)
            RB.wjson(dst, parsed)
            for arm in RB.ARMS:
                RB.wjson(os.path.join(ROOT, arm, "%s_stage1.json" % did),
                         parsed)
            n_s1 += 1
    # ---- stage 2 ----
    for arm in RB.ARMS:
        for h in range(1, hyp + 1):
            p = os.path.join(RAW, "expB__glm__stage2__%s__%s__h%d.json"
                             % (arm, did, h))
            if not os.path.exists(p):
                continue
            msg = (json.load(open(p, encoding="utf-8"))
                   .get("choices", [{}])[0].get("message", {}))
            obj, tier = gen2_parse.parse_json(msg.get("content"))
            arr = obj if isinstance(obj, list) else None
            parsed, problems, fmt = (None, [tier], []) if arr is None \
                else RB.validate_stage2(arr, spec["slots_per_hypothesis"])
            if parsed is not None:
                RB.wjson(os.path.join(ROOT, arm, "%s_h%d.json" % (did, h)),
                         parsed)
                n_s2 += 1

print("rebuilt: %d/%d stage-1 files, %d stage-2 slot files" %
      (n_s1, n_domains, n_s2))
for arm in RB.ARMS:
    n = len([f for f in os.listdir(os.path.join(ROOT, arm))
             if re.match(r".*_h\d+\.json$", f)])
    print("  %-14s %d/70 h-files" % (arm, n))
