"""Aggregator の StatsMessage 統合 & 追加統計(p50/p95/EMA) テスト。"""

from datetime import timedelta

from app.scripts.core.aggregator import Aggregator, ResultRecord
from app.scripts.core.messages import StatsMessage
from app.scripts.core import utils_time


def test_aggregator_apply_stats_message_and_percentiles() -> None:
    """StatsMessage 適用と p50/p95, EMA 計算を検証。

    シナリオ:
        - 2 レコード (latency 10ms, 30ms)
        - StatsMessage で fps=5.0 / avg_latency_ms=20.0 / drop_rate=0.1 を上書き
        - p50 は (10,30) の中央値=20.0, p95 は 線形補間で 10 + (30-10)*0.95 ≒ 29.0
        - EMA 初回は window FPS=2 を初期値とし override 適用後 ema_fps が override 方向へ更新される
    """
    agg = Aggregator(capacity=10)
    now = utils_time.now_utc()
    agg.push_result(
        ResultRecord(
            camera_id="cam1",
            timestamp_utc=now - timedelta(milliseconds=500),
            gesture_label="g1",
            confidence=0.9,
            latency_ms=10.0,
        )
    )
    agg.push_result(
        ResultRecord(
            camera_id="cam1",
            timestamp_utc=now,
            gesture_label="g2",
            confidence=0.8,
            latency_ms=30.0,
        )
    )
    # snapshot (override 無) で初期 EMA を確定 (窓FPS=2)
    pre = agg.snapshot_stats(now=now)
    assert pre["cam1"]["fps"] == 2.0
    base_ema = pre["cam1"]["ema_fps"]
    # StatsMessage 適用 (override)
    agg.apply_stats_message(
        StatsMessage(camera_id="cam1", fps=5.0, avg_latency_ms=20.0, drop_rate=0.1)
    )
    snap = agg.snapshot_stats(now=now)
    assert "cam1" in snap
    cam = snap["cam1"]
    assert cam["drop_rate"] == 0.1
    assert cam["fps"] == 5.0  # override 反映
    assert cam["avg_latency_ms"] == 20.0  # override 反映
    # p50/p95 チェック (許容誤差)
    assert cam["latency_p50_ms"] == 20.0
    assert 28.5 <= cam["latency_p95_ms"] <= 29.5
    # EMA は override fps 方向へ移動 (alpha=0.2)
    assert cam["ema_fps"] > base_ema
    assert cam["ema_fps"] < cam["fps"]  # まだ完全には追随しない
