"""Operational model configuration, independent of investment data and credentials."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shlex
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

PATH_ENV = "STOCKANALYSIS_AI_MODEL_SETTINGS_PATH"
SESSION_SECONDS = 30 * 24 * 3600
MODEL_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
WORKLOADS = (
    ("news-rss-korean-translation", "뉴스 한국어 번역", "뉴스 제목과 요약을 한국어로 번역", "ingest/news/translation.py", "뉴스 배치 · Codex OAuth / OpenAI SDK"),
    ("news-rss-ai-extract", "뉴스 이벤트 추출", "뉴스 근거와 종목·테마 영향을 구조화", "ingest/news/ai_extract.py", "뉴스 배치 · Codex OAuth / OpenAI SDK"),
    ("event-intelligence-llm-extract", "공시 이벤트 추출", "SEC 공시에서 투자 관련 사건을 추출", "ingest/sec/ai_event_extract.py", "선택 실행 · 기본 fixture, Codex OAuth 지정 가능"),
    ("cycle-community-ai-summary-v2", "사이클·커뮤니티 요약", "연결된 뉴스와 산업 사이클 흐름을 요약", "ai/cycle_community_ai_summary.py", "배치 / 선택 실행 · Codex OAuth"),
    ("ai-equity-research-reporting", "기업 리서치", "재무·밸류에이션·투자 논리의 검토 보고서 생성", "ai/equity_research_reporting.py", "배치 / 선택 실행 · Codex OAuth"),
)
TASKS = {row[0] for row in WORKLOADS}


class SettingsError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def configured_path() -> Path | None:
    value = os.getenv(PATH_ENV, "").strip()
    return Path(value) if value else None


def legacy_model() -> str | None:
    """Read only explicit model flags, never credentials or the full command."""
    try:
        args = shlex.split(os.getenv("STOCKANALYSIS_CODEX_CLI_COMMAND", "codex"))
    except ValueError:
        return None
    model = None
    for index, value in enumerate(args):
        if value in {"--model", "-m"} and index + 1 < len(args):
            model = args[index + 1]
        elif value.startswith("model="):
            model = value[6:].strip('"\'')
        elif value.startswith("--model="):
            model = value[8:]
    return model if model and MODEL_PATTERN.fullmatch(model) else None


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class ModelSettingsStore:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        if not self.path.is_file():
            raise SettingsError("모델 설정 저장소가 준비되지 않았습니다.", 503)
        db = sqlite3.connect(f"{self.path.as_uri()}?mode=rw", uri=True, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def initialize(self, default_model: str) -> None:
        if not MODEL_PATTERN.fullmatch(default_model):
            raise SettingsError("올바른 모델 ID가 필요합니다.")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with self.connect() as db:
            db.executescript("""
                create table settings (id integer primary key check(id=1), revision integer not null, default_model text not null, overrides text not null);
                create table catalog (id integer primary key check(id=1), checked_at real not null, models text not null);
                create table audit (revision integer primary key, changed_at real not null, actor text not null, before_json text not null, after_json text not null);
                create table access_codes (digest text primary key, expires_at real not null);
                create table sessions (digest text primary key, expires_at real not null);
                create table invocations (id text primary key, task text not null, started_at real not null, finished_at real, revision integer, requested_model text, selected_model text, actual_model text, reasoning_effort text, status text not null);
                create index invocation_task_time on invocations(task, started_at desc);
            """)
            db.execute("insert into settings values (1, 0, ?, '{}')", (default_model,))

    @staticmethod
    def _settings(db: sqlite3.Connection) -> dict[str, Any]:
        row = db.execute("select * from settings where id=1").fetchone()
        return {"revision": row["revision"], "default_model": row["default_model"], "overrides": json.loads(row["overrides"])}

    def read(self, session: str = "") -> dict[str, Any]:
        with self.connect() as db:
            settings = self._settings(db)
            catalog = db.execute("select * from catalog where id=1").fetchone()
            latest = {row["task"]: dict(row) for row in db.execute("""
                select * from (select *, row_number() over(partition by task order by started_at desc) as n from invocations) where n=1
            """)}
            successful = {row["task"]: dict(row) for row in db.execute("""
                select * from (select *, row_number() over(partition by task order by started_at desc) as n from invocations where status='succeeded') where n=1
            """)}
            audit = [dict(row) for row in db.execute("select * from audit order by revision desc limit 20")]
            for row in audit:
                row["before"] = json.loads(row.pop("before_json"))
                row["after"] = json.loads(row.pop("after_json"))
            expires = self._session_expiry(db, session)
        return {**settings, "enabled": True, "authorized": bool(expires), "session_expires_at": expires,
                "catalog": json.loads(catalog["models"]) if catalog else [], "catalog_checked_at": catalog["checked_at"] if catalog else None,
                "workloads": [{"task": task, "label": label, "purpose": purpose, "source": source, "execution": execution,
                    "effective_model": settings["overrides"].get(task) or settings["default_model"],
                    "latest": latest.get(task), "last_success": successful.get(task)} for task, label, purpose, source, execution in WORKLOADS],
                "audit": audit}

    def set_catalog(self, models: list[dict[str, Any]]) -> None:
        safe = [{"id": row["id"], "label": str(row.get("label") or row["id"])[:120]} for row in models
                if isinstance(row.get("id"), str) and MODEL_PATTERN.fullmatch(row["id"]) and not row.get("hidden")]
        if not safe or len(safe) > 100:
            raise SettingsError("사용 가능한 모델 목록을 확인하지 못했습니다.")
        with self.connect() as db:
            db.execute("insert or replace into catalog values (1, ?, ?)", (time.time(), json.dumps(safe)))

    def issue_code(self) -> str:
        code = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("delete from access_codes where expires_at <= ?", (time.time(),))
            db.execute("insert into access_codes values (?, ?)", (_hash(code), time.time() + 600))
        return code

    def claim_code(self, code: str) -> str:
        if not isinstance(code, str) or len(code) != 43:
            raise SettingsError("접근 코드가 올바르지 않거나 만료됐습니다.", 401)
        session = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("begin immediate")
            deleted = db.execute("delete from access_codes where digest=? and expires_at>?", (_hash(code), time.time()))
            if deleted.rowcount != 1:
                raise SettingsError("접근 코드가 올바르지 않거나 만료됐습니다.", 401)
            db.execute("delete from sessions where expires_at<=?", (time.time(),))
            db.execute("insert into sessions values (?, ?)", (_hash(session), time.time() + SESSION_SECONDS))
        return session

    @staticmethod
    def _session_expiry(db: sqlite3.Connection, session: str) -> float | None:
        if not isinstance(session, str) or len(session) != 43:
            return None
        row = db.execute("select expires_at from sessions where digest=? and expires_at>?", (_hash(session), time.time())).fetchone()
        return row[0] if row else None

    def revoke(self, session: str) -> None:
        with self.connect() as db:
            db.execute("delete from sessions where digest=?", (_hash(session),))

    def update(self, payload: dict[str, Any], session: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute("begin immediate")
            if not self._session_expiry(db, session):
                raise SettingsError("모델 변경을 위해 관리자 잠금을 해제해 주세요.", 403)
            if not isinstance(payload, dict) or set(payload) != {"revision", "default_model", "overrides"}:
                raise SettingsError("설정 요청 형식이 올바르지 않습니다.")
            before = self._settings(db)
            if type(payload["revision"]) is not int or payload["revision"] != before["revision"]:
                raise SettingsError("다른 변경이 저장됐습니다. 새로고침 후 다시 선택해 주세요.", 409)
            catalog = db.execute("select models from catalog where id=1").fetchone()
            allowed = {row["id"] for row in json.loads(catalog[0])} if catalog else set()
            overrides = payload["overrides"]
            selected = payload["default_model"]
            if not isinstance(selected, str) or selected not in allowed:
                raise SettingsError("서버 모델 목록에서 기본 모델을 선택해 주세요.")
            if not isinstance(overrides, dict) or not set(overrides).issubset(TASKS) or any(not isinstance(v, str) or v not in allowed for v in overrides.values()):
                raise SettingsError("작업별 모델 선택이 올바르지 않습니다.")
            if selected == before["default_model"] and overrides == before["overrides"]:
                return before
            after = {"revision": before["revision"] + 1, "default_model": selected, "overrides": overrides}
            db.execute("update settings set revision=?, default_model=?, overrides=? where id=1", (after["revision"], selected, json.dumps(overrides)))
            db.execute("insert into audit values (?, ?, ?, ?, ?)", (after["revision"], time.time(), "model-manager:" + _hash(session)[:12], json.dumps(before), json.dumps(after)))
        return after


def store_from_env() -> ModelSettingsStore:
    path = configured_path()
    if path is None:
        raise SettingsError("서버에 모델 설정 저장소가 구성되지 않았습니다.", 503)
    return ModelSettingsStore(path.resolve())


def inventory(session: str = "") -> dict[str, Any]:
    if configured_path():
        return store_from_env().read(session)
    return {"enabled": False, "authorized": False, "session_expires_at": None, "revision": 0,
            "default_model": legacy_model(), "overrides": {}, "catalog": [], "catalog_checked_at": None, "audit": [],
            "workloads": [{"task": t, "label": l, "purpose": p, "source": s, "execution": e,
                "effective_model": legacy_model(), "latest": None, "last_success": None} for t, l, p, s, e in WORKLOADS]}


class CodexModelInvocation:
    """Snapshot settings once, preserve explicit CLI overrides, observe transport metadata."""
    def __init__(self, task: str, requested: str):
        self.task, self.requested = task, requested
        self.id = secrets.token_hex(16)
        self.store = store_from_env() if configured_path() else None
        self.actual_model: str | None = None
        self.actual_reasoning: str | None = None
        self.revision: int | None = None
        self.model = requested

    def __enter__(self) -> CodexModelInvocation:
        settings = None
        if self.store:
            with self.store.connect() as db:
                settings = self.store._settings(db)
        if self.requested in {"", "default", "codex-cli-default"}:
            self.model = (settings["overrides"].get(self.task) or settings["default_model"]) if settings else (legacy_model() or self.requested)
        if settings:
            self.revision = settings["revision"]
            with self.store.connect() as db:
                db.execute("insert into invocations(id,task,started_at,revision,requested_model,selected_model,status) values (?,?,?,?,?,?,?)", (self.id, self.task, time.time(), self.revision, self.requested, self.model, "running"))
        return self

    def run(self, runner: Any, *args: Any, **kwargs: Any) -> Any:
        completed = runner(*args, **kwargs)
        # The first CLI header is authoritative; never trust generated JSON model labels.
        header = str(completed.stderr or "")[:4096].split("\nuser\n", 1)[0]
        match = re.search(r"(?m)^model: ([A-Za-z0-9._-]+)\s*$", header)
        self.actual_model = match.group(1) if match else None
        effort = re.search(r"(?m)^reasoning effort: ([a-z]+)\s*$", header)
        self.actual_reasoning = effort.group(1) if effort else None
        return completed

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.store:
            with self.store.connect() as db:
                db.execute("update invocations set finished_at=?, actual_model=?, reasoning_effort=?, status=? where id=?", (time.time(), self.actual_model, self.actual_reasoning, "failed" if exc_type else "succeeded", self.id))


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure model settings and grant scoped web access.")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--default-model", required=True)
    commands.add_parser("grant-access", help="Issue a one-use code valid for 10 minutes; web session lasts 30 days.")
    commands.add_parser("refresh-catalog", help="Read the authenticated Codex model/list catalog without inference.")
    args = parser.parse_args()
    store = store_from_env()
    if args.command == "init":
        store.initialize(args.default_model)
        print("Model settings initialized.")
    elif args.command == "grant-access":
        print(store.issue_code())
    else:
        from stockanalysis.ai.model_catalog import load_codex_catalog
        models = load_codex_catalog()
        store.set_catalog(models)
        print(json.dumps({"model_count": len(models), "models": models}))


if __name__ == "__main__":
    main()
