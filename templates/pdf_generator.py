from fpdf import FPDF
from io import BytesIO

# Colores
BLUE = (0, 51, 102)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def safe_text(v):
    """Convierte cualquier valor a string, evitando None"""
    if v is None:
        return ""
    return str(v)

class FormularioPDF(FPDF):
    """Clase personalizada para el PDF de hoja de vida"""
    
    def header(self):
        """Encabezado del documento"""
        self.image("static/image.png", x=12, y=8, w=40)
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'FORMULARIO HOJA DE VIDA', align='C', ln=True)
        self.ln(3)
    
    def footer(self):
        """Pie de página con número de página"""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')
    
    def section_title(self, title):
        """Título de sección con fondo azul"""
        self.set_fill_color(*BLUE)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 7, title, fill=True, ln=True)
        self.set_text_color(*BLACK)
        self.ln(1)
    
    def add_labeled_field(self, label, value, label_w, value_w, height=5):
        """Campo con etiqueta y línea para valor"""
        # Etiqueta
        self.set_font('Helvetica', 'B', 9)
        self.cell(label_w, height, label, border=0)
        
        # Valor con línea debajo
        self.set_font('Helvetica', '', 9)
        x_start = self.get_x()
        y_start = self.get_y()
        self.cell(value_w, height, safe_text(value), border=0)
        
        # Dibujar línea debajo del valor
        self.line(x_start, y_start + height, x_start + value_w, y_start + height)
    
    def check_page_break(self, height_needed):
        """Verifica si hay espacio suficiente, si no, agrega nueva página"""
        if self.get_y() + height_needed > self.page_break_trigger:
            self.add_page()
            return True
        return False

def _calc_lines(pdf, w, txt):
    """
    Calcula cuántas líneas ocupará un texto dentro de un ancho w.
    Soporta palabras largas sin espacios (ej: 'aaaaaaaaaaaa').
    """
    txt = safe_text(txt)

    if txt.strip() == "":
        return 1

    # margen interno (padding)
    usable_w = w - 2
    if usable_w <= 0:
        return 1

    lines = 0
    for paragraph in txt.split("\n"):
        if paragraph == "":
            lines += 1
            continue

        current_line = ""
        for word in paragraph.split(" "):
            if word == "":
                continue

            test = (current_line + " " + word).strip()

            # Si cabe, lo agregamos
            if pdf.get_string_width(test) <= usable_w:
                current_line = test
            else:
                # Si ya había contenido, cerramos línea
                if current_line:
                    lines += 1
                    current_line = word
                else:
                    # Palabra demasiado larga: partirla por caracteres
                    chunk = ""
                    for ch in word:
                        test2 = chunk + ch
                        if pdf.get_string_width(test2) <= usable_w:
                            chunk = test2
                        else:
                            lines += 1
                            chunk = ch
                    current_line = chunk

        if current_line:
            lines += 1

    return max(1, lines)


def row_multicell(pdf, data, widths, line_height=5, aligns=None, valign="T"):
    """
    Dibuja una fila de tabla usando multi_cell SIN que se sobreponga.
    - Mantiene ancho fijo
    - Ajusta altura según el texto más largo
    """
    if aligns is None:
        aligns = ["L"] * len(data)

    # Calcular altura máxima de la fila
    max_lines = 1
    for txt, w in zip(data, widths):
        lines = _calc_lines(pdf, w, txt)
        max_lines = max(max_lines, lines)

    row_h = max_lines * line_height

    # salto de página si no entra
    if pdf.get_y() + row_h > pdf.page_break_trigger:
        pdf.add_page()

    x_start = pdf.get_x()
    y_start = pdf.get_y()

    # Dibujar cada celda
    for i, (txt, w) in enumerate(zip(data, widths)):
        x = pdf.get_x()
        y = pdf.get_y()

        # Borde
        pdf.rect(x, y, w, row_h)

        # Ajuste vertical opcional (Top / Middle)
        text_lines = _calc_lines(pdf, w, txt)
        text_h = text_lines * line_height

        if valign == "M":
            y_text = y + (row_h - text_h) / 2
        else:
            y_text = y

        # Escribir texto dentro de la celda
        pdf.set_xy(x, y_text)
        pdf.multi_cell(w, line_height, safe_text(txt), border=0, align=aligns[i])

        # Restaurar posición para siguiente celda (a la derecha)
        pdf.set_xy(x + w, y)

    # Bajar una sola vez al final de la fila
    pdf.set_xy(x_start, y_start + row_h)

def cortar(txt, max_len=120):
    txt = safe_text(txt)
    return txt if len(txt) <= max_len else txt[:max_len] + "..."


def genera_pdf_formulario(persona, experiencia=None, formacion=None, cursos=None,
                         paquetes=None, idiomas=None, docencia=None, referencias=None,
                         registro=None, pretension=None, incompatibilidades=None, 
                         declaracion=None):
    """Genera el PDF del formulario completo"""
    
    pdf = FormularioPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # ==================== I. DATOS PERSONALES ====================
    pdf.section_title('I. DATOS PERSONALES')
    
    # Fila 1
    pdf.add_labeled_field('Nombres:', persona.get('nombres', ''), 17, 45)
    pdf.add_labeled_field('Ap. Paterno:', persona.get('ap_pat', ''), 22, 40)
    pdf.add_labeled_field('Ap. Materno:', persona.get('ap_mat', ''), 22, 40)
    pdf.ln(7)
    
    # Fila 2
    pdf.add_labeled_field('CI:', persona.get('ci', ''), 8, 54)
    pdf.add_labeled_field('Exp:', persona.get('exp', ''), 10, 53)
    pdf.add_labeled_field('Estado Civil:', persona.get('est_civil', ''), 22, 36)
    pdf.ln(7)
    
    # Fila 3
    pdf.add_labeled_field('Fecha Nac:', persona.get('fecha_nac', ''), 20, 41)
    pdf.add_labeled_field('Lugar:', persona.get('lugar', ''), 12, 53)
    pdf.add_labeled_field('Nacionalidad:', persona.get('nacio', ''), 24, 36)
    pdf.ln(7)
    
    # Fila 4
    pdf.add_labeled_field('Dirección:', persona.get('direccion', ''), 22, 95)
    pdf.add_labeled_field('Ciudad:', persona.get('ciudad', ''), 17, 50)
    pdf.ln(7)
    
    # Fila 5
    pdf.add_labeled_field('Grupo Sanguíneo:', persona.get('gr_san', ''), 30, 30)
    pdf.add_labeled_field('Tel. Celular:', persona.get('tcel', ''), 20, 40)
    pdf.add_labeled_field('Tel. Fijo:', persona.get('tfijo', ''), 17, 40)
    pdf.ln(7)

    # Fila 7
    pdf.add_labeled_field('Correo Electrónico:', persona.get('correo', ''), 32, 85)
    pdf.add_labeled_field('N° Libreta Servicio Militar:', persona.get('n_libser', ''), 43, 25)
    pdf.ln(7)

        # ==================== II. FORMACIÓN ACADÉMICA ====================
    pdf.check_page_break(40)
    pdf.section_title('II. FORMACIÓN ACADÉMICA')

    if formacion and len(formacion) > 0:
        widths = [45, 45, 50, 20, 25]

        # Encabezados
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Detalle', 'Institución', 'Grado/Título', 'Año', 'N° Folio']

        for h, w in zip(headers, widths):
            pdf.cell(w, 8, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 7)
        for f in formacion:
            row_multicell(
                pdf,
                [
                    cortar(f.get('detalle', '')),
                    cortar(f.get('institucion', '')),
                    cortar(f.get('grado', '')),
                    cortar(f.get('anio_form', '')),
                    cortar(f.get('n_folio', ''))
                ],
                widths,
                line_height=4.5,
                aligns=['L', 'L', 'L', 'C', 'C']
            )
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 8, 'Sin registros de formación académica', ln=True)

    pdf.ln(8)

    # ==================== III. EXPERIENCIA LABORAL ====================
    pdf.check_page_break(40)
    pdf.section_title('III. EXPERIENCIA LABORAL')

    if experiencia and len(experiencia) > 0:
        widths = [55, 42, 35, 53]  # deben sumar ~185

        # Encabezado
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Institución/Empresa', 'Cargo', 'Periodo', 'Motivo Retiro']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 7)
        for exp in experiencia:
            desde = safe_text(exp.get('desde', ''))
            hasta = safe_text(exp.get('hasta', ''))
            periodo = f"{desde} - {hasta}".strip(" -")

            row_multicell(
                pdf,
                [
                    exp.get('nombre', ''),
                    exp.get('puesto', ''),
                    periodo,
                    exp.get('motivo', ''),
                ],
                widths,
                line_height=4,
                aligns=['L', 'L', 'C', 'L']
            )
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 8, 'Sin registros de experiencia laboral', ln=True)

    pdf.ln(8)

    # ==================== IV. CURSOS Y CAPACITACIONES ====================
    if cursos and len(cursos) > 0:
        pdf.check_page_break(40)
        pdf.section_title('IV. CURSOS Y CAPACITACIONES')

        widths = [15, 38, 50, 57, 25]

        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Año', 'Área', 'Institución', 'Nombre Capacitación', 'Horas']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_font('Helvetica', '', 7)
        for c in cursos:
            row_multicell(
                pdf,
                [
                    safe_text(c.get('anio_curso', '')),
                    safe_text(c.get('area_capacitacion', '')),
                    safe_text(c.get('institucion', '')),
                    safe_text(c.get('nombre_capacitacion', '')),
                    safe_text(c.get('duracion_horas', ''))
                ],
                widths,
                line_height=3.8,
                aligns=['C', 'L', 'L', 'L', 'C']
            )

        pdf.ln(8)
    
    # ==================== V. PAQUETES INFORMÁTICOS ====================
    if paquetes and len(paquetes) > 0:
        pdf.check_page_break(40)
        pdf.section_title('V. CONOCIMIENTO DE PAQUETES INFORMÁTICOS')

        widths = [65, 45, 75]

        # Encabezado
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Paquete', 'Nivel', 'N° Folio']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 8)
        for p in paquetes:
            nivel = safe_text(p.get('nivel', ''))
            if nivel == 'muy_bueno':
                nivel = 'Muy Bueno'
            elif nivel == 'bueno':
                nivel = 'Bueno'
            elif nivel == 'regular':
                nivel = 'Regular'

            row_multicell(
                pdf,
                [
                    p.get('paquete', ''),
                    nivel,
                    p.get('folio', '')
                ],
                widths,
                line_height=4,
                aligns=['L', 'C', 'C']
            )

        pdf.ln(8)

    # ==================== VI. IDIOMAS ====================
    if idiomas and len(idiomas) > 0:
        pdf.check_page_break(40)
        pdf.section_title('VI. IDIOMAS')

        widths = [50, 30, 30, 30, 35]

        # Encabezado
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Idioma', 'Lectura', 'Escritura', 'Conversación', 'N° Folio']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 8)
        for i in idiomas:
            row_multicell(
                pdf,
                [
                    i.get('idioma', ''),
                    'Sí' if i.get('lectura') else 'No',
                    'Sí' if i.get('escritura') else 'No',
                    'Sí' if i.get('conversacion') else 'No',
                    i.get('folio', '')
                ],
                widths,
                line_height=4,
                aligns=['L', 'C', 'C', 'C', 'C']
            )

        pdf.ln(8)
    
    # ==================== VII. DOCENCIA ====================
    if docencia and len(docencia) > 0:
        pdf.check_page_break(40)
        pdf.section_title('VII. DOCENCIA')

        widths = [15, 55, 65, 25, 25]

        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Año', 'Institución', 'Nombre del Curso', 'Horas', 'N° Folio']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_font('Helvetica', '', 7)
        for d in docencia:
            row_multicell(
                pdf,
                [
                    d.get('anio_doc', ''),
                    d.get('institucion', ''),
                    d.get('nombre_curso', ''),
                    d.get('duracion_horas', ''),
                    d.get('folio', '')
                ],
                widths,
                line_height=4,
                aligns=['C', 'L', 'L', 'C', 'C']
            )

        pdf.ln(8)

    # ==================== VIII. REFERENCIAS ====================
    if referencias and len(referencias) > 0:
        pdf.check_page_break(40)
        pdf.section_title('VIII. REFERENCIAS PERSONALES')

        widths = [55, 50, 45, 35]

        # Encabezado
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        headers = ['Nombre y Apellido', 'Institución', 'Puesto', 'Teléfono']

        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 8)
        for r in referencias:
            row_multicell(
                pdf,
                [
                    r.get('nombre_apellido', ''),
                    r.get('institucion', ''),
                    r.get('puesto', ''),
                    r.get('telefono', '')
                ],
                widths,
                line_height=4,
                aligns=['L', 'L', 'L', 'C']
            )

        pdf.ln(8)

    
    # ==================== IX. REGISTRO PROFESIONAL ====================
    if registro:
        pdf.check_page_break(25)
        pdf.section_title('IX. REGISTRO PROFESIONAL')
        pdf.add_labeled_field('Nombre:', registro.get('nombre', ''), 20, 80)
        pdf.ln(7)
        pdf.add_labeled_field('Número de Registro:', registro.get('numero_registro', ''), 40, 60)
        pdf.ln(10)
    
    # ==================== X. PRETENSIÓN SALARIAL ====================
    if pretension:
        pdf.check_page_break(20)
        pdf.section_title('X. PRETENSIÓN SALARIAL')
        pdf.add_labeled_field('Monto en Bs.:', pretension.get('monto_bs', ''), 30, 50)
        pdf.ln(10)
    
    # ==================== XI. INCOMPATIBILIDADES ====================
    if incompatibilidades:
        pdf.check_page_break(50)
        pdf.section_title('XI. INCOMPATIBILIDADES')
        
        pdf.set_font('Helvetica', '', 9)
        
        vinc = incompatibilidades.get('vinculacion_ministerio', '')
        pdf.add_labeled_field('¿Tiene vinculación con el Ministerio de Culturas?', 
                            'SÍ' if vinc == 'si' else 'NO', 105, 25)
        pdf.ln(7)
        
        otra = incompatibilidades.get('otra_actividad', '')
        pdf.add_labeled_field('¿Realiza otra actividad remunerada?', 
                            'SÍ' if otra == 'si' else 'NO', 105, 25)
        pdf.ln(7)
        
        renta = incompatibilidades.get('percibe_renta', '')
        pdf.add_labeled_field('¿Percibe renta de jubilación o pensión?', 
                            'SÍ' if renta == 'si' else 'NO', 105, 25)
        pdf.ln(7)
        
        destit = incompatibilidades.get('destitucion_sentencia', '')
        pdf.add_labeled_field('¿Ha sido destituido o tiene sentencia ejecutoriada?', 
                            'SÍ' if destit == 'si' else 'NO', 105, 25)
        pdf.ln(10)
    
    # ==================== XII. DECLARACIÓN JURADA ====================
    if declaracion:
        pdf.check_page_break(60)
        pdf.section_title('XII. DECLARACIÓN JURADA')
        
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, 
            'Declaro bajo juramento que los datos consignados en el presente formulario '
            'son verdaderos y exactos, sometiéndome a las sanciones que establece la ley '
            'en caso de falsedad o inexactitud.')
        pdf.ln(5)
        
        pdf.add_labeled_field('Lugar:', declaracion.get('lugar', ''), 18, 60)
        pdf.add_labeled_field('Fecha:', declaracion.get('fecha', ''), 18, 50)
        pdf.ln(20)
        
        pdf.cell(0, 5, '________________________________', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 5, 'Firma del Postulante', align='C', ln=True)
    
    # Generar output
    pdf_output = BytesIO()
    pdf_bytes = pdf.output()
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output