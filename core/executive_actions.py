# ==================================================
# MESAN Omega -- MOTOR DE RECOMENDACIONES EJECUTIVAS
# ==================================================

class ExecutiveActions:

    @staticmethod
    def generar_recomendaciones(riesgo, sector):
        recomendaciones = []

        if riesgo == "CRITICO":
            recomendaciones.extend([
                "Activar comite de crisis ejecutivo en menos de 24 horas.",
                "Designar responsable unico de continuidad operativa.",
                "Generar flujo de caja proyectado diario por 60 dias.",
                "Suspender gastos no estrategicos inmediatamente.",
                "Priorizar obligaciones laborales, fiscales y operativas criticas."
            ])

        if sector == "FINANCIERO":
            recomendaciones.extend([
                "Renegociar deuda bancaria antes de entrar en mora formal.",
                "Ejecutar recuperacion acelerada de cartera vencida.",
                "Reestructurar flujo operativo semanal.",
                "Limitar exposicion a gastos variables."
            ])
        elif sector == "SEGURIDAD":
            recomendaciones.extend([
                "Regularizar permisos SSPC prioritariamente.",
                "Blindar contratos criticos.",
                "Contratar cobertura de responsabilidad civil.",
                "Regularizar IMSS y REPSE."
            ])
        elif sector == "LABORAL":
            recomendaciones.extend([
                "Abrir negociacion preventiva sindical.",
                "Evitar escalamiento publico del conflicto.",
                "Proteger continuidad de produccion.",
                "Reducir exposicion contractual."
            ])

        return recomendaciones
