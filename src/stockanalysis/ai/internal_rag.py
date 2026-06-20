from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from urllib.parse import urlsplit


DEFAULT_CONTEXT_CHAR_BUDGET = 12000


def build_internal_rag_context_package(
    *,
    symbol: str,
    as_of_date: date | str,
    instrument: Mapping[str, object],
    themes: Sequence[Mapping[str, object]],
    theme_edges: Sequence[Mapping[str, object]],
    events: Sequence[Mapping[str, object]],
    story_groups: Sequence[Mapping[str, object]],
    ai_artifacts: Sequence[Mapping[str, object]],
    evidence_chunks: Sequence[Mapping[str, object]],
    theses: Sequence[Mapping[str, object]],
    recommendations: Sequence[Mapping[str, object]],
    positions: Sequence[Mapping[str, object]],
    context_char_budget: int = DEFAULT_CONTEXT_CHAR_BUDGET,
) -> dict[str, object]:
    """Build a secret-free Postgres-backed context package for offline AI batches."""

    normalized_symbol = _safe_token(symbol.upper(), fallback="UNKNOWN")
    as_of_text = as_of_date.isoformat() if isinstance(as_of_date, date) else _safe_text(as_of_date, fallback="")
    section_payloads = [
        _instrument_section(instrument),
        _theme_section(themes, theme_edges),
        _event_section(events, story_groups),
        _source_section(evidence_chunks),
        _ai_artifact_section(ai_artifacts),
        _decision_section(theses, recommendations, positions),
    ]
    evidence_items = _build_evidence_items(
        events=events,
        story_groups=story_groups,
        evidence_chunks=evidence_chunks,
        ai_artifacts=ai_artifacts,
        theses=theses,
        recommendations=recommendations,
    )
    context_text = _build_context_text(
        symbol=normalized_symbol,
        as_of_date=as_of_text,
        sections=section_payloads,
        evidence_items=evidence_items,
        char_budget=context_char_budget,
    )
    translation_ready_count = sum(
        1
        for event in events
        if _safe_text(event.get("korean_title"), fallback="") or _safe_text(event.get("korean_summary"), fallback="")
    )
    chunk_count = len(evidence_chunks)
    artifact_count = len(ai_artifacts)
    event_count = len(events)

    return {
        "status": "ready" if any(section["item_count"] for section in section_payloads) else "empty",
        "symbol": normalized_symbol,
        "as_of_date": as_of_text,
        "retrieval_policy": {
            "mode": "offline_batch_context",
            "retrieval_backend": "postgres_sql_graph_context",
            "canonical_store": "postgres",
            "vector_backend": "not_configured",
            "graph_backend": "postgres_classification_graph",
            "external_rag_service": "not_used",
            "external_vector_db": "not_used",
            "external_graph_db": "not_used",
            "live_llm_call_enabled": False,
            "write_enabled": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
        "context_inventory": {
            "theme_count": len(themes),
            "theme_edge_count": len(theme_edges),
            "event_count": event_count,
            "story_group_count": len(story_groups),
            "ai_artifact_count": artifact_count,
            "evidence_chunk_count": chunk_count,
            "translated_event_count": translation_ready_count,
            "thesis_count": len(theses),
            "recommendation_count": len(recommendations),
            "position_count": len(positions),
            "estimated_prompt_chars": len(context_text),
        },
        "quality_gates": _quality_gates(
            event_count=event_count,
            translation_ready_count=translation_ready_count,
            chunk_count=chunk_count,
            artifact_count=artifact_count,
            recommendation_count=len(recommendations),
        ),
        "sections": section_payloads,
        "evidence_items": evidence_items[:25],
        "prompt_context": {
            "language": "ko",
            "purpose": "종목 분석 AI 배치가 원천 근거, 한국어 번역, 그래프 관계, 추천 연결을 한 번에 검토하기 위한 내부 RAG context다.",
            "instruction": (
                "아래 context만 근거로 사용한다. 원문 근거가 부족하면 unknown으로 남기고, "
                "추천 점수나 주문은 직접 결정하지 않는다."
            ),
            "context_char_budget": context_char_budget,
            "context_text": context_text,
        },
        "guardrails": [
            "Postgres canonical table에서 읽은 증거만 포함한다.",
            "FastAPI 요청 중 live LLM 호출을 하지 않는다.",
            "외부 유료 RAG, vector DB, graph DB를 사용하지 않는다.",
            "벡터 저장 위치, DB URL, token, webhook 같은 secret 값은 포함하지 않는다.",
            "추천 weight, portfolio position, broker/order flow를 변경하지 않는다.",
        ],
    }


def _instrument_section(instrument: Mapping[str, object]) -> dict[str, object]:
    symbol = _safe_text(instrument.get("symbol") or instrument.get("primary_symbol"), fallback="")
    name = _safe_text(instrument.get("name"), fallback="")
    found = bool(instrument.get("found", True)) if instrument else False
    items: list[dict[str, object]] = []
    if symbol or name:
        items.append(
            {
                "item_id": f"instrument:{symbol or 'unknown'}",
                "title_ko": "분석 대상 종목",
                "summary_ko": f"{symbol or '미확인'} · {name or '회사명 미확인'}",
                "metadata": {
                    "symbol": symbol,
                    "market_code": _safe_text(instrument.get("market_code"), fallback=""),
                    "found": found,
                },
            }
        )
    return _section("instrument_identity", "종목 식별", items)


def _theme_section(
    themes: Sequence[Mapping[str, object]], theme_edges: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for theme in themes[:10]:
        theme_key = _safe_text(theme.get("theme_key") or theme.get("code"), fallback="UNKNOWN_THEME")
        items.append(
            {
                "item_id": f"theme:{theme_key}",
                "title_ko": theme_key,
                "summary_ko": (
                    f"{_safe_text(theme.get('theme_name') or theme.get('name'), fallback=theme_key)} · "
                    f"연결 유형 {_safe_text(theme.get('membership_type'), fallback='unknown')} · "
                    f"신뢰도 {_safe_number_text(theme.get('confidence'))}"
                ),
                "metadata": {
                    "theme_key": theme_key,
                    "node_type": _safe_text(theme.get("node_type"), fallback=""),
                    "taxonomy_family": _safe_text(theme.get("taxonomy_family"), fallback=""),
                },
            }
        )
    for edge in theme_edges[:10]:
        parent = _safe_text(edge.get("parent_theme_key") or edge.get("parent_code"), fallback="")
        child = _safe_text(edge.get("child_theme_key") or edge.get("child_code"), fallback="")
        if not parent and not child:
            continue
        items.append(
            {
                "item_id": f"edge:{parent}->{child}",
                "title_ko": "테마 관계",
                "summary_ko": (
                    f"{parent or '상위 미확인'} → {child or '하위 미확인'} · "
                    f"{_safe_text(edge.get('relation_type'), fallback='unknown')} · "
                    f"가중치 {_safe_number_text(edge.get('weight'))}"
                ),
                "metadata": {"parent_theme_key": parent, "child_theme_key": child},
            }
        )
    return _section("classification_graph", "테마·사이클 그래프", items)


def _event_section(
    events: Sequence[Mapping[str, object]], story_groups: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for group in story_groups[:8]:
        title = _best_title(group)
        story_id = _safe_text(group.get("story_id"), fallback=f"story:{len(items) + 1}")
        items.append(
            {
                "item_id": story_id,
                "title_ko": title,
                "summary_ko": (
                    f"뉴스 묶음 · 이벤트 {int(_optional_float(group.get('event_count')) or 0)}개 · "
                    f"묶인 이유 {', '.join(_as_text_list(group.get('relation_reasons'))[:2]) or '미확인'}"
                ),
                "metadata": {
                    "theme_keys": _as_text_list(group.get("theme_keys")),
                    "source_document_ids": _as_text_list(group.get("source_document_ids")),
                },
            }
        )
    for event in events[:12]:
        event_id = _safe_text(event.get("event_id"), fallback=f"event:{len(items) + 1}")
        items.append(
            {
                "item_id": f"event:{event_id}",
                "title_ko": _best_title(event),
                "summary_ko": _safe_text(event.get("korean_summary"), fallback=_safe_text(event.get("title"), fallback="")),
                "metadata": {
                    "event_at": _safe_text(event.get("event_at"), fallback=""),
                    "theme_key": _safe_text(event.get("theme_key"), fallback=""),
                    "impact_direction": _safe_text(event.get("impact_direction"), fallback=""),
                    "impact_score": _optional_float(event.get("impact_score")),
                    "source_document_id": _safe_text(event.get("source_document_id"), fallback=""),
                },
            }
        )
    return _section("events_and_story_groups", "뉴스·공시와 묶음", items)


def _source_section(evidence_chunks: Sequence[Mapping[str, object]]) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for chunk in evidence_chunks[:12]:
        chunk_id = _safe_text(chunk.get("chunk_id"), fallback=f"chunk:{len(items) + 1}")
        source_host = _safe_text(chunk.get("source_url_host"), fallback="")
        if not source_host:
            source_host = _safe_host(_safe_text(chunk.get("source_url"), fallback=""))
        items.append(
            {
                "item_id": f"chunk:{chunk_id}",
                "title_ko": "원문 근거 청크",
                "summary_ko": _safe_text(chunk.get("text_preview"), fallback=""),
                "metadata": {
                    "source_document_id": _safe_text(chunk.get("source_document_id") or chunk.get("document_id"), fallback=""),
                    "chunk_index": int(_optional_float(chunk.get("chunk_index")) or 0),
                    "token_count": int(_optional_float(chunk.get("token_count")) or 0),
                    "source_url_host": source_host,
                    "source_text_kind": _safe_text(chunk.get("source_text_kind"), fallback=""),
                    "embedding_status": _safe_text(chunk.get("embedding_status"), fallback=""),
                },
            }
        )
    return _section("source_chunks", "원문 근거", items)


def _ai_artifact_section(ai_artifacts: Sequence[Mapping[str, object]]) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for artifact in ai_artifacts[:10]:
        evidence_id = _safe_text(artifact.get("evidence_id") or artifact.get("artifact_id"), fallback=f"ai:{len(items) + 1}")
        items.append(
            {
                "item_id": f"ai:{evidence_id}",
                "title_ko": "투자 근거",
                "summary_ko": (
                    f"{_safe_text(artifact.get('evidence_type') or artifact.get('artifact_type'), fallback='artifact')} · "
                    f"{_safe_text(artifact.get('provider'), fallback='provider_unknown')} · "
                    f"상태 {_safe_text(artifact.get('status'), fallback='unknown')} · "
                    f"신뢰도 {_safe_number_text(artifact.get('confidence'))}"
                ),
                "metadata": {
                    "event_id": _safe_text(artifact.get("event_id"), fallback=""),
                    "source_document_id": _safe_text(artifact.get("source_document_id") or artifact.get("document_id"), fallback=""),
                    "model_id": _safe_text(artifact.get("model_id") or artifact.get("model_name"), fallback=""),
                },
            }
        )
    return _section("ai_artifacts", "AI 분석 산출물", items)


def _decision_section(
    theses: Sequence[Mapping[str, object]],
    recommendations: Sequence[Mapping[str, object]],
    positions: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for recommendation in recommendations[:6]:
        recommendation_id = _safe_text(recommendation.get("recommendation_id"), fallback=f"recommendation:{len(items) + 1}")
        items.append(
            {
                "item_id": f"recommendation:{recommendation_id}",
                "title_ko": "추천 검토 연결",
                "summary_ko": (
                    f"{_safe_text(recommendation.get('action'), fallback='unknown')} · "
                    f"점수 {_safe_number_text(recommendation.get('total_score'))} · "
                    f"권장 비중 {_safe_number_text(recommendation.get('recommended_weight'))}"
                ),
                "metadata": {
                    "as_of_date": _safe_text(recommendation.get("as_of_date"), fallback=""),
                    "bucket": _safe_text(recommendation.get("bucket"), fallback=""),
                    "linked_thesis_id": _safe_text(recommendation.get("linked_thesis_id") or recommendation.get("thesis_id"), fallback=""),
                },
            }
        )
    for thesis in theses[:6]:
        thesis_id = _safe_text(thesis.get("thesis_id"), fallback=f"thesis:{len(items) + 1}")
        items.append(
            {
                "item_id": f"thesis:{thesis_id}",
                "title_ko": "투자 논리",
                "summary_ko": (
                    f"{_safe_text(thesis.get('title'), fallback='제목 없음')} · "
                    f"상태 {_safe_text(thesis.get('status'), fallback='unknown')} · "
                    f"확신 {_safe_number_text(thesis.get('conviction_score'))}"
                ),
                "metadata": {
                    "expected_holding_days": int(_optional_float(thesis.get("expected_holding_days")) or 0),
                    "invalidation_conditions": _safe_text(thesis.get("invalidation_conditions"), fallback=""),
                },
            }
        )
    for position in positions[:4]:
        portfolio_name = _safe_text(position.get("portfolio_name"), fallback="portfolio")
        items.append(
            {
                "item_id": f"position:{portfolio_name}:{_safe_text(position.get('snapshot_date'), fallback='')}",
                "title_ko": "보유 포지션",
                "summary_ko": (
                    f"{portfolio_name} · 비중 {_safe_number_text(position.get('weight'))} · "
                    f"시장가치 {_safe_number_text(position.get('market_value'))}"
                ),
                "metadata": {
                    "snapshot_date": _safe_text(position.get("snapshot_date"), fallback=""),
                    "linked_thesis_id": _safe_text(position.get("linked_thesis_id"), fallback=""),
                },
            }
        )
    return _section("decision_context", "추천·보유 맥락", items)


def _build_evidence_items(
    *,
    events: Sequence[Mapping[str, object]],
    story_groups: Sequence[Mapping[str, object]],
    evidence_chunks: Sequence[Mapping[str, object]],
    ai_artifacts: Sequence[Mapping[str, object]],
    theses: Sequence[Mapping[str, object]],
    recommendations: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for group in story_groups[:8]:
        story_id = _safe_text(group.get("story_id"), fallback=f"story:{len(items) + 1}")
        items.append(
            {
                "evidence_id": story_id,
                "evidence_type": "story_group",
                "title_ko": _best_title(group),
                "linking_reason_ko": ", ".join(_as_text_list(group.get("relation_reasons"))[:3]) or "같은 이야기 후보",
                "source_document_ids": _as_text_list(group.get("source_document_ids")),
            }
        )
    for event in events[:10]:
        event_id = _safe_text(event.get("event_id"), fallback=f"event:{len(items) + 1}")
        items.append(
            {
                "evidence_id": f"event:{event_id}",
                "evidence_type": "event",
                "title_ko": _best_title(event),
                "linking_reason_ko": (
                    f"{_safe_text(event.get('theme_key'), fallback='테마 미확인')} · "
                    f"{_safe_text(event.get('impact_direction'), fallback='방향 미확인')}"
                ),
                "source_document_ids": [_safe_text(event.get("source_document_id"), fallback="")],
            }
        )
    for chunk in evidence_chunks[:8]:
        chunk_id = _safe_text(chunk.get("chunk_id"), fallback=f"chunk:{len(items) + 1}")
        items.append(
            {
                "evidence_id": f"chunk:{chunk_id}",
                "evidence_type": "source_chunk",
                "title_ko": "원문 근거",
                "linking_reason_ko": _safe_text(chunk.get("text_preview"), fallback=""),
                "source_document_ids": [_safe_text(chunk.get("source_document_id") or chunk.get("document_id"), fallback="")],
            }
        )
    if ai_artifacts:
        items.append(
            {
                "evidence_id": "ai_artifacts",
                "evidence_type": "ai_artifact_summary",
                "title_ko": "AI 분석 산출물",
                "linking_reason_ko": f"저장된 AI artifact {len(ai_artifacts)}개",
                "source_document_ids": [],
            }
        )
    if theses or recommendations:
        items.append(
            {
                "evidence_id": "decision_links",
                "evidence_type": "decision_context_summary",
                "title_ko": "추천·투자 논리 연결",
                "linking_reason_ko": f"추천 {len(recommendations)}개, 투자 논리 {len(theses)}개",
                "source_document_ids": [],
            }
        )
    return items


def _quality_gates(
    *,
    event_count: int,
    translation_ready_count: int,
    chunk_count: int,
    artifact_count: int,
    recommendation_count: int,
) -> list[dict[str, object]]:
    return [
        {
            "gate": "korean_translation",
            "status": "passed" if event_count == 0 or translation_ready_count == event_count else "attention",
            "message_ko": f"한국어 제목/요약이 있는 이벤트 {translation_ready_count}/{event_count}개",
        },
        {
            "gate": "source_grounding",
            "status": "passed" if chunk_count > 0 else "attention",
            "message_ko": f"원문 청크 {chunk_count}개를 context에 포함",
        },
        {
            "gate": "ai_artifact_linkage",
            "status": "passed" if artifact_count > 0 else "attention",
            "message_ko": f"저장된 투자 근거 {artifact_count}개",
        },
        {
            "gate": "decision_linkage",
            "status": "passed" if recommendation_count > 0 else "watch",
            "message_ko": f"추천 검토 연결 {recommendation_count}개",
        },
        {
            "gate": "write_order_boundary",
            "status": "passed",
            "message_ko": "RAG context 생성은 읽기 전용이며 주문/쓰기 경계를 열지 않는다.",
        },
    ]


def _build_context_text(
    *,
    symbol: str,
    as_of_date: str,
    sections: Sequence[Mapping[str, object]],
    evidence_items: Sequence[Mapping[str, object]],
    char_budget: int,
) -> str:
    lines = [
        f"[대상] {symbol}",
        f"[기준일] {as_of_date}",
        "[역할] 이 context는 중장기 투자 분석 AI 배치의 근거 묶음이다. 원문 근거가 없으면 추정하지 않는다.",
    ]
    for section in sections:
        lines.append(f"\n## {section['title_ko']} ({section['item_count']}개)")
        for item in _as_list(section.get("items"))[:8]:
            title = _safe_text(item.get("title_ko"), fallback="")
            summary = _safe_text(item.get("summary_ko"), fallback="")
            lines.append(f"- {title}: {summary}")
    if evidence_items:
        lines.append("\n## 주요 근거")
        for item in evidence_items[:12]:
            lines.append(f"- {item['title_ko']}: {item['linking_reason_ko']}")
    context_text = "\n".join(lines)
    if char_budget < 500:
        raise ValueError("context_char_budget must be at least 500.")
    return context_text[:char_budget]


def _section(section_id: str, title_ko: str, items: list[dict[str, object]]) -> dict[str, object]:
    return {
        "section_id": section_id,
        "title_ko": title_ko,
        "item_count": len(items),
        "items": items,
    }


def _best_title(item: Mapping[str, object]) -> str:
    return _safe_text(
        item.get("korean_title") or item.get("korean_summary") or item.get("title"),
        fallback="제목 미확인",
        max_length=240,
    )


def _safe_text(value: object, *, fallback: str, max_length: int = 500) -> str:
    text = str(value or "").replace("\x00", " ").strip()
    if not text:
        return fallback
    compact = " ".join(text.split())
    return compact[:max_length]


def _safe_token(value: object, *, fallback: str) -> str:
    text = _safe_text(value, fallback=fallback, max_length=64)
    return "".join(char for char in text if char.isalnum() or char in {"_", "-", ".", ":"}) or fallback


def _safe_number_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "unknown"
    return f"{number:.4f}"


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_list(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    if isinstance(value, tuple):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _as_text_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_safe_text(item, fallback="", max_length=120) for item in value if _safe_text(item, fallback="")]


def _safe_host(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    return parsed.hostname or ""
