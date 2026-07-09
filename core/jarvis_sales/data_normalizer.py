from __future__ import annotations
import logging
from typing import Any, Dict
logger = logging.getLogger('mesan.sales.normalizer')
EMPLEADOS_MAP = {'1-10':5,'1 - 10':5,'11-50':30,'11 - 50':30,'1-50':25,'1 - 50':25,'51-250':100,'250+':300}
def parse_empleados(v):
    if v is None: return 0
    if isinstance(v,(int,float)): return int(v)
    s=str(v).strip()
    if s in EMPLEADOS_MAP: return EMPLEADOS_MAP[s]
    for k,val in EMPLEADOS_MAP.items():
        if k in s: return val
    d=''.join(filter(str.isdigit,s))[:4]
    return int(d) if d else 0
def normalize_lead(data):
    d=dict(data)
    d['empleados']=parse_empleados(d.get('empleados'))
    mn=float(d.get('impacto_min') or 0)
    mx=float(d.get('impacto_max') or 0)
    if not d.get('impacto_estimado') and (mn or mx): d['impacto_estimado']=(mn+mx)/2
    if not d.get('nivel_riesgo') and d.get('clasificacion'): d['nivel_riesgo']=d['clasificacion']
    d['diagnostico_hecho']=bool(d.get('omega_score') or d.get('nivel_riesgo'))
    if d.get('fecha') and not d.get('created_at'): d['created_at']=str(d['fecha'])
    return d
