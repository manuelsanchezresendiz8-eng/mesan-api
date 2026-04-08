from fpdf import FPDF

def generar_pdf(nombre, score, clasificacion, impacto_min, impacto_max, soluciones):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "DIAGNOSTICO EMPRESARIAL MESAN-OMEGA", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Empresa: {nombre}", ln=True)
    pdf.cell(0, 10, f"Score de Riesgo: {score}", ln=True)
    pdf.cell(0, 10, f"Clasificacion: {clasificacion}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Impacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "PLAN DE ACCION:", ln=True)
    pdf.set_font("Arial", "", 11)

    for s in soluciones:
        pdf.multi_cell(0, 8, f"- {s['area']}: {s['accion']}")

    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 6, "Este diagnostico es una estimacion basada en la informacion proporcionada y no sustituye una auditoria formal. MESAN-Omega.")

    filename = f"/tmp/diagnostico_{nombre.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename
