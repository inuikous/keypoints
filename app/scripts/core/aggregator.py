"""推論結果集約 Aggregator 実装 (Phase1 MVP 版)。

責務:
- カメラ毎のリングバッファ保持 (最新優先 / capacity 超で古い順自動破棄)
- クエリ (since 指定) / スナップショット統計 (FPS, 平均レイテンシ, 最終更新)

設計簡略 (将来拡張点):
- drop_rate: Worker 側で送信される StatsMessage 導入フェーズまで None。
- StatsMessage / ExitNotice 受信 API は後続フェーズで拡張 (Phase2+)。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, Iterable, List, Optional

from . import utils_time


@dataclass(frozen=True, slots=True)
class ResultRecord:
    """単一推論結果レコード。

    Attributes:
        camera_id (str): カメラID。
        timestamp_utc (datetime): 推論完了UTC時刻 (tz-aware)。
        gesture_label (str): 予測ラベル。
        confidence (float): 信頼度 0.0-1.0。
        latency_ms (Optional[float]): 前処理+推論時間 (ms)。
    """

    camera_id: str
    timestamp_utc: datetime
    gesture_label: str
    confidence: float
    latency_ms: Optional[float]


class Aggregator:
    """結果集約と軽量統計計算を行うコンポーネント。

    スレッド安全性: Phase1 では単一スレッド利用 (ResultDispatcherThread 内) 想定のため
    ロック不要。将来マルチスレッド化する際は per-camera Lock もしくは RWLock 追加検討。
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity は正数である必要があります")
        self._capacity = capacity
        self._buffers: Dict[str, Deque[ResultRecord]] = {}

    # ------------------------------ 公開 API ------------------------------ #
    def push_result(self, record: ResultRecord) -> None:
        """結果を対応するカメラバッファへ追加する。

        古いデータは deque(maxlen) により自動破棄される。
        """
        buf = self._buffers.get(record.camera_id)
        if buf is None:
            buf = deque(maxlen=self._capacity)
            self._buffers[record.camera_id] = buf
        buf.append(record)

    def query(
        self, camera_id: str, since: Optional[datetime] = None
    ) -> List[ResultRecord]:
        """カメラIDでフィルタし (オプションで since 以降) の結果を返す。"""
        buf = self._buffers.get(camera_id)
        if not buf:
            return []
        if since is None:
            return list(buf)
        return [r for r in buf if r.timestamp_utc >= since]

    def snapshot_stats(
        self, now: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """全カメラ統計を辞書で返す。

        統計項目:
            fps: 直近1秒に含まれるレコード数 (秒窓: (now-1s, now])
            avg_latency_ms: 同じ1秒窓内レコードの平均 (latency_ms が None は除外)
            last_update: 最終結果時刻 ISO8601
            drop_rate: None (Phase2 で計算導入)
        """
        if now is None:
            now = utils_time.now_utc()
        window_start = now - timedelta(seconds=1)
        out: Dict[str, Dict[str, Any]] = {}
        for cam, buf in self._buffers.items():
            if not buf:
                continue
            # FPS 計算
            recent = [r for r in buf if r.timestamp_utc > window_start]
            fps = float(len(recent))
            # 平均レイテンシ (同じ 1 秒窓)
            latencies = [r.latency_ms for r in recent if r.latency_ms is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else None
            # バッファ挿入順と時刻順が一致しない場合があるため明示的に最大時刻を計算
            last_ts = max(r.timestamp_utc for r in buf)
            out[cam] = {
                "fps": fps,
                "avg_latency_ms": avg_latency,
                "last_update": utils_time.isoformat_utc(last_ts),
                "drop_rate": None,
            }
        return out

    # ------------------------------ 補助/検査 ------------------------------ #
    def cameras(self) -> Iterable[str]:  # pragma: no cover - 極小ヘルパ
        return self._buffers.keys()


__all__ = ["ResultRecord", "Aggregator"]
