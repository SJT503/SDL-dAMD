#!/usr/bin/env python3
"""
Assemble the turnkey STAR-Audit v1.0 NMI-First submission package in both:
  1. D:\\Papers\\Robin_Nature_2026\\BiB_work_2026-09-02\\STAR-Audit_投稿包_v1.0
  2. C:\\Users\\sheng\\Desktop\\STAR-Audit_投稿包_v1.0

Root package is configured for *Nature Machine Intelligence* (Slimmed Article:
180-word Abstract, 4,008-word Main Text, 6 Main Figures, 1 Extended Data Figure,
2 Extended Data Tables, 69 live-Entrez-verified references).
Backup packages are cleanly organized in:
  - backup_npj_Digital_Medicine/ (Full-length *npj Digital Medicine* Article + ZH review edition)
  - backup_CellPress_Patterns/ (Cell Press *Patterns* Research Article)
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

WS_ROOT = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
FIG_SRC = WS_ROOT / "GEN2_exec" / "figures"
DESKTOP_ROOT = Path(r"C:\Users\sheng\Desktop")

WS_PKG = WS_ROOT / "STAR-Audit_投稿包_v1.0"
DESKTOP_PKG = DESKTOP_ROOT / "STAR-Audit_投稿包_v1.0"

BANNED_RE = re.compile(
    r"\bOSF\b|KF2G8|(?i:preregist)|(?i:pre-regist)|预注册|(?i:external\s+(?:paid\s+)?API)|无外部付费|db-wal|PREREG_v2|Nosek\s+BA|Errington\s+TM"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_md_cell(text: str) -> str:
    s = text.strip()
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"`(.*?)`", r"\1", s)
    replacements = {
        r"\rightarrow": "->",
        r"\to": "->",
        r"\leftarrow": "<-",
        r"\ge": ">=",
        r"\le": "<=",
        r"\neq": "!=",
        r"\pm": "+/-",
        r"\times": "x",
        r"\Delta": "Delta ",
        r"\chi^2": "chi2",
        r"\%": "%",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = s.replace("$", "")
    return re.sub(r"\s+", " ", s).strip()


def parse_markdown_tables_after_headers(md_path: Path, specs: list[tuple[str, str, str]]) -> dict[str, tuple[str, list[list[str]]]]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    out: dict[str, tuple[str, list[list[str]]]] = {}
    for pattern, sheet_name, csv_name in specs:
        start_idx = None
        for idx, line in enumerate(lines):
            if re.search(pattern, line):
                start_idx = idx
                break
        if start_idx is None:
            raise RuntimeError(f"Could not find table header matching {pattern} in {md_path.name}")
        rows: list[list[str]] = []
        in_table = False
        for line in lines[start_idx + 1 :]:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c != ""):
                    continue
                rows.append([strip_md_cell(c) for c in cells])
            elif in_table:
                break
        if not rows:
            raise RuntimeError(f"Found header for {sheet_name} in {md_path.name}, but 0 table rows followed.")
        out[sheet_name] = (csv_name, rows)
    return out


def export_tables_csv_and_xlsx(pkg_dir: Path) -> list[str]:
    tables_dir = pkg_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    ext_specs = [
        (r"^\*\*Extended Data Table 1\.", "ExtData_Table_1", "Extended_Data_Table1_STAR_Audit_Framework_Comparison.csv"),
        (r"^\*\*Extended Data Table 2\.", "ExtData_Table_2", "Extended_Data_Table2_Confirmatory_Hypothesis_Family_Outcomes.csv"),
    ]
    supp_specs = [
        (r"^## Supplementary Table S1\.", "Table_S1_Top5_Dossiers", "TableS1_12Runs_Top5_Target_Dossiers.csv"),
        (r"^## Supplementary Table S2\.", "Table_S2_PositionBias", "TableS2_Tournament_PositionBias_and_OAE.csv"),
        (r"^## Supplementary Table S3\.", "Table_S3_ExpB_Citations", "TableS3_ExpB_14Domains_Randomized_Citation_Trial.csv"),
        (r"^## Supplementary Table S4\.", "Table_S4_ExpC_HPO_IC", "TableS4_ExpC_v4_MultiVendor_HPO_IC_Deletion.csv"),
        (r"^## Supplementary Table S5\.", "Table_S5_NLI_Audit", "TableS5_DeBERTa_v3_CrossStage_NLI_Contradiction_Audit.csv"),
        (r"^## Supplementary Table S6\.", "Table_S6_Governance", "TableS6_Operational_Governance_Ledger_D2_001_to_012.csv"),
        (r"^## Supplementary Table S7\.", "Table_S7_CoT_4Family", "TableS7_WhiteBox_CoT_and_4Family_Validation.csv"),
    ]

    parsed = {}
    parsed.update(parse_markdown_tables_after_headers(WS_ROOT / "MANUSCRIPT_NMI_v1.0.md", ext_specs))
    parsed.update(parse_markdown_tables_after_headers(WS_ROOT / "SUPPLEMENTARY_GEN2_v1.0.md", supp_specs))

    csv_files: list[str] = []
    for sheet_name, (csv_name, rows) in parsed.items():
        csv_path = tables_dir / csv_name
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        csv_files.append(csv_name)

    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        header_font = Font(name="Times New Roman", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(fill_type="solid", start_color="1F4E78", end_color="1F4E78")
        body_font = Font(name="Times New Roman", size=10.5)
        thin_side = Side(border_style="thin", color="D9D9D9")
        bottom_heavy = Side(border_style="medium", color="1F4E78")

        for sheet_name, (_, rows) in parsed.items():
            ws = wb.create_sheet(title=sheet_name[:31])
            for r_idx, row in enumerate(rows, start=1):
                ws.append(row)
                for c_idx in range(1, len(row) + 1):
                    cell = ws.cell(row=r_idx, column=c_idx)
                    if r_idx == 1:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                    else:
                        cell.font = body_font
                        cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                        cell.border = Border(bottom=bottom_heavy if r_idx == len(rows) else thin_side)
            ws.freeze_panes = "A2"
            for col_idx in range(1, ws.max_column + 1):
                col_letter = get_column_letter(col_idx)
                max_len = max(len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(1, ws.max_row + 1))
                ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 52)

        xlsx_path = pkg_dir / "Supplementary_Tables_S1_to_S7_v1.0.xlsx"
        wb.save(xlsx_path)
    except Exception as exc:
        print(f"[WARN] openpyxl workbook generation skipped: {exc}")

    return csv_files


def write_upload_manifest(pkg_dir: Path) -> None:
    manifest = """# UPLOAD MANIFEST & SUBMISSION GUIDE (`STAR-Audit` v1.0 — *Nature Machine Intelligence* Primary & *npj Digital Medicine* Backup)

