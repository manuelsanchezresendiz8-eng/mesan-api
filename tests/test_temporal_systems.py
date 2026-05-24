# tests/test_temporal_systems.py -- MESAN Omega Temporal Systems v1.1

import uuid

from datetime import datetime, timedelta

from core.temporal_replay_engine import TemporalReplayEngine
from core.snapshot_engine import SnapshotEngine
from core.timeline_engine import TimelineEngine
from core.state_rebuilder import StateRebuilder


TENANT = "EMP-LOGISTICA-001"


def make_event(score, days_ago=0, event_type="RISK_UPDATED"):

    ts = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

    return {
        "tenant_id": TENANT,
        "trace_id": str(uuid.uuid4()),
        "timestamp": ts,
        "event_type": event_type,
        "engine": "predictive_engine",
        "score": score,
        "payload": {}
    }


def test_replay_engine():

    replay_engine = TemporalReplayEngine()

    for score, days in [
        (40, 10),
        (55, 7),
        (70, 4),
        (85, 1)
    ]:

        replay_engine.append_event(
            make_event(score, days)
        )

    result = replay_engine.replay_by_tenant(TENANT)

    assert result.total_events == 4
    assert result.deterioration_detected is True
    assert result.replay_duration_ms >= 0


def test_snapshot_engine():

    snapshot_engine = SnapshotEngine()

    s1 = snapshot_engine.create_snapshot(
        TENANT,
        {
            "score": 45,
            "nivel_riesgo": "MEDIO",
            "exposicion_probable": 500000,
            "confidence": 0.82
        }
    )

    s2 = snapshot_engine.create_snapshot(
        TENANT,
        {
            "score": 78,
            "nivel_riesgo": "ALTO",
            "exposicion_probable": 1200000,
            "confidence": 0.70
        }
    )

    comparison = snapshot_engine.compare_snapshots(
        s1.snapshot_id,
        s2.snapshot_id
    )

    assert comparison["score_delta"] == 33.0
    assert comparison["deterioration_detected"] is True

    drift = snapshot_engine.detect_drift(TENANT)

    assert drift["drift_detected"] is True
    assert drift["tendency"] == "DETERIORO"


def test_timeline_engine():

    timeline_engine = TimelineEngine()

    events = [
        {
            "timestamp": (
                datetime.utcnow() - timedelta(days=d)
            ).isoformat(),
            "score": s,
            "event_type": "SCORE_UPDATED"
        }
        for d, s in [
            (10, 40),
            (7, 55),
            (4, 70),
            (1, 88)
        ]
    ]

    result = timeline_engine.build_timeline(
        TENANT,
        events
    )

    assert result.trend == "DETERIORO"
    assert len(result.critical_events) > 0

    collapse_risk = timeline_engine.detect_collapse_risk(
        result.timeline
    )

    assert "collapse_risk" in collapse_risk


def test_state_rebuilder():

    replay_engine = TemporalReplayEngine()
    snapshot_engine = SnapshotEngine()

    replay_engine.append_event(
        make_event(60, 5)
    )

    replay_engine.append_event(
        make_event(80, 1)
    )

    snapshot_engine.create_snapshot(
        TENANT,
        {
            "score": 60,
            "nivel_riesgo": "ALTO"
        }
    )

    rebuilder = StateRebuilder(
        replay_engine=replay_engine,
        snapshot_engine=snapshot_engine
    )

    result = rebuilder.rebuild(TENANT)

    assert result.success is True
    assert result.integrity_hash != ""

    trail = rebuilder.audit_trail(TENANT)

    assert len(trail) > 0
