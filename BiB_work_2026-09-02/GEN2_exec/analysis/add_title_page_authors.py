from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
MS_PATH = BASE / "MANUSCRIPT_GEN2_v1.0.md"
ms = MS_PATH.read_text(encoding="utf-8")

title_line = "# Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery\n\n## Highlights"
title_with_authors = """# Auditing and rectifying reasoning, tournament, and grounding failures in autonomous AI scientific discovery

**Jiangtao Sheng$^{1,\\#,\\*}$, Xueer Liu$^{1}$, Runmin Lin$^{1}$, Qiaochu Sun$^{1}$, Xiaoxuan Chen$^{1}$, Kangsheng Li$^{1}$, and Weiqiang Chen$^{2,\\*}$**

$^{1}$Department of Microbiology and Immunology, Shantou University Medical College, 22 Xinling Road, Shantou 515041, Guangdong, China

$^{2}$Department of Neurosurgery, The First Affiliated Hospital of Shantou University Medical College, 57 Changping Road, Shantou 515041, Guangdong, China

$^{\\text{#}}$Lead contact: Jiangtao Sheng (jtsheng@stu.edu.cn)

$^{\\text{*}}$Correspondence: Jiangtao Sheng (jtsheng@stu.edu.cn; ORCID: 0000-0003-2438-7345); Weiqiang Chen (wqchen@stu.edu.cn; ORCID: 0000-0002-2612-0890)

## Highlights"""

if "Xueer Liu" not in ms[:800]:
    assert title_line in ms
    ms = ms.replace(title_line, title_with_authors, 1)
    MS_PATH.write_text(ms, encoding="utf-8")
    print("Added Title Page author/affiliation/correspondence block to MANUSCRIPT_GEN2_v1.0.md")
else:
    print("Author block already present in MANUSCRIPT_GEN2_v1.0.md")
