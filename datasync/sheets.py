"""Optional Google Sheets sync. Requires `pip install gspread` and a service account key."""
import pandas as pd


def push_to_sheet(df: pd.DataFrame, credentials_file: str, spreadsheet_name: str, worksheet: str = "DataSync"):
    try:
        import gspread
    except ImportError as exc:
        raise SystemExit("Google Sheets sync needs gspread: pip install gspread") from exc

    client = gspread.service_account(filename=credentials_file)
    sheet = client.open(spreadsheet_name)
    try:
        ws = sheet.worksheet(worksheet)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=worksheet, rows=len(df) + 1, cols=len(df.columns))

    clean = df.astype(object).where(df.notna(), "")
    ws.update([list(clean.columns)] + clean.astype(str).values.tolist())
    return len(df)


def pull_from_sheet(credentials_file: str, spreadsheet_name: str, worksheet: str = "DataSync") -> pd.DataFrame:
    try:
        import gspread
    except ImportError as exc:
        raise SystemExit("Google Sheets sync needs gspread: pip install gspread") from exc

    client = gspread.service_account(filename=credentials_file)
    ws = client.open(spreadsheet_name).worksheet(worksheet)
    return pd.DataFrame(ws.get_all_records())
