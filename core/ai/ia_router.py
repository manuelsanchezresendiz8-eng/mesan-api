# core/ai/ai_router.py -- MESAN Omega AI Router v1.1
import os, logging
from typing import Dict, Optional
from core.ai.anthropic_client import AnthropicClient, MesanAIException

logger = logging.getLogger("mesan.ai.router")

class AIRouter:
    VERSION = "1.1.0"

    def __init__(self):
        self.client      = AnthropicClient()
        self._prompts:   Dict[str, str] = {}
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")

    def load_prompt(self, name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise MesanAIException("Prompt name invalid.")
        name = name.strip()
        if name in self._prompts: return self._prompts[name]
        path = os.path.join(self.prompts_dir, f"{name}.txt")
        if not os.path.exists(path):
            logger.warning(f"[AI_ROUTER] Prompt not found: {name}")
            self._prompts[name] = ""; return ""
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read().strip()
            if not content: logger.warning(f"[AI_ROUTER] Empty prompt: {name}")
            self._prompts[name] = content
            return content
        except Exception as e:
            logger.error(f"[AI_ROUTER] Failed loading prompt {name}: {e}")
            raise MesanAIException(f"Could not load prompt: {name}")

    def _compose_prompt(self, system_prompt: str, context: str) -> str:
        if not isinstance(context, str): raise MesanAIException("Context must be string.")
        context = context.strip()
        if not context: raise MesanAIException("Context cannot be empty.")
        return f"{system_prompt}\n\n{context}"

    async def executive(self, context: str, tenant_id: str, trace_id: str,
                        correlation_id: Optional[str] = None) -> dict:
        try:
            prompt = self._compose_prompt(self.load_prompt("executive_prompt"), context)
            logger.info("[AI_ROUTER] executive", extra={"tenant_id":tenant_id,"trace_id":trace_id})
            return await self.client.generate(prompt=prompt, tenant_id=tenant_id,
                                              trace_id=trace_id, correlation_id=correlation_id)
        except Exception as e:
            logger.error(f"[AI_ROUTER] executive failed: {e}")
            return {"response": "MESAN executive narrative temporarily unavailable.",
                    "fallback": True, "confidence": 0, "error": str(e),
                    "tenant_id": tenant_id, "trace_id": trace_id}

    async def contradiction(self, data: str, tenant_id: str, trace_id: str,
                            correlation_id: Optional[str] = None) -> dict:
        try:
            prompt = self._compose_prompt(self.load_prompt("contradiction_prompt"), data)
            logger.info("[AI_ROUTER] contradiction", extra={"tenant_id":tenant_id,"trace_id":trace_id})
            return await self.client.generate(prompt=prompt, tenant_id=tenant_id,
                                              trace_id=trace_id, correlation_id=correlation_id)
        except Exception as e:
            logger.error(f"[AI_ROUTER] contradiction failed: {e}")
            return {"response": "MESAN contradiction analysis temporarily unavailable.",
                    "fallback": True, "confidence": 0, "error": str(e),
                    "tenant_id": tenant_id, "trace_id": trace_id}

    def clear_prompt_cache(self):
        self._prompts.clear()
        logger.info("[AI_ROUTER] Prompt cache cleared.")
