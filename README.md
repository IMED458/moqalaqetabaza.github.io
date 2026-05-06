# მოქალაქეთა ძებნა

ლოკალური Python/SQLite საძიებო აპი username/password ავტორიზაციით.

## გაშვება

1. SQLite ფაილი ჩადეთ აქ:

```text
data/citizens.sqlite
```

2. გაუშვით სერვერი:

```bash
APP_USERNAME=admin APP_PASSWORD='strong-password' APP_SECRET='random-long-secret' python3 server.py
```

3. გახსენით:

```text
http://127.0.0.1:8765
```

ნაგულისხმევი ლოკალური მონაცემებია:

```text
username: admin
password: change-this-password
```

გაშვებისას შეცვალეთ `APP_PASSWORD` და `APP_SECRET`.

## მონაცემები

`data/` საქაღალდე მზად არის მონაცემთა ფაილისთვის, მაგრამ `.gitignore` იცავს, რომ `.mdb`, `.sqlite`, `.csv`, `.db` და მსგავსი ფაილები Git-ში შემთხვევით არ მოხვდეს.

მოსალოდნელი SQLite სტრუქტურა:

- table: `citizens`
- optional metadata table: `metadata`, key `columns`
- ძირითადი სვეტები: `saxeli`, `gvari`, `piadi #`, `quCa`, `raioni`

## MDB-დან SQLite-მდე

თუ გაქვთ `.mdb` ფაილი და გინდათ ამ აპისთვის SQLite ბაზის მომზადება:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python tools/import_mdb_to_sqlite.py "path/to/database.mdb" reestri data/citizens.sqlite
```

შემდეგ გაუშვით `python3 server.py`.

## ქსელში გახსნა

იგივე Wi-Fi-ზე სხვა მოწყობილობიდან გასახსნელად:

```bash
HOST=0.0.0.0 APP_USERNAME=admin APP_PASSWORD='strong-password' APP_SECRET='random-long-secret' python3 server.py
```

შემდეგ გახსენით `http://MAC_IP:8765`.
