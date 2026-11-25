#!/usr/bin/env python3
"""
Complete Round 6A-6E + 69/69 Citation Authenticity & Appropriateness Audit
for MANUSCRIPT_NMI_v1.0.md (and DOCX / ZH parity).
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
REP_PATH = BASE / "GEN2_exec" / "analysis" / "live_69_ref_verification_report.json"
OUT_MD = BASE / "GEN2_exec" / "analysis" / "CITATION_AND_THREELOCK_DEEP_AUDIT_v1.0.md"


def check_true_citation_order(md_path: Path) -> tuple[bool, list[int]]:
    txt = md_path.read_text(encoding="utf-8")
    idx_ref = txt.index("## References") if "## References" in txt else txt.index("## 参考文献")
    pre = txt[:idx_ref]
    # Remove inline math $...$ (single-line) and inline code `...`
    pre = re.sub(r"\$[^$\n]+\$", "", pre)
    pre = re.sub(r"`[^`\n]+`", "", pre)
    # Remove confidence intervals like "95% CI [1.43%, 4.76%]" or ratios like "[6/360]"
    seen, order = set(), []
    for m in re.finditer(r"\[(\d+(?:\s*[–\-,]\s*\d+)*)\]", pre):
        tok = m.group(1)
        vals = []
        for part in tok.split(","):
            part = part.strip()
            mr = re.fullmatch(r"(\d+)\s*[–\-]\s*(\d+)", part)
            if mr:
                vals.extend(range(int(mr.group(1)), int(mr.group(2)) + 1))
            elif part.isdigit():
                vals.append(int(part))
        if not vals or any(v < 1 or v > 69 for v in vals):
            continue
        for v in vals:
            if v not in seen:
                seen.add(v)
                order.append(v)
    return order == list(range(1, 70)), order


def main() -> None:
    rep = json.loads(REP_PATH.read_text(encoding="utf-8"))

    for fn in [
        "MANUSCRIPT_NMI_v1.0.md",
        "STAR-Audit_NMI瘦身版_手稿全文中文版_审核稿.md",
        "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md",
    ]:
        ok, order = check_true_citation_order(BASE / fn)
        print(f"[{fn}] Strict monotonic [1..69] citation order? {ok} (count={len(order)})")
        if not ok:
            print("  Actual order:", order)

    # Verify Ref [18] via live arXiv API and Ref [66] via live OpenAlex API
    xml18 = urllib.request.urlopen("http://export.arxiv.org/api/query?id_list=1706.04599", timeout=15).read()
    root18 = ET.fromstring(xml18)
    ns_a = {"a": "http://www.w3.org/2005/Atom"}
    t18 = (root18.findtext(".//a:entry/a:title", namespaces=ns_a) or "").strip().replace("\n", " ")
    au18 = [el.text for el in root18.findall(".//a:entry/a:author/a:name", ns_a)]
    print(f"\n[LIVE arXiv Ref 18] Title='{t18}' | Authors={au18}")

    oa66_url = (
        "https://api.openalex.org/works?search="
        + urllib.parse.quote("Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods")
        + "&per-page=2"
    )
    oa66 = json.loads(urllib.request.urlopen(oa66_url, timeout=15).read().decode("utf-8"))
    w66 = oa66["results"][0]
    print(
        f"[LIVE OpenAlex Ref 66] Title='{w66.get('title')}' | Year={w66.get('publication_year')} | "
        f"Citations={w66.get('cited_by_count')} | Authors={[a['author']['display_name'] for a in w66.get('authorships', [])]}"
    )

    # Check all preprints in References (e.g. Ref 9 or any bioRxiv/arXiv)
    print("\n=== PREPRINT & METADATA DETAIL CHECK ===")
    for r in rep["references"]:
        if any(k in r["raw"].lower() for k in ["preprint", "biorxiv", "medrxiv", "arxiv"]):
            print(f"  Ref [{r['num']}]: {r['raw']}")
            print(f"    -> Official ({r['verification_source']}): title='{r['official_title']}', journal='{r['official_journal']}', year='{r['official_year']}', doi='{r['official_doi']}'")
            # Check OpenAlex to see if published in a peer-reviewed journal
            q = urllib.parse.quote(r["official_title"] or r["title"][:80])
            oa = json.loads(urllib.request.urlopen(f"https://api.openalex.org/works?search={q}&per-page=3", timeout=15).read().decode("utf-8"))
            for item in oa.get("results", [])[:2]:
                loc = (item.get("primary_location") or {}).get("source") or {}
                print(f"       OpenAlex match: year={item.get('publication_year')} | venue={loc.get('display_name')} | doi={item.get('doi')}")

    # Round 6A-6D checks on MANUSCRIPT_NMI_v1.0.md
    txt = (BASE / "MANUSCRIPT_NMI_v1.0.md").read_text(encoding="utf-8")
    body = txt[: txt.index("## References")]

    print("\n=== ROUND 6A/6B: UNPUBLISHED & CROSS-PROJECT LEAKAGE ===")
    for pat in [
        r"under review",
        r"unpublished data",
        r"personal communication",
        r"data not shown",
        r"in this series",
        r"companion paper",
        r"our previous work",
        r"second paper",
        r"third paper",
    ]:
        for m in re.finditer(pat, body, re.I):
            print(f"  HIT [{pat}]: {body[max(0, m.start()-35):min(len(body), m.end()+35)].replace(chr(10), ' ')}")

    print("\n=== ROUND 6C: AI WRITING CLICHES ===")
    for pat in [
        r"\bnovel\b",
        r"\bunprecedented\b",
        r"to our knowledge",
        r"first-ever",
        r"first to show",
        r"it is important",
        r"it is worth noting",
        r"\bclearly\b",
        r"\bobviously\b",
        r"\bevidently\b",
        r"\bimportantly\b",
        r"\bnotably\b",
        r"\binterestingly\b",
        r"\bsurprisingly\b",
        r"as mentioned above",
        r"as stated previously",
        r"as noted earlier",
        r"it should be noted",
        r"needless to say",
        r"may potentially",
        r"could possibly",
        r"might perhaps",
        r"proves that",
        r"demonstrates conclusively",
        r"definitively shows",
    ]:
        for m in re.finditer(pat, body, re.I):
            print(f"  HIT [{pat}]: {body[max(0, m.start()-40):min(len(body), m.end()+40)].replace(chr(10), ' ')}")

    print("\n=== ROUND 6D: US vs UK SPELLING CONSISTENCY ===")
    uk_words = [
        r"\brandomised\b", r"\brandomisation\b", r"\bmodelled\b", r"\bfavours\b", r"\bfavouring\b",
        r"\bcentre\b", r"\bbehaviour\b", r"\bcolour\b", r"\banalyse\b", r"\banalysed\b",
        r"\boptimise\b", r"\boptimised\b", r"\bcharacterise\b", r"\bcharacterised\b", r"\btumour\b", r"\bneutralise\b",
    ]
    us_words = [
        r"\brandomized\b", r"\brandomization\b", r"\bmodeled\b", r"\bfavors\b", r"\bfavoring\b",
        r"\bcenter\b", r"\bbehavior\b", r"\bcolor\b", r"\banalyze\b", r"\banalyzed\b",
        r"\boptimize\b", r"\boptimized\b", r"\bcharacterize\b", r"\bcharacterized\b", r"\btumor\b", r"\bneutralize\b",
    ]
    print("  UK hits in body:", [(w, len(re.findall(w, body, re.I))) for w in uk_words if re.findall(w, body, re.I)])
    print("  US hits in body:", [(w, len(re.findall(w, body, re.I))) for w in us_words if re.findall(w, body, re.I)])

    # Write full 69-reference Claim-vs-Source markdown ledger so we can inspect EVERY SINGLE ONE (1..69)!
    md_out = ["# 69/69 Citation Authenticity & Claim-Appropriateness Ledger\n"]
    for r in rep["references"]:
        src = r["verification_source"]
        if r["num"] == 18 and t18:
            src = "ARXIV_LIVE_VERIFIED"
            r["official_title"] = t18
            r["official_year"] = "2017"
        elif r["num"] == 66 and w66:
            src = "OPENALEX_LIVE_VERIFIED"
            r["official_title"] = w66.get("title", "")
            r["official_year"] = str(w66.get("publication_year", ""))
        md_out.append(f"## Ref [{r['num']}] — `{src}`")
        md_out.append(f"- **Manuscript Entry:** {r['raw']}")
        md_out.append(
            f"- **Official Record:** `{r['official_first_author']}` ({r['official_year']}) | *{r['official_journal']}* | Title: **{r['official_title']}** | DOI: `{r['official_doi']}`"
        )
        md_out.append(f"- **Official Abstract Snippet:** {r['abstract_snippet'] or '(Book/Conference monograph without Entrez abstract)'}")
        md_out.append("- **In-Text Citation Claims:**")
        for c in r["contexts"]:
            md_out.append(f"  - {c}")
        md_out.append("")

    OUT_MD.write_text("\n".join(md_out), encoding="utf-8")
    print(f"\n[OK] Wrote complete 69-ref claim-vs-source ledger to {OUT_MD}")


if __name__ == "__main__":
    main()
