"""Data download functions using yfinance."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class DownloadResult:
    symbol: str
    history: pd.DataFrame
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.history.empty


def _inclusive_end_date(end_date: pd.Timestamp) -> pd.Timestamp:
    return end_date + pd.Timedelta(days=1)


def download_history(
    symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> DownloadResult:
    try:
        history = yf.download(
            tickers=symbol,
            start=start_date.strftime("%Y-%m-%d"),
            end=_inclusive_end_date(end_date).strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except (
        Exception
    ) as exc:  # pragma: no cover - defensive for network/runtime failures
        return DownloadResult(symbol=symbol, history=pd.DataFrame(), error=str(exc))

    if history.empty:
        return DownloadResult(symbol=symbol, history=history, error="empty response")

    history.index = pd.to_datetime(history.index).tz_localize(None)
    history.index.name = "Date"
    return DownloadResult(symbol=symbol, history=history)


def extract_adjusted_close(history: pd.DataFrame, symbol: str) -> pd.Series:
    column = "Adj Close"
    if column not in history.columns:
        raise ValueError(f"missing '{column}' for {symbol}")

    adjusted_close = history[column]
    if isinstance(adjusted_close, pd.DataFrame):
        if symbol in adjusted_close.columns:
            adjusted_close = adjusted_close[symbol]
        elif adjusted_close.shape[1] == 1:
            adjusted_close = adjusted_close.iloc[:, 0]
        else:
            raise ValueError(f"ambiguous '{column}' column for {symbol}")

    series = pd.to_numeric(adjusted_close, errors="coerce").rename(symbol)
    return series
