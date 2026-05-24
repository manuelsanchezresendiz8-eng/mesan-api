# tests/test_multi_tenant_flow.py -- MESAN Omega Multi-Tenant Test v1.1
from fastapi.testclient import TestClient
from main_enterprise import app

client = TestClient(app)

def test_multi_tenant_execution():
    tenants = ["tenant_1", "tenant_2"]
    results = []

    for t in tenants:
        headers = {
            "Authorization": f"Bearer jwt_not_installed_{t}",
            "X-Tenant-ID": t
        }
        response = client.post("/execute", json={"input": "simulation"}, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["tenant"] == t
        assert "result" in data
        assert "invoice" in data
        assert "report" in data
        results.append(data)

    assert results[0]["tenant"] != results[1]["tenant"]
    assert results[0]["invoice"]["amount"] > 0
    assert results[1]["invoice"]["amount"] > 0
