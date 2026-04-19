'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { normalizeCombinedRows } from '@/lib/normalizers';
import { Card, RiskBadge, SectionTitle } from '@/components/ui';

export default function MethodInsightsPage({ params }: { params: { identifier: string } }) {
  const identifier = decodeURIComponent(params.identifier);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rows, setRows] = useState<ReturnType<typeof normalizeCombinedRows>>([]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const combined = await api.combinedRisk(identifier, 0.15);
        setRows(normalizeCombinedRows(combined.summary || []));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load method insights');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [identifier]);

  const methodOverview = useMemo(() => {
    const zYears = rows.filter((r) => r.triggeredMethods.includes('global_zscore')).map((r) => r.fiscalYear);
    const bYears = rows.filter((r) => r.triggeredMethods.includes('beneish')).map((r) => r.fiscalYear);
    const iYears = rows.filter((r) => r.triggeredMethods.includes('isolation_forest')).map((r) => r.fiscalYear);
    return { zYears, bYears, iYears };
  }, [rows]);

  return (
    <div className="space-y-5">
      <SectionTitle title={`Method Insights: ${identifier}`} subtitle="How each method contributed to combined year-level risk signals." />
      <Link href={`/company/${identifier}`} className="text-sm text-sky-300">← Back to overview</Link>

      {loading && <Card>Loading method insights…</Card>}
      {error && <Card className="text-rose-300">{error}</Card>}

      {!loading && !error && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <h3 className="text-sm font-semibold text-white">Global Z-score</h3>
              <p className="mt-2 text-sm text-slate-400">Triggered years: {methodOverview.zYears.join(', ') || 'none'}</p>
            </Card>
            <Card>
              <h3 className="text-sm font-semibold text-white">Beneish M-score</h3>
              <p className="mt-2 text-sm text-slate-400">Triggered years: {methodOverview.bYears.join(', ') || 'none'}</p>
            </Card>
            <Card>
              <h3 className="text-sm font-semibold text-white">Isolation Forest</h3>
              <p className="mt-2 text-sm text-slate-400">Triggered years: {methodOverview.iYears.join(', ') || 'none'}</p>
            </Card>
          </div>

          <Card>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Year-by-Year Trigger Matrix</h3>
            <div className="mt-4 overflow-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-xs uppercase text-slate-500">
                    <th className="px-2 py-2">Year</th>
                    <th className="px-2 py-2">Combined Risk</th>
                    <th className="px-2 py-2">Global Z-score</th>
                    <th className="px-2 py-2">Beneish</th>
                    <th className="px-2 py-2">Isolation Forest</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.fiscalYear} className="border-b border-slate-900">
                      <td className="px-2 py-2">{row.fiscalYear}</td>
                      <td className="px-2 py-2"><RiskBadge risk={row.combinedRiskLevel} /></td>
                      <td className="px-2 py-2">{row.triggeredMethods.includes('global_zscore') ? 'triggered' : 'no signal'}</td>
                      <td className="px-2 py-2">{row.triggeredMethods.includes('beneish') ? 'triggered' : 'no signal'}</td>
                      <td className="px-2 py-2">{row.triggeredMethods.includes('isolation_forest') ? 'triggered' : 'no signal'}</td>
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
