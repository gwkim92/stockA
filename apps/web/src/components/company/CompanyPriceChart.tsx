'use client';
import { useState } from 'react';
import { currencyValue } from '@/lib/research-reader-model';
import type { PricePoint } from '@/lib/company-evidence-model';
import styles from './CompanyWorkspace.module.css';

export function CompanyPriceChart({ points, currency, excluded }: { points: PricePoint[] | null; currency: string | null; excluded: number | null }) {
  const [limit, setLimit] = useState(30);
  if (!points?.length) return <p className={styles.empty}>{points === null ? '가격 관측 목록 미제공' : '그릴 수 있는 날짜별 가격 기록이 없습니다.'}</p>;
  const visible = limit ? points.slice(-limit) : points;
  const measured = visible.filter((point): point is PricePoint & { close: number } => point.close !== null);
  const min = Math.min(...measured.map(point => point.close));
  const max = Math.max(...measured.map(point => point.close));
  const from = Date.parse(visible[0].date), to = Date.parse(visible[visible.length - 1].date);
  const x = (date: string) => 72 + (Date.parse(date) - from) / Math.max(to - from, 1) * 650;
  const y = (close: number) => max === min ? 110 : 30 + (max - close) / (max - min) * 160;
  let newSegment = true;
  const path = visible.map(point => {
    if (point.close === null) { newSegment = true; return ''; }
    const command = `${newSegment ? 'M' : 'L'}${x(point.date).toFixed(2)},${y(point.close).toFixed(2)}`;
    newSegment = false;
    return command;
  }).join(' ');
  return <div data-testid="company-price-chart">
    <div className={styles.chartControls} role="group" aria-label="가격 관측 범위">
      {[[30, '최근 30개 관측'], [90, '최근 90개 관측'], [0, '수신 전체']].map(([value, label]) => <button key={value} type="button" aria-pressed={limit === value} onClick={() => setLimit(Number(value))}>{label}</button>)}
    </div>
    {measured.length >= 2 ? <figure className={styles.priceFigure}>
      <svg viewBox="0 0 760 232" role="img" aria-label={`${visible[0].date}부터 ${visible[visible.length - 1].date}까지 저장된 종가. 유효한 가격 ${measured.length}개.`}>
        {[30, 110, 190].map(py => <line key={py} x1="72" y1={py} x2="722" y2={py} className={styles.gridLine} />)}
        <text x="8" y="35">{max.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}</text>
        <text x="8" y="195">{min.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}</text>
        <path d={path} className={styles.priceLine} />
        {measured.length <= 90 && measured.map(point => <circle key={point.date} cx={x(point.date)} cy={y(point.close)} r="3" className={styles.priceDot} />)}
        <text x="72" y="224">{visible[0].date}</text><text x="722" y="224" textAnchor="end">{visible[visible.length - 1].date}</text>
      </svg>
      <figcaption>저장된 종가 · {currency ?? '통화 미확인'} · {measured.length}/{visible.length}개 측정. 수신 구간만 표시하며 거래일 연속성을 보장하지 않습니다.</figcaption>
    </figure> : <p className={styles.empty}>차트를 그리기에 유효한 가격 관측이 부족합니다.</p>}
    <details className={styles.disclosure}><summary>가격 기록과 표시 기준</summary>
      <p>수정종가·실시간 시세가 아닌 저장된 종가입니다. 기업행동 조정이나 누락 거래일을 추정하지 않습니다. 날짜 오류·중복·기준일 이후 관측 제외: {excluded ?? '미확인'}개.</p>
      <div className={styles.tableScroll} role="region" aria-label="날짜별 종가 표" tabIndex={0}><table><caption>현재 선택 구간의 관측값</caption><thead><tr><th scope="col">관측일</th><th scope="col">종가</th></tr></thead><tbody>{visible.map(point => <tr key={point.date}><td>{point.date}</td><td>{currencyValue(point.close, currency)}</td></tr>)}</tbody></table></div>
    </details>
  </div>;
}