**Primary Target Journal (Root Package — Nature Portfolio MTS `https://mts-natmachintell.nature.com/`):** *Nature Machine Intelligence* (Article: 180-word Abstract; ~4,000-word Main Text; 6 Main Figures; 1 Extended Data Figure; 2 Extended Data Tables; 69 live-Entrez-verified references)
**First Backup Package (`backup_npj_Digital_Medicine/`):** *npj Digital Medicine* (Full-Length Article: 224-word Abstract; 7 Main Figures; 2 Main Tables; 69 live-Entrez-verified references)
**Second Backup Package (`backup_CellPress_Patterns/`):** Cell Press *Patterns* (Research Article with Highlights / The Bigger Picture / eTOC Blurb)
**Manuscript Title (EN):** Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery
**手稿标题（中文审阅版）：** 审计与纠偏自主人工智能科学发现中的推理、锦标赛与文献锚定失效
**Corresponding Authors:** Jiangtao Sheng (`jtsheng@stu.edu.cn`, Lead Contact; ORCID: `0000-0003-2438-7345`), Weiqiang Chen (`wqchen@stu.edu.cn`; ORCID: `0000-0002-2612-0890`)
**Code & SHA-256 Frozen Protocol Repository:** `https://github.com/SJT503/SDL-dAMD`
**Archived Audit Telemetry Dataset DOI:** Zenodo (`https://doi.org/10.5281/zenodo.20574265`)

---

## 1. *Nature Machine Intelligence* 正式上传顺序指引（Springer Nature SNAPP 主投清单）

