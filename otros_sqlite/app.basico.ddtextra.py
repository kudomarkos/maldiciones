#!/usr/bin/env python3
# app.py — servidor HTTP minimal sin Flask, solo stdlib
import http.server
import socketserver
import urllib.parse
import json
import sqlite3
import os
import io

PORT = 8007
DB_PATH = os.path.join(os.path.dirname(__file__), "ddtextra.sqlite")
TABLE = "MITABLA"

class Handler(http.server.BaseHTTPRequestHandler):
    def _db(self):
        # per-request connection
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _send(self, status=200, ctype="application/json; charset=utf-8", data=b""):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            # serve index.html
            try:
                with open("Catalogadorddtextra.html", "rb") as f:
                    content = f.read()
                self._send(200, "text/html; charset=utf-8", content)
            except FileNotFoundError:
                self._send(404, "text/plain; charset=utf-8", b"catalogadorDDTEXTRA not found")
            return

        if path == "/api/columns":
            conn = self._db()
            try:
                cur = conn.execute(f"PRAGMA table_info({TABLE})")
                cols = [r["name"] for r in cur.fetchall()]
                if "ROWID" not in cols:
                    cols = ["ROWID"] + cols
                preferred = ["ROWID","numExtra","pagina","serie","titulo","personaje","autor"]
                ordered = [c for c in preferred if c in cols] + [c for c in cols if c not in preferred]
                payload = json.dumps(ordered).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", payload)
            finally:
                conn.close()
            return

        if path == "/api/rows":
            offset = int(qs.get("offset", ["0"])[0])
            limit = int(qs.get("limit", ["200"])[0])
            filters = []
            params = []
            for k, vals in qs.items():
                if k.startswith("filter__"):
                    v = vals[0].strip()
                    if v != "":
                        col = k.split("__",1)[1]
                        filters.append(f"{col} LIKE ?")
                        params.append(f"%{v}%")
            where = ("WHERE " + " AND ".join(filters)) if filters else ""
            sql = f"SELECT ROWID as ROWID, * FROM {TABLE} {where} ORDER BY numExtra, pagina LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            conn = self._db()
            try:
                cur = conn.execute(sql, params)
                rows = [dict(r) for r in cur.fetchall()]
                payload = json.dumps(rows, ensure_ascii=False).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", payload)
            finally:
                conn.close()
            return

        # unknown GET
        self._send(404, "application/json; charset=utf-8", json.dumps({"error":"not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:
            self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"invalid json"}).encode("utf-8"))
            return

        if path == "/api/update":
            if not data:
                self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"no json"}).encode("utf-8"))
                return
            row_id = data.get("id")
            col = data.get("column")
            val = data.get("value")
            if row_id is None or not col:
                self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"missing id or column"}).encode("utf-8"))
                return
            conn = self._db()
            try:
                cur = conn.execute(f"PRAGMA table_info({TABLE})")
                cols = [r["name"] for r in cur.fetchall()]
                if col not in cols:
                    self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"invalid column"}).encode("utf-8"))
                    return
                if isinstance(val, str):
                    val = val.upper()
                # Use parameter binding
                conn.execute(f'UPDATE {TABLE} SET "{col}" = ? WHERE ROWID = ?', (val, row_id))
                conn.commit()

                # (Optional) Trigger-like logic could be added here by querying updated row and performing more updates.
                self._send(200, "application/json; charset=utf-8", json.dumps({"ok":True}).encode("utf-8"))
            except Exception as e:
                conn.rollback()
                self._send(500, "application/json; charset=utf-8", json.dumps({"ok":False,"error":str(e)}).encode("utf-8"))
            finally:
                conn.close()
            return

        if path == "/api/copy_fields":
            if not data:
                self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"no json"}).encode("utf-8"))
                return
            src = data.get("src")
            dst = data.get("dst")
            if src is None or dst is None:
                self._send(400, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"missing src or dst"}).encode("utf-8"))
                return
            conn = self._db()
            try:
                cur = conn.execute("SELECT serie,titulo,personaje,autor FROM " + TABLE + " WHERE ROWID = ?", (src,))
                row = cur.fetchone()
                if not row:
                    self._send(404, "application/json; charset=utf-8", json.dumps({"ok":False,"error":"source not found"}).encode("utf-8"))
                    return
                conn.execute("UPDATE " + TABLE + " SET serie = ?, titulo = ?, personaje = ?, autor = ? WHERE ROWID = ?",
                             (row["serie"], row["titulo"], row["personaje"], row["autor"], dst))
                conn.commit()
                self._send(200, "application/json; charset=utf-8", json.dumps({"ok":True}).encode("utf-8"))
            except Exception as e:
                conn.rollback()
                self._send(500, "application/json; charset=utf-8", json.dumps({"ok":False,"error":str(e)}).encode("utf-8"))
            finally:
                conn.close()
            return

        # unknown POST
        self._send(404, "application/json; charset=utf-8", json.dumps({"error":"not found"}).encode("utf-8"))

    # avoid logging each request to stderr in default format
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"DB not found at {DB_PATH}")
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down")
            httpd.server_close()
