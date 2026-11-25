import re
import sys
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
DESKTOP = Path(r"C:\Users\sheng\Desktop")

MD_FILES = [
    ("MS_NMI_PRIMARY_MD", BASE / "MANUSCRIPT_NMI_v1.0.md"),
    ("ZH_MS_NMI_PRIMARY_MD", BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md"),
    ("ZH_MS_MAIN_MD", BASE / "STAR-Audit_手稿全文中文版_审核稿.md"),
    ("CL_NMI_PRIMARY_MD", BASE / "COVER_LETTER_NMI_v1.0.md"),
    ("CL_NMI_BILINGUAL_MD", BASE / "STAR-Audit_投稿信_NMI_中英对照版.md"),
    ("MS_NPJ_BACKUP_MD", BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md"),
    ("ZH_MS_NPJ_BACKUP_MD", BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md"),
    ("CL_NPJ_BACKUP_MD", BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.md"),
    ("SUPP_MD", BASE / "SUPPLEMENTARY_GEN2_v1.0.md"),
    ("MS_PATTERNS_BACKUP_MD", BASE / "MANUSCRIPT_GEN2_v1.0.md"),
    ("CL_PATTERNS_BACKUP_MD", BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md"),
    ("QC_REPORT_MD", BASE / "PRE_SUBMISSION_QC_REPORT_GEN2_v1.0.md"),
]

DOCX_FILES = [
    ("MS_NMI_PRIMARY_DOCX", BASE / "MANUSCRIPT_NMI_v1.0.docx"),
    ("ZH_MS_NMI_PRIMARY_DOCX", BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx"),
    ("ZH_MS_MAIN_DOCX", BASE / "STAR-Audit_手稿全文中文版_审核稿.docx"),
    ("CL_NMI_PRIMARY_DOCX", BASE / "COVER_LETTER_NMI_v1.0.docx"),
    ("CL_NMI_BILINGUAL_DOCX", BASE / "STAR-Audit_投稿信_NMI_中英对照版.docx"),
    ("MS_NPJ_BACKUP_DOCX", BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.docx"),
    ("ZH_MS_NPJ_BACKUP_DOCX", BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.docx"),
    ("CL_NPJ_BACKUP_DOCX", BASE / "COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.docx"),
    ("SUPP_DOCX", BASE / "SUPPLEMENTARY_GEN2_v1.0.docx"),
    ("MS_PATTERNS_BACKUP_DOCX", BASE / "MANUSCRIPT_GEN2_v1.0.docx"),
    ("CL_PATTERNS_BACKUP_DOCX", BASE / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.docx"),
    ("DESKTOP_EN_NMI_DOCX", DESKTOP / "STAR-Audit_Manuscript_NaturePortfolio_v1.0.docx"),
    ("DESKTOP_SUPP_DOCX", DESKTOP / "STAR-Audit_Supplementary_Information_v1.0.docx"),
    ("DESKTOP_ZH_MS_DOCX", DESKTOP / "STAR-Audit_手稿全文中文版_审核稿.docx"),
    ("DESKTOP_ZH_CL_DOCX", DESKTOP / "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx"),
]

STALE_OR_BANNED_PATTERNS = [
    r"\bOSF\b",
    r"KF2G8",
    r"(?i:preregist)",
    r"(?i:pre-regist)",
    r"预注册",
    r"(?i:external\s+(?:paid\s+)?API)",
    r"无外部付费",
    r"db-wal",
    r"PREREG_v2",
    r"Nosek\s+BA",
    r"Errington\s+TM",
    r"Gemini[-‑ ]Pro\b",
    r"Gemini[-‑ ]Flash\b",
    r"\b36\.03\b",
    r"3,603",
    r"183\s+(?:distinct\s+)?Gemini",
    r"(?<!\\t)ext\{ECE\}",
    r"grok[-‑]4\.20",
    r"grok[-‑]4[-‑]1[-‑]fast",
    r"Full[-‑ ]Thinking",
    r"full\s+thinking",
    r"完整推理",
    r"Ranks?\s+12[–\-]18",
    r"第\s*12[–\-]18\s*名",
    r"Rank\s+18\s*\(Eliminated\)",
    r"\b6,193\b",
    r"\b9,336\.2\b",
    r"\b0\.1621\b",
    r"\b0\.1043\b",
    r"\b0\.728\b",
    r"\b1\.385\b",
]
STALE_RE = re.compile("|".join(STALE_OR_BANNED_PATTERNS))

total_errors = 0

print("=====================================================================")
print("1. MANUSCRIPT-SUBMISSION-DOCX-FORMAT & BANNED-TERM HARD AUDIT (15 DOCX)")
print("=====================================================================")
for name, dpath in DOCX_FILES:
    if not dpath.exists():
        print(f"[ERROR] Missing DOCX file: {dpath}")
        total_errors += 1
        continue
    doc = docx.Document(str(dpath))
    n_paras = len(doc.paragraphs)
    n_tables = len(doc.tables)
    ls_bad, align_bad, font_bad, raw_latex_bad, stale_bad = [], [], [], [], []

    for idx, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        if p.paragraph_format.line_spacing != 2.0:
            ls_bad.append((idx, p.paragraph_format.line_spacing, p.text[:50]))
        if p.alignment != WD_ALIGN_PARAGRAPH.JUSTIFY:
            align_bad.append((idx, p.alignment, p.text[:50]))
        for r in p.runs:
            if r.text.strip() and r.font.name != "Times New Roman":
                font_bad.append((idx, r.font.name, r.text[:30]))
        if re.search(r"[\\\$]|\*\*|\b_[a-zA-Z0-9]|∈fty|\^→p|\t", p.text):
            raw_latex_bad.append((f"P{idx}", p.text[:100]))
        m_st = STALE_RE.search(p.text)
        if m_st:
            stale_bad.append((f"P{idx}", m_st.group(0), p.text[:100]))

    for tidx, tbl in enumerate(doc.tables):
        for ridx, row in enumerate(tbl.rows):
            for cidx, cell in enumerate(row.cells):
                ct = cell.text
                if re.search(r"[\\\$]|\*\*|\b_[a-zA-Z0-9]|∈fty|\^→p|\t", ct):
                    raw_latex_bad.append((f"T{tidx}R{ridx}C{cidx}", ct[:100]))
                m_st = STALE_RE.search(ct)
                if m_st:
                    stale_bad.append((f"T{tidx}R{ridx}C{cidx}", m_st.group(0), ct[:100]))

    errs = len(ls_bad) + len(align_bad) + len(font_bad) + len(raw_latex_bad) + len(stale_bad)
    total_errors += errs
    print(
        f"[{name}] Paras={n_paras}, Tables={n_tables} | ls!=2.0: {len(ls_bad)} | "
        f"align!=JUSTIFY: {len(align_bad)} | font!=TNR: {len(font_bad)} | "
        f"raw_LaTeX/MD/TAB: {len(raw_latex_bad)} | banned/stale: {len(stale_bad)}"
    )
    for item in raw_latex_bad[:5]:
        print("   RAW HIT:", item)
    for item in stale_bad[:5]:
        print("   BANNED/STALE HIT:", item)

print("\n=====================================================================")
print("2. ALL 12 MARKDOWN DELIVERABLES BANNED-TERM & VERSIONED TIER AUDIT")
print("=====================================================================")
for name, mpath in MD_FILES:
    if not mpath.exists():
        print(f"[ERROR] Missing MD file: {mpath}")
        total_errors += 1
        continue
    txt = mpath.read_text(encoding="utf-8")
    stale_hits = [m.group(0) for m in STALE_RE.finditer(txt)]
    has_argon = ("Gemini-4-Argon-High" in txt) and ("gemini-4-argon-high" in txt)
    has_flash38 = ("Gemini-3.8-Flash" in txt) and ("gemini-3.8-flash-tiered" in txt)
    if stale_hits or not has_argon or not has_flash38:
        total_errors += len(stale_hits) + (0 if has_argon else 1) + (0 if has_flash38 else 1)
    print(f"[{name}] Banned/stale hits: {len(stale_hits)} {stale_hits[:5]} | Argon-4-High IDs: {has_argon} | Flash-3.8 IDs: {has_flash38}")

if (BASE / "STAR-Audit_手稿全文中文版_审核稿.docx").read_bytes() != (DESKTOP / "STAR-Audit_手稿全文中文版_审核稿.docx").read_bytes():
    print("[ERROR] Desktop Chinese DOCX and workspace Chinese DOCX differ!")
    total_errors += 1
else:
    print("[OK] Desktop Chinese DOCX and workspace NMI Chinese DOCX are byte-for-byte identical.")

print("\n=====================================================================")
print("3. NMI PRIMARY & NPJ BACKUP WORD BUDGET + 69-REF + PLACEHOLDER GATES")
print("=====================================================================")
nmi_txt = (BASE / "MANUSCRIPT_NMI_v1.0.md").read_text(encoding="utf-8")
npj_txt = (BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md").read_text(encoding="utf-8")

m_nmi_abs = re.search(r"## Abstract\s+(.+?)\s+(?:\*\*Keywords:\*\*|## Introduction)", nmi_txt, re.S)
nmi_abs_words = len(m_nmi_abs.group(1).strip().split()) if m_nmi_abs else 999
nmi_parts = re.split(r"^##\s+(.+)$", nmi_txt, flags=re.M)
nmi_secs = {nmi_parts[i].strip(): nmi_parts[i + 1].strip() for i in range(1, len(nmi_parts), 2)}
nmi_main_words = sum(len(nmi_secs[k].split()) for k in ["Introduction", "Results", "Discussion"])
print(f"[NMI PRIMARY] Abstract={nmi_abs_words} words (<200): {'OK' if nmi_abs_words < 200 else 'EXCEEDED'} | Main Text={nmi_main_words} words (3500..4500): {'OK' if 3500 <= nmi_main_words <= 4500 else 'OUT_OF_RANGE'}")
if nmi_abs_words >= 200 or not (3500 <= nmi_main_words <= 4500):
    total_errors += 1

m_npj_abs = re.search(r"## Abstract\s+(.+?)\s+(?:\*\*Keywords:\*\*|## Introduction)", npj_txt, re.S)
npj_abs_words = len(m_npj_abs.group(1).strip().split()) if m_npj_abs else 999
print(f"[NPJ BACKUP]  Abstract={npj_abs_words} words (<250): {'OK' if npj_abs_words < 250 else 'EXCEEDED'}")
if npj_abs_words >= 250:
    total_errors += 1

# Verify 69 references and new [31-35] 2025-2026 NMI/npj Digit Med papers in both NMI and npj manuscripts
for label_ms, ms_text in [("NMI_PRIMARY", nmi_txt), ("NPJ_BACKUP", npj_txt), ("PATTERNS_BACKUP", (BASE / "MANUSCRIPT_GEN2_v1.0.md").read_text(encoding="utf-8"))]:
    has_69 = bool(re.search(r"(?m)^69\.\s+Brier GW\.", ms_text)) and not bool(re.search(r"(?m)^70\.\s+", ms_text))
    has_5_new = all(tok in ms_text for tok in ["10.1038/s42256-026-01266-0", "10.1038/s42256-025-01124-5", "10.1038/s41746-026-02951-5", "10.1038/s41746-026-03069-4", "10.1038/s41746-026-03097-0"])
    print(f"[{label_ms}] Exact 69 verified references? {has_69} | All 5 new 2025–2026 NMI/npj benchmarks cited? {has_5_new}")
    if not has_69 or not has_5_new:
        total_errors += 1

# Placeholder order check
nmi_body = nmi_txt.split("## Figure Legends")[0]
nmi_ph = [p.title() for p in re.findall(r"^\[INSERT (FIGURE \d+) ABOUT HERE\]$", nmi_body, re.M)]
print(f"[NMI_PRIMARY] Main Figure placeholders: {nmi_ph} == Figure 1..6? {nmi_ph == [f'Figure {i}' for i in range(1, 7)]}")
if nmi_ph != [f"Figure {i}" for i in range(1, 7)]:
    total_errors += 1

fig_dir = BASE / "GEN2_exec" / "figures"
expected_figs = [
    "Fig1_Audit_Remediation_Architecture",
    "Fig2_Dim1_Trojan_Horse_Citations",
    "Fig3_Dim2_Reasoning_vs_Memorization",
    "Fig4_Dim3_Dim5_Primacy_and_NLI",
    "Fig5_Dim4_Dim6_Reasoning_Paradox",
    "Fig6_Audit_Guided_Rectification_Impact",
    "Fig7_STAR_Audit_Working_Model",
]
fig_ok = all((fig_dir / f"{fn}.png").exists() and (fig_dir / f"{fn}.pdf").exists() for fn in expected_figs)
print(f"Lock 2 (All 7 PNG + 7 PDF display items exist on disk)? {fig_ok}")
if not fig_ok:
    total_errors += 1

print("\n=====================================================================")
print("4. CROSS-PROJECT CONTAMINATION & RAW DATA TRACEABILITY CHECK")
print("=====================================================================")
contam_terms = [r"\bTBI\b", r"\btraumatic brain injury\b", r"\bPANoptosis\b", r"\bMIMIC-IV\b", r"\beICU\b", r"\bglioblastoma\b", r"\bstroke\b", r"\bsepsis\b"]
contam_hits = [(pat, re.findall(pat, nmi_txt, re.I)) for pat in contam_terms if re.findall(pat, nmi_txt, re.I)]
print(f"Cross-project contamination hits: {len(contam_hits)} {contam_hits}")
total_errors += len(contam_hits)

trace_files = [
    BASE / "GEN2_exec" / "canary_prompts.json",
    BASE / "GEN2_exec" / "analysis" / "offtopic_calibration_100.csv",
    BASE / "GEN2_exec" / "analysis" / "MASTER_GEN2_AUDIT_RESULTS.json",
    BASE / "GEN2_exec" / "analysis" / "step1_pubmed_results.json",
    BASE / "GEN2_exec" / "analysis" / "step2_dim2_3_4_rectification_results.json",
    BASE / "GEN2_exec" / "analysis" / "step3_expC_dim6_paradox_results.json",
    BASE / "GEN2_exec" / "analysis" / "step4_dim5_nli_results.json",
    BASE / "GEN2_exec" / "analysis" / "cot_trajectory_dynamics_summary.json",
    BASE / "GEN2_exec" / "analysis" / "gemini_cross_ecosystem_summary.json",
    BASE / "GEN2_exec" / "analysis" / "grok_cross_ecosystem_summary.json",
    BASE / "GEN2_exec" / "analysis" / "generate_all_figures.py",
    BASE / "GEN2_exec" / "analysis" / "build_nmi_primary_edition.py",
]
missing_trace = [str(f) for f in trace_files if not f.exists()]
print(f"Traceability raw data & script files verified: {len(trace_files) - len(missing_trace)}/{len(trace_files)}")
total_errors += len(missing_trace)

print("\n=====================================================================")
print(f"FINAL PRE-SUBMISSION QC GATE: {total_errors} ERRORS")
print("=====================================================================")
sys.exit(1 if total_errors > 0 else 0)
