# ============================================
# MESAN Ω — main.py v2.5.0
# Enterprise Survival OS LATAM
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ============================================
# APP
# ============================================

app = FastAPI(
    title="MESAN Omega",
    version="2.5.0"
)

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# AUTH MIDDLEWARE
# ============================================

from core.auth.auth_middleware import auth_middleware

app.middleware("http")(auth_middleware)

# ============================================
# HEALTH
# ============================================

@app.get("/")
async def root():
    return {
        "system": "MESAN Omega",
        "status": "online",
        "version": "2.5.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.5.0"
    }

@app.get("/ready")
async def ready():
    return {
        "ready": True
    }

# ============================================
# EXECUTION ENDPOINT
# ============================================

@app.post("/execute")
async def execute(payload: dict):

    from core.auth.tenant_context import get_tenant
    from core.auth.audit_log import AuditLog
    from core.billing.billing_engine import BillingEngine
    from services.executive_narrative_generator import ExecutiveNarrativeGenerator

    tenant = get_tenant()

    if not tenant:
        return JSONResponse(
            status_code=401,
            content={"error": "TENANT_MISSING"}
        )

    ingresos = payload.get("ingresos", 0)
    gastos = payload.get("gastos", 0)
    deuda = payload.get("deuda_mensual", 0)
    cartera = payload.get("cartera_vencida", 0)
    trabajadores_sin_imss = payload.get("trabajadores_sin_imss", 0)

    score = 72
    nivel = "ALTO"

    if deuda > ingresos * 0.35:
        score += 8

    if cartera > ingresos:
        score += 6

    if trabajadores_sin_imss > 10:
        score += 5

    if score >= 85:
        nivel = "CRITICO"
    elif score >= 70:
        nivel = "ALTO"
    elif score >= 50:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"

    flujo_operativo = ingresos - gastos - deuda

    dias_supervivencia = 18

    if flujo_operativo > 0:
        dias_supervivencia = 90

    resultado = {
        "nivel": nivel,
        "score": score,
        "dias_supervivencia": dias_supervivencia,
        "flujo_operativo": flujo_operativo,
        "dscr": 1.2,

        "acciones_hoy": [
            "Reducir gasto operativo",
            "Negociar deuda bancaria",
            "Ejecutar cobranza inmediata"
        ],

        "acciones_72h": [
            "Reestructurar pasivos",
            "Congelar contrataciones",
            "Proteger flujo crítico"
        ],

        "acciones_7d": [
            "Optimizar capital de trabajo",
            "Auditar proveedores",
            "Renegociar contratos"
        ]
    }

    # ============================================
    # AUDIT + BILLING + NARRATIVE
    # ============================================

    audit = AuditLog()
    billing = BillingEngine()
    narrative = ExecutiveNarrativeGenerator()

    audit.log(
        tenant_id=tenant.tenant_id,
        event_type="EXECUTION",
        payload=resultado
    )

    invoice = billing.charge(
        tenant_id=tenant.tenant_id,
        operation="EXECUTION_DECISION",
        risk_score=resultado["score"]
    )

    report = narrative.generar(resultado)

    # ============================================
    # RESPONSE
    # ============================================

    return {
        "tenant": tenant.tenant_id,

        "result": resultado,

        "invoice": {
            "amount": invoice.amount,
            "currency": invoice.currency,
            "reason": invoice.reason
        },

        "report": report
    }

# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup_event():
    print("MESAN Ω ENTERPRISE ONLINE")

# ============================================
# LOCAL RUN
# ============================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
