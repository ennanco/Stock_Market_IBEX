"""Financial metrics computation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_beta(daily_returns: pd.DataFrame, benchmark: str) -> pd.Series:
    benchmark_returns = daily_returns[benchmark]
    benchmark_variance = benchmark_returns.var()
    if benchmark_variance == 0 or np.isnan(benchmark_variance):
        return pd.Series(np.nan, index=daily_returns.columns, dtype="float64")

    beta_values = {
        symbol: daily_returns[symbol].cov(benchmark_returns) / benchmark_variance
        for symbol in daily_returns.columns
    }
    return pd.Series(beta_values, dtype="float64")


def compute_metrics(
    prices: pd.DataFrame, daily_returns: pd.DataFrame, benchmark: str
) -> pd.DataFrame:
    if prices.empty or daily_returns.empty:
        raise ValueError("prices and daily returns must contain data")

    results = pd.DataFrame(index=prices.columns)
    results["Yearly"] = ((prices.iloc[-1] / prices.iloc[0]) - 1.0) * 100.0
    results["Daily Avg."] = daily_returns.mean() * 100.0
    results["Daily Std."] = daily_returns.std() * 100.0
    results["Sharpe"] = (
        np.sqrt(len(daily_returns)) * results["Daily Avg."] / results["Daily Std."]
    )
    results["Beta"] = _compute_beta(daily_returns=daily_returns, benchmark=benchmark)
    results["Alpha"] = results["Daily Avg."] - (
        results["Beta"] * results.loc[benchmark, "Daily Avg."]
    )

    return results.replace([np.inf, -np.inf], np.nan)
