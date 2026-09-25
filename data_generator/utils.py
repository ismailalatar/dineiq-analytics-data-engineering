from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DATE_FMT = "%Y-%m-%d"


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def weighted_choice(generator: np.random.Generator, values: Iterable, weights, size=None):
    values = np.asarray(list(values))
    weights = np.asarray(weights, dtype=float)
    weights = np.clip(weights, 0, None)
    if weights.sum() <= 0:
        weights = np.ones_like(weights, dtype=float)
    weights = weights / weights.sum()
    return generator.choice(values, size=size, p=weights)


def normalize_probabilities(weights) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    weights = np.clip(weights, 0, None)
    total = weights.sum()
    return weights / total if total > 0 else np.full_like(weights, 1 / len(weights))


def ensure_min_rows(df: pd.DataFrame, n: int, generator: np.random.Generator) -> pd.DataFrame:
    """Upsample rows when a smoke configuration needs a minimum row count."""
    if len(df) >= n:
        return df
    extra = df.iloc[generator.integers(0, len(df), size=n - len(df))].copy()
    return pd.concat([df, extra], ignore_index=True)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, date_format=DATE_FMT)


def save_optional_parquet(df: pd.DataFrame, path: Path) -> bool:
    """Write Parquet when an engine is installed; otherwise return False."""
    try:
        df = df.copy()
        df.attrs ={}
        
        df.to_parquet(path,index=False)
        return True
    except (ImportError, ValueError):
        return False


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def choose_without_replacement(generator: np.random.Generator, items, n: int, weights=None):
    """Weighted sampling without replacement with a robust fallback."""
    items = np.asarray(items)
    n = min(int(n), len(items))
    if n <= 0:
        return np.array([], dtype=items.dtype)
    if weights is None:
        return generator.choice(items, size=n, replace=False)
    w = np.asarray(weights, dtype=float)
    w = np.clip(w, 1e-12, None)
    p = w / w.sum()
    try:
        return generator.choice(items, size=n, replace=False, p=p)
    except ValueError:
        return generator.choice(items, size=n, replace=False)
