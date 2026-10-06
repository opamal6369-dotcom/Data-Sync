# DataSync

A Python command-line tool that cleans messy CSV/Excel files, syncs them into a database, and generates summary reports with charts. It only writes rows that are new or changed, so repeated runs stay fast and safe.

## What it does

- **Cleans data:** standardizes column names, trims whitespace, normalizes mixed date formats, drops empty rows and duplicates, and combines multiple files into one table.
- **Syncs to a database:** stores rows in SQLite keyed by a column you choose, and reports how many rows were inserted, updated, or unchanged.
- **Reports:** writes a text summary and Matplotlib charts (numeric distributions, category counts).
- **Optional Google Sheets sync:** pushes the synced data to a Google Sheet via the Sheets API.
- **Export:** dumps the database back to CSV.

## Setup

```bash
pip install -r requirements.txt
```

Python 3.10+ required.

## Usage

```bash
# Clean every CSV/Excel file in a folder and sync it into datasync.db
python -m datasync sync sample_data --key order_id

# Same, plus generate a report and charts in ./reports
python -m datasync sync sample_data --key order_id --report

# Re-run: unchanged rows are skipped
python -m datasync sync sample_data --key order_id

# Report from existing database, or export to CSV
python -m datasync report
python -m datasync export --output export.csv
```

Example output:

```
Loaded 8 clean rows from sample_data
Sync result: 8 inserted, 0 updated, 0 unchanged
```

### Google Sheets (optional)

1. `pip install gspread`
2. Create a Google Cloud service account, download its JSON key as `service_account.json`, and share your sheet with the service account's email.
3. Run: `python -m datasync sync sample_data --key order_id --sheet "My Sheet Name"`

Never commit `service_account.json`; it is already in `.gitignore`.

## Project layout

```
datasync/
  cleaner.py   load + standardize files
  db.py        SQLite storage and change detection (row hashing)
  report.py    text summary and charts
  sheets.py    optional Google Sheets sync
  cli.py       command-line interface
tests/         pytest tests
sample_data/   example input files
```

## Tests

```bash
pip install pytest
python -m pytest
```
