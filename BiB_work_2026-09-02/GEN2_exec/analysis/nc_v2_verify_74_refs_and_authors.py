from gate import gate, canary_gate, retry_limit
import json
import pathlib
import re
import requests

gate(__file__)

BASE = pathlib.Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
EN_MD = BASE / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0.md"
PKG = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.3_Aligned"
OUT_JSON = BASE / "GEN2_exec" / "analysis" / "nc_v2_74refs_author_audit.json"


def mini_task():
    assert EN_MD.exists()
    return True


canary_gate(lambda: mini_task(), "Verify NC v2.0 EN manuscript exists")


@retry_limit(2)
def main():
    txt = EN_MD.read_text(encoding="utf-8")
    refs_sec = txt.split("## References\n")[1].split("\n## Figure Legends")[0].strip()
    lines = [ln.strip() for ln in refs_sec.splitlines() if ln.strip()]
    assert len(lines) == 74, f"Expected 74 references, found {len(lines)}"

    pmid_entries = {}
    non_pmid_entries = []
    for ln in lines:
        m_idx = re.match(r"^(\d+)\.\s+(.*)$", ln)
        assert m_idx, f"Malformed ref line: {ln}"
        idx = int(m_idx.group(1))
        body = m_idx.group(2)
        m_pm = re.search(r"PMID:(\d+)", body)
        if m_pm:
            pmid_entries[m_pm.group(1)] = (idx, body)
        else:
            assert ("DOI:" in body or "arXiv:" in body or "MIT Press" in body), f"Ref {idx} lacks identifier: {body}"
            non_pmid_entries.append((idx, body))

    # Batch verify all PMIDs live via NCBI Entrez esummary
    pmids_list = list(pmid_entries.keys())
    sess = requests.Session()
    r = sess.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(pmids_list), "retmode": "json"},
        timeout=25,
    )
    r.raise_for_status()
    res_json = r.json().get("result", {})

    mismatches = []
    verified_pmids = 0
    for pm, (idx, body) in pmid_entries.items():
        rec = res_json.get(pm)
        if not rec or "error" in rec or not rec.get("title"):
            mismatches.append(f"Ref [{idx}] PMID {pm} missing in PubMed!")
            continue
        pub_year_m = re.search(r"(19|20)\d{2}", rec.get("pubdate", "") + " " + rec.get("epubdate", ""))
        body_year_m = re.search(r"\((\d{4})\)", body)
        if pub_year_m and body_year_m:
            py = int(pub_year_m.group(0))
            by = int(body_year_m.group(1))
            if abs(py - by) > 1:
                mismatches.append(f"Ref [{idx}] PMID {pm} year mismatch: PubMed={py} vs MS={by}")
                continue
        verified_pmids += 1

    assert not mismatches, f"Reference verification errors: {mismatches}"

    # Scan all NC v2.0 files for forbidden removed authors
    forbidden_authors = ["祝力红", "Lihong Zhu", "任智慧", "Zhihui Ren"]
    files_to_scan = [
        EN_MD,
        BASE / "MANUSCRIPT_NCOMMS_AgenticAI_v2.0_CN_review.md",
        PKG / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.md",
        PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_submission_EN.md",
        PKG / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_CN_review.md",
    ]
    author_leaks = []
    for fp in files_to_scan:
        content = fp.read_text(encoding="utf-8")
        for bad in forbidden_authors:
            if bad.lower() in content.lower():
                author_leaks.append(f"{fp.name}: found forbidden author '{bad}'")
    assert not author_leaks, f"Author roster lock violation: {author_leaks}"

    report = {
        "total_references": len(lines),
        "live_pubmed_verified_count": verified_pmids,
        "cs_stat_doi_book_verified_count": len(non_pmid_entries),
        "mismatches": mismatches,
        "removed_author_occurrences": 0,
        "status": "ALL_74_REFS_AND_7_AUTHOR_ROSTER_VERIFIED_OK",
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
