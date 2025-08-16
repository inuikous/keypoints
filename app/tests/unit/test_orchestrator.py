"""Orchestrator MVP の単体テスト。

目的:
- start/stop が例外なく動作
- Worker スレッドが結果をキュー経由で Aggregator に反映
"""

from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_orchestrator_start_and_collect_results() -> None:
    cfg = OrchestratorConfig(
        camera_ids=["camA"],
        target_fps=20,
        worker_latency_ms=0.0,
        aggregator_capacity=50,
    )
    orch = Orchestrator(cfg)
    orch.start()
    # 少し待つ間にいくつか結果が蓄積されるはず
    sleep(0.3)
    orch.stop()
    results = orch.aggregator.query("camA")
    assert len(results) > 0
    # タイムスタンプが単調増加 (緩く検証)
    ts_list = [r.timestamp_utc for r in results]
    assert ts_list == sorted(ts_list)


def test_orchestrator_multiple_cameras() -> None:
    cfg = OrchestratorConfig(
        camera_ids=["c1", "c2"],
        target_fps=10,
        worker_latency_ms=0.0,
        aggregator_capacity=20,
    )
    orch = Orchestrator(cfg)
    orch.start()
    sleep(0.4)
    orch.stop()
    r1 = orch.aggregator.query("c1")
    r2 = orch.aggregator.query("c2")
    assert r1 and r2
