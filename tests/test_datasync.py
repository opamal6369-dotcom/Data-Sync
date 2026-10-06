import pandas as pd

from datasync import cleaner, db


def test_standardize_column():
    assert cleaner.standardize_column(" Order Date ") == "order_date"
    assert cleaner.standardize_column("Amount ($)") == "amount"


def test_clean_frame_removes_duplicates_and_empty_rows():
    df = pd.DataFrame({"Name ": [" a ", " a ", None], "Order Date": ["01/05/2026", "01/05/2026", None]})
    out = cleaner.clean_frame(df)
    assert list(out.columns) == ["name", "order_date"]
    assert len(out) == 1
    assert out.loc[0, "name"] == "a"
    assert out.loc[0, "order_date"] == "2026-01-05"


def test_load_folder_combines_files():
    df = cleaner.load_folder("sample_data")
    assert len(df) == 8
    assert "source_file" in df.columns


def test_sync_detects_inserts_updates_unchanged(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    df = pd.DataFrame({"id": [1, 2], "v": ["a", "b"]})
    assert db.sync_frame(conn, df, "id") == {"inserted": 2, "updated": 0, "unchanged": 0}
    assert db.sync_frame(conn, df, "id") == {"inserted": 0, "updated": 0, "unchanged": 2}
    df.loc[1, "v"] = "changed"
    df.loc[len(df)] = [3, "c"]
    assert db.sync_frame(conn, df, "id") == {"inserted": 1, "updated": 1, "unchanged": 1}
