from __future__ import annotations

from stockanalysis.ai_agents.registry import DEFAULT_AGENT_DEFINITIONS, build_agent_registry_summary


def build_ai_agent_registry_report(*, include_prompts: bool = False) -> dict[str, object]:
    summary = build_agent_registry_summary()
    agents: list[dict[str, object]] = []
    for agent in DEFAULT_AGENT_DEFINITIONS:
        agent_payload: dict[str, object] = {
            "agent_key": agent.agent_key,
            "display_name": agent.display_name,
            "agent_role": agent.agent_role,
            "owner_domain": agent.owner_domain,
            "business_goal": agent.business_goal,
            "default_task_name": agent.default_task_name,
            "prompt_version": agent.prompt.prompt_version,
            "prompt_cache_key": agent.prompt.prompt_cache_key,
            "output_schema_name": agent.prompt.output_schema_name,
            "model_policy": {
                "primary_provider": agent.model_policy.primary_provider,
                "primary_model": agent.model_policy.primary_model,
                "fallback_provider": agent.model_policy.fallback_provider,
                "fallback_model": agent.model_policy.fallback_model,
                "local_fallback_provider": agent.model_policy.local_fallback_provider,
                "model_tier": agent.model_policy.model_tier,
                "reasoning_effort": agent.model_policy.reasoning_effort,
                "max_input_chars": agent.model_policy.max_input_chars,
                "max_requests_per_run": agent.model_policy.max_requests_per_run,
                "daily_usd_cap": agent.model_policy.daily_usd_cap,
            },
            "safety_boundary": {
                "can_write_canonical": agent.can_write_canonical,
                "can_trigger_order": agent.can_trigger_order,
                "requires_approval_for_side_effects": agent.requires_approval_for_side_effects,
                "order_boundary": "read_only_no_order",
            },
        }
        if include_prompts:
            agent_payload["instructions"] = agent.prompt.instructions
        agents.append(agent_payload)
    return {
        "report_name": "ai_agent_registry",
        "status": "loaded",
        **summary,
        "include_prompts": include_prompts,
        "agents": agents,
    }
