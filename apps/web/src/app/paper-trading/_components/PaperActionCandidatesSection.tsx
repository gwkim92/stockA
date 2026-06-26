import type { Route } from "next";
import Link from "next/link";

import { koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { PaperTradingPreviewData } from "@/lib/types";

import {
  formatPaperCurrency,
  formatPaperPercent,
  recommendationHref,
  riskClass,
  thesisHref,
  userFacingText,
} from "./paperTradingFormat";

type PaperActionCandidatesSectionProps = {
  readonly data: PaperTradingPreviewData;
};

export function PaperActionCandidatesSection({ data }: PaperActionCandidatesSectionProps) {
  return (
    <section className="split-ledger reveal delay-2" id="paper-action-candidates">
      <article className="ledger-panel queue-panel">
        <div className="section-heading">
          <span>시뮬레이션 항목 목록</span>
          <h2>주문이 아니라 검증용 항목만 보여준다</h2>
        </div>
        <p className="empty-copy">
          표의 조치는 실제 주문 명령이 아닙니다. 추천서, 투자 논리, 종목 상세를 대조하기 위한 가상 검증 항목이며,
          주문 제출 기능은 의도적으로 닫아 두었습니다.
        </p>
        {data.paper_actions.length > 0 ? (
          <div className="paper-action-card-grid" aria-label="가상 매매 검증 항목">
            {data.paper_actions.map((action) => {
              const recommendationLink = recommendationHref(action.recommendation_id);
              const thesisLink = thesisHref(action.linked_thesis_id);
              return (
                <article
                  className={`paper-action-card ${action.conflict ? "is-conflict" : ""}`}
                  key={`${action.symbol}-${action.paper_action}`}
                >
                  <div className="paper-action-card-head">
                    <span>가상 검증 · 주문 아님</span>
                    <strong>{action.symbol}</strong>
                    <b className={`risk-tag ${riskClass(action.risk_level)}`}>
                      {userFacingText(action.paper_action)}
                    </b>
                  </div>
                  <p>{koReason(action.reason)}</p>
                  <dl className="paper-action-metrics">
                    <div>
                      <dt>현재 비중</dt>
                      <dd>{formatPaperPercent(action.current_weight)}</dd>
                    </div>
                    <div>
                      <dt>목표 비중</dt>
                      <dd>{formatPaperPercent(action.target_weight)}</dd>
                    </div>
                    <div>
                      <dt>추천 점수</dt>
                      <dd>{formatPaperPercent(action.recommendation_score)}</dd>
                    </div>
                  </dl>
                  <div className="paper-action-context">
                    <div>
                      <span>추천 상태</span>
                      <strong>{koCode(action.recommendation_action)}</strong>
                      <small>추천일 {action.recommendation_as_of_date || "미확인"} · 가격일 {action.latest_price_date || "미확인"}</small>
                    </div>
                    <div>
                      <span>실거래 경계</span>
                      <strong>{action.requires_human_approval ? "안전 조건 대기" : "읽기 전용"}</strong>
                      <small>
                        {action.conflict ? "추천과 보유 상태 충돌 있음" : "저장된 충돌 없음"} · 최근 가격{" "}
                        {formatPaperCurrency(action.latest_price)}
                      </small>
                    </div>
                  </div>
                  <div className="paper-action-links">
                    {recommendationLink ? (
                      <Link className="btn btn-secondary" href={recommendationLink}>
                        추천 보기
                      </Link>
                    ) : null}
                    {thesisLink ? (
                      <Link className="btn btn-secondary" href={thesisLink}>
                        투자 논리 보기
                      </Link>
                    ) : null}
                    <Link className="btn btn-secondary" href={`/stocks/${action.symbol}` as Route}>
                      종목 보기
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <p className="empty-state" style={{ margin: 0 }}>
            현재 시뮬레이션 항목이 없습니다. 추천 신호나 보유 내역이 갱신되면 다시 표시됩니다.
          </p>
        )}
      </article>

      <aside className="side-ledger">
        <article className="ledger-panel">
          <div className="section-heading stacked-heading">
            <span>실거래 안전장치</span>
            <h2>아직 실제 주문이 아닌 이유</h2>
          </div>
          <p className="empty-copy">
            아래 항목은 가상 매매 검증 결과입니다. 실제 주문은 증권사 연결, 계좌 권한, 주문 한도,
            킬 스위치, 감사 기록이 모두 통과해야 별도 단계에서만 다룹니다.
          </p>
          <div className="tag-ledger">
            {data.guardrails.map((guardrail) => (
              <span className="risk-tag risk-medium" key={guardrail}>
                {userFacingText(guardrail)}
              </span>
            ))}
          </div>
          <div className="btn-row">
            <Link className="btn btn-secondary" href={"/trading-readiness" as Route}>
              거래 안전 상태 보기
            </Link>
          </div>
        </article>

        <article className="ledger-panel">
          <div className="section-heading stacked-heading">
            <span>성과 해석</span>
            <h2>추천 성과 점검</h2>
          </div>
          <dl className="fact-list">
            <div>
              <dt>포트폴리오</dt>
              <dd>{koLabel(data.portfolio_name)}</dd>
            </div>
            <div>
              <dt>전략</dt>
              <dd>{userFacingText(data.strategy_name)}</dd>
            </div>
            <div>
              <dt>기간</dt>
              <dd>{userFacingText(data.latest_recommendation_batch.horizon_type)}</dd>
            </div>
            <div>
              <dt>종목군</dt>
              <dd>{userFacingText(data.latest_recommendation_batch.universe_version)}</dd>
            </div>
          </dl>
        </article>
      </aside>
    </section>
  );
}
