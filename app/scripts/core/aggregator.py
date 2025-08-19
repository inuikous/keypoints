"""推論結果集約 Aggregator 実装。

Phase2 で以下の高度統計を追加済:
    - latency_p50_ms / latency_p95_ms (1秒窓レイテンシ分位点)
    - ema_fps (指数移動平均 FPS, alpha=0.2)
    - StatsMessage による fps / avg_latency_ms / drop_rate オーバーライド

責務:
    * カメラ毎リングバッファ保持 (最新優先 / capacity 超で古い順自動破棄)
    * クエリ (since 指定)
    * スナップショット統計算出 (瞬間FPS, EMA FPS, 平均/分位レイテンシ, drop_rate, 最終更新時刻)
    * StatsMessage 適用 (worker 事前集計値優先統合)

注意:
    - 現時点でマルチスレッド排他は不要 (単一 dispatcher スレッド想定)。
    - マルチプロセス化時は親プロセス専有アクセスを前提とし Lock を後付け可能。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, Iterable, List, Optional

from . import utils_time
from .messages import StatsMessage


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
        # StatsMessage オーバーライド保持
        self._stats_overrides: Dict[str, StatsMessage] = {}
        # EMA FPS 保持
        self._ema_fps: Dict[str, float] = {}
        self._ema_alpha: float = 0.2

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
            p50 = p95 = None
            if latencies:
                sorted_l = sorted(latencies)
                def _pct(values: List[float], pct: float) -> float:
                    if not values:
                        return float("nan")
                    k = (len(values) - 1) * pct
                    i = int(k)
                    if i == k:
                        return values[i]
                    return values[i] + (values[i + 1] - values[i]) * (k - i)
                p50 = _pct(sorted_l, 0.5)
                p95 = _pct(sorted_l, 0.95)
            # バッファ挿入順と時刻順が一致しない場合があるため明示的に最大時刻を計算
            last_ts = max(r.timestamp_utc for r in buf)
            # EMA FPS
            prev = self._ema_fps.get(cam)
            ema_fps = fps if prev is None else prev + self._ema_alpha * (fps - prev)
            self._ema_fps[cam] = ema_fps

            entry: Dict[str, Any] = {
                "fps": fps,
                "avg_latency_ms": avg_latency,
                "last_update": utils_time.isoformat_utc(last_ts),
                "drop_rate": None,
                "latency_p50_ms": p50,
                "latency_p95_ms": p95,
                "ema_fps": ema_fps,
            }
            override = self._stats_overrides.get(cam)
            if override:
                if override.fps is not None:
                    # override fps を使い EMA も更新して表示
                    self._ema_fps[cam] = self._ema_fps[cam] + self._ema_alpha * (override.fps - self._ema_fps[cam])
                    entry["fps"] = override.fps
                    entry["ema_fps"] = self._ema_fps[cam]
                if override.avg_latency_ms is not None:
                    entry["avg_latency_ms"] = override.avg_latency_ms
                entry["drop_rate"] = override.drop_rate
            out[cam] = entry
        return out

    # ------------------------------ 補助/検査 ------------------------------ #
    def cameras(self) -> Iterable[str]:  # pragma: no cover - 極小ヘルパ
        return self._buffers.keys()

    def apply_stats_message(self, msg: StatsMessage) -> None:
        """StatsMessage を適用し snapshot_stats 出力へ反映。"""
        self._stats_overrides[msg.camera_id] = msg

    def last_update_dt(self, camera_id: str) -> Optional[datetime]:
        buf = self._buffers.get(camera_id)
        if not buf:
            return None
        return max(r.timestamp_utc for r in buf)


__all__ = ["ResultRecord", "Aggregator"]
