import { koCode } from "@/lib/korean-labels";

import type { SchedulerCadenceGroup } from "./dataHealthModel";
import {
  schedulerGroupNextElapse,
  schedulerGroupStatusLabel,
  schedulerGroupTone,
} from "./dataHealthModel";

type DataHealthSchedulerCadenceSectionProps = {
  readonly ec2SchedulerInstalled: boolean;
  readonly groups: readonly SchedulerCadenceGroup[];
};

export function DataHealthSchedulerCadenceSection({
  ec2SchedulerInstalled,
  groups,
}: DataHealthSchedulerCadenceSectionProps) {
  return (
    <section className="feature-map-panel reveal delay-1" aria-labelledby="scheduler-profile-title">
      <div className="section-heading stacked-heading">
        <span>자동 실행 주기</span>
        <h2 id="scheduler-profile-title">
          {ec2SchedulerInstalled ? "현재 서버에서 실제로 도는 작업" : "자동 실행 연결 상태"}
        </h2>
      </div>
      <p className="board-intro">
        웹 화면은 작업을 직접 실행하지 않고 저장된 결과를 읽는다. 실제 수집과 분석은 아래 작업들이 각자
        다른 주기로 실행한다.
      </p>
      {groups.length > 0 ? (
        <div className="cadence-group-grid">
          {groups.map((group) => (
            <article className="cadence-group-card" key={group.key}>
              <div className="cadence-group-head">
                <span>{group.label}</span>
                <strong>{group.title}</strong>
                <small>{group.description}</small>
              </div>
              <dl className="cadence-group-metrics">
                <div>
                  <dt>상태</dt>
                  <dd>
                    <span className={`risk-tag ${schedulerGroupTone(group)}`}>
                      {schedulerGroupStatusLabel(group)}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>예약</dt>
                  <dd>
                    {group.activeCount}/{group.timers.length}개 활성 · 성공 {group.successCount}개
                  </dd>
                </div>
                <div>
                  <dt>다음 실행</dt>
                  <dd>{schedulerGroupNextElapse(group)}</dd>
                </div>
              </dl>
              <div className="timer-chip-list" aria-label={`${group.title} 세부 예약`}>
                {group.timers.map((timer) => (
                  <div className="timer-chip" key={timer.profile_id}>
                    <b>{koCode(timer.profile_id)}</b>
                    <span>{timer.schedule || "스케줄 미확인"}</span>
                    <small>
                      {koCode(timer.active_state)} · {koCode(timer.last_result || "unknown")}
                    </small>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          아직 화면에 연결된 서버 예약 실행 스케줄이 없다. 수동 실행 결과와 실행 로그만 참고한다.
        </div>
      )}
    </section>
  );
}
