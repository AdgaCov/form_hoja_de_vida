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
        CREATE TABLE IF NOT EXISTS formacion_academica(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        detalle TEXT NOT NULL,
        institucion TEXT NOT NULL,
        grado TEXT NOT NULL,
        anio INTEGER,
        n_folio TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
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
        CREATE TABLE IF NOT EXISTS cursos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        anio INTEGER,
        area_capacitacion TEXT NOT NULL,
        institucion TEXT NOT NULL,
        nombre_capacitacion TEXT NOT NULL,
        duracion_horas INTEGER,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS paquetes_informaticos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        paquete TEXT NOT NULL,
        nivel TEXT CHECK(nivel IN ('regular', 'bueno', 'muy_bueno')),
        folio TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS idiomas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        idioma TEXT NOT NULL,
        lectura BOOLEAN DEFAULT 0,
        escritura BOOLEAN DEFAULT 0,
        conversacion BOOLEAN DEFAULT 0,
        folio TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS docencia(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        anio INTEGER,
        institucion TEXT NOT NULL,
        nombre_curso TEXT NOT NULL,
        duracion_horas INTEGER,
        folio TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS referencias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        nombre_apellido TEXT NOT NULL,
        institucion TEXT NOT NULL,
        puesto TEXT NOT NULL,
        telefono TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS registro_profesional(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        nombre TEXT,
        numero_registro TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pretension_salarial(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        monto_bs TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incompatibilidades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        vinculacion_ministerio TEXT CHECK(vinculacion_ministerio IN ('si', 'no')),
        otra_actividad TEXT CHECK(otra_actividad IN ('si', 'no')),
        percibe_renta TEXT CHECK(percibe_renta IN ('si', 'no')),
        destitucion_sentencia TEXT CHECK(destitucion_sentencia IN ('si', 'no')),
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS declaracion_jurada(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        lugar TEXT,
        fecha TEXT,
        FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
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
    with get_db_connection() as conn:
        datos = conn.execute('SELECT * FROM datos ORDER BY id ASC').fetchall()
        usuarios = conn.execute('SELECT id, username FROM users ORDER BY id').fetchall()
    return render_template("usuarios.html", datos=datos, usuarios=usuarios)

@app.route("/crear_usuario", methods=["POST"])
@login_required
def crear_usuario():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if password != confirm_password:
        flash('Las contraseñas no coinciden', 'danger')
        return redirect(url_for('usuarios'))
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
        
        flash(f'Usuario {username} creado exitosamente', 'success')
    except sqlite3.IntegrityError:
        flash('El usuario ya existe', 'danger')
    
    return redirect(url_for('usuarios'))

# Ruta para editar usuario
@app.route("/editar_usuario/<int:id>", methods=["POST"])
@login_required
def editar_usuario(id):
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if password:
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "UPDATE users SET username = ?, password = ? WHERE id = ?",
                    (username, hashed_password, id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET username = ? WHERE id = ?",
                    (username, id)
                )
            
            conn.commit()
        
        flash(f'Usuario actualizado exitosamente', 'success')
    except sqlite3.IntegrityError:
        flash('El nombre de usuario ya existe', 'danger')
    except Exception as e:
        flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios'))

@app.route("/eliminar_usuario/<int:id>", methods=["POST"])
@login_required
def eliminar_usuario(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (id,))
            conn.commit()
        
        flash('Usuario eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios'))


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

            #formacion
            detalles = request.form.getlist('detalle[]')
            instituciones = request.form.getlist('institucion[]')
            grados = request.form.getlist('grado[]')
            anios = request.form.getlist('anio[]')
            folios = request.form.getlist('n_folio[]')

            for i in range(len(detalles)):
                if detalles[i].strip() and instituciones[i].strip():
                    cursor.execute(
                        """
                        INSERT INTO formacion_academica (persona_id, detalles, isntituciones, grados, anios, folios)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (persona_id,
                         detalles[i],
                         instituciones[i],
                         grados[i],
                         int(anios[i]) if anios[i] else None,
                         folios[i] if i < len(folios) else None
                        )
                    )

            #experiencia
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
            
            #cursos
            anios_cursos = request.form.getlist['anio[]']
            capacitaciones = request.form.getlist['cap[]']
            instituciones_curso = request.form.getlist['inst[]']
            nombres_cap = request.form.getlist['n_cap[]']
            horas = request.form.getlist['horas[]']

            for i in range(len(capacitaciones)):
                if capacitaciones[i].strip() and instituciones_curso[i].strip():
                    cursor.execute(
                        """
                        INSERT INTO cursos (persona_id, anio, cap, inst, n_cap, horas)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            int(anios_cursos[i]) if i < len(anios_cursos) and anios_cursos[i] else None,
                            capacitaciones[i],
                            instituciones_curso[i],
                            nombres_cap[i] if i < len(nombres_cap) else '',
                            int(horas[i]) if i < len(horas) and horas[i] else None
                        )
                    )
            
            #paquetes
            paquetes = request.form.getlist('paquete[]')
            folios_paquete = request.form.getlist('folio_paquete[]')
            
            for i in range(len(paquetes)):
                if paquetes[i].strip():
                    nivel = request.form.get(f'nivel_{i}')
                    cursor.execute(
                        """
                        INSERT INTO paquetes_informaticos (persona_id, paquete, nivel, folio)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            paquetes[i],
                            nivel,
                            folios_paquete[i] if i < len(folios_paquete) else None
                        )
                    )

            #idiomas
            idiomas = request.form.getlist('idioma[]')
            folios_idioma = request.form.getlist('folio_idioma[]')
            
            for i in range(len(idiomas)):
                if idiomas[i].strip():
                    lectura = 1 if f'lectura_{i}' in request.form else 0
                    escritura = 1 if f'escritura_{i}' in request.form else 0
                    conversacion = 1 if f'conversacion_{i}' in request.form else 0
                    
                    cursor.execute(
                        """
                        INSERT INTO idiomas (persona_id, idioma, lectura, escritura, conversacion, folio)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            idiomas[i],
                            lectura,
                            escritura,
                            conversacion,
                            folios_idioma[i] if i < len(folios_idioma) else None
                        )
                    )
            
            #docencia
            anios_docencia = request.form.getlist('anio_docencia[]')
            instituciones_docencia = request.form.getlist('institución_docencia[]')
            nombres_curso = request.form.getlist('nombre_curso[]')
            horas_docencia = request.form.getlist('horas_docencia[]')
            folios_docencia = request.form.getlist('folio_docencia[]')

            for i in range(len(instituciones_docencia)):
                if instituciones_docencia[i].strip() and nombres_curso[i].strip():
                    cursor.execute(
                        """
                        INSERT INTO docencia (persona_id, anio, institucion, nombre_curso, duracion_horas, folio)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            int(anios_docencia[i]) if i < len(anios_docencia) and anios_docencia[i] else None,
                            instituciones_docencia[i],
                            nombres_curso[i],
                            int(horas_docencia[i]) if i < len(horas_docencia) and horas_docencia[i] else None,
                            folios_docencia[i] if i < len(folios_docencia) else None
                        )
                    )
            
            #referencias
            nombres_ref = request.form.getlist('nombre_ref[]')
            instituciones_ref = request.form.getlist('institucion_ref[]')
            puestos_ref = request.form.getlist('puesto_ref[]')
            telefonos_ref = request.form.getlist('telefono_ref[]')
            
            for i in range(len(nombres_ref)):
                if nombres_ref[i].strip() and instituciones_ref[i].strip():
                    cursor.execute(
                        """
                        INSERT INTO referencias (persona_id, nombre_apellido, institucion, puesto, telefono)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            persona_id,
                            nombres_ref[i],
                            instituciones_ref[i],
                            puestos_ref[i] if i < len(puestos_ref) else '',
                            telefonos_ref[i] if i < len(telefonos_ref) else None
                        )
                    )
            
            #registro profesional
            nombre_registro = request.form.get('nombre_registro')
            numero_registro = request.form.get('numero_registro')
            
            if nombre_registro or numero_registro:
                cursor.execute(
                    """
                    INSERT INTO registro_profesional (persona_id, nombre, numero_registro)
                    VALUES (?, ?, ?)
                    """,
                    (
                        persona_id,
                        nombre_registro,
                        numero_registro
                    )
                )

            #pretension salarial
            monto_bs = request.form.get('monto_bs')

            if monto_bs:
                cursor.execute(
                    """
                    INSERT INTO pretension_salarial (persona_id, monto_bs)
                    VALUES (?, ?)
                    """,
                    (persona_id, monto_bs)
                )

            #incopatibilidades
            cursor.execute(
                """
                INSERT INTO incompatibilidades (persona_id, vinculacion_ministerio, otra_actividad, percibe_renta, destitucion_sentencia)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    persona_id,
                    request.form.get('prg1'),
                    request.form.get('prg2'),
                    request.form.get('prg3'),
                    request.form.get('prg4')
                )
            )

            #declaracion
            lugar_declaracion = request.form.get('lugar_declaracion')
            fecha_declaracion = request.form.get('fecha_declaracion')
            
            if lugar_declaracion or fecha_declaracion:
                cursor.execute(
                    """
                    INSERT INTO declaracion_jurada (persona_id, lugar, fecha)
                    VALUES (?, ?, ?)
                    """,
                    (
                        persona_id,
                        lugar_declaracion,
                        fecha_declaracion
                    )
                )

            conn.commit()
            flash('Formulario guardado exitosamente','success')


            conn = get_db_connection()
            persona = conn.execute("SELECT * FROM datos WHERE id = ?", (persona_id,)).fetchone()
            experiencia = conn.execute("SELECT * FROM experiencia WHERE persona_id = ?",(persona_id,)).fetchone()
            conn.close()

            pdf_file = genera_pdf_formulario(persona, experiencia)
            nombre_pdf = f"FORMULARIO_HV_{persona_id}.pdf"

            return send_file(
                pdf_file,
                as_attachment=True,
                download_name=nombre_pdf,
                mimetype="application/pdf"
            )           

        
        flash('Formulario guardado correctamente', 'success')
        return redirect(url_for('index'))
    
    except sqlite3.IntegrityError as e:
        flash('El correo ya existe', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error al guardar: {str(e)}','error')
        return redirect(url_for('index'))

def genera_pdf_formulario(persona, experiencia):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "FORMULARIO - HOJA DE VIDA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)
    #datos 
    datos_personales_layout(pdf, persona)

    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest="S")
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

def datos_personales_layout(pdf, persona):
    pdf.set_font("Helvetica", "", 10)

    left = 12
    right = 12
    top = pdf.get_y() + 5

    page_w = pdf.w - left - right
    box_h = 8
    gap_y = 14
    label_gap = 4

    container_x = left
    container_y = top
    container_w = page_w
    container_h = 95

    pdf.rect(container_x, container_y, container_w, container_h)

    header_h = 10
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(container_x, container_y)
    pdf.cell(container_w, header_h, "I. DATOS PERSONALES", border=0, fill=True, new_x="LMARGIN", new_y="TOP")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)

    inner_x = container_x + 8
    inner_y = container_y + header_h + 6
    inner_w = container_w - 16

    col_gap = 6
    col_w = (inner_w - (col_gap * 2)) / 3

    def draw_field(label, value, x, y, w):
        #label
        pdf.set_xy(x, y)
        pdf.cell(w, 4, label)
        #box
        box_y = y + label_gap
        pdf.rect(x, box_y, w, box_h)

        pdf.set_xy(x + 2, box_y + 2)
        txt = "" if value is None else str(value)
        pdf.cell(w - 4, 4, txt)

    x1 = inner_x
    x2 = inner_x + col_w + col_gap
    x3 = inner_x + (col_w + col_gap) * 2

    y = inner_y

    #f1
    draw_field("Nombres:", persona["nombres"], x1, y, col_w)
    draw_field("Apellido Paterno:", persona["ap_pat"], x2, y, col_w)
    draw_field("Apellido Materno:", persona["ap_mat"], x3, y, col_w)

    #F2
    y += gap_y
    draw_field("Cédula de Identidad:", persona["ci"], x1, y, col_w)
    draw_field("Expedido:", persona["exp"], x2, y, col_w)
    draw_field("Estado Civil:", persona["est_civil"], x3, y, col_w)

    #F3
    y += gap_y
    draw_field("Fecha de nacimiento:", persona["fecha_nac"], x1, y, col_w)
    draw_field("Lugar:", persona["lugar"], x2, y, col_w)
    draw_field("Nacionalidad:", persona["nacio"], x3, y, col_w)

    #F4
    y += gap_y
    dir_w = col_w * 1.5 + col_gap / 2
    rest_w = inner_w - dir_w - col_gap
    ciudad_w = rest_w / 2
    grupo_w = rest_w / 2

    draw_field("Dirección:", persona["direccion"], x1, y, dir_w)
    x_ciudad = x1 + dir_w + col_gap
    draw_field("Ciudad:", persona["ciudad"], x_ciudad, y, ciudad_w)
    x_grupo = x_ciudad + ciudad_w + col_gap
    draw_field("Grupo Sanguíneo:", persona["gr_san"], x_grupo, y, grupo_w)

    #F5
    y += gap_y
    draw_field("Teléfono Celular:", persona["tcel"], x1, y, col_w)
    draw_field("Teléfono Fijo:", persona["tfijo"], x2, y, col_w)
    draw_field("Correo Electrónico:", persona["correo"], x3, y, col_w)

    #F6
    y += gap_y
    draw_field("N° de Libreta de Servicio Militar", persona["n_libser"], x1, y, inner_w)


    pdf.set_y(container_y + container_h + 8)



if __name__ == "__main__":
    app.run(debug=True)