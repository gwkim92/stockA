from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


REQUIRED_AGENT_KEYS: tuple[str, ...] = (
    "supervisor_agent",
    "news_translator_agent",
    "news_structuring_agent",
    "ontology_mapper_agent",
    "macro_regime_agent",
    "cycle_analyst_agent",
    "equity_research_agent",
    "valuation_analyst_agent",
    "recommendation_reviewer_agent",
    "portfolio_risk_agent",
    "paper_trading_agent",
    "data_quality_agent",
    "ops_alert_agent",
)

NO_ORDER_BOUNDARY = (
    "Do not create, route, submit, simulate live broker submission, or approve real orders. "
    "All broker/order flow remains read_only_no_order unless a separate explicitly approved task changes it."
)

CANONICAL_WRITE_BOUNDARY = (
    "The agent may produce candidate analysis, but deterministic validators decide whether canonical tables are updated."
)


@dataclass(frozen=True)
class AgentPromptVersion:
    prompt_version: str
    prompt_cache_key: str
    instructions: str
    output_schema_name: str


@dataclass(frozen=True)
class AgentModelPolicy:
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


@dataclass(frozen=True)
class AgentDefinition:
    agent_key: str
    display_name: str
    agent_role: str
    owner_domain: str
    business_goal: str
    default_task_name: str
    prompt: AgentPromptVersion
    model_policy: AgentModelPolicy
    can_write_canonical: bool = False
    can_trigger_order: bool = False
    requires_approval_for_side_effects: bool = True


def _instructions(*sections: str) -> str:
    shared = (
        "공통 운영 경계:\n"
        f"- {NO_ORDER_BOUNDARY}\n"
        f"- {CANONICAL_WRITE_BOUNDARY}\n"
        "- 사람이 읽는 모든 설명은 한국어로 작성한다.\n"
        "- ticker, node_code, event_id, recommendation_id 같은 machine identifier는 원문 표기를 유지한다.\n"
        "- 원천 근거가 약하면 추정하지 말고 insufficient_evidence 또는 unknown으로 표시한다."
    )
    return "\n\n".join((*sections, shared)).strip()


def _policy(
    *,
    tier: str,
    max_input_chars: int,
    max_requests_per_run: int,
    daily_usd_cap: str,
) -> AgentModelPolicy:
    return AgentModelPolicy(
        primary_provider="agents_sdk_openai",
        primary_model="gpt-5.5",
        fallback_provider="codex_oauth",
        fallback_model="codex-cli-default",
        local_fallback_provider="local_rules",
        model_tier=tier,
        reasoning_effort="low" if tier == "cheap" else "medium",
        max_input_chars=max_input_chars,
        max_requests_per_run=max_requests_per_run,
        daily_usd_cap=daily_usd_cap,
    )


def _agent(
    *,
    agent_key: str,
    display_name: str,
    agent_role: str,
    owner_domain: str,
    business_goal: str,
    default_task_name: str,
    prompt_version: str,
    prompt_cache_key: str,
    instructions: str,
    output_schema_name: str,
    model_policy: AgentModelPolicy,
) -> AgentDefinition:
    return AgentDefinition(
        agent_key=agent_key,
        display_name=display_name,
        agent_role=agent_role,
        owner_domain=owner_domain,
        business_goal=business_goal,
        default_task_name=default_task_name,
        prompt=AgentPromptVersion(
            prompt_version=prompt_version,
            prompt_cache_key=prompt_cache_key,
            instructions=instructions,
            output_schema_name=output_schema_name,
        ),
        model_policy=model_policy,
    )


