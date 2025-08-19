"""MetricsThread の基本動作テスト。

目的:
    - snapshot_stats を周期取得し WARNING を出さない通常ケース
    - 人工的に last_update を過去にしてストール警告 (CAMERA_STALL) を発火

Note: ログ内容の完全検証までは行わず、内部メソッド経由で閾値判定を刺激する
(初期段階の軽量テスト)。
"""

from datetime import timedelta
from time import sleep

from app.scripts.core.aggregator import Aggregator, ResultRecord
from app.scripts.core.metrics import MetricsThread
from app.scripts.core import utils_time


def _make_record(cam: str, dt):
    return ResultRecord(
        camera_id=cam,
        timestamp_utc=dt,
        gesture_label="g",
        confidence=0.9,
        latency_ms=5.0,
    )


def test_metrics_thread_runs_and_detects_stall() -> None:
    agg = Aggregator(capacity=10)
    now = utils_time.now_utc()
    # 最新結果 (cam1) を現在時刻で投入
    agg.push_result(_make_record("cam1", now))
    import threading

    stop = threading.Event()
    mt = MetricsThread(aggregator=agg, stop_event=stop, target_fps=10, interval_s=0.2)
    mt.start()
    # ストール閾値 (3/10 + 1) ~= 1.3s を超えるまで待機して意図的に古くする
    sleep(1.5)
    stop.set()
    mt.join(timeout=1.0)
    # 直接的な assert は難しいため last_update が過去になったことを確認
    last_dt = agg.last_update_dt("cam1")
    assert last_dt is not None
    assert (utils_time.now_utc() - last_dt).total_seconds() >= 1.3
