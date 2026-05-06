#!/usr/bin/env python3
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from access_parser import AccessParser
from access_parser.access_parser import AccessTable
from access_parser.parsing_primitives import parse_data_page_header


class CellWriter:
    def __init__(self, sink, column):
        self.sink = sink
        self.column = column

    def append(self, value):
        self.sink.current[self.column] = value


class RowSink(defaultdict):
    def __init__(self):
        super().__init__()
        self.current = {}

    def __missing__(self, key):
        writer = CellWriter(self, key)
        self[key] = writer
        return writer


def clean(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


def export_table(db_path, table_name, output_path, limit=0):
    parser = AccessParser(str(db_path))
    access_table = parser.get_table(table_name)
    if not isinstance(access_table, AccessTable):
        raise SystemExit(f"Table not found: {table_name}")

    columns = [column.col_name_str for _, column in sorted(access_table.columns.items())]
    sink = RowSink()
    access_table.parsed_table = sink

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    partial_rows = 0

    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()

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

                sink.current = {}
                access_table._parse_row(record)
                if not sink.current:
                    continue
                if len(sink.current) < len(columns):
                    partial_rows += 1

                writer.writerow({column: clean(sink.current.get(column)) for column in columns})
                rows_written += 1

                if rows_written % 10000 == 0:
                    print(f"{rows_written} rows exported...", file=sys.stderr, flush=True)

                if limit and rows_written >= limit:
                    print(f"Stopped at limit: {limit}", file=sys.stderr)
                    return rows_written, partial_rows, columns

            if page_index % 10000 == 0:
                print(f"{page_index} pages scanned...", file=sys.stderr, flush=True)

    return rows_written, partial_rows, columns


def main():
    arg_parser = argparse.ArgumentParser(description="Export a Microsoft Access MDB table to CSV.")
    arg_parser.add_argument("db_path", type=Path)
    arg_parser.add_argument("table_name")
    arg_parser.add_argument("output_path", type=Path)
    arg_parser.add_argument("--limit", type=int, default=0)
    args = arg_parser.parse_args()

    rows, partial, columns = export_table(args.db_path, args.table_name, args.output_path, args.limit)
    print(f"Exported {rows} rows to {args.output_path}")
    print(f"Columns: {', '.join(columns)}")
    if partial:
        print(f"Rows with missing parsed fields: {partial}")


if __name__ == "__main__":
    main()
