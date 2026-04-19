'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useEffect } from 'react';
import { api } from '@/lib/api';
import { asNumber, formatMoney, formatNumber } from '@/lib/utils';
import { Card, SectionTitle } from '@/components/ui';

export default function AnnualFinancialsPage({ params }: { params: { identifier: string } }) {
  const identifier = decodeURIComponent(params.identifier);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortKey, setSortKey] = useState('fiscal_year');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await api.annualFinancials(identifier);
        setRows(data.rows || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load annual financials');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [identifier]);

  const columns = useMemo(() => Array.from(new Set(rows.flatMap((row) => Object.keys(row)))), [rows]);

  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const an = asNumber(av);
      const bn = asNumber(bv);
      if (an !== null && bn !== null) return sortDir === 'asc' ? an - bn : bn - an;
      const as = String(av ?? '');
      const bs = String(bv ?? '');
      return sortDir === 'asc' ? as.localeCompare(bs) : bs.localeCompare(as);
    });
  }, [rows, sortKey, sortDir]);

  const renderCell = (key: string, value: unknown) => {
    if (key.includes('ratio') || key.includes('_yoy') || key.includes('margin')) return formatNumber(value);
    if (typeof value === 'number' && Math.abs(value) >= 1000) return formatMoney(value);
    return formatNumber(value);
  };

  const toggleSort = (key: string) => {
    if (sortKey === key) setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  return (
    <div className="space-y-5">
      <SectionTitle title={`Annual Financials: ${identifier}`} subtitle="Sortable annual row view suitable for export and audit review." />
      <Link href={`/company/${identifier}`} className="text-sm text-sky-300">← Back to overview</Link>

      {loading && <Card>Loading annual financials…</Card>}
      {error && <Card className="text-rose-300">{error}</Card>}

      {!loading && !error && (
        <Card>
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase text-slate-500">
                  {columns.map((col) => (
                    <th key={col} className="px-2 py-2 text-left">
                      <button onClick={() => toggleSort(col)} className="hover:text-slate-200">
                        {col} {sortKey === col ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedRows.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-900">
                    {columns.map((col) => (
                      <td key={col} className="whitespace-nowrap px-2 py-2 text-slate-200">{renderCell(col, row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
