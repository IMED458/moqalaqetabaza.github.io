#!/usr/bin/env python3
import argparse
import sqlite3
import sys
from pathlib import Path

from access_parser import AccessParser
from access_parser.access_parser import AccessTable
from access_parser.parsing_primitives import parse_data_page_header


def clean(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


def q(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def iter_rows(access_table, columns):
    for page_index, data_chunk in enumerate(access_table.table.linked_pages, start=1):
        parsed_data = parse_data_page_header(data_chunk, version=access_table.version)
        last_offset = None

        for rec_offset in parsed_data.record_offsets:
            if rec_offset & 0x8000:
                last_offset = rec_offset & 0xFFF
                continue

            if rec_offset & 0x4000:
                rec_ptr_offset = rec_offset & 0xFFF
                last_offset = rec_ptr_offset
                overflow_rec_ptr = int.from_bytes(data_chunk[rec_ptr_offset:rec_ptr_offset + 4], "little")
                record = access_table._get_overflow_record(overflow_rec_ptr)
            elif not last_offset:
                record = data_chunk[rec_offset:]
                last_offset = rec_offset
            else:
                record = data_chunk[rec_offset:last_offset]
                last_offset = rec_offset

            if not record:
                continue

            access_table.parsed_table.current = {}
            access_table._parse_row(record)
            current = access_table.parsed_table.current
            if current:
                yield [clean(current.get(column)) for column in columns]

        if page_index % 10000 == 0:
            print(f"{page_index} pages scanned...", file=sys.stderr, flush=True)


class CellWriter:
    def __init__(self, sink, column):
        self.sink = sink
        self.column = column

    def append(self, value):
        self.sink.current[self.column] = value


class RowSink(dict):
    def __init__(self):
        super().__init__()
        self.current = {}

    def __missing__(self, key):
        writer = CellWriter(self, key)
        self[key] = writer
        return writer


def import_table(db_path, table_name, sqlite_path, limit=0):
    parser = AccessParser(str(db_path))
    access_table = parser.get_table(table_name)
    if not isinstance(access_table, AccessTable):
        raise SystemExit(f"Table not found: {table_name}")

    columns = [column.col_name_str for _, column in sorted(access_table.columns.items())]
    access_table.parsed_table = RowSink()

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("DROP TABLE IF EXISTS citizens")
        conn.execute("CREATE TABLE citizens (" + ", ".join(f"{q(column)} TEXT" for column in columns) + ")")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citizens_personal_id ON citizens (" + q("piadi #") + ")")

        placeholders = ", ".join("?" for _ in columns)
        insert_sql = "INSERT INTO citizens (" + ", ".join(q(column) for column in columns) + f") VALUES ({placeholders})"

        batch = []
        rows_written = 0
        for row in iter_rows(access_table, columns):
            batch.append(row)
            rows_written += 1
            if len(batch) >= 2000:
                conn.executemany(insert_sql, batch)
                conn.commit()
                batch.clear()
            if rows_written % 10000 == 0:
                print(f"{rows_written} rows imported...", file=sys.stderr, flush=True)
            if limit and rows_written >= limit:
                break

        if batch:
            conn.executemany(insert_sql, batch)
            conn.commit()

        conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO metadata VALUES ('columns', ?)", ("|".join(columns),))
        conn.execute("INSERT OR REPLACE INTO metadata VALUES ('source', ?)", (str(db_path),))
        conn.commit()
        return rows_written, columns
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Import an Access MDB table into a local SQLite search database.")
    parser.add_argument("db_path", type=Path)
    parser.add_argument("table_name")
    parser.add_argument("sqlite_path", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows, columns = import_table(args.db_path, args.table_name, args.sqlite_path, args.limit)
    print(f"Imported {rows} rows into {args.sqlite_path}")
    print(f"Columns: {', '.join(columns)}")


if __name__ == "__main__":
    main()
