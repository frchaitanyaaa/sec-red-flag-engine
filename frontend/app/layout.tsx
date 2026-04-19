import './globals.css';
import Link from 'next/link';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'SEC Red Flag Dashboard',
  description: 'Analytics dashboard for SEC annual filing risk signals.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-800 bg-slate-900/70">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
              <Link href="/" className="text-sm font-semibold tracking-wide text-slate-100">
                SEC Red Flag Engine
              </Link>
              <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                Risk Signal Dashboard
              </span>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
