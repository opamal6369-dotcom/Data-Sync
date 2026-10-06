"""Load and standardize CSV/Excel files from a folder."""
from pathlib import Path
import re

import pandas as pd

SUPPORTED = {".csv", ".xlsx", ".xls"}


def standardize_column(name: str) -> str:
    """'Order Date ' -> 'order_date'."""
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
    return name.strip("_")


def load_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names, trim text, parse dates, drop empty rows and duplicates."""
    df = df.copy()
    df.columns = [standardize_column(c) for c in df.columns]
    df = df.dropna(how="all")

    # Whole-number float columns (e.g. IDs read as 1001.0) become integers.
    for col in df.select_dtypes(include="float").columns:
        values = df[col].dropna()
        if len(values) and (values % 1 == 0).all():
            df[col] = df[col].astype("Int64")

    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype).startswith("str"):
            df[col] = df[col].astype("string").str.strip()
            if "date" in col:
                parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
                df[col] = parsed.dt.strftime("%Y-%m-%d")

    return df.drop_duplicates().reset_index(drop=True)


def load_folder(folder: str) -> pd.DataFrame:
    """Read every supported file in a folder and combine into one cleaned table."""
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    frames = []
    for path in sorted(folder_path.iterdir()):
        if path.suffix.lower() in SUPPORTED:
            frame = clean_frame(load_file(path))
            frame["source_file"] = path.name
            frames.append(frame)

    if not frames:
        raise ValueError(f"No CSV or Excel files found in {folder}")

    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(
        subset=[c for c in combined.columns if c != "source_file"]
    ).reset_index(drop=True)
