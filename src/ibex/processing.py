"""Processing helpers for price series and returns."""

from __future__ import annotations

import pandas as pd


def build_prices_frame(
    price_series: dict[str, pd.Series], benchmark: str
) -> pd.DataFrame:
    if benchmark not in price_series:
        raise ValueError(f"benchmark '{benchmark}' is missing from downloaded data")

    frame = pd.concat(price_series.values(), axis=1)
    frame = frame.sort_index()
    frame = frame.loc[~frame.index.duplicated(keep="last")]
    frame = frame.apply(pd.to_numeric, errors="coerce")

    frame = frame.dropna(subset=[benchmark])
    asset_columns = [column for column in frame.columns if column != benchmark]
    if asset_columns:
        frame[asset_columns] = frame[asset_columns].ffill().bfill()

    return frame


def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    daily_returns = prices.pct_change()
    return daily_returns.dropna(how="any")
