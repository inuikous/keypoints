"""MetricsThread: Aggregator から周期的に統計を取得しログ出力/簡易異常検知を行う。

機能:
    * interval_s 毎に Aggregator.snapshot_stats()
    * DEBUG ログ (event=METRIC_SNAPSHOT)
    * last_update_age_sec > (3/target_fps + 1.0) で WARNING (event=CAMERA_STALL)

注意: 以前 `_stop` という属性名が `threading.Thread._stop` (callable) と衝突し
TypeError("'Event' object is not callable") を誘発していたため `_stop_event` に改名。
"""

from __future__ import annotations

import logging
import threading

from .aggregator import Aggregator
from . import utils_time

logger = logging.getLogger(__name__)


class MetricsThread(threading.Thread):
    """Aggregator 監視/統計ログスレッド。"""

    def __init__(self, aggregator: Aggregator, stop_event: threading.Event, target_fps: int, interval_s: float = 1.0) -> None:
        super().__init__(name="MetricsThread", daemon=True)
        self._agg = aggregator
        self._stop_event = stop_event
        self._interval = interval_s
        self._target_fps = target_fps
        self._stall_threshold_s = (3.0 / target_fps) + 1.0 if target_fps > 0 else 2.0

    def run(self) -> None:  # pragma: no cover - ループ本体は他テストで間接検証
        while not self._stop_event.wait(self._interval):
            now = utils_time.now_utc()
            stats = self._agg.snapshot_stats(now=now)
            for cam, data in stats.items():
                logger.debug(
                    "metrics snapshot",
                    extra={
                        "event": "METRIC_SNAPSHOT",
                        "camera": cam,
                        "fps": data.get("fps"),
                        "ema_fps": data.get("ema_fps"),
                        "latency_ms": data.get("avg_latency_ms"),
                        "latency_p50_ms": data.get("latency_p50_ms"),
                        "latency_p95_ms": data.get("latency_p95_ms"),
                        "drop_rate": data.get("drop_rate"),
                    },
                )
                last_dt = self._agg.last_update_dt(cam)
                if last_dt is None:
                    continue
                age = (now - last_dt).total_seconds()
                if age > self._stall_threshold_s:
                    logger.warning(
                        "camera stalled (age=%.2fs > %.2fs)",
                        age,
                        self._stall_threshold_s,
                        extra={
                            "event": "CAMERA_STALL",
                            "camera": cam,
                        },
                    )


__all__ = ["MetricsThread"]
