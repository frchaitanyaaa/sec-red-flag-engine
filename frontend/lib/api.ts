import type {
  AnalyzeResponse,
  AnnualFinancialsResponse,
  BeneishResponse,
  CombinedRiskResponse,
  CompanySearchItem
} from '@/types/api';

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!baseUrl) {
  // eslint-disable-next-line no-console
  console.warn('NEXT_PUBLIC_API_BASE_URL is not set. API calls will fail until configured.');
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {})
    },
    cache: 'no-store'
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const parsed = (await response.json()) as { detail?: string };
      detail = parsed.detail || detail;
    } catch {
      // keep fallback detail
    }
    throw new Error(detail || 'Request failed');
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<{ status: string }>('/health'),
  searchCompanies: (q: string) => apiFetch<{ results: CompanySearchItem[] }>(`/companies/search?q=${encodeURIComponent(q)}`),
  runAnalysis: (identifier: string, contamination = 0.15) =>
    apiFetch<AnalyzeResponse>('/analysis/run', {
      method: 'POST',
      body: JSON.stringify({ identifier, contamination })
    }),
  annualFinancials: (identifier: string) =>
    apiFetch<AnnualFinancialsResponse>(`/companies/${encodeURIComponent(identifier)}/annual-financials`),
  beneish: (identifier: string) => apiFetch<BeneishResponse>(`/companies/${encodeURIComponent(identifier)}/beneish`),
  combinedRisk: (identifier: string, contamination = 0.15) =>
    apiFetch<CombinedRiskResponse>(`/companies/${encodeURIComponent(identifier)}/combined-risk?contamination=${contamination}`)
};
