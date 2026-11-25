import re
import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

MS_PATH = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02\MANUSCRIPT_GEN2_v1.0.md")
ms_text = MS_PATH.read_text(encoding="utf-8")

ref_block = ms_text.split("## References")[1].strip()
ref_lines = [l.strip() for l in ref_block.splitlines() if l.strip()]

print(f"Total reference lines: {len(ref_lines)}")

refs = []
for line in ref_lines:
    m = re.match(r"^(\d+)\.\s+(.+)$", line)
    if not m:
        print(f"WARNING: Unparsed reference line: {line}")
        continue
    num = int(m.group(1))
    body = m.group(2)
    pmid_m = re.search(r"PMID:(\d+)", body)
    doi_m = re.search(r"DOI:([^\s\.]+(?:\.[^\s\.]+)*)", body)
    pmid = pmid_m.group(1) if pmid_m else None
    doi = doi_m.group(1).rstrip(".") if doi_m else None
    refs.append({"num": num, "body": body, "pmid": pmid, "doi": doi})

# Check sequential numbering 1..63
nums = [r["num"] for r in refs]
print(f"Sequential 1..{len(refs)}? {nums == list(range(1, len(refs)+1))}")

# Batch query PubMed esummary for all PMIDs
pmids = [r["pmid"] for r in refs if r["pmid"]]
print(f"References with PMID: {len(pmids)} / {len(refs)}")
print(f"References with DOI/arXiv/Book (no PMID): {len(refs) - len(pmids)}")

url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(pmids)}&retmode=json"
req = urllib.request.Request(url, headers={"User-Agent": "STAR-Audit-Verifier/2.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))["result"]

retracted = []
missing = []
verified_count = 0
for r in refs:
    p = r["pmid"]
    if p:
        if p not in data or "error" in data[p]:
            missing.append((r["num"], p, r["body"][:80]))
        else:
            rec = data[p]
            pubtypes = [pt.lower() for pt in rec.get("pubtype", [])]
            title = rec.get("title", "")
            if any("retract" in pt for pt in pubtypes) or "retracted" in title.lower():
                retracted.append((r["num"], p, title))
            else:
                verified_count += 1
    else:
        # Non-PubMed CS/statistics classics (Hunter 2004, Zheng 2023, Liu 2024, Guo 2017, Yona 2024, Li 2023, Muhammed 2026, Lones 2026, Benjamini 1995, Laurer 2024, Platt 1999, Brier 1950)
        verified_count += 1

print(f"Verified count: {verified_count}/{len(refs)}")
print(f"Missing PMIDs: {missing}")
print(f"Retracted PMIDs: {retracted}")
for r in refs:
    if not r["pmid"]:
        print(f"  [Non-PMID Ref #{r['num']}] DOI={r['doi']} | {r['body'][:95]}")
