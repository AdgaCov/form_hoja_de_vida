from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask import send_file
import os
from io import BytesIO
from itertools import zip_longest
from templates.pdf_generator import genera_pdf_formulario
from templates.pdf_generator_detalles import genera_pdf_detalles

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
        desde TEXT,
        hasta TEXT,
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

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS resumen_experiencia(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id INTEGER NOT NULL,
    total_anios INTEGER DEFAULT 0,
    total_meses INTEGER DEFAULT 0,
    fecha_calculo TEXT,
    FOREIGN KEY (persona_id) REFERENCES datos(id) ON DELETE CASCADE
    )
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
    persona = conn.execute("SELECT * FROM datos WHERE id = ?", (id,)).fetchone()
    
    if persona is None:
        conn.close()
        flash("Persona no encontrada", "error")
        return redirect(url_for('usuarios'))
    
    # Obtener TODOS los datos
    experiencia = conn.execute("SELECT * FROM experiencia WHERE persona_id = ? ORDER BY desde DESC", (id,)).fetchall()
    formacion = conn.execute("SELECT * FROM formacion_academica WHERE persona_id = ?", (id,)).fetchall()
    cursos = conn.execute("SELECT * FROM cursos WHERE persona_id = ?", (id,)).fetchall()
    paquetes = conn.execute("SELECT * FROM paquetes_informaticos WHERE persona_id = ?", (id,)).fetchall()
    idiomas = conn.execute("SELECT * FROM idiomas WHERE persona_id = ?", (id,)).fetchall()
    docencia = conn.execute("SELECT * FROM docencia WHERE persona_id = ?", (id,)).fetchall()
    referencias = conn.execute("SELECT * FROM referencias WHERE persona_id = ?", (id,)).fetchall()
    registro = conn.execute("SELECT * FROM registro_profesional WHERE persona_id = ?", (id,)).fetchone()
    pretension = conn.execute("SELECT * FROM pretension_salarial WHERE persona_id = ?", (id,)).fetchone()
    incompatibilidades = conn.execute("SELECT * FROM incompatibilidades WHERE persona_id = ?", (id,)).fetchone()
    declaracion = conn.execute("SELECT * FROM declaracion_jurada WHERE persona_id = ?", (id,)).fetchone()
    resumen = conn.execute("SELECT * FROM resumen_experiencia WHERE persona_id = ? ORDER BY id DESC LIMIT 1", (id,)).fetchone()
    
    conn.close()
    
    return render_template("detalles.html", 
                        persona=persona,
                        experiencia=experiencia,
                        formacion=formacion,
                        cursos=cursos,
                        paquetes=paquetes,
                        idiomas=idiomas,
                        docencia=docencia,
                        referencias=referencias,
                        registro=registro,
                        pretension=pretension,
                        incompatibilidades=incompatibilidades,
                        declaracion=declaracion,
                        resumen=resumen)

@app.route('/guardar_resumen/<int:id>', methods=['POST'])
@login_required
def guardar_resumen(id):
    try:
        anios = request.json.get('anios', 0)
        meses = request.json.get('meses', 0)
        
        from datetime import datetime
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar nuevo resumen
        cursor.execute("""
            INSERT INTO resumen_experiencia (persona_id, total_anios, total_meses, fecha_calculo)
            VALUES (?, ?, ?, ?)
        """, (id, anios, meses, fecha_actual))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Resumen guardado correctamente'}
    except Exception as e:
        return {'success': False, 'message': str(e)}, 400
    
@app.route('/imprimir_detalles/<int:id>')
@login_required
def imprimir_detalles(id):
    conn = get_db_connection()
    
    persona_row = conn.execute("SELECT * FROM datos WHERE id = ?", (id,)).fetchone()
    persona = dict(persona_row) if persona_row else None

    if not persona:
        conn.close()
        flash("Persona no encontrada", "error")
        return redirect(url_for('usuarios'))
    
    experiencia_rows = conn.execute(
        "SELECT * FROM experiencia WHERE persona_id = ? ORDER BY desde DESC", 
        (id,)
    ).fetchall()
    experiencia = [dict(row) for row in experiencia_rows]
    
    resumen_row = conn.execute(
        "SELECT * FROM resumen_experiencia WHERE persona_id = ? ORDER BY id DESC LIMIT 1", 
        (id,)
    ).fetchone()
    resumen = dict(resumen_row) if resumen_row else None
    
    conn.close()
    
    pdf_file = genera_pdf_detalles(persona, experiencia, resumen)
    nombre_pdf = f"DETALLES_HV_{id}.pdf"
    
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=nombre_pdf,
        mimetype="application/pdf"
    )

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