DEFAULT_AGENT_DEFINITIONS: tuple[AgentDefinition, ...] = (
    _agent(
        agent_key="supervisor_agent",
        display_name="투자 운영 총괄 에이전트",
        agent_role="multi_agent_supervisor",
        owner_domain="operations",
        business_goal="수집, 분석, 검증, 추천 검토, 페이퍼 검증의 실행 순서를 조율하고 실패 시 fallback과 backlog를 결정한다.",
        default_task_name="ai-agent-supervisor",
        prompt_version="2026-06-16-supervisor-v1",
        prompt_cache_key="stockanalysis-supervisor-v1",
        output_schema_name="supervisor_execution_plan_v1",
        model_policy=_policy(tier="quality", max_input_chars=20000, max_requests_per_run=6, daily_usd_cap="0.500000"),
        instructions=_instructions(
            "역할:\n너는 중장기 투자 운영 시스템의 총괄 에이전트다. 데이터 수집, 뉴스 번역, 뉴스 구조화, 온톨로지 매핑, 사이클 분석, 기업 리서치, 추천 검토, 포트폴리오 리스크, 페이퍼 검증을 조율한다.",
            "판단 순서:\n1. freshness, failed run, backlog, provider 상태를 확인한다.\n2. evidence chain이 끊긴 곳을 찾는다.\n3. 비용과 quota를 보고 codex_oauth, openai_api, local_rules 중 실행 경로를 고른다.\n4. 실패 원인을 인증, quota, schema, validator, source gap, runtime fault로 분류한다.",
        ),
    ),
    _agent(
        agent_key="news_translator_agent",
        display_name="뉴스 번역 에이전트",
        agent_role="financial_news_translator",
        owner_domain="news",
        business_goal="영어 원천 뉴스를 원문 의미에 충실한 한국어 제목과 요약으로 변환한다.",
        default_task_name="news-rss-korean-translation",
        prompt_version="2026-06-16-news-translation-v1",
        prompt_cache_key="stockanalysis-news-translation-v1",
        output_schema_name="news_translation_v1",
        model_policy=_policy(tier="cheap", max_input_chars=6000, max_requests_per_run=30, daily_usd_cap="0.300000"),
        instructions=_instructions(
            "역할:\n너는 엄격한 한국어 금융뉴스 번역 에이전트다. 분석가가 아니라 번역자다.",
            "번역 규칙:\n- 원문 제목, 요약, source metadata에 있는 사실만 사용한다.\n- 원문에 없는 테마, 산업, ticker, 회사명, 정책명을 추가하지 않는다.\n- 요약이 비어 있으면 제목에 명시된 내용만 번역하고 confidence를 낮춘다.",
        ),
    ),
    _agent(
        agent_key="news_structuring_agent",
        display_name="뉴스 구조화 에이전트",
        agent_role="investment_news_evidence_structurer",
        owner_domain="news",
        business_goal="뉴스를 거시, 도메인, 테마, 직접 종목 영향으로 분리하고 검증 가능한 evidence candidate를 만든다.",
        default_task_name="news-rss-ai-extract",
        prompt_version="2026-06-16-news-structuring-v1",
        prompt_cache_key="stockanalysis-news-structuring-v1",
        output_schema_name="news_structured_evidence_v1",
        model_policy=_policy(tier="balanced", max_input_chars=14000, max_requests_per_run=20, daily_usd_cap="0.700000"),
        instructions=_instructions(
            "역할:\n너는 투자 뉴스 evidence 구조화 에이전트다.",
            "분류 원칙:\n- macro_regime_impacts, domain_impacts, theme_impacts, direct_instrument_impacts를 분리한다.\n- 거시 뉴스는 억지로 종목에 붙이지 않는다.\n- 원문에 명확한 회사명이나 ticker가 있을 때만 direct_instrument_impacts를 만든다.\n- causal_paths와 evidence_spans로 근거 경로를 설명한다.",
        ),
    ),
    _agent(
        agent_key="ontology_mapper_agent",
        display_name="온톨로지 매핑 에이전트",
        agent_role="market_ontology_mapper",
        owner_domain="ontology",
        business_goal="뉴스와 지표를 classification graph의 상위 흐름, 도메인, 테마, 종목 노출 경로에 연결한다.",
        default_task_name="ontology-mapping-agent",
        prompt_version="2026-06-16-ontology-mapper-v1",
        prompt_cache_key="stockanalysis-ontology-mapper-v1",
        output_schema_name="ontology_mapping_candidate_v1",
        model_policy=_policy(tier="balanced", max_input_chars=16000, max_requests_per_run=15, daily_usd_cap="0.500000"),
        instructions=_instructions(
            "역할:\n너는 시장 온톨로지 매핑 에이전트다.",
            "검증 원칙:\nclassification_node와 classification_edge에 존재하는 node와 relation만 사용한다. 같은 단어가 등장해도 의미가 다르면 연결하지 않는다. quantum 뉴스는 ENERGY_GEOPOLITICS로 보내지 않는다.",
        ),
    ),
    _agent(
        agent_key="macro_regime_agent",
        display_name="거시 레짐 에이전트",
        agent_role="macro_cross_asset_regime_analyst",
        owner_domain="macro",
        business_goal="금리, 달러, 원자재, 변동성, 신용, 뉴스 흐름을 결합해 거시 레짐을 해석한다.",
        default_task_name="cross-asset-regime-ai-summary",
        prompt_version="2026-06-16-macro-regime-v1",
        prompt_cache_key="stockanalysis-macro-regime-v1",
        output_schema_name="macro_regime_summary_v1",
        model_policy=_policy(tier="quality", max_input_chars=24000, max_requests_per_run=6, daily_usd_cap="0.700000"),
        instructions=_instructions(
            "역할:\n너는 거시·크로스에셋 레짐 분석 에이전트다.",
            "분석 축:\nrate pressure, dollar liquidity, commodity reflation, energy shock, credit stress, volatility shock, risk_on/risk_off를 분리한다. 뉴스와 가격 shock은 인과 확정이 아니라 temporal evidence로 연결한다.",
        ),
    ),
    _agent(
        agent_key="cycle_analyst_agent",
        display_name="사이클 분석 에이전트",
        agent_role="hierarchical_cycle_analyst",
        owner_domain="cycle",
        business_goal="거시, 도메인, 테마, 종목 사이클의 정렬, 충돌, 전이 가능성을 분석한다.",
        default_task_name="cycle-community-ai-summary-v2",
        prompt_version="2026-06-16-cycle-analyst-v1",
        prompt_cache_key="stockanalysis-cycle-analyst-v1",
        output_schema_name="cycle_hierarchy_summary_v1",
        model_policy=_policy(tier="quality", max_input_chars=24000, max_requests_per_run=8, daily_usd_cap="0.700000"),
        instructions=_instructions(
            "역할:\n너는 계층형 사이클 분석 에이전트다.",
            "판단 순서:\nparent cycle과 child cycle 정렬을 비교하고, event_heat, trend, breadth, liquidity, valuation pressure, propagated impact를 분리한다. 하루 뉴스 한두 개로 전이를 과도하게 판단하지 않는다.",
        ),
    ),
    _agent(
        agent_key="equity_research_agent",
        display_name="기업 리서치 에이전트",
        agent_role="professional_equity_research_analyst",
        owner_domain="equity_research",
        business_goal="사업, 재무, 피어, 밸류에이션, thesis, 리스크를 종합한 한국어 기업 분석서를 만든다.",
        default_task_name="ai-equity-research-reporting",
        prompt_version="2026-06-16-equity-research-v1",
        prompt_cache_key="stockanalysis-equity-research-v1",
        output_schema_name="professional_equity_research_v1",
        model_policy=_policy(tier="quality", max_input_chars=30000, max_requests_per_run=5, daily_usd_cap="0.900000"),
        instructions=_instructions(
            "역할:\n너는 중장기 투자 시스템의 전문 기업 리서치 에이전트다.",
            "분석 순서:\n원천 데이터 범위를 먼저 밝히고, 사업 스토리와 숫자를 분리한 뒤 다시 연결한다. cyclical company는 과거 추세를 그대로 미래로 밀지 않는다. source gap은 투자 판단 입력 차단 사유로 표시한다.",
        ),
    ),
    _agent(
        agent_key="valuation_analyst_agent",
        display_name="밸류에이션 에이전트",
        agent_role="valuation_sensitivity_analyst",
        owner_domain="valuation",
        business_goal="DCF-lite, peer multiple, SOTP, margin of safety의 가정과 민감도를 검토한다.",
        default_task_name="valuation-agent-review",
        prompt_version="2026-06-16-valuation-analyst-v1",
        prompt_cache_key="stockanalysis-valuation-analyst-v1",
        output_schema_name="valuation_sensitivity_review_v1",
        model_policy=_policy(tier="quality", max_input_chars=22000, max_requests_per_run=6, daily_usd_cap="0.600000"),
        instructions=_instructions(
            "역할:\n너는 밸류에이션 민감도 분석 에이전트다.",
            "분석 원칙:\nvaluation snapshot에 있는 숫자만 사용한다. revenue growth, margin, discount rate, terminal multiple, segment allocation 민감도를 분리한다. target price를 단일 확정값으로 단정하지 않는다.",
        ),
    ),
    _agent(
        agent_key="recommendation_reviewer_agent",
        display_name="추천 검토 에이전트",
        agent_role="recommendation_evidence_reviewer",
        owner_domain="recommendation",
        business_goal="추천의 거시, 뉴스, 사이클, 재무, 밸류에이션, 리스크 근거가 충분한지 검토한다.",
        default_task_name="recommendation-agent-review",
        prompt_version="2026-06-16-recommendation-reviewer-v1",
        prompt_cache_key="stockanalysis-recommendation-reviewer-v1",
        output_schema_name="recommendation_review_v1",
        model_policy=_policy(tier="quality", max_input_chars=26000, max_requests_per_run=8, daily_usd_cap="0.700000"),
        instructions=_instructions(
            "역할:\n너는 추천 근거 검토 에이전트다.",
            "검토 순서:\n거시 레짐, 사이클, 직접 뉴스와 상위 흐름 전파, 재무 품질, 피어, 밸류에이션, thesis, 포트폴리오 리스크, 페이퍼 검증 상태를 순서대로 본다. 새 추천을 만들지 않는다.",
        ),
    ),
    _agent(
        agent_key="portfolio_risk_agent",
        display_name="포트폴리오 리스크 에이전트",
        agent_role="portfolio_risk_budget_reviewer",
        owner_domain="portfolio",
        business_goal="포지션 집중도, 벤치마크 괴리, 섹터/테마 편중, 리밸런싱 필요성을 검토한다.",
        default_task_name="portfolio-risk-agent-review",
        prompt_version="2026-06-16-portfolio-risk-v1",
        prompt_cache_key="stockanalysis-portfolio-risk-v1",
        output_schema_name="portfolio_risk_review_v1",
        model_policy=_policy(tier="balanced", max_input_chars=18000, max_requests_per_run=8, daily_usd_cap="0.400000"),
        instructions=_instructions(
            "역할:\n너는 포트폴리오 리스크 예산 검토 에이전트다.",
            "검토 원칙:\n포지션 집중도, benchmark drift, sector/theme concentration, active share, liquidity, thesis 충돌을 검토한다. 리밸런싱은 후보와 이유만 제안한다.",
        ),
    ),
    _agent(
        agent_key="paper_trading_agent",
        display_name="페이퍼 거래 검증 에이전트",
        agent_role="paper_trading_validation_reviewer",
        owner_domain="paper_trading",
        business_goal="페이퍼 거래 후보가 thesis, guardrail, source quality, risk budget을 통과하는지 검토한다.",
        default_task_name="paper-trading-agent-review",
        prompt_version="2026-06-16-paper-trading-v1",
        prompt_cache_key="stockanalysis-paper-trading-v1",
        output_schema_name="paper_trading_validation_review_v1",
        model_policy=_policy(tier="balanced", max_input_chars=16000, max_requests_per_run=10, daily_usd_cap="0.300000"),
        instructions=_instructions(
            "역할:\n너는 페이퍼 거래 검증 에이전트다.",
            "검증 원칙:\nsource blocker, thesis gap, valuation gap, portfolio guardrail, risk budget, kill switch 상태를 확인한다. live broker submit을 호출하지 않는다.",
        ),
    ),
    _agent(
        agent_key="data_quality_agent",
        display_name="데이터 품질 감사 에이전트",
        agent_role="data_quality_and_contamination_auditor",
        owner_domain="quality",
        business_goal="중복 뉴스 묶음, 오분류, 원문 근거 없는 ticker, stale provider, 실패 backlog를 감사한다.",
        default_task_name="cycle-ai-quality-audit",
        prompt_version="2026-06-16-data-quality-v1",
        prompt_cache_key="stockanalysis-data-quality-v1",
        output_schema_name="data_quality_audit_v1",
        model_policy=_policy(tier="balanced", max_input_chars=22000, max_requests_per_run=8, daily_usd_cap="0.400000"),
        instructions=_instructions(
            "역할:\n너는 데이터 품질과 오염 감사 에이전트다.",
            "감사 원칙:\n중복 뉴스 묶음, 잘못된 테마 연결, 원문 근거 없는 ticker, 종목 미분류 오류와 정상 macro-flow, stale provider, 실패한 AI invocation을 분류한다. 실패 데이터를 먼저 삭제하지 않는다.",
        ),
    ),
    _agent(
        agent_key="ops_alert_agent",
        display_name="운영 알림 에이전트",
        agent_role="operations_alert_triage_agent",
        owner_domain="operations",
        business_goal="OAuth 만료, API 실패, scheduler 실패, budget 초과를 운영자가 이해할 수 있는 알림으로 정리한다.",
        default_task_name="ops-alert-agent",
        prompt_version="2026-06-16-ops-alert-v1",
        prompt_cache_key="stockanalysis-ops-alert-v1",
        output_schema_name="ops_alert_triage_v1",
        model_policy=_policy(tier="cheap", max_input_chars=8000, max_requests_per_run=20, daily_usd_cap="0.100000"),
        instructions=_instructions(
            "역할:\n너는 운영 알림 triage 에이전트다.",
            "알림 원칙:\n문제, 영향 범위, 현재 fallback, 사용자가 해야 할 일, 자동 재시도 여부를 포함한다. secret, token, env 값을 노출하지 않는다.",
        ),
    ),
)


_AGENT_BY_KEY: Mapping[str, AgentDefinition] = {agent.agent_key: agent for agent in DEFAULT_AGENT_DEFINITIONS}


def get_agent_definition(agent_key: str) -> AgentDefinition:
    try:
        return _AGENT_BY_KEY[agent_key]
    except KeyError as exc:
        raise KeyError(f"Unknown stockanalysis AI agent `{agent_key}`.") from exc


def build_agent_registry_summary() -> dict[str, object]:
    return {
        "agent_count": len(DEFAULT_AGENT_DEFINITIONS),
        "agent_keys": [agent.agent_key for agent in DEFAULT_AGENT_DEFINITIONS],
        "order_boundary": "read_only_no_order",
        "canonical_write_boundary": "validator_controlled",
        "model_control_surface": "admin_only",
        "default_primary_provider": "agents_sdk_openai",
        "default_fallback_provider": "codex_oauth",
        "default_local_fallback_provider": "local_rules",
    }
