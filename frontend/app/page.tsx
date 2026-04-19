import { SearchPanel } from '@/components/search-panel';

export default function HomePage() {
  return (
    <div className="space-y-6">
      <SearchPanel />
      <section className="grid gap-4 md:grid-cols-3">
        {[
          ['Global Z-score', 'Flags unusually large deviations in key growth and ratio signals.'],
          ['Beneish M-score', 'Uses accounting indicators that may signal earnings manipulation risk patterns.'],
          ['Isolation Forest', 'Machine-learning outlier detection over annual engineered features.']
        ].map(([title, text]) => (
          <div key={title} className="card p-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">{title}</h3>
            <p className="mt-2 text-sm text-slate-400">{text}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
