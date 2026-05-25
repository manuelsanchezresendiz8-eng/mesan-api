# routes/execution_routes.py -- MESAN Omega Execution Routes v1.0
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.auth.tenant_context import get_tenant
from core.auth.audit_log import AuditLog
from core.billing.billing_engine import BillingEngine
from services.executive_narrative_generator import ExecutiveNarrativeGenerator

router = APIRouter()

@router.post("/execute")
async def execute(payload: dict):
    tenant = get_tenant()
    print("TENANT:", tenant)
    if not tenant:
        return JSONResponse(status_code=401, content={"error": "TENANT_MISSING"})

    ingresos = payload.get("ingresos", 0)
    gastos   = payload.get("gastos", 0)
    deuda    = payload.get("deuda_mensual", 0)
    cartera  = payload.get("cartera_vencida", 0)
    sin_imss = payload.get("trabajadores_sin_imss", 0)

    score = 72
    if deuda > ingresos * 0.35: score += 8
    if cartera > ingresos:      score += 6
    if sin_imss > 10:           score += 5

    if score >= 85:   nivel = "CRITICO"
    elif score >= 70: nivel = "ALTO"
    elif score >= 50: nivel = "MEDIO"
    else:             nivel = "BAJO"

    flujo_operativo    = ingresos - gastos - deuda
    dias_supervivencia = 90 if flujo_operativo > 0 else 18

    resultado = {
        "nivel": nivel, "score": score,
        "dias_supervivencia": dias_supervivencia,
        "flujo_operativo": flujo_operativo, "dscr": 1.2,
        "acciones_hoy": ["Reducir gasto operativo", "Negociar deuda bancaria", "Ejecutar cobranza inmediata"],
        "acciones_72h": ["Reestructurar pasivos", "Congelar contrataciones", "Proteger flujo critico"],
        "acciones_7d":  ["Optimizar capital de trabajo", "Auditar proveedores", "Renegociar contratos"]
    }

    audit     = AuditLog()
    billing   = BillingEngine()
    narrative = ExecutiveNarrativeGenerator()

    audit.log(tenant_id=tenant.tenant_id, event_type="EXECUTION", payload=resultado)
    invoice = billing.charge(tenant_id=tenant.tenant_id, operation="EXECUTION_DECISION", risk_score=resultado["score"])
    report  = narrative.generar(resultado)

    return {
        "tenant": tenant.tenant_id,
        "result": resultado,
        "invoice": {"amount": invoice.amount, "currency": invoice.currency, "reason": invoice.reason},
        "report": report
    }
