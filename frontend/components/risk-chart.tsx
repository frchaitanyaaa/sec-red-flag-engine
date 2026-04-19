import { RiskBadge } from './ui';
import type { CombinedYear } from '@/types/api';

const levelScore: Record<string, number> = { none: 0, low: 1, medium: 2, high: 3 };

export function RiskByYearChart({ rows, onYearClick }: { rows: CombinedYear[]; onYearClick: (year: number) => void }) {
  const max = 3;
  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">Combined Risk by Year</h3>
      <div className="mt-4 grid gap-3">
        {rows.map((row) => {
          const score = levelScore[row.combinedRiskLevel] ?? 0;
          const width = `${(score / max) * 100}%`;
          return (
            <button key={row.fiscalYear} onClick={() => onYearClick(row.fiscalYear)} className="text-left">
              <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                <span>{row.fiscalYear}</span>
                <RiskBadge risk={row.combinedRiskLevel} />
              </div>
              <div className="h-2 rounded-full bg-slate-800">
                <div className="h-2 rounded-full bg-gradient-to-r from-sky-500 via-amber-400 to-rose-500" style={{ width }} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
