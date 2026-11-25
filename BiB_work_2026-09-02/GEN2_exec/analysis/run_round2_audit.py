import re
import json
import docx
from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
MS_PATH = BASE / "MANUSCRIPT_GEN2_v1.0.md"
SUPP_PATH = BASE / "SUPPLEMENTARY_GEN2_v1.0.md"
CL_PATH = BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md"
DOCX_PATH = BASE / "MANUSCRIPT_GEN2_v1.0.docx"

ms_text = MS_PATH.read_text(encoding="utf-8")
supp_text = SUPP_PATH.read_text(encoding="utf-8")
cl_text = CL_PATH.read_text(encoding="utf-8")

print("=== 1. SECTION WORD COUNTS & PARAGRAPH LENGTH AUDIT (R5) ===")
parts = re.split(r"(?m)^##\s+", ms_text)
for p in parts[1:]:
    lines = p.strip().splitlines()
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    words = len(body.split())
    if title == "References":
        paras = [x.strip() for x in body.splitlines() if x.strip()]
    else:
        paras = [x.strip() for x in re.split(r"\n\s*\n", body) if x.strip() and not x.strip().startswith("#") and not x.strip().startswith("|") and not x.strip().startswith("[INSERT")]
    p_lens = [len(x.split()) for x in paras]
    avg_p = sum(p_lens)/len(p_lens) if p_lens else 0
    max_p = max(p_lens) if p_lens else 0
    over_250 = [(idx+1, len(x.split()), x[:80].replace("\n", " ")) for idx, x in enumerate(paras) if len(x.split()) > 250]
    over_450 = [(idx+1, len(x.split()), x[:80].replace("\n", " ")) for idx, x in enumerate(paras) if len(x.split()) > 450]
    print(f"[{title}] Total: {words}w | Paras: {len(p_lens)} | Avg: {avg_p:.1f}w | Max: {max_p}w | >250w: {len(over_250)} | >450w: {len(over_450)}")
    for idx, wlen, snip in over_250:
        flag = "🔴 >450w" if wlen > 450 else "🟡 >250w"
        print(f"   {flag} Para #{idx} ({wlen}w): {snip}...")

print("\n=== 2. STEP 6.5 AI WRITING HABITS & ROUND 6C SCAN (PROSE EXCLUDING BIBLIOGRAPHY) ===")
ms_prose = ms_text.split("## References")[0]
for doc_name, txt in [("MANUSCRIPT_PROSE", ms_prose), ("SUPPLEMENTARY", supp_text), ("COVER_LETTER", cl_text)]:
    hits = 0
    for idx, line in enumerate(txt.splitlines(), 1):
        if line.strip().startswith("[INSERT "):
            continue
        m27 = re.findall(r"\b(first\s+to|the\s+first|for\s+the\s+first\s+time|novel|unprecedented|groundbreaking|paradigm\s+shift|pioneering|unique|only\s+study|to\s+our\s+knowledge|no\s+prior\s+study|never\s+before)\b", line, re.I)
        m28 = re.findall(r"\b(to\s+directly\s+address|to\s+preempt|to\s+satisfy|as\s+requested\s+by|in\s+order\s+to\s+convince|to\s+guard\s+against\s+the\s+criticism|anticipating\s+the\s+concern|to\s+circumvent\s+reviewer|to\s+demonstrate\s+rigor|we\s+deliberately\s+chose)\b", line, re.I)
        m29 = re.findall(r"\b(prior\s+studies\s+failed\s+to|previous\s+work\s+overlooked|existing\s+methods\s+are\s+incapable|unlike\s+flawed\s+prior|bridging\s+this\s+critical\s+void|fills\s+a\s+critical\s+gap|remains\s+completely\s+unexplored)\b", line, re.I)
        m30 = re.findall(r"\b(aligns\s+with\s+the\s+scope\s+of|fits\s+the\s+readership|suitable\s+for\s+publication\s+in|of\s+broad\s+interest\s+to\s+the\s+readers)\b", line, re.I)
        m31 = re.findall(r"(\bTODO\b|\bTBD\b|\bFIXME\b|\bPLACEHOLDER\b|\[citation\s*needed\]|\[ref\]|\bRound\s*\d|\bReviewer\s*#?\d|\bR\d+-C\d+|\bPoint\s*\d+\.\d+|\bv\d+\.\d+\b)", line, re.I)
        m6c = re.findall(r"\b(clearly|obviously|evidently|undoubtedly|indisputably|strikingly|remarkably|dramatically|profoundly|importantly|notably|interestingly|crucially|post\s+hoc|post-hoc|secondary\s+analysis|retrospective\s+re-analysis)\b", line, re.I)
        m_h3 = re.findall(r"\b(comprehensive|systematic|systematically|robust|rigorous|delve|tapestry|testament|underscore|watershed|hallmark)\b", line, re.I)
        for tag, mm in [("AI-27", m27), ("AI-28", m28), ("AI-29", m29), ("AI-30", m30), ("AI-31", m31), ("6C/R13", m6c), ("H3", m_h3)]:
            if mm:
                hits += 1
                print(f"  [{doc_name} {tag} L{idx}] {mm}: {line[:105]}")
    print(f"--- {doc_name}: Total prose hits = {hits} ---")

