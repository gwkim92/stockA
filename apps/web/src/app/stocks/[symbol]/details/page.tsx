import Link from 'next/link';
import type { Route } from 'next';
import { notFound } from 'next/navigation';
import { getStockDetail } from '@/lib/frontend-api';
import { stockSymbol } from '@/lib/company-evidence-model';
import { ReaderUnavailable } from '@/components/readers/ReaderFrame';
import { StockFinancialStatementModelPanel } from '../_components/StockFinancialStatementModelPanel';
import { StockFundInstrumentAnalysisPanel } from '../_components/StockFundInstrumentAnalysisPanel';
import { StockValuationResearchPanel } from '../_components/StockValuationResearchPanel';
import { StockIndustryCompetitivePositionPanel } from '../_components/StockIndustryCompetitivePositionPanel';
import { StockPriceAndMarketSections } from '../_components/StockPriceAndMarketSections';
import { StockProfessionalSourceGuardrailPanel } from '../_components/StockProfessionalSourceGuardrailPanel';
export const dynamic = 'force-dynamic';
export const metadata = { title: '기업 전문 분석 상세' };
export default async function AnalysisPage({ params }: { params: Promise<{ symbol: string }> }) {
  const symbol = stockSymbol((await params).symbol);
  if (!symbol) notFound();
  const { data } = await getStockDetail(symbol);
  if (data.symbol !== symbol) return <ReaderUnavailable issue="invalid" />;
  const fund = !!data.fund_instrument_analysis || data.professional_source_guardrail.status === 'fund_or_etf_company_model_not_applicable';
  const valuationItems = Object.entries(data.equity_research?.valuation_sensitivity ?? {}).filter(([, value]) => typeof value === 'string' || typeof value === 'number').map(([key, value]) => ({ key, value: String(value) }));
  return <div className="pageStack" data-testid="company-full-analysis">
    <header><Link href={`/stocks/${encodeURIComponent(symbol)}` as Route}>← 기업 리서치로 돌아가기</Link><h1>{symbol} 전문 분석</h1><p>기존 재무·가치평가·산업·가격 분석입니다. 각 분석의 기준일과 원천 제한을 함께 확인하세요.</p></header>
    <StockProfessionalSourceGuardrailPanel guardrail={data.professional_source_guardrail} symbol={symbol} />
    {fund ? <StockFundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} /> : <><StockFinancialStatementModelPanel model={data.financial_statement_model} symbol={symbol} /><StockValuationResearchPanel data={data} valuationItems={valuationItems} /><StockIndustryCompetitivePositionPanel position={data.industry_competitive_position} symbol={symbol} /></>}
    <StockPriceAndMarketSections data={data} latestChangePct={typeof data.latest_price.change_pct === 'number' && Number.isFinite(data.latest_price.change_pct) ? data.latest_price.change_pct : null} />
  </div>;
}
