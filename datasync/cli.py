"""Command-line interface: python -m datasync <command>."""
import argparse
import sys

from . import cleaner, db, report


def cmd_sync(args):
    df = cleaner.load_folder(args.folder)
    conn = db.connect(args.db)
    stats = db.sync_frame(conn, df, args.key)
    print(f"Loaded {len(df)} clean rows from {args.folder}")
    print(f"Sync result: {stats['inserted']} inserted, {stats['updated']} updated, {stats['unchanged']} unchanged")

    if args.sheet:
        from . import sheets
        n = sheets.push_to_sheet(db.read_frame(conn), args.credentials, args.sheet)
        print(f"Pushed {n} rows to Google Sheet '{args.sheet}'")

    if args.report:
        path = report.build_report(db.read_frame(conn), args.out, stats)
        print(f"Report written to {path}")
    conn.close()


def cmd_report(args):
    conn = db.connect(args.db)
    df = db.read_frame(conn)
    conn.close()
    if df.empty:
        sys.exit("Database is empty. Run `sync` first.")
    print(f"Report written to {report.build_report(df, args.out)}")


def cmd_export(args):
    conn = db.connect(args.db)
    df = db.read_frame(conn)
    conn.close()
    df.to_csv(args.output, index=False)
    print(f"Exported {len(df)} rows to {args.output}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="datasync", description="Clean, sync, and report on tabular data.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sync", help="Clean files in a folder and sync them into the database")
    s.add_argument("folder")
    s.add_argument("--key", required=True, help="Column that uniquely identifies a row")
    s.add_argument("--db", default="datasync.db")
    s.add_argument("--report", action="store_true", help="Also generate a report after syncing")
    s.add_argument("--out", default="reports")
    s.add_argument("--sheet", help="Optional Google Sheet name to push results to")
    s.add_argument("--credentials", default="service_account.json")
    s.set_defaults(func=cmd_sync)

    r = sub.add_parser("report", help="Generate a summary report and charts from the database")
    r.add_argument("--db", default="datasync.db")
    r.add_argument("--out", default="reports")
    r.set_defaults(func=cmd_report)

    e = sub.add_parser("export", help="Export the database to a CSV file")
    e.add_argument("--db", default="datasync.db")
    e.add_argument("--output", default="export.csv")
    e.set_defaults(func=cmd_export)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)
