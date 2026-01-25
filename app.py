from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_secreta"

def init_database():
    conn = sqlite3.connect("form_hv.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS datos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT NOT NULL,
        ap_pat TEXT,
        ap_mat TEXT,
        ci TEXT NOT NULL,
        exp TEXT,
        est_civil TEXT NOT NULL,
        fecha_nac TEXT NOT NULL,
        lugar TEXT NOT NULL,
        nacio TEXT NOT NULL,
        direccion TEXT NOT NULL,
        ciudad TEXT NOT NULL,
        gr_san TEXT NOT NULL,
        tcel INTEGER NOT NULL,
        tfijo INTEGER
        correo TEXT UNIQUE,
        n_libser TEXT
        )
"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS experiencia(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        puesto TEXT NOT NULL,
        breve TEXT NOT NULL,
        desde TEXT NOT NULL,
        hasta TEXT NOT NULL,
        motivo TEXT NOT NULL,
        FOREIGN KEY (persona_id) REFERENCES datos(id)
        )
    """
    )

    conn.commit()
    conn.close()

init_database()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)