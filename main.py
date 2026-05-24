# ============================================
# MESAN Ω EXECUTION ENDPOINT v1.0
# ============================================

@app.post("/execute")
async def execute(payload: dict):

    from core.auth.tenant_context import get_tenant
    from core.auth.audit_log import AuditLog
    from core.billing.billing_engine import BillingEngine
    from services.executive_narrative_generator import ExecutiveNarrativeGenerator

    tenant = get_tenant()

    if not tenant:
        return {
            "error": "TENANT_MISSING"
        }

    resultado = {
        "nivel": "ALTO",
        "score": 72,
        "dias_supervivencia": 18,
        "flujo_operativo": 250000,
        "dscr": 1.2,

        "acciones_hoy": [
            "Reducir gasto operativo",
            "Negociar deuda bancaria",
            "Ejecutar cobranza"
        ],

        "acciones_72h": [
            "Reestructurar pasivos",
            "Congelar contrataciones"
        ],

        "acciones_7d": [
            "Optimizar flujo de caja",
            "Auditar proveedores"
        ]
    }

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
