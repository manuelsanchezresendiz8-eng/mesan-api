from fpdf import FPDF

class PDF(FPDF):

    def portada(self, nombre):
        self.add_page()
        self.set_font("Arial", "B", 28)
        self.cell(0, 40, "", ln=True)
        self.cell(0, 15, "MESAN Omega", ln=True, align="C")
        self.set_font("Arial", "", 12)
        self.cell(0, 10, "Inteligencia Financiera y Fiscal", ln=True, align="C")
        self.ln(30)
        self.set_font("Arial", "B", 18)
        self.multi_cell(0, 10, "Reporte Ejecutivo de Diagnostico Empresarial", align="C")
        self.ln(20)
        self.set_font("Arial", "", 11)
        self.cell(0, 8, f"Cliente: {nombre}", ln=True, align="C")
        self.ln(40)
        self.set_font("Arial", "I", 9)
        self.cell(0, 6, "Confidencial", align="C")

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, "MESAN Omega", ln=True)
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, f"Pagina {self.page_no()} | mesanomega.com", align="C")


def generar_diagnostico_pdf(
    nombre, email, telefono,
    score, clasificacion,
    soluciones,
    impacto_min, impacto_max,
    finanzas=None,
    precio_sugerido=None
):
    pdf = PDF()

    pdf.portada(nombre)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Resumen Ejecutivo", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(
        0, 6,
        "El presente analisis evalua la situacion operativa, fiscal y financiera de la empresa, "
        "identificando riesgos potenciales y oportunidades de optimizacion.\n\n"
        "El objetivo es proporcionar claridad en la toma de decisiones y proteger la rentabilidad."
    )
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Indicadores Clave", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Score de riesgo: {score}", ln=True)
    pdf.cell(0, 6, f"Clasificacion: {clasificacion}", ln=True)
    pdf.cell(0, 6, f"Exposicion economica estimada: ${impacto_min:,} - ${impacto_max:,} MXN", ln=True)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Hallazgos y Riesgos Detectados", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    for s in soluciones:
        texto = s if isinstance(s, str) else f"{s.get('area','')} - {s.get('accion','')}"
        pdf.multi_cell(0, 6, f"- {texto}")
        pdf.ln(1)

    if finanzas:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Impacto Financiero", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Costo real por empleado: ${finanzas['costo_empleado']:,}", ln=True)
        pdf.cell(0, 6, f"Costo total operativo: ${finanzas['costo_total']:,}", ln=True)
        pdf.cell(0, 6, f"Ingreso actual: ${finanzas['ingreso']:,}", ln=True)
        pdf.cell(0, 6, f"Utilidad estimada: ${finanzas['utilidad']:,}", ln=True)
        pdf.cell(0, 6, f"Margen operativo: {round(finanzas['margen']*100,1)}%", ln=True)

    if precio_sugerido:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Recomendacion Estrategica", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(
            0, 6,
            f"Se recomienda ajustar el precio por elemento a aproximadamente "
            f"${precio_sugerido:,} MXN.\n\n"
            "Este ajuste permite mantener un margen operativo saludable, "
            "proteger la rentabilidad y evitar presion competitiva basada en precio."
        )

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Conclusion y Siguiente Paso", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(
        0, 6,
        "El analisis confirma la existencia de riesgos operativos y financieros que requieren atencion.\n\n"
        "La implementacion de las recomendaciones propuestas permite optimizar costos, "
        "reducir exposicion y mejorar la rentabilidad del negocio.\n\n"
        "MESAN Omega ofrece acompanamiento en la ejecucion de estas estrategias."
    )
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 6, "Agenda una sesion estrategica:\nWhatsApp: +52 686 162 9643")

    return bytes(pdf.output())
