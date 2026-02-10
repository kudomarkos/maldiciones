from flask import Flask, g, jsonify, request, send_file, abort
import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), "Publicaciones.sqlite")
TABLE = "ZZODS23ENERO"

app = Flask(__name__, static_folder=None)

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Serve the single-page app
@app.route("/")
def index():
    return send_file("index.html")

# Get list of columns (order you prefer)
@app.route("/api/columns")
def columns():
    preferred = ["ROWID","ID","DIA","MES","ANIO","PUBLICACION","TITULO","PP","TT","DIALOGO","COMENTARIO","PAQUETE","INTERNO","MITIPO","TIPO_HISTORIETA","DATO","REVISTAS","COLECCIONES","ESTRENO"]
    db = get_db()
    cur = db.execute(f"PRAGMA table_info({TABLE})")
    cols = [r["name"] for r in cur.fetchall()]
    # insert virtual ROWID at front if not a real column
    if "ROWID" not in cols:
        cols = ["ROWID"] + cols
    ordered = [c for c in preferred if c in cols]
    for c in cols:
        if c not in ordered:
            ordered.append(c)
    return jsonify(ordered)

# Fetch rows with optional filters (simple equality or substring)
@app.route("/api/rows")
def rows():
    db = get_db()
    # pagination optional: offset, limit
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 200))
    # filters: expect params like filter__COLNAME=somevalue (substring match)
    filters = []
    params = []
    for k, v in request.args.items():
        if k.startswith("filter__") and v.strip() != "":
            col = k.split("__",1)[1]
            filters.append(f"{col} LIKE ?")
            params.append(f"%{v}%")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    sql = f"SELECT ROWID as ROWID, * FROM {TABLE} {where} ORDER BY ANIO,MES,DIA,PUBLICACION LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cur = db.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

# Update single cell: expects JSON { "id": <id>, "column": "<COL>", "value": "<new>" }
@app.route("/api/update", methods=["POST"])
def update_cell():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "no json"}), 400
    row_id = data.get("id")
    col = data.get("column")
    val = data.get("value")
    if row_id is None or not col:
        return jsonify({"ok": False, "error": "missing id or column"}), 400
    # Basic safety: allow only existing columns
    db = get_db()
    cur = db.execute(f"PRAGMA table_info({TABLE})")
    cols = [r["name"] for r in cur.fetchall()]
    if col not in cols:
        return jsonify({"ok": False, "error": "invalid column"}), 400

    try:
        if isinstance(val, str):
            val = val.upper()
        sql = f'UPDATE {TABLE} SET "{col}" = ? WHERE ROWID = ?'
        db.execute(sql, (val, row_id))
        db.commit()
        '''
        # --- Trigger logic implemented in Python ---
        # Fetch the updated row to check fields
        cur = db.execute("SELECT ROWID AS ROWID, PUBLICACION, ANIO, MITIPO, TITULO, PP, TT, DIALOGO, ROWID FROM ZZODS23ENERO WHERE ROWID = ?", (row_id,))
        updated = cur.fetchone()
        if not updated:
            return jsonify({"ok": True})

        def bad(x):
            if x is None:
                return True
            s = str(x).strip().upper()
            return s == "??" or s.startswith("NO LLEVA HISTORIETA") or s == "NO"

        # Only proceed if none of the four fields are "bad"
        if not (bad(updated["TITULO"]) or bad(updated["PP"]) or bad(updated["TT"])):
            # Find matched records (exact match on the four fields)
            q = """
            SELECT PUBLICACION, ANIO, MITIPO, TITULO, PP, TT, DIALOGO, ROWID
            FROM ZZODS23ENERO
            WHERE TITULO = ? AND PP = ? AND TT = ? AND DIALOGO = ?
            ORDER BY ANIO
            """
            params = (updated["TITULO"], updated["PP"], updated["TT"], updated["DIALOGO"])
            cur = db.execute(q, params)
            matches = cur.fetchall()
            if matches:
                # Determine min ROWID (first by ANIO ordering because we used ORDER BY ANIO)
                rowids = [r["ROWID"] for r in matches]
                publis = [r["PUBLICACION"] for r in matches]
                anios = [r["ANIO"] for r in matches]
                min_publi = publis[0]
                min_rowid = rowids[0]
                min_anio = anios[0]
        '''
        '''
                # Update DATO for each matched record
                for r in matches:
                    print(r)
                    if r["ROWID"] == min_rowid:
                        dato = "Estreno"
                    else:
                        pub = min_publi
                        anio = min_anio
                        dato = f"{pub} en {anio}".strip()
                    db.execute("UPDATE ZZODS23ENERO SET DATO = ? WHERE ROWID = ?", (dato, r["ROWID"]))

                # Build REVISTAS and COLECCIONES strings using Python to mimic GROUP_CONCAT(..., ', ')
                revistas_list = [r["PUBLICACION"] for r in matches if r["MITIPO"] == "R" and r["PUBLICACION"]]
                colec_list = [r["PUBLICACION"] for r in matches if r["MITIPO"] != "R" and r["PUBLICACION"]]
                revistas = ", ".join(dict.fromkeys(revistas_list)) if revistas_list else None
                colecciones = ", ".join(dict.fromkeys(colec_list)) if colec_list else None

                # Update REVISTAS and COLECCIONES for all matched ROWIDs
                for rid in rowids:
                    db.execute(
                        "UPDATE ZZODS23ENERO SET REVISTAS = ?, COLECCIONES = ? WHERE ROWID = ?",
                        (revistas, colecciones, rid),
                    )

                db.commit()
        '''
        return jsonify({"ok": True})

    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# Añadir en app.py (ruta POST)
@app.route("/api/copy_fields", methods=["POST"])
def copy_fields():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "no json"}), 400
    src = data.get("src")
    dst = data.get("dst")
    if src is None or dst is None:
        return jsonify({"ok": False, "error": "missing src or dst"}), 400
    db = get_db()
    try:
        cur = db.execute("SELECT TITULO, PP, TT, DIALOGO FROM ZZODS23ENERO WHERE ROWID = ?", (src,))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": False, "error": "source not found"}), 404
        db.execute(
            "UPDATE ZZODS23ENERO SET TITULO = ?, PP = ?, TT = ?, DIALOGO = ? WHERE ROWID = ?",
            (row["TITULO"], row["PP"], row["TT"], row["DIALOGO"], dst),
        )
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
