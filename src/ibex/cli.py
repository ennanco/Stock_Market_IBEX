"""CLI entrypoint for IBEX data download and analysis."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from ibex.config import DEFAULT_BENCHMARK, DEFAULT_SYMBOLS
from ibex.data_fetch import download_history, extract_adjusted_close
from ibex.io import (
    prepare_output_dirs,
    write_metadata,
    write_metrics_csv,
    write_prices_csv,
    write_raw_csv,
)
from ibex.metrics import compute_metrics
from ibex.processing import build_prices_frame, compute_daily_returns


def _parse_date(raw_date: str, field_name: str) -> pd.Timestamp:
    try:
        return pd.Timestamp(raw_date).normalize()
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            f"invalid {field_name} date '{raw_date}', expected YYYY-MM-DD"
        ) from exc


def _parse_symbols(raw_symbols: str | None) -> list[str]:
    if not raw_symbols:
        return list(DEFAULT_SYMBOLS)

    symbols = [
        token.strip().upper() for token in raw_symbols.split(",") if token.strip()
    ]
    if not symbols:
        raise argparse.ArgumentTypeError("--symbols must contain at least one symbol")

    unique_symbols = list(dict.fromkeys(symbols))
    return unique_symbols


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ibex-analyze",
        description="Download IBEX prices with yfinance and compute basic risk/return metrics.",
    )
    parser.add_argument(
        "--start", required=True, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated list of symbols (default: built-in IBEX universe)",
    )
    parser.add_argument(
        "--benchmark",
        default=DEFAULT_BENCHMARK,
        help=f"Benchmark symbol used for Beta/Alpha (default: {DEFAULT_BENCHMARK})",
    )
    parser.add_argument(
        "--output-dir", default="output", help="Directory where run outputs are stored"
    )
    parser.add_argument("--run-name", default=None, help="Optional run folder name")
    parser.add_argument(
        "--skip-raw", action="store_true", help="Do not write per-symbol raw CSV files"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    start_date = _parse_date(args.start, "start")
    end_date = _parse_date(args.end, "end")
    if start_date > end_date:
        parser.error("--start must be less than or equal to --end")

    benchmark = args.benchmark.strip().upper()
    symbols = _parse_symbols(args.symbols)
    symbols = [symbol for symbol in symbols if symbol != benchmark]
    symbols_with_benchmark = [benchmark] + symbols

    run_name = args.run_name or f"{start_date.date()}_{end_date.date()}"
    output_paths = prepare_output_dirs(Path(args.output_dir), run_name)

    price_series: dict[str, pd.Series] = {}
    failures: dict[str, str] = {}
    downloaded_symbols: list[str] = []

    for symbol in symbols_with_benchmark:
        result = download_history(
            symbol=symbol, start_date=start_date, end_date=end_date
        )
        if not result.ok:
            failures[symbol] = result.error or "unknown error"
            continue

        try:
            price_series[symbol] = extract_adjusted_close(result.history, symbol)
        except ValueError as exc:
            failures[symbol] = str(exc)
            continue

        downloaded_symbols.append(symbol)
        if not args.skip_raw:
            write_raw_csv(output_paths.raw_dir, symbol, result.history)

    if benchmark not in price_series:
        print(
            f"error: benchmark '{benchmark}' could not be downloaded", file=sys.stderr
        )
        for symbol, reason in failures.items():
            print(f" - {symbol}: {reason}", file=sys.stderr)
        return 1

    prices = build_prices_frame(price_series=price_series, benchmark=benchmark)
    daily_returns = compute_daily_returns(prices)
    metrics = compute_metrics(
        prices=prices, daily_returns=daily_returns, benchmark=benchmark
    )

    prices_path = write_prices_csv(output_paths.processed_dir, prices)
    metrics_path = write_metrics_csv(output_paths.reports_dir, metrics)

    metadata = {
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "start_date": str(start_date.date()),
        "end_date": str(end_date.date()),
        "benchmark": benchmark,
        "requested_symbols": symbols_with_benchmark,
        "downloaded_symbols": downloaded_symbols,
        "failed_symbols": failures,
        "paths": {
            "run_root": str(output_paths.run_root),
            "raw_dir": str(output_paths.raw_dir),
            "prices_csv": str(prices_path),
            "metrics_csv": str(metrics_path),
        },
    }
    metadata_path = write_metadata(output_paths.run_root, metadata)

    print(f"Run written to: {output_paths.run_root}")
    print(f"Prices: {prices_path}")
    print(f"Metrics: {metrics_path}")
    print(f"Metadata: {metadata_path}")
    if failures:
        print("Symbols with download issues:")
        for symbol, reason in failures.items():
            print(f" - {symbol}: {reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