> **重要提示：** 向 *Nature Machine Intelligence* 投稿系统上传时，**请仅上传根目录纯英文 `_submission_EN` / `_EN` 文件、`figures/main/` 下的 6 张主图及 `figures/extended_data/` 下的 1 张扩展数据图**，切勿误传中英对照投稿信或中文审阅稿。

| SNAPP 上传槽位 (Upload Slot) | 请选择本包内文件 | 格式与投稿前 QC 状态 |
| :--- | :--- | :--- |
| **1. Manuscript File**（主手稿） | `Manuscript_NMI_v1.0_submission_EN.docx` | 纯英文 *Nature Machine Intelligence* 瘦身标准主稿（Abstract **180 词** `< 200 词上限`；Main Text [Intro+Results+Discussion] **4,008 词** `[正中 3,500–4,500 词甜点区]`；Methods 2,243 词；Figures 1–6 图注 + Extended Data Fig. 1 + Extended Data Tables 1–2 原生三线表；**69 篇** live-Entrez 核验文献；`Times New Roman` 12pt + 2.0 倍行距 + 两端对齐，0 源码残留） |
| **2. Cover Letter**（投稿信） | `Cover_Letter_NMI_v1.0_submission_EN.docx` | **纯英文 *Nature Machine Intelligence* 定制投稿信**（致主编 Dr. Liesbeth Venema，紧扣 *NMI* 2025–2026 同类研究 `DeepEvidence` / `GOLLuM` / `CleanSplit` 定位测试时推理悖论与四大零调用确定性纠偏算子） |
| **3. Supplementary Information**（补充材料） | `Supplementary_Information_v1.0_EN.docx` 及 `Supplementary_Tables_S1_to_S7_v1.0.xlsx` | 纯英文补充材料（Supplementary Notes 1–3 + Supplementary Tables S1–S7 全量三线表；Excel 9 工作表工作簿含 `ExtData_Table_1–2` 与 `Table_S1–S7`） |
| **4. Main Figures (1–6)**（主图） | `figures/main/Fig1_*.pdf`（或 `.png`）至 `Fig6_*.pdf`（或 `.png`） | 6 张 *NMI* 主图（矢量 `.pdf` + `300 DPI` `.png` + `.svg`），全部通过无遮挡、无文字重叠美学门禁 |
| **5. Extended Data Figure 1**（扩展数据图） | `figures/extended_data/Extended_Data_Fig1_STAR_Audit_Working_Model.pdf`（或 `.png`） | 1 张扩展数据图（STAR-Audit 工作模型与三阶段运行架构示意图） |
| **6. Confidential Notes to Editor**（给编辑的保密备注） | 粘贴 Zenodo 审稿人免登录预览链接 | 请将 Zenodo 后台生成的 Private Reviewer Share Link（对应 `10.5281/zenodo.20574265`）粘贴至投稿系统 *Confidential Notes to Editor* 栏 |

---

## 2. 一键切换至备选一刊 *npj Digital Medicine* 指引（`backup_npj_Digital_Medicine/`）

若需一键转投 *npj Digital Medicine*（不限正文词数的完整详尽版）：
1. **Manuscript File**：上传 `backup_npj_Digital_Medicine/Manuscript_npjDigitMed_Backup_v1.0_EN.docx`（Abstract 224 词 `< 250 词`；完整详尽正文 + 7 张主图 + 2 张主表 + 69 篇核验文献）。
2. **Cover Letter**：上传 `backup_npj_Digital_Medicine/Cover_Letter_npjDigitMed_Backup_v1.0_EN.docx`（致主编 Prof. Joseph C. Kvedar）。
3. **Supplementary Information**：直接复用根目录 `Supplementary_Information_v1.0_EN.docx` 与 `Supplementary_Tables_S1_to_S7_v1.0.xlsx`。
4. **Figures (1–7)**：上传 `figures/main/Fig1..Fig6` + `backup_npj_Digital_Medicine/Fig7_STAR_Audit_Working_Model.pdf`（或 `.png`）。

---

## 3. 包内完整文件目录说明

