from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from stockanalysis.ai_agents.prompt_contract import (
    PromptContractError, analysis_instructions, check_schema, is_strict_schema,
    render_source_data, strict_json_object, validate_output,
)
from stockanalysis.ai_agents.registry import get_agent_definition
from stockanalysis.ai_agents.provider_health import load_cached_openai_provider_block, record_provider_failure
from stockanalysis.ai_agents.runtime_policy import AgentRuntimePolicy, build_agent_runtime_policy


DEFAULT_PROVIDER_NAME = "agents_sdk_openai"
OPENAI_BILLING_STATUS_ENV = "STOCKANALYSIS_OPENAI_BILLING_STATUS"
DISABLE_OPENAI_API_ENV = "STOCKANALYSIS_DISABLE_OPENAI_API"
KNOWN_ZERO_BALANCE_VALUES = frozenset({"known_zero_balance", "zero_balance", "no_balance", "insufficient_quota"})


@dataclass(frozen=True)
class AgentsSdkStructuredRequest:
    agent_key: str
    task_name: str
    input_payload: Mapping[str, object]
    output_schema: Mapping[str, object]
    model_name: str | None = None
    reasoning_effort: str | None = None
    max_input_chars: int | None = None


@dataclass(frozen=True)
class AgentsSdkStructuredResponse:
    provider: str
    model_name: str
    reasoning_effort: str | None
    output: dict[str, object]
    input_token_count: int | None = None
    output_token_count: int | None = None
    cached_input_token_count: int | None = None
    estimated_cost_usd: Decimal | None = None
    latency_ms: int | None = None


AgentsSdkRunner = Callable[[AgentsSdkStructuredRequest, AgentRuntimePolicy, str], Mapping[str, object] | str]


class AgentsSdkProviderUnavailable(RuntimeError):
    pass


class AgentsSdkProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        fallback_provider: str,
        local_fallback_provider: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.fallback_provider = fallback_provider
        self.local_fallback_provider = local_fallback_provider
        self.retryable = retryable


def run_agents_sdk_structured_request(
    request: AgentsSdkStructuredRequest,
    *,
    runner: AgentsSdkRunner | None = None,
) -> AgentsSdkStructuredResponse:
    policy = build_agent_runtime_policy(request.agent_key)
    model_name = request.model_name or policy.primary_model
    reasoning_effort = request.reasoning_effort or policy.reasoning_effort
    prompt = build_agents_sdk_prompt(request=request, policy=policy)
    started = time.monotonic()

    if runner is None:
        cached_block = _cached_provider_block(policy)
        if cached_block is not None:
            raise cached_block
        disabled_error = _disabled_by_runtime_env(policy)
        if disabled_error is not None:
            record_provider_failure(
                provider=DEFAULT_PROVIDER_NAME,
                error_code=disabled_error.error_code,
                message=str(disabled_error),
                fallback_provider=disabled_error.fallback_provider,
                local_fallback_provider=disabled_error.local_fallback_provider,
                retryable=disabled_error.retryable,
            )
            raise disabled_error
        raw_output = _run_openai_agents_sdk(request=request, policy=policy, prompt=prompt, model_name=model_name)
    else:
        try:
            raw_output = runner(request, policy, prompt)
        except Exception as exc:
            provider_error = classify_agents_sdk_exception(exc, policy=policy)
            record_provider_failure(
                provider=DEFAULT_PROVIDER_NAME,
                error_code=provider_error.error_code,
                message=str(provider_error),
                fallback_provider=provider_error.fallback_provider,
                local_fallback_provider=provider_error.local_fallback_provider,
                retryable=provider_error.retryable,
            )
            raise provider_error from exc

    latency_ms = int((time.monotonic() - started) * 1000)
    payload = strict_json_object(raw_output)
    # A declared field named output/result belongs to the contract, not an envelope.
    properties = request.output_schema.get("properties", {})
    if "output" in payload and "output" not in properties:
        output = strict_json_object(payload["output"])
    elif "result" in payload and "result" not in properties:
        output = strict_json_object(payload["result"])
    else:
        output = payload
    validate_output(output, request.output_schema)
    return AgentsSdkStructuredResponse(
        provider=DEFAULT_PROVIDER_NAME,
        model_name=_optional_text(payload.get("model_name") or payload.get("model")) or model_name,
        reasoning_effort=_optional_text(payload.get("reasoning_effort")) or reasoning_effort,
        output=output,
        input_token_count=_optional_int(_usage_payload(payload).get("input_tokens")),
        output_token_count=_optional_int(_usage_payload(payload).get("output_tokens")),
        cached_input_token_count=_optional_int(_usage_payload(payload).get("cached_input_tokens")),
        estimated_cost_usd=_optional_decimal(_usage_payload(payload).get("estimated_cost_usd")),
        latency_ms=_optional_int(_usage_payload(payload).get("latency_ms")) or latency_ms,
    )


def build_agents_sdk_prompt(*, request: AgentsSdkStructuredRequest, policy: AgentRuntimePolicy) -> str:
    agent = get_agent_definition(request.agent_key)
    check_schema(request.output_schema)
    requested_limit = request.max_input_chars if request.max_input_chars is not None else policy.max_input_chars
    if type(requested_limit) is not int or requested_limit <= 0:
        raise PromptContractError("invalid_input_budget")
    bounded_payload = render_source_data(request.input_payload, max_chars=min(requested_limit, policy.max_input_chars))
    return "\n".join(
        (
            analysis_instructions(request.agent_key, agent.prompt.instructions),
            "",
            "Output contract:",
            json.dumps(request.output_schema, ensure_ascii=False, sort_keys=True),
            "",
            "Runtime policy:",
            json.dumps(policy.as_config_json(), ensure_ascii=False, sort_keys=True),
            "",
            "Task input payload:",
            bounded_payload,
        )
    )


