import { koCode } from '@/lib/korean-labels';
import { ratioText, scoreText, newsHref, type ThemeData } from '@/lib/news-theme-model';
import { NewsRecord, SignalLink } from './SignalShared';
import { ThemeCompanies } from './ThemeCompanies';
import { ThemeDateForm } from './SignalControls';
import styles from './SignalWorkspace.module.css';

export function ThemeWorkspace({ data, date, today }: { data: ThemeData; date: string; today: string }) {
  const duplicates = new Set(data.history?.filter((item, index, items) => item.date && items.findIndex(other => other.date === item.date) !== index).map(item => item.date));
  return <div className={styles.page} data-testid="theme-workspace">
    <header className={styles.header}><div><span className={styles.eyebrow}>THEME REVIEW · {data.key}</span><h1>{koCode(data.name)}</h1><p>테마의 해석을 연결 기업과 실제 뉴스에 대조하세요.</p></div><ThemeDateForm date={date} today={today} /></header>
    <nav className={styles.chapters} aria-label="테마 검토 목차"><a href="#theme-companies">연결 기업</a><a href="#theme-history">사이클 기록</a><a href="#theme-news">관련 뉴스</a><a href="#theme-features">모델 특징</a></nav>
    <p className={styles.context}>요청 기준일 {date} · API 반환 기준 {data.asOf ?? '미확인'} · {koCode(data.strategy)} / {koCode(data.horizon)}</p>
    <div className={styles.phase}><div><span>원천 보고 상태</span><strong>{data.state ? koCode(data.state) : '미확인'}</strong></div><div><span>원천의 이전 상태</span><strong>{data.previous ? koCode(data.previous) : '미확인'}</strong></div><div><span>사이클 모델 점수</span><strong>{scoreText(data.score)}</strong></div></div>
    <div className={styles.themeLayout}><div className={styles.themeMain}>
      <section className={styles.section} id="theme-companies" aria-labelledby="theme-companies-title"><h2 id="theme-companies-title">다음으로 검토할 연결 기업</h2><ThemeCompanies companies={data.companies} /><p className={styles.note}>테마 연결은 매수 적합성이나 순위를 뜻하지 않습니다. 기업·투자 논리 상세는 각 경로의 반환 기준이며, 이 조회일 당시 상태를 완전히 재현한 것은 아닙니다.</p></section>
      <section className={styles.section} id="theme-history" aria-labelledby="theme-history-title"><h2 id="theme-history-title">저장된 사이클 관측</h2><p className={styles.note}>실제 반환된 기록만 표시합니다. 누락 구간을 메우거나 상태 차이를 새 전환 신호로 계산하지 않습니다.</p>
        <ol className={styles.history}>{data.history?.map((item, index) => <li key={index}><time dateTime={item.date ?? undefined}>{item.date ?? '기준일 미확인'}</time><strong>{item.state ? koCode(item.state) : '상태 미확인'}</strong><span>보고된 신뢰도 {ratioText(item.confidence)}</span>{item.date && duplicates.has(item.date) && <small className={styles.warning}>동일 기준일 기록 중복</small>}{item.date && item.date > date && <small className={styles.warning}>조회일 이후 기록</small>}</li>)}</ol>
        {!data.history?.length && <p className={styles.empty}>{data.history === null ? '사이클 이력 미제공' : '기록된 사이클 이력이 없습니다.'}</p>}
      </section>
      <section className={styles.panel} id="theme-news" aria-labelledby="theme-news-title"><div className={styles.panelHead}><h2 id="theme-news-title">테마와 연결된 뉴스·공시</h2><SignalLink href={newsHref({ date, theme: data.key, symbol: '', cursor: '' })}>이 테마의 뉴스 선별 →</SignalLink></div>
        {data.events?.map((item, index) => <NewsRecord key={`${item.id}-${index}`} item={item} date={date} />)}
        {!data.events?.length && <p className={styles.empty}>{data.events === null ? '관련 뉴스 자료 미제공' : '수신된 관련 뉴스 목록이 비어 있습니다.'}</p>}
      </section>
    </div><aside className={styles.themeAside}>
      <section className={styles.section} id="theme-features" aria-labelledby="theme-features-title"><h2 id="theme-features-title">모델에 들어간 특징</h2>
        {data.features.map(feature => <div className={styles.feature} key={feature.key}><div><span>{feature.name}</span><strong>{ratioText(feature.value)}</strong></div><div className={styles.track} aria-hidden="true">{feature.value !== null && <i style={{ width: `${feature.value * 100}%` }} />}</div></div>)}
        <p className={styles.note}>정규화된 모델 입력입니다. 0과 미측정은 다르며, 실제 가격 수익률로 해석하지 않습니다.</p>
        <dl className={styles.facts}><div><dt>현재 상태의 보고된 신뢰도</dt><dd>{ratioText(data.confidence)}</dd></div></dl>
      </section>
      <section className={styles.section}><h2>자료의 범위</h2><p className={styles.note}>조회일과 관측일은 다릅니다. API의 이력·기업·뉴스 목록은 일부 기록일 수 있고, 연결된 최신 투자 논리는 과거 조회일보다 나중에 작성됐을 수 있습니다.</p><details className={styles.disclosure}><summary>저장된 사용 안내</summary>{data.notes?.map((note, index) => <p key={index} className={styles.original}>{note}</p>)}{data.notes === null && <p>원천 안내 미제공</p>}</details><SignalLink href="/cycles">전체 테마 사이클 →</SignalLink></section>
    </aside></div>
  </div>;
}
