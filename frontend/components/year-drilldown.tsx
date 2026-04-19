import type { CombinedYear } from '@/types/api';
import { formatMoney, formatNumber } from '@/lib/utils';
import { Card, RiskBadge } from './ui';

export function YearDrilldown({
  year,
  financialRow,
  beneishFeature
}: {
  year: CombinedYear;
  financialRow?: Record<string, unknown>;
  beneishFeature?: Record<string, unknown>;
}) {
  const metrics = ['revenue', 'net_income', 'cfo', 'total_assets', 'total_liabilities'];

  return (
    <Card>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Year Detail: {year.fiscalYear}</h3>
        <RiskBadge risk={year.combinedRiskLevel} />
      </div>
      <p className="mt-2 text-sm text-slate-400">
        Triggered methods: {year.triggeredMethods.length ? year.triggeredMethods.join(', ') : 'none'}
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map((key) => (
          <div key={key} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">{key.replace('_', ' ')}</p>
            <p className="mt-1 text-sm text-slate-100">{formatMoney(financialRow?.[key])}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Beneish M-Score</p>
          <p className="mt-1 text-sm text-slate-100">{formatNumber(beneishFeature?.beneish_mscore ?? year.beneishMScore)}</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Method Trigger Count</p>
          <p className="mt-1 text-sm text-slate-100">{year.triggeredMethodCount}</p>
        </div>
      </div>
    </Card>
  );
}
