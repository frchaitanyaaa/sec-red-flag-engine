'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { normalizeCombinedRows } from '@/lib/normalizers';
import { asNumber } from '@/lib/utils';
import { Card, RiskBadge, SectionTitle } from '@/components/ui';
import { RiskByYearChart } from '@/components/risk-chart';
import { YearDrilldown } from '@/components/year-drilldown';
import type { CombinedYear } from '@/types/api';

export default function CompanyOverviewPage({ params }: { params: { identifier: string } }) {
  const identifier = decodeURIComponent(params.identifier);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [company, setCompany] = useState<{ title: string; ticker: string; cik: string } | null>(null);
  const [combinedRows, setCombinedRows] = useState<CombinedYear[]>([]);
  const [focusRows, setFocusRows] = useState<CombinedYear[]>([]);
  const [annualRows, setAnnualRows] = useState<Record<string, unknown>[]>([]);
  const [beneishFeatures, setBeneishFeatures] = useState<Record<string, unknown>[]>([]);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const analysis = await api.runAnalysis(identifier, 0.15);
        const combined = normalizeCombinedRows(analysis.combined_risk_summary || []);
        const focus = normalizeCombinedRows(analysis.combined_focus_years || []);
        setCompany(analysis.company);
        setCombinedRows(combined);
        setFocusRows(focus);
        setSelectedYear(focus[0]?.fiscalYear ?? combined[combined.length - 1]?.fiscalYear ?? null);

        const [annual, beneish] = await Promise.all([api.annualFinancials(identifier), api.beneish(identifier)]);
        setAnnualRows(annual.rows || []);
        setBeneishFeatures(beneish.features || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analysis');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [identifier]);

  const selected = useMemo(() => combinedRows.find((row) => row.fiscalYear === selectedYear), [combinedRows, selectedYear]);
  const selectedAnnual = annualRows.find((row) => asNumber(row.fiscal_year) === selectedYear);
  const selectedBeneish = beneishFeatures.find((row) => asNumber(row.fiscal_year) === selectedYear);

  const quickStats = useMemo(() => {
    const yearsAnalyzed = combinedRows.length;
    const triggeredYears = combinedRows.filter((row) => row.triggeredMethodCount > 0).length;
    const top = [...combinedRows].sort((a, b) => b.triggeredMethodCount - a.triggeredMethodCount || a.fiscalYear - b.fiscalYear)[0];
    const beneishAny = combinedRows.some((row) => row.beneishFlag);
    return { yearsAnalyzed, triggeredYears, top, beneishAny };
  }, [combinedRows]);

  return (
    <div className="space-y-6">
      <SectionTitle
        title={company ? `${company.title} (${company.ticker})` : `Company Overview: ${identifier}`}
        subtitle={company ? `CIK ${company.cik}` : 'Running analysis and loading company profile...'}
      />

      <div className="flex flex-wrap gap-3">
        <Link href={`/company/${identifier}/financials`} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200">
          Annual Financials
        </Link>
        <Link href={`/company/${identifier}/insights`} className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200">
          Method Insights
        </Link>
      </div>

      {loading && <Card>Running full analysis and loading data…</Card>}
      {error && <Card className="text-rose-300">{error}</Card>}

      {!loading && !error && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card><p className="text-xs text-slate-400">Years analyzed</p><p className="mt-1 text-2xl font-semibold">{quickStats.yearsAnalyzed}</p></Card>
            <Card><p className="text-xs text-slate-400">Triggered years</p><p className="mt-1 text-2xl font-semibold">{quickStats.triggeredYears}</p></Card>
            <Card><p className="text-xs text-slate-400">Top focus year</p><p className="mt-1 text-2xl font-semibold">{quickStats.top?.fiscalYear ?? '—'}</p></Card>
            <Card><p className="text-xs text-slate-400">Beneish flagged any year</p><p className="mt-1 text-2xl font-semibold">{quickStats.beneishAny ? 'Yes' : 'No'}</p></Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              <Card>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Focus Years</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(focusRows.length ? focusRows : combinedRows).map((row) => (
                    <button
                      key={row.fiscalYear}
                      onClick={() => setSelectedYear(row.fiscalYear)}
                      className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm hover:border-slate-500"
                    >
                      {row.fiscalYear} <span className="text-slate-400">({row.triggeredMethodCount} method{row.triggeredMethodCount === 1 ? '' : 's'})</span>
                    </button>
                  ))}
                </div>
              </Card>

              {selected && <YearDrilldown year={selected} financialRow={selectedAnnual} beneishFeature={selectedBeneish} />}
            </div>

            <RiskByYearChart rows={combinedRows} onYearClick={(year) => setSelectedYear(year)} />
          </div>

          <Card>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Combined Risk Summary</h3>
            <div className="mt-4 overflow-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-xs uppercase text-slate-500">
                    <th className="px-2 py-2">Year</th><th className="px-2 py-2">Risk</th><th className="px-2 py-2">Methods Triggered</th><th className="px-2 py-2">Method Count</th>
                  </tr>
                </thead>
                <tbody>
                  {combinedRows.map((row) => (
                    <tr key={row.fiscalYear} className="border-b border-slate-900">
                      <td className="px-2 py-2">{row.fiscalYear}</td>
                      <td className="px-2 py-2"><RiskBadge risk={row.combinedRiskLevel} /></td>
                      <td className="px-2 py-2">{row.triggeredMethods.join(', ') || 'none'}</td>
                      <td className="px-2 py-2">{row.triggeredMethodCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
