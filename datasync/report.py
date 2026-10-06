"""Generate a text summary and charts from the synced data."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _numeric(df: pd.DataFrame) -> pd.DataFrame:
    converted = df.apply(pd.to_numeric, errors="coerce")
    converted = converted.loc[:, converted.notna().sum() > 0]
    # Skip ID-like columns: they are labels, not measurements.
    return converted.loc[:, [c for c in converted.columns if not c.endswith("id")]]


def build_report(df: pd.DataFrame, out_dir: str, sync_stats: dict | None = None) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = out / f"report_{stamp}.txt"

    lines = [f"DataSync report - {datetime.now():%Y-%m-%d %H:%M}", "=" * 40, f"Total rows: {len(df)}"]
    if sync_stats:
        lines.append("Last sync: " + ", ".join(f"{k}={v}" for k, v in sync_stats.items()))

    nums = _numeric(df)
    if not nums.empty:
        lines += ["", "Numeric summary:", nums.describe().round(2).to_string()]
        for col in nums.columns[:3]:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            nums[col].dropna().plot(kind="hist", bins=15, ax=ax, edgecolor="black")
            ax.set_title(f"Distribution of {col}")
            ax.set_xlabel(col)
            fig.tight_layout()
            fig.savefig(out / f"{col}_distribution_{stamp}.png", dpi=120)
            plt.close(fig)

    # Chart categorical columns only: skip IDs, dates, and columns where every value is unique.
    text_cols = [
        c for c in df.columns
        if c not in nums.columns
        and c != "source_file"
        and not c.endswith("id")
        and "date" not in c
        and df[c].nunique() <= len(df) / 2
    ]
    for col in text_cols[:2]:
        counts = df[col].value_counts().head(8)
        if 1 < len(counts) <= 8:
            lines += ["", f"Top values in '{col}':", counts.to_string()]
            fig, ax = plt.subplots(figsize=(6, 3.5))
            counts.plot(kind="bar", ax=ax)
            ax.set_title(f"Top values: {col}")
            fig.tight_layout()
            fig.savefig(out / f"{col}_counts_{stamp}.png", dpi=120)
            plt.close(fig)

    report_path.write_text("\n".join(lines) + "\n")
    return report_path
