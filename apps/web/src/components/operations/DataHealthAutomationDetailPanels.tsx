import type {
  DataHealthAutomationCard,
  DataHealthFactRow,
  DataHealthLocalWorkerPanel,
  DataHealthManualSmokePanel,
  DataHealthOperatingFlowStep,
  DataHealthProfileSchedulerPanel,
  DataHealthSchedulerDetailPanel,
} from "./DataHealthAutomationDetailTypes";

function FactList({ rows }: { readonly rows: readonly DataHealthFactRow[] }) {
  return (
    <dl className="fact-list compact-facts">
      {rows.map((row) => (
        <div key={`${row.label}-${row.value}`}>
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SchedulerDetailPanel({ panel }: { readonly panel: DataHealthSchedulerDetailPanel }) {
  return (
    <article className="ledger-panel" id="scheduler-detail">
      <div className="section-heading stacked-heading">
        <span>자동 반복 실행 상태</span>
        <h3>{panel.title}</h3>
      </div>
      <p className="panel-support-copy">{panel.description}</p>
      <FactList rows={panel.factRows} />
    </article>
  );
}

export function ExecutionStructurePanel() {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>실제 실행 구조</span>
        <h3>웹 화면은 저장된 결과를 읽고, 서버 예약 작업이 수집·분석을 실행한다</h3>
      </div>
      <p className="panel-support-copy">
        FastAPI와 Next.js는 저장된 결과를 읽어 보여준다. 뉴스 수집, 캔들 보강, AI 분석, 추천 갱신은 서버 예약
        실행기가 백그라운드 작업 실행기를 호출해 수행하고, 결과는 서버 저장 기록과 실행 요약에 남긴다.
      </p>
      <FactList
        rows={[
          { label: "화면", value: "Next.js 운영 화면" },
          { label: "읽기 API", value: "FastAPI 읽기 전용 백엔드" },
          { label: "작업 실행", value: "서버 예약 실행 → 백그라운드 작업 실행기" },
          { label: "상태 저장", value: "서버 저장 기록 + 저장소 밖 실행 요약" },
        ]}
      />
    </article>
  );
}

export function ProfileSchedulerPanel({ panel }: { readonly panel: DataHealthProfileSchedulerPanel }) {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>서버 반복 실행기</span>
        <h3>{panel.activeTimerSummaryLabel}</h3>
      </div>
      <p className="panel-support-copy">
        수집기는 하나로 묶여 있지 않다. 뉴스/AI는 짧은 주기, 캔들은 장 마감 후, 신호/추천은 캔들 이후,
        거시·SEC·성과는 느린 주기로 분리되어 돈을 아끼면서도 필요한 데이터가 갱신되게 한다.
      </p>
      <div className="scheduler-timer-grid">
        {panel.timers.map((timer) => (
          <div className="scheduler-timer-card" key={timer.profileLabel}>
            <span>{timer.profileLabel}</span>
            <strong>{timer.activeStateLabel}</strong>
            <small>{timer.scheduleLabel}</small>
            <dl>
              <div>
                <dt>다음 실행</dt>
                <dd>{timer.nextElapseLabel}</dd>
              </div>
              <div>
                <dt>마지막 결과</dt>
                <dd>{timer.lastResultLabel}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </article>
  );
}

export function NewsAfterAnalysisPanel({ steps }: { readonly steps: readonly DataHealthOperatingFlowStep[] }) {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>뉴스 분석 이후 운영 흐름</span>
        <h3>AI 근거 이후에는 추천·투자 논리·보유 상태로 넘어간다</h3>
      </div>
      <p className="panel-support-copy">
        뉴스 분석은 끝점이 아니다. 수집된 뉴스는 이벤트와 AI 근거가 되고, 이후 가격·테마·사이클 데이터와
        결합되어 중장기 추천 항목, 투자 논리, 보유 상태 큐를 만든다. 주문은 자동 실행하지 않는다.
      </p>
      <div className="operating-flow-grid">
        {steps.map((step) => (
          <div className="operating-flow-card" key={step.index}>
            <b>{step.index}</b>
            <span>{step.ownerLabel}</span>
            <strong>{step.title}</strong>
            <p>{step.output}</p>
            <small>{step.next}</small>
            {step.warningLabel ? <small>{step.warningLabel}</small> : null}
            <dl>
              <div>
                <dt>상태</dt>
                <dd>{step.statusLabel}</dd>
              </div>
              <div>
                <dt>최근 완료</dt>
                <dd>{step.finishedAtLabel}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </article>
  );
}

export function LocalWorkerPanel({ panel }: { readonly panel: DataHealthLocalWorkerPanel }) {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>{panel.eyebrow}</span>
        <h3>{panel.title}</h3>
      </div>
      <p className="panel-support-copy">{panel.description}</p>
      <FactList rows={panel.factRows} />
      {panel.cycleRows.length > 0 ? (
        <div className="ledger-table-wrap table-section">
          <table className="ledger-table data-health-table">
            <thead>
              <tr>
                <th scope="col">회차</th>
                <th scope="col">단발 점검</th>
                <th scope="col">작업</th>
                <th scope="col">결과 기록</th>
              </tr>
            </thead>
            <tbody>
              {panel.cycleRows.map((row) => (
                <tr key={`${row.title}-${row.startedAtLabel}`}>
                  <td>
                    <strong>{row.title}</strong>
                    <small>{row.startedAtLabel}</small>
                  </td>
                  <td>{row.smokeStatusLabel}</td>
                  <td>{row.jobCountLabel}</td>
                  <td>{row.artifactRunCountLabel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </article>
  );
}

export function ManualSmokePanel({ panel }: { readonly panel: DataHealthManualSmokePanel }) {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>{panel.eyebrow}</span>
        <h3>{panel.title}</h3>
      </div>
      <p className="panel-support-copy">{panel.description}</p>
      <FactList rows={panel.factRows} />
      {panel.artifactRows.length > 0 ? (
        <div className="ledger-table-wrap table-section">
          <table className="ledger-table data-health-table">
            <thead>
              <tr>
                <th scope="col">작업</th>
                <th scope="col">상태</th>
                <th scope="col">종료 코드</th>
                <th scope="col">오류 내용</th>
              </tr>
            </thead>
            <tbody>
              {panel.artifactRows.map((row) => (
                <tr key={`${row.jobLabel}-${row.exitCodeLabel}`}>
                  <td>
                    <strong>{row.jobLabel}</strong>
                    <small>{row.pipelineLabel}</small>
                  </td>
                  <td>{row.statusLabel}</td>
                  <td>{row.exitCodeLabel}</td>
                  <td>{row.errorLabel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </article>
  );
}

export function AutomationCardsPanel({ cards }: { readonly cards: readonly DataHealthAutomationCard[] }) {
  return (
    <div className="flow-steps data-health-summary-grid">
      {cards.map((card) => (
        <article className="flow-step" key={card.title}>
          <span>{card.title}</span>
          <strong>{card.stateLabel}</strong>
          <p>{card.description}</p>
          <FactList
            rows={[
              { label: "반복 기준", value: card.cadenceLabel },
              { label: "최근 완료", value: card.finishedAtLabel },
              { label: "사용처", value: card.detail },
            ]}
          />
        </article>
      ))}
    </div>
  );
}
