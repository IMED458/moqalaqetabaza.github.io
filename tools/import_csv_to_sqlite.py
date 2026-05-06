#!/usr/bin/env python3
import argparse
import csv
import sqlite3
from pathlib import Path


def q(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def sniff_dialect(sample):
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def import_csv(csv_path, sqlite_path, limit=0):
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        sample = source.read(65536)
        source.seek(0)
        reader = csv.DictReader(source, dialect=sniff_dialect(sample))
        if not reader.fieldnames:
            raise SystemExit("CSV headers were not found.")

        columns = [column.strip() or f"field_{index + 1}" for index, column in enumerate(reader.fieldnames)]

        conn = sqlite3.connect(sqlite_path)
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("DROP TABLE IF EXISTS citizens")
            conn.execute("CREATE TABLE citizens (" + ", ".join(f"{q(column)} TEXT" for column in columns) + ")")

            if "piadi #" in columns:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_citizens_personal_id ON citizens (" + q("piadi #") + ")")
            if "saxeli" in columns:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_citizens_first_name ON citizens (" + q("saxeli") + ")")
            if "gvari" in columns:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_citizens_last_name ON citizens (" + q("gvari") + ")")

            placeholders = ", ".join("?" for _ in columns)
            insert_sql = "INSERT INTO citizens (" + ", ".join(q(column) for column in columns) + f") VALUES ({placeholders})"

            rows_written = 0
            batch = []
            for raw_row in reader:
                batch.append([raw_row.get(original, "") for original in reader.fieldnames])
                rows_written += 1
                if len(batch) >= 5000:
                    conn.executemany(insert_sql, batch)
                    conn.commit()
                    batch.clear()
                if limit and rows_written >= limit:
                    break

            if batch:
                conn.executemany(insert_sql, batch)
                conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("INSERT OR REPLACE INTO metadata VALUES ('columns', ?)", ("|".join(columns),))
            conn.execute("INSERT OR REPLACE INTO metadata VALUES ('source', ?)", (str(csv_path),))
            conn.commit()
            return rows_written, columns
        finally:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="Import a CSV file into the local SQLite search database.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("sqlite_path", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows, columns = import_csv(args.csv_path, args.sqlite_path, args.limit)
    print(f"Imported {rows} rows into {args.sqlite_path}")
    print(f"Columns: {', '.join(columns)}")


if __name__ == "__main__":
    main()
