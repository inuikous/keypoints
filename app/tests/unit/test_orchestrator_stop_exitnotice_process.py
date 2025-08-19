"""Process mode Orchestrator STOP/ExitNotice テスト.

目的:
  * use_process=True でも STOP 制御で各 Worker から ExitNotice を受信できることを確認。
  * code=0 / reason="STOP" を検証。
注意:
  * Windows spawn に伴うオーバーヘッドを考慮し十分な猶予 (>=0.6s) を与える。
"""
from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_orchestrator_stop_collects_exitnotice_process_mode():
    cfg = OrchestratorConfig(
        camera_ids=["camP"],
        target_fps=5,
        worker_latency_ms=1.0,
        ping_interval_sec=0.3,
        ping_timeout_sec=0.6,
        use_process=True,
    )
    orch = Orchestrator(cfg)
    orch.start()
    # プロセス起動+初期ループ開始猶予
    sleep(0.7)
    orch.stop()
    notices = orch.exit_notices
    assert "camP" in notices, "Process モード ExitNotice 未収集"
    # 重複がない (1件) ことを明示確認
    assert len(notices) == 1, f"ExitNotice 重複: {notices}"
    en = notices["camP"]
    assert en.code == 0
    assert en.reason == "STOP"
