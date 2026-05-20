#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REQUIRED_OTEL_MODULES = (
    "opentelemetry.trace",
    "opentelemetry.sdk.trace",
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "opentelemetry.instrumentation.fastapi",
)


class OtlpReceiver(ThreadingHTTPServer):
    events: list[dict[str, Any]]
    lock: threading.Lock


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    _assert_otel_modules_available()

    receiver = _start_receiver()
    receiver_thread = threading.Thread(target=receiver.serve_forever, name="local-otlp-receiver", daemon=True)
    receiver_thread.start()
    receiver_base_url = f"http://127.0.0.1:{receiver.server_port}"
    api_port = _free_loopback_port()
    api_base_url = f"http://127.0.0.1:{api_port}"
    api_process: subprocess.Popen[str] | None = None

    try:
        api_process = _start_frontend_api_server(
            repo_root=repo_root,
            api_port=api_port,
            otlp_endpoint=receiver_base_url,
            allowed_origin=args.allowed_origin,
        )
        startup_line = _read_startup_line(api_process, timeout_seconds=args.startup_timeout_seconds)
        _assert_no_endpoint_leak(startup_line, receiver_base_url, context="startup metadata")

        health = _wait_for_json(f"{api_base_url}/__health", timeout_seconds=args.startup_timeout_seconds)
        _assert_health_metadata(health, receiver_base_url)
        dashboard = _get_json(f"{api_base_url}/api/dashboard/today", timeout_seconds=args.request_timeout_seconds)
        if dashboard.get("contract_version") != "frontend-api-v0.1":
            raise RuntimeError("dashboard response did not return the frontend API contract")

        trace_posts = _wait_for_receiver_path(
            receiver,
            expected_path="/v1/traces",
            timeout_seconds=args.trace_timeout_seconds,
        )
        summary = {
            "status": "ok",
            "receiver_base_url": receiver_base_url,
            "api_base_url": api_base_url,
            "trace_post_count": len(trace_posts),
            "received_paths": sorted({event["path"] for event in _receiver_events(receiver)}),
            "observability": health.get("observability", {}),
        }
        print(json.dumps(summary, sort_keys=True))
        return 0
    finally:
        if api_process is not None:
            _terminate_process(api_process)
        receiver.shutdown()
        receiver.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke the frontend API OTLP exporter against a local OTLP/HTTP receiver."
    )
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--allowed-origin", default="http://127.0.0.1:3000")
    parser.add_argument("--startup-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--request-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--trace-timeout-seconds", type=float, default=20.0)
    return parser


def _assert_otel_modules_available() -> None:
    missing: list[str] = []
    for module_name in REQUIRED_OTEL_MODULES:
        try:
            found = importlib.util.find_spec(module_name) is not None
        except ModuleNotFoundError:
            found = False
        if not found:
            missing.append(module_name)
    if missing:
        raise RuntimeError(
            "OpenTelemetry optional packages are missing. "
            'Run this smoke with a Python environment that installed `stockanalysis[otel]`. '
            f"Missing modules: {', '.join(missing)}"
        )


def _start_receiver() -> OtlpReceiver:
    class Handler(BaseHTTPRequestHandler):
        server: OtlpReceiver

        def do_POST(self) -> None:  # noqa: N802
            body_length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(body_length) if body_length > 0 else b""
            event = {
                "method": "POST",
                "path": self.path,
                "content_type": self.headers.get("Content-Type", ""),
                "body_length": len(body),
            }
            with self.server.lock:
                self.server.events.append(event)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = OtlpReceiver(("127.0.0.1", 0), Handler)
    server.events = []
    server.lock = threading.Lock()
    return server


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_frontend_api_server(
    *,
    repo_root: Path,
    api_port: int,
    otlp_endpoint: str,
    allowed_origin: str,
) -> subprocess.Popen[str]:
    env = os.environ.copy()
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
    env["OTEL_BSP_SCHEDULE_DELAY"] = "100"
    env["OTEL_BSP_EXPORT_TIMEOUT"] = "5000"
    env["OTEL_EXPORTER_OTLP_TIMEOUT"] = "5"
    env["OTEL_METRIC_EXPORT_INTERVAL"] = "1000"
    command = [
        sys.executable,
        "-m",
        "stockanalysis.frontend.api_server",
        "--host",
        "127.0.0.1",
        "--port",
        str(api_port),
        "--repo-root",
        str(repo_root),
        "--source",
        "fixture",
        "--runtime-profile",
        "local",
        "--auth-mode",
        "disabled",
        "--allowed-origin",
        allowed_origin,
        "--observability-mode",
        "otlp",
        "--otlp-endpoint",
        otlp_endpoint,
        "--log-level",
        "warning",
    ]
    return subprocess.Popen(
        command,
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _read_startup_line(process: subprocess.Popen[str], *, timeout_seconds: float) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"frontend API server exited early with code {process.returncode}: {stderr}")
        if process.stdout is None:
            break
        line = process.stdout.readline()
        if line:
            return line.strip()
        time.sleep(0.05)
    raise RuntimeError("frontend API server did not print startup metadata before timeout")


def _wait_for_json(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return _get_json(url, timeout_seconds=1.0)
        except Exception as exc:  # pragma: no cover - error text is used for smoke diagnostics.
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _get_json(url: str, *, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {payload}") from exc
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise RuntimeError(f"{url} returned non-object JSON")
    return value


def _assert_health_metadata(health: dict[str, Any], otlp_endpoint: str) -> None:
    observability = health.get("observability")
    if not isinstance(observability, dict):
        raise RuntimeError("health metadata is missing observability object")
    if observability.get("observability_mode") != "otlp":
        raise RuntimeError(f"unexpected observability mode: {observability}")
    if observability.get("exporter") != "otlp_http":
        raise RuntimeError(f"unexpected exporter metadata: {observability}")
    if observability.get("instrumented") is not True:
        raise RuntimeError(f"server did not report instrumented=true: {observability}")
    _assert_no_endpoint_leak(json.dumps(health, sort_keys=True), otlp_endpoint, context="health metadata")


def _assert_no_endpoint_leak(text: str, endpoint: str, *, context: str) -> None:
    if endpoint in text:
        raise RuntimeError(f"{context} exposed the OTLP endpoint")


def _wait_for_receiver_path(
    receiver: OtlpReceiver,
    *,
    expected_path: str,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        matches = [event for event in _receiver_events(receiver) if event["path"] == expected_path]
        if matches:
            return matches
        time.sleep(0.1)
    raise RuntimeError(
        f"Timed out waiting for {expected_path}; received paths: "
        f"{sorted({event['path'] for event in _receiver_events(receiver)})}"
    )


def _receiver_events(receiver: OtlpReceiver) -> list[dict[str, Any]]:
    with receiver.lock:
        return list(receiver.events)


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
