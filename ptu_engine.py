# ptu_engine.py — MESAN Ω
# Motor PTU deterministico — NO usa IA para calculos

from typing import List, Dict
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, Boolean
from database import Base

class EmpleadoAcumuladoAnual(BaseModel):
    empleado_id: int
    nombre_completo: str
    dias_trabajados: int
    salario_anual_devengado: Decimal
    salario_mensual_base: Decimal
    puesto_directivo: bool = False
    es_eventual: bool = False

class RemanentePTU(Base):
    __tablename__ = "remanente_ptu"
    id = Column(Integer, primary_key=True, index=True)
    anio_fiscal_origen = Column(Integer, unique=True, nullable=False)
    monto_acumulado = Column(Float, nullable=False)
    aplicado_en_siguiente_ejercicio = Column(Boolean, default=False)

def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calcular_reparto_ptu(
    utilidad_total_repartir: Decimal,
    empleados: List[EmpleadoAcumuladoAnual],
    historicos: Dict[int, List[Decimal]],
    anio_fiscal: int
) -> List[dict]:

    empleados_aptos = [
        emp for emp in empleados
        if not emp.puesto_directivo
        and not (emp.es_eventual and emp.dias_trabajados < 60)
    ]

    if not empleados_aptos:
        return []

    mitad = utilidad_total_repartir / Decimal("2")
    suma_dias     = sum(Decimal(e.dias_trabajados) for e in empleados_aptos)
    suma_salarios = sum(max(e.salario_anual_devengado, Decimal("0")) for e in empleados_aptos)

    factor_dias    = mitad / suma_dias     if suma_dias > 0     else Decimal("0")
    factor_salario = mitad / suma_salarios if suma_salarios > 0 else Decimal("0")

    resultado_final = []

    for emp in empleados_aptos:
        salario_valido = max(emp.salario_anual_devengado, Decimal("0"))
        ptu_dias       = Decimal(emp.dias_trabajados) * factor_dias
        ptu_salario    = salario_valido * factor_salario
        ptu_calculada  = ptu_dias + ptu_salario

        tope_3_meses   = emp.salario_mensual_base * Decimal("3")
        hist_valido    = [Decimal(x) for x in historicos.get(emp.empleado_id, []) if Decimal(x) > 0]
        tope_promedio  = sum(hist_valido) / Decimal(len(hist_valido)) if hist_valido else Decimal("0")
        tope_maximo    = max(tope_3_meses, tope_promedio)

        ptu_definitiva = min(ptu_calculada, tope_maximo)
        remanente      = ptu_calculada - ptu_definitiva

        resultado_final.append({
            "empleado_id":        emp.empleado_id,
            "nombre":             emp.nombre_completo,
            "ptu_sin_tope":       float(money(ptu_calculada)),
            "tope_aplicado":      float(money(tope_maximo)),
            "ptu_a_pagar":        float(money(ptu_definitiva)),
            "remanente_generado": float(money(remanente)),
            "ejercicio_origen":   anio_fiscal
        })

    return resultado_final
