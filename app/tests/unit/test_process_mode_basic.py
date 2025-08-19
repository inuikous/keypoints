"""Process mode basic tests (v0.6 experimental).

Covers:
- Orchestrator start/stop with use_process=True
- Result production (at least one ResultRecord or StatsMessage)
- Ping loop functioning (losses reset when respond_to_ping=True)
"""
from __future__ import annotations

from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_process_mode_start_stop_and_results():
    cfg = OrchestratorConfig(camera_ids=["pc1"], use_process=True, ping_interval_sec=0.1, ping_timeout_sec=0.2, ping_loss_threshold=3, worker_latency_ms=0.0)
    orch = Orchestrator(cfg)
    orch.start()
    sleep(0.6)  # allow some frames + ping rounds
    snap = orch.aggregator.snapshot_stats()
    assert "pc1" in snap  # camera stats present
    # health state losses should be 0 because respond_to_ping True by default
    hs = orch.health_state["pc1"]
    assert hs["losses"] == 0
    orch.stop()
