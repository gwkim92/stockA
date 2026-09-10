"""Narrow model-settings writes; read credentials alone never grant mutation."""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from stockanalysis.ai.model_settings import SettingsError, inventory, store_from_env

SESSION_HEADER = "X-Stockanalysis-Model-Session"


def register_model_settings_routes(app: FastAPI, authorize_read: Callable[..., Any]) -> None:
    async def respond(request: Request, action: str) -> JSONResponse:
        rejected = authorize_read(request)
        if rejected is not None:
            return rejected
        session = request.headers.get(SESSION_HEADER, "")
        try:
            if action == "read":
                payload = await run_in_threadpool(inventory, session)
                executor = getattr(app.state, "frontend_executor", None)
                payload["history_available"] = False
                if executor is not None:
                    try:
                        history = json.loads(await run_in_threadpool(executor.execute_scalar, """
                            select coalesce(jsonb_agg(to_jsonb(x)), '[]'::jsonb) from (
                              select i.invocation_id, i.task_name, i.provider, i.model_name, i.status, i.created_at
                              from (values ('news-rss-korean-translation'), ('news-rss-ai-extract'),
                                ('event-intelligence-llm-extract'), ('cycle-community-ai-summary-v2'),
                                ('ai-equity-research-reporting')) as tasks(name)
                              cross join lateral (select invocation_id, task_name, provider, model_name, status, created_at
                                from ai.model_invocation where task_name=tasks.name order by created_at desc limit 1) i
                            ) x
                        """))
                        by_task = {row["task_name"]: row for row in history}
                        for workload in payload["workloads"]:
                            workload["business_history"] = by_task.get(workload["task"])
                        payload["history_available"] = True
                    except Exception:
                        pass  # History failure does not disable model configuration.
            elif action == "logout":
                await run_in_threadpool(store_from_env().revoke, session)
                payload = {"authorized": False}
            else:
                body = await request.body()
                if len(body) > 8192:
                    raise SettingsError("설정 요청이 너무 큽니다.", 413)
                try:
                    data = json.loads(body)
                except (ValueError, UnicodeDecodeError):
                    raise SettingsError("JSON 설정 요청이 필요합니다.") from None
                if not isinstance(data, dict):
                    raise SettingsError("설정 요청 형식이 올바르지 않습니다.")
                store = store_from_env()
                if action == "login":
                    payload = {"session": await run_in_threadpool(store.claim_code, data.get("code"))}
                else:
                    payload = await run_in_threadpool(store.update, data, session)
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})
        except SettingsError as exc:
            return JSONResponse({"error": str(exc)}, status_code=exc.status)
        except Exception:
            # No exception text: database paths, commands and credentials stay private.
            logging.getLogger(__name__).error("Model settings operation unavailable: %s", action)
            return JSONResponse({"error": "모델 설정을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."}, status_code=503)

    @app.get("/__admin/model-settings")
    async def read(request: Request) -> JSONResponse:
        return await respond(request, "read")

    @app.patch("/__admin/model-settings")
    async def update(request: Request) -> JSONResponse:
        return await respond(request, "update")

    @app.post("/__admin/model-settings/session")
    async def login(request: Request) -> JSONResponse:
        return await respond(request, "login")

    @app.delete("/__admin/model-settings/session")
    async def logout(request: Request) -> JSONResponse:
        return await respond(request, "logout")
