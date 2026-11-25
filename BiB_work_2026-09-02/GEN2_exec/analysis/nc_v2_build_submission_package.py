from gate import gate, canary_gate, retry_limit
import os
import pathlib
import re
import shutil
import sys
import pandas as pd
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

gate(__file__)

BASE = pathlib.Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
ANAL = BASE / "GEN2_exec" / "analysis"
FIG_SRC = BASE / "GEN2_exec" / "figures_NC_v2_planA"
PKG = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.1_PlanA"

REF_MS_DOCX = pathlib.Path(r"C:\Users\sheng\.claude\skills\manuscript-submission-docx-format\templates\reference_manuscript.docx")
REF_CL_DOCX = pathlib.Path(r"C:\Users\sheng\.claude\skills\manuscript-submission-docx-format\templates\reference_cover_letter.docx")

SUP_DIGITS = str.maketrans("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
SUB_DIGITS = str.maketrans("+-0123456789", "₊₋₀₁₂₃₄₅₆₇₈₉")


def mini_task():
    assert (BASE / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0.md").exists()
    assert (FIG_SRC / "Source_Data_NC_v2.0.xlsx").exists()
    return True


canary_gate(lambda: mini_task(), "Verify NC v2.1 Plan-A MD and Source Data XLSX exist")


def copy_pkg_asset(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        print(f"[skip] {dst.name} — 已存在，保留现有版本")
        return
    shutil.copy2(src, dst)


def clean_math_expr(expr: str) -> str:
    s = expr.strip()
    # Specific structured expressions first
    s = s.replace(r"\mathcal{L}(\boldsymbol{\theta}, \gamma)", "L(θ, γ)")
    s = s.replace(r"\boldsymbol{\theta}", "θ")
    s = s.replace(r"\boldsymbol{\phi}", "ϕ")
    s = s.replace(r"\mathbf{x}", "x")
    s = s.replace(r"\mathbf{g}", "g")
    s = s.replace(r"\mathbf{H}", "H")
    s = s.replace(r"\mathbf{I}", "I")
    s = s.replace(r"\mathbf{0}", "0")
    s = s.replace(r"\mathbb{R}", "R")
    s = re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", lambda m: "[" + m.group(1).replace(r"\\", "; ").replace("&", ",") + "]", s)
    s = re.sub(r"\\binom\{([^\}]+)\}\{([^\}]+)\}", r"C(\1, \2)", s)
    s = re.sub(r"\\frac\{([^\}]+)\}\{([^\}]+)\}", r"(\1/\2)", s)
    s = re.sub(r"\\sqrt\{\[H\^\{-1\}\]\s*_\{([^\}]+)\}\}", r"sqrt(H⁻¹_\1)", s)
    s = re.sub(r"\\sqrt\{([^\}]+)\}", r"sqrt(\1)", s)

    # Hats and bars
    s = re.sub(r"\\hat\{\\gamma\}", "γ̂", s)
    s = re.sub(r"\\bar\{\\gamma\}", "γ̄", s)
    s = re.sub(r"\\hat\{\\beta\}", "β̂", s)
    s = re.sub(r"\\hat\{\\theta\}", "θ̂", s)
    s = re.sub(r"\\hat\{p\}", "p̂", s)
    s = re.sub(r"\\tilde\{c\}", "c̃", s)
    s = re.sub(r"\\bar\{J\}", "J̄", s)
    s = re.sub(r"\\bar\{y\}", "ȳ", s)
    s = re.sub(r"\\bar\{p\}", "p̄", s)

    # \text{...}
    s = re.sub(r"\\text\{([^\}]+)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^\}]+)\}", r"\1", s)

    # Powers of 10 and superscripts
    s = re.sub(r"10\^\{([+\-0-9]+)\}", lambda m: "^" + m.group(1) + "^" if False else "10^" + m.group(1) + "^", s)
    s = re.sub(r"\^\{([^\}]+)\}", lambda m: "^" + m.group(1).replace(r"\*", "*").replace(r"\top", "T") + "^", s)
    s = re.sub(r"_\{([^\}]+)\}", lambda m: "~" + m.group(1) + "~", s)
    s = re.sub(r"\^([0-9+\-*])", r"^\1^", s)
    s = re.sub(r"_([A-Za-z0-9])(?![A-Za-z0-9])", r"~\1~", s)

    # Greek & operators
    rep_map = [
        (r"\sum", "Σ"), (r"\prod", "Π"), (r"\ln", "ln"), (r"\log", "log"),
        (r"\min", "min"), (r"\max", "max"), (r"\le", "≤"), (r"\leq", "≤"),
        (r"\ge", "≥"), (r"\geq", "≥"), (r"\neq", "≠"), (r"\ne", "≠"),
        (r"\pm", "±"), (r"\times", "×"), (r"\cdot", "·"), (r"\to", " to "),
        (r"\Rightarrow", "=>"), (r"\in", " in "), (r"\dots", "..."),
        (r"\quad", "  "), (r"\left", ""), (r"\right", ""),
        (r"\gamma", "γ"), (r"\theta", "θ"), (r"\beta", "β"), (r"\alpha", "α"),
        (r"\lambda", "λ"), (r"\sigma", "σ"), (r"\tau", "τ"), (r"\kappa", "κ"),
        (r"\chi", "χ"), (r"\Delta", "Δ"), (r"\pi", "π"), (r"\phi", "ϕ"),
        (r"\infty", "∞"), (r"\%", "%"), (r"\*", "*"), (r"\|", "|"),
        ("{", ""), ("}", ""), ("\\", ""),
    ]
    for k, v in rep_map:
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def sanitize_line_for_docx(line: str) -> str:
    txt = line
    # Block math $$...$$
    txt = re.sub(r"\$\$([^\$]+)\$\$", lambda m: clean_math_expr(m.group(1)), txt)
    # Inline math $...$
    txt = re.sub(r"\$([^\$]+)\$", lambda m: clean_math_expr(m.group(1)), txt)
    # Inline code backticks `...` -> plain text
    txt = re.sub(r"`([^`]+)`", r"\1", txt)
    # Replace U+2212 with en-dash for SimSun compatibility
    txt = txt.replace("\u2212", "–")
    # Convert any leftover Unicode superscripts/subscripts to ^...^ / ~...~
    txt = re.sub(r"[⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + m.group(0).translate(str.maketrans("⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "+-0123456789")) + "^", txt)
    txt = re.sub(r"[₊₋₀₁₂₃₄₅₆₇₈₉]+", lambda m: "~" + m.group(0).translate(str.maketrans("₊₋₀₁₂₃₄₅₆₇₈₉", "+-0123456789")) + "~", txt)
    return txt


_MD_TOKEN_RE = re.compile(r"(\*\*(?:[^*\n]|\*[^*\n]+\*)+\*\*|\*[^*\n]+\*)")
_SUPSUB_RE = re.compile(r"(\^[^\^\n]+\^|~[^~\n]+~)")


def format_paragraph_locked(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.alignment = align


def add_clean_runs(p, raw_text: str, east_asia_font: str = "SimSun", force_bold: bool = False, font_size_pt=None):
    txt = sanitize_line_for_docx(raw_text)
    AST_TOK = "\x00LITAST\x00"
    txt = txt.replace(r"\*", AST_TOK)
    # Protect literal significance/author asterisks: (*), q = 0.03096*, ^1,*^, *Correspondence, (*)
    txt = re.sub(r"\(\*\)", f"({AST_TOK})", txt)
    txt = re.sub(r"(\d)\*(?!\*)", rf"\1{AST_TOK}", txt)
    txt = re.sub(r"\^\*\^", f"^{AST_TOK}^", txt)
    txt = re.sub(r"\^([0-9,]+)\*\^", rf"^\1{AST_TOK}^", txt)
    txt = re.sub(r"(?<!\*)\*(?=\s*(?:Correspondence|通讯作者|Corresponding|p\s*[<≤=]))", AST_TOK, txt)

    def emit_leaf(chunk: str, b_flag: bool, i_flag: bool):
        if not chunk:
            return
        for sp in _SUPSUB_RE.split(chunk):
            if not sp:
                continue
            is_sup = sp.startswith("^") and sp.endswith("^") and len(sp) > 2
            is_sub = sp.startswith("~") and sp.endswith("~") and len(sp) > 2
            val = sp[1:-1] if (is_sup or is_sub) else sp
            # Strip any stray unrendered *, ^, ~
            val = val.replace("*", "").replace("^", "").replace("~", "")
            val = val.replace(AST_TOK, "*")
            if not val:
                continue
            r = p.add_run(val)
            r.bold = bool(b_flag or force_bold)
            r.italic = bool(i_flag)
            if is_sup:
                r.font.superscript = True
            if is_sub:
                r.font.subscript = True
            r.font.name = "Times New Roman"
            r._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), east_asia_font)
            if font_size_pt is not None:
                r.font.size = Pt(font_size_pt)

    for tok in _MD_TOKEN_RE.split(txt):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            inner = tok[2:-2]
            for ip in re.split(r"(\*[^*\n]+\*)", inner):
                if not ip:
                    continue
                if ip.startswith("*") and ip.endswith("*") and len(ip) > 2:
                    emit_leaf(ip[1:-1], True, True)
                else:
                    emit_leaf(ip, True, False)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            emit_leaf(tok[1:-1], False, True)
        else:
            emit_leaf(tok, False, False)


def render_md_to_docx(
    md_path: pathlib.Path,
    out_docx: pathlib.Path,
    ref_docx: pathlib.Path,
    embed_fig_map: dict = None,
    is_cover_letter: bool = False,
):
    doc = Document(str(ref_docx)) if ref_docx.exists() else Document()
    # Clear template body paragraphs/tables
    for tbl in list(doc.tables):
        tbl._element.getparent().remove(tbl._element)
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)

    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue

        # Markdown pipe table block
        if s.startswith("|") and s.endswith("|"):
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i].strip())
                i += 1
            rows_parsed = []
            for tl in tbl_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                if all(re.match(r"^[:\-]+$", c) for c in cells if c):
                    continue
                rows_parsed.append(cells)
            if rows_parsed:
                n_cols = max(len(r) for r in rows_parsed)
                wtbl = doc.add_table(rows=len(rows_parsed), cols=n_cols)
                if "Table Grid" in [st.name for st in doc.styles]:
                    wtbl.style = "Table Grid"
                for r_idx, r_cells in enumerate(rows_parsed):
                    for c_idx in range(n_cols):
                        val = r_cells[c_idx] if c_idx < len(r_cells) else ""
                        cp = wtbl.cell(r_idx, c_idx).paragraphs[0]
                        cp.text = ""
                        cp.paragraph_format.line_spacing = 1.15
                        cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        add_clean_runs(cp, val, force_bold=(r_idx == 0), font_size_pt=8.5)
            continue

        # Embedded figure hook (for SI or merged review edition)
        if embed_fig_map and s in embed_fig_map:
            img_p = embed_fig_map[s]
            if img_p.exists():
                pic_para = doc.add_paragraph()
                format_paragraph_locked(pic_para, align=WD_ALIGN_PARAGRAPH.CENTER)
                pic_para.add_run().add_picture(str(img_p), width=Inches(6.2))
            i += 1
            continue

        # Headings
        m_h = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m_h:
            lvl = min(len(m_h.group(1)), 3)
            h_txt = m_h.group(2).strip()
            sname = f"Heading {lvl}"
            p = doc.add_paragraph(style=sname if sname in [st.name for st in doc.styles] else None)
            format_paragraph_locked(p)
            add_clean_runs(p, h_txt, force_bold=True)
            i += 1
            continue

        # Bullet or blockquote lines
        if s.startswith("- "):
            s_clean = "• " + s[2:].strip()
        elif s.startswith("> "):
            s_clean = s[2:].strip()
        else:
            s_clean = s

        bstyle = "Body Text" if (is_cover_letter and "Body Text" in [st.name for st in doc.styles]) else None
        p = doc.add_paragraph(style=bstyle)
        format_paragraph_locked(p)
        add_clean_runs(p, s_clean)
        i += 1

    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    assert_zero_garble(out_docx)
    print(f"Saved & verified zero-garble DOCX -> {out_docx}")


def assert_zero_garble(docx_path: pathlib.Path):
    d = Document(str(docx_path))
    full_txt = "\n".join(
        [p.text for p in d.paragraphs]
        + [c.text for t in d.tables for r in t.rows for c in r.cells]
    )
    assert "$" not in full_txt, f"Raw '$' leaked in {docx_path.name}"
    bs_hits = re.findall(r"\\[a-zA-Z\*]+", full_txt)
    assert not bs_hits, f"Raw backslash command leaked in {docx_path.name}: {bs_hits[:5]}"
    sym_hits = re.findall(r"[\{\}\^`]", full_txt)
    assert not sym_hits, f"Raw braces/caret/backtick leaked in {docx_path.name}: {sym_hits[:5]}"
    hdr_hits = re.findall(r"(?m)^#+\s", full_txt)
    assert not hdr_hits, f"Raw '#' heading leaked in {docx_path.name}: {hdr_hits[:5]}"
    md_bold = re.findall(r"\*\*", full_txt)
    assert not md_bold, f"Unrendered '**' leaked in {docx_path.name}"


def export_supp_tables_xlsx(si_md: pathlib.Path, out_xlsx: pathlib.Path):
    txt = si_md.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^###\s+(Supplementary Table\s+\d+\..*)$", txt)
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(str(out_xlsx), engine="openpyxl") as writer:
        for idx in range(1, len(parts), 2):
            title_line = sanitize_line_for_docx(parts[idx].strip()).replace("**", "").replace("*", "")
            m_num = re.search(r"Supplementary Table\s+(\d+)", title_line)
            s_num = m_num.group(1) if m_num else str((idx + 1) // 2)
            sheet_name = f"Supplementary_Table_{s_num}"
            body = parts[idx + 1]
            # Parse all markdown tables inside this Supplementary Table section
            all_rows = [[title_line]]
            for block in re.findall(r"((?:^\|.*\|$\n?)+)", body, flags=re.M):
                t_lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
                for tl in t_lines:
                    cells = [
                        sanitize_line_for_docx(c.strip()).replace("**", "").replace("*", "").replace("^", "").replace("~", "")
                        for c in tl.strip("|").split("|")
                    ]
                    if all(re.match(r"^[:\-]+$", c) for c in cells if c):
                        continue
                    all_rows.append(cells)
                all_rows.append([])
            pd.DataFrame(all_rows).to_excel(writer, sheet_name=sheet_name, index=False, header=False)
    print(f"Saved 7-sheet Supplementary Tables workbook -> {out_xlsx}")


@retry_limit(2)
def main():
    # 1. Copy Main Figures 1-6 & Supplementary Figures 1-4 & Source Data / Audits / Demo
    main_fig_stems = [
        "Fig1_Audit_Remediation_Architecture",
        "Fig2_Dim1_Trojan_Horse_Citations",
        "Fig3_Dim2_Reasoning_vs_Memorization",
        "Fig4_Dim3_Dim5_Primacy_and_NLI",
        "Fig5_Dim4_Dim6_Reasoning_Paradox",
        "Fig6_Audit_Guided_Rectification_Impact",
    ]
    for stem in main_fig_stems:
        for ext in [".pdf", ".png", ".svg"]:
            src = FIG_SRC / f"{stem}{ext}"
            assert src.exists(), f"Missing main figure asset: {src}"
            copy_pkg_asset(src, PKG / "02_Figures_Main" / f"{stem}{ext}")

    supp_stems = [
        "Supplementary_Fig_1_Module3_ClosedLoop_and_ExpertAudit",
        "Supplementary_Fig_2_ExpC_Starvation_Ablation_and_Grid",
        "Supplementary_Fig_3_OABTL_Identifiability_and_Sensitivity",
        "Supplementary_Fig_4_MultiModel_Calibration_NLI_and_Latency",
    ]
    for dst_stem in supp_stems:
        for ext in [".pdf", ".png", ".svg"]:
            src = FIG_SRC / f"{dst_stem}{ext}"
            assert src.exists(), f"Missing supp figure asset: {src}"
            copy_pkg_asset(src, PKG / "03_Supplementary" / f"{dst_stem}{ext}")

    shutil.copy2(FIG_SRC / "Source_Data_NC_v2.0.xlsx", PKG / "04_Source_Data_and_Tables" / "Source_Data_NC_v2.0.xlsx")
    shutil.copy2(ANAL / "expert_audit_tier2_100_annotated.csv", PKG / "04_Source_Data_and_Tables" / "expert_audit_tier2_100_annotated.csv")
    shutil.copy2(ANAL / "expert_audit_nli_100_annotated.csv", PKG / "04_Source_Data_and_Tables" / "expert_audit_nli_100_annotated.csv")
    shutil.copy2(BASE / "GEN2_exec" / "star_audit_demo.py", PKG / "04_Source_Data_and_Tables" / "star_audit_demo.py")

    # 2. Render DOCX files
    en_md = PKG / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_submission_EN.md"
    zh_md = PKG / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_CN_review.md"
    si_md = PKG / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.md"
    cl_en_md = PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_submission_EN.md"
    cl_zh_md = PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_CN_review.md"

    render_md_to_docx(en_md, PKG / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_submission_EN.docx", REF_MS_DOCX)
    render_md_to_docx(zh_md, PKG / "01_Manuscript" / "Manuscript_NCOMMS_AgenticAI_v2.0_CN_review.docx", REF_MS_DOCX)

    # Also render Merged Review Edition with Figures 1-6 embedded inline above each Figure Legend
    merged_md_txt = en_md.read_text(encoding="utf-8")
    for idx in range(1, 7):
        merged_md_txt = merged_md_txt.replace(f"**Figure {idx}.", f"[EMBED_MAIN_FIG_{idx}]\n\n**Figure {idx}.", 1)
    tmp_merged_md = ANAL / "_tmp_merged_en.md"
    tmp_merged_md.write_text(merged_md_txt, encoding="utf-8")
    main_embed_map = {
        f"[EMBED_MAIN_FIG_{idx}]": PKG / "02_Figures_Main" / f"{stem}.png"
        for idx, stem in enumerate(main_fig_stems, 1)
    }
    render_md_to_docx(
        tmp_merged_md,
        PKG / "01_Manuscript" / "Merged_Review_With_Figures_NCOMMS_AgenticAI_v2.0_EN.docx",
        REF_MS_DOCX,
        embed_fig_map=main_embed_map,
    )
    tmp_merged_md.unlink(missing_ok=True)

    si_embed_map = {
        "[EMBED_SUPP_FIG_1]": PKG / "03_Supplementary" / "Supplementary_Fig_1_Module3_ClosedLoop_and_ExpertAudit.png",
        "[EMBED_SUPP_FIG_2]": PKG / "03_Supplementary" / "Supplementary_Fig_2_ExpC_Starvation_Ablation_and_Grid.png",
        "[EMBED_SUPP_FIG_3]": PKG / "03_Supplementary" / "Supplementary_Fig_3_OABTL_Identifiability_and_Sensitivity.png",
        "[EMBED_SUPP_FIG_4]": PKG / "03_Supplementary" / "Supplementary_Fig_4_MultiModel_Calibration_NLI_and_Latency.png",
    }
    render_md_to_docx(si_md, PKG / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.docx", REF_MS_DOCX, embed_fig_map=si_embed_map)
    render_md_to_docx(cl_en_md, PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_submission_EN.docx", REF_CL_DOCX, is_cover_letter=True)
    render_md_to_docx(cl_zh_md, PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_CN_review.docx", REF_CL_DOCX, is_cover_letter=True)

    # 3. Export Supplementary_Tables_1_to_7_NC_v2.0.xlsx & standalone Tables_1_to_2_NC_v2.0.docx
    export_supp_tables_xlsx(si_md, PKG / "04_Source_Data_and_Tables" / "Supplementary_Tables_1_to_7_NC_v2.0.xlsx")

    en_txt = en_md.read_text(encoding="utf-8")
    if "## Tables" in en_txt:
        tbl_sec = "# Auditing and rectifying reasoning, ranking, and grounding biases in agentic scientific discovery — Main Tables 1–2\n\n## Tables\n" + en_txt.split("## Tables", 1)[1]
        tbl_tmp_md = ANAL / "_tmp_tables_1_to_2.md"
        tbl_tmp_md.write_text(tbl_sec, encoding="utf-8")
        render_md_to_docx(tbl_tmp_md, PKG / "04_Source_Data_and_Tables" / "Tables_1_to_2_NC_v2.0.docx", REF_MS_DOCX)
        tbl_tmp_md.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