### 3.1 根目录（*Nature Machine Intelligence* 主投包 + 中文审阅稿）
- `Manuscript_NMI_v1.0_submission_EN.docx`（及 `.md`）—— ***Nature Machine Intelligence* 英文瘦身主投版手稿**
- `Cover_Letter_NMI_v1.0_submission_EN.docx`（及 `.md`）—— ***Nature Machine Intelligence* 纯英文正式投稿信**
- `Supplementary_Information_v1.0_EN.docx`（及 `.md`）—— **英文补充材料 Word 版**（Supplementary Notes 1–3 + Tables S1–S7）
- `Supplementary_Tables_S1_to_S7_v1.0.xlsx` —— **扩展数据表与补充数据总表（Excel 9 工作表工作簿）**
- `STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx` / `Manuscript_NMI_v1.0_CN_review.docx`（及 `.md`）—— ***NMI* 瘦身版 1:1 逐段对应中文全文审阅稿**（仅供作者团队内部审阅）
- `Cover_Letter_NMI_v1.0_CN_review.docx`（及 `.md`）—— ***NMI* 投稿信中英对照审阅版**（仅供内部审阅）
- `Pre_Submission_QC_Report_v1.0.md` —— 投稿前五重硬门禁与格式质检报告（`0 ERRORS`）

### 3.2 独立高清主图与扩展数据图（`figures/`）
- `figures/main/Fig1_Audit_Remediation_Architecture.*` 至 `Fig6_Audit_Guided_Rectification_Impact.*`（6 张 *NMI* 主图：`.pdf` / `.png` / `.svg`）
- `figures/extended_data/Extended_Data_Fig1_STAR_Audit_Working_Model.pdf` / `.png`（扩展数据图 1）

### 3.3 结构化 CSV 数据表（`tables/`）
- `Extended_Data_Table1_STAR_Audit_Framework_Comparison.csv`
- `Extended_Data_Table2_Confirmatory_Hypothesis_Family_Outcomes.csv`
- `TableS1_12Runs_Top5_Target_Dossiers.csv` 至 `TableS7_WhiteBox_CoT_and_4Family_Validation.csv`

### 3.4 *npj Digital Medicine* 备选完整版投稿包（`backup_npj_Digital_Medicine/`）
- `Manuscript_npjDigitMed_Backup_v1.0_EN.docx`（及 `.md`）
- `Cover_Letter_npjDigitMed_Backup_v1.0_EN.docx`（及 `.md`）
- `STAR-Audit_npj备选版_手稿全文中文版_审核稿.docx`（及 `.md`）
- `Fig7_STAR_Audit_Working_Model.pdf` / `.png`

