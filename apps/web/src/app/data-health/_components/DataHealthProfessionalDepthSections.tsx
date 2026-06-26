import { koCode } from "@/lib/korean-labels";

import type { ProfessionalAnalysisDepth, ProfessionalSourceGapPrioritization } from "./dataHealthTypes";
import {
  executionIdLabel,
  formatPercent,
  operationCopy,
  orderBoundaryCopy,
  professionalDepthItemTone,
  professionalDepthStatusLabel,
  professionalDepthTitle,
  professionalDepthTone,
  professionalSourceGapExplanation,
  professionalSourceGapTitle,
  professionalSourceGapTone,
  statusRiskClass,
} from "./dataHealthModel";

type DataHealthProfessionalDepthSectionsProps = {
  readonly professionalDepth: ProfessionalAnalysisDepth;
  readonly professionalSourceGaps: ProfessionalSourceGapPrioritization;
};

export function DataHealthProfessionalDepthSections({
  professionalDepth,
  professionalSourceGaps,
}: DataHealthProfessionalDepthSectionsProps) {
  return (
    <>
      <section
        className="feature-map-panel reveal delay-1"
        id="professional-analysis-depth"
        aria-labelledby="professional-analysis-depth-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 깊이</span>
          <h2 id="professional-analysis-depth-title">
            활성 후보가 재무·피어·밸류에이션·리서치 근거를 얼마나 갖췄는지 본다.
          </h2>
        </div>
        <p className="board-intro">
          이 영역은 추천 점수를 바꾸지 않는다. 어떤 종목이 전문 분석서로 충분히 설명 가능한지, 어떤 종목은 원천 데이터 부족으로
          판단 입력에서 제외해야 하는지만 보여준다.
        </p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${professionalDepthTone(professionalDepth)}`}>
              {professionalDepthTitle(professionalDepth)}
            </strong>
            <small>{professionalDepth.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell">
	            <span>활성 후보</span>
            <strong>{professionalDepth.active_candidate_count}</strong>
            <small>개별 기업 {professionalDepth.operating_company_candidate_count} · ETF/펀드 {professionalDepth.fund_like_candidate_count}</small>
          </article>
          <article className="rail-cell">
            <span>완비 후보</span>
            <strong>{professionalDepth.complete_candidate_count}</strong>
	            <small>필요 근거 충족</small>
          </article>
          <article className="rail-cell">
	            <span>평균 연결률</span>
            <strong>{formatPercent(professionalDepth.average_coverage_ratio)}</strong>
            <small>최저 {formatPercent(professionalDepth.weakest_coverage_ratio)}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>원천 차단</span>
            <strong>{professionalDepth.source_blocked_count}</strong>
            <small>합성 재무 금지</small>
          </article>
          <article className="rail-cell rail-critical">
	            <span>추천 산식/실거래 상태</span>
	            <strong>{professionalDepth.automatic_weight_change_allowed ? "추천 산식 변경 허용" : "추천 산식 변경 금지"}</strong>
            <small>{orderBoundaryCopy(professionalDepth.order_boundary)}</small>
          </article>
        </div>

        <div className="insight-grid">
          {professionalDepth.layer_coverage.map((layer) => (
            <article className="insight-card" key={layer.layer_key}>
              <span>{operationCopy(layer.label)}</span>
              <strong>{formatPercent(layer.coverage_ratio)}</strong>
              <p>
                {layer.available_count}/{layer.expected_count}개 후보가 이 근거를 갖췄다.
              </p>
            </article>
          ))}
          {professionalDepth.layer_coverage.length === 0 ? (
            <article className="insight-card">
	              <span>근거 없음</span>
              <strong>계산 대기</strong>
	              <p>활성 후보별 재무·피어·밸류에이션·리서치 연결률을 아직 계산하지 못했다.</p>
            </article>
          ) : null}
        </div>

        {professionalDepth.items.length > 0 ? (
          <div className="feature-map-grid collection-map-grid">
            {professionalDepth.items.map((item) => (
              <article className="feature-map-card collection-map-card" key={`${item.rank}-${item.symbol}`}>
                <span>
                  #{item.rank} · {item.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}
                </span>
                <strong>
                  <a href={item.detail_href}>{item.symbol}</a> · {professionalDepthStatusLabel(item.depth_status)}
                </strong>
                <small>{item.instrument_name || "종목명 미확인"}</small>
                <small>
                  근거 연결률 {formatPercent(item.coverage_ratio)} · 근거 {item.available_layer_count}/{item.expected_layer_count}
                </small>
                <small>추천 연결 {item.active_recommendation_count}개 · 보유 {formatPercent(item.current_weight)}</small>
                <small className={`risk-tag ${professionalDepthItemTone(item.depth_status)}`}>
                  {professionalDepthStatusLabel(item.depth_status)}
                </small>
                {item.missing_layer_labels.length > 0 ? (
                  <p>부족 근거: {item.missing_layer_labels.join(" · ")}</p>
                ) : (
                  <p>현재 기준에서 표시할 부족 근거가 없다.</p>
                )}
                {item.blocker_code ? <small>차단 사유 {koCode(item.blocker_code)}</small> : null}
                {item.remediation_action ? <p>{operationCopy(item.remediation_action)}</p> : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            활성 추천 기준으로 표시할 전문 분석 후보가 없다.
          </div>
        )}

        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalDepth.next_action)}</p>
        </div>
      </section>

      <section
        className="feature-map-panel reveal delay-1"
        id="professional-source-gaps"
        aria-labelledby="professional-source-gaps-title"
      >
        <div className="section-heading stacked-heading">
          <span>전문 분석 소스 공백</span>
          <h2 id="professional-source-gaps-title">
            추천·보유 판단에 필요한 재무, 밸류에이션, 펀드 원천이 어디서 막혔는지 본다.
          </h2>
        </div>
        <p className="board-intro">{professionalSourceGapExplanation(professionalSourceGaps)}</p>
        <div className="status-rail compact-rail">
          <article className="rail-cell">
            <span>판정</span>
            <strong className={`risk-tag ${professionalSourceGapTone(professionalSourceGaps)}`}>
              {professionalSourceGapTitle(professionalSourceGaps)}
            </strong>
            <small>{professionalSourceGaps.as_of_date || "기준일 없음"}</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>우선 보강</span>
            <strong>{professionalSourceGaps.high_priority_count}</strong>
            <small>추천·보유 노출 큰 공백</small>
          </article>
          <article className="rail-cell">
            <span>원천 차단</span>
            <strong>{professionalSourceGaps.source_blocker_count}</strong>
            <small>SEC/companyfacts 등</small>
          </article>
          <article className="rail-cell rail-critical">
            <span>추천 차단 적용</span>
            <strong>{professionalSourceGaps.guarded_source_blocked_recommendation_count}</strong>
            <small>전문 판단·가상 매매 입력 차단</small>
          </article>
          <article className="rail-cell">
            <span>펀드 비적용</span>
            <strong>{professionalSourceGaps.fund_not_applicable_count}</strong>
            <small>기업 재무 모델 제외</small>
          </article>
          <article className="rail-cell">
            <span>전체 공백</span>
            <strong>{professionalSourceGaps.gap_count}</strong>
            <small>상위 {professionalSourceGaps.gaps.length}개 표시</small>
          </article>
        </div>

        {professionalSourceGaps.gaps.length > 0 ? (
          <div className="ledger-table-wrap" style={{ marginTop: "18px" }}>
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">우선순위</th>
                  <th scope="col">대상</th>
                  <th scope="col">무엇이 비었나</th>
                  <th scope="col">왜 막혔나</th>
                  <th scope="col">다음 조치</th>
                </tr>
              </thead>
              <tbody>
                {professionalSourceGaps.gaps.map((gap) => (
                  <tr key={`${gap.priority_rank}-${gap.symbol}`}>
                    <td>
                      <strong>#{gap.priority_rank}</strong>
                      <small className={`risk-tag ${statusRiskClass(gap.priority_band)}`}>
                        {koCode(gap.priority_band)}
                      </small>
                    </td>
                    <td>
                      <strong>
                        <a href={gap.detail_href}>{gap.symbol}</a>
                      </strong>
                      <small>{gap.product_type === "fund_or_etf" ? "ETF·펀드형" : "개별 기업"}</small>
                      <small>
                        추천 {gap.active_recommendation_count}개 · 보유 {formatPercent(gap.current_weight)}
                      </small>
                    </td>
                    <td>
                      <strong>{gap.missing_layer_count}개 layer</strong>
                      <small>
                        {gap.missing_layer_labels.length > 0
                          ? gap.missing_layer_labels.join(" · ")
                          : "기업 재무 모델 비적용만 표시"}
                      </small>
                    </td>
                    <td>
                      <strong>{gap.blocker_label}</strong>
                      <small>{gap.blocker_code || koCode(gap.blocker_type)}</small>
                      {gap.source_run_id ? <small>{executionIdLabel(gap.source_run_id)}</small> : null}
                      {gap.active_recommendation_professional_use_blocked ? (
                        <small className="risk-tag risk-high">추천 전문 판단 차단됨</small>
                      ) : null}
                    </td>
                    <td>
                      <strong>{gap.remediation_action}</strong>
                      {gap.remediation_command ? <small>{gap.remediation_command}</small> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            활성 추천 기준으로 표시할 전문 분석 원천 공백이 없다.
          </div>
        )}
        <div className="empty-state">
          <strong>다음 조치</strong>
          <p>{operationCopy(professionalSourceGaps.next_action)}</p>
        </div>
      </section>
    </>
  );
}
