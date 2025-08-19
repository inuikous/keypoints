"""Orchestrator STOP/ExitNotice 振る舞いテスト.

目的:
  * start -> stop シーケンスで CONTROL_STOP がワーカーに届き ExitNotice を受信できる
  * exit_notices プロパティにカメラ毎 1 件格納され code=0 / reason="STOP" を確認
"""
from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_orchestrator_stop_collects_exitnotice_thread_mode():
    cfg = OrchestratorConfig(camera_ids=["camA"], target_fps=5, worker_latency_ms=1.0, ping_interval_sec=0.2, ping_timeout_sec=0.5)
    orch = Orchestrator(cfg)
    orch.start()
    # 少し動かして結果/ステータス生成を促す
    sleep(0.4)
    orch.stop()
    notices = orch.exit_notices
    assert "camA" in notices, "ExitNotice が収集されていない"
    en = notices["camA"]
    assert en.code == 0
    assert en.reason == "STOP"
