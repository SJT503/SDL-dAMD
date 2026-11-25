# Deviations Log — Generation 2

**Governing document**: PREREG_v2_FROZEN_v1.1.md (OSF-registered DOI 10.17605/OSF.IO/KF2G8)
**Format**: append-only, per-entry SHA-256 sealed (same mechanics as gen-1)
**Clock convention**: all timestamps UTC

---

## Registry

| Event | UTC | Note |
|---|---|---|
| OSF registration completed | 2026-09-03T13:28Z | DOI 10.17605/OSF.IO/KF2G8; 5 files attached; public immediately |
| Probe v2 completed (both endpoints) | 2026-09-03T~09:40Z | GLM (Coding Plan endpoint) + DeepSeek; all checks recorded |
| First experimental call | 2026-09-04T20:58Z | smoke pair (1 GLM + 1 DeepSeek) via gen2_call; then canary baseline 20/20 ok (2026-09-04T21:00Z) |
| D2-002 data-dir reset | 2026-09-04T21:35Z | see entry below; canary baseline re-established 2026-09-04T21:52Z (20/20 ok, isolated mock root shipped) |
| D2-003 retrieval-arm implementation | 2026-09-04T21:55Z | see entry below |
| D2-004 Experiment-B stage-2 max_tokens 2048 → 8192 | 2026-09-04T22:40Z | see entry below |
| D2-005 unified task max_tokens = 16384 (B stage-2 8192→16384; C 1024→16384) | 2026-09-04T23:59Z | see entry below |
| D2-006 task caps 16384 → 32768 (worst-case recall reasoning needs >16K; GLM-5.3 max output 128K) | 2026-09-05T00:15Z | see entry below |
| D2-007 client timeout 300s → 900s; residual-truncation handling rule for C | 2026-09-05T00:50Z | see entry below |
| D2-008 second runs/ deletion; recovery from raw archives; concurrency added | 2026-09-05T02:0xZ | see entry below |
| D2-009 step-1 generation tasks 8192 → 32768; blind redraft mechanism | 2026-09-05T03:1xZ | see entry below |
| D2-010 blind redraft budget 2 → 4 (ALS bucket2 TAM-axis attractor) | 2026-09-06T03:2xZ | see entry below |
| D2-011 step-6 protocol caps 8192 → 32768; failed-slot resume; parse_json bracket-order fix | 2026-09-06T11:5xZ | see entry below |
| Author ruling — DS off-peak-only billing | 2026-09-06T12:5xZ | peak windows (Mon-Fri 01:00-04:00 & 06:00-10:00 UTC, verified live) are gated: DS dispatches sleep through them and resume at half-rate; ledger keeps peak-rate accounting as the conservative guard. §10.1's off-peak clause is satisfied: all DS arms run off-peak. |

---

## D2-011 — Step-6 protocol caps 8192 → 32768; failed-slot resume; parse bracket-order fix (recorded 2026-09-06T11:5xZ)

**Clause affected**: D2-009's Scope line ("step-6 protocols stay 8192 pending
observed behaviour") — behaviour now observed.

**Evidence**: after the 12-run sweep, 40/60 step-6 protocol slots (67%) were
`failed` with `refs=None`; the call log shows 43/65 step-6 calls
`stop_reason=length` at 8192, all-reasoning empties — identical failure class
to D2-009's synthesiser. Separately, one dossier (`ALS_blind_R2/step3/c09`)
exposed a parser defect: `parse_json`'s bracket_scan tried `[` before `{`
unconditionally, so an unclosed-fence JSON OBJECT was mis-grabbed as its first
internal array ("not_an_object"). No data was altered — the archive was
re-parsed correctly after the fix.

**Action**:
1. step-6 calls → 32768 with `_gen_or_redispatch` (stale 8192 archives
   auto-revived; fresh parse failures recorded as model behaviour);
2. step-6 resume now re-dispatches ONLY failed slots (completed protocols are
   kept byte-identical); the step returns `protocols_failed(n/5)` if any
   remain failed rather than silently "done";
3. `gen2_parse.parse_json` bracket_scan order now follows whichever bracket
   appears first in the text (object-before-array when the object opens first).

**Dimension-① note**: 60 protocol reference-slots per run (5×6) are the
primary faithfulness material; the 20 completed 8192-era protocols are
retained unchanged, the 40 failed slots are re-dispatched under the new cap
with identical call_ids.

sha256(this entry body through end of Dimension-① note): `0bd88ab1bb01b8a0ff57e8b7aa4366ea9db8e46544c564bc681b443aaf80397e`

## D2-010 — Blind-redraft budget per step-1 bucket raised 2 → 4 (recorded 2026-09-06T03:2xZ)

**Clause affected**: D2-009's redraft mechanism (operationalisation of §2.1
"any hit voids the run and forces redraft" — the clause itself sets no retry
budget).

**Evidence**: ALS_blind_R2's bucket-2 (intercellular/immune bucket) drew
dAMD-leak tokens in three consecutive independent samples (original: ITGB5,
ITGAV; rd1: GAS6, ITGAV; rd2: MERTK — logged under
`parent/ALS_blind_R2/step1/bucket2*`). The TAM-receptor/phagocytosis axis is a
genuine ALS neuroinflammation attractor for the model, so repeated hits are
substantive associations, not formatting noise. With the budget of 2 the run
parked as blind-blocked while 11/12 runs completed.

**Action**: bucket redraft budget 2 → 4 (attempts 0..4). If a bucket still
hits after 4 independent samples, the run is reported as
`blind-blocked` — itself an honest, reportable boundary finding of the blind
protocol (attractor-strength vs leakage-control trade-off), and the affected
arm's analyses proceed on the remaining runs (noted wherever the ALS-blind
arm has n=2 instead of 3).

**No protocol constant changed**: the forbidden lists, scan points and the
void-and-redraft rule are exactly as frozen; only the retry budget of the
redraft loop (harness construction) is widened.

sha256(this entry body through end of No-protocol line): `2c828c76738cbfbbf90411f3906e88dbd464e1cfceef774b1ff996b9926a16b9`

## D2-009 — Step-1 (litreview) caps 8192 → 32768; one-shot blind redraft (recorded 2026-09-05T03:1xZ, before any parent run proceeds past step 1)

**Clause affected**: D2-001's 8192 for parent-pipeline judging/generation;
refined — step-1 is a LARGE-OUTPUT generation task (synthesiser emits 30
mechanism statements ≈ 8-12K tokens of content alone), unlike the short-JSON
judging tasks D2-001's pilots measured.

**Evidence**: first parent-plan pass (2026-09-05T02-3xZ): 12/12 runs failed at
step-1 synthesiser — `stop=length` truncations producing unparseable partial
JSON (e.g. `parent__dAMD_blind_R1__step1__synth` archive: 349 chars of a
~10K-char array). Buckets (12-mechanism outputs) completed at 8192; the
synthesiser output volume does not fit. Same §1.3 not-load-bearing authority
as D2-001/005/006.

