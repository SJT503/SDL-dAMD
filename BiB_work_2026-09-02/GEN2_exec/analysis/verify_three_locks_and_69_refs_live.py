#!/usr/bin/env python3
"""
Zero-trust live verification of:
1. Figure & Table Three-Lock Alignment (Lock 1, Lock 2, Lock 3, Lock 3+, Extended Data, Supplementary, Panel A-D parity)
   across MANUSCRIPT_NMI_v1.0.md, Manuscript_NMI_v1.0_submission_EN.docx, and STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md.
2. Live bibliographic authenticity of ALL 69 references via NCBI PubMed Entrez (esummary + efetch XML) and Crossref REST API.
3. Extraction of every in-text citation sentence mapped against the live official title & abstract of each cited reference
   for 100% Round 6E citation appropriateness auditing.
"""

from __future__ import annotations

import difflib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
MS_MD = BASE / "MANUSCRIPT_NMI_v1.0.md"
ZH_MD = BASE / "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md"
PKG_DOCX = BASE / "STAR-Audit_投稿包_v1.0" / "Manuscript_NMI_v1.0_submission_EN.docx"
SUPP_MD = BASE / "SUPPLEMENTARY_GEN2_v1.0.md"
OUT_JSON = BASE / "GEN2_exec" / "analysis" / "live_69_ref_verification_report.json"


def expand_cite_token(block: str) -> list[int]:
    """Expand e.g. '[3–5]' or '[37, 40, 58–60]' into integer list."""
    nums: list[int] = []
    inner = block.strip("[]")
    for part in inner.split(","):
        part = part.strip()
        m_range = re.fullmatch(r"(\d+)\s*[–\-]\s*(\d+)", part)
        if m_range:
            a, b = int(m_range.group(1)), int(m_range.group(2))
            nums.extend(range(a, b + 1))
        elif re.fullmatch(r"\d+", part):
            nums.append(int(part))
    return nums