def obtener_datos_completos(persona_id):
    """Obtiene todos los datos de una persona y los convierte a diccionarios"""
    conn = get_db_connection()
    
    # Datos personales
    persona_row = conn.execute("SELECT * FROM datos WHERE id = ?", (persona_id,)).fetchone()
    persona = dict(persona_row) if persona_row else None
    
    # Experiencia
    experiencia_rows = conn.execute(
        "SELECT * FROM experiencia WHERE persona_id = ? ORDER BY id DESC", 
        (persona_id,)
    ).fetchall()
    experiencia = [dict(row) for row in experiencia_rows]
    
    # Formación académica
    formacion_rows = conn.execute(
        "SELECT * FROM formacion_academica WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    formacion = [dict(row) for row in formacion_rows]
    
    # Cursos
    cursos_rows = conn.execute(
        "SELECT * FROM cursos WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    cursos = [dict(row) for row in cursos_rows]
    
    # Paquetes informáticos
    paquetes_rows = conn.execute(
        "SELECT * FROM paquetes_informaticos WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    paquetes = [dict(row) for row in paquetes_rows]
    
    # Idiomas
    idiomas_rows = conn.execute(
        "SELECT * FROM idiomas WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    idiomas = [dict(row) for row in idiomas_rows]
    
    # Docencia
    docencia_rows = conn.execute(
        "SELECT * FROM docencia WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    docencia = [dict(row) for row in docencia_rows]
    
    # Referencias
    referencias_rows = conn.execute(
        "SELECT * FROM referencias WHERE persona_id = ?", 
        (persona_id,)
    ).fetchall()
    referencias = [dict(row) for row in referencias_rows]
    
    # Registro profesional
    registro_row = conn.execute(
        "SELECT * FROM registro_profesional WHERE persona_id = ?", 
        (persona_id,)
    ).fetchone()
    registro = dict(registro_row) if registro_row else None
    
    # Pretensión salarial
    pretension_row = conn.execute(
        "SELECT * FROM pretension_salarial WHERE persona_id = ?", 
        (persona_id,)
    ).fetchone()
    pretension = dict(pretension_row) if pretension_row else None
    
    # Incompatibilidades
    incompatibilidades_row = conn.execute(
        "SELECT * FROM incompatibilidades WHERE persona_id = ?", 
        (persona_id,)
    ).fetchone()
    incompatibilidades = dict(incompatibilidades_row) if incompatibilidades_row else None
    
    # Declaración jurada
    declaracion_row = conn.execute(
        "SELECT * FROM declaracion_jurada WHERE persona_id = ?", 
        (persona_id,)
    ).fetchone()
    declaracion = dict(declaracion_row) if declaracion_row else None
    
    conn.close()
    
    return persona, experiencia, formacion, cursos, paquetes, idiomas, docencia, referencias, registro, pretension, incompatibilidades, declaracion

@app.route("/guardar_formulario", methods=["POST"])
def guardar_formulario():
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
            anios = request.form.getlist('anio_formacion[]')
            folios = request.form.getlist('n_folio[]')

            for detalle, institucion, grado, anio, folio in zip_longest(detalles, instituciones, grados, anios, folios, fillvalue=""):
                detalle = detalle.strip()
                institucion = institucion.strip()
                grado = grado.strip()
                anio = anio.strip()
                folio = folio.strip()

                if not detalle and not institucion and not grado and not anio and not folio:
                    continue

                cursor.execute(
                    """
                    INSERT INTO formacion_academica (persona_id, detalle, institucion, grado, anio, n_folio)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,(persona_id, detalle, institucion, grado, 
                        int(anio) if anio.isdigit() else None, 
                        folio if folio else None)
                )

            # experiencia
            nombres = request.form.getlist('nombre[]')
            puestos = request.form.getlist('puesto[]')
            breves = request.form.getlist('breve[]')
            desdes = request.form.getlist('desde[]')
            hastas = request.form.getlist('hasta[]')
            motivos = request.form.getlist('motivo[]')

            for nombre, puesto, breve, desde, hasta, motivo in zip_longest(nombres, puestos, breves, desdes, hastas, motivos, fillvalue=""):
                # limpiamos
                nombre = nombre.strip()
                puesto = puesto.strip()
                breve = breve.strip()
                desde = desde.strip()
                hasta = hasta.strip()
                motivo = motivo.strip()

                # si la fila está vacía, no insertamos
                if not nombre and not puesto and not breve and not desde and not hasta and not motivo:
                    continue

                cursor.execute("""
                    INSERT INTO experiencia (persona_id, nombre, puesto, breve, desde, hasta, motivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (persona_id, nombre, puesto, breve, desde if desde else None, hasta if hasta else None, motivo))

            #cursos
            anios_cursos = request.form.getlist('anio_curso[]')
            capacitaciones = request.form.getlist('cap[]')
            instituciones_curso = request.form.getlist('inst[]')
            nombres_cap = request.form.getlist('n_cap[]')
            horas = request.form.getlist('horas[]')

            for anio, cap, inst, n_cap, horas in zip_longest(anios_cursos, capacitaciones, instituciones_curso, nombres_cap, horas, fillvalue=""):
                anio = anio.strip()
                cap = cap.strip()
                inst = inst.strip()
                n_cap = n_cap.strip()
                horas = horas.strip()
                
                if not anio and not cap and not inst and not n_cap and not horas:
                    continue
                
                cursor.execute(
                    """
                    INSERT INTO cursos (persona_id, anio, area_capacitacion, institucion, nombre_capacitacion, duracion_horas)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,(persona_id, 
                        int(anio) if anio.isdigit() else None, cap, inst, n_cap, 
                        int(horas) if horas.isdigit() else None))
            
            #paquetes
            paquetes = request.form.getlist('paquete[]')
            folios_paquete = request.form.getlist('folio_paquete[]')
            
            for i, (paquete, folio) in enumerate(zip_longest(paquetes, folios_paquete, fillvalue="")):
                paquete = paquete.strip()
                folio = folio.strip()
                nivel = request.form.get(f'nivel_{i}')

                if not (paquete and folio and nivel):
                    continue

                cursor.execute(
                    """
                    INSERT INTO paquetes_informaticos (persona_id, paquete, nivel, folio)
                    VALUES (?, ?, ?, ?)
                    """,(persona_id, paquete, nivel, folio if folio else None))

            #idiomas
            idiomas = request.form.getlist('idioma[]')
            folios_idioma = request.form.getlist('folio_idioma[]')
            
            for i, (idioma, folio_idioma) in enumerate(zip_longest(idiomas, folios_idioma, fillvalue="")):
                idioma = idioma.strip()
                folio_idioma = folio_idioma.strip()
                
                lectura = 1 if request.form.get(f'lectura_{i}') else 0
                escritura = 1 if request.form.get(f'escritura_{i}') else 0
                conversacion = 1 if request.form.get(f'conversacion_{i}') else 0

                if not (idioma or folio_idioma or lectura or escritura or conversacion):
                    continue

                cursor.execute(
                        """
                        INSERT INTO idiomas (persona_id, idioma, lectura, escritura, conversacion, folio)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (persona_id, idioma, lectura, escritura, conversacion, folio_idioma if folio_idioma else None))
            
            #docencia
            anios_doc = request.form.getlist('anio_docencia[]')
            inst_doc = request.form.getlist('institucion_docencia[]')
            nombres_curso = request.form.getlist('nombre_curso[]')
            horas_doc = request.form.getlist('horas_docencia[]')
            folios_doc = request.form.getlist('folio_docencia[]')

            for anio, inst, curso, horas, folio in zip_longest(
                anios_doc, inst_doc, nombres_curso, horas_doc, folios_doc, fillvalue=""
            ):
                anio = anio.strip()
                inst = inst.strip()
                curso = curso.strip()
                horas = horas.strip()
                folio = folio.strip()

                if not (anio or inst or curso or horas or folio):
                    continue

                cursor.execute("""
                    INSERT INTO docencia (persona_id, anio, institucion, nombre_curso, duracion_horas, folio)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    persona_id,
                    int(anio) if anio.isdigit() else None,
                    inst,
                    curso,
                    int(horas) if horas.isdigit() else None,
                    folio if folio else None
                ))
            
            #referencias
            nombres_ref = request.form.getlist('nombre_ref[]')
            instituciones_ref = request.form.getlist('institucion_ref[]')
            puestos_ref = request.form.getlist('puesto_ref[]')
            telefonos_ref = request.form.getlist('telefono_ref[]')

            for nom, inst, puesto, tel in zip_longest(
                nombres_ref, instituciones_ref, puestos_ref, telefonos_ref, fillvalue=""
            ):
                nom = nom.strip()
                inst = inst.strip()
                puesto = puesto.strip()
                tel = tel.strip()

                if not (nom or inst or puesto or tel):
                    continue

                cursor.execute("""
                    INSERT INTO referencias (persona_id, nombre_apellido, institucion, puesto, telefono)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    persona_id,
                    nom,
                    inst,
                    puesto,
                    tel if tel else None
                ))

            
            #registro profesional
            nombre_registro = (request.form.get('nombre_registro') or "").strip()
            numero_registro = (request.form.get('numero_registro') or "").strip()

            if nombre_registro or numero_registro:
                cursor.execute("""
                    INSERT INTO registro_profesional (persona_id, nombre, numero_registro)
                    VALUES (?, ?, ?)
                """, (persona_id, nombre_registro, numero_registro))

            #pretension salarial
            monto_bs = (request.form.get('monto_bs') or "").strip()
            if monto_bs:
                cursor.execute("""
                    INSERT INTO pretension_salarial (persona_id, monto_bs)
                    VALUES (?, ?)
                """, (persona_id, monto_bs))

            #incopatibilidades
            cursor.execute("""
                INSERT INTO incompatibilidades (
                    persona_id, vinculacion_ministerio, otra_actividad, percibe_renta, destitucion_sentencia
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                persona_id,
                request.form.get('prg1'),
                request.form.get('prg2'),
                request.form.get('prg3'),
                request.form.get('prg4')
            ))

            #declaracion
            lugar_decl = (request.form.get('lugar_declaracion') or "").strip()
            fecha_decl = (request.form.get('fecha_declaracion') or "").strip()

            if lugar_decl or fecha_decl:
                cursor.execute("""
                    INSERT INTO declaracion_jurada (persona_id, lugar, fecha)
                    VALUES (?, ?, ?)
                """, (persona_id, lugar_decl, fecha_decl))

            conn.commit()
            
            persona, experiencia, formacion, cursos, paquetes, idiomas, docencia, referencias, registro, pretension, incompatibilidades, declaracion = obtener_datos_completos(persona_id)
            pdf_file = genera_pdf_formulario(persona, experiencia, formacion, cursos, paquetes, idiomas, docencia, referencias, registro, pretension, incompatibilidades, declaracion)
            nombre_pdf = f"FORMULARIO_HV_{persona_id}.pdf"

            flash('Formulario guardado exitosamente', 'success')

            return send_file(
                pdf_file,
                as_attachment=True,
                download_name=nombre_pdf,
                mimetype="application/pdf"
            )

    except sqlite3.IntegrityError:
        flash('El correo ya existe', 'error')
        return redirect(url_for('index'))

    except Exception as e:
        flash(f'Error al guardar: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route("/reimprimir", methods=["POST"])
def reimprimir():
    correo = (request.form.get("correo") or "").strip()

    if not correo:
        flash("Ingresa tu correo electrónico", "danger")
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    persona_row = conn.execute("SELECT * FROM datos WHERE correo = ?", (correo,)).fetchone()

    if not persona_row:
        conn.close()
        flash("No existe ningun formulario con ese correo.", "danger")
        return redirect(url_for("index"))
    
    persona_id = persona_row["id"]
    conn.close()

    persona, experiencia, formacion, cursos, paquetes, idiomas, docencia, referencias, registro, pretension, incompatibilidades, declaracion = obtener_datos_completos(persona_id)
    pdf_file = genera_pdf_formulario(persona, experiencia, formacion, cursos, paquetes, idiomas, docencia, referencias, registro, pretension, incompatibilidades, declaracion)
    nombre_pdf = f"FORMULARIO_HV_{persona_id}.pdf"

    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=nombre_pdf,
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)