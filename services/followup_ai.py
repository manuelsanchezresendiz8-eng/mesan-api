import os
import logging

USE_GPT = False
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if os.getenv("OPENAI_API_KEY"):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        USE_GPT = True
        logging.info(f"GPT followup activo: {MODEL}")
    except Exception as e:
        logging.error(f"Error OpenAI followup: {e}")


def generar_mensaje_fallback(lead, step: int) -> str:
    nombre = getattr(lead, "nombre", "")

    if step == 1:
        return f"{nombre}, detectamos posibles pérdidas en tu operación. ¿Quieres ver cómo corregirlo?"
    if step == 2:
        return f"Esto puede costarte miles al mes si no se corrige. ¿Te explico?"
    if step == 3:
        return f"Último aviso: muchas empresas corrigen esto tarde. Aún estás a tiempo. 👉 mesanomega.com"

    return "Seguimos disponibles para ayudarte."


def generar_mensaje_ia(lead, step: int) -> str:

    contexto = f"""
Empresa: {getattr(lead, 'nombre', 'N/A')}
Giro: {getattr(lead, 'giro', 'N/A')}
Empleados: {getattr(lead, 'num_empleados', 'N/A')}
Estatus: {getattr(lead, 'estatus', 'N/A')}
Seguimiento paso: {step}
"""

    prompt = f"""
Genera un mensaje corto de WhatsApp para dar seguimiento comercial.

Objetivo: que el cliente responda o compre.

Reglas:
- Maximo 60 palabras
- Directo
- Enfatiza perdida economica o riesgo
- Termina con pregunta o CTA

Contexto:
{contexto}
"""

    if USE_GPT:
        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Eres un closer experto en ventas B2B Mexico."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=120,
                timeout=15.0
            )

            msg = res.choices[0].message.content.strip()

            if len(msg) > 10:
                return msg

        except Exception as e:
            logging.error(f"GPT followup error: {e}")

    return generar_mensaje_fallback(lead, step)
