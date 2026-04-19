import type { CombinedYear } from '@/types/api';
import { asNumber, asString, splitCsv } from './utils';

export const normalizeCombinedRows = (rows: Record<string, unknown>[]): CombinedYear[] => {
  return rows
    .map((row) => {
      const fiscalYear = asNumber(row.fiscal_year);
      if (fiscalYear === null) return null;

      return {
        fiscalYear,
        combinedRiskLevel: asString(row.combined_risk_level || 'none'),
        triggeredMethods: splitCsv(row.triggered_methods),
        triggeredMethodCount: asNumber(row.triggered_method_count) ?? 0,
        zscoreRiskLevel: asString(row.zscore_risk_level),
        zscoreFeatures: splitCsv(row.zscore_features_triggered),
        beneishFlag: Boolean(row.beneish_flag),
        beneishMScore: asNumber(row.beneish_mscore),
        ifFlag: Boolean(row.if_flag),
        raw: row
      };
    })
    .filter((row): row is CombinedYear => row !== null)
    .sort((a, b) => a.fiscalYear - b.fiscalYear);
};
