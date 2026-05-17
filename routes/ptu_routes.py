# routes/ptu_routes.py — MESAN Ω
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List
import models
import ptu_engine
from database import SessionLocal

router = APIRouter(prefix="/api/v1/ptu", tags=["PTU"])

class PTUCierreRequest(BaseModel):
    anio_fiscal: int
    utilidad_neta_declarada: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def money(value) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

@router.post("/procesar-cierre")
def procesar_cierre_ptu(data: PTUCierreRequest, db: Session = Depends(get_db)):
    try:
        if data.utilidad_neta_declarada <= 0:
            raise HTTPException(status_code=400, detail="La utilidad neta declarada debe ser mayor a cero.")

        utilidad = Decimal(str(data.utilidad_neta_declarada))
        anio = data.anio_fiscal

        remanente_anterior = (
            db.query(models.RemanentePTU)
            .filter(
                models.RemanentePTU.anio_fiscal_origen == anio - 1,
                models.RemanentePTU.aplicado_en_siguiente_ejercicio == False
            ).first()
        )

        remanente_previo = Decimal(str(remanente_anterior.monto_acumulado)) if remanente_anterior else Decimal("0")
        bolsa_total = utilidad + remanente_previo

        empleados = db.query(models.EmpleadoAcumuladoAnual).filter(models.EmpleadoAcumuladoAnual.anio_fiscal == anio).all()

        if not empleados:
            raise HTTPException(status_code=404, detail=f"Sin registros de nomina para el ejercicio {anio}.")

        registros_hist = db.query(models.HistoricoPTU).filter(models.HistoricoPTU.anio_fiscal.in_([anio - 1, anio - 2, anio - 3])).all()

        historicos: Dict[int, List[Decimal]] = {}
        for h in registros_hist:
            historicos.setdefault(h.empleado_id, []).append(Decimal(str(h.monto_recibido)))

        calculos = ptu_engine.calcular_reparto_ptu(
            utilidad_total_repartir=bolsa_total,
            empleados=empleados,
            historicos=historicos,
            anio_fiscal=anio
        )

        remanente_total = Decimal("0")

        for item in calculos:
            remanente_total += Decimal(str(item["remanente_generado"]))
            existe = db.query(models.HistoricoPTU).filter(
                models.HistoricoPTU.empleado_id == item["empleado_id"],
                models.HistoricoPTU.anio_fiscal == anio
            ).first()
            if not existe:
                db.add(models.HistoricoPTU(
                    empleado_id=item["empleado_id"],
                    anio_fiscal=anio,
                    monto_recibido=money(item["ptu_a_pagar"])
                ))

        if remanente_total > 0:
            rem_existente = db.query(models.RemanentePTU).filter(models.RemanentePTU.anio_fiscal_origen == anio).first()
            if rem_existente:
                rem_existente.monto_acumulado = money(remanente_total)
            else:
                db.add(models.RemanentePTU(
                    anio_fiscal_origen=anio,
                    monto_acumulado=money(remanente_total),
                    aplicado_en_siguiente_ejercicio=False
                ))

        if remanente_anterior:
            remanente_anterior.aplicado_en_siguiente_ejercicio = True

        db.commit()

        return {
            "status": "success",
            "mensaje": f"PTU ejercicio {anio} procesada correctamente.",
            "resumen": {
                "utilidad_ejercicio": money(utilidad),
                "remanente_recuperado_anio_anterior": money(remanente_previo),
                "bolsa_total_repartida": money(bolsa_total),
                "total_remanente_guardado_proximo_anio": money(remanente_total),
                "empleados_procesados": len(calculos)
            },
            "detalle_empleados": calculos
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error DB: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error PTU: {str(e)}")
