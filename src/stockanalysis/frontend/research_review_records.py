"""Curated 2026-09-11 source audit. Evidence: docs/tasks/research-data-quality-20260911/.

Keys are SHA-256 of the exact API report fields defined in research_content_review.
These records report issues and partial checks; they are not investment approvals.
"""

_COMMON = {
    'status': 'needs_source_correction',
    'reviewed_at': '2026-09-11',
    'reviewer': 'Codex · AI 보조 원문 대조',
    'scope': 'exact_report_content',
    'human_approved': False,
    'limitations': '주요 주장과 수치의 표본 검토입니다. 전체 사실 검증이나 투자 판단 승인을 뜻하지 않습니다. 원 보고서는 보존합니다.',
}

REVIEW_RECORDS = {
    '6c235648d00cb221da416eec97501dba8c030a99f01f584d35d379e5c9889854': {
        **_COMMON,
        'summary': '재무가 없다는 설명에 입력 선택 오류가 있습니다. 최신 실적 원문과 사업 비교군을 보강해야 합니다.',
        'findings': [
            {'title': '재무 결측 설명 수정 필요', 'status': 'issue',
             'detail': '주식 수만 있는 2026-02-20을 연간 재무로 선택했습니다. DB에는 2026-01-25 종료 매출·이익이 있으며 공식 연간 실적과 대조했습니다.',
             'source_label': 'NVIDIA FY2026 실적',
             'source_url': 'https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/default.aspx'},
            {'title': '최근 실적 근거 보강 필요', 'status': 'issue',
             'detail': '8월 26일 공개된 FY2027 2분기 실적 원문이 보고서 입력에 없습니다. 기사 제목을 대신할 회사 실적 근거가 공개돼 있습니다.',
             'source_label': 'NVIDIA FY2027 2분기 실적',
             'source_url': 'https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/default.aspx'},
            {'title': '비교군과 가격 범위는 별도 검증 필요', 'status': 'unverified',
             'detail': 'AI Labor and Productivity는 테마 연결 집합입니다. 비교 수치와 가격 범위는 저장 모델 출력과 일치하지만 사업 경쟁력이나 내재가치의 입증은 아닙니다.'},
        ],
    },
    '0176acd7856fef45cf53cef1965185ab76197cf42f34b8b3312c648cc27824db': {
        **_COMMON,
        'summary': '연간 재무 선택 오류와 격리된 입력 문서가 확인됐습니다. 제품 가격은 공식 발표로 일부 확인했습니다.',
        'findings': [
            {'title': '재무 결측 설명 수정 필요', 'status': 'issue',
             'detail': '주식 수만 있는 2025-10-17을 선택했습니다. DB에는 2025-09-27 종료 매출·순이익·현금흐름이 있습니다. Macro Rates and Fed 비교군은 사업 경쟁사 검증을 거치지 않았습니다.',
             'source_label': 'Apple FY2025 실적',
             'source_url': 'https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/'},
            {'title': '격리된 문서가 과거 입력에 포함', 'status': 'issue',
             'detail': '입력 문서 22는 기사 식별자 충돌로 격리됐습니다. 핵심 주장·촉매에서 직접 인용하지 않았지만 입력 이력이 남아 있어 보고서 전체를 검토 통과로 처리하지 않습니다.'},
            {'title': '제품 가격 일부 확인 · 실적 영향 미확인', 'status': 'partial',
             'detail': '9월 9일 공식 발표에서 iPhone Duo 시작 가격 1,999달러를 확인했습니다. 비용 자체 부담·수요·마진 영향과 MacBook 계획 철회는 이 발표로 입증되지 않습니다.',
             'source_label': 'Apple iPhone Duo 발표',
             'source_url': 'https://www.apple.com/newsroom/2026/09/apple-unveils-iphone-duo/'},
        ],
    },
    '971b02667681c930cd262a07531eb3f3050c3361d1c9f4494296276fc31966ff': {
        **_COMMON,
        'summary': '2025년 주요 수치는 원문과 맞습니다. 이전 매출 누락 설명과 오래된 재무·사업 근거는 보완이 필요합니다.',
        'findings': [
            {'title': '주요 재무 수치 확인 · 최신 기간 누락', 'status': 'partial',
             'detail': '2025년 매출 4,007백만달러, 매출총이익 3,886백만달러, 순이익 792백만달러, 영업현금흐름 397백만달러를 대조했습니다. 2026년 연차보고서가 공개됐지만 보고서는 2025년 지표를 사용합니다.',
             'source_label': 'ARM FY2026 20-F 및 비교 재무',
             'source_url': 'https://investors.arm.com/node/8281/html'},
            {'title': '성장률 미계산은 수집 처리 문제', 'status': 'issue',
             'detail': '2024년 매출 3,233백만달러는 DB와 공시에 모두 있습니다. 서로 다른 기간이 같은 회계연도로 저장돼 이전 연도를 찾지 못했습니다. 공개 자료 부재로 설명하면 안 됩니다.',
             'source_label': 'ARM 연간 비교 재무',
             'source_url': 'https://investors.arm.com/node/8281/html'},
            {'title': '칩 사업 공식 발표 확인 · 매출 기여 별도', 'status': 'partial',
             'detail': '3월 24일 Arm AGI CPU와 Meta 협업 발표를 확인했습니다. 8월 기사 제목보다 직접적인 사업 원천입니다. 고객 매출·수익성의 실현까지 입증하는 자료는 아닙니다.',
             'source_label': 'ARM AGI CPU 공식 발표',
             'source_url': 'https://newsroom.arm.com/news/arm-agi-cpu-launch'},
        ],
    },
}
