#!/usr/bin/env python3
"""
pipeline_prompts.py -- six-step SDL pipeline prompt templates (gen-2).

Structure identical to gen-1 (prereg 2.1): literature review -> Tournament I
(300 pairs x 1 verdict) -> candidate expansion -> Tournament II (45 pairs x 3
judges x 2 orders) -> BTL aggregation (local, btl.py) -> Top-5 grounded
protocols. All templates are frozen at harness build time (2026-09-05, before
the first experimental call); each template's SHA-256 is recorded by the driver
in the run manifest (construction decision C1).

The §5.6 confidence line appears VERBATIM in candidate-generation prompts
(step-1 buckets, step-3 dossiers) and is part of the frozen template.
"""

CONFIDENCE_LINE = ("State your confidence that this candidate will rank in "
                   "the top five, as an integer between 0 and 100.")

DISEASES = {
    "dAMD": {
        "display": "dry age-related macular degeneration (geographic atrophy)",
        "short": "dAMD",
    },
    "ALS": {
        "display": "amyotrophic lateral sclerosis",
        "short": "ALS",
    },
}

# Generic mechanism-space buckets -- deliberately not axis-leading (a bucket
# taxonomy that privileged any pre-registered axis would leak the gold standard).
BUCKETS = [
    ("1", "cell-intrinsic molecular and organelle-level processes"),
    ("2", "intercellular signalling, immune and inflammatory processes"),
    ("3", "metabolic, transport and extracellular-matrix processes"),
]


# ------------------------------------------------------------------ step 1 --
def step1_bucket_prompt(disease, bucket_id, bucket_focus, arm, context_block=None):
    dis = DISEASES[disease]["display"]
    if arm == "blind":
        constraints = (
            "- Describe pathogenic mechanisms and molecular targets. Do NOT name "
            "any specific drug compound, approved or investigational therapeutic, "
            "or chemical inhibitor.\n"
            "- Do not cite any literature at this stage.\n")
    else:  # retrieval arm: tokens lifted, retrieval context injected (C6)
        constraints = (
            "- You may draw on published literature you know and on the "
            "retrieved literature context provided below, including "
            "established therapeutic mechanisms.\n")
    ctx = ("\n%s\n" % context_block if context_block else "")
    return f"""You are the literature-review and hypothesis-generation module of an autonomous biomedical discovery pipeline.

Disease: {dis}
{ctx}
Task bucket {bucket_id} of 3: {bucket_focus}

Propose exactly 12 distinct, testable mechanistic hypotheses about disease pathogenesis within this bucket. Each hypothesis must name specific molecular entities (genes, proteins, pathways) and state the direction of the proposed effect.

Requirements:
- The 12 hypotheses must be mechanistically distinct from one another.
{constraints}- {CONFIDENCE_LINE}

Output a STRICT JSON array of exactly 12 objects, each:
{{"id": 1..12, "mechanism": "<one sentence naming entities and direction>", "key_players": ["GENE1", "GENE2"], "class_hint": "cell_intrinsic|intercellular|metabolic_matrix", "confidence": <integer 0-100>}}
Output the JSON array and nothing else."""


def step1_synthesizer_prompt(disease, bucket_outputs_json, arm):
    dis = DISEASES[disease]["display"]
    blind_line = ("- Do not name any drug compound or therapeutic agent.\n"
                  "- Do not cite literature.\n") if arm == "blind" else ""
    return f"""You are the synthesis module of an autonomous biomedical discovery pipeline.

Disease: {dis}

Three parallel buckets produced the following hypotheses (JSON):
{bucket_outputs_json}

Consolidate these into exactly 30 distinct mechanistic hypotheses:
- Merge near-duplicates, keeping the more precise formulation.
- Preserve coverage across all three mechanism classes.
- Keep the strongest, most testable hypotheses.

Requirements:
{blind_line}- Each hypothesis names specific molecular entities and the direction of the effect.
- {CONFIDENCE_LINE}

Output a STRICT JSON array of exactly 30 objects, each:
{{"id": 1..30, "mechanism": "<one sentence>", "key_players": ["GENE1", "GENE2"], "class_hint": "cell_intrinsic|intercellular|metabolic_matrix", "confidence": <integer 0-100>}}
Output the JSON array and nothing else."""


# ------------------------------------------------------------------ step 2 --
def t1_judge_prompt(disease, mech_a, mech_b):
    dis = DISEASES[disease]["display"]
    return f"""You are an independent judge in a blinded pairwise review of competing mechanistic hypotheses.

Disease: {dis}

Option A:
{mech_a}

Option B:
{mech_b}

Judge each option on three criteria, then give an overall verdict:
- SCIENCE: mechanistic depth and consistency with established biology of this disease.
- FEASIBILITY: how testable and tractable the proposal is with current experimental tools.
- NOVELTY: distance from already-saturated mainstream hypotheses.

Output STRICT JSON only, no other text:
{{"winner": "A" or "B", "science": "A" or "B" or "tie", "feasibility": "A" or "B" or "tie", "novelty": "A" or "B" or "tie", "reasoning": "<2-3 sentences>"}}
Output the JSON object and nothing else."""


