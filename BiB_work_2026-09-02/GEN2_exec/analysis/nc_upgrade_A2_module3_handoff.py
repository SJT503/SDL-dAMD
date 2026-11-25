#!/usr/bin/env python3
"""
nc_upgrade_A2_module3_handoff.py -- Phase-1 Task A2 for Nature Communications
Special Collection 'Agentic AI Systems':
  1. Decompose Module 3 (Epistemic Abstention + Tier-2 Gate) honestly into:
     - Citation Safety Rate (1 - ungrounded_rate_of_total)
     - Abstention Rate (abstained / total_slots)
     - Parametric Grounded Yield (grounded / total_slots)
     - Conditional Ungrounded Rate Among Emitted (ungrounded / emitted)
     across all 5 evaluated Exp B models + Parent Step 6 (Blind vs Retrieval).
  2. Execute Closed-Loop Deterministic 'Abstention-to-Entrez Handoff' (Module 3b):
     - Zero new LLM API calls / zero extra reasoning tokens.
     - Any slot routed to NO_CITATION (by parametric abstention or deterministic
       Tier-2 rejection of fabricated/Trojan PMIDs) triggers deterministic NCBI
       Entrez esearch -> esummary/efetch retrieval on the structured (domain +
       mechanism entity) query, retaining ONLY distinct PMIDs passing the exact
       frozen Tier-2 relevance rubric (check_on_topic & check_domain_topic_match).
"""
from gate import gate, canary_gate, retry_limit

import json
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import requests
from scipy import stats

from step1_pubmed_verify import (
    HERE,
    EXEC_ROOT,
    NCBI,
    MAILTO,
    load_cache,
    save_cache,
    check_on_topic,
    extract_keywords,
)
from analyze_gemini_cross_ecosystem import check_domain_topic_match

gate(__file__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": f"star-audit-nc/{MAILTO}"})


def fast_get(url, timeout=15, max_tries=6):
    last_err = None
    for att in range(1, max_tries + 1):
        try:
            time.sleep(0.36)
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.text
            last_err = f"HTTP {r.status_code}"
            time.sleep(1.5 * att)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * att)
    raise RuntimeError(f"GET failed for {url}: {last_err}")


def fast_fetch_pubmed_batch(pmids, cache):
    todo = [p for p in sorted(set(pmids)) if p not in cache]
    if not todo:
        return cache
    print(f"[A2 PubMed] Fetching {len(todo)} uncached PMIDs via keep-alive Session (batches of 150)...", flush=True)
    bs = 150
    for i in range(0, len(todo), bs):
        batch = todo[i:i + bs]
        ids_s = ",".join(batch)
        es_txt = fast_get(f"{NCBI}esummary.fcgi?db=pubmed&retmode=json&id={ids_s}&email={MAILTO}", timeout=20)
        es_d = json.loads(es_txt).get("result", {})
        resolved = []
        for pid in batch:
            it = es_d.get(pid)
            if not it or "error" in it or not it.get("title"):
                cache[pid] = {"exists": False, "title": "", "journal": "", "pubdate": "", "abstract": "", "mesh": [], "keywords": []}
            else:
                authors = [a.get("name", "") for a in it.get("authors", []) if isinstance(a, dict)]
                cache[pid] = {
                    "exists": True,
                    "title": it.get("title", ""),
                    "journal": it.get("fulljournalname") or it.get("source", ""),
                    "source": it.get("source", ""),
                    "pubdate": it.get("pubdate", ""),
                    "first_author": authors[0] if authors else "",
                    "abstract": "",
                    "mesh": [],
                    "keywords": [],
                }
                resolved.append(pid)
        if resolved:
            ef_txt = fast_get(f"{NCBI}efetch.fcgi?db=pubmed&retmode=xml&id={','.join(resolved)}&email={MAILTO}", timeout=25)
            try:
                root = ET.fromstring(ef_txt)
                for art in root.findall(".//PubmedArticle"):
                    pe = art.find(".//MedlineCitation/PMID")
                    if pe is None or not pe.text:
                        continue
                    pid = pe.text.strip()
                    if pid in cache:
                        cache[pid]["abstract"] = " ".join(ab.text.strip() for ab in art.findall(".//Article/Abstract/AbstractText") if ab.text)
                        cache[pid]["mesh"] = [m.text.strip() for m in art.findall(".//MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName") if m.text]
                        cache[pid]["keywords"] = [k.text.strip() for k in art.findall(".//MedlineCitation/KeywordList/Keyword") if k.text]
            except Exception as e:
                print(f"  [WARN] XML parse batch {i}: {e}", flush=True)
        save_cache(cache)
        print(f"  fetched {min(i + bs, len(todo))}/{len(todo)} PMIDs", flush=True)
    return cache

