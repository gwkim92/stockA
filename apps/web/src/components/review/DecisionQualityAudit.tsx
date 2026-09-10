import { koCode, koReason } from '@/lib/korean-labels';
import { percent, weight, type Outcome, type ReviewReport } from '@/lib/review-workspace-model';
import { recommendationQualityAudit } from '@/lib/recommendation-quality-model';
import styles from './DecisionQualityAudit.module.css';

const ratio = (value: number, total: number) => total ? `${value}/${total} · ${((value / total) * 100).toLocaleString('ko-KR',{maximumFractionDigits:1})}%` : '미측정';
const bps = (value: number | null) => value === null ? '미측정' : `${value > 0 ? '+' : ''}${value.toLocaleString('ko-KR',{maximumFractionDigits:2})}bp`;

export function DecisionQualityAudit({ report, outcomes }: { report: ReviewReport; outcomes: readonly Outcome[] }) {
  const audit = recommendationQualityAudit(report, outcomes);
  return <section className={styles.audit} aria-labelledby="quality-audit-title" data-testid="decision-quality-audit">
    <div className={styles.heading}><div><span>DECISION QUALITY AUDIT</span><h2 id="quality-audit-title">추천 품질 감사</h2><p>저장된 보고서 요약과 수신된 추천별 결과를 분리해 대조합니다.</p></div><div className={styles.status}><small>보고서 품질 상태</small><strong>{koCode(audit.qualityStatus)}</strong><span>{koCode(audit.sampleStatus)}</span></div></div>

    <div className={styles.metrics} role="region" aria-label="추천 품질 핵심 지표">
      <div><span>수신 결과</span><strong>{audit.derived.received}개</strong><small>현재 응답 행 기준</small></div>
      <div><span>실제 측정 가능</span><strong>{audit.derived.measured ? `${audit.derived.measured}개` : '미측정'}</strong><small>alpha + 관찰기간 확인</small></div>
      <div><span>평균 초과수익</span><strong>{percent(audit.derived.averageAlpha, true)}</strong><small>측정 가능한 행에서 재계산</small></div>
      <div><span>행 기준 적중률</span><strong>{weight(audit.derived.hitRate)}</strong><small>alpha &gt; 0 비중</small></div>
    </div>

    <div className={styles.grid}>
      <section className={styles.panel} aria-labelledby="consistency-title"><div className={styles.panelHead}><h3 id="consistency-title">보고서 내부 일관성</h3><span data-tone={audit.mismatchCount ? 'warn':'ok'}>{audit.mismatchCount ? `${audit.mismatchCount}개 불일치` : '확인된 불일치 없음'}</span></div>
        <p className={styles.note}>저장된 요약값을 자동 수정하지 않습니다. 차이가 있으면 생산 파이프라인을 재검토해야 합니다.</p>
        <div className={styles.checks}>{audit.checks.map(check=><div key={check.key} data-status={check.status}><div><strong>{check.label}</strong><span>{check.status === 'match' ? '일치' : check.status === 'mismatch' ? '불일치' : '비교 불가'}</span></div><dl><div><dt>저장 보고서</dt><dd>{check.key === 'measured' ? (check.stored===null?'미확인':`${check.stored}개`) : check.key === 'hit' ? weight(check.stored) : percent(check.stored,true)}</dd></div><div><dt>수신 행 재계산</dt><dd>{check.key === 'measured' ? (check.derived===null?'미측정':`${check.derived}개`) : check.key === 'hit' ? weight(check.derived) : percent(check.derived,true)}</dd></div></dl></div>)}</div>
      </section>

      <section className={styles.panel} aria-labelledby="coverage-title"><div className={styles.panelHead}><h3 id="coverage-title">측정·연결 커버리지</h3></div>
        <dl className={styles.coverage}><div><dt>추천 링크 유지</dt><dd>{ratio(audit.derived.recommendationLinked,audit.derived.measured)}</dd></div><div><dt>투자 논리 링크 유지</dt><dd>{ratio(audit.derived.thesisLinked,audit.derived.measured)}</dd></div><div><dt>벤치마크 수익 존재</dt><dd>{ratio(audit.derived.benchmarkMeasured,audit.derived.measured)}</dd></div><div><dt>미측정 결과</dt><dd>{audit.derived.unmeasured}개</dd></div></dl>
        {!!audit.exclusions.length && <div className={styles.exclusions}><h4>측정 제외</h4>{audit.exclusions.map((row,index)=><div key={`${row.symbol}-${index}`}><strong>{row.symbol}</strong><span>{koCode(row.reason)} · {weight(row.weight)}</span><small>{koCode(row.action)}</small></div>)}</div>}
      </section>
    </div>

    <section className={styles.panel} aria-labelledby="cohort-title"><div className={styles.panelHead}><h3 id="cohort-title">관찰 기간별 성과</h3><span>서로 다른 기간을 하나의 연환산 수익률로 합치지 않습니다</span></div>
      {audit.horizonCohorts.length ? <div className={styles.cohorts}>{audit.horizonCohorts.map(row=><div key={row.key}><strong>{row.label}</strong><span>{row.measured}/{row.total} 측정</span><dl><div><dt>평균 alpha</dt><dd>{percent(row.averageAlpha,true)}</dd></div><div><dt>적중률</dt><dd>{weight(row.hitRate)}</dd></div></dl></div>)}</div> : <p className={styles.empty}>관찰 기간이 확인된 결과가 없습니다.</p>}
    </section>

    <section className={styles.panel} aria-labelledby="action-title"><div className={styles.panelHead}><h3 id="action-title">추천 행동별 결과</h3><span>행 수가 적은 그룹은 그대로 작은 표본입니다</span></div>
      {audit.actionCohorts.length ? <div className={styles.cohorts}>{audit.actionCohorts.map(row=><div key={row.key}><strong>{koCode(row.label)}</strong><span>{row.measured}/{row.total} 측정</span><dl><div><dt>평균 alpha</dt><dd>{percent(row.averageAlpha,true)}</dd></div><div><dt>적중률</dt><dd>{weight(row.hitRate)}</dd></div></dl></div>)}</div> : <p className={styles.empty}>추천 행동별로 묶을 수 있는 결과가 없습니다.</p>}
    </section>

    <div className={styles.grid}>
      <section className={styles.panel} aria-labelledby="gate-title"><div className={styles.panelHead}><h3 id="gate-title">품질 게이트</h3></div>{audit.gates.length ? <ul className={styles.gates}>{audit.gates.map((gate,index)=><li key={`${gate.gate}-${index}`}><div><strong>{koCode(gate.gate)}</strong><span>{koCode(gate.status)}</span></div><p>{koReason(gate.reason)}</p></li>)}</ul> : <p className={styles.empty}>저장된 품질 게이트가 없습니다.</p>}</section>
      <section className={styles.panel} aria-labelledby="lens-title"><div className={styles.panelHead}><h3 id="lens-title">관점별 기여 렌즈</h3></div>{audit.lenses.length ? <ul className={styles.gates}>{audit.lenses.map((lens,index)=><li key={`${lens.type}-${index}`}><div><strong>{lens.label}</strong><span>{bps(lens.contributionBps)}</span></div><p>{koCode(lens.type)}{lens.symbol ? ` · ${lens.symbol}`:''}{lens.theme ? ` · ${lens.theme}`:''} · alpha {percent(lens.alpha,true)}</p></li>)}</ul> : <p className={styles.empty}>저장된 기여도 렌즈가 없습니다.</p>}<p className={styles.note}>종목 선택·테마 노출·현금 타이밍은 설명 렌즈이며 서로 합산해 총수익률을 만들지 않습니다.</p></section>
    </div>
  </section>;
}
