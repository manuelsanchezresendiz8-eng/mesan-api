# main_enterprise.py -- MESAN Omega Enterprise Entry Point v1.0
from fastapi import FastAPI
from core.auth.auth_middleware import auth_middleware
from core.middleware.tenant_middleware import TenantMiddleware
from core.auth.tenant_context import get_tenant
from core.auth.audit_log import AuditLog
from core.billing.billing_engine import BillingEngine
from services.executive_narrative_generator import ExecutiveNarrativeGenerator

app = FastAPI(title="MESAN Omega", version="1.0")

# Middleware order CRITICO
app.middleware("http")(auth_middleware)
app.add_middleware(TenantMiddleware)

audit     = AuditLog()
billing   = BillingEngine()
narrative = ExecutiveNarrativeGenerator()

@app.get("/health")
def health():
    return {"status": "OK", "system": "MESAN Omega"}

@app.post("/execute")
def execute(payload: dict):
    tenant = get_tenant()
    if not tenant:
        return {"error": "TENANT_MISSING"}

    resultado_engine = {
        "nivel": "HIGH", "score": 72, "dias_supervivencia": 18,
        "flujo_operativo": 250000, "dscr": 1.2,
        "acciones_hoy": ["Reducir gasto operativo", "Negociar deuda bancaria"],
        "acciones_72h": ["Reestructurar pasivos", "Congelar contrataciones"],
        "acciones_7d":  ["Optimizar flujo de caja", "Auditar proveedores"]
    }

    audit.log(tenant_id=tenant.tenant_id, event_type="EXECUTION", payload=resultado_engine)

    invoice = billing.charge(tenant_id=tenant.tenant_id,
                             operation="EXECUTION_DECISION",
                             risk_score=resultado_engine["score"])

    report = narrative.generar(resultado_engine)

    return {
        "tenant": tenant.tenant_id,
        "result": resultado_engine,
        "invoice": {"amount": invoice.amount, "currency": invoice.currency, "reason": invoice.reason},
        "report": report
    }
