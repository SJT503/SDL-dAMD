#!/usr/bin/env python3
"""
gen2_parse.py -- three-tier JSON parsing of model output (gen-1 elicit layer
design, retained): strict -> fenced -> bracket_scan. The tier used is recorded
per call. A response no tier recovers is a parse failure: the raw text is kept
under the run's _parse_failed/ directory and NO canonical file is written.

Also: single-JSON-object parsing for judge verdicts / dossiers (first balanced
{...} span when the top-level parse fails).
"""

import json
import re

FENCE = re.compile(r"^\s*```(?:json|JSON)?\s*(.*?)\s*```\s*$", re.S)
TIERS = ("strict", "fenced", "bracket_scan")


def first_balanced(t, open_ch="[", close_ch="]"):
    start = t.find(open_ch)
    while start != -1:
        depth, i, instr, esc = 0, start, False, False
        while i < len(t):
            ch = t[i]
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    instr = False
            elif ch == '"':
                instr = True
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return t[start:i + 1]
            i += 1
        start = t.find(open_ch, start + 1)
    return None


def parse_json(text):
    """Return (obj, tier) or (None, reason). Accepts any JSON value at top level."""
    t = (text or "").strip()
    if not t:
        return None, "empty_response"
    try:
        return json.loads(t), "strict"
    except Exception:                                            # noqa: BLE001
        pass
    m = FENCE.match(t)
    if m:
        try:
            return json.loads(m.group(1)), "fenced"
        except Exception:                                        # noqa: BLE001
            pass
    # bracket_scan: try the bracket type that appears FIRST in the text --
    # an unclosed-fence JSON OBJECT containing arrays must be grabbed as an
    # object, not as its first internal array (observed 2026-09-06, step-3
    # dossier c09)
    order = sorted((("[", "]"), ("{", "}")), key=lambda oc: t.find(oc[0]))
    for o, c in [oc for oc in order if t.find(oc[0]) >= 0]:
        seg = first_balanced(t, o, c)
        if seg:
            try:
                return json.loads(seg), "bracket_scan"
            except Exception:                                    # noqa: BLE001
                pass
    return None, "unparseable"


def parse_array(text, n_expected):
    """(list, tier) if parseable AND a list; else (None, reason)."""
    obj, how = parse_json(text)
    if obj is None:
        return None, how
    if not isinstance(obj, list):
        return None, "not_a_list"
    if len(obj) != n_expected:
        return obj, "count_%d_expected_%d" % (len(obj), n_expected)
    return obj, how if how in ("strict", "fenced", "bracket_scan") else "strict"


def parse_object(text):
    """(dict, tier) or (None, reason)."""
    obj, how = parse_json(text)
    if obj is None:
        return None, how
    if not isinstance(obj, dict):
        return None, "not_an_object"
    return obj, how if how in ("strict", "fenced", "bracket_scan") else "strict"


VALID_AB = {"A", "B"}
VALID_ABT = {"A", "B", "tie"}


def validate_verdict(obj):
    """Judge verdict schema check. Returns (clean_dict, problems).

    winner "tie" is ACCEPTED (honest model behaviour; BTL credits 0.5 each).
    Only malformed values (empty, "Option A", numeric) are problems.
    """
    problems = []
    v = {k: str(obj.get(k, "")).strip() for k in
         ("winner", "science", "feasibility", "novelty")}
    if v["winner"] not in VALID_ABT:
        problems.append("bad_%s=%r" % ("winner", v["winner"]))
    for k in ("science", "feasibility", "novelty"):
        if v[k] not in VALID_ABT:
            problems.append("bad_%s=%r" % (k, v[k]))
    reasoning = obj.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        problems.append("bad_reasoning")
    out = {"winner": v["winner"], "science": v["science"],
           "feasibility": v["feasibility"], "novelty": v["novelty"],
           "reasoning": (reasoning or "").strip()}
    return (out if not problems else None), problems