HANDOFF_CACHE_PATH = os.path.join(HERE, "nc_upgrade_entrez_handoff_cache.json")
OUT_JSON = os.path.join(HERE, "nc_upgrade_A2_results.json")

GENERIC_BIO = {
    "increases", "increasing", "decreases", "decreasing", "drives", "driving",
    "promotes", "promoting", "inhibits", "inhibiting", "activates", "activating",
    "causes", "causing", "leads", "leading", "thereby", "resulting", "impairs",
    "impairing", "disrupts", "disrupting", "triggers", "triggering", "suppresses",
    "suppressing", "reduces", "reducing", "enhances", "enhancing", "accumulates",
    "accumulation", "release", "releases", "production", "chronic", "acute",
    "progressive", "severe", "damage", "injury", "dysfunction", "homeostasis",
    "response", "responses", "cascade", "stress", "tissue", "organ", "system",
}


def build_entrez_queries(domain_name, mechanism_text):
    """Build deterministic primary + fallback Entrez PubMed queries from domain & mechanism."""
    clean_dom = re.sub(r"\([^)]*\)", "", domain_name).strip()
    if "," in clean_dom:
        parts = [p.strip() for p in clean_dom.split(",") if p.strip()]
        dom_phrase = " ".join(reversed(parts))
    else:
        dom_phrase = clean_dom

    # Extract specific biomedical symbols / entities (uppercase acronyms, hyphenated molecules, long terms)
    acronyms = re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,12}\b", mechanism_text or "")
    specific_ents = []
    seen = set()
    dom_low_tokens = set(re.findall(r"[a-z0-9]+", dom_phrase.lower()))
    for tok in acronyms:
        tl = tok.lower()
        if tl in GENERIC_BIO or tl in dom_low_tokens or tl in seen:
            continue
        if tok in {"The", "This", "These", "Airway", "Loss", "Chronic", "Excessive", "Impaired", "Defective"}:
            continue
        seen.add(tl)
        specific_ents.append(tok)

    if len(specific_ents) < 3:
        for kw in sorted(extract_keywords(mechanism_text), key=lambda x: (-len(x), x)):
            if kw not in GENERIC_BIO and kw not in dom_low_tokens and kw not in seen and len(kw) >= 5:
                seen.add(kw)
                specific_ents.append(kw)
            if len(specific_ents) >= 5:
                break

    queries = []
    if specific_ents:
        ent_or = " OR ".join(f'"{e}"[Title/Abstract]' for e in specific_ents[:5])
        queries.append(f'("{dom_phrase}"[Title/Abstract] OR "{clean_dom}"[MeSH Terms]) AND ({ent_or})')
    queries.append(f'"{dom_phrase}"[Title/Abstract] OR "{clean_dom}"[MeSH Terms]')
    queries.append(dom_phrase)
    return queries, specific_ents[:5]


def esearch_pmids(query, retmax=20):
    q_enc = urllib.parse.quote(query)
    url = f"{NCBI}esearch.fcgi?db=pubmed&retmode=json&sort=relevance&retmax={retmax}&term={q_enc}&email={MAILTO}"
    raw = fast_get(url, timeout=12)
    data = json.loads(raw).get("esearchresult", {})
    return data.get("idlist", []), int(data.get("count", "0") or 0)


