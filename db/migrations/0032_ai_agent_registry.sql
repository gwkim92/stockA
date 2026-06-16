create table if not exists ai.agent_definition (
    agent_id bigint generated always as identity primary key,
    agent_key text not null unique,
    display_name text not null,
    agent_role text not null,
    business_goal text not null,
    owner_domain text not null,
    orchestration_mode text not null default 'agents_sdk',
    default_task_name text,
    status text not null default 'active',
    can_write_canonical boolean not null default false,
    can_trigger_order boolean not null default false,
    requires_approval_for_side_effects boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (agent_key ~ '^[a-z0-9_]+$'),
    check (orchestration_mode in ('agents_sdk', 'deterministic_service', 'manual_fallback')),
    check (status in ('active', 'disabled', 'pilot')),
    check (can_trigger_order = false)
);

create table if not exists ai.agent_prompt_version (
    prompt_version_id bigint generated always as identity primary key,
    agent_id bigint not null references ai.agent_definition (agent_id) on delete cascade,
    prompt_version text not null,
    prompt_kind text not null default 'agent_instructions',
    prompt_text text not null,
    output_schema_json jsonb not null default '{}'::jsonb,
    research_basis_json jsonb not null default '{}'::jsonb,
    prompt_cache_key text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    check (prompt_kind in ('agent_instructions', 'tool_instructions', 'guardrail_instructions')),
    unique (agent_id, prompt_version, prompt_kind)
);

create table if not exists ai.agent_model_policy (
    policy_id bigint generated always as identity primary key,
    agent_id bigint not null references ai.agent_definition (agent_id) on delete cascade,
    policy_name text not null default 'default',
    primary_provider text not null,
    primary_model text not null,
    fallback_provider text,
    fallback_model text,
    local_fallback_provider text not null default 'local_rules',
    reasoning_effort text,
    service_tier text,
    model_tier text not null default 'balanced',
    max_input_chars integer not null default 12000,
    max_output_tokens integer,
    max_requests_per_run integer not null default 10,
    daily_usd_cap numeric(12,6),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (policy_name ~ '^[a-z0-9_]+$'),
    check (model_tier in ('cheap', 'balanced', 'quality', 'batch', 'local')),
    check (max_input_chars > 0),
    check (max_output_tokens is null or max_output_tokens > 0),
    check (max_requests_per_run > 0),
    check (daily_usd_cap is null or daily_usd_cap >= 0),
    unique (agent_id, policy_name)
);

create table if not exists ai.agent_tool_permission (
    permission_id bigint generated always as identity primary key,
    agent_id bigint not null references ai.agent_definition (agent_id) on delete cascade,
    tool_name text not null,
    permission_scope text not null,
    needs_approval boolean not null default true,
    is_enabled boolean not null default true,
    rationale text not null,
    created_at timestamptz not null default now(),
    check (permission_scope in ('read', 'propose_write', 'write', 'admin_control')),
    unique (agent_id, tool_name)
);

create table if not exists ai.agent_run (
    agent_run_id bigint generated always as identity primary key,
    run_id bigint references ops.pipeline_run (run_id) on delete set null,
    agent_id bigint not null references ai.agent_definition (agent_id) on delete restrict,
    prompt_version_id bigint references ai.agent_prompt_version (prompt_version_id) on delete set null,
    policy_id bigint references ai.agent_model_policy (policy_id) on delete set null,
    invocation_id bigint references ai.model_invocation (invocation_id) on delete set null,
    status text not null,
    input_hash text,
    state_json jsonb not null default '{}'::jsonb,
    interruption_json jsonb not null default '[]'::jsonb,
    output_json jsonb,
    error_summary text,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    check (status in ('planned', 'running', 'succeeded', 'failed', 'interrupted', 'fallback_used', 'blocked_by_guardrail')),
    check (completed_at is null or completed_at >= started_at)
);

create index if not exists ai_agent_definition_status_idx
    on ai.agent_definition (status, owner_domain, agent_key);

create index if not exists ai_agent_prompt_active_idx
    on ai.agent_prompt_version (agent_id, prompt_kind, is_active);

create index if not exists ai_agent_model_policy_active_idx
    on ai.agent_model_policy (agent_id, is_active, model_tier);

create index if not exists ai_agent_tool_permission_scope_idx
    on ai.agent_tool_permission (agent_id, permission_scope, is_enabled);

create index if not exists ai_agent_run_agent_started_idx
    on ai.agent_run (agent_id, started_at desc);

create index if not exists ai_agent_run_status_idx
    on ai.agent_run (status, started_at desc);
