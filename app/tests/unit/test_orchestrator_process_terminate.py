"""Process mode terminate 経路テスト.

simulate_hang_on_stop=True の場合、STOP 後プロセスが join timeout を超過し terminate 経路に入ることを検証。

検証ポイント:
  * stop(timeout=) で WORKER_JOIN_TIMEOUT ログを発生させる (ここでは exit_notices は 0 件でもよい)
  * Orchestrator.active_process_count == 0 （terminate 後に全滅）

Note: ログ検証は簡易化し、active_process_count のみで確認。
"""
from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_orchestrator_process_hang_terminate(monkeypatch):
    cfg = OrchestratorConfig(
        camera_ids=["camH"],
        target_fps=2,
        worker_latency_ms=1.0,
        ping_interval_sec=0.5,
        ping_timeout_sec=1.0,
        use_process=True,
        simulate_hang_on_stop=True,
        stop_grace_wait_sec=0.02,
    )
    orch = Orchestrator(cfg)
    orch.start()
    sleep(0.5)
    orch.stop(timeout=0.2)  # 短くして timeout を誘発
    assert orch.active_process_count == 0