### 3.5 Cell Press *Patterns* 备选投稿包（`backup_CellPress_Patterns/`）
- `Manuscript_Patterns_Backup_v1.0_EN.docx`（及 `.md`）
- `Cover_Letter_Patterns_Backup_v1.0_EN.docx`（及 `.md`）
"""
    (pkg_dir / "UPLOAD_MANIFEST_v1.0.md").write_text(manifest, encoding="utf-8")


def build_package(pkg_dir: Path) -> None:
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # 1. Root NMI Primary submission & review documents
    copy_map = [
        ("MANUSCRIPT_NMI_v1.0.docx", "Manuscript_NMI_v1.0_submission_EN.docx"),
        ("MANUSCRIPT_NMI_v1.0.md", "Manuscript_NMI_v1.0_submission_EN.md"),
        ("COVER_LETTER_NMI_v1.0.docx", "Cover_Letter_NMI_v1.0_submission_EN.docx"),
        ("COVER_LETTER_NMI_v1.0.md", "Cover_Letter_NMI_v1.0_submission_EN.md"),
        ("SUPPLEMENTARY_GEN2_v1.0.docx", "Supplementary_Information_v1.0_EN.docx"),
        ("SUPPLEMENTARY_GEN2_v1.0.md", "Supplementary_Information_v1.0_EN.md"),
        ("STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx", "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx"),
        ("STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx", "Manuscript_NMI_v1.0_CN_review.docx"),
        ("STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md", "Manuscript_NMI_v1.0_CN_review.md"),
        ("STAR-Audit_投稿信_NMI_中英对照版.docx", "Cover_Letter_NMI_v1.0_CN_review.docx"),
        ("STAR-Audit_投稿信_NMI_中英对照版.md", "Cover_Letter_NMI_v1.0_CN_review.md"),
        ("PRE_SUBMISSION_QC_REPORT_GEN2_v1.0.md", "Pre_Submission_QC_Report_v1.0.md"),
    ]
    for src_name, dst_name in copy_map:
        shutil.copy2(WS_ROOT / src_name, pkg_dir / dst_name)

    # 2. Figures: 6 Main Figures in figures/main/ and Extended Data Fig. 1 in figures/extended_data/
    fig_main_dst = pkg_dir / "figures" / "main"
    fig_ext_dst = pkg_dir / "figures" / "extended_data"
    fig_main_dst.mkdir(parents=True, exist_ok=True)
    fig_ext_dst.mkdir(parents=True, exist_ok=True)

    for fig_file in sorted(FIG_SRC.iterdir()):
        if not (fig_file.is_file() and fig_file.suffix.lower() in {".pdf", ".png", ".svg"}):
            continue
        if fig_file.name.startswith(("Fig1_", "Fig2_", "Fig3_", "Fig4_", "Fig5_", "Fig6_")):
            shutil.copy2(fig_file, fig_main_dst / fig_file.name)
        elif fig_file.name.startswith("Fig7_"):
            ext_name = fig_file.name.replace("Fig7_", "Extended_Data_Fig1_", 1)
            shutil.copy2(fig_file, fig_ext_dst / ext_name)

    # 3. Tables (CSV + multi-sheet XLSX)
    export_tables_csv_and_xlsx(pkg_dir)

    # 4. First Backup: npj Digital Medicine Full-Length Edition
    npj_dir = pkg_dir / "backup_npj_Digital_Medicine"
    npj_dir.mkdir(parents=True, exist_ok=True)
    npj_copies = [
        ("MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.docx", "Manuscript_npjDigitMed_Backup_v1.0_EN.docx"),
        ("MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md", "Manuscript_npjDigitMed_Backup_v1.0_EN.md"),
        ("COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.docx", "Cover_Letter_npjDigitMed_Backup_v1.0_EN.docx"),
        ("COVER_LETTER_NPJ_DigitalMed_Backup_v1.0.md", "Cover_Letter_npjDigitMed_Backup_v1.0_EN.md"),
        ("STAR-Audit_npj备选版_手稿全文中文版_审核稿.docx", "STAR-Audit_npj备选版_手稿全文中文版_审核稿.docx"),
        ("STAR-Audit_npj备选版_手稿全文中文版_审核稿.md", "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md"),
    ]
    for src_name, dst_name in npj_copies:
        shutil.copy2(WS_ROOT / src_name, npj_dir / dst_name)
    for ext in (".pdf", ".png"):
        f7 = FIG_SRC / f"Fig7_STAR_Audit_Working_Model{ext}"
        if f7.exists():
            shutil.copy2(f7, npj_dir / f7.name)

    # 5. Second Backup: Cell Press Patterns Edition
    patterns_dir = pkg_dir / "backup_CellPress_Patterns"
    patterns_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WS_ROOT / "MANUSCRIPT_GEN2_v1.0.docx", patterns_dir / "Manuscript_Patterns_Backup_v1.0_EN.docx")
    shutil.copy2(WS_ROOT / "MANUSCRIPT_GEN2_v1.0.md", patterns_dir / "Manuscript_Patterns_Backup_v1.0_EN.md")
    shutil.copy2(
        WS_ROOT / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.docx",
        patterns_dir / "Cover_Letter_Patterns_Backup_v1.0_EN.docx",
    )
    shutil.copy2(
        WS_ROOT / "COVER_LETTER_AND_EDITORIAL_RESPONSE_GEN2_v1.0.md",
        patterns_dir / "Cover_Letter_Patterns_Backup_v1.0_EN.md",
    )

    # 6. Upload manifest
    write_upload_manifest(pkg_dir)


def audit_built_package_zero_banned(pkg_dir: Path) -> None:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    hits: list[tuple[str, str]] = []
    checked = 0
    for fpath in sorted(pkg_dir.rglob("*")):
        if not fpath.is_file():
            continue
        rel = str(fpath.relative_to(pkg_dir))
        m_name = BANNED_RE.search(rel)
        if m_name:
            hits.append((rel, f"FILENAME:{m_name.group(0)}"))
        suf = fpath.suffix.lower()
        if suf in {".md", ".csv"}:
            checked += 1
            txt = fpath.read_text(encoding="utf-8-sig")
            for m in BANNED_RE.finditer(txt):
                hits.append((rel, m.group(0)))
        elif suf == ".docx":
            checked += 1
            with zipfile.ZipFile(fpath) as zf:
                root = ET.fromstring(zf.read("word/document.xml"))
                txt = "\n".join("".join(el.itertext()) for el in root.findall(".//w:body/*", ns))
            for m in BANNED_RE.finditer(txt):
                hits.append((rel, m.group(0)))
    print(f"=== PACKAGE ZERO-BANNED-TERM SCAN ({checked} text/csv/docx files inspected) ===")
    if hits:
        for rel, tok in hits[:20]:
            print(f"  [FAIL] {rel} -> {tok}")
        raise AssertionError(f"Found {len(hits)} banned term hits inside package!")
    print("  [PASS] 0 occurrences of OSF / KF2G8 / preregistered / external API / db-wal across entire package!")


def verify_desktop_chinese_docx() -> None:
    ws_zh = WS_ROOT / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.docx"
    dt_zh_main = DESKTOP_ROOT / "STAR-Audit_手稿全文中文版_审核稿.docx"

    h_ws = sha256_file(ws_zh)
    h_dt_main = sha256_file(dt_zh_main)

    print("=== ZERO-TRUST DESKTOP CHINESE MANUSCRIPT VERIFICATION ===")
    print(f"Workspace NMI ZH .docx : {ws_zh.stat().st_size:,} B | SHA256={h_ws[:16]}")
    print(f"Desktop   NMI ZH main  : {dt_zh_main.stat().st_size:,} B | SHA256={h_dt_main[:16]}")
    assert h_ws == h_dt_main, "SHA-256 mismatch on Desktop Chinese docx!"

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(dt_zh_main) as zf:
        media_files = [n for n in zf.namelist() if n.startswith("word/media/")]
        root = ET.fromstring(zf.read("word/document.xml"))
        paras = ["".join(p.itertext()) for p in root.findall(".//w:body/w:p", ns)]
        tables = root.findall(".//w:body/w:tbl", ns)
    full_text = "\n".join(paras)

    checks = {
        "NMI Slimmed Edition header & 11,818 evaluations (9,130 + 2,688)": (
            "Nature Machine Intelligence" in full_text and "11,818" in full_text and "9,130" in full_text and "2,688" in full_text
        ),
        "4 zero-call remediation modules (OA-BTL / Platt / NCBI gating / CoT-SRAD)": (
            "OA-BTL" in full_text and "Platt" in full_text and "CoT-SRAD" in full_text
        ),
        "Zero OSF / 预注册 / 无外部付费 API residue": not bool(BANNED_RE.search(full_text)),
        "Zenodo DOI 10.5281/zenodo.20574265 & GitHub SJT503/SDL-dAMD": (
            "10.5281/zenodo.20574265" in full_text and "SJT503/SDL-dAMD" in full_text
        ),
        "69 verified references incl. 5 new 2025–2026 NMI/npj benchmarks (69. Brier GW 1950)": (
            "69. Brier GW." in full_text and "10.1038/s42256-026-01266-0" in full_text and "10.1038/s41746-026-03097-0" in full_text
        ),
        "7 embedded 300-DPI figures (Figs 1–6 + Extended Data Fig. 1)": len(media_files) == 7,
        "2 native three-line Extended Data tables": len(tables) == 2,
        "6 [INSERT FIGURE 1..6 ABOUT HERE] anchors": full_text.count("ABOUT HERE]") == 6,
    }
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        assert ok, f"Desktop Chinese manuscript check failed: {label}"


def main() -> None:
    build_package(WS_PKG)
    audit_built_package_zero_banned(WS_PKG)
    if DESKTOP_PKG.exists():
        shutil.rmtree(DESKTOP_PKG)
    shutil.copytree(WS_PKG, DESKTOP_PKG)
    print(f"[OK] Built workspace NMI-first package: {WS_PKG}")
    print(f"[OK] Mirrored Desktop NMI-first package: {DESKTOP_PKG}")
    verify_desktop_chinese_docx()


if __name__ == "__main__":
    main()
