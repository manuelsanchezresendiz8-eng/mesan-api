# AUDITORÍA DE PRODUCCIÓN — MESAN Ω v1.5.0
**Fecha:** Junio 2026  
**Rol:** Principal Software Architect + Production Reliability Engineer  
**Estado:** 4 P0 confirmados en código real — NO apto para producción sin correcciones

---

## Scores de Evaluación

| Dimensión | Score |
|---|---|
| **Risk Score Global** | 42/100 |
| **Production Readiness** | 51/100 |
| **Escalabilidad** | 48/100 |
| **Confiabilidad** | 55/100 |
| **Deuda Técnica** | 38/100 |

---

## Hallazgos por Severidad

**P0 (fallo crítico o resultado incorrecto): 4**  
**P1 (riesgo alto): 5**  
**P2 (riesgo medio): 3**  
**Total: 12**

---

## P0 — CRÍTICOS

---

### P0-A2 — Race condition en `_load_engines()` ✅ VERIFICADO EN CÓDIGO

**Ubicación:** `OmegaOrchestrator._load_engines()`  
**Verificación:** 10 threads simultáneos → 10 inicializaciones ejecutadas (confirmado)

**Código problemático:**
```python
def _load_engines(self):
    if self._engines_loaded:   # check sin lock
        return
    # ... inicialización ...
    self._engines_loaded = True
```

**Escenario de fallo:** Dos requests simultáneos sobre la instancia singleton `omega_orchestrator` en `app.state`. Ambos pasan el check antes de que cualquiera setee `_engines_loaded=True`. Resultado: dos sets de engines inicializados simultáneamente, posible estado inconsistente.

**Impacto:** En producción con FastAPI async, múltiples workers o el primer request bajo carga → engines duplicados, posible error de importación circular, estado inconsistente de ContinuityEngine.

**Fix:**
```python
import threading

def __init__(self):
    self._lock = threading.Lock()
    self._engines_loaded = False

def _load_engines(self):
    if self._engines_loaded:
        return
    with self._lock:
        if self._engines_loaded:  # double-checked locking
            return
        # ... inicialización ...
        self._engines_loaded = True
```

---

### P0-A1 — ThreadPoolExecutor sin timeout ✅ VERIFICADO

**Ubicación:** `OmegaOrchestrator._run_pipeline()` línea `as_completed(futures)`

**Código problemático:**
```python
for f in as_completed(futures):   # sin timeout
```

**Escenario de fallo:** Engine fiscal conecta a SAT API externa que no responde. El thread queda bloqueado indefinidamente. En multi-tenant, 100 evaluaciones simultáneas → pool exhausto → todos los requests posteriores cuelgan.

**Impacto:** Degradación total del servicio. SLA de 2 segundos imposible. Render timeout después de 30s → 502 masivos.

**Fix:**
```python
for f in as_completed(futures, timeout=15):
    # manejar TimeoutError individualmente
```

---

### P0-C2 — FiscalSentinel score=0 con engine ERROR → health=100 ✅ VERIFICADO

**Ubicación:** `ScoreNormalizer.normalize_engine_result()` + `FiscalSentinelEngine`

**Escenario de fallo:** FiscalSentinelEngine falla silenciosamente y retorna `{"fiscal_score": 0, "engine_status": "ERROR"}`. ScoreNormalizer invierte: `health = 100 - 0 = 100`. Empresa con engine roto recibe health_score=100 (máximo saludable) en dimensión fiscal.

**Impacto:** Falso positivo de riesgo. Empresa en crisis fiscal aparece como perfectamente saludable. omega_score inflado. War Room no se activa.

**Fix:**
```python
def normalize_engine_result(self, engine_result: dict) -> NormalizedScore:
    if engine_result.get("engine_status") == "ERROR":
        return NormalizedScore(engine=engine_name, health_score=50,
                               risk_score=50, raw_score=50, inverted=False)
    # ... resto del método
```

---

### P0-E1 — WarRoom fallback retorna `required=False` en excepción ✅ VERIFICADO

**Ubicación:** `OmegaOrchestrator.ejecutar()` bloque except de WarRoom

**Código problemático:**
```python
except Exception as e:
    war_result = WarRoomResult(required=False, ...)  # conservador incorrecto
```

**Escenario de fallo:** WarRoomEngine lanza excepción porque `enterprise_survival_index=None` (Continuity falló). Empresa con ESI=0, exposición $5M, 10 hallazgos críticos → War Room falla → `required=False` → CRM clasifica como `sales_priority=C` → cliente en crisis no recibe intervención.

**Impacto:** Falso negativo de riesgo. El más peligroso del sistema. Consecuencia regulatoria potencial.

**Fix conservador:**
```python
except Exception as e:
    logger.critical("[WarRoom] FAILED — aplicando escalamiento conservador: %s", e)
    war_result = WarRoomResult(
        required = True,   # conservador: ante duda, escalar
        score    = 50,
        priority = "48H",
        reasons  = [f"WarRoom evaluation failed — conservative escalation: {str(e)}"],
        signals  = WarRoomSignals(),
    )
```

---

## P1 — RIESGO ALTO

---

### P1-A4 — Financial engine excluido de `omega_health_score` weights

**Ubicación:** `OmegaOrchestrator.ejecutar()` — dict de weights

**Problema:** El dict de pesos no incluye `"financial"`. El engine financiero corre, normaliza, pero su score tiene peso=0 en el omega_score final. Una empresa insolvente puede recibir omega_score=85 si los otros 5 engines son positivos.

