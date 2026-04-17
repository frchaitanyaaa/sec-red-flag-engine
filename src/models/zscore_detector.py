import numpy as np
import pandas as pd


def zscore_series(series: pd.Series) -> pd.Series:
    """
    Compute z-scores for a numeric pandas Series.
    If standard deviation is 0 or missing, return zeros.
    """
    s = pd.to_numeric(series, errors="coerce")
    mean = s.mean()
    std = s.std(ddof=0)

    if pd.isna(std) or std == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)

    return (s - mean) / std


def add_zscore_flags(
    df: pd.DataFrame,
    columns: list[str],
    threshold: float = 2.0
) -> pd.DataFrame:
    """
    Add z-score columns and boolean flag columns for the selected metrics.
    """
    out = df.copy()

    for col in columns:
        z_col = f"{col}_zscore"
        flag_col = f"{col}_zflag"

        out[z_col] = zscore_series(out[col])
        out[flag_col] = out[z_col].abs() >= threshold

    return out
