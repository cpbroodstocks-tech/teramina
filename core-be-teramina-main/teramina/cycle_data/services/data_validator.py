"""Pre-ingestion validation for cycle data uploads.

Produces a DataValidationReport before any data is persisted.
Hard failures block ingestion (return 400).
Warnings are surfaced in the 200 payload for operator review.
"""
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# Physiological bounds for Pacific white shrimp (Litopenaeus vannamei)
PHYSIOLOGICAL_BOUNDS = {
    "do": {
        "hard_min": 0,       # DO=0 crashes pipeline; biological death
        "warn_min": 3.0,     # hypoxia stress threshold
        "warn_max": 15.0,    # sensor saturation / aeration anomaly
        "hard_max": 20.0,    # physically impossible in pond water
    },
    "temperature": {
        "hard_min": 0,
        "warn_min": 22.0,    # cold stress
        "warn_max": 32.0,    # heat stress
        "hard_max": 45.0,    # physically impossible
    },
    "nh3": {
        "hard_min": -0.001,  # cannot be negative
        "warn_min": None,
        "warn_max": 1.0,     # acutely toxic
        "hard_max": 50.0,    # sensor error range
    },
    "abw": {
        "hard_min": 0,       # weight must be positive
        "warn_min": None,
        "warn_max": 60.0,    # unusually large for L. vannamei
        "hard_max": 200.0,   # impossible harvest weight
    },
}


@dataclass
class ValidationIssue:
    col: str
    doc: Any
    value: Any
    reason: str


@dataclass
class DataValidationReport:
    hard_failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def has_hard_failures(self) -> bool:
        return len(self.hard_failures) > 0

    def to_dict(self) -> dict:
        return {
            "hard_failures": [vars(i) for i in self.hard_failures],
            "warnings": [vars(i) for i in self.warnings],
        }


def validate_cycle_data(df: pd.DataFrame) -> DataValidationReport:
    """Run physiological bounds checks on cycle data.

    Args:
        df: dataframe after gap-completion and imputation, before pipeline

    Returns:
        DataValidationReport with hard_failures and warnings
    """
    report = DataValidationReport()
    doc_col = df["doc"] if "doc" in df.columns else df.index

    for col, bounds in PHYSIOLOGICAL_BOUNDS.items():
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce")

        # hard lower bound
        hard_min = bounds.get("hard_min")
        if hard_min is not None:
            mask = series <= hard_min
            for idx in df[mask].index:
                report.hard_failures.append(ValidationIssue(
                    col=col,
                    doc=int(doc_col.iloc[idx]) if hasattr(doc_col, "iloc") else idx,
                    value=float(series.iloc[idx]),
                    reason=f"{col} must be > {hard_min} (got {series.iloc[idx]:.4g})",
                ))

        # hard upper bound
        hard_max = bounds.get("hard_max")
        if hard_max is not None:
            mask = series >= hard_max
            for idx in df[mask].index:
                report.hard_failures.append(ValidationIssue(
                    col=col,
                    doc=int(doc_col.iloc[idx]) if hasattr(doc_col, "iloc") else idx,
                    value=float(series.iloc[idx]),
                    reason=f"{col} must be < {hard_max} (got {series.iloc[idx]:.4g})",
                ))

        # soft lower bound
        warn_min = bounds.get("warn_min")
        if warn_min is not None:
            # exclude rows already flagged as hard failures
            hard_min_val = hard_min if hard_min is not None else float("-inf")
            mask = (series > hard_min_val) & (series < warn_min)
            for idx in df[mask].index:
                report.warnings.append(ValidationIssue(
                    col=col,
                    doc=int(doc_col.iloc[idx]) if hasattr(doc_col, "iloc") else idx,
                    value=float(series.iloc[idx]),
                    reason=f"{col} below recommended minimum {warn_min} (got {series.iloc[idx]:.4g})",
                ))

        # soft upper bound
        warn_max = bounds.get("warn_max")
        if warn_max is not None:
            hard_max_val = hard_max if hard_max is not None else float("inf")
            mask = (series > warn_max) & (series < hard_max_val)
            for idx in df[mask].index:
                report.warnings.append(ValidationIssue(
                    col=col,
                    doc=int(doc_col.iloc[idx]) if hasattr(doc_col, "iloc") else idx,
                    value=float(series.iloc[idx]),
                    reason=f"{col} above recommended maximum {warn_max} (got {series.iloc[idx]:.4g})",
                ))

    return report
