#!/usr/bin/env python3
"""
gen2_call.py -- dual-vendor call layer for gen-2 (GLM glm-5.3 + DeepSeek deepseek-v4-pro).

Implements PREREG_v2_FROZEN_v1.1:
  §1.3 frozen constants  temperature=1.0, top_p=0.95, effort=high (every call)
  §1.4 per-call logging  18-field schema, append-only JSONL, one record per call
  §1.5 independent dispatch  fresh session id + empty context + prompt SHA-256 +
                         session-creation UTC (API calls are stateless; every call
                         is one dispatch, context_empty=true by construction)
  §10.3 budget guards  per-vendor cumulative ledger, DeepSeek USD estimate at
                         PEAK rates (conservative), hard stop before dispatch

Design inherited from gen-1 bc_api.py (raw urllib, retry transport only,
credentials never logged, mock mode). A refusal/abstention/malformed body is
MODEL BEHAVIOUR and is recorded, never retried away.

Credentials: GLM key file  ../GEN2_prereg/.glm_key   (or GEN2_GLM_KEY_FILE)
             DS  key file  .ds_key next to this file (or GEN2_DS_KEY_FILE)
Mock mode:   GEN2_MOCK=1  -> no network; canned JSON so drivers can be dry-run.
"""

import hashlib
import json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# Mock dry-runs write to an isolated root so they can NEVER pollute the live
# audit trail (D2-002 remediation). Override with GEN2_MOCK_DATA if desired.
if os.environ.get("GEN2_MOCK"):
    DATA = os.environ.get("GEN2_MOCK_DATA") or os.path.join(HERE, "data_mock")
else:
    DATA = os.path.join(HERE, "data")
RAW_DIR = os.path.join(DATA, "raw")
LOG_PATH = os.path.join(DATA, "calls_log.jsonl")
LEDGER_PATH = os.path.join(DATA, "budget_ledger.json")

REDACTED = "<REDACTED>"

# Serialises ledger read-modify-write within one process (multi-threaded
# drivers). Cross-process JSONL appends verified safe in practice (O_APPEND
# single-line writes; 265/265 intact under observed concurrency).
_LOCK = threading.RLock()   # re-entrant: ledger helpers nest inside budget_update's lock

# Verified 2026-09-05: api-docs.deepseek.com/quick_start/pricing (USD / 1M tokens)
# Budget guard uses PEAK rates -> the live estimate never underestimates spend.
DS_PRICE = {"in": 1.32, "out": 3.96}
DS_USD_HARD_STOP = 400.0          # §10.3: $500 ceiling; stop early pending author ruling
GLM_CALL_HARD_STOP = 200000       # absolute call ceiling (quota is window-limited; ledger tracks)

VENDORS = {
    "glm": {
        "endpoint": "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions",
        "model": "glm-5.3",
        "key_file": os.path.join(HERE, "..", "GEN2_prereg", ".glm_key"),
    },
    "deepseek": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-v4-pro",
        "key_file": os.path.join(HERE, ".ds_key"),
    },
}

FROZEN = {"temperature": 1.0, "top_p": 0.95,
          "thinking": {"type": "enabled", "reasoning_effort": "high"}}


class ConfigError(RuntimeError):
    pass


class BudgetStop(RuntimeError):
    """Raised BEFORE dispatch when a budget guard trips. Nothing is spent."""


def _load_key(vendor):
    env = os.environ.get("GEN2_GLM_KEY_FILE" if vendor == "glm" else "GEN2_DS_KEY_FILE")
    path = env or VENDORS[vendor]["key_file"]
    if not os.path.exists(path):
        raise ConfigError("key file not found for %s: %s" % (vendor, path))
    k = open(path, encoding="utf-8").read().strip()
    if not k:
        raise ConfigError("key file empty: %s" % path)
    return k


