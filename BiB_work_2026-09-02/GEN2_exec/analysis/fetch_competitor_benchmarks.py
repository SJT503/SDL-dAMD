"""
Fetch live PubMed metadata and PMC full-text sections (Introduction, Results, Discussion, Limitations)
for recent (2024-2026) peer-reviewed benchmark papers in Cell Reports Methods, Patterns, Nature,
Nature Methods, and Nature Communications for journal-benchmark-review Step 1-3.5 and biomed-paper-writing Step 1.
"""
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT_DIR = r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\GEN2_exec\analysis\benchmark_competitors"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "AuditGen2Benchmark/1.0 (mailto:sheng@stu.edu.cn)"}


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def esearch_pubmed(query: str, retmax: int = 8):
    q = urllib.parse.quote(query)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={q}&retmax={retmax}&retmode=json&sort=relevance"
    data = json.loads(fetch_url(url).decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_pubmed_details(pmids):
    if not pmids:
        return []
    ids_str = ",".join(pmids)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids_str}&retmode=xml"
    xml_bytes = fetch_url(url)
    root = ET.fromstring(xml_bytes)
    results = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID", default="")
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        journal = art.findtext(".//Journal/Title", default="")
        iso = art.findtext(".//Journal/ISOAbbreviation", default="")
        year = (
            art.findtext(".//JournalIssue/PubDate/Year")
            or art.findtext(".//ArticleDate/Year")
            or ""
        )
        doi = ""
        pmcid = ""
        for aid in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
            id_type = aid.attrib.get("IdType", "")
            if id_type == "doi":
                doi = aid.text or ""
            elif id_type == "pmc":
                pmcid = aid.text or ""
        abs_parts = []
        for ab in art.findall(".//Abstract/AbstractText"):
            label = ab.attrib.get("Label", "")
            txt = "".join(ab.itertext()).strip()
            if label:
                abs_parts.append(f"[{label}] {txt}")
            else:
                abs_parts.append(txt)
        abstract = "\n".join(abs_parts)
        authors = []
        for au in art.findall(".//AuthorList/Author"):
            ln = au.findtext("LastName", default="")
            fn = au.findtext("Initials", default="")
            if ln:
                authors.append(f"{ln} {fn}".strip())
        results.append({
            "pmid": pmid,
            "pmcid": pmcid,
            "doi": doi,
            "title": title,
            "journal": journal,
            "iso": iso,
            "year": year,
            "first_author": authors[0] if authors else "",
            "authors": authors[:5],
            "abstract": abstract,
        })
    return results


def fetch_pmc_fulltext_sections(pmcid: str):
    """Fetch full-text XML from PMC and extract section titles and paragraphs."""
    pmc_num = pmcid.replace("PMC", "").strip()
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_num}&retmode=xml"
    try:
        xml_bytes = fetch_url(url)
        root = ET.fromstring(xml_bytes)
        sections = []
        body = root.find(".//body")
        if body is None:
            return []
        for sec in body.findall("./sec"):
            sec_title = "".join(sec.find("title").itertext()).strip() if sec.find("title") is not None else "Untitled Section"
            paras = []
            for p in sec.findall(".//p"):
                ptxt = " ".join("".join(p.itertext()).split())
                if ptxt:
                    paras.append(ptxt)
            sections.append({
                "section_title": sec_title,
                "paragraph_count": len(paras),
                "word_count": sum(len(x.split()) for x in paras),
                "paragraphs": paras,
            })
        return sections
    except Exception as e:
        return [{"error": str(e)}]


def main():
    # Core benchmark PMIDs from our 2024-2026 reference list + targeted Cell Reports Methods / Patterns / Nature queries
    seed_pmids = [
        "38898292",  # Farquhar et al. Nature 2024 (Detecting hallucinations in large language models using semantic entropy)
        "41748781",  # Gottweis et al. Nature 2026 (Towards an AI co-scientist)
        "41639376",  # Ghareeb et al. Nature 2026 (Robin: multi-agent laboratory discovery)
        "40038545",  # Wang et al. Nat Methods 2025 (scGPT / foundation model evaluation)
        "40118987",  # Xu et al. Nat Commun 2025 (LLM biomedical evaluation / agentic benchmark)
        "40185950",  # Liu et al. Nat Methods 2025
        "39443795",  # Jin et al. Nat Mach Intell / Nature portfolio 2024-2025
        "39905226",  # Chen et al. Nat Methods 2025
    ]

    queries = [
        '("Cell Reports Methods"[Journal] OR "Cell Rep Methods"[Journal]) AND ("language model" OR "benchmark" OR "framework" OR "audit" OR "single-cell") AND 2024:2026[dp]',
        '("Patterns (N Y)"[Journal]) AND ("language model" OR "benchmark" OR "trustworthiness" OR "hallucination" OR "evaluation") AND 2024:2026[dp]',
        '("Nature Methods"[Journal] OR "Nature Communications"[Journal]) AND ("large language model" OR "hallucination" OR "benchmark") AND ("gene" OR "biomedical" OR "discovery") AND 2024:2026[dp]',
    ]

    discovered_pmids = list(seed_pmids)
    for q in queries:
        time.sleep(0.4)
        ids = esearch_pubmed(q, retmax=6)
        for i in ids:
            if i not in discovered_pmids:
                discovered_pmids.append(i)

    print(f"Fetching details for {len(discovered_pmids)} PMIDs...")
    details = fetch_pubmed_details(discovered_pmids)
    print(f"Retrieved {len(details)} records.")

    # Filter for papers with PMC full text or strong abstracts, and fetch PMC full texts for those with PMCID
    fulltext_count = 0
    for d in details:
        if d["pmcid"]:
            time.sleep(0.4)
            secs = fetch_pmc_fulltext_sections(d["pmcid"])
            if secs and "error" not in secs[0] and len(secs) >= 2:
                d["pmc_sections"] = secs
                fulltext_count += 1
                print(f"  [PMC FULLTEXT OK] PMID={d['pmid']} PMCID={d['pmcid']} ({d['iso']} {d['year']}): {len(secs)} sections")
            else:
                d["pmc_sections"] = []
        else:
            d["pmc_sections"] = []

    out_path = os.path.join(OUT_DIR, "competitor_benchmarks_2024_2026.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(details)} records ({fulltext_count} with full PMC body sections) to {out_path}")


if __name__ == "__main__":
    main()