# ------------------------------------------------------------------ step 3 --
def step3_dossier_prompt(disease, mechanism, rank, arm, context_block=None):
    dis = DISEASES[disease]["display"]
    if arm == "blind":
        constraints = ("- Do NOT name any drug compound or inhibitor; describe "
                       "the molecular target and intervention principle.\n")
    else:
        constraints = ""
    ctx = ("\n%s\n" % context_block if context_block else "")
    return f"""You are the candidate-expansion module of an autonomous biomedical discovery pipeline.

Disease: {dis}
{ctx}
Hypothesis ranked #{rank} by the first tournament:
{mechanism}

Expand this hypothesis into one intervention-ready candidate profile.
Requirements:
{constraints}- Name the target entities (HGNC symbols where applicable) and the intervention principle (what to activate, inhibit or restore).
- State the rationale linking the mechanism to the disease.
- State feasibility: a concrete experimental readout in a relevant model system.
- {CONFIDENCE_LINE}

Output STRICT JSON only:
{{"name": "<short candidate name>", "mechanism": "<one sentence>", "targets": ["GENE1"], "intervention_principle": "<one sentence>", "rationale": "<2-3 sentences>", "feasibility": "<2-3 sentences with model system and readout>", "confidence": <integer 0-100>}}
Output the JSON object and nothing else."""


# ------------------------------------------------------------------ step 4 --
def t2_judge_prompt(disease, cand_a, cand_b):
    dis = DISEASES[disease]["display"]

    def block(label, c):
        return (f"{label}:\n{name_block(c)}\n"
                f"Mechanism: {c.get('mechanism', '')}\n"
                f"Targets: {', '.join(c.get('targets', []))}\n"
                f"Intervention principle: {c.get('intervention_principle', '')}\n"
                f"Rationale: {c.get('rationale', '')}\n"
                f"Feasibility: {c.get('feasibility', '')}")

    return f"""You are an independent judge in a blinded pairwise review of candidate therapeutic-mechanism proposals.

Disease: {dis}

{block("Candidate A", cand_a)}

{block("Candidate B", cand_b)}

Judge each candidate on three criteria, then give an overall verdict:
- SCIENCE: mechanistic depth and disease relevance.
- FEASIBILITY: testability and tractability with current tools.
- NOVELTY: distance from already-saturated mainstream directions.

Output STRICT JSON only, no other text:
{{"winner": "A" or "B", "science": "A" or "B" or "tie", "feasibility": "A" or "B" or "tie", "novelty": "A" or "B" or "tie", "reasoning": "<3-6 sentences justifying each criterion>"}}
Output the JSON object and nothing else."""


def name_block(c):
    return f"Name: {c.get('name', '<unnamed>')}"


# ------------------------------------------------------------------ step 6 --
def step6_protocol_prompt(disease, candidate, rank, arm):
    dis = DISEASES[disease]["display"]
    if arm == "blind":
        src_line = ("- Do not use any search tool, database lookup or browsing. "
                    "Answer from what you already know.\n")
        blind_line = ("- Do not name any specific drug compound or inhibitor.\n")
    else:
        src_line = ""
        blind_line = ""
    return f"""You are the protocol-drafting module of an autonomous biomedical discovery pipeline.

Disease: {dis}
Selected candidate (rank {rank} of 5):
{json_dossier(candidate)}

Draft a grounded experimental protocol for testing this candidate, supported by exactly 6 published references. For each reference give the PubMed identifier (PMID) and one sentence stating what the cited work shows.

Requirements:
{src_line}{blind_line}- Every reference entry must have a numeric PMID.
- The protocol must name the model system, intervention approach, primary readout and controls.

Output STRICT JSON only:
{{"protocol_name": "<short name>", "aim": "<one sentence>", "model_system": "<one sentence>", "intervention": "<one sentence>", "primary_readout": "<one sentence>", "controls": ["<control 1>", "<control 2>"], "references": [{{"slot": 1, "pmid": "<digits>", "claim": "<one sentence>"}}, ... exactly 6 slots]}}
Output the JSON object and nothing else."""


def json_dossier(c):
    import json
    return json.dumps(c, ensure_ascii=False, indent=1)


# ------------------------------------------------------- template registry --
def template_sha256s():
    """SHA-256 of every frozen template (recorded in run manifests, C1)."""
    import hashlib

    def h(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    out = {
        "step1_bucket_blind": h(step1_bucket_prompt("dAMD", "1", BUCKETS[0][1], "blind")),
        "step1_bucket_retrieval": h(step1_bucket_prompt("dAMD", "1", BUCKETS[0][1], "retrieval")),
        "step1_synthesizer": h(step1_synthesizer_prompt("dAMD", "<BUCKETS>", "blind")),
        "t1_judge": h(t1_judge_prompt("dAMD", "<A>", "<B>")),
        "step3_dossier": h(step3_dossier_prompt("dAMD", "<MECH>", 1, "blind")),
        "t2_judge": h(t2_judge_prompt("dAMD", {"name": "A"}, {"name": "B"})),
        "step6_protocol": h(step6_protocol_prompt("dAMD", {}, 1, "blind")),
        "confidence_line": h(CONFIDENCE_LINE),
    }
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(template_sha256s(), indent=1))
