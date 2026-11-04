"""Strict validation and summary of the Lab04 real CI-run sample (Issue #77)."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

REQUIRED = (
    "run_id", "created_at", "run_url", "repository", "workflow_id",
    "workflow_name", "branch", "conclusion", "failed",
)
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("CI sample must contain at least one run")
    frame = df.copy()
    for column in REQUIRED:
        frame[column] = frame[column].astype("string").str.strip()
        if frame[column].isna().any() or frame[column].eq("").any():
            raise ValueError(f"Blank value in {column}")
    for column in ("run_id", "workflow_id"):
        if not frame[column].str.fullmatch(r"[1-9]\d*").all():
            raise ValueError(f"{column} must be a positive integer")
        frame[column] = frame[column].astype("int64")
    if frame["run_id"].duplicated().any():
        raise ValueError("Duplicate run_id")
    if not frame["created_at"].str.fullmatch(UTC_TIMESTAMP).all():
        raise ValueError("created_at must be UTC ISO 8601 with seconds")
    dates = pd.to_datetime(frame["created_at"], format="%Y-%m-%dT%H:%M:%SZ", utc=True, errors="coerce")
    if dates.isna().any():
        raise ValueError("Invalid created_at")
    if frame["repository"].nunique() != 1 or not frame["repository"].str.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+").all():
        raise ValueError("Sample must contain one valid repository")
    for column in ("workflow_id", "workflow_name", "branch"):
        if frame[column].nunique() != 1:
            raise ValueError(f"Sample must contain one {column}")
    if not frame["conclusion"].isin(["success", "failure"]).all():
        raise ValueError("Only completed success/failure runs belong in the denominator")
    if not frame["failed"].isin(["0", "1"]).all():
        raise ValueError("failed must be 0 or 1")
    if (frame["failed"].eq("1") != frame["conclusion"].eq("failure")).any():
        raise ValueError("failed indicator disagrees with conclusion")
    frame["failed"] = frame["failed"].astype("int8")
    for row in frame.itertuples(index=False):
        parsed = urlparse(row.run_url)
        expected = f"/{row.repository}/actions/runs/{row.run_id}"
        if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.path != expected or parsed.query or parsed.fragment:
            raise ValueError(f"Invalid run_url for run_id {row.run_id}")
    return frame


def load_ci_runs(path: str | Path) -> pd.DataFrame:
    """Load and validate a single-workflow CSV; reject malformed/duplicate rows."""
    try:
        raw = pd.read_csv(path, dtype="string", keep_default_na=False)
    except (OSError, pd.errors.ParserError) as exc:
        raise ValueError(f"Cannot read CI CSV: {exc}") from exc
    return _validate(raw)


def summarize_ci_runs(df: pd.DataFrame) -> dict:
    """Return n, failures k and the observed proportion k/n."""
    valid = _validate(df)
    n = len(valid)
    k = int(valid["failed"].sum())
    return {"n": n, "k": k, "p_hat": k / n}
