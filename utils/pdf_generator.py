from fpdf import FPDF
from datetime import datetime

class PDFDiagnostico(FPDF):

    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "MESAN Ω — Diagnóstico Estratégico", 0, 1, "R")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")


def generar_diagnostico_pdf(
    nombre,
    empresa,
    riesgo,
    impacto_min,
    impacto_max,
    causas,
    contexto,
    respuestas_usuario=None
):

    pdf = PDFDiagnostico()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "DIAGNÓSTICO EMPRESARIAL", 0, 1)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Empresa: {empresa}", 0, 1)
    pdf.cell(0, 8, f"Responsable: {nombre}", 0, 1)
    pdf.cell(0, 8, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Resumen Ejecutivo", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7,
        f"Se detecta un nivel de riesgo {riesgo} en la operación actual. "
        f"El impacto económico estimado oscila entre ${impacto_min:,} y ${impacto_max:,} MXN."
    )
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Contexto Detectado", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, contexto)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Hallazgos Clave", 0, 1)
    pdf.set_font("Arial", "", 11)
    for c in causas:
        pdf.multi_cell(0, 6, f"- {c}")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Impacto Económico", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7,
        f"Escenario conservador: ${impacto_min:,} MXN\n"
        f"Escenario probable: ${(impacto_min + impacto_max)//2:,} MXN\n"
        f"Escenario crítico: ${impacto_max:,} MXN"
    )
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Plan de Acción (30 Días)", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7,
        "Fase 1: Contención inmediata\n"
        "Fase 2: Regularización operativa\n"
        "Fase 3: Ajuste fiscal\n"
        "Fase 4: Implementación de controles"
    )
    pdf.ln(5)

    if respuestas_usuario:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Información Proporcionada", 0, 1)
        pdf.set_font("Arial", "", 11)
        for r in respuestas_usuario:
            pdf.multi_cell(0, 6, f"- {r}")
        pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Implementación Recomendada", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7,
        "MESAN Ω puede ejecutar el proceso de regularización completo en 30 días.\n"
        "Incluye regularización técnica, corrección documental y estrategia fiscal."
    )
    pdf.ln(8)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Siguiente Paso", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7,
        "Para implementar la solución completa, agende una sesión estratégica con MESAN Ω."
    )

    return pdf.output(dest="S").encode("latin-1")

    
