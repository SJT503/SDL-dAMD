#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Generates:
1. Nature Portfolio English Submission Package (Prioritizing npj Digital Medicine & Nature Machine Intelligence):
   - D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md & .docx
   - D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\COVER_LETTER_GEN2_NaturePortfolio_v1.0.md & .docx
2. Complete, Unabridged Chinese Review Edition on the User's Desktop (C:\Users\sheng\Desktop\):
   - C:\Users\sheng\Desktop\STAR-Audit_手稿全文中文版_审核稿.md
   - C:\Users\sheng\Desktop\STAR-Audit_手稿全文中文版_审核稿.docx (with all 7 figures & 2 tables embedded)
   - C:\Users\sheng\Desktop\STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx
"""

import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02"
FIG_DIR = os.path.join(BASE, "GEN2_exec", "figures")
DESKTOP = r"C:\Users\sheng\Desktop"


def set_cell_Borders(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge, edge_data in kwargs.items():
        if edge_data:
            tag = "w:{}".format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ["val", "color", "sz", "space"]:
                if key in edge_data:
                    element.set(qn("w:{}".format(key)), str(edge_data[key]))


def format_run_font(run, size_pt=12, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")
    rFonts.set(qn("w:eastAsia"), "Times New Roman")


def sanitize_latex_to_supsub(text: str) -> str:
    s = text

    def clean_backtick(m):
        inner = m.group(1)
        return inner.replace("_", "‑")

    s = re.sub(r"`([^`]+)`", clean_backtick, s)
    s = re.sub(r"\$\$([^$]+)\$\$", r"\1", s)
    s = re.sub(r"\$([^$]+)\$", r"\1", s)

    s = s.replace(r"\begin{bmatrix} \boldsymbol{\theta} \\ 0 \end{bmatrix}", "[θ; 0]")
    s = s.replace(r"\begin{bmatrix} \mathbf{I}_M & \mathbf{0} \\ \mathbf{0}^\top & 0 \end{bmatrix}", "diag(I⟦SUB:M⟧, 0)")
    s = re.sub(r"\\frac\{([^\}]+)\}\{([^\}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\binom\{([^\}]+)\}\{([^\}]+)\}", r"C(\1, \2)", s)
    s = re.sub(r"\\sqrt\{\[H\^\{-1\}\]\s*_\{([^\}]+)\}\}", r"sqrt([H⟦SUP:-1⟧]⟦SUB:\1⟧)", s)
    s = re.sub(r"\\sqrt\{([^\}]+)\}", r"sqrt(\1)", s)

    s = re.sub(r"\\text\{--\}", "–", s)
    s = re.sub(r"\\text\{\s*\}", " ", s)
    s = re.sub(r"\\text\{([^\}]+)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^\}]+)\}", r"\1", s)
    s = re.sub(r"\\mathbf\{([^\}]+)\}", r"**\1**", s)
    s = re.sub(r"\\boldsymbol\{\\theta\}", "**θ**", s)
    s = re.sub(r"\\boldsymbol\{\\phi\}", "**φ**", s)
    s = re.sub(r"\\boldsymbol\{([^\}]+)\}", r"**\1**", s)
    s = re.sub(r"\\mathcal\{([^\}]+)\}", r"\1", s)
    s = re.sub(r"\\mathbb\{R\}", "R", s)
    s = re.sub(r"\\hat\{\\beta\}", "β̂", s)
    s = re.sub(r"\\hat\{\\gamma\}", "γ̂", s)
    s = re.sub(r"\\hat\{\\theta\}", "θ̂", s)
    s = re.sub(r"\\hat\{\\phi\}", "φ̂", s)
    s = re.sub(r"\\hat\{p\}", "p̂", s)
    s = re.sub(r"\\bar\{J\}", "J̄", s)
    s = re.sub(r"\\bar\{y\}", "ȳ", s)
    s = re.sub(r"\\bar\{p\}", "p̄", s)
    s = re.sub(r"\\tilde\{c\}", "c̃", s)

    s = s.replace(r"\left[", "[").replace(r"\right]", "]")
    s = s.replace(r"\left(", "(").replace(r"\right)", ")")
    s = s.replace(r"\left\{", "{").replace(r"\right\}", "}")
    s = s.replace(r"\left|", "|").replace(r"\right|", "|")
    s = s.replace(r"\|", "||")
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = s.replace(r"\%", "%").replace(r"\_", "_").replace(r"\#", "#").replace(r"\*", "*")
    s = s.replace(r"\quad", "   ").replace(r"\;", " ").replace(r"\,", " ")
    s = s.replace(r"\dots", "...").replace(r"\cdots", "...").replace(r"\cdot", "·")
    s = s.replace(r"\Rightarrow", "⇒").replace(r"\top", "T").replace(r"\to", "→").replace(r"\mid", "|")
    s = s.replace(r"\infty", "∞").replace(r"\in", "∈").replace(r"\cup", "∪").replace(r"\cap", "∩")
    s = s.replace(r"\times", "×").replace(r"\pm", "±").replace(r"\neq", "≠")
    s = s.replace(r"\ge", "≥").replace(r"\le", "≤").replace(r"\sim", "≈")
    s = s.replace(r"\ln", "ln").replace(r"\log", "log").replace(r"\min", "min").replace(r"\max", "max")
    s = s.replace(r"\sum", "∑").replace(r"\prod", "∏")
    s = s.replace(r"\Delta", "Δ").replace(r"\chi", "χ").replace(r"\beta", "β")
    s = s.replace(r"\gamma", "γ").replace(r"\theta", "θ").replace(r"\pi", "π")
    s = s.replace(r"\sigma", "σ").replace(r"\lambda", "λ").replace(r"\alpha", "α")
    s = s.replace(r"\tau", "τ").replace(r"\phi", "φ")

    s = re.sub(r"_\{([a-zA-Z0-9]+)_([a-zA-Z0-9]+)\}", r"⟦SUB:\1\2⟧", s)
    s = re.sub(r"\^\{([^\}]+)\}", r"⟦SUP:\1⟧", s)
    s = re.sub(r"_\{([^\}]+)\}", r"⟦SUB:\1⟧", s)
    s = re.sub(r"\^\*(?!\*)", "⟦SUP:AST⟧", s)
    s = re.sub(r"\^\*(?=\*\*)", "⟦SUP:AST⟧", s)
    s = re.sub(r"\^([+\-0-9a-zA-Z\#]+)", r"⟦SUP:\1⟧", s)
    s = re.sub(r"_([+\-0-9a-zA-Z∞]+)", r"⟦SUB:\1⟧", s)
    s = re.sub(r"⟦SUP:([^⟧]*)\*([^⟧]*)⟧", r"⟦SUP:\1AST\2⟧", s)
    return s


def add_formatted_runs(p, text, size_pt=12, default_bold=False):
    clean = sanitize_latex_to_supsub(text)
    tokens = re.split(r"(\*\*(?:[^*]|\*[^*]+\*)+\*\*|\*[^*]+\*)", clean)
    for tok in tokens:
        if not tok:
            continue
        is_b = default_bold
        is_i = False
        inner = tok
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            is_b = True
            inner = tok[2:-2]
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            is_i = True
            inner = tok[1:-1]
        inner = inner.replace("**", "")
        sub_parts = re.split(r"(⟦SUP:[^⟧]+⟧|⟦SUB:[^⟧]+⟧)", inner)
        for sp in sub_parts:
            if not sp:
                continue
            if sp.startswith("⟦SUP:") and sp.endswith("⟧"):
                r = p.add_run(sp[5:-1].replace("AST", "*"))
                format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)
                r.font.superscript = True
            elif sp.startswith("⟦SUB:") and sp.endswith("⟧"):
                r = p.add_run(sp[5:-1].replace("AST", "*"))
                format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)
                r.font.subscript = True
            else:
                r = p.add_run(sp)
                format_run_font(r, size_pt=size_pt, bold=is_b, italic=is_i)


def create_base_doc():
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.paragraph_format.line_spacing = 2.0
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(0)
    return doc


def add_heading_para(doc, text, level=1):
    style_name = "Heading 1" if level <= 1 else ("Heading 2" if level == 2 else "Heading 3")
    p = doc.add_paragraph(style=style_name)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(18 if level == 0 else (8 if level <= 2 else 6))
    p.paragraph_format.space_after = Pt(4)
    sz = 20 if level == 0 else (16 if level == 1 else (14 if level == 2 else 12))
    add_formatted_runs(p, text, size_pt=sz, default_bold=True)
    return p


def add_body_para(doc, text, justify=True, indent_first=False, line_spacing=2.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    if indent_first:
        p.paragraph_format.first_line_indent = Inches(0.3)
    add_formatted_runs(p, text, size_pt=12, default_bold=False)
    return p


def add_three_line_table(doc, rows_md):
    hdr = [c.strip() for c in rows_md[0].strip("|").split("|")]
    body = [[c.strip() for c in r.strip("|").split("|")] for r in rows_md[2:]]
    tbl = doc.add_table(rows=1 + len(body), cols=len(hdr))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    top_b = {"val": "single", "sz": 12, "color": "000000"}
    mid_b = {"val": "single", "sz": 6, "color": "000000"}
    bot_b = {"val": "single", "sz": 12, "color": "000000"}

    for j, h_text in enumerate(hdr):
        cell = tbl.rows[0].cells[j]
        set_cell_Borders(cell, top=top_b, bottom=mid_b)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        add_formatted_runs(p, h_text, size_pt=9.5, default_bold=True)

    for i, row_vals in enumerate(body):
        is_last = i == len(body) - 1
        for j, val in enumerate(row_vals):
            if j >= len(hdr):
                continue
            cell = tbl.rows[i + 1].cells[j]
            set_cell_Borders(cell, bottom=bot_b if is_last else None)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_runs(p, val, size_pt=9.0, default_bold=False)


def render_markdown_to_docx(md_path, docx_path, embed_figures=False, zh_mode=False):
    doc = create_base_doc()
    lines = open(md_path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if not ln or ln == "---":
            i += 1
            continue
        if ln.startswith("# ") and not ln.startswith("## "):
            add_heading_para(doc, ln[2:].strip(), level=0)
            i += 1
            continue
        if ln.startswith("## "):
            add_heading_para(doc, ln[3:].strip(), level=1)
            i += 1
            continue
        if ln.startswith("### "):
            add_heading_para(doc, ln[4:].strip(), level=2)
            i += 1
            continue
        if ln.startswith("#### "):
            add_heading_para(doc, ln[5:].strip(), level=3)
            i += 1
            continue
        if ln.startswith("$$") and ln.endswith("$$"):
            add_body_para(doc, ln.strip("$"), justify=True)
            i += 1
            continue
        if ln.startswith("|"):
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i].strip())
                i += 1
            if len(tbl_lines) >= 3:
                add_three_line_table(doc, tbl_lines)
            continue
        if ln.startswith("- "):
            add_body_para(doc, "• " + ln[2:].strip(), justify=True)
            i += 1
            continue
        add_body_para(doc, ln, justify=True)
        i += 1

    if embed_figures:
        add_heading_para(doc, "附图（Figures 1–7 高清主图）" if zh_mode else "Figures", level=1)
        fig_files = [
            ("图 1 (Figure 1)" if zh_mode else "Figure 1", "Fig1_Audit_Remediation_Architecture.png"),
            ("图 2 (Figure 2)" if zh_mode else "Figure 2", "Fig2_Dim1_Trojan_Horse_Citations.png"),
            ("图 3 (Figure 3)" if zh_mode else "Figure 3", "Fig3_Dim2_Reasoning_vs_Memorization.png"),
            ("图 4 (Figure 4)" if zh_mode else "Figure 4", "Fig4_Dim3_Dim5_Primacy_and_NLI.png"),
            ("图 5 (Figure 5)" if zh_mode else "Figure 5", "Fig5_Dim4_Dim6_Reasoning_Paradox.png"),
            ("图 6 (Figure 6)" if zh_mode else "Figure 6", "Fig6_Audit_Guided_Rectification_Impact.png"),
            ("图 7 (Figure 7)" if zh_mode else "Figure 7", "Fig7_STAR_Audit_Working_Model.png"),
        ]
        for fig_label, fname in fig_files:
            fpath = os.path.join(FIG_DIR, fname)
            if os.path.exists(fpath):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_img.paragraph_format.line_spacing = 2.0
                r_img = p_img.add_run()
                r_img.font.name = "Times New Roman"
                r_img.add_picture(fpath, width=Inches(6.4))
                cap = f"**{fig_label}.** 多面板高清主图（完整图注见上文“图注”一节）。" if zh_mode else f"**{fig_label}.** Multi-panel main figure (see Figure Legends for full description)."
                add_body_para(doc, cap, justify=True)

    doc.save(docx_path)
    print("Saved Word document:", docx_path)


def build_all():
    nat_md_path = os.path.join(BASE, "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md")
    nat_docx_path = os.path.join(BASE, "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.docx")
    with open(nat_md_path, "r", encoding="utf-8") as f:
        nat_md = f.read()

    # 1. Sync Cell Press Patterns Backup Edition (MANUSCRIPT_GEN2_v1.0.md) from Nature Portfolio Edition
    idx_intro = nat_md.index("## Introduction")
    nat_body = nat_md[idx_intro:]
    pat_body = nat_body.replace("### Methodological scope boundaries and operational governance", "## Limitations of the Study")
    pat_body = pat_body.replace("## Methods", "## STAR Methods")
    pat_body = re.sub(r"\n## Data availability\n.*?\n(?=## Acknowledgments\n)", "\n", pat_body, flags=re.S)
    pat_body = pat_body.replace("## Competing interests", "## Declaration of Interests")

    pat_frontmatter = """# Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery

**Jiangtao Sheng$^{1,\\#,\\*}$, Xueer Liu$^{1}$, Runmin Lin$^{1}$, Qiaochu Sun$^{1}$, Xiaoxuan Chen$^{1}$, Kangsheng Li$^{1}$, and Weiqiang Chen$^{2,\\*}$**

$^{1}$Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China

$^{2}$Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China

$^{\\text{#}}$Lead contact: Jiangtao Sheng (jtsheng@stu.edu.cn)

$^{\\text{*}}$Correspondence: Jiangtao Sheng (jtsheng@stu.edu.cn; ORCID: 0000-0003-2438-7345); Weiqiang Chen (wqchen@stu.edu.cn; ORCID: 0000-0002-2612-0890)

## Highlights
- **STAR-Audit** evaluates 9,130 primary calls + 2,688 Gemini/Grok evaluations (11,818 total) across 136 diseases
- White-box CoT trajectory dynamics uncover the Test-Time Reasoning Paradox and enable zero-cost **CoT-SRAD**
- Real-PMID Trojan horse citations (11.9%–76.2%) and positional flips (8.9%–43.0%) generalize across 4 model families
- Four zero-cost rectification modules rescue suppressed pathways, boost Mendelian recall by 57.1%, and cut compute by 86.2%–97.3%

## The bigger picture
Autonomous artificial intelligence (AI) systems now generate therapeutic hypotheses, rank candidate mechanisms through multi-agent tournaments, and synthesize experimental protocols for wet-lab execution. While these architectures scale hypothesis generation, their internal decision reliability has remained largely unmeasured. A widespread assumption in current agentic design is that scaling test-time reasoning tokens allows frontier models to self-correct citation errors, evaluation biases, and overconfidence. Under a preregistered protocol across 136 disease contexts, we audited 9,130 primary live model invocations (35.58 million internal reasoning tokens across 8,973 white-box traces) on GLM-5.3 and DeepSeek-V4-Pro alongside 2,688 cross-ecosystem evaluations across Google Gemini (`Gemini-4-Argon-High` [`gemini-4-argon-high`] and `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`]; 1.15 million output/reasoning tokens) and xAI Grok (`Grok-4.7` and `Grok-4.7-Fast`; 450,879 native reasoning tokens), totaling 11,818 live evaluations and 37.18 million reasoning/output tokens across four sovereign frontier model families and six versioned compute tiers. Test-time chain-of-thought frequently rationalizes rather than corrects failure modes: models trial 35.8 candidate PMIDs per call to cite real PubMed identifiers that do not support their claims (11.9%–76.2% Trojan horse citations), focus 88.4%–90.6% of Decile-1 attention on Slot A to extinguish late-indexed biological pathways, and self-prune valid causal genes activated at 2.1% reasoning depth in favor of textbook syndromic attractors. Within our **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification) framework, we convert these six audit dimensions into four lightweight mathematical and architectural rectifications: Order-Adjusted Bradley–Terry–Luce ranking with Natural Language Inference contradiction filtering, Leave-One-Run-Out Platt recalibration, two-tier epistemic citation gating, and Chain-of-Thought Stream Recovery and Attractor Deconfounding (`CoT-SRAD`). Together, these deterministic operators repair ranking distortion, rescue +36 self-pruned Mendelian gene discoveries (+57.1% relative recall gain on DeepSeek-V4-Pro), restore calibration across all four model families ($\\text{ECE} \\le 0.115$ across all six models), and eliminate fabricated citations without a single extra language-model call. Embedding measurable audit-and-rectification layers into autonomous discovery pipelines ensures that experimental resources and preclinical investments rest on verified evidence rather than uncalibrated model assertions.

## Summary
Autonomous multi-agent systems combine hypothesis generation, pairwise tournaments, and literature grounding for therapeutic discovery, yet whether test-time reasoning ensures pipeline trustworthiness remains unknown. Here we present **STAR-Audit** (**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification), an OSF-preregistered (DOI: 10.17605/OSF.IO/KF2G8) evaluation and zero-cost remediation framework covering faithfulness, reasoning versus memorization, positional fairness, stability, coherence, and calibration. Auditing 9,130 primary calls (35.58 million reasoning tokens; 93.83% of output) on GLM-5.3 and DeepSeek-V4-Pro plus 2,688 cross-ecosystem evaluations on Google Gemini (Gemini-4-Argon-High/Gemini-3.8-Flash) and xAI Grok (Grok-4.7/Grok-4.7-Fast) across 136 diseases uncovers a test-time reasoning paradox: deeper chain-of-thought fails to self-correct pipeline biases. Naive checks score 96.9–100.0% of protocol PubMed identifiers as existent, whereas two-tier verification exposes 11.9–76.2% Trojan horse citations driven by 35.8 candidate identifiers dredged per call. Epistemic gating cuts ungrounded citations by 11.9–54.8 percentage points ($p \\le 0.00147$), eliminates fabricated identifiers ($q_{\\text{BH}} = 0.03096$), and reduces citation reasoning tokens by 86.2–97.3%. Tournament I exhibits a 71.3% Slot-A win rate suppressing Bucket-3 pathways ($\\chi^2 = 55.40$), while 8.9–43.0% of Tournament II pairs flip under A/B reversal and 23.3% of failed Mendelian inferences self-prune causal genes activated at 2.1% chain-of-thought depth. Four zero-call modules (Order-Adjusted Bradley–Terry–Luce ranking, Platt scaling, epistemic gating, and CoT-SRAD) rescue validated targets, cut calibration error in miscalibrated models by 50.7–89.5% ($\\text{ECE} \\le 0.115$ across all six models), and boost Mendelian recall by 57.1% ($p = 9.43 \\times 10^{-7}$).

**Keywords:** autonomous scientific discovery; large language models; test-time reasoning; Bradley–Terry–Luce tournament; citation faithfulness; confidence calibration; algorithmic rectification

"""
    pat_md_path = os.path.join(BASE, "MANUSCRIPT_GEN2_v1.0.md")
    with open(pat_md_path, "w", encoding="utf-8") as f:
        f.write(pat_frontmatter + pat_body)

    render_markdown_to_docx(nat_md_path, nat_docx_path, embed_figures=True, zh_mode=False)

    # 2. Nature Portfolio Cover Letter (Read updated COVER_LETTER_GEN2_NaturePortfolio_v1.0.md directly)
    cl_md_path = os.path.join(BASE, "COVER_LETTER_GEN2_NaturePortfolio_v1.0.md")
    cl_docx_path = os.path.join(BASE, "COVER_LETTER_GEN2_NaturePortfolio_v1.0.docx")
    with open(cl_md_path, "r", encoding="utf-8") as f:
        cl_nat = f.read()
    render_markdown_to_docx(cl_md_path, cl_docx_path, embed_figures=False, zh_mode=False)

    # 3. Complete Unabridged Chinese Manuscript & Bilingual Cover Letter (MD in workspace, DOCX in workspace + Desktop)
    import shutil
    zh_md_path = os.path.join(BASE, "STAR-Audit_手稿全文中文版_审核稿.md")
    zh_ws_docx_path = os.path.join(BASE, "STAR-Audit_手稿全文中文版_审核稿.docx")
    zh_docx_path = os.path.join(DESKTOP, "STAR-Audit_手稿全文中文版_审核稿.docx")
    zh_alt_docx_path = os.path.join(DESKTOP, "STAR-Audit_手稿全文中文版_审核稿_二轮修订版.docx")
    if os.path.exists(zh_md_path):
        render_markdown_to_docx(zh_md_path, zh_ws_docx_path, embed_figures=True, zh_mode=True)
        try:
            shutil.copy2(zh_ws_docx_path, zh_docx_path)
            print("Synced Desktop ZH Word document:", zh_docx_path)
        except PermissionError:
            shutil.copy2(zh_ws_docx_path, zh_alt_docx_path)
            print("Desktop ZH .docx is open in Word/WPS; saved updated Desktop copy to:", zh_alt_docx_path)

    cl_bilingual_md = cl_nat + """

---

# 投稿信中文对照版（供审阅：优先投递 *npj Digital Medicine* / *Nature Machine Intelligence*）

**日期：** 2026年10月29日
**手稿标题：** 自主 AI 科学发现中推理、锦标赛与文献溯源失效的审计与算法纠偏（Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery）
**目标期刊（路线 B 首选）：** *npj Digital Medicine*（中科院 1 区 Top，IF ~12.4）/ *Nature Machine Intelligence*（中科院 1 区 Top，IF ~18.8）
**通讯作者：** 盛江涛 教授（jtsheng@stu.edu.cn；主通讯作者 / Lead Contact）、陈伟强 教授（wqchen@stu.edu.cn），汕头大学医学院
**OSF 预注册：** DOI 10.17605/OSF.IO/KF2G8 | **Zenodo 归档：** DOI 10.5281/zenodo.20574265

尊敬的编辑：

我们非常荣幸地提交题为《Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery》的研究论文（Article），申请在贵刊发表。

近期，多智能体自主人工智能（AI）系统已展现出生成治疗假说、通过成对锦标赛对候选机制进行排序以及合成临床前/临床转化实验方案的强大能力（例如 Ghareeb 等，*Nature* 2026，DOI: 10.1038/s41586-026-10652-y；Gottweis 等，*Nature* 2026，DOI: 10.1038/s41586-026-10644-y）。当前推动生物医学智能体部署的核心假设是：扩大测试时思维链（test-time chain-of-thought）推理预算能够使前沿大语言模型自我纠正引文幻觉、评估偏倚和过度自信。然而，数字医学与机器智能学界目前尚缺乏一套端到端、外部锚定的方法学标准，以在投入稀缺的湿实验和临床转化资源之前，审计这些发现管线是否可信，并从算法上纠正其结构性失效模式。

为填补这一空白，我们设计并执行了 **STAR-Audit**（**S**ix-dimension **T**rustworthiness **A**udit and **R**ectification，六维可信度审计与纠偏框架）。这是一项在开放科学框架（OSF）预注册（DOI: 10.17605/OSF.IO/KF2G8）的系统审计与零成本算法修复研究，涵盖在 **GLM-5.3 与 DeepSeek-V4-Pro** 上执行的 **9,130 次真实大语言模型调用（跨越 8,973 条白盒思维链轨迹，共 35.58M 内部推理词元，占全部生成输出词元的 93.83%）**，以及在美国两大主流商业前沿模型家族——**Google Gemini（`Gemini-4-Argon-High` [`gemini-4-argon-high`] 旗舰高推理模型与 `Gemini-3.8-Flash` [`gemini-3.8-flash-tiered`] 轻量分层模型，1,344 次评估，含 1,149,908 个输出/推理词元与 12.05M 含缓存总词元）与 xAI Grok（`Grok-4.7` [`grok-4.7`，旗舰推理] 与 `Grok-4.7-Fast` [`grok-4.7-build-fast`，快速推理]，1,344 次评估，含 450,879 个原生推理词元）**——上执行的 **2,688 次跨生态系统验证评估**，全研究总计 **11,818 次真实评估（3,718 万个推理/输出词元）**，横跨 **四大主权前沿模型家族、六个精确版本化推理层级与 136 个独立生物医学疾病场景**（包括在干性年龄相关性黄斑变性 [dAMD] 与肌萎缩侧索硬化症 [ALS] 中开展的 12 次多轮端到端发现运行、跨越 14 个临床专科共 1,260 个主槽位 + 1,008 个跨生态槽位的临床引文门控试验，以及涵盖 120 种单基因孟德尔疾病的人类表型本体 [HPO] 扰动基准测试）。

本研究报告了三项主要的方法学与实证进展：

1. **跨越四大主权前沿模型家族的白盒“测试时推理悖论”（Test-Time Reasoning Paradox）机制解析：** 通过追踪 8,973 条原始白盒思维链（`reasoning_content`）轨迹并结合 2,688 次 Google `Gemini-4-Argon-High`/`Gemini-3.8-Flash` 与 xAI `Grok-4.7`/`Grok-4.7-Fast` 跨生态系统评估，我们定量证明：每次调用分配数万个内部推理词元并不能自我纠正结构性管线脆弱性。相反，缺乏外部锚定的深度思维链在推理前十分之一阶段（Decile-1）将 **88.4%–90.6% 的注意力锚定于槽位 A** 并用于合理化位置翻转（$p = 0.0254$，消耗 360 万个推理词元；在 xAI Grok 家族中，旗舰推理的 `Grok-4.7` 翻转率 **13.3%** 及分项-裁决自相矛盾率 **10.0%** 均高于快速推理的 `Grok-4.7-Fast` [8.9% 与 6.7%]）；在无防护引文生成中每次调用通过年份前缀猜测尝试 **35.82 个候选 7–8 位 PubMed 标识符**（总提及 129.4 次，伴随 390.3 次犹豫标记词/调用），直至碰撞上真实但完全偏题的论文；并在孟德尔致病基因推断中遵循 **“2.1% 瞬时识别定律”**——即在 **23.3% 已完成的假阴性列表** 中，模型早已在思维链极早期（成功调用中位深度 `t = 2.1%`）激活了真正的致病基因，却在随后的过度推敲中将其自我剪除（Self-pruned），最终回退至教科书高频综合征吸引子（`CHD7`、`KMT2D`、`FOXG1`、`VARS2`、`POLG`、`FBXL4`）。
2. **跨四大模型家族鉴定“特洛伊木马引文”（Trojan Horse Citations）与“索引顺序通路灭绝”（Index-Order Pathway Extinction）：** 我们证明，朴素的标识符存在性检查将 GLM-5.3、Google Gemini 与 xAI Grok-4.7 的实验方案引文评为 96.9% 至 100.0% 有效，而双层语义核查揭示：**主方案中 58.3% 的引文、GLM-5.3 实验 B 中 54.3% 的引文、`Gemini-4-Argon-High` 中 11.9% 的引文、`Gemini-3.8-Flash` 中 76.2% 的引文、`Grok-4.7` 中 29.8% 的引文以及 `Grok-4.7-Fast` 中 33.3% 的引文均属于“特洛伊木马引文”**（即将真实存在但主题无关的 PubMed 论文错误归因于无支撑的临床/生物学声明）。同时，我们发现在单向锦标赛 I 筛选中存在 **71.3% 的槽位 A 胜率**（$p = 4.37 \\times 10^{-148}$），该偏倚与分桶索引生成发生耦合，导致第 3 桶细胞外基质与补体通路发生 60% 的系统性灭绝（$\\chi^2 = 55.40, p = 9.33 \\times 10^{-13}$）；而在独立会话盲法 A/B 顺序反转测试中，**GLM-5.3 上 43.0% 的配对、`Gemini-4-Argon-High`/`Gemini-3.8-Flash` 上 11.1%/26.7% 的配对以及 `Grok-4.7`/`Grok-4.7-Fast` 上 13.3%/8.9% 的配对发生翻转**，并伴随 **DeBERTa-v3 NLI 自相矛盾率激增 $2.5\\times$ 至 $3.4\\times$**（$p = 1.15 \\times 10^{-5}$）。
3. **四大零成本算法级管线纠偏模块（“从审计到修复”，Audit-to-Remediation）：** 超越被动的诊断审计，我们提出了四个无需任何额外 LLM 调用（**零推理算力开销**）的轻量级数学与架构修复模块：(i) **位置偏倚校正 BTL 模型结合 NLI 分歧中和（OA-BTL）**，同时剥离首因偏倚（`GLM-5.3`）、近因偏倚（`Gemini-3.8-Flash`）与对称翻转（`Gemini-4-Argon-High`、`Grok-4.7`）中的位置截距 $\\hat{\\gamma}$，将第 3 桶通路扭曲度降低 **72.8%**，并直接挽救了被标准 BTL 淘汰的、具有人类遗传学因果验证和临床阶段试验支撑的核心治疗通路（dAMD 中的 `GAS6/MERTK` 胞葬作用、`TIMP3/MMP9` 细胞外基质重塑、`ABCA1/LIPC` 胆固醇流出及 `CD59` 膜攻击复合物防护；ALS 中的 `MMP9/LAMA1`、`MCT1/SLC16A1` 及 `CCS/ATP7A`）；(ii) **留一运行交叉验证（LORO）Platt 缩放**，在失准前沿模型上将期望校准误差（ECE）降低 **50.7% 至 89.5%**（主运行从 $0.222 \\to 0.027$；`Gemini-3.8-Flash` 从 $0.542 \\to 0.075$；`Grok-4.7` 从 $0.229 \\to 0.104$；`Grok-4.7-Fast` 从 $0.165 \\to 0.081$），同时使原生近似校准的旗舰模型 `Gemini-4-Argon-High` 预测概率均值精确对齐至 $65.4\\%$（经验准确率 $65.0\\%$；全部六款模型均处于 $\\text{ECE} \\le 0.115$ 校准带）；(iii) **双层认知引文门控（Two-Tier Epistemic Citation Gating）**，截断思维链 PMID 打捞（从 $35.8 \\to 5.0$ 个候选 PMID/调用，$p = 2.07 \\times 10^{-44}$），彻底消除伪造 PMID（$q_{\\text{BH}} = 0.0310$），将无支撑引文削减 **11.9 至 54.8 个百分点**（$p \\le 0.00147$），并将引文推理算力开销在 GLM-5.3 上降低 **86.2%**、在 Grok-4.7 上降低 **96.7%–97.3%（原生推理词元骤降 30 倍以上）**；以及 (iv) **思维链流恢复与吸引子去混杂算法（`CoT-SRAD`）**，通过过滤留一疾病交叉验证（LODO）综合征吸引子并回收被思维链自我剪除的早期候选基因，在零额外调用下挽救了 **+36 个真实的孟德尔致病基因发现**（$p = 7.07 \\times 10^{-6}$；在 DeepSeek-V4-Pro 上实现 **+57.1% 的相对召回率提升**，$p = 9.43 \\times 10^{-7}$）。

所有预注册方案、疾病金标准、验证缓存及分析脚本均已在 OSF（DOI: 10.17605/OSF.IO/KF2G8）与 GitHub（https://github.com/SJT503/SDL-dAMD，MIT 许可协议）完全公开；完整逐调用 JSONL 遥测归档已存缴于 Zenodo（DOI: 10.5281/zenodo.20574265，CC BY 4.0 协议；同行评审期间处于预发表防污染封存状态以防基准泄露至预训练爬虫，可随时向审稿人提供私密访问链接并在发表时自动完全开放）。本手稿系原创研究，未曾发表，亦未在其他期刊同时投递。全体作者均已审阅并批准本手稿，且声明不存在任何利益冲突。

此致
敬礼！

**盛江涛 博士、教授**（主通讯作者 / Lead Contact）
汕头大学医学院微生物学与免疫学教研室，中国广东省汕头市新陵路22号（515041）
电子邮箱：jtsheng@stu.edu.cn | ORCID: 0000-0003-2438-7345

**陈伟强 医学博士、教授**（共同通讯作者）
汕头大学医学院第一附属医院神经外科，中国广东省汕头市长平路57号（515041）
电子邮箱：wqchen@stu.edu.cn | ORCID: 0000-0002-2612-0890
"""
    cl_bi_md_path = os.path.join(BASE, "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.md")
    cl_bi_ws_docx_path = os.path.join(BASE, "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx")
    cl_bi_docx_path = os.path.join(DESKTOP, "STAR-Audit_投稿信_npjDigitalMed_NatMachIntell_中英对照版.docx")
    with open(cl_bi_md_path, "w", encoding="utf-8") as f:
        f.write(cl_bilingual_md)
    render_markdown_to_docx(cl_bi_md_path, cl_bi_ws_docx_path, embed_figures=False, zh_mode=True)
    shutil.copy2(cl_bi_ws_docx_path, cl_bi_docx_path)

    shutil.copy2(nat_docx_path, os.path.join(DESKTOP, "STAR-Audit_Manuscript_NaturePortfolio_v1.0.docx"))


if __name__ == "__main__":
    build_all()