def audit_three_locks() -> dict:
    text = MS_MD.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Split body (before ## Figure Legends), legends, extended data, references
    idx_legends = next(i for i, l in enumerate(lines) if l.startswith("## Figure Legends"))
    idx_ext = next(i for i, l in enumerate(lines) if l.startswith("## Extended Data"))
    idx_refs = next(i for i, l in enumerate(lines) if l.startswith("## References"))

    body_lines = lines[:idx_legends]
    legend_lines = lines[idx_legends:idx_ext]
    ext_lines = lines[idx_ext:idx_refs]
    ref_lines = lines[idx_refs + 1 :]

    # 1. Placeholders in body
    placeholders: list[tuple[int, str]] = []
    body_no_ph_lines: list[str] = []
    for i, l in enumerate(body_lines, 1):
        m_ph = re.fullmatch(r"\[INSERT (.+?) ABOUT HERE\]", l.strip())
        if m_ph:
            placeholders.append((i, m_ph.group(1).title()))
            body_no_ph_lines.append("")
        else:
            body_no_ph_lines.append(l)

    # 2. First mentions in body (excluding placeholders)
    first_fig: dict[str, int] = {}
    first_ext_fig: dict[str, int] = {}
    first_ext_tab: dict[str, int] = {}
    first_supp_note: dict[str, int] = {}
    first_supp_tab: dict[str, int] = {}
    panel_mentions: dict[str, set[str]] = {f"Figure {k}": set() for k in range(1, 7)}

    for i, l in enumerate(body_no_ph_lines, 1):
        for m in re.finditer(r"Extended Data (?:Figure|Fig\.)\s*(\d+)", l):
            k = f"Extended Data Figure {m.group(1)}"
            first_ext_fig.setdefault(k, i)
        for m in re.finditer(r"Extended Data Table\s*(\d+)", l):
            k = f"Extended Data Table {m.group(1)}"
            first_ext_tab.setdefault(k, i)
        # Remove Extended Data mentions before scanning main Figure/Table mentions
        l_clean = re.sub(r"Extended Data (?:Figure|Fig\.|Table)\s*\d+", "", l)
        l_clean = re.sub(r"Supplementary (?:Figure|Fig\.|Table)\s*S?\d+", "", l_clean)
        for m in re.finditer(r"\b(?:Figure|Fig\.)\s*(\d+)([A-Da-d](?:[–\-,\s]+[A-Da-d])*)?", l_clean):
            k = f"Figure {m.group(1)}"
            first_fig.setdefault(k, i)
            if m.group(2):
                raw_p = m.group(2).upper()
                m_rng = re.fullmatch(r"([A-D])\s*[–\-]\s*([A-D])", raw_p.strip())
                if m_rng:
                    for code in range(ord(m_rng.group(1)), ord(m_rng.group(2)) + 1):
                        panel_mentions[k].add(chr(code))
                else:
                    for ch in re.findall(r"[A-D]", raw_p):
                        panel_mentions[k].add(ch)
        for m in re.finditer(r"Supplementary Note\s*(\d+)", l):
            first_supp_note.setdefault(f"Supplementary Note {m.group(1)}", i)
        for m in re.finditer(r"Supplementary Table\s*S(\d+)", l):
            first_supp_tab.setdefault(f"Supplementary Table S{m.group(1)}", i)

    # Check Legend order and panels in legends
    legend_text = "\n".join(legend_lines)
    legend_headers = re.findall(r"^\*\*Figure (\d+)\.", legend_text, flags=re.M)
    legend_panels: dict[str, set[str]] = {}
    for k in range(1, 7):
        m_leg = re.search(rf"\*\*Figure {k}\..*?(?=\n\*\*Figure \d+\.|\Z)", legend_text, flags=re.S)
        if m_leg:
            pts = set(re.findall(r"\*\*([A-D])\*\*", m_leg.group(0)))
            if not pts:
                pts = set(re.findall(r"\(([A-D])\)", m_leg.group(0)))
            legend_panels[f"Figure {k}"] = pts

    ext_text = "\n".join(ext_lines)
    ext_headers = re.findall(r"^\*\*(Extended Data (?:Figure|Table) \d+)\.", ext_text, flags=re.M)

    # Check DOCX placeholders & tables
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(PKG_DOCX) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
        docx_paras = ["".join(p.itertext()).strip() for p in root.findall(".//w:body/w:p", ns)]
        docx_tables = len(root.findall(".//w:body/w:tbl", ns))
        docx_media = len([n for n in zf.namelist() if n.startswith("word/media/")])
    docx_phs = [p for p in docx_paras if p.startswith("[INSERT ") and p.endswith("ABOUT HERE]")]

    # Check every placeholder line > first_mention line
    ph_after_first = {
        label: (ph_line > first_fig.get(label, 999999), first_fig.get(label), ph_line)
        for ph_line, label in placeholders
    }

    # Check citation first-appearance monotonicity in body
    cite_first_order: list[int] = []
    seen_cites: set[int] = set()
    body_joined = "\n".join(body_lines)
    for m in re.finditer(r"\[(\d+(?:\s*[–\-,]\s*\d+)*)\]", body_joined):
        for c in expand_cite_token(m.group(0)):
            if c not in seen_cites:
                seen_cites.add(c)
                cite_first_order.append(c)

    # Also check Extended Data Tables citations for any refs only appearing in Extended Data
    all_joined = "\n".join(lines[:idx_refs])
    seen_all_cites: set[int] = set()
    all_cite_order: list[int] = []
    for m in re.finditer(r"\[(\d+(?:\s*[–\-,]\s*\d+)*)\]", all_joined):
        for c in expand_cite_token(m.group(0)):
            if c not in seen_all_cites:
                seen_all_cites.add(c)
                all_cite_order.append(c)

    return {
        "first_fig_order": sorted(first_fig.items(), key=lambda x: x[1]),
        "placeholders": placeholders,
        "ph_equals_first_fig_order": [lbl for _, lbl in placeholders] == [k for k, _ in sorted(first_fig.items(), key=lambda x: x[1])],
        "ph_strictly_after_first_mention": ph_after_first,
        "first_ext_fig": sorted(first_ext_fig.items(), key=lambda x: x[1]),
        "first_ext_tab": sorted(first_ext_tab.items(), key=lambda x: x[1]),
        "first_supp_note": sorted(first_supp_note.items(), key=lambda x: x[1]),
        "first_supp_tab": sorted(first_supp_tab.items(), key=lambda x: x[1]),
        "legend_headers": legend_headers,
        "ext_headers": ext_headers,
        "panel_mentions_in_text": {k: sorted(v) for k, v in panel_mentions.items()},
        "legend_panels": {k: sorted(v) for k, v in legend_panels.items()},
        "docx_placeholders": docx_phs,
        "docx_tables": docx_tables,
        "docx_embedded_figures": docx_media,
        "body_citation_first_order": cite_first_order,
        "all_citation_first_order": all_cite_order,
        "all_citations_strictly_1_to_69": all_cite_order == list(range(1, 70)),
    }


def fetch_json(url: str, timeout: float = 20.0) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "STAR-Audit-IntegrityVerifier/1.0 (mailto:jtsheng@stu.edu.cn)"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == 2:
                return {"_error": str(e)}
            time.sleep(0.8 * (attempt + 1))
    return None


def fetch_pubmed_batch(pmids: list[str]) -> tuple[dict[str, dict], dict[str, str]]:
    """Fetch esummary + efetch abstracts in batches of 40 from NCBI Entrez."""
    summaries: dict[str, dict] = {}
    abstracts: dict[str, str] = {}
    for start in range(0, len(pmids), 40):
        chunk = pmids[start : start + 40]
        ids_param = ",".join(chunk)
        sum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_param}&retmode=json"
        data = fetch_json(sum_url)
        if data and "result" in data:
            for pid in chunk:
                if pid in data["result"]:
                    summaries[pid] = data["result"][pid]
        time.sleep(0.4)
        efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids_param}&retmode=xml"
        req = urllib.request.Request(efetch_url, headers={"User-Agent": "STAR-Audit-IntegrityVerifier/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=25.0) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            for art in root.findall(".//PubmedArticle"):
                pmid_el = art.find(".//MedlineCitation/PMID")
                if pmid_el is None or not pmid_el.text:
                    continue
                pid = pmid_el.text.strip()
                abs_texts = ["".join(ab.itertext()).strip() for ab in art.findall(".//Abstract/AbstractText")]
                abstracts[pid] = " ".join(abs_texts)
        except Exception as e:
            print(f"[WARN] efetch batch error: {e}")
        time.sleep(0.4)
    return summaries, abstracts


def parse_references_and_contexts() -> list[dict]:
    text = MS_MD.read_text(encoding="utf-8")
    idx_refs = text.index("## References")
    pre_ref_text = text[:idx_refs]
    ref_block = text[idx_refs:]

    # Split pre_ref_text into sentences/lines for context mapping
    contexts_by_num: dict[int, list[str]] = {k: [] for k in range(1, 70)}
    for para in pre_ref_text.splitlines():
        para = para.strip()
        if not para:
            continue
        # Split sentences roughly while preserving table rows as whole lines
        if para.startswith("|"):
            sents = [para]
        else:
            sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`*])", para)
        for s in sents:
            for m in re.finditer(r"\[(\d+(?:\s*[–\-,]\s*\d+)*)\]", s):
                for c in expand_cite_token(m.group(0)):
                    if 1 <= c <= 69 and s not in contexts_by_num[c]:
                        contexts_by_num[c].append(s)

    refs: list[dict] = []
    for line in ref_block.splitlines():
        m = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if not m:
            continue
        num = int(m.group(1))
        raw = m.group(2).strip()
        m_pmid = re.search(r"PMID:\s*(\d+)", raw)
        m_doi = re.search(r"DOI:\s*([^\s]+?)(?:\.\s*PMID:|$)", raw)
        if not m_doi:
            m_doi = re.search(r"DOI:\s*([^\s]+)", raw)
        doi = m_doi.group(1).rstrip(".") if m_doi else None
        pmid = m_pmid.group(1) if m_pmid else None
        m_year = re.search(r"\((\d{4})\)", raw)
        year = m_year.group(1) if m_year else None
        # Extract title between first ". " and " *"
        m_title = re.match(r"^[^.]+\.\s+(.+?)\.\s+\*([^*]+)\*", raw)
        title = m_title.group(1).strip() if m_title else raw
        journal = m_title.group(2).strip() if m_title else ""
        first_author = raw.split(",")[0].split(" ")[0].strip()
        refs.append(
            {
                "num": num,
                "raw": raw,
                "first_author": first_author,
                "title": title,
                "journal": journal,
                "year": year,
                "doi": doi,
                "pmid": pmid,
                "contexts": contexts_by_num.get(num, []),
            }
        )
    return refs


def verify_all_69_references(refs: list[dict]) -> list[dict]:
    pmids = [r["pmid"] for r in refs if r["pmid"]]
    print(f"Querying NCBI Entrez for {len(pmids)} PMIDs...")
    pm_summaries, pm_abstracts = fetch_pubmed_batch(pmids)

    results = []
    for r in refs:
        num = r["num"]
        pid = r["pmid"]
        doi = r["doi"]
        status = "UNVERIFIED"
        issues: list[str] = []
        official_title = ""
        official_year = ""
        official_first_author = ""
        official_journal = ""
        official_doi = ""
        abstract = ""

        if pid and pid in pm_summaries and "title" in pm_summaries[pid]:
            s = pm_summaries[pid]
            official_title = re.sub(r"<[^>]+>", "", s.get("title", "")).rstrip(".")
            official_year = (s.get("pubdate", "") or "")[:4]
            authors = s.get("authors", [])
            official_first_author = authors[0]["name"].split(" ")[0] if authors else ""
            official_journal = s.get("source", "")
            for aid in s.get("articleids", []):
                if aid.get("idtype") == "doi":
                    official_doi = aid.get("value", "")
            abstract = pm_abstracts.get(pid, "")
            status = "PUBMED_VERIFIED"
        elif doi:
            cr_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
            cr = fetch_json(cr_url)
            time.sleep(0.15)
            if cr and cr.get("status") == "ok":
                msg = cr["message"]
                t_list = msg.get("title", [])
                official_title = re.sub(r"<[^>]+>", "", t_list[0]).rstrip(".") if t_list else ""
                for date_key in ("published-print", "published-online", "issued", "created"):
                    if date_key in msg and "date-parts" in msg[date_key]:
                        official_year = str(msg[date_key]["date-parts"][0][0])
                        break
                au_list = msg.get("author", [])
                if au_list:
                    official_first_author = au_list[0].get("family", "") or au_list[0].get("name", "")
                c_list = msg.get("container-title", [])
                official_journal = c_list[0] if c_list else msg.get("publisher", "")
                official_doi = msg.get("DOI", "")
                raw_abs = msg.get("abstract", "")
                abstract = re.sub(r"<[^>]+>", " ", raw_abs).strip()
                status = "CROSSREF_VERIFIED"
            else:
                issues.append(f"Crossref lookup failed for DOI={doi}: {cr}")

        # Compare title similarity, year, first author, and DOI
        def norm(x: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()

        title_sim = difflib.SequenceMatcher(None, norm(r["title"]), norm(official_title)).ratio() if official_title else 0.0
        if title_sim < 0.85:
            issues.append(f"Title similarity={title_sim:.2f}: MS='{r['title']}' vs OFFICIAL='{official_title}'")
        if r["year"] and official_year and r["year"] != official_year:
            # Allow +/- 1 year for epub vs print, but flag it so we inspect manually!
            issues.append(f"Year check: MS={r['year']} vs OFFICIAL={official_year}")
        if r["first_author"] and official_first_author:
            if norm(r["first_author"]) != norm(official_first_author.split("-")[0]) and norm(official_first_author) not in norm(r["raw"][:40]):
                issues.append(f"First author check: MS='{r['first_author']}' vs OFFICIAL='{official_first_author}'")
        if doi and official_doi and doi.lower() != official_doi.lower():
            issues.append(f"DOI mismatch: MS='{doi}' vs OFFICIAL='{official_doi}'")

        results.append(
            {
                **r,
                "verification_source": status,
                "title_similarity": round(title_sim, 4),
                "official_title": official_title,
                "official_year": official_year,
                "official_first_author": official_first_author,
                "official_journal": official_journal,
                "official_doi": official_doi,
                "abstract_snippet": abstract[:700],
                "issues": issues,
            }
        )
    return results


def main() -> None:
    locks = audit_three_locks()
    print("=== 1. THREE-LOCK ALIGNMENT SUMMARY ===")
    print("Main Figures first-mention order:", locks["first_fig_order"])
    print("Main Figure placeholders:        ", locks["placeholders"])
    print("Placeholders == First-mention?   ", locks["ph_equals_first_fig_order"])
    print("Each placeholder > first mention?", all(v[0] for v in locks["ph_strictly_after_first_mention"].values()))
    print("Extended Data Fig first mention: ", locks["first_ext_fig"])
    print("Extended Data Tab first mention: ", locks["first_ext_tab"])
    print("Supp Notes first mention:        ", locks["first_supp_note"])
    print("Supp Tables first mention:       ", locks["first_supp_tab"])
    print("Legend headers:                  ", locks["legend_headers"])
    print("Extended Data headers:           ", locks["ext_headers"])
    print("Panel mentions in text:          ", locks["panel_mentions_in_text"])
    print("Panels in Figure Legends:        ", locks["legend_panels"])
    print("DOCX placeholders:               ", locks["docx_placeholders"])
    print("DOCX tables / embedded figs:     ", locks["docx_tables"], "/", locks["docx_embedded_figures"])
    print("Citations strictly 1..69?        ", locks["all_citations_strictly_1_to_69"])

    refs = parse_references_and_contexts()
    print(f"\n=== 2. LIVE VERIFYING ALL {len(refs)} REFERENCES ===")
    verified = verify_all_69_references(refs)

    n_verified = sum(1 for r in verified if r["verification_source"] in ("PUBMED_VERIFIED", "CROSSREF_VERIFIED"))
    flagged = [r for r in verified if r["issues"] or r["verification_source"] == "UNVERIFIED" or len(r["contexts"]) == 0]
    print(f"Verified via live PubMed/Crossref: {n_verified}/{len(verified)}")
    print(f"Flagged entries for closer inspection: {len(flagged)}")
    for r in flagged:
        print(f"  Ref [{r['num']}] ({r['verification_source']}, contexts={len(r['contexts'])}): {r['issues']}")

    OUT_JSON.write_text(json.dumps({"three_locks": locks, "references": verified}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Saved full report to {OUT_JSON}")


if __name__ == "__main__":
    main()
