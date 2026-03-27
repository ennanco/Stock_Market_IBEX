"""Output and metadata persistence helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class OutputPaths:
    run_root: Path
    raw_dir: Path
    processed_dir: Path
    reports_dir: Path


def prepare_output_dirs(output_dir: Path, run_name: str) -> OutputPaths:
    run_root = output_dir / run_name
    raw_dir = run_root / "raw"
    processed_dir = run_root / "processed"
    reports_dir = run_root / "reports"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    return OutputPaths(
        run_root=run_root,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        reports_dir=reports_dir,
    )


def write_raw_csv(raw_dir: Path, symbol: str, history: pd.DataFrame) -> Path:
    output_path = raw_dir / f"{symbol}.csv"
    history.to_csv(output_path)
    return output_path


def write_prices_csv(processed_dir: Path, prices: pd.DataFrame) -> Path:
    output_path = processed_dir / "prices.csv"
    prices.to_csv(output_path)
    return output_path


def write_metrics_csv(reports_dir: Path, metrics: pd.DataFrame) -> Path:
    output_path = reports_dir / "metrics.csv"
    metrics.to_csv(output_path)
    return output_path


def write_metadata(run_root: Path, metadata: dict) -> Path:
    output_path = run_root / "metadata.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output_path
