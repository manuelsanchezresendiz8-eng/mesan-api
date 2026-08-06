# core/demo/demo_mode.py v1.0
from datetime import datetime,timezone
DEMO={"empresa":"Industrias Demo SA","sector":"Manufactura","empleados":150,"omega_score":52,"nivel":"ALTO","esi":75,"exposure_mxn":850000,"war_room_required":True,"acciones_hoy":["Regularizar REPSE","Solicitar opinion SAT","Alta IMSS trabajadores"]}
DEMO_GUARDIAN={"health_score":72,"health_status":"DEGRADED","alerts_count":3,"incidents_count":1}
class DemoMode:
    def __init__(self):self.version="1.0.0"
    def get_diagnostico(self):return{"timestamp":datetime.now(timezone.utc).isoformat(),"mode":"DEMO","result":DEMO}
    def get_guardian(self):return{"timestamp":datetime.now(timezone.utc).isoformat(),"mode":"DEMO",**DEMO_GUARDIAN}
    def get_warroom(self):return{"timestamp":datetime.now(timezone.utc).isoformat(),"mode":"DEMO","status":"ACTIVE","risk_level":"ALTO","exposure":850000,"actions":DEMO["acciones_hoy"]}
    def get_dashboard(self):return{"timestamp":datetime.now(timezone.utc).isoformat(),"mode":"DEMO","diagnostico":self.get_diagnostico(),"guardian":self.get_guardian(),"warroom":self.get_warroom()}
demo_mode=DemoMode()