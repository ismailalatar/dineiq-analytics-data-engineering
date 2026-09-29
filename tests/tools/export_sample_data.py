"""Export small samples of every table into sample_data/ for the GitHub repository.

The full dataset lives on Google Drive, but SRS 1.10 item 3 asks for raw and cleaned
sample data in the repo.
Usage (from the repo root):  python tests/tools/export_sample_data.py [--rows 500]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.data_access import CLEAN_DIR, RAW_DIR, TABLES, read_table  # noqa: E402


def export(folder, formats, dest, rows):
    if not folder.is_dir():
        print(f"skip {folder} (not found)")
        return
    dest.mkdir(parents=True, exist_ok=True)
    print(f"{folder} -> {dest}")
    for table in TABLES:
        try:
            df = read_table(folder, table, formats, nrows=rows)
        except FileNotFoundError:
            print(f"  {table}: not found")
            continue
        df.to_csv(dest / f"{table}.csv", index=False)
        print(f"  {table}: {len(df)} rows")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=500)
    rows = parser.parse_args().rows
    export(RAW_DIR, ("csv",), ROOT / "sample_data" / "raw", rows)
    export(CLEAN_DIR, ("parquet", "csv"), ROOT / "sample_data" / "clean", rows)


if __name__ == "__main__":
    main()