**Also here — blind-redraft mechanism (§2.1 operationalised)**: one ALS bucket
response contained a dAMD-leak token (e.g. a TAM-receptor mechanism naming
MERTK/GAS6 in the ALS context), which then contaminated the synthesiser prompt
and tripped the pre-dispatch prompt scan. Per §2.1 ("any hit voids the run and
forces redraft"), the driver now: (a) scans each bucket's PARSED OUTPUT before
it enters any later prompt, (b) on a hit, re-dispatches that bucket once under
a fresh session (`/rd1` call_id suffix; the hit response stays in the log),
(c) same one-shot redraft for synthesiser outputs; a run whose second attempt
still hits is parked as `blind_violation_stuck` for author ruling rather than
silently re-rolled indefinitely. Prompt-level hits (template text) remain hard
stops — only model-output contamination is redraftable.

**Scope**: step-1 bucket + synthesiser calls → 32768 (all arms, both diseases).
T1/T2 judging stays 8192 (short-JSON outputs, pilots ≤1.5K tokens); step-6
protocols stay 8192 pending observed behaviour.

sha256(this entry body through end of Scope): `a1fcc118afc5104bd341b250784f3b4c459d48187c2c4f937177c0cd5a35a15e`

## D2-008 — Second accidental `rm -rf runs`; canonical files rebuilt from raw archives; concurrent dispatch added (recorded 2026-09-05T02:0xZ)

**What happened**: while cleaning up after a mock dry-run of the parent driver,
`rm -rf runs` was executed with the live Experiment-B chain still running,
deleting the canonical `runs/expB` tree (≈101 completed slot files + 13/14
stage-1 files at that moment). Same failure class as D2-002 (mock/live
separation held for `data/` but `runs/` was still shared). The chain was
stopped immediately.

**Recovery (zero re-dispatch)**: `data/raw/` archives were intact (archives
store each call_id's LAST response). `recover_expB_from_raw.py` re-parsed every
archive and rebuilt 13/14 stage-1 files and 101 stage-2 slot files
byte-equivalently; the one unparseable archive (B12 stage-1, a 2048-cap
truncation from the second stage-1 pass) and the 109 never-completed slots are
re-dispatched by normal resume. No scientific data lost; no fabricated data.

**Hardening shipped with this entry**:
1. Mock runs now also redirect RESULTS/outputs: drivers' mock roots cover
   `runs/` paths (C driver's results file was already redirected; a mock
   parent run now writes to an isolated root by convention — enforced by the
   harness data-root switch).
2. Experiment-B stage-1 max_tokens unified at 32768 (B12's truncation shows the
   same long-tail as stage-2; same D2-005/006 rationale).
3. Concurrent dispatch added to cut wall-clock to the preregistered 1-3-day
   execution window: C driver `--workers`, parent steps 2/4 `GEN2_WORKERS`
   (seeded interleaving preserved — job order is fixed by the shuffle;
   completion order under concurrency is irrelevant to the frozen order).
   Ledger/log writes are lock-protected (RLock, unique tmp names).

sha256(this entry body through end of item 3): `247134e3543d20263142003e13484b9ff9c07d7906121918a07eaede30efcc6a`

## D2-007 — Client read timeout 300s → 900s; residual truncations handled as excluded-truncation (recorded 2026-09-05T00:50Z)

**Clause affected**: none of the frozen constants — transport-layer parameter
and an analysis-inclusion rule for an event the prereg did not specify.

**Part 1 — timeout**: at effort=high, generating 12–30K reasoning tokens takes
2–8+ minutes; the harness's original 300 s read timeout killed three C-pilot
calls mid-generation (`TimeoutError`, logged 2026-09-05T00:2xZ). A client-side
timeout is transport behaviour, not model behaviour — it would masquerade as
missing data. Default raised to 900 s; timeouts remain retryable transport
failures (re-dispatched on resume).

**Part 2 — residual truncation rule**: even at 32768, one C slot
(`expC_v4/glm/del_topIC/d0/V001/r1`) burned 32,766 reasoning tokens without
answering. Rather than escalate caps indefinitely, the rule is: a call whose
`stop_reason=length` yields an empty answer is recorded verbatim (parse_tier
`empty_response`, n_pred=0) and analysed as **excluded-truncation** — excluded
from the recall@10 denominator, counted and reported per vendor × arm × dose
as a behavioural endpoint in its own right (unbounded deliberation without
commitment). No further cap escalation.

sha256(this entry body through end of Part 2 paragraph): `7568a916bedf00744c4c0cbddcb9a750c98b5ce81c0d9df5789e27e8698d8572`

## D2-006 — Experiment task caps raised 16384 → 32768 (recorded 2026-09-05T00:15Z, before any B slot or C pair is scored)

**Clause affected**: D2-005's 16384 for B stage-2 and C-v4.

**Evidence (logged, same call_id as D2-005's truncation)**:
`expB/glm/stage2/as_discovered/B02/h3` @16384 (2026-09-05T00:05Z):
`stop_reason=length`, 16384/16384 tokens all reasoning. The same slot @32768
(00:08Z): `stop=stop`, 17,593 output tokens (17,073 reasoning + 520 content),
strict JSON with 6 numeric PMIDs. Genuine recall reasoning on this slot needs
>16K; 32768 (a quarter of GLM-5.3's documented 128K max output) completes it.

**Rationale**: identical to D2-005 — the cap must exceed the model's honest
reasoning consumption or the endpoint denominators break. Cost note: thinking
tokens bill as output (Coding Plan quota for GLM; DeepSeek pay-as-you-go within
the $400 guard).

**Scope**: B stage-2 and C-v4 calls on both vendors → 32768. Parent pipeline
(8192, D2-001) unchanged — its T1/T2 verdict pilots completed at ≤1.5K tokens.
Truncated prior dispatches remain in the log; re-dispatches carry identical
call_ids.

sha256(this entry body through end of Scope line): `414e2ab543f6b6b6c82b81025694e85e191c20b7f9ecd3c32ff2587648862d5c`

## D2-005 — All experiment task caps unified at max_tokens = 16384 (recorded 2026-09-04T23:59Z, before any B slot or C pair is scored)

**Clause affected**: §1.3 task-class values for Experiment B (2048, revised to
8192 by D2-004) and Experiment C (1024); revises both.

**Evidence (all logged)**:
- B stage-2 @8192 re-dispatch (2026-09-04T23:53Z, `expB/glm/stage2/as_discovered/B02/h3`):
  `stop_reason=length`, 8192/8192 tokens, 8190 reasoning; the archived
  reasoning_content (26,185 chars) shows genuine per-candidate PMID recall and
  directionality checking, cut mid-way through slot 5 of 6 — divergence, not
  looping.
- C-v4 pilot (6 real calls, `expC_v4/glm/del_*/d*/V001/r1`, frozen 1024):
  6/6 `stop_reason=length`, all 1020–1024 tokens consumed by reasoning,
  empty content.

**Rationale**: at effort=high, glm-5.3's reasoning consumption on recall/
judgment tasks ranges ~1K–10K+ tokens regardless of the (short) final answer
size. The pre-registered caps (1024/2048) assumed answer-size-scaled budgets;
they measure the harness, not the model. Truncation of the reasoning eliminates
the answer entirely, voiding the fabrication/abstention (B) and recall@10 (C)
denominators — a broken instrument, not a model-behaviour finding. A compressed
"think less" prompt instruction would contaminate the measured behaviour itself
and is rejected. The cap is a ceiling, not a spend target; short-reasoning
calls still terminate in hundreds of tokens. Same §1.3 authority as D2-001
("not pre-registered as load-bearing; recorded per call").

**Scope**: B stage-2 and all C-v4 calls → 16384 (parent pipeline already 8192
per D2-001 and unaffected). Canary stays 2048 (short tasks, baseline
comparability). Uniform per task class, no per-call selection. The truncated
prior dispatches remain in the log; re-dispatches carry identical call_ids.

sha256(this entry body through end of Scope line): `02c31806f1d1a707368a53f47fbc001796ea3f0f3a08ff17d7be41bd30a7586f`

## D2-004 — Experiment-B stage-2 max_tokens raised 2048 → 8192 (recorded 2026-09-04T22:40Z, before any B slot is scored)

**Clause affected**: §1.3 ("Experiment-B JSON = 2048"); revises D2-001's split
(which had retained 2048 for B on the strength of a single gated-arm pilot).

**What happened**: the first real B stage-2 pass (210 calls, glm-5.3, effort=high)
produced 159/210 truncations (`stop_reason=length`, 2048/2048 tokens consumed by
reasoning, content empty, verdict unparseable), distributed across all three arms
(as_discovered 65, gated 32, abstain_probe 62). 36/210 calls completed at 2048 and
are retained unchanged (their output files exist; the resume logic skips them).
The D2-001 gated-arm pilot (287 reasoning tokens) sampled the arm's easy path
(fast abstention) and underestimated reasoning consumption on genuine
PMID-recall effort.

**Action**: stage-2 calls re-dispatched at max_tokens=8192 (driver default
changed; the 36 completed slots are not re-run). Same authority as D2-001
(§1.3 "not pre-registered as load-bearing; recorded per call"). The 159
truncated raw responses remain in the append-only log as the record of this
event; re-dispatches carry the same call_id with max_tokens=8192.

**Also recorded here (same execution window)**: the parent-plan launcher crashed
on a transient NCBI SSL reset during retrieval-context fetch; fetch retry
hardened (8 tries, capped backoff) and the interleaved loop now isolates a
blocked run instead of dying. No data affected.

sha256(this entry body through end of Also line): `815920e03bb9191134339cb3703e6cc8954017a5c6d4d1ebe1624a23aca20c15`

## D2-003 — Retrieval arm implemented by PubMed context injection (web_search tool not executable on the certified endpoint; recorded 2026-09-04T21:55Z)

**Clause affected**: §5.2 "retrieval tools enabled" in the retrieval arm.

**What**: the retrieval arm runs the same six-step pipeline with blind tokens
lifted and a deterministic PubMed context block injected into step-1 bucket and
step-3 dossier prompts (frozen neutral MeSH query per disease, 20 best-match
records, fetched once per run, SHA-256 + fetch UTC logged per run). The GLM
`web_search` API tool is NOT used.

**Evidence** (logged calls `certify/retrieval/*`, 2026-09-04): the Coding Plan
endpoint ACCEPTS a `tools` block (billed ~2.5K extra prompt tokens) but the tool
never executes — (a) with-tool and no-tool answers to a GWAS question are both
parametric-knowledge answers, no tool_calls in any response; (b) a forced-search
probe asking for a live exchange rate returns the model's own statement: "I
don't have access to a web search tool in this conversation".

**Why this satisfies §5.2**: the dimension-② endpoint compares the pipeline's
self-consistency under two information conditions (blind vs retrieval-aided).
Context injection is a real, logged, per-run-frozen information channel to the
published literature — functionally the retrieval the clause asks for, executed
deterministically rather than via a vendor tool that does not execute on the
certified endpoint. The injection prompt text is frozen in
`pipeline_prompts.py` (SHA recorded in run manifests).

sha256(this entry body through end of Why line): `1be2c3d71ea752bc851eb25471416856c7a1d69273d879fe72a3e62f5de0e545`

## D2-002 — Harness data directory reset removed 30 real probe/canary records (recorded 2026-09-04T21:35Z)

**What happened**: before the full 12-run mock dry-run of the parent pipeline, the
harness data directory (`GEN2_exec/data`, `GEN2_exec/runs`) was wiped to prevent
mock-mode records from contaminating the live resume index. The wipe also removed
the records of ~30 already-made REAL calls: the smoke pair, the web-search
certification pair, 5 max_tokens pilots (D2-001 evidence), and the 20-call canary
baseline of 2026-09-04.

**Impact**: (a) D2-001's pilot call_ids (`pilot/*`) no longer resolve to raw
archives — the observed token counts quoted in D2-001 are preserved verbatim in
that entry's text and stand as the record; (b) the canary baseline must be
re-established before the first experimental block of the execution window (cost
≈ $0.01); (c) no experimental (B/C/parent) data existed yet — zero scientific
data affected.

**Remediation**: canary baseline re-run logged as the first block after the
harness build completes; harness hardened so mock dry-runs write to a separate
`GEN2_MOCK_DATA` root by default, preventing recurrence.

sha256(this entry body through end of Remediation line): `6f940c548e87151db4c2944d597dd9f39a3e3b0e38e4f7302ec844e578d92ae2`

## D2-001 — Pipeline judging/generation max_tokens raised 2048 → 8192 (pre-first-pipeline-call, recorded 2026-09-04T21:20Z)

**Clause affected**: §1.3 task-class table ("judging and Experiment-B JSON = 2048").

**What**: Parent-pipeline model calls (Tournament I verdicts, Tournament II verdicts,
step-3 candidate dossiers) use `max_tokens = 8192`, not 2048. Experiment B stays
2048; Experiment C stays 1024 (unchanged).

**Evidence (logged pilot calls, `data/calls_log.jsonl`, call_ids `pilot/*`)**:
- T1-style judge @2048: completed (1551/2048 tokens; 1398 reasoning) — thin margin.
- T2-style judge @2048: `finish_reason=length`, 2048/2048 tokens all reasoning,
  content empty, verdict unparseable.
- T2-style judge @4096: truncated identically (4096/4096 reasoning).
- T2-style judge @8192: completed (964 tokens, 667 reasoning), strict JSON.
- Experiment-B gated stage-2 @2048: completed (654 tokens), strict JSON — frozen
  value retained for B.

**Authority**: §1.3 itself states the max_tokens values are "recorded per call;
not pre-registered as load-bearing (gen-1 D-004 item 4 precedent)". At
effort=high, glm-5.3 reasoning consumption on multi-dossier judgment tasks can
exceed 2048 and 4096; a truncation is not interpretable as model behaviour on
the judgment task (it is a harness cap), so completing the task class within
the cap is required for the fairness/verdict endpoints to measure anything.

**Scope**: applies to all pipeline judging/generation calls in both arms and
both diseases, uniformly (no per-call selection). Recorded per call in the
§1.4 log (max_tokens field). Cost impact: none (cap, not spend).

sha256(this entry body through end of Scope line): `b4d5400a3313eaa68c32ff0e7842eff0c17a47a447890475544f52bc1942f1a2`

