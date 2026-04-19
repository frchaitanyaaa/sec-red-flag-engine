export type CompanyInfo = {
  ticker: string;
  cik: string;
  title: string;
};

export type CompanySearchItem = {
  name: string;
  ticker: string;
  cik: string;
};

export type AnalyzeResponse = {
  company: CompanyInfo;
  storage_key: string;
  combined_focus_years: Record<string, unknown>[];
  combined_risk_summary: Record<string, unknown>[];
};

export type AnnualFinancialsResponse = {
  company: CompanyInfo;
  storage_key: string;
  rows: Record<string, unknown>[];
};

export type BeneishResponse = {
  company: CompanyInfo;
  storage_key: string;
  summary: Record<string, unknown>[];
  features: Record<string, unknown>[];
};

export type CombinedRiskResponse = {
  company: CompanyInfo;
  storage_key: string;
  summary: Record<string, unknown>[];
  focus_years: Record<string, unknown>[];
};

export type CombinedYear = {
  fiscalYear: number;
  combinedRiskLevel: string;
  triggeredMethods: string[];
  triggeredMethodCount: number;
  zscoreRiskLevel?: string;
  zscoreFeatures?: string[];
  beneishFlag?: boolean;
  beneishMScore?: number | null;
  ifFlag?: boolean;
  raw: Record<string, unknown>;
};
