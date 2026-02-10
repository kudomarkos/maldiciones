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
    # Return columns in the order you specified (if exist in table)
    preferred = ["ID","DIA","MES","ANIO","PUBLICACION","TITULO","PP","TT","DIALOGO","COMENTARIO","PAQUETE","INTERNO","MITIPO","TIPO_HISTORIETA","DATO","REVISTAS","COLECCIONES","ESTRENO"]
    db = get_db()
    cur = db.execute(f"PRAGMA table_info({TABLE})")
    cols = [r["name"] for r in cur.fetchall()]
    ordered = [c for c in preferred if c in cols]
    # append any remaining columns not in preferred
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
    sql = f"SELECT * FROM {TABLE} {where} ORDER BY ANIO,MES,DIA,PUBLICACION LIMIT ? OFFSET ?"
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
        # Use parameterized query
        if isinstance(val, str):
            val = val.upper()
        sql = f"UPDATE {TABLE} SET \"{col}\" = ? WHERE ID = ?"
        db.execute(sql, (val, row_id))
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
