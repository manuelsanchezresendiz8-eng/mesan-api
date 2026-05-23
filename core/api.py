# core/api.py -- MESAN Omega Production API Layer v1.1
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
from core.integration_layer import IntegrationLayer

app = FastAPI(title="MESAN Omega API", version="1.1.0", docs_url="/docs", redoc_url="/redoc")

integration_layer: Optional[IntegrationLayer] = None

class AnalysisRequest(BaseModel):
    tenant_id: str = Field(default="DEFAULT", min_length=1, max_length=120)
    data: Dict[str, Any]

def set_pipeline(layer: IntegrationLayer):
    global integration_layer
    integration_layer = layer

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "status": "ERROR", "message": str(exc),
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url), "trace": traceback.format_exc(limit=2)
    })

@app.get("/")
def root():
    return {"system": "MESAN Omega", "status": "ONLINE", "version": "1.1.0",
            "timestamp": datetime.utcnow().isoformat()}

@app.post("/analyze")
def analyze(request: AnalysisRequest):
    if not integration_layer:
        raise HTTPException(status_code=500, detail="Integration layer not initialized")
    result = integration_layer.run(raw_data=request.data, tenant_id=request.tenant_id)
    return {"status": "SUCCESS", "trace_id": result["trace_id"],
            "state": result["state"], "consistency": result["consistency"],
            "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "MESAN Omega API",
            "version": "1.1.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
def readiness_check():
    ready = integration_layer is not None
    return {"ready": ready, "integration_layer": ready,
            "timestamp": datetime.utcnow().isoformat()}

@app.get("/metrics")
def metrics():
    if integration_layer and integration_layer.observability:
        r = integration_layer.observability.generate_report()
        return {"status": r.system_status, "total_executions": r.total_executions,
                "avg_latency_ms": r.avg_latency_ms, "error_rate": r.error_rate,
                "avg_confidence": r.avg_confidence, "avg_drift": r.avg_drift,
                "engines_health": r.engines_health, "timestamp": r.timestamp}
    return {"status": "NO_DATA", "message": "Observability not initialized",
            "timestamp": datetime.utcnow().isoformat()}