def _assert_clean(obj, key):
    if not key:
        return obj
    blob = json.dumps(obj, ensure_ascii=False, default=str)
    if key in blob or (len(key) > 12 and key[:12] in blob):
        raise RuntimeError("refusing to emit a record containing credential material")
    return obj


def _safe_id(call_id):
    return re.sub(r"[^A-Za-z0-9._-]+", "__", call_id)


# ---------------------------------------------------------------- budget ----
def _read_ledger():
    with _LOCK:
        if os.path.exists(LEDGER_PATH):
            try:
                return json.load(open(LEDGER_PATH, encoding="utf-8"))
            except Exception:                                    # noqa: BLE001
                pass
        return {"glm": {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                        "reasoning_tokens": 0},
                "deepseek": {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                             "reasoning_tokens": 0, "est_cost_usd_peak": 0.0}}


def _write_ledger(led):
    # unique tmp name per writer thread; callers hold _LOCK
    os.makedirs(DATA, exist_ok=True)
    tmp = "%s.%d.tmp" % (LEDGER_PATH, threading.get_ident())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(led, fh, indent=1)
    os.replace(tmp, LEDGER_PATH)


def budget_check(vendor):
    """Pre-dispatch guard (§10.3). Raises BudgetStop; returns ledger row."""
    led = _read_ledger()
    row = led.get(vendor) or _read_ledger()[vendor]
    if vendor == "deepseek" and row.get("est_cost_usd_peak", 0.0) >= DS_USD_HARD_STOP:
        raise BudgetStop(
            "DeepSeek estimated spend $%.2f >= hard stop $%.2f (peak-rate "
            "estimate). Author ruling required (§10.3). Ledger: %s"
            % (row["est_cost_usd_peak"], DS_USD_HARD_STOP, LEDGER_PATH))
    if vendor == "glm" and row.get("calls", 0) >= GLM_CALL_HARD_STOP:
        raise BudgetStop("GLM call count %d >= hard stop %d"
                         % (row["calls"], GLM_CALL_HARD_STOP))
    return row


# DS off-peak gate (author ruling 2026-09-06): peak = Mon-Fri 01:00-04:00 and
# 06:00-10:00 UTC (verified live at api-docs.deepseek.com/quick_start/pricing);
# everything else, including all of Sat/Sun, is half-price off-peak. DS
# dispatches SLEEP through peak windows and resume automatically -- no call is
# ever billed at peak rate. GLM is unaffected (subscription quota).
def _ds_peak_seconds_remaining(now=None):
    import calendar
    import datetime as _dt
    now = now or _dt.datetime.utcnow()
    peak_windows = ((1, 0), (4, 0), (6, 0), (10, 0))   # (start,end) hours UTC
    if now.weekday() >= 5:                              # Sat/Sun: all off-peak
        return 0.0
    for start, end in ((1, 4), (6, 10)):
        if start <= now.hour < end:
            # seconds until this window ends
            end_dt = now.replace(hour=end, minute=0, second=0, microsecond=0)
            return (end_dt - now).total_seconds()
    return 0.0


def ds_offpeak_gate(call_id):
    """Block until DeepSeek billing is off-peak. Called before every DS
    dispatch; logs one line per wait so the pause is auditable."""
    wait = _ds_peak_seconds_remaining()
    if wait <= 0:
        return
    import sys
    print("[ds-offpeak-gate] %s: peak billing window active -- sleeping "
          "%.0f min until off-peak (half-rate) resumes"
          % (call_id, wait / 60.0), file=sys.stderr, flush=True)
    time.sleep(wait + 30)      # 30s margin past the boundary


def budget_report():
    led = _read_ledger()
    ds = led["deepseek"]
    ds["est_cost_usd_peak"] = round(
        (ds["input_tokens"] / 1e6) * DS_PRICE["in"]
        + (ds["output_tokens"] / 1e6) * DS_PRICE["out"], 4)
    return led


