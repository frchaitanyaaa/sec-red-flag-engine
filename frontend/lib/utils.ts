export const asNumber = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const num = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(num) ? num : null;
};

export const asString = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  return String(value);
};

export const splitCsv = (value: unknown): string[] =>
  asString(value)
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

export const formatMoney = (value: unknown): string => {
  const num = asNumber(value);
  if (num === null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: Math.abs(num) >= 1_000_000_000 ? 'compact' : 'standard',
    maximumFractionDigits: 2
  }).format(num);
};

export const formatPercent = (value: unknown): string => {
  const num = asNumber(value);
  if (num === null) return '—';
  return `${(num * 100).toFixed(1)}%`;
};

export const formatNumber = (value: unknown): string => {
  const num = asNumber(value);
  if (num === null) return asString(value) || '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(num);
};

export const riskClasses = (risk: string): string => {
  const key = risk.toLowerCase();
  if (key === 'high') return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
  if (key === 'medium') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
  if (key === 'low') return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
  return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
};