def _run_openai_agents_sdk(
    *,
    request: AgentsSdkStructuredRequest,
    policy: AgentRuntimePolicy,
    prompt: str,
    model_name: str,
) -> Mapping[str, object] | str:
    try:
        from agents import Agent, Runner
        from agents.agent_output import AgentOutputSchemaBase
        from agents.exceptions import ModelBehaviorError
    except Exception as exc:  # pragma: no cover - depends on optional package installation.
        raise AgentsSdkProviderUnavailable(
            "openai-agents is not installed. Install the optional `agents` extra before using agents_sdk_openai."
        ) from exc

    if not is_strict_schema(request.output_schema):
        raise PromptContractError("generation_requires_strict_schema")

    class ContractOutput(AgentOutputSchemaBase):
        def is_plain_text(self) -> bool:
            return False

        def name(self) -> str:
            return policy.output_schema_name

        def json_schema(self) -> dict[str, Any]:
            return json.loads(json.dumps(request.output_schema))

        def is_strict_json_schema(self) -> bool:
            return True

        def validate_json(self, json_str: str) -> dict[str, Any]:
            try:
                output = strict_json_object(json_str)
                validate_output(output, request.output_schema)
                return output
            except PromptContractError as exc:
                raise ModelBehaviorError("Structured analysis output failed its contract.") from exc

    agent_definition = get_agent_definition(request.agent_key)
    agent = Agent(
        name=agent_definition.display_name,
        instructions=analysis_instructions(request.agent_key, agent_definition.prompt.instructions),
        model=model_name,
        tools=[],
        output_type=ContractOutput(),
    )
    try:
        result = Runner.run_sync(agent, prompt)
    except Exception as exc:  # pragma: no cover - real SDK error surface varies by version.
        provider_error = classify_agents_sdk_exception(exc, policy=policy)
        record_provider_failure(
            provider=DEFAULT_PROVIDER_NAME,
            error_code=provider_error.error_code,
            message=str(provider_error),
            fallback_provider=provider_error.fallback_provider,
            local_fallback_provider=provider_error.local_fallback_provider,
            retryable=provider_error.retryable,
        )
        raise provider_error from exc
    return getattr(result, "final_output", result)


def _cached_provider_block(policy: AgentRuntimePolicy) -> AgentsSdkProviderError | None:
    cached = load_cached_openai_provider_block()
    if cached is None:
        return None
    return AgentsSdkProviderError(
        cached.message,
        error_code=cached.error_code,
        fallback_provider=cached.fallback_provider or policy.fallback_provider,
        local_fallback_provider=cached.local_fallback_provider or policy.local_fallback_provider,
        retryable=False,
    )


def classify_agents_sdk_exception(exc: Exception, *, policy: AgentRuntimePolicy) -> AgentsSdkProviderError:
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(token in text for token in ("insufficient_quota", "exceeded your current quota", "quota exceeded")):
        return _provider_error(
            "OpenAI quota is exhausted. Falling back to the configured offline provider.",
            error_code="openai_insufficient_quota",
            policy=policy,
            retryable=False,
        )
    if any(token in text for token in ("billing", "credit", "balance", "payment required")):
        return _provider_error(
            "OpenAI billing is unavailable. Falling back to the configured offline provider.",
            error_code="openai_billing_unavailable",
            policy=policy,
            retryable=False,
        )
    if any(token in text for token in ("invalid_api_key", "incorrect api key", "unauthorized", "401")):
        return _provider_error(
            "OpenAI API authentication failed. Falling back to the configured offline provider.",
            error_code="openai_auth_invalid",
            policy=policy,
            retryable=False,
        )
    if any(token in text for token in ("rate_limit", "429", "too many requests")):
        return _provider_error(
            "OpenAI rate limit was reached. Falling back to the configured offline provider.",
            error_code="openai_rate_limited",
            policy=policy,
            retryable=True,
        )
    if any(token in text for token in ("timeout", "timed out", "deadline")):
        return _provider_error(
            "OpenAI provider timed out. Falling back to the configured offline provider.",
            error_code="openai_timeout",
            policy=policy,
            retryable=True,
        )
    return _provider_error(
        "OpenAI provider failed. Falling back to the configured offline provider.",
        error_code="openai_provider_error",
        policy=policy,
        retryable=True,
    )


def _disabled_by_runtime_env(policy: AgentRuntimePolicy) -> AgentsSdkProviderError | None:
    if _truthy(os.environ.get(DISABLE_OPENAI_API_ENV, "")):
        return _provider_error(
            "OpenAI API calls are disabled by runtime configuration.",
            error_code="openai_provider_disabled",
            policy=policy,
            retryable=False,
        )
    billing_status = os.environ.get(OPENAI_BILLING_STATUS_ENV, "").strip().lower()
    if billing_status in KNOWN_ZERO_BALANCE_VALUES:
        return _provider_error(
            "OpenAI billing is marked as zero balance by runtime configuration.",
            error_code="openai_billing_unavailable",
            policy=policy,
            retryable=False,
        )
    return None


def _provider_error(
    message: str,
    *,
    error_code: str,
    policy: AgentRuntimePolicy,
    retryable: bool,
) -> AgentsSdkProviderError:
    return AgentsSdkProviderError(
        message,
        error_code=error_code,
        fallback_provider=policy.fallback_provider,
        local_fallback_provider=policy.local_fallback_provider,
        retryable=retryable,
    )


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _coerce_json_object(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Agents SDK provider output must be a JSON object.")


def _usage_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    usage = payload.get("usage")
    return usage if isinstance(usage, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid estimated_cost_usd `{value}`.") from exc
