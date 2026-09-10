"""One read-only recommendation policy for list and detail projections."""


def recommendation_boundary(*, has_thesis: bool, component_count: int,
                            evidence_count: int, source_blocked: bool,
                            outcome_measured: bool, evidence_blocked: bool = False) -> dict[str, object]:
    if source_blocked:
        status, reason = 'blocked_source', '원천 자료가 차단되어 가상 검증에 사용할 수 없습니다.'
    elif not has_thesis:
        status, reason = 'blocked_missing_thesis', '투자 논리가 연결되지 않아 근거 보강이 필요합니다.'
    elif component_count <= 0:
        status, reason = 'blocked_missing_score_components', '추천 점수의 입력 근거가 없습니다.'
    elif evidence_count <= 0 or evidence_blocked:
        status, reason = 'blocked_missing_ai_or_event_evidence', '뉴스·공시·AI 근거의 보강 또는 검토가 필요합니다.'
    elif not outcome_measured:
        status, reason = 'paper_validation_pending', '가상 검증 입력은 가능합니다. 성과가 아직 기록되지 않아 검증 완료로 볼 수 없습니다.'
    else:
        status, reason = 'decision_review_ready', '근거와 성과 기록을 함께 검토할 수 있습니다. 투자 판단의 채택은 별도 검토가 필요합니다.'
    return {
        'status': status, 'reason': reason,
        'paper_validation_input_allowed': not status.startswith('blocked'),
        'outcome_measured': outcome_measured,
        'automatic_order_allowed': False, 'broker_submit_allowed': False,
        'order_boundary': 'read_only_no_order',
    }
