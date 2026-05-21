# app/services/jarvis_core.py
import os
import httpx
from fastapi import HTTPException

class JarvisCore:
    def __init__(self):
        self.base_url   = os.getenv("JARVIS_LLM_URL", "http://localhost:11434/v1")
        self.model_name = os.getenv("JARVIS_MODEL", "llama3:8b")
        self.headers    = {"Authorization": f"Bearer {os.getenv('JARVIS_API_KEY', 'local_secret')}"}

    async def ejecutar_comando(self, prompt_sistema: str, prompt_usuario: str, temperatura: float = 0.2) -> dict:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user",   "content": prompt_usuario}
            ],
            "temperature": temperatura,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=60.0) as cliente:
            try:
                r = await cliente.post(f"{self.base_url}/chat/completions", json=payload, headers=self.headers)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"Error Jarvis Core: {e.response.text}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Falla Jarvis: {str(e)}")
