import clsx from 'clsx';
import type { ReactNode } from 'react';
import { riskClasses } from '@/lib/utils';

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
    </div>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx('card p-4', className)}>{children}</div>;
}

export function RiskBadge({ risk }: { risk: string }) {
  return (
    <span className={clsx('inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize', riskClasses(risk))}>
      {risk || 'none'}
    </span>
  );
}
