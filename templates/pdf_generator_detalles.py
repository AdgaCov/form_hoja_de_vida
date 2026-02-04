from fpdf import FPDF
from io import BytesIO
import json

# Colores
BLUE = (0, 51, 102)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_RED = (255, 230, 230)
RED = (255, 0, 0) 

def safe_text(v):
    """Convierte cualquier valor a string, evitando None"""
    if v is None:
        return ""
    return str(v)

class DetallesPDF(FPDF):
    """Clase para PDF simplificado de detalles"""
    
    def header(self):
        """Encabezado del documento"""
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'HOJA DE VIDA - RESUMEN', align='C', ln=True)
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
        self.set_font('Helvetica', 'B', 9)
        self.cell(label_w, height, label, border=0)
        
        self.set_font('Helvetica', '', 9)
        x_start = self.get_x()
        y_start = self.get_y()
        self.cell(value_w, height, safe_text(value), border=0)
        
        self.line(x_start, y_start + height, x_start + value_w, y_start + height)

def _calc_lines(pdf, w, txt):
    """
    Calcula cuántas líneas ocupará un texto dentro de un ancho w.
    Soporta palabras largas sin espacios.
    """
    txt = safe_text(txt)

    if txt.strip() == "":
        return 1

    usable_w = w - 2  # padding interno
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

            if pdf.get_string_width(test) <= usable_w:
                current_line = test
            else:
                if current_line:
                    lines += 1
                    current_line = word
                else:
                    # palabra muy larga: partir por caracteres
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


def row_multicell(pdf, data, widths, line_height=4.5, aligns=None, fill=False, fill_color=(255,255,255), text_color=(0,0,0)):
    """
    Dibuja una fila tipo tabla usando multi_cell sin superposición.
    - respeta ancho fijo
    - altura dinámica según celda más grande
    """
    if aligns is None:
        aligns = ["L"] * len(data)

    # calcular altura máxima
    max_lines = 1
    for txt, w in zip(data, widths):
        max_lines = max(max_lines, _calc_lines(pdf, w, txt))

    row_h = max_lines * line_height

    # salto de página si no entra
    if pdf.get_y() + row_h > pdf.page_break_trigger:
        pdf.add_page()

    x_start = pdf.get_x()
    y_start = pdf.get_y()

    # estilos
    pdf.set_fill_color(*fill_color)
    pdf.set_text_color(*text_color)

    for i, (txt, w) in enumerate(zip(data, widths)):
        x = pdf.get_x()
        y = pdf.get_y()

        # borde + fondo
        if fill:
            pdf.rect(x, y, w, row_h, style="DF")
        else:
            pdf.rect(x, y, w, row_h)

        # texto
        pdf.set_xy(x, y)
        pdf.multi_cell(w, line_height, safe_text(txt), border=0, align=aligns[i])

        # volver arriba y avanzar a la derecha
        pdf.set_xy(x + w, y)

    # bajar una sola vez al final
    pdf.set_xy(x_start, y_start + row_h)

    # devolver info útil por si quieres tachar o pintar
    return x_start, y_start, sum(widths), row_h

def genera_pdf_detalles(persona, experiencia=None, resumen=None, ids_marcados=None):
    """Genera PDF simplificado con datos personales y experiencia"""
    
    # Procesar ids_marcados
    if ids_marcados:
        if isinstance(ids_marcados, str):
            try:
                ids_marcados = json.loads(ids_marcados)
            except:
                ids_marcados = []
        # Asegurar que todos sean enteros
        ids_marcados = [int(id) for id in ids_marcados if id is not None]
    else:
        ids_marcados = []

    pdf = DetallesPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # ==================== I. DATOS PERSONALES ====================
    pdf.section_title('I. DATOS PERSONALES')
    
    # Fila 1
    pdf.add_labeled_field('Nombres:', persona.get('nombres', ''), 20, 55)
    pdf.add_labeled_field('Ap. Paterno:', persona.get('ap_pat', ''), 23, 45)
    pdf.add_labeled_field('Ap. Materno:', persona.get('ap_mat', ''), 23, 45)
    pdf.ln(7)
    
    # Fila 2
    pdf.add_labeled_field('CI:', persona.get('ci', ''), 8, 35)
    pdf.add_labeled_field('Exp:', persona.get('exp', ''), 10, 18)
    pdf.add_labeled_field('Estado Civil:', persona.get('est_civil', ''), 25, 50)
    pdf.ln(7)
    
    # Fila 3
    pdf.add_labeled_field('Fecha Nac:', persona.get('fecha_nac', ''), 25, 35)
    pdf.add_labeled_field('Lugar:', persona.get('lugar', ''), 15, 45)
    pdf.add_labeled_field('Nacionalidad:', persona.get('nacio', ''), 27, 40)
    pdf.ln(7)
    
    # Fila 4
    pdf.add_labeled_field('Dirección:', persona.get('direccion', ''), 22, 95)
    pdf.add_labeled_field('Ciudad:', persona.get('ciudad', ''), 17, 50)
    pdf.ln(7)
    
    # Fila 5
    pdf.add_labeled_field('Grupo Sanguíneo:', persona.get('gr_san', ''), 38, 20)
    pdf.ln(7)
    
    # Fila 6
    pdf.add_labeled_field('Tel. Celular:', persona.get('tcel', ''), 27, 40)
    pdf.add_labeled_field('Tel. Fijo:', persona.get('tfijo', ''), 20, 40)
    pdf.ln(7)
    
    # Fila 7
    pdf.add_labeled_field('Correo Electrónico:', persona.get('correo', ''), 40, 145)
    pdf.ln(7)
    
    # Fila 8
    pdf.add_labeled_field('N° Libreta Servicio Militar:', persona.get('n_libser', ''), 60, 60)
    pdf.ln(10)
    
    # ==================== III. EXPERIENCIA LABORAL ====================
    pdf.section_title('III. EXPERIENCIA LABORAL')

    if experiencia and len(experiencia) > 0:
        widths = [55, 42, 35, 53]
        headers = ['Institución/Empresa', 'Cargo', 'Periodo', 'Motivo Retiro']

        # Encabezados
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        for h, w in zip(headers, widths):
            pdf.cell(w, 7, h, border=1, fill=True, align='C')
        pdf.ln()

        # Filas
        pdf.set_font('Helvetica', '', 7)

        for exp in experiencia:
            exp_id = exp.get('id')

            nombre = safe_text(exp.get('nombre', ''))
            puesto = safe_text(exp.get('puesto', ''))
            desde = safe_text(exp.get('desde', ''))
            hasta = safe_text(exp.get('hasta', ''))
            periodo = f"{desde} - {hasta}" if desde or hasta else ""
            motivo = safe_text(exp.get('motivo', ''))

            # Verificar si está marcada
            esta_marcada = True
            if ids_marcados is not None and len(ids_marcados) > 0:
                esta_marcada = exp_id in ids_marcados

            # estilos normales o desmarcada
            if esta_marcada:
                fill = False
                fill_color = (255, 255, 255)
                text_color = (0, 0, 0)
            else:
                fill = True
                fill_color = LIGHT_RED
                text_color = (153, 0, 0)

            # dibujar fila dinámica
            x, y, w_total, h_total = row_multicell(
                pdf,
                [nombre, puesto, periodo, motivo],
                widths,
                line_height=4.5,
                aligns=['L', 'L', 'C', 'L'],
                fill=fill,
                fill_color=fill_color,
                text_color=text_color
            )

            # si NO marcada: tachado centrado dentro de la fila completa
            if not esta_marcada:
                linea_y = y + (h_total / 2)

                pdf.set_draw_color(153, 0, 0)
                pdf.set_line_width(0.7)
                pdf.line(x + 1, linea_y, x + w_total - 1, linea_y)

                # restaurar estilos
                pdf.set_draw_color(0, 0, 0)
                pdf.set_text_color(0, 0, 0)
                pdf.set_line_width(0.2)

    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 8, 'Sin registros de experiencia laboral', ln=True)

    pdf.ln(8)

    # ==================== RESUMEN DE EXPERIENCIA ====================
    if resumen:
        pdf.set_fill_color(227, 242, 253)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'RESUMEN DE EXPERIENCIA LABORAL', fill=True, ln=True, border=1)
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(95, 8, f'Total de Años: {resumen.get("total_anios", 0)}', border=1, align='C')
        pdf.cell(90, 8, f'Total de Meses: {resumen.get("total_meses", 0)}', border=1, align='C', ln=True)
        
        pdf.set_font('Helvetica', 'I', 8)
        pdf.ln(2)
        pdf.cell(0, 5, f'Fecha de cálculo: {resumen.get("fecha_calculo", "")}', align='C', ln=True)
    
    # Generar output
    pdf_output = BytesIO()
    pdf_bytes = pdf.output()
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output