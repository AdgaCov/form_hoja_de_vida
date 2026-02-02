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


def genera_pdf_detalles(persona, experiencia=None, resumen=None):
    """Genera PDF simplificado con datos personales y experiencia"""
    
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
        # Encabezados
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(55, 7, 'Institución/Empresa', border=1, fill=True, align='C')
        pdf.cell(42, 7, 'Cargo', border=1, fill=True, align='C')
        pdf.cell(35, 7, 'Periodo', border=1, fill=True, align='C')
        pdf.cell(53, 7, 'Motivo Retiro', border=1, fill=True, align='C', ln=True)
        
        # Filas
        pdf.set_font('Helvetica', '', 7)
        for exp in experiencia:
            nombre = safe_text(exp.get('nombre', ''))[:45]
            puesto = safe_text(exp.get('puesto', ''))[:30]
            desde = safe_text(exp.get('desde', ''))
            hasta = safe_text(exp.get('hasta', ''))
            periodo = f"{desde} - {hasta}" if desde or hasta else ""
            motivo = safe_text(exp.get('motivo', ''))[:40]
            
            pdf.cell(55, 10, nombre, border=1)
            pdf.cell(42, 10, puesto, border=1)
            pdf.cell(35, 10, periodo, border=1, align='C')
            pdf.cell(53, 10, motivo, border=1, ln=True)
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