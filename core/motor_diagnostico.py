from core.riesgo_laboral import evaluar_riesgo_laboral
from enterprise.modules.omision_baja import evaluar_omision_baja

def ejecutar_motor(data):
    laboral = evaluar_riesgo_laboral(data)
    omision = evaluar_omision_baja(data)

    return {
        "laboral": laboral,
        "omision": omision
    }

