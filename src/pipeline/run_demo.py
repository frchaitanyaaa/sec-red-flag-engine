import pandas as pd
from src.models.zscore_detector import add_zscore_flags


def main() -> None:
    df = pd.DataFrame(
        {
            "year": [2020, 2021, 2022, 2023, 2024],
            "revenue": [100, 108, 112, 115, 210],
            "receivables": [12, 13, 12, 14, 40],
            "total_assets": [150, 155, 160, 165, 220],
        }
    )

    result = add_zscore_flags(
        df=df,
        columns=["revenue", "receivables", "total_assets"],
        threshold=1.5,
    )

    print(result)


if __name__ == "__main__":
    main()
