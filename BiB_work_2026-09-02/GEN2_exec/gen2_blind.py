#!/usr/bin/env python3
"""
gen2_blind.py -- forbidden-token scanner (prereg §2.1).

Blind protocol: disease-specific forbidden-token lists; pre-dispatch scans at
three points: (1) prompts, (2) parsed JSON responses, (3) grounded titles or
abstracts. Any hit voids the dispatch and forces a redraft of the PROMPT
(model responses are never edited -- a response hit is recorded as a blind
violation and the affected item is reported/repaired per protocol).

Lists extracted verbatim from the gen-1 deposit (audit_data):
  dAMD 11-word list  -> sdl_main_state.json (run 2026-05-28)
  ALS v2 list        -> stage2_ALS/run1/step1_litreview/final_30_mechanisms_ALS.json
                        (11 drug words + 13 dAMD Stage-1 leak words)
"""

BLIND_LISTS = {
    "dAMD": {
        "tokens": [
            "ripasudil", "kl001", "y-27632", "y27632", "fasudil",
            "robin paper", "ghareeb", "nature 2026", "rock inhibitor",
            "10.1038/s41586-026-10652-y", "42156546",
        ],
    },
    "ALS": {
        "tokens": [
            # 11 ALS forbidden-drug words
            "Riluzole", "Edaravone", "Radicava", "Tofersen", "Qalsody",
            "AMX0035", "Relyvrio", "sodium phenylbutyrate", "taurursodiol",
            "Methylcobalamin", "Rozebalamin",
            # 13 dAMD Stage-1 leak words (cross-stage defense)
            "MERTK", "MerTK-kd", "MFG-E8", "GAS6", "ITGB5", "ITGAV",
            "rProS1", "ProS1", "Y-27632", "ROCK inhibitor", "ROCK1",
            "ROCK2", "Ripasudil",
        ],
    },
}


def scan(text, disease):
    """Case-insensitive substring scan. Returns list of hit tokens."""
    if text is None:
        return []
    hay = str(text).lower()
    hits = []
    for tok in BLIND_LISTS[disease]["tokens"]:
        if tok.lower() in hay:
            hits.append(tok)
    return hits


def scan_prompt(text, disease):
    """Point (1): prompts. Hits void the dispatch BEFORE any call is made."""
    return scan(text, disease)


def scan_response(text, disease):
    """Point (2): parsed JSON responses (serialised). Hits are blind violations."""
    return scan(text, disease)


def scan_grounded(text, disease):
    """Point (3): grounded titles/abstracts entering any prompt."""
    return scan(text, disease)


def assert_prompt_clean(text, disease, call_id):
    """Hard gate for drivers: raise before dispatch if the prompt leaks."""
    hits = scan_prompt(text, disease)
    if hits:
        raise BlindViolation(
            "PROMPT BLIND VIOLATION (%s) in %s: hits=%s -- redraft the prompt"
            % (disease, call_id, hits))
    return True


class BlindViolation(RuntimeError):
    pass


if __name__ == "__main__":
    import sys
    tests = [
        # "ROCK signaling" alone is NOT in the list; only the exact token
        # "rock inhibitor" is forbidden -> no hit expected
        ("A mechanism involving ROCK signaling cascade", "dAMD", []),
        ("ripasudil is a drug", "dAMD", ["ripasudil"]),
        ("Riluzole blocks glutamate", "ALS", ["Riluzole"]),
        ("MERTK shedding in AMD", "ALS", ["MERTK"]),
        ("complement C3 activation", "dAMD", []),
    ]
    ok = True
    for text, dis, expect in tests:
        got = scan(text, dis)
        # expected: non-empty iff expect non-empty (approximate fixture)
        status = "PASS" if bool(got) == bool(expect) else "FAIL"
        if status == "FAIL":
            ok = False
        print("%s  %-45r %-5s hits=%s" % (status, text[:45], dis, got))
    print("\nall pass" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)
