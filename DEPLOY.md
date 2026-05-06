# Deploy Notes

## Database Location

The app reads a SQLite database from:

```text
data/citizens.sqlite
```

You can also store the database somewhere else and point the app to it:

```bash
DATABASE_PATH=/absolute/path/to/citizens.sqlite python3 server.py
```

The database file is intentionally ignored by Git. Upload it to your server by the hosting provider's file manager, SCP/SFTP, SSH, or a private volume. After upload, the file must be readable by the process that runs `server.py`.

## Required Environment Variables

Set these before running the server:

```bash
APP_USERNAME=admin
APP_PASSWORD='strong-password'
APP_SECRET='long-random-secret'
DATABASE_PATH=data/citizens.sqlite
```

For a public server, bind to the provider's host/port:

```bash
HOST=0.0.0.0 PORT=8765 python3 server.py
```

## Convert MDB To SQLite

If you only have the Access `.mdb` file, convert it first:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python tools/import_mdb_to_sqlite.py "path/to/database.mdb" reestri data/citizens.sqlite
```

Then upload `data/citizens.sqlite` to the same location on the server.

## Upload CSV Instead

If you want to upload a CSV file, put it here:

```text
data/citizens.csv
```

Then import it into SQLite:

```bash
python tools/import_csv_to_sqlite.py data/citizens.csv data/citizens.sqlite
```

Or let the app import it on first start when the SQLite database does not exist:

```bash
AUTO_IMPORT_CSV=1 CSV_PATH=data/citizens.csv DATABASE_PATH=data/citizens.sqlite python3 server.py
```

The CSV file is ignored by Git. Upload it to the server through your hosting file manager, SCP/SFTP, SSH, or private volume.

## Quick Check

After the server starts, open:

```text
http://SERVER_ADDRESS:PORT
```

Log in with `APP_USERNAME` and `APP_PASSWORD`.
