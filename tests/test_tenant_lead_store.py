"""Pruebas de integración SQLite para aislamiento de leads entre empresas."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import core.lead_store as lead_store
from database import Base
from models import Lead
from core.auth.tenant_db_models import TenantRecord


@pytest.fixture
def tenant_db(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    db.add_all([
        TenantRecord(id="tenant-a", name="Empresa A", status="active"),
        TenantRecord(id="tenant-b", name="Empresa B", status="active"),
    ])
    db.add_all([
        Lead(id="lead-a", nombre="Lead A", tenant_id="tenant-a", estatus="nuevo"),
        Lead(id="lead-b", nombre="Lead B", tenant_id="tenant-b", estatus="nuevo"),
        Lead(id="lead-publico", nombre="Lead público", tenant_id=None, estatus="nuevo"),
    ])
    db.commit()
    db.close()
    monkeypatch.setattr(lead_store, "SessionLocal", Session)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_list_tenant_leads_never_returns_other_or_public_leads(tenant_db):
    leads = lead_store.list_tenant_leads("tenant-a")
    assert [lead.id for lead in leads] == ["lead-a"]


def test_get_tenant_lead_hides_cross_tenant_and_public_records(tenant_db):
    assert lead_store.get_tenant_lead("lead-a", "tenant-a").id == "lead-a"
    with pytest.raises(lead_store.LeadNotFoundError):
        lead_store.get_tenant_lead("lead-b", "tenant-a")
    with pytest.raises(lead_store.LeadNotFoundError):
        lead_store.get_tenant_lead("lead-publico", "tenant-a")


def test_update_tenant_lead_cannot_modify_other_tenant(tenant_db):
    with pytest.raises(lead_store.LeadNotFoundError):
        lead_store.update_tenant_lead("lead-b", "tenant-a", {"estatus": "modificado"})

    assert lead_store.get_tenant_lead("lead-b", "tenant-b").estatus == "nuevo"


def test_update_tenant_lead_only_changes_allowlisted_fields(tenant_db):
    lead = lead_store.update_tenant_lead(
        "lead-a", "tenant-a",
        {"estatus": "en_revision", "tenant_id": "tenant-b", "id": "lead-b"},
    )
    assert lead.estatus == "en_revision"
    assert lead.tenant_id == "tenant-a"
    assert lead.id == "lead-a"
