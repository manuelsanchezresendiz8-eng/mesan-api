# ============================================
# routes/execution_routes.py
# MESAN Omega Execution Routes v1.1
# ============================================

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

    # ============================================
    # VALIDAR TENANT
    # ============================================

    if not tenant:
        return JSONResponse(
            status_code=401,
            content={"error": "TENANT_MISSING"}
        )

    # ============================================
    # INPUTS
    # ============================================

    ingresos = payload.get("ingresos", 0)
    gastos = payload.get("gastos", 0)
    deuda = payload.get("deuda_mensual", 0)
    cartera = payload.get("cartera_vencida", 0)
    sin_imss = payload.get("trabajadores_sin_imss", 0)

    # ============================================
    # ENGINE
    # ============================================

    score = 72

    if deuda > ingresos * 0.35:
        score += 8

    if cartera > ingresos:
        score += 6

    if sin_imss > 10:
        score += 5

    # ============================================
    # NIVEL
    # ============================================

    if score >= 85:
        nivel = "CRITICO"

    elif score >= 70:
        nivel = "ALTO"

    elif score >= 50:
        nivel = "MEDIO"

    else:
        nivel = "BAJO"

    # ============================================
    # FLUJO
    # ============================================

    flujo_operativo = ingresos - gastos - deuda

    dias_supervivencia = (
        90 if flujo_operativo > 0 else 18
    )

    # ============================================
    # RESULTADO
    # ============================================

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
    # SERVICES
    # ============================================

    audit = AuditLog()
    billing = BillingEngine()
    narrative = ExecutiveNarrativeGenerator()

    # ============================================
    # SAFE AUDIT
    # ============================================

    try:

        audit.log(
            tenant_id=tenant.tenant_id,
            event_type="EXECUTION",
            payload=resultado
        )

    except Exception as e:

        print("AUDIT ERROR:", str(e))

    # ============================================
    # SAFE BILLING
    # ============================================

    try:

        invoice = billing.charge(
            tenant_id=tenant.tenant_id,
            operation="EXECUTION_DECISION",
            risk_score=resultado["score"]
        )

    except Exception as e:

        print("BILLING ERROR:", str(e))

        class DummyInvoice:
            amount = 0
            currency = "MXN"
            reason = "billing_disabled"

        invoice = DummyInvoice()

    # ============================================
    # SAFE NARRATIVE
    # ============================================

    try:

        report = narrative.generar(resultado)

    except Exception as e:

        print("NARRATIVE ERROR:", str(e))

        report = "Narrativa temporalmente no disponible"

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
