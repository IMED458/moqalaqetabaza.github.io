#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "data" / "citizens.sqlite"))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))
USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "change-this-password")
SECRET = os.environ.get("APP_SECRET", "dev-secret-change-before-deploy")
SESSION_TTL_SECONDS = 60 * 60 * 12


def q(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def sign(value):
    return hmac.new(SECRET.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def make_session(username):
    expires = str(int(time.time()) + SESSION_TTL_SECONDS)
    nonce = secrets.token_urlsafe(16)
    payload = f"{username}|{expires}|{nonce}"
    token = f"{payload}|{sign(payload)}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("ascii")


def verify_session(raw_cookie):
    if not raw_cookie:
        return False
    try:
        token = base64.urlsafe_b64decode(raw_cookie.encode("ascii")).decode("utf-8")
        username, expires, nonce, signature = token.rsplit("|", 3)
        payload = f"{username}|{expires}|{nonce}"
        return (
            username == USERNAME
            and int(expires) >= int(time.time())
            and hmac.compare_digest(signature, sign(payload))
        )
    except Exception:
        return False


def add_like_clause(clauses, params, columns, value):
    value = value.strip()
    if not value:
        return
    clauses.append("(" + " OR ".join(f"{q(column)} LIKE ?" for column in columns) + ")")
    params.extend([f"%{value}%"] * len(columns))


def get_columns(conn):
    row = conn.execute("SELECT value FROM metadata WHERE key = 'columns'").fetchone()
    if row and row[0]:
        return row[0].split("|")
    return [item[1] for item in conn.execute("PRAGMA table_info(citizens)").fetchall()]


def search(filters, limit=100):
    if not DB_PATH.exists():
        return {"ok": False, "error": "SQLite ბაზა ჯერ არ არის ჩატვირთული.", "rows": [], "columns": []}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        columns = get_columns(conn)
        total = conn.execute("SELECT COUNT(*) FROM citizens").fetchone()[0]
        params = []
        clauses = []
        add_like_clause(clauses, params, ["saxeli"], filters.get("first_name", ""))
        add_like_clause(clauses, params, ["gvari"], filters.get("last_name", ""))
        add_like_clause(clauses, params, ["piadi #"], filters.get("personal_id", ""))
        add_like_clause(clauses, params, ["quCa", "raioni"], filters.get("address", ""))

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = "SELECT rowid, " + ", ".join(q(column) for column in columns) + " FROM citizens" + where + " LIMIT ?"
        rows = [dict(row) for row in conn.execute(sql, [*params, limit]).fetchall()]
        matched = conn.execute("SELECT COUNT(*) FROM citizens" + where, params).fetchone()[0]
        return {"ok": True, "rows": rows, "columns": ["rowid", *columns], "total": total, "matched": matched}
    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):
    def is_authenticated(self):
        parsed = cookies.SimpleCookie(self.headers.get("Cookie"))
        session = parsed.get("session")
        return verify_session(session.value if session else "")

    def send_bytes(self, data, content_type="text/html; charset=utf-8", status=200, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != "/login":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]
        if hmac.compare_digest(username, USERNAME) and hmac.compare_digest(password, PASSWORD):
            session = make_session(username)
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"session={session}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_TTL_SECONDS}")
            self.end_headers()
            return
        self.redirect("/login?error=1")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/login":
            self.send_bytes((ROOT / "login.html").read_bytes())
            return

        if parsed.path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.send_header("Set-Cookie", "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")
            self.end_headers()
            return

        if parsed.path == "/styles.css":
            self.send_bytes((ROOT / "styles.css").read_bytes(), "text/css; charset=utf-8")
            return

        if not self.is_authenticated():
            if parsed.path.startswith("/api/"):
                payload = json.dumps({"ok": False, "error": "ავტორიზაცია საჭიროა."}, ensure_ascii=False).encode("utf-8")
                self.send_bytes(payload, "application/json; charset=utf-8", status=401)
                return
            self.redirect("/login")
            return

        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            payload = json.dumps(search({
                "first_name": params.get("first_name", [""])[0],
                "last_name": params.get("last_name", [""])[0],
                "personal_id": params.get("personal_id", [""])[0],
                "address": params.get("address", [""])[0],
            }), ensure_ascii=False).encode("utf-8")
            self.send_bytes(payload, "application/json; charset=utf-8")
            return

        target = ROOT / "index.html" if parsed.path in {"/", "/index.html"} else ROOT / parsed.path.lstrip("/")
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        content_type = "application/javascript; charset=utf-8" if target.suffix == ".js" else "text/html; charset=utf-8"
        self.send_bytes(target.read_bytes(), content_type)

    def log_message(self, format, *args):
        print(format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Open http://{HOST}:{PORT}")
    server.serve_forever()
