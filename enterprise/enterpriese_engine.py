from core.mesan_core import ejecutar_diagnostico
from enterprise.enterprise_engine import sistema_enterprise

@app.post("/diagnostico")
def diagnostico(data: dict):
    return ejecutar_diagnostico(data)

@app.post("/enterprise")
def enterprise(data: dict):
    return sistema_enterprise(data)

@app.get("/health")
def health():
    return {"status": "ok"}
