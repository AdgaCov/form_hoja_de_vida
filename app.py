from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_database():
    conn = sqlite3.connect("form_hv.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS datos(
        id INTEGER PRIMARY KEY,
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
        tcel INTEGER NOT NULL,
        tfijo INTEGER
        correo TEXT UNIQUE,
        n_libser TEXT
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