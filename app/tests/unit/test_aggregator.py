"""aggregator モジュールの単体テスト。"""

from datetime import datetime, timedelta, timezone

from app.scripts.core.aggregator import Aggregator, ResultRecord


def _rec(
    cam: str,
    ts: datetime,
    label: str = "ok",
    conf: float = 0.9,
    lat: float | None = 10.0,
) -> ResultRecord:
    return ResultRecord(
        camera_id=cam,
        timestamp_utc=ts,
        gesture_label=label,
        confidence=conf,
        latency_ms=lat,
    )


def test_push_and_query() -> None:
    agg = Aggregator(capacity=5)
    now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    agg.push_result(_rec("cam1", now))
    res = agg.query("cam1")
    assert len(res) == 1
    assert res[0].gesture_label == "ok"


def test_capacity_eviction() -> None:
    agg = Aggregator(capacity=3)
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        agg.push_result(_rec("c", base + timedelta(milliseconds=10 * i), label=str(i)))
    labels = [r.gesture_label for r in agg.query("c")]
    # 先頭2件(0,1)が破棄され 2,3,4 が残る
    assert labels == ["2", "3", "4"]


def test_snapshot_stats_fps_and_latency() -> None:
    agg = Aggregator(capacity=10)
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # 直近1秒窓内 3件, 古い1件
    agg.push_result(_rec("camX", base - timedelta(seconds=2)))  # 古い -> FPS 集計外
    for dt_offset in (0.2, 0.4, 0.8):
        agg.push_result(_rec("camX", base - timedelta(seconds=dt_offset), lat=5.0))
    snap = agg.snapshot_stats(now=base)
    st = snap["camX"]
    assert st["fps"] == 3.0
    assert abs(st["avg_latency_ms"] - 5.0) < 1e-6
    # 最も新しいレコードは base-0.2s (23:59:59.800000Z)
    assert st["last_update"].startswith("2024-12-31T23:59:59.800000Z")


def test_query_since_filter() -> None:
    agg = Aggregator(capacity=10)
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    agg.push_result(_rec("cam", base))
    agg.push_result(_rec("cam", base + timedelta(seconds=1)))
    filtered = agg.query("cam", since=base + timedelta(microseconds=1))
    assert len(filtered) == 1
    assert filtered[0].timestamp_utc == base + timedelta(seconds=1)
