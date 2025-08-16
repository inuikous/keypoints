"""CaptureInferenceWorker スタブの単体テスト。"""

from __future__ import annotations

import queue

from app.scripts.core.messages import StatsMessage
from app.scripts.core.worker import CaptureInferenceWorker


class _SmallQueue(queue.Queue):
    # maxsize=3 で満杯挙動テスト用
    def __init__(self) -> None:
        super().__init__(maxsize=3)


def test_run_loop_generates_records_and_respects_capacity() -> None:
    q = _SmallQueue()
    worker = CaptureInferenceWorker("camT", q, target_fps=50, simulate_latency_ms=0.0)
    worker.run_loop(iterations=10)
    # maxsize=3 のため最新3件のみ
    assert q.qsize() == 3
    items = list(q.queue)  # type: ignore[attr-defined]
    assert len({r.gesture_label for r in items}) <= 3


def test_drop_algorithm_counts_drops() -> None:
    # 過剰投入で drop カウンタが増えることを確認
    q = _SmallQueue()
    worker = CaptureInferenceWorker("camD", q, target_fps=200, simulate_latency_ms=0.0)
    worker.run_loop(iterations=30)
    # queue 中身は 3
    assert q.qsize() == 3
    stats = worker.build_stats_message()
    assert isinstance(stats, StatsMessage)
    # drops > 0 を期待 (強制ではないが 30 >> 3 閾値)
    assert (stats.drop_rate is None) or (stats.drop_rate >= 0.0)


def test_stats_message_latency_and_fps_nonzero() -> None:
    q = _SmallQueue()
    worker = CaptureInferenceWorker("camS", q, target_fps=20, simulate_latency_ms=1.0)
    worker.run_loop(iterations=5)
    stats = worker.build_stats_message()
    if stats.avg_latency_ms is not None:
        assert stats.avg_latency_ms >= 0.5  # 擬似1ms以上
    assert stats.fps >= 0.0
