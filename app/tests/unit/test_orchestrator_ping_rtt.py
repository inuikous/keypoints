"""Ping RTT 計測確認テスト.

目的:
  * PingThread により PING が送信され、StatusUpdate の pong を受け取ると last_rtt_ms が設定される。
  * 一定時間後 health_state[cam]["last_rtt_ms"] が None でない ( >0 )。
"""
from time import sleep

from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig


def test_orchestrator_ping_rtt_thread_mode():
    cfg = OrchestratorConfig(
        camera_ids=["camR"],
        target_fps=5,
        worker_latency_ms=1.0,
        ping_interval_sec=0.2,
        ping_timeout_sec=0.5,
        stop_grace_wait_sec=0.02,
    )
    orch = Orchestrator(cfg)
    orch.start()
    # 少なくとも 2 回 ping 往復が起きる程度待機
    sleep(0.8)
    hs = orch.health_state
    assert "camR" in hs
    rtt = hs["camR"].get("last_rtt_ms")
    assert rtt is not None and rtt > 0, f"RTT 未計測 rtt={rtt}"
    orch.stop()
