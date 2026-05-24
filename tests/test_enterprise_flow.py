# tests/test_enterprise_flow.py -- MESAN Omega Integration Test v1.1

from fastapi.testclient import TestClient
from main_enterprise import app

client = TestClient(app)


def test_enterprise_flow_complete():

    headers = {
        "Authorization": "Bearer jwt_not_installed_tenant_1",
        "X-Tenant-ID": "tenant_1"
    }

    response = client.post(
        "/execute",
        json={"input": "test"},
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    # --------------------------------------------------------
    # CORE RESPONSE
    # --------------------------------------------------------

    assert "tenant" in data
    assert "result" in data
    assert "invoice" in data
    assert "report" in data

    # --------------------------------------------------------
    # EXECUTION ENGINE
    # --------------------------------------------------------

    assert "score" in data["result"]
    assert "nivel" in data["result"]

    # --------------------------------------------------------
    # BILLING
    # --------------------------------------------------------

    assert data["invoice"]["amount"] > 0
    assert data["invoice"]["currency"] == "MXN"

    # --------------------------------------------------------
    # NARRATIVE ENGINE
    # --------------------------------------------------------

    assert "DECISION CEO" in data["report"]
