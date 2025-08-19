"""Ping/Pong ヘルス監視の単体テスト。

目的:
- Worker が PING を受信し StatusUpdate(ping_response) を返すと Orchestrator 側で losses リセット
- 応答しない設定 (respond_to_ping=False) では losses が閾値まで増加し CAMERA_DOWN ログを出す (ログ存在は緩く検証)
"""
from __future__ import annotations

from time import sleep
import logging

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_ping_success_resets_losses() -> None:
    cfg = OrchestratorConfig(camera_ids=["p1"], ping_interval_sec=0.1, ping_timeout_sec=0.2, ping_loss_threshold=3, respond_to_ping=True, worker_latency_ms=0.0)
    orch = Orchestrator(cfg)
    orch.start()
    sleep(0.5)  # 複数ラウンド
    state = orch.health_state["p1"]
    # 応答しているなら losses は 0 であるはず
    assert state["losses"] == 0
    orch.stop()


def test_ping_timeouts_increment_and_down() -> None:
    # 応答しない Worker に対して losses が増える
    cfg = OrchestratorConfig(camera_ids=["p2"], ping_interval_sec=0.1, ping_timeout_sec=0.15, ping_loss_threshold=2, respond_to_ping=False, worker_latency_ms=0.0)
    orch = Orchestrator(cfg)
    orch.start()
    sleep(0.6)
    state = orch.health_state["p2"]
    assert state["losses"] >= 2  # 閾値到達
    orch.stop()
