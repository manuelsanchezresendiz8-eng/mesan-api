# core/ai/local_llm_adapter.py v1.0
import os
class LocalLLMAdapter:
    def __init__(self):self.version="1.0.0";self._provider=self._detect()
    def _detect(self):
        if os.getenv("ANTHROPIC_API_KEY"):return"claude"
        if os.getenv("OPENAI_API_KEY"):return"openai"
        return"deterministic"
    def ask(self,prompt):
        p=prompt.lower()
        if "riesgo" in p:return{"response":"Se recomienda ejecutar un diagnostico completo.","provider":"deterministic"}
        return{"response":"MESAN Omega esta disponible para analizar su empresa.","provider":"deterministic"}
    def get_status(self):return{"version":self.version,"provider":self._provider}
local_llm=LocalLLMAdapter()