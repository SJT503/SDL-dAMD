#!/usr/bin/env python3
"""Decisive web_search test: a question parametric memory cannot answer."""
import json
import time

import gen2_call

tools = [{"type": "web_search",
          "web_search": {"enable": True}}]
prompt = ("Use the web search tool to find: what is the current spot exchange "
          "rate of USD to CNY today, and what is today's date? You must call "
          "the search tool; do not answer from memory. Give the numbers the "
          "search returned and cite the source URL.")
rec = gen2_call.call(
    "glm", prompt, 4096,
    call_id="certify/retrieval/forced_search/%s"
            % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
    about={"task_class": "certify", "probe": "forced_search"},
    tools=tools)
print("ok=%s stop=%s out=%s rt=%s"
      % (rec["ok"], rec.get("stop_reason"), rec.get("output_tokens"),
         rec.get("reasoning_tokens")))
d = json.load(open(rec["raw_path"], encoding="utf-8"))
msg = (d.get("choices") or [{}])[0].get("message") or {}
print("tool_calls:", json.dumps(msg.get("tool_calls"))[:400])
print("text:", (rec.get("text") or "")[:500].replace("\n", " "))
