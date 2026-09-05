from __future__ import annotations

from dataclasses import dataclass

from stockanalysis.ai_agents.registry import AgentDefinition, get_agent_definition
from stockanalysis.ai_agents.prompt_contract import PROMPT_CONTRACT_VERSION


AGENTS_SDK_OPENAI_PROVIDER = "agents_sdk_openai"
CODEX_OAUTH_PROVIDER = "codex_oauth"
LOCAL_RULES_PROVIDER = "local_rules"


@dataclass(frozen=True)
class AgentRuntimePolicy:
    agent_key: str
    agent_role: str
    prompt_version: str
    prompt_cache_key: str
    output_schema_name: str
    primary_provider: str
    primary_model: str
    fallback_provider: str
    fallback_model: str
    local_fallback_provider: str
    model_tier: str
    reasoning_effort: str
    max_input_chars: int
    max_requests_per_run: int
    daily_usd_cap: str
    order_boundary: str = "read_only_no_order"
    canonical_write_boundary: str = "validator_controlled"

    def as_config_json(self) -> dict[str, object]:
        return {
            "agent_key": self.agent_key,
            "agent_role": self.agent_role,
            "agent_prompt_version": self.prompt_version,
            "agent_prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "agent_prompt_cache_key": self.prompt_cache_key,
            "agent_output_schema_name": self.output_schema_name,
            "agent_primary_provider": self.primary_provider,
            "agent_primary_model": self.primary_model,
            "agent_fallback_provider": self.fallback_provider,
            "agent_fallback_model": self.fallback_model,
            "agent_local_fallback_provider": self.local_fallback_provider,
            "agent_model_tier": self.model_tier,
            "agent_reasoning_effort": self.reasoning_effort,
            "agent_max_input_chars": self.max_input_chars,
            "agent_max_requests_per_run": self.max_requests_per_run,
            "agent_daily_usd_cap": self.daily_usd_cap,
            "agent_order_boundary": self.order_boundary,
            "agent_canonical_write_boundary": self.canonical_write_boundary,
        }


def build_agent_runtime_policy(agent_key: str) -> AgentRuntimePolicy:
    agent = get_agent_definition(agent_key)
    return build_agent_runtime_policy_from_definition(agent)


def build_agent_runtime_policy_from_definition(agent: AgentDefinition) -> AgentRuntimePolicy:
    policy = agent.model_policy
    return AgentRuntimePolicy(
        agent_key=agent.agent_key,
        agent_role=agent.agent_role,
        prompt_version=f"{agent.prompt.prompt_version}+{PROMPT_CONTRACT_VERSION}",
        prompt_cache_key=f"{agent.prompt.prompt_cache_key}:{PROMPT_CONTRACT_VERSION}",
        output_schema_name=agent.prompt.output_schema_name,
        primary_provider=policy.primary_provider,
        primary_model=policy.primary_model,
        fallback_provider=policy.fallback_provider,
        fallback_model=policy.fallback_model,
        local_fallback_provider=policy.local_fallback_provider,
        model_tier=policy.model_tier,
        reasoning_effort=policy.reasoning_effort,
        max_input_chars=policy.max_input_chars,
        max_requests_per_run=policy.max_requests_per_run,
        daily_usd_cap=policy.daily_usd_cap,
    )


def resolve_runner_model_name(
    *,
    requested_provider: str,
    requested_model_name: str,
    policy: AgentRuntimePolicy,
    default_model_name: str,
) -> str:
    """Resolve a model without changing existing provider behavior.

    Existing runners can still pass `codex-cli-default` or fixture model names.
    New agent-backed providers can opt into their configured primary model by
    passing the `agents_sdk_openai` provider.
    """

    if requested_provider == policy.primary_provider and requested_model_name in {"", "default", default_model_name}:
        return policy.primary_model
    if requested_provider == policy.fallback_provider and requested_model_name in {"", "default", default_model_name}:
        return policy.fallback_model
    return requested_model_name or default_model_name
