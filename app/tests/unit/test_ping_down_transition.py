"""Ping 連続失敗による DOWN 遷移と回復のテスト。"""
from __future__ import annotations

from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_ping_down_transition_and_recover() -> None:
    # フェーズ1: 応答しない -> DOWN
    cfg_down = OrchestratorConfig(camera_ids=["pd"], ping_interval_sec=0.05, ping_timeout_sec=0.08, ping_loss_threshold=2, respond_to_ping=False, worker_latency_ms=0.0)
    orch_down = Orchestrator(cfg_down)
    orch_down.start()
    sleep(0.5)
    state_down = orch_down.health_state["pd"]
    assert state_down["down"] is True
    orch_down.stop()
    # フェーズ2: 応答する新インスタンスで losses が 0 維持 (DOWN しない)
    cfg_ok = OrchestratorConfig(camera_ids=["pd"], ping_interval_sec=0.05, ping_timeout_sec=0.08, ping_loss_threshold=2, respond_to_ping=True, worker_latency_ms=0.0)
    orch_ok = Orchestrator(cfg_ok)
    orch_ok.start()
    sleep(0.3)
    state_ok = orch_ok.health_state["pd"]
    assert state_ok["losses"] == 0
    assert state_ok["down"] is False
    orch_ok.stop()
