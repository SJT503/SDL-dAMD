#!/usr/bin/env python3
"""T2 judge truncation fix pilots: (a) 8192 as-is; (b) slim prompt @2048."""
import gen2_call
import gen2_parse

ca = {
    "name": "Lysosomal acidification restoration in RPE",
    "mechanism": ("Restoring v-ATPase-driven lysosomal acidification re-enables "
                  "outer-segment digestion and clears lipofuscin."),
    "targets": ["ATP6V0A1", "TFEB"],
    "intervention_principle": "activate TFEB-mediated lysosomal biogenesis",
    "rationale": ("Aging RPE shows declining lysosomal pH; clearance failure is "
                  "upstream of phototoxic A2E accumulation and RPE death in "
                  "geographic atrophy."),
    "feasibility": ("ARPE-19 and iPSC-RPE monolayers with pH-sensitive probes "
                    "(LysoSensor), outer-segment challenge assay, lipofuscin "
                    "quantification by autofluorescence."),
}
cb = {
    "name": "Complement terminal-pathway blockade at the RPE-Bruch interface",
    "mechanism": ("Blocking C3 convertase activity prevents C5b-9 deposition on "
                  "RPE, slowing drusen consolidation."),
    "targets": ["C3", "CFB"],
    "intervention_principle": "inhibit alternative-pathway amplification",
    "rationale": ("GWAS-strong complement locus genetics and two approved C3/C5 "
                  "inhibitors establish terminal-pathway drive in GA expansion."),
    "feasibility": ("Complement-depleted serum on RPE monolayers, MAC deposition "
                    "readout by immunostaining, established assays."),
}


def slim_t2_prompt(disease, ca, cb):
    """Slim variant: name+mechanism+targets+one-line feasibility per candidate,
    short reasoning ask. Construction alternative if full-dossier over-reasons."""
    dis = "dry age-related macular degeneration (geographic atrophy)"
    return f"""You are an independent judge in a blinded pairwise review of candidate therapeutic-mechanism proposals.

Disease: {dis}

Candidate A:
{ca['name']}
Mechanism: {ca['mechanism']}
Targets: {', '.join(ca['targets'])}
Feasibility: {ca['feasibility'].split('.')[0]}.

Candidate B:
{cb['name']}
Mechanism: {cb['mechanism']}
Targets: {', '.join(cb['targets'])}
Feasibility: {cb['feasibility'].split('.')[0]}.

Judge on SCIENCE (mechanistic depth, disease relevance), FEASIBILITY (tractability with current tools), NOVELTY (distance from saturated mainstream), then overall winner. Decide efficiently; do not deliberate at length.

Output STRICT JSON only, no other text:
{{"winner": "A" or "B", "science": "A" or "B" or "tie", "feasibility": "A" or "B" or "tie", "novelty": "A" or "B" or "tie", "reasoning": "<2-4 sentences>"}}
Output the JSON object and nothing else."""


def report(tag, rec):
    obj, tier = gen2_parse.parse_object(rec.get("text"))
    v, probs = (None, [tier]) if obj is None else gen2_parse.validate_verdict(obj)
    print("%s: ok=%s stop=%s out=%s rt=%s | parse=%s verdict_ok=%s %s"
          % (tag, rec["ok"], rec.get("stop_reason"), rec.get("output_tokens"),
             rec.get("reasoning_tokens"), tier, v is not None, probs))


import pipeline_prompts as PP
full_prompt = PP.t2_judge_prompt("dAMD", ca, cb)
rec = gen2_call.call("glm", full_prompt, 8192, call_id="pilot/t2_judge/8192_1",
                     about={"task_class": "judging", "pilot": True})
report("T2-full@8192", rec)

slim = slim_t2_prompt("dAMD", ca, cb)
rec2 = gen2_call.call("glm", slim, 2048, call_id="pilot/t2_slim/2048_1",
                      about={"task_class": "judging", "pilot": True})
report("T2-slim@2048", rec2)
