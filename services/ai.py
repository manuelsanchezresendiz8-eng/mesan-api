import os
from config.settings import settings

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    def analyze_ai(text: str) -> str:
        return "Analisis no disponible — OpenAI no configurado."
else:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    def analyze_ai(text: str) -> str:
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Eres MESAN Omega. Auditor fiscal y laboral experto en Mexico. Sé directo y conciso."},
                    {"role": "user", "content": text[:5000]}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error en analisis IA: {str(e)}"
