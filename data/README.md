# Data Folder

Place the local SQLite database here as:

```text
data/citizens.sqlite
```

This folder is intentionally ignored by Git except for this README and `.gitkeep`.

If you deploy the app, upload `citizens.sqlite` into this folder on the server, or set `DATABASE_PATH` to the uploaded file's absolute path.

You can also upload a CSV file here as:

```text
data/citizens.csv
```

Then run:

```bash
python tools/import_csv_to_sqlite.py data/citizens.csv data/citizens.sqlite
```
