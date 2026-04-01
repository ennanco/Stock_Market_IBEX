# Stock Market IBEX

![Maintenance](https://img.shields.io/badge/maintained%3F-no-red.svg)

This project downloads historical market data from Yahoo Finance via `yfinance` and computes a basic risk/return report for IBEX symbols.

## What it does

- Downloads daily historical data for a benchmark and a list of symbols.
- Builds a consolidated adjusted-close price matrix.
- Computes metrics per symbol:
  - `Yearly`
  - `Daily Avg.`
  - `Daily Std.`
  - `Sharpe`
  - `Beta` (vs benchmark)
  - `Alpha` (vs benchmark)

## Setup with uv

```bash
uv sync
```

This creates/updates `.venv` and installs dependencies from `pyproject.toml`.

Run commands with uv (recommended):

```bash
uv run ibex-analyze --help
```

## Usage

```bash
uv run ibex-analyze --start 2024-01-01 --end 2024-12-31
```

Optional flags:

- `--symbols SAN.MC,BBVA.MC,ITX.MC`
- `--benchmark ^IBEX`
- `--output-dir output`
- `--run-name custom_run`
- `--skip-raw`

## Output structure

Every run is written to:

```text
output/<run_name>/
  raw/<SYMBOL>.csv
  processed/prices.csv
  reports/metrics.csv
  metadata.json
```

Legacy CSV outputs were removed from version control; generated datasets should live under `output/`.
