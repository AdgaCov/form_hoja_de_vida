from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from fpdf import FPDF
from flask import send_file
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "clave_secreta"

#login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

def get_db_connection():
    conn = sqlite3.connect('form_hv.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode = WAL")

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
        tfijo INTEGER,
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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
        );
        """
    )

    cursor.execute("SELECT * FROM users WHERE username = ?",('admin',))
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash ('culturas')
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password)
        )
        print("Usuario por defecto creado")


    conn.commit()
    conn.close()

init_database()

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id=?',(user_id, )).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'],user['password'])
        return None
    
    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username=?', (username, )).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['password'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Inicio de sesión exitoso','success')
            return redirect(url_for('usuarios'))
        else:
            flash('Credenciales inválidas','danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión','info')
    return redirect(url_for('login'))

@app.route('/usuarios')
@login_required
def usuarios():
    conn = get_db_connection()
    datos = conn.execute(
        """
        SELECT id, nombres, ap_pat, ap_mat, ci FROM datos ORDER BY id DESC
        """
    ).fetchall()
    conn.close()

    return render_template("usuarios.html", datos=datos)

@app.route('/detalles/<int:id>')
@login_required
def detalles(id):
    conn = get_db_connection()
    persona = conn.execute("SELECT * FROM datos WHERE id = ?", (id, )).fetchone()
    experiencia = conn.execute(
        """
        SELECT * FROM experiencia
        WHERE persona_id = ?
        ORDER BY id DESC
        """, (id,)).fetchall()
    
    conn.close()

    if persona is None:
        flash("Persona no encontrada", "error")
        return redirect(url_for('usuarios'))
    return render_template("detalles.html", persona=persona, experiencia=experiencia)

@app.route("/eliminar/<int:id>", methods=['POST'])
@login_required
def eliminar(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM experiencia WHERE persona_id = ?", (id, ))
        cursor.execute("DELETE FROM datos WHERE id = ?", (id, ))

        conn.commit()
        conn.close()

        flash("Registro eliminado!!!", 'success')
        return redirect(url_for("usuarios"))
    
    except Exception as e:
        flash(f"Error al eliminar: {str(e)}", 'error')
        return redirect(url_for('usuarios'))

@app.route("/guardar_formulario", methods=["POST"])
def guardar_formulario():
    persona_id = None
    try:
        with get_db_connection() as conn:
        
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO datos (nombres, ap_pat, ap_mat, ci, exp, est_civil, fecha_nac, lugar, nacio, direccion, ciudad, gr_san, tcel, tfijo, correo, n_libser)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.form.get('nombres'),
                    request.form.get('ap_pat'),
                    request.form.get('ap_mat'),
                    request.form.get('ci'),
                    request.form.get('exp'),
                    request.form.get('est_civil'),
                    request.form.get('fecha_nac'),
                    request.form.get('lugar'),
                    request.form.get('nacio'),
                    request.form.get('direccion'),
                    request.form.get('ciudad'),
                    request.form.get('gr_san'),
                    request.form.get('tcel'),
                    request.form.get('tfijo'),
                    request.form.get('correo'),
                    request.form.get('n_libser')
                )
            )
            
            persona_id = cursor.lastrowid

            nombre = request.form.getlist('nombre[]')
            puesto = request.form.getlist('puesto[]')
            breve = request.form.getlist('breve[]')
            desde = request.form.getlist('desde[]')
            hasta = request.form.getlist('hasta[]')
            motivo = request.form.getlist('motivo[]')

            for i in range(len(nombre)):
                if nombre[i].strip() and puesto[i].strip():
                    cursor.execute(
                        """
                        INSERT INTO experiencia (persona_id, nombre, puesto, breve, desde, hasta, motivo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            nombre[i],
                            puesto[i],
                            breve[i],
                            desde[i],
                            hasta[i],
                            motivo[i]
                        )
                    )
            conn.commit()
        
        flash('Formulario guardado correctamente', 'success')
        return redirect(url_for('index'))
    
    except sqlite3.IntegrityError as e:
        flash('El correo ya existe', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error al guardar: {str(e)}','error')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)