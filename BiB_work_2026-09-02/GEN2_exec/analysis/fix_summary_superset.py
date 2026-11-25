from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
MS_PATH = BASE / "MANUSCRIPT_GEN2_v1.0.md"
ms = MS_PATH.read_text(encoding="utf-8")

old_s = "combine hypothesis generation, pairwise tournaments, and literature grounding to propose therapeutic targets, yet whether test-time reasoning ensures pipeline trustworthiness remains unresolved."
new_s = "combine hypothesis generation, pairwise tournaments, and literature grounding for target discovery, yet whether test-time reasoning ensures pipeline trustworthiness remains unresolved."
assert old_s in ms
ms = ms.replace(old_s, new_s, 1)

old_s2 = "with a 2.5-fold natural language inference (NLI) contradiction surge."
new_s2 = "with a 2.5-fold NLI contradiction surge."
assert old_s2 in ms
ms = ms.replace(old_s2, new_s2, 1)

MS_PATH.write_text(ms, encoding="utf-8")
