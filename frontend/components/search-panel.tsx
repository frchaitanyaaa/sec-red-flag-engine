'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { CompanySearchItem } from '@/types/api';

export function SearchPanel() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<CompanySearchItem[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setError('');
    setLoading(true);
    try {
      const data = await api.searchCompanies(query.trim());
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-6">
      <h1 className="text-3xl font-semibold text-white">SEC Red Flag Analytics Dashboard</h1>
      <p className="mt-2 max-w-3xl text-sm text-slate-400">
        Search by company name, ticker, or CIK. Then run an integrated analysis to review combined risk, method triggers,
        and year-level focus signals.
      </p>

      <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={handleSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try AAPL, Apple, or 0000320193"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-200 placeholder:text-slate-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 disabled:opacity-60"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

      <div className="mt-5 space-y-2">
        {!loading && results.length === 0 ? <p className="text-sm text-slate-500">No companies selected yet.</p> : null}
        {results.map((item) => (
          <button
            key={`${item.cik}-${item.ticker}`}
            onClick={() => router.push(`/company/${item.ticker}`)}
            className="flex w-full items-center justify-between rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3 text-left hover:border-slate-600"
          >
            <div>
              <p className="font-medium text-slate-100">{item.name}</p>
              <p className="text-xs text-slate-400">{item.ticker} • {item.cik}</p>
            </div>
            <span className="text-xs text-sky-300">Run analysis</span>
          </button>
        ))}
      </div>
    </div>
  );
}
