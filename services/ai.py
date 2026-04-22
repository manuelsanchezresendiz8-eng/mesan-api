# services/ai.py

import os
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


if not OPENAI_API_KEY:

    def analyze_ai(text: str) -> str:
        logging.warning("IA no disponible — falta OPENAI_API_KEY")
        return "IA no disponible"

    def consultor_mesan(datos: dict, request_id: str = "") -> str:
        return "IA no disponible"

else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        def analyze_ai(text: str) -> str:
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Eres un auditor fiscal experto en Mexico. Analiza el riesgo empresarial."},
                        {"role": "user", "content": text}
                    ],
                    max_tokens=300
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.error(f"Error OpenAI: {e}")
                return "Error en analisis IA"

        def consultor_mesan(datos: dict, request_id: str = "") -> str:
            prompt = f"""
Analiza el siguiente caso empresarial:

Datos: {datos}

Responde con:
1. Nivel de riesgo (CRITICO/ALTO/MEDIO/BAJO)
2. Principal problema detectado
3. Accion inmediata recomendada
"""
            return analyze_ai(prompt)

    except Exception as e:
        logging.error(f"Error importando OpenAI: {e}")

        def analyze_ai(text: str) -> str:
            return "IA no disponible"

        def consultor_mesan(datos: dict, request_id: str = "") -> str:
            return "IA no disponible"

# v2 — actualizado