def summarize_arm_metrics(total, abstained, fabricated, trojan, grounded):
    emitted = total - abstained
    ungrounded = fabricated + trojan
    safety = total - ungrounded
    return {
        "total_slots": int(total),
        "emitted_slots": int(emitted),
        "abstained_slots": int(abstained),
        "grounded_slots": int(grounded),
        "fabricated_slots": int(fabricated),
        "trojan_slots": int(trojan),
        "ungrounded_slots": int(ungrounded),
        "safety_rate_pct": round(100.0 * safety / max(1, total), 2),
        "ungrounded_rate_pct": round(100.0 * ungrounded / max(1, total), 2),
        "abstention_rate_pct": round(100.0 * abstained / max(1, total), 2),
        "parametric_grounded_yield_pct": round(100.0 * grounded / max(1, total), 2),
        "conditional_ungrounded_among_emitted_pct": round(100.0 * ungrounded / emitted, 2) if emitted > 0 else None,
        "conditional_grounded_among_emitted_pct": round(100.0 * grounded / emitted, 2) if emitted > 0 else None,
    }


@retry_limit(2)
def main():
    t0 = time.perf_counter()
    pm_cache = load_cache()
    handoff_cache = {}
    if os.path.exists(HANDOFF_CACHE_PATH):
        handoff_cache = json.load(open(HANDOFF_CACHE_PATH, encoding="utf-8"))

    # 1. Load GLM Exp B (1,260 slots across 3 arms, 70 Stage-1 hypotheses) & Parent (360 slots)
    expb_glm = json.load(open(os.path.join(HERE, "step1_expB_slots_scored.json"), encoding="utf-8"))
    parent_glm = json.load(open(os.path.join(HERE, "step1_parent_slots_scored.json"), encoding="utf-8"))
    gem_sum = json.load(open(os.path.join(HERE, "gemini_cross_ecosystem_summary.json"), encoding="utf-8"))
    grok_sum = json.load(open(os.path.join(HERE, "grok_cross_ecosystem_summary.json"), encoding="utf-8"))

    # Canary: verify 1,260 GLM ExpB slots and 360 Parent slots
    canary_gate(lambda: len(expb_glm) == 1260 and len(parent_glm) == 360, "Verify GLM slot counts (1260 ExpB + 360 Parent)")

    # 2. Honest Split Table Across All 5 Models in Exp B + Parent Step 6
    split_table = {}

    # 2a. Parent Step 6 (GLM-5.3 Blind vs Live PubMed Retrieval Arm, 180 slots each)
    for p_arm in ["blind", "retrieval"]:
        sub = [r for r in parent_glm if r["arm"] == p_arm]
        n_tot = len(sub)
        n_abs = sum(1 for r in sub if r["abstained"])
        n_fab = sum(1 for r in sub if r["fabricated"])
        n_troj = sum(1 for r in sub if r["resolved"] and not r["on_topic"])
        n_grd = sum(1 for r in sub if r["resolved"] and r["on_topic"])
        split_table.setdefault("GLM-5.3_Parent_Step6", {})[p_arm] = summarize_arm_metrics(
            n_tot, n_abs, n_fab, n_troj, n_grd
        )

    # 2b. GLM-5.3 Exp B (all 70 hypotheses = 420 slots/arm, AND matched h1 subset = 84 slots/arm)
    for subset_tag, filter_h1 in [("GLM-5.3_ExpB_Full420", False), ("GLM-5.3_ExpB_MatchedH1_84", True)]:
        split_table[subset_tag] = {}
        for arm in ["as_discovered", "abstain_probe", "gated"]:
            sub = [r for r in expb_glm if r["arm"] == arm and (not filter_h1 or int(r["hyp_id"]) == 1)]
            n_tot = len(sub)
            n_abs = sum(1 for r in sub if r["abstained"])
            n_fab = sum(1 for r in sub if r["fabricated"])
            n_troj = sum(1 for r in sub if r["resolved"] and not r["on_topic"])
            n_grd = sum(1 for r in sub if r["resolved"] and r["on_topic"])
            split_table[subset_tag][arm] = summarize_arm_metrics(n_tot, n_abs, n_fab, n_troj, n_grd)

    # 2c. Gemini-4-Argon-High, Gemini-3.8-Flash, Grok-4.7-High, Grok-4.7-Fast (84 slots/arm)
    ext_models = [
        ("Gemini-4-Argon-High", gem_sum["arena2_expB_gemini"]["pro"]),
        ("Gemini-3.8-Flash", gem_sum["arena2_expB_gemini"]["flash"]),
        ("Grok-4.7-High", grok_sum["arena2_expB_grok"]["high"]),
        ("Grok-4.7-Fast", grok_sum["arena2_expB_grok"]["fast"]),
    ]
    for m_label, m_dict in ext_models:
        split_table[m_label] = {}
        for arm in ["as_discovered", "abstain_probe", "gated"]:
            ad = m_dict[arm]
            split_table[m_label][arm] = summarize_arm_metrics(
                ad["total_slots"],
                ad["abstained_slots"],
                ad["fabricated_slots"],
                ad["trojan_horse_slots"],
                ad["grounded_slots"],
            )

    # 3. Execute Deterministic Abstention-to-Entrez Handoff Across All 70 Exp B Hypotheses
    hyps_70 = {}
    for r in expb_glm:
        key = f"{r['domain_id']}_h{r['hyp_id']}"
        if key not in hyps_70:
            hyps_70[key] = {
                "domain_id": r["domain_id"],
                "domain": r["domain"],
                "tier": r["tier"],
                "literature_count": r["literature_count"],
                "hyp_id": int(r["hyp_id"]),
                "mechanism": r["hypothesis_mechanism"],
            }

    print(f"[A2] Running deterministic Entrez handoff across {len(hyps_70)} Exp B Stage-1 hypotheses...", flush=True)
    todo_hkeys = [hk for hk in sorted(hyps_70.keys()) if hk not in handoff_cache]

    def query_one_hyp(hkey):
        hinfo = hyps_70[hkey]
        queries, ents = build_entrez_queries(hinfo["domain"], hinfo["mechanism"])
        cand_ids = []
        q_counts = []
        for q in queries[:2]:
            ids, cnt = esearch_pmids(q, retmax=20)
            q_counts.append({"query": q, "total_hits": cnt, "returned": len(ids)})
            for pid in ids:
                if pid not in cand_ids:
                    cand_ids.append(pid)
            if len(cand_ids) >= 15:
                break
        return hkey, {
            "domain_id": hinfo["domain_id"],
            "domain": hinfo["domain"],
            "hyp_id": hinfo["hyp_id"],
            "extracted_entities": ents,
            "queries_executed": q_counts,
            "candidate_pmids": cand_ids[:20],
        }

    if todo_hkeys:
        for done_i, hk in enumerate(todo_hkeys, 1):
            _, hres = query_one_hyp(hk)
            handoff_cache[hk] = hres
            if done_i % 5 == 0 or done_i == len(todo_hkeys):
                print(f"  [esearch] {done_i}/{len(todo_hkeys)} remaining hypotheses queried", flush=True)
                with open(HANDOFF_CACHE_PATH, "w", encoding="utf-8") as fh:
                    json.dump(handoff_cache, fh, indent=2, ensure_ascii=False)

    all_candidate_pmids = set()
    for hk in sorted(hyps_70.keys()):
        all_candidate_pmids.update(handoff_cache[hk]["candidate_pmids"])

    # Batch-fetch PubMed metadata + abstracts + MeSH for all Entrez handoff candidate PMIDs
    pm_cache = fast_fetch_pubmed_batch(sorted(all_candidate_pmids), pm_cache)
    save_cache(pm_cache)

    # Pre-filter verified on-topic Entrez pool per hypothesis under BOTH:
    #   (i) Frozen PREREG check_on_topic (used on GLM-5.3 420-slot audit)
    #   (ii) Domain+mechanism synonym rubric check_domain_topic_match (used on cross-ecosystem 84-slot audit)
    verified_pool_prereg = {}
    verified_pool_cross = {}
    for hkey, hinfo in hyps_70.items():
        cands = handoff_cache[hkey]["candidate_pmids"]
        ctx_str = f"{hinfo['domain']} {hinfo['mechanism']}"
        v_pre = []
        v_crs = []
        for pid in cands:
            rec = pm_cache.get(pid, {})
            if not rec.get("exists"):
                continue
            ok_pre, _, _, _ = check_on_topic(hinfo["mechanism"], ctx_str, rec)
            if ok_pre:
                v_pre.append(pid)
            if int(hinfo["hyp_id"]) == 1:
                if check_domain_topic_match(hinfo["domain"], hinfo["mechanism"], rec):
                    v_crs.append(pid)
        verified_pool_prereg[hkey] = v_pre
        if int(hinfo["hyp_id"]) == 1:
            verified_pool_cross[hkey] = v_crs

    # 4. Evaluate Closed-Loop Pipeline (Module 3a Epistemic Gate + Tier-2 Filter -> Module 3b Entrez Handoff)
    # 4a. GLM-5.3 Full 420-slot Gated Arm + Tier-2 + Entrez Handoff (overall and stratified by density tier)
    glm_gated_by_hyp = defaultdict(list)
    for r in expb_glm:
        if r["arm"] == "gated":
            glm_gated_by_hyp[f"{r['domain_id']}_h{r['hyp_id']}"].append(r)

    handoff_glm_rows = []
    tier_breakdown = defaultdict(lambda: {"slots": 0, "param_kept": 0, "entrez_filled": 0, "honest_residual_abstain": 0, "ungrounded": 0})

    for hkey in sorted(glm_gated_by_hyp.keys()):
        slots = sorted(glm_gated_by_hyp[hkey], key=lambda x: int(x["slot"]))
        tier = hyps_70[hkey]["tier"]
        used_pmids = set()
        # Step A: Retain parametric emissions that pass deterministic Tier-2 check_on_topic
        kept_slots = []
        for s in slots:
            if (not s["abstained"]) and s["resolved"] and s["on_topic"] and s["clean_pmid"] not in used_pmids:
                used_pmids.add(s["clean_pmid"])
                kept_slots.append(("parametric_verified", s["clean_pmid"]))
            else:
                kept_slots.append(("needs_handoff", None))

        # Step B: Fill NO_CITATION / Tier-2-rejected slots from deterministic Entrez verified pool
        pool = [p for p in verified_pool_prereg[hkey] if p not in used_pmids]
        p_idx = 0
        for status, pid in kept_slots:
            tier_breakdown[tier]["slots"] += 1
            if status == "parametric_verified":
                tier_breakdown[tier]["param_kept"] += 1
                handoff_glm_rows.append({"hkey": hkey, "tier": tier, "outcome": "parametric_verified", "pmid": pid})
            elif p_idx < len(pool):
                fill_pid = pool[p_idx]
                p_idx += 1
                tier_breakdown[tier]["entrez_filled"] += 1
                handoff_glm_rows.append({"hkey": hkey, "tier": tier, "outcome": "entrez_handoff_verified", "pmid": fill_pid})
            else:
                tier_breakdown[tier]["honest_residual_abstain"] += 1
                handoff_glm_rows.append({"hkey": hkey, "tier": tier, "outcome": "honest_abstain_sparse", "pmid": "NO_CITATION"})

    # 4b. Evaluate Closed-Loop Handoff across all 5 Models on the Matched 84-slot Benchmark (14 domains x h1 x 6 slots)
    DATA_DIR = os.path.join(EXEC_ROOT, "data")
    raw_84_lists = {
        "GLM-5.3": [
            {
                "domain_id": d_id,
                "slots": [
                    {"pmid": r["clean_pmid"] if not r["abstained"] else "NO_CITATION"}
                    for r in sorted(
                        [x for x in expb_glm if x["arm"] == "gated" and x["domain_id"] == d_id and int(x["hyp_id"]) == 1],
                        key=lambda z: int(z["slot"]),
                    )
                ],
            }
            for d_id in sorted({x["domain_id"] for x in expb_glm})
        ],
        "Gemini-4-Argon-High": [
            x for x in json.load(open(os.path.join(DATA_DIR, "gemini_outputs", "expB_pro_42lists.json"), encoding="utf-8"))
            if x["arm"] == "gated"
        ],
        "Gemini-3.8-Flash": [
            x for x in json.load(open(os.path.join(DATA_DIR, "gemini_outputs", "expB_flash_42lists.json"), encoding="utf-8"))
            if x["arm"] == "gated"
        ],
        "Grok-4.7-High": [
            x for x in json.load(open(os.path.join(DATA_DIR, "grok_outputs", "expB_high_42lists.json"), encoding="utf-8"))
            if x["arm"] == "gated"
        ],
        "Grok-4.7-Fast": [
            x for x in json.load(open(os.path.join(DATA_DIR, "grok_outputs", "expB_fast_42lists.json"), encoding="utf-8"))
            if x["arm"] == "gated"
        ],
    }

    closed_loop_5model_84 = {}
    for m_name, obj_list in raw_84_lists.items():
        param_kept = 0
        entrez_filled = 0
        honest_abstain = 0
        tot_s = 0
        for obj in obj_list:
            did = obj["domain_id"]
            hkey = f"{did}_h1"
            dname = hyps_70[hkey]["domain"]
            mech = hyps_70[hkey]["mechanism"]
            used = set()
            slot_states = []
            for s in obj["slots"]:
                tot_s += 1
                p_str = str(s.get("pmid", "")).strip()
                if p_str.isdigit() and p_str not in used:
                    rec = pm_cache.get(p_str, {})
                    if rec.get("exists") and check_domain_topic_match(dname, mech, rec):
                        used.add(p_str)
                        slot_states.append(("param", p_str))
                        continue
                slot_states.append(("handoff", None))
            pool = [p for p in verified_pool_cross[hkey] if p not in used]
            idx_p = 0
            for st, _ in slot_states:
                if st == "param":
                    param_kept += 1
                elif idx_p < len(pool):
                    entrez_filled += 1
                    idx_p += 1
                else:
                    honest_abstain += 1
        grounded_post = param_kept + entrez_filled
        closed_loop_5model_84[m_name] = {
            "total_slots": tot_s,
            "parametric_tier2_kept_slots": param_kept,
            "entrez_handoff_filled_slots": entrez_filled,
            "total_verified_grounded_slots": grounded_post,
            "honest_residual_abstain_slots": honest_abstain,
            "post_handoff_ungrounded_slots": 0,
            "post_handoff_ungrounded_rate_pct": 0.0,
            "post_handoff_safety_rate_pct": 100.0,
            "post_handoff_verified_yield_pct": round(100.0 * grounded_post / max(1, tot_s), 2),
            "extra_llm_tokens": 0,
        }

    # Summarize GLM-5.3 Full 420 Closed-Loop Handoff
    n420 = len(handoff_glm_rows)
    n_param_420 = sum(1 for r in handoff_glm_rows if r["outcome"] == "parametric_verified")
    n_entrez_420 = sum(1 for r in handoff_glm_rows if r["outcome"] == "entrez_handoff_verified")
    n_abs_420 = sum(1 for r in handoff_glm_rows if r["outcome"] == "honest_abstain_sparse")
    n_grd_420 = n_param_420 + n_entrez_420

    tier_summary_420 = {}
    for t_label, td in tier_breakdown.items():
        s_cnt = td["slots"]
        g_cnt = td["param_kept"] + td["entrez_filled"]
        tier_summary_420[t_label] = {
            "total_slots": s_cnt,
            "parametric_verified": td["param_kept"],
            "entrez_handoff_verified": td["entrez_filled"],
            "total_verified_grounded": g_cnt,
            "verified_yield_pct": round(100.0 * g_cnt / max(1, s_cnt), 2),
            "honest_residual_abstain": td["honest_residual_abstain"],
            "residual_abstain_pct": round(100.0 * td["honest_residual_abstain"] / max(1, s_cnt), 2),
            "ungrounded_rate_pct": 0.0,
        }

    elapsed = round(time.perf_counter() - t0, 2)
    out = {
        "task": "A2_Module3_Honest_Split_and_Closed_Loop_Entrez_Handoff",
        "elapsed_sec": elapsed,
        "honest_split_by_model_and_arm": split_table,
        "closed_loop_glm_full420": {
            "total_slots": n420,
            "baseline_as_discovered_grounded_slots": split_table["GLM-5.3_ExpB_Full420"]["as_discovered"]["grounded_slots"],
            "baseline_as_discovered_grounded_yield_pct": split_table["GLM-5.3_ExpB_Full420"]["as_discovered"]["parametric_grounded_yield_pct"],
            "baseline_as_discovered_ungrounded_rate_pct": split_table["GLM-5.3_ExpB_Full420"]["as_discovered"]["ungrounded_rate_pct"],
            "module3a_gated_raw_grounded_yield_pct": split_table["GLM-5.3_ExpB_Full420"]["gated"]["parametric_grounded_yield_pct"],
            "module3a_gated_raw_ungrounded_rate_pct": split_table["GLM-5.3_ExpB_Full420"]["gated"]["ungrounded_rate_pct"],
            "module3a_plus_tier2_parametric_kept_slots": n_param_420,
            "module3b_entrez_handoff_filled_slots": n_entrez_420,
            "closed_loop_total_verified_grounded_slots": n_grd_420,
            "closed_loop_verified_grounded_yield_pct": round(100.0 * n_grd_420 / n420, 2),
            "closed_loop_honest_residual_abstain_slots": n_abs_420,
            "closed_loop_honest_residual_abstain_pct": round(100.0 * n_abs_420 / n420, 2),
            "closed_loop_ungrounded_rate_pct": 0.0,
            "closed_loop_safety_rate_pct": 100.0,
            "extra_llm_calls": 0,
            "extra_llm_tokens": 0,
            "by_literature_density_tier": tier_summary_420,
        },
        "closed_loop_5model_matched84": closed_loop_5model_84,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(f"\n[A2 DONE in {elapsed}s] Saved to {OUT_JSON}")
    print(f"  GLM-5.3 Full 420: Baseline Yield={out['closed_loop_glm_full420']['baseline_as_discovered_grounded_yield_pct']}% "
          f"(Ungrounded={out['closed_loop_glm_full420']['baseline_as_discovered_ungrounded_rate_pct']}%) -> "
          f"Module 3a Gated Raw Yield={out['closed_loop_glm_full420']['module3a_gated_raw_grounded_yield_pct']}% "
          f"(Ungrounded={out['closed_loop_glm_full420']['module3a_gated_raw_ungrounded_rate_pct']}%) -> "
          f"Closed-Loop Module 3a+3b Verified Yield={out['closed_loop_glm_full420']['closed_loop_verified_grounded_yield_pct']}% "
          f"({n_grd_420}/420;Ungrounded=0.00%; Extra LLM tokens=0)")
    for m_name, md in closed_loop_5model_84.items():
        print(f"  [84-slot Closed-Loop] {m_name:22s}: Verified Yield={md['post_handoff_verified_yield_pct']}% "
              f"(param={md['parametric_tier2_kept_slots']}, entrez={md['entrez_handoff_filled_slots']}, "
              f"abstain={md['honest_residual_abstain_slots']}, ungrounded=0.0%)")


if __name__ == "__main__":
    main()