def budget_update(vendor, in_tok, out_tok, reason_tok):
    with _LOCK:
        led = _read_ledger()
        row = led[vendor]
        row["calls"] += 1
        row["input_tokens"] += in_tok or 0
        row["output_tokens"] += out_tok or 0
        row["reasoning_tokens"] += reason_tok or 0
        if vendor == "deepseek":
            row["est_cost_usd_peak"] = round(
                (row["input_tokens"] / 1e6) * DS_PRICE["in"]
                + (row["output_tokens"] / 1e6) * DS_PRICE["out"], 4)
        _write_ledger(led)
    return row


# ------------------------------------------------------------------- log ----
_LOG_CACHE = {"stamp": None, "ids": {}}


def logged_call_ids():
    """call_id -> ok for every record in the log (resume checkpoint index).

    Cached on (file size, mtime) so thousands of resume checks do not re-read
    the whole log each time. Cache is invalidated by any append (size change).
    """
    if not os.path.exists(LOG_PATH):
        return {}
    st = os.stat(LOG_PATH)
    stamp = (st.st_size, st.st_mtime_ns)
    if _LOG_CACHE["stamp"] == stamp:
        return _LOG_CACHE["ids"]
    out = {}
    with open(LOG_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:                                # noqa: BLE001
                continue
            if "call_id" in rec:
                prev = out.get(rec["call_id"])
                # a later ok=True record supersedes an earlier failure
                if prev is None or rec.get("ok"):
                    out[rec["call_id"]] = bool(rec.get("ok"))
    _LOG_CACHE["stamp"] = stamp
    _LOG_CACHE["ids"] = out
    return out


def _append_log(rec):
    with _LOCK:
        os.makedirs(DATA, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _archive_raw(call_id, payload):
    os.makedirs(RAW_DIR, exist_ok=True)
    p = os.path.join(RAW_DIR, _safe_id(call_id) + ".json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, default=str)
    return p


# ------------------------------------------------------------------ mock ----
def _mock_text(prompt, call_id, mock_parse_ok):
    """Schema-aware canned output so the full pipeline can be dry-run offline.

    Mock output is NEVER scientific data: every raw payload carries mock=True
    and the model id is suffixed '-mock'.
    """
    h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
    tail = "MOCK %s sha:%s" % (call_id, h)
    if not mock_parse_ok:
        return tail
    import re
    if '"winner"' in prompt and '"reasoning"' in prompt:
        return json.dumps({"winner": "A" if int(h[:2], 16) % 2 == 0 else "B",
                           "science": "A", "feasibility": "B",
                           "novelty": "tie", "reasoning": tail})
    m = re.search(r"exactly (\d+) (?:objects|references|distinct)", prompt)
    if m:
        n = int(m.group(1))
        return json.dumps([{"mock": i + 1, "id": i + 1, "call_id": call_id,
                            "mechanism": "mock mechanism %d; %s" % (i + 1, tail),
                            "key_players": ["MOCK%d" % (i + 1)],
                            "class_hint": "cell_intrinsic",
                            "confidence": 50,
                            "name": "MockCandidate%d" % (i + 1),
                            "targets": ["MOCKG%d" % (i + 1)],
                            "intervention_principle": tail,
                            "rationale": tail, "feasibility": tail,
                            "slot": i + 1, "pmid": "1000000%d" % (i + 1),
                            "claim": tail}
                           for i in range(n)])
    m2 = re.search(r"exactly 6 published references", prompt)
    if m2:
        return json.dumps({"protocol_name": tail, "aim": tail,
                           "model_system": tail, "intervention": tail,
                           "primary_readout": tail, "controls": [tail],
                           "references": [{"slot": i + 1,
                                           "pmid": "1000000%d" % (i + 1),
                                           "claim": tail} for i in range(6)]})
    if '"name"' in prompt and '"targets"' in prompt:      # step-3 dossier shape
        return json.dumps({"name": "MockCandidate_" + h[:4],
                           "mechanism": tail, "targets": ["MOCKG1"],
                           "intervention_principle": tail, "rationale": tail,
                           "feasibility": tail, "confidence": 50})
    return tail


# ------------------------------------------------------------------ call ----
def call(vendor, prompt, max_tokens, *, call_id, system=None, about=None,
         tools=None, timeout=900, max_tries=6, expect_error=False,
         mock_parse_ok=True):
    """One model call -> §1.4 record (dict). `ok` False on non-retryable failure.

    timeout default 900 s: at effort=high, generation of 12-30K reasoning
    tokens takes 2-8+ minutes; the original 300 s read timeout killed deep
    calls mid-generation (observed 2026-09-05, 3 C-pilot calls). Timeouts are
    transport failures (retried, then re-dispatched on resume), never model
    behaviour.

    tools: optional list merged into the body (e.g. GLM web_search block for the
      retrieval arm). Recorded verbatim in the record so the arm is rebuildable.
    mock_parse_ok: in mock mode, return a canned strict-JSON-shaped text.
    """
    if vendor not in VENDORS:
        raise ConfigError("unknown vendor %r" % vendor)
    vconf = VENDORS[vendor]
    prompt_sha = hashlib.sha256((system or "") + "\x00" + prompt).hexdigest() if system else \
        hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    base = {
        "call_id": call_id,
        # ---- §1.4 schema (18 fields) ----
        "utc": None,                                  # filled on completion
        "vendor": vendor,
        "endpoint": vconf["endpoint"],
        "model_alias_passed": vconf["model"],
        "model_exact_id_returned": None,
        "thinking_effort": "high",
        "temperature": FROZEN["temperature"],
        "top_p": FROZEN["top_p"],
        "max_tokens": max_tokens,
        "prompt_sha256": prompt_sha,
        "prompt_chars": len(prompt),
        "input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "stop_reason": None,
        "raw_response_sha256": None,
        "session_id": None,                           # uuid4, below
        "session_created_utc": None,
        "context_empty": True,                        # stateless API: no context
        # ---- practical extras (schema-superset) ----
        "system_prompt_sha256": hashlib.sha256(system.encode()).hexdigest() if system else None,
        "ok": False,
        "status": None,
        "attempts": 0,
        "elapsed_s": None,
        "tools": tools or None,
        "about": about or {},
        "mock": bool(os.environ.get("GEN2_MOCK")),
    }

    import uuid
    base["session_id"] = str(uuid.uuid4())
    base["session_created_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    started = time.time()
    budget_check(vendor)                              # raises BudgetStop pre-dispatch
    if vendor == "deepseek":
        ds_offpeak_gate(call_id)                      # author ruling: half-rate only

    body = {
        "model": vconf["model"],
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}],
        "temperature": FROZEN["temperature"],
        "top_p": FROZEN["top_p"],
        "max_tokens": max_tokens,
        "thinking": {"type": "enabled", "reasoning_effort": "high"},
    }
    if tools:
        body["tools"] = tools

    # ------------------------------------------------------------ mock ----
    if base["mock"]:
        time.sleep(0.01)
        text = _mock_text(prompt, call_id, mock_parse_ok)
        payload = {"mock": True, "model": vconf["model"] + "-mock",
                   "choices": [{"message": {"content": text},
                                "finish_reason": "stop"}],
                   "usage": {"prompt_tokens": max(1, len(prompt) // 4),
                             "completion_tokens": max(1, len(text) // 4),
                             "completion_tokens_details": {"reasoning_tokens": 7}}}
        rec = dict(base)
        rec.update({
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model_exact_id_returned": payload["model"],
            "input_tokens": payload["usage"]["prompt_tokens"],
            "output_tokens": payload["usage"]["completion_tokens"],
            "reasoning_tokens": 7,
            "stop_reason": "stop",
            "raw_response_sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "ok": True, "status": 200, "attempts": 1,
            "elapsed_s": round(time.time() - started, 3),
        })
        rec["text"] = text
        rec["raw_path"] = _archive_raw(call_id, payload)
        _append_log(rec)
        budget_update(vendor, rec["input_tokens"], rec["output_tokens"], 7)
        return rec

    # ----------------------------------------------------------- live ----
    key = _load_key(vendor)
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context()
    url = vconf["endpoint"]
    last_err = None

    for attempt in range(1, max_tries + 1):
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                payload = json.loads(r.read().decode("utf-8", "replace"))
            usage = payload.get("usage") or {}
            ctd = usage.get("completion_tokens_details") or {}
            choice = (payload.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            text = msg.get("content") or ""
            reasoning_text = msg.get("reasoning_content")
            rec = dict(base)
            rec.update({
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "model_exact_id_returned": payload.get("model"),
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "reasoning_tokens": ctd.get("reasoning_tokens"),
                "stop_reason": choice.get("finish_reason"),
                "raw_response_sha256": hashlib.sha256(
                    json.dumps(payload, sort_keys=True,
                               ensure_ascii=False).encode()).hexdigest(),
                "ok": True, "status": r.status, "attempts": attempt,
                "elapsed_s": round(time.time() - started, 3),
            })
            rec["text"] = text
            rec["reasoning_chars"] = len(reasoning_text) if reasoning_text else 0
            rec["model_id_mismatch"] = (payload.get("model") != vconf["model"])
            rec["raw_path"] = _archive_raw(call_id, payload)
            _assert_clean(rec, key)
            _append_log(rec)
            budget_update(vendor, rec["input_tokens"], rec["output_tokens"],
                          rec["reasoning_tokens"])
            return rec

        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")[:2000]
            retryable = e.code == 429 or 500 <= e.code < 600
            last_err = {"status": e.code, "body_head": raw[:400]}
            if not retryable or attempt == max_tries or expect_error:
                rec = dict(base)
                rec.update({
                    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "ok": False, "status": e.code, "attempts": attempt,
                    "error": json.loads(_redact_json(raw, key)) if raw.startswith("{")
                             else raw[:400],
                    "elapsed_s": round(time.time() - started, 3),
                })
                _assert_clean(rec, key)
                _append_log(rec)
                return rec
        except Exception as e:                                # noqa: BLE001
            last_err = {"status": None, "body_head": repr(e)[:300]}
            if attempt == max_tries:
                rec = dict(base)
                rec.update({
                    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "ok": False, "status": None, "attempts": attempt,
                    "error": last_err,
                    "elapsed_s": round(time.time() - started, 3),
                })
                _assert_clean(rec, key)
                _append_log(rec)
                return rec
        time.sleep(min(60.0, 2.0 * (2 ** (attempt - 1))))

    rec = dict(base)
    rec.update({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "ok": False, "status": None, "attempts": max_tries,
                "error": last_err,
                "elapsed_s": round(time.time() - started, 3)})
    _assert_clean(rec, key)
    _append_log(rec)
    return rec


def _redact_json(text, key):
    out = str(text)
    if key:
        out = out.replace(key, REDACTED)
        if len(key) > 12:
            out = out.replace(key[:12], REDACTED)
    return out


# ------------------------------------------------------------ convenience ---
def call_ok(call_id):
    """Is this call_id already done-and-ok in the log? (resume check)"""
    return logged_call_ids().get(call_id) is True


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="budget report / tiny smoke call")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--smoke", choices=["glm", "deepseek"])
    a = ap.parse_args()
    if a.report or not a.smoke:
        print(json.dumps(budget_report(), indent=1))
    if a.smoke:
        rec = call(a.smoke, "Reply with exactly: ok", 64,
                   call_id="smoke/%s/%s" % (
                       a.smoke, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())),
                   about={"task_class": "smoke"})
        slim = {k: v for k, v in rec.items() if k != "text"}
        print(json.dumps(slim, indent=1, ensure_ascii=False, default=str))
        print("text:", (rec.get("text") or "")[:120])
