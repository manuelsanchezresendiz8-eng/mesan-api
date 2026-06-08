CORRECCIÓN CRÍTICA ANTES DEL MERGE
build_engines_safe()
Actualmente:
Python
engines = build_engines()

for critical in CRITICAL_ENGINES:
    if critical not in engines:
        raise RuntimeError(...)
El problema es:
Python
CRITICAL_ENGINES = [
    "Governance",
    "FiscalSentinel",
    "ComplianceVerify",
    "LaborShield"
]
pero no sé cómo regresa exactamente build_engines().
Si devuelve:
Python
{
   "MESAN_GOVERNANCE": ...
}
o
Python
{
   "governance": ...
}
el startup va a fallar siempre.
Antes del merge Claude debe verificar:
Python
logger.info("Loaded engines: %s", list(engines.keys()))
y validar que los nombres coincidan exactamente.
⚠️ CORRECCIÓN IMPORTANTE
En:
Python
app.middleware("http")(context_middleware)
app.middleware("http")(auth_middleware)
FastAPI ejecuta middleware en orden inverso.
Actualmente el orden real será:
Plain text
auth_middleware
context_middleware
trace_middleware
latency_middleware
o similar dependiendo del stack.
Yo prefiero explícitamente:
Python
trace
context
auth
latency
porque Auth normalmente necesita TraceID.
Revisar.
⚠️ HEALTH ENDPOINT
Aquí:
Python
"uptime_seconds": round(
    time.time() - request.app.state.started_at,
    2
)
Si alguien llama /health antes de completar lifespan podría lanzar:
Python
AttributeError
Más seguro:
Python
started = getattr(request.app.state, "started_at", time.time())

"uptime_seconds": round(
    time.time() - started,
    2
)
⚠️ READY ENDPOINT
Aquí:
Python
c = getattr(request.app.state, "container", None)

engines = getattr(c, "engines", {}) or {}
Correcto.
Pero después haces:
Python
if missing or not c:
Yo invertiría:
Python
if not c:
antes de usar cualquier propiedad.
No es un bug grave porque usaste getattr, pero es más limpio.
⚠️ OBSERVACIÓN OPERATIVA
Tienes:
Python
FEATURE_SELF_HEALING=true
pero:
Python
app.state.self_healing = None
Entonces /health mostrará:
JSON
{
  "self_healing": null
}
aunque la feature esté activa.
Eso genera confusión operacional.
Yo mostraría:
Python
{
   "enabled": FEATURE_SELF_HEALING,
   "running": healing is not None
}
