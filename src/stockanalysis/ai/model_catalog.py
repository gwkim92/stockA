"""Read public model identifiers from the installed authenticated Codex CLI."""
from __future__ import annotations

import json
import queue
import shlex
import os
import subprocess
import threading
import time
from typing import Any


def load_codex_catalog() -> list[dict[str, Any]]:
    base = shlex.split(os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex"))
    process = subprocess.Popen([*base, "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    messages: queue.Queue[Any] = queue.Queue()

    def reader() -> None:
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                pass
        messages.put(None)

    threading.Thread(target=reader, daemon=True).start()
    deadline = time.monotonic() + 45

    def request(method: str, request_id: int, params: dict[str, Any]) -> dict[str, Any]:
        process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        while True:
            message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            if message is None or time.monotonic() > deadline:
                raise RuntimeError("Codex model catalog unavailable")
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError("Codex model catalog rejected")
                return message["result"]

    try:
        request("initialize", 0, {"clientInfo": {"name": "stockanalysis_model_settings", "version": "1.0.0"}})
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        models, cursor = [], None
        for request_id in range(1, 11):
            page = request("model/list", request_id, {"limit": 100, "includeHidden": False, **({"cursor": cursor} if cursor else {})})
            models.extend({"id": row["model"], "label": row.get("displayName") or row["model"], "hidden": bool(row.get("hidden"))} for row in page.get("data", []) if not row.get("hidden"))
            cursor = page.get("nextCursor")
            if not cursor:
                return models
        raise RuntimeError("Codex model catalog pagination incomplete")
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