print("\n=== 3. STEP 5 THREE-LOCK & DOCX PLACEHOLDER CHECK ===")
body_before_legends = ms_text.split("## Figure Legends")[0]
# Remove [INSERT ... ABOUT HERE] lines when scanning prose first-appearance
prose_no_insert = re.sub(r"(?m)^\[INSERT .+\]$", "", body_before_legends)

fig_mentions = []
for m in re.finditer(r"\bFigures?\s+(\d+)[A-Za-z]?\b", prose_no_insert):
    n = int(m.group(1))
    if n not in fig_mentions:
        fig_mentions.append(n)

tab_mentions = []
for m in re.finditer(r"(?<!Supplementary )\bTables?\s+(\d+)\b", prose_no_insert):
    n = int(m.group(1))
    if n not in tab_mentions:
        tab_mentions.append(n)

snote_mentions = []
for m in re.finditer(r"\bSupplementary Note\s+(\d+)\b", prose_no_insert):
    n = int(m.group(1))
    if n not in snote_mentions:
        snote_mentions.append(n)

stab_mentions = []
for m in re.finditer(r"\bSupplementary Table\s+(S\d+)\b", prose_no_insert):
    s = m.group(1)
    if s not in stab_mentions:
        stab_mentions.append(s)

ref_mentions = []
body_before_refs = ms_text.split("## References")[0]
# Exclude math interval [0, 1] and [100 - ECE%] and [H^{-1}]
body_clean_refs = re.sub(r"\[0,\s*1\]", "", body_before_refs)
for m in re.finditer(r"\[(\d+(?:[–\-,\s]+\d+)*)\]", body_clean_refs):
    raw = m.group(1)
    for part in re.split(r"[,\s]+", raw):
        if "–" in part or "-" in part:
            ab = re.split(r"[–\-]", part)
            if len(ab) == 2 and ab[0].isdigit() and ab[1].isdigit():
                for k in range(int(ab[0]), int(ab[1])+1):
                    if k not in ref_mentions:
                        ref_mentions.append(k)
        elif part.isdigit():
            k = int(part)
            if k not in ref_mentions:
                ref_mentions.append(k)

print(f"First-appearance Main Figures: {fig_mentions} (Expected: [1, 2, 3, 4, 5, 6, 7])")
print(f"First-appearance Main Tables:  {tab_mentions} (Expected: [1, 2])")
print(f"First-appearance Supp Notes:   {snote_mentions} (Expected: [1, 2, 3])")
print(f"First-appearance Supp Tables:  {stab_mentions} (Expected: ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])")
print(f"First-appearance References:   1..{len(ref_mentions)} strictly monotonic? {ref_mentions == list(range(1, 64))}")

d = docx.Document(str(DOCX_PATH))
docx_txt = "\n".join(p.text for p in d.paragraphs)
placeholders = re.findall(r"\[INSERT (?:FIGURE|TABLE) \w+ ABOUT HERE\]", docx_txt)
print(f"DOCX [INSERT ... ABOUT HERE] placeholders ({len(placeholders)}): {placeholders}")

print("\n=== 4. NUMERICAL SUPERSET LOCK (SUMMARY / HIGHLIGHTS / BIGGER PICTURE VS MAIN BODY) ===")
sec_dict = {}
for p in parts[1:]:
    lines = p.strip().splitlines()
    sec_dict[lines[0].strip()] = "\n".join(lines[1:]).strip()

front_matter = sec_dict["Highlights"] + "\n" + sec_dict["The bigger picture"] + "\n" + sec_dict["Summary"]
main_body = (
    sec_dict["Introduction"] + "\n" +
    sec_dict["Results"] + "\n" +
    sec_dict["Discussion"] + "\n" +
    sec_dict["Limitations of the Study"] + "\n" +
    sec_dict["STAR Methods"] + "\n" +
    sec_dict["Figure Legends"] + "\n" +
    sec_dict["Tables"]
)
front_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?", front_matter))
body_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?", main_body))
missing_in_body = front_nums - body_nums
print(f"Front-matter numeric tokens count: {len(front_nums)}")
print(f"Missing in Main Body (Must be empty set): {missing_in_body}")
