import Link from 'next/link';
import type { Route } from 'next';
import type { ReactNode } from 'react';
import { koCode } from '@/lib/korean-labels';
import { recordHref, ratioText, scoreText, themeHref, type NewsItem } from '@/lib/news-theme-model';
import type { SignalIssue } from '@/lib/news-theme-data';
import styles from './SignalWorkspace.module.css';

export function SignalLink({ href, children }: { href: string | null; children: ReactNode }) {
  return href ? <Link className={styles.link} href={href as Route} prefetch={false}>{children}</Link> : null;
}
export function SignalError({ issue, home }: { issue: SignalIssue | null; home: string }) {
  const title = issue === 'query' ? '조회 조건을 확인해 주세요' : issue === 'timeout' ? '자료 응답이 지연되고 있습니다' : issue === 'invalid' ? '요청 조건과 반환 자료를 대조해야 합니다' : '자료를 불러오지 못했습니다';
  return <section className={styles.empty} role="status"><h2>{title}</h2><p>{issue === 'query' ? '유효한 날짜·종목·테마를 하나씩 입력하세요. 미래 날짜와 중복 조회 조건은 허용하지 않습니다.' : '조회 실패를 뉴스 0건이나 분석 완료로 표시하지 않습니다.'}</p><a className={styles.link} href="">다시 조회</a><SignalLink href={home}>조회 조건 초기화</SignalLink></section>;
}
export function NewsRecord({ item, date }: { item: NewsItem; date: string }) {
  const after = !!item.at && item.at.slice(0, 10) > date;
  return <article className={styles.newsRecord} data-restricted={item.restricted}>
    <div className={styles.recordMeta}>
      <time dateTime={item.at ?? undefined}>{item.at?.slice(0, 10) ?? '사건일 미확인'}</time>
      <span>{item.symbol ?? '종목 연결 미확인'}</span><span>{koCode(item.type)}</span>
      {item.restricted && <strong className={styles.warning}>추천 입력 차단·보류</strong>}
      {after && <strong className={styles.warning}>조회일 이후 기록</strong>}
    </div>
    <h3>{item.title}</h3>
    {item.summary && <p className={styles.summary}>{item.summary}</p>}
    <div className={styles.recordState}>
      <span>{item.evidence ? '해석 연결' : '해석 미연결'}</span>
      <span>{item.source ? '원천 연결' : '원천 미연결'}</span>
      <span>원천 판정: {koCode(item.gate)}</span>
    </div>
    <div className={styles.actions}>
      <SignalLink href={recordHref('source-documents', item.source)}>원천 문서 →</SignalLink>
      <SignalLink href={recordHref('ai-evidence', item.evidence)}>근거 해석 →</SignalLink>
      <SignalLink href={recordHref('stocks', item.symbol)}>기업 분석 →</SignalLink>
      <SignalLink href={themeHref(item.theme, date)}>테마 검토 →</SignalLink>
    </div>
    <details className={styles.disclosure}>
      <summary>원제·분류·연결 기록</summary>
      <p className={styles.original}>{item.originalTitle}</p>
      <dl className={styles.facts}>
        <div><dt>사건 시각 원기록</dt><dd>{item.at ?? '미기록'}</dd></div>
        <div><dt>분류된 테마</dt><dd>{item.theme ? item.themeName : '미분류'}</dd></div>
        <div><dt>해석 방향 / 영향 점수</dt><dd>{koCode(item.direction)} / {scoreText(item.score)}</dd></div>
        <div><dt>보고된 모델 신뢰도</dt><dd>{ratioText(item.confidence)}</dd></div>
        <div><dt>이벤트 식별자</dt><dd>{item.id}</dd></div>
      </dl>
      <p className={styles.note}>연결의 존재는 근거 승인이나 매수 신호가 아닙니다. 점수·신뢰도는 수익률 또는 성공 확률이 아닙니다.</p>
      {item.related?.map((related, index) => <div key={`${related.id}-${index}`} className={styles.related}><h4>{related.title}</h4><p>{koCode(related.relation)} · {related.reason}</p></div>)}
      {item.related === null && <p className={styles.note}>관련 이벤트 목록 미제공</p>}
    </details>
  </article>;
}
