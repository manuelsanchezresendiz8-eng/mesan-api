# core/ai/anthropic_client.py -- MESAN Omega AI Infrastructure v1.2
import os, httpx, logging, asyncio, time
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("mesan.ai")

# ============================================================
# EXCEPTIONS
# ============================================================

class MesanAIException(Exception): pass
class AITimeoutException(MesanAIException): pass
class AIRateLimitException(MesanAIException): pass
class AIProviderException(MesanAIException): pass

# ============================================================
# CONFIG
# ============================================================

MAX_PROMPT_CHARS  = int(os.getenv("AI_MAX_PROMPT_CHARS",        "12000"))
MAX_TOKENS        = int(os.getenv("AI_MAX_TOKENS",               "1400"))
CIRCUIT_THRESHOLD = int(os.getenv("AI_CIRCUIT_THRESHOLD",        "5"))
CIRCUIT_RESET_SEC = int(os.getenv("AI_CIRCUIT_RESET_SECONDS",    "60"))

CONFIDENCE_BY_ATTEMPT = {1: 0.92, 2: 0.80, 3: 0.65}

# ============================================================
# CLIENT
# ============================================================

class AnthropicClient:

    VERSION = "1.2.0"

    def __init__(self):
        self.api_key        = os.getenv("ANTHROPIC_API_KEY")
        self.model          = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
        self.timeout        = int(os.getenv("AI_TIMEOUT", "20"))
        self.max_retries    = int(os.getenv("AI_MAX_RETRIES", "3"))
        self.url            = "https://api.anthropic.com/v1/messages"
        self.prompt_version = "v1.2"

        self._failures          = 0
        self._breaker_open      = False
        self._breaker_opened_at: Optional[float] = None
        self._tokens_consumed   = 0

        if not self.api_key:
            logger.warning("[AI] ANTHROPIC_API_KEY missing — degraded mode enabled.")

    # ====================================================
    # CIRCUIT BREAKER
    # ====================================================

    def _check_circuit(self):
        if not self._breaker_open: return
        elapsed = time.time() - (self._breaker_opened_at or 0)
        if elapsed >= CIRCUIT_RESET_SEC:
            self._breaker_open = False; self._failures = 0
            logger.info("[AI] Circuit breaker reset.")
        else:
            raise AIProviderException(f"Circuit breaker OPEN. Retry in {int(CIRCUIT_RESET_SEC-elapsed)}s.")

    def _record_failure(self):
        self._failures += 1
        if self._failures >= CIRCUIT_THRESHOLD:
            self._breaker_open = True; self._breaker_opened_at = time.time()
            logger.error("[AI] Circuit breaker OPEN.")

    def _record_success(self): self._failures = 0

    # ====================================================
    # SANITIZATION
    # ====================================================

    def _sanitize_prompt(self, prompt: str) -> str:
        if not isinstance(prompt, str): raise MesanAIException("Prompt must be a string.")
        prompt = prompt.strip()
        if not prompt: raise MesanAIException("Prompt cannot be empty.")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise MesanAIException(f"Prompt exceeds MAX_PROMPT_CHARS={MAX_PROMPT_CHARS}")
        return prompt

    # ====================================================
    # TOKEN ACCOUNTING
    # ====================================================

    def _register_tokens(self, usage: Dict[str, Any]):
        self._tokens_consumed += usage.get("input_tokens",0) + usage.get("output_tokens",0)

    def get_token_stats(self) -> dict:
        return {"tokens_consumed": self._tokens_consumed, "model": self.model, "version": self.VERSION}

    # ====================================================
    # SAFE PARSING
    # ====================================================

    def _extract_text(self, data: dict) -> str:
        try:    return data["content"][0]["text"]
        except: raise AIProviderException("Unexpected response structure from provider.")

    # ====================================================
    # GENERATE
    # ====================================================

    async def generate(
        self,
        prompt:         str,
        tenant_id:      str           = "DEFAULT",
        trace_id:       str           = "",
        correlation_id: Optional[str] = None,
        max_tokens:     int           = MAX_TOKENS
    ) -> dict:

        if not self.api_key:
            return {"response": "MESAN AI temporalmente degradado.", "confidence": 0,
                    "fallback": True, "tenant_id": tenant_id, "trace_id": trace_id, "model": self.model}

        self._check_circuit()
        prompt     = self._sanitize_prompt(prompt)
        max_tokens = min(max_tokens, MAX_TOKENS)
        last_error = None
        t0         = datetime.utcnow()

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.post(
                        self.url,
                        headers={"x-api-key": self.api_key,
                                 "anthropic-version": "2023-06-01",
                                 "content-type": "application/json"},
                        json={"model": self.model, "max_tokens": max_tokens,
                              "messages": [{"role": "user", "content": prompt}]}
                    )

                latency = (datetime.utcnow() - t0).total_seconds()

                if r.status_code == 429:
                    self._record_failure()
                    raise AIRateLimitException("Rate limit reached.")

                if r.status_code >= 500:
                    self._record_failure()
                    raise AIProviderException(f"Provider error {r.status_code}.")

                if r.status_code == 200:
                    data       = r.json()
                    response   = self._extract_text(data)
                    tokens     = data.get("usage", {})
                    confidence = CONFIDENCE_BY_ATTEMPT.get(attempt, 0.60)
                    self._record_success()
                    self._register_tokens(tokens)

                    logger.info("[AI] success", extra={
                        "tenant_id": tenant_id, "trace_id": trace_id,
                        "model": self.model, "latency": round(latency,3),
                        "tokens": tokens, "attempt": attempt, "fallback": False
                    })

                    return {"response": response, "confidence": confidence, "fallback": False,
                            "attempt": attempt, "prompt_version": self.prompt_version,
                            "model": self.model, "latency": latency, "tokens": tokens,
                            "tenant_id": tenant_id, "trace_id": trace_id}

                last_error = f"HTTP {r.status_code}"

            except (AIRateLimitException, AIProviderException): raise
            except httpx.TimeoutException:
                self._record_failure()
                raise AITimeoutException(f"Timeout after {self.timeout}s.")
            except Exception as e:
                last_error = str(e); self._record_failure()
                await asyncio.sleep(2 ** (attempt-1))

        logger.warning("[AI] all retries exhausted", extra={
            "tenant_id": tenant_id, "trace_id": trace_id, "error": last_error})

        return {"response": "MESAN AI temporalmente degradado.", "confidence": 0,
                "fallback": True, "error": last_error, "model": self.model,
                "tenant_id": tenant_id, "trace_id": trace_id}
