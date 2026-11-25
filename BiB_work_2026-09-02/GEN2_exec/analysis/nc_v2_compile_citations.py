from gate import gate, canary_gate, retry_limit
import json
import pathlib
import re

gate(__file__)

BASE = pathlib.Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
ANAL = BASE / "GEN2_exec" / "analysis"
TPL_EN = ANAL / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0_template.md"
TPL_ZH = ANAL / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0_CN_template.md"
REFS_JSON = ANAL / "nc_v2_references_master.json"
OUT_EN_ROOT = BASE / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0.md"
OUT_EN_PKG = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.3_Aligned" / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_submission_EN.md"
OUT_ZH_ROOT = BASE / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0_CN_review.md"
OUT_ZH_PKG = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.3_Aligned" / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_CN_review.md"
MAP_OUT = ANAL / "nc_v2_citation_order_map.json"


def mini_task():
    assert TPL_EN.exists() and REFS_JSON.exists()
    return True


canary_gate(lambda: mini_task(), "Verify template MD and master 74-ref JSON exist")


def compress_nums(nums):
    nums = sorted(set(nums))
    if not nums:
        return ""
    spans = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
        else:
            spans.append((start, prev))
            start = prev = n
    spans.append((start, prev))
    parts = []
    for a, b in spans:
        if a == b:
            parts.append(str(a))
        elif b == a + 1:
            parts.append(f"{a}, {b}")
        else:
            parts.append(f"{a}–{b}")
    return "[" + ", ".join(parts) + "]"


@retry_limit(2)
def main():
    refs_master = json.loads(REFS_JSON.read_text(encoding="utf-8"))
    tpl = TPL_EN.read_text(encoding="utf-8")

    # Split at ## References so first-appearance order is determined strictly from body_before_refs
    body_part, after_refs = tpl.split("## References\n{{REFERENCES_BLOCK}}", 1)

    cite_re = re.compile(r"\[CITE:([A-Za-z0-9_,]+)\]")
    key_to_num = {}
    ordered_keys = []

    for m in cite_re.finditer(body_part):
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        for k in keys:
            if k not in refs_master:
                raise KeyError(f"Unknown citekey in body: {k}")
            if k not in key_to_num:
                key_to_num[k] = len(ordered_keys) + 1
                ordered_keys.append(k)

    # Check if any citekey appears ONLY in after_refs (e.g. Tables)
    for m in cite_re.finditer(after_refs):
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        for k in keys:
            if k not in refs_master:
                raise KeyError(f"Unknown citekey in tables/legends: {k}")
            if k not in key_to_num:
                raise ValueError(f"Citekey {k} used in Tables/Legends without appearing in main body first!")

    unused = sorted(set(refs_master.keys()) - set(ordered_keys))
    if unused:
        print(f"NOTE: Unused master references ({len(unused)}): {unused}")

    def repl_cite(m):
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        nums = [key_to_num[k] for k in keys]
        return compress_nums(nums)

    body_compiled = cite_re.sub(repl_cite, body_part)
    after_compiled = cite_re.sub(repl_cite, after_refs)

    ref_lines = [f"{idx}. {refs_master[k]}" for idx, k in enumerate(ordered_keys, 1)]
    refs_block = "## References\n" + "\n".join(ref_lines)

    full_md = body_compiled + refs_block + after_compiled
    OUT_EN_ROOT.write_text(full_md, encoding="utf-8")
    OUT_EN_PKG.parent.mkdir(parents=True, exist_ok=True)
    OUT_EN_PKG.write_text(full_md, encoding="utf-8")
    MAP_OUT.write_text(json.dumps({"ordered_keys": ordered_keys, "key_to_num": key_to_num}, indent=2), encoding="utf-8")

    print(f"Compiled {len(ordered_keys)} references [1..{len(ordered_keys)}] -> {OUT_EN_ROOT}")

    if TPL_ZH.exists():
        tpl_zh = TPL_ZH.read_text(encoding="utf-8")
        body_zh, after_zh = tpl_zh.split("## 参考文献\n{{REFERENCES_BLOCK}}", 1)
        body_zh_comp = cite_re.sub(repl_cite, body_zh)
        after_zh_comp = cite_re.sub(repl_cite, after_zh)
        refs_block_zh = "## 参考文献\n" + "\n".join(ref_lines)
        full_zh = body_zh_comp + refs_block_zh + after_zh_comp
        OUT_ZH_ROOT.write_text(full_zh, encoding="utf-8")
        OUT_ZH_PKG.write_text(full_zh, encoding="utf-8")
        print(f"Compiled ZH parity review manuscript -> {OUT_ZH_ROOT}")


if __name__ == "__main__":
    main()