**Fix:** Redistribuir pesos sumando financial:
```python
weights={
    "compliance": 0.10, "fiscal": 0.15, "labor": 0.15,
    "contractual": 0.10, "policy": 0.10, "governance": 0.20,
    "financial": 0.20,   # ← agregar
}
```

---

### P1-C1 — Engine desconocido retorna health=50 sin warning ✅ VERIFICADO

**Ubicación:** `ScoreNormalizer.normalize_engine_result()`

**Verificación:** Engine con score=15 (alto riesgo) → health=50 (neutral) silenciosamente.

**Fix:**
```python
if engine_name not in ENGINE_SCORE_KEYS:
    logger.warning("[ScoreNormalizer] Engine '%s' no registrado — usando fallback 50", engine_name)
```

---

### P1-D1 — drift_pct produce 6000% cuando v1=0 ✅ VERIFICADO

**Ubicación:** `OmegaOrchestrator.ejecutar()` — cálculo de drift_pct

**Verificación:** v1=0, v2=60 → drift_pct=6000%. `drift_level="CRITICAL"`. `adoption_signal.recommend_promote=False`. Sistema reporta divergencia catastrófica cuando ambos engines detectan crisis correctamente.

**Fix:**
```python
if v1 is not None and v2 is not None and v1 > 0:
    drift_pct = round((drift / float(v1)) * 100, 2)
else:
    drift_pct = None  # no calculable cuando v1=0
```

---

### P1-B1 — OmegaResponse mutable post-build

**Ubicación:** `OmegaResponse` dataclass

**Problema:** `@dataclass` sin `frozen=True`. Código downstream puede modificar `response.omega_score` sin error. En handlers async con múltiples lectores concurrentes → corrupción silenciosa.

**Fix:** `@dataclass(frozen=True)` — o separar en modelo de construcción (builder) y modelo de lectura (frozen).

---

### P1-F1 — Remediation recibe `nivel` de GovernanceEngine ✅ VERIFICADO

**Ubicación:** `OmegaOrchestrator.ejecutar()` — `remediation_input["nivel"]`

**Verificación:** `governance.nivel="WORLD_CLASS"` → `remediation nivel="MEDIO"` (default).

**Impacto:** Plan de remediación puede tener nivel incorrecto para cualquier empresa cuyo governance use nomenclatura no estándar.

**Fix:**
```python
from core.risk_classification import risk_classifier
nivel_esi = risk_classifier.classify_esi(esi)  # usar ESI, no governance.nivel
remediation_input["nivel"] = nivel_esi
```

---

## P2 — RIESGO MEDIO

---

### P2-A3 — `_collect_alerts` puede retornar objetos no serializables

**Ubicación:** `OmegaOrchestrator._collect_alerts()`

**Fix:**
```python
safe_alert = a if isinstance(a, (dict, str)) else str(a)
```

---

### P2-B2 — `model_drift` es `Optional[dict]` sin schema

**Ubicación:** `OmegaResponse.model_drift`

**Fix:** Crear `ModelDriftResult` dataclass tipada con `v1_score`, `v2_score`, `drift`, `drift_pct`, `drift_level`, `adoption_signal`.

---

### P2-G1 — `financial_v2` exposición no se suma al total ✅ VERIFICADO

**Ubicación:** `ExposureAggregator.aggregate_from_pipeline()`

**Verificación:** financial_v2 retorna `"exposicion": 500000` → aggregator suma `0.0`.

**Fix:** En `financial_intelligence_engine_v2.py`:
```python
"exposicion_estimada_mxn": round(exposicion, 2),  # alias requerido por aggregator
```

---

## Top 10 Riesgos Prioritarios

| # | Riesgo | Severidad | Impacto |
|---|---|---|---|
| 1 | WarRoom fallback `required=False` en excepción | P0 | Empresa en crisis no recibe intervención |
| 2 | Race condition en `_load_engines()` | P0 | Estado inconsistente bajo concurrencia |
| 3 | FiscalSentinel score=0 en ERROR → health=100 | P0 | Falso positivo fiscal silencioso |
| 4 | ThreadPoolExecutor sin timeout | P0 | Thread starvation bajo carga |
| 5 | Financial engine excluido de omega_score | P1 | Score financiero no contribuye al índice global |
| 6 | Remediation nivel desde governance (escala incorrecta) | P1 | Plan de acción incorrecto |
| 7 | drift_pct=6000% cuando v1=0 | P1 | Señal de promoción v2 siempre False en crisis |
| 8 | Engine desconocido → health=50 silencioso | P1 | Falso negativo sin log ni alerta |
| 9 | OmegaResponse mutable post-build | P1 | Corrupción posible en async |
| 10 | financial_v2 exposición no agregada | P2 | Total exposure subestimado |

---

## Veredicto de Producción

**Clasificación: C — REQUIERE CORRECCIONES**

Los 4 P0 son bloqueadores. Específicamente P0-E1 (WarRoom falso negativo) y P0-C2 (Fiscal falso positivo) pueden producir evaluaciones de riesgo incorrectas que el sistema no detecta ni reporta.

**Para alcanzar clasificación B (producción con observaciones):**
1. Fix P0-A2: threading.Lock en _load_engines
2. Fix P0-A1: timeout en as_completed
3. Fix P0-C2: engine_status=ERROR bypass en ScoreNormalizer
4. Fix P0-E1: WarRoom fallback conservador (required=True)
5. Fix P1-A4: agregar financial a omega_health_score weights
6. Fix P1-D1: drift_pct solo cuando v1 > 0

Los P1-B1, P1-F1, P2-* pueden ir en el sprint posterior sin bloquear staging.
