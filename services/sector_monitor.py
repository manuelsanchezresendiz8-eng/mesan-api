from __future__ import annotations
import logging
from typing import List
from services.market_models import SectorStatus

logger = logging.getLogger('mesan.market.sector')

class SectorMonitor:
    SECTORS = [
        {'sector':'MANUFACTURA','status':'ACTIVE','risk':'BAJO','events':['Produccion industrial +2.1%','Nearshoring incrementa demanda'],'opportunity':'Alta demanda de personal — oportunidad REPSE'},
        {'sector':'COMERCIO','status':'WARNING','risk':'MEDIO','events':['Inflacion presiona margenes','Cambios CFDI'],'opportunity':'Revision compliance fiscal urgente'},
        {'sector':'CONSTRUCCION','status':'WARNING','risk':'ALTO','events':['REPSE obligatorio subcontratacion','Cartera vencida en aumento'],'opportunity':'Alta exposicion laboral — diagnostico urgente'},
        {'sector':'TRANSPORTE','status':'ACTIVE','risk':'MEDIO','events':['Salario minimo impacta operadores','NOM-087'],'opportunity':'Alta rotacion laboral — riesgo IMSS elevado'},
        {'sector':'SERVICIOS','status':'ACTIVE','risk':'BAJO','events':['Crecimiento sostenido','REPSE simplificado aplica'],'opportunity':'Regimen simplificado reduce carga regulatoria'},
        {'sector':'SALUD','status':'ACTIVE','risk':'BAJO','events':['Expansion post-pandemia','Regulacion COFEPRIS'],'opportunity':'Alta demanda servicios especializados'},
        {'sector':'TECNOLOGIA','status':'ACTIVE','risk':'BAJO','events':['Nearshoring impulsa sector','Demanda talento en alza'],'opportunity':'Crecimiento acelerado — riesgo laboral por expansion'},
        {'sector':'EDUCACION','status':'ACTIVE','risk':'BAJO','events':['Modalidad presencial consolidada'],'opportunity':'Revision contratos colectivos recomendada'},
    ]
    def scan(self):
        return [SectorStatus(sector=s['sector'],status=s['status'],risk_level=s['risk'],key_events=s['events'],opportunity=s['opportunity']) for s in self.SECTORS]
    def check(self): return self.scan()

sector_monitor = SectorMonitor()
