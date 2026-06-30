import { koCode } from "@/lib/korean-labels";

import {
  executionIdLabel,
  formatPercent,
  newsAiEvalExplanation,
  newsAiEvalTitle,
  newsAiEvalTone,
  operationCopy,
} from "./dataHealthModel";
import type { NewsAiEvalQuality } from "./dataHealthTypes";

type DataHealthNewsAiEvalQualitySectionProps = {
  readonly newsAiEvalQuality: NewsAiEvalQuality;
};

export function DataHealthNewsAiEvalQualitySection({
  newsAiEvalQuality,
}: DataHealthNewsAiEvalQualitySectionProps) {
  return (
    <section
      className="feature-map-panel reveal delay-1"
      id="news-ai-eval-quality"
      aria-labelledby="news-ai-eval-quality-title"
    >
      <div className="section-heading stacked-heading">
        <span>뉴스 AI 기준 평가</span>
        <h2 id="news-ai-eval-quality-title">
          AI가 뉴스에서 테마와 종목을 잘못 뽑기 시작했는지 기준 세트로 본다.
        </h2>
      </div>
      <p className="board-intro">{newsAiEvalExplanation(newsAiEvalQuality)}</p>
      <div className="status-rail compact-rail">
        <article className="rail-cell">
          <span>평가 결과</span>
          <strong className={`risk-tag ${newsAiEvalTone(newsAiEvalQuality)}`}>
            {newsAiEvalTitle(newsAiEvalQuality)}
          </strong>
          <small>{newsAiEvalQuality.created_at || "최근 결과 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>통과 항목</span>
          <strong>
            {newsAiEvalQuality.passed_case_count}/{newsAiEvalQuality.case_count}
          </strong>
          <small>{executionIdLabel(newsAiEvalQuality.eval_run_id)}</small>
        </article>
        <article className="rail-cell">
          <span>테마 정밀도</span>
          <strong>{formatPercent(newsAiEvalQuality.theme_precision)}</strong>
          <small>금리·양자·에너지 등</small>
        </article>
        <article className="rail-cell">
          <span>종목 근거 정밀도</span>
          <strong>{formatPercent(newsAiEvalQuality.direct_ticker_grounding_precision)}</strong>
          <small>원문 없는 종목 코드 차단</small>
        </article>
        <article className="rail-cell">
          <span>한국어 준비</span>
          <strong>{formatPercent(newsAiEvalQuality.korean_translation_availability)}</strong>
          <small>제목·요약 기준</small>
        </article>
      </div>
      <div className="insight-grid">
        <article className="insight-card">
          <span>거시 뉴스 종목 오부착</span>
          <strong>{newsAiEvalQuality.macro_only_false_ticker_count}</strong>
          <p>금리·물가 같은 상위 흐름 뉴스를 억지로 개별 종목에 붙이면 추천 근거가 오염된다.</p>
        </article>
        <article className="insight-card">
          <span>양자→에너지 오분류</span>
          <strong>{newsAiEvalQuality.quantum_energy_misclassification_count}</strong>
          <p>양자컴퓨팅 정책 뉴스가 XOM/XLE 또는 에너지 테마로 잘못 흐르는지 본다.</p>
        </article>
        <article className="insight-card">
          <span>차단 후보 정확도</span>
          <strong>{formatPercent(newsAiEvalQuality.blocked_candidate_correctness)}</strong>
          <p>자동 검증이 낮은 신뢰도, 원문 근거 없는 종목 코드, 알 수 없는 테마를 제대로 막는지 본다.</p>
        </article>
        <article className="insight-card">
          <span>평가 방식</span>
          <strong>{koCode(newsAiEvalQuality.provider)}</strong>
          <p>기본 평가는 무료 기준 정답 뉴스 세트로 돈다. 실시간 유료 AI 호출이 아니라 저장된 기준 세트 검증이다.</p>
        </article>
      </div>
      <div className="simple-table-wrap">
        <table className="simple-table">
          <thead>
            <tr>
              <th>평가 항목</th>
              <th>결과</th>
              <th>테마</th>
              <th>직접 종목</th>
              <th>차단/오류</th>
            </tr>
          </thead>
          <tbody>
            {newsAiEvalQuality.case_results.slice(0, 6).map((item) => (
              <tr key={item.case_id}>
                <td>
                  <strong>{koCode(item.case_id)}</strong>
                  <small>{koCode(item.category)}</small>
                </td>
                <td>{item.passed ? "통과" : "중단"}</td>
                <td>{item.accepted_theme_codes.map(koCode).join(" · ") || "없음"}</td>
                <td>{item.accepted_direct_symbols.join(" · ") || "없음"}</td>
                <td>
                  {[
                    ...item.missing_theme_codes,
                    ...item.missing_direct_symbols,
                    ...item.forbidden_theme_hits,
                    ...item.forbidden_symbol_hits,
                    ...item.blocked_symbols_accepted,
                  ]
                    .map(koCode)
                    .join(" · ") || "없음"}
                </td>
              </tr>
            ))}
            {newsAiEvalQuality.case_results.length === 0 ? (
              <tr>
                <td colSpan={5}>저장된 평가 항목이 없다.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <div className="empty-state">
        <strong>다음 조치</strong>
        <p>{operationCopy(newsAiEvalQuality.next_action)}</p>
      </div>
    </section>
  );
}
