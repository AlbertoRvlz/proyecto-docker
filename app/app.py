import os
import time
import psycopg2
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    for _ in range(10):
        try:
            if db_url:
                return psycopg2.connect(db_url)
            return psycopg2.connect(
                host=os.environ.get("DB_HOST", "db"),
                database=os.environ.get("DB_NAME", "catalogo_db"),
                user=os.environ.get("DB_USER", "admin"),
                password=os.environ.get("DB_PASS", "admin123")
            )
        except psycopg2.OperationalError:
            time.sleep(2)
    raise Exception("No se pudo conectar a PostgreSQL")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(100) NOT NULL,
            estado VARCHAR(50) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestor de Catálogo - Docker</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; background: #0f172a; color: #f8fafc; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        input, select, button { padding: 10px; border-radius: 6px; border: none; margin-right: 8px; }
        button { background: #3b82f6; color: white; cursor: pointer; font-weight: bold; }
        ul { list-style: none; padding: 0; }
        li { background: #334155; padding: 10px 15px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; }
        .badge { background: #10b981; color: #064e3b; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold; }
    </style>
</head>
<body>
    <h2>Gestor de Series y Películas</h2>
    <div class="card">
        <form method="POST" action="/agregar">
            <input type="text" name="titulo" placeholder="Nombre del título..." required>
            <select name="estado">
                <option value="Pendiente">Pendiente</option>
                <option value="Viendo">Viendo</option>
                <option value="Visto">Visto</option>
            </select>
            <button type="submit">Guardar</button>
        </form>
    </div>
    <div class="card">
        <h3>Registros en PostgreSQL ({{ items|length }})</h3>
        <ul>
            {% for item in items %}
            <li><span>{{ item[1] }}</span> <span class="badge">{{ item[2] }}</span></li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, estado FROM items ORDER BY id DESC;")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(HTML, items=items)

@app.route("/agregar", methods=["POST"])
def agregar():
    titulo = request.form.get("titulo")
    estado = request.form.get("estado")
    if titulo:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO items (titulo, estado) VALUES (%s, %s);", (titulo, estado))
        conn.commit()
        cur.close()
        conn.close()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
