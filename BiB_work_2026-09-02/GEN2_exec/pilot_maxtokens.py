#!/usr/bin/env python3
"""max_tokens pilots before first pipeline call (T2@4096, B-gated@2048)."""
import gen2_call
import gen2_parse
import pipeline_prompts as PP

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

prompt = PP.t2_judge_prompt("dAMD", ca, cb)
rec = gen2_call.call("glm", prompt, 4096, call_id="pilot/t2_judge/4096_1",
                     about={"task_class": "judging", "pilot": True})
print("T2@4096: ok=%s stop=%s out=%s rt=%s"
      % (rec["ok"], rec.get("stop_reason"), rec.get("output_tokens"),
         rec.get("reasoning_tokens")))
obj, tier = gen2_parse.parse_object(rec.get("text"))
v, probs = (None, [tier]) if obj is None else gen2_parse.validate_verdict(obj)
print("  parse:", tier, "| verdict ok:", v is not None, probs)

import run_expB_gen2 as RB
spec = RB.load_spec("expB_prompts.json")
tmpl = spec["stage2_templates"]["gated"]
mech = ("ILC2-driven type-2 inflammation amplification via epithelial-derived "
        "TSLP activates STAT5-dependent effector programs in airway eosinophils")
prompt2 = tmpl.format(disease="Asthma", mechanism=mech)
rec2 = gen2_call.call("glm", prompt2, 2048, call_id="pilot/expB_gated/2048_1",
                      about={"task_class": "judging", "pilot": True})
print("B@2048: ok=%s stop=%s out=%s rt=%s"
      % (rec2["ok"], rec2.get("stop_reason"), rec2.get("output_tokens"),
         rec2.get("reasoning_tokens")))
obj2, tier2 = gen2_parse.parse_json(rec2.get("text"))
arr = obj2 if isinstance(obj2, list) else None
parsed, problems, fmt = (None, [tier2], []) if arr is None \
    else RB.validate_stage2(arr, 6)
print("  parse:", tier2, "| ok:", parsed is not None, problems)
if parsed:
    print("  pmids:", [x["pmid"] for x in parsed][:6])
