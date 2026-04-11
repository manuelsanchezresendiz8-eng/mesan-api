from fpdf import FPDF

def generar_diagnostico_pdf(
    nombre,
    email,
    telefono,
    score,
    clasificacion,
    soluciones,
    impacto_min,
    impacto_max
):
    pdf = FPDF()
    pdf.add_page()

    impacto_min = impacto_min or 0
    impacto_max = impacto_max or 0
    soluciones = soluciones or []

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="MESAN Omega - Reporte de Diagnostico", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Sistema de Inteligencia Empresarial", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Datos del Cliente", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt="Nombre: " + (nombre or "N/D"), ln=True)
    pdf.cell(0, 8, txt="Email: " + (email or "N/D"), ln=True)
    pdf.cell(0, 8, txt="Telefono: " + (telefono or "N/D"), ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Resultado del Diagnostico", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt="Score de Riesgo: " + str(score), ln=True)
    pdf.cell(0, 8, txt="Clasificacion: " + str(clasificacion), ln=True)
    pdf.cell(0, 8, txt="Exposicion estimada: $" + "{:,.0f}".format(impacto_min) + " - $" + "{:,.0f}".format(impacto_max) + " MXN", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Areas de Atencion Detectadas", ln=True)
    pdf.set_font("Arial", size=11)

    if not soluciones:
        pdf.cell(0, 8, txt="Sin observaciones registradas", ln=True)
    else:
        for s in soluciones:
            if isinstance(s, str):
                texto = s
            else:
                texto = s.get("area", "") + " - " + s.get("accion", "")
            pdf.multi_cell(0, 8, txt="* " + texto)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 10, txt="Documento generado automaticamente por MESAN-Omega | mesanomega.com", align='C')

    return pdf.output(dest='S').encode('latin-1')
