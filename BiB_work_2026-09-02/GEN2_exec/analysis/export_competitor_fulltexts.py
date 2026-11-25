import json
import os

OUT_DIR = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\GEN2_exec\analysis\benchmark_competitors"
data = json.load(open(os.path.join(OUT_DIR, "competitor_benchmarks_2024_2026.json"), encoding="utf-8"))

for d in data:
    secs = d.get("pmc_sections", [])
    sec_names = [s.get("section_title", "") for s in secs]
    print(f"PMID={d['pmid']} | PMCID={d['pmcid']} | {d['iso']} ({d['year']}) | {d['first_author']} | {d['title'][:80]} | secs={len(secs)}: {sec_names[:6]}")

# Export a markdown file containing full text sections (Abstract, Intro, Results, Discussion, Limitations) for the best 6 full-text papers
selected_pmids = ["38898292", "40957400", "41015027", "40543500", "40575123", "42746527", "40628696", "38965443"]
md_lines = ["# Full-Text Benchmark Competitor Corpus (2024-2026)\n"]
for d in data:
    if d["pmid"] in selected_pmids or (d.get("pmc_sections") and len(d["pmc_sections"]) >= 5):
        md_lines.append(f"## PMID {d['pmid']} | {d['pmcid']} | {d['first_author']} et al. ({d['year']}) - *{d['journal']}* (`{d['iso']}`)")
        md_lines.append(f"**Title:** {d['title']}")
        md_lines.append(f"**DOI:** {d['doi']}")
        md_lines.append(f"### Abstract\n{d['abstract']}\n")
        for s in d.get("pmc_sections", []):
            st = s.get("section_title", "Section")
            wc = s.get("word_count", 0)
            md_lines.append(f"### Section: {st} ({s.get('paragraph_count', 0)} paragraphs, {wc} words)")
            for idx, p in enumerate(s.get("paragraphs", []), 1):
                md_lines.append(f"[P{idx}] {p}\n")

out_md = os.path.join(OUT_DIR, "competitor_fulltexts_readable.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))
print("Saved readable fulltexts to:", out_md)
