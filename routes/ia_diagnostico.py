async def llamar_anthropic(
    texto,
    industria,
    impacto,
    riesgo,
    causas,
    modo="NORMAL"
):

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logging.error("ANTHROPIC_API_KEY no configurada")
        return ""

    fecha = datetime.now().strftime("%d %B %Y")

    causas_txt = " | ".join(causas[:4])

    impacto_bajo = int(impacto * 0.45)
    impacto_probable = int(impacto * 0.75)
    impacto_critico = int(impacto)

    prompt = f"""
Actua como CRO (Chief Restructuring Officer) y War-Room Advisor.

Fecha: {fecha}
Industria: {industria}
Modo: {modo}
Nivel de Riesgo: {riesgo}

Situacion:
{texto}

Factores Detectados:
{causas_txt}

ESCENARIOS FINANCIEROS:
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

REGLAS:
- MAXIMO 70 palabras por seccion
- NO usar tablas markdown
- NO cortar frases
- NO usar recomendaciones genericas
- TODAS las acciones deben incluir:
  accion + objetivo + plazo
- NO usar:
  "monitorear"
  "evaluar opciones"
  "dar seguimiento"
  "revisar continuamente"

ESTRUCTURA OBLIGATORIA:

## 1. HALLAZGO CRITICO
[2 lineas maximo]

## 2. RIESGO DE CONTINUIDAD
[impacto operativo inmediato]

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

## 4. VENTANA DE COLAPSO OPERATIVO
[fechas y consecuencias]

## 5. ACCIONES EJECUTIVAS PRIORITARIAS

🔴 ACCION 24H
- Ejecutar:
- Objetivo:
- Plazo:

🟠 ACCION 72H
- Ejecutar:
- Objetivo:
- Plazo:

🟡 ACCION SEMANA 1
- Ejecutar:
- Objetivo:
- Plazo:

## 6. PROTOCOLO DE SUPERVIVENCIA
- Priorizar:
- Suspender:
- Proteger:
- Riesgo embargo:

## 7. DECISION CEO
[orden ejecutiva final]

Analisis referencial sujeto a validacion especializada.
"""

    try:

        async with httpx.AsyncClient(timeout=45) as client:

            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )

            if response.status_code == 200:

                data = response.json()

                respuesta = data["content"][0]["text"]

                # VALIDADORES DE RESPUESTA

                if len(respuesta) < 300:
                    logging.error("Respuesta demasiado corta")
                    return "Error de convergencia ejecutiva."

                if "## 5." not in respuesta:
                    logging.error("Respuesta incompleta")
                    return "Respuesta incompleta."

                if respuesta.count("##") < 5:
                    logging.error("Estructura insuficiente")
                    return "Estructura insuficiente."

                return respuesta

            logging.error(f"Claude Error: {response.text}")

    except Exception:
        logging.error(traceback.format_exc())

    return ""
