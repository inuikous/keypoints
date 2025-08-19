"""CaptureInferenceWorker スタブ実装 (Phase1 MVP 用).

目的:
- 実カメラ/モデルに依存せず ResultRecord を生成しキューへ投入
- Queue 満杯時のドロップアルゴリズム検証
- FPS/Latency/Drop 統計の一次集計 (簡易)

制約 (Phase1):
- RTSP 接続/前処理/モデル推論はダミー (固定レイテンシ近似)
- マルチプロセス起動は後続 Orchestrator 実装で統合

ドロップアルゴリズム:
1. put_nowait()
2. queue.Full → 直ちに oldest get_nowait() で1件破棄
3. 再度 put_nowait() 試行
4. なお失敗 (理論上並列競合) → drop_counter++ (Result 未投入)

テスト容易性のため run_loop(iterations=N) を提供し N フレーム生成後に停止できる。
"""

from __future__ import annotations

import queue
from dataclasses import dataclass
from time import perf_counter_ns, sleep
from typing import Any, Optional, Protocol, Sequence

from . import utils_time
from .aggregator import ResultRecord
from .messages import (
    StatsMessage,
    StatusUpdate,
    CONTROL_PING,
    CONTROL_STOP,
    ControlMessage,
    ExitNotice,
)


class _QueueLike(Protocol):  # pragma: no cover - 型補助
    def put_nowait(self, item: Any) -> None: ...
    def get_nowait(self) -> Any: ...
    def full(self) -> bool: ...


@dataclass(slots=True)
class WorkerStats:
    frames: int = 0
    drops: int = 0
    total_latency_ms: float = 0.0

    def fps(self, elapsed_sec: float) -> float:
        return self.frames / elapsed_sec if elapsed_sec > 0 else 0.0

    def avg_latency(self) -> Optional[float]:
        return self.total_latency_ms / self.frames if self.frames else None

    def drop_rate(self) -> Optional[float]:
        total = self.frames + self.drops
        return (self.drops / total) if total else None


class CaptureInferenceWorker:
    """スタブ Worker。

    Attributes:
        camera_id: カメラID
        result_queue: 結果送信先 (queue.Queue or multiprocessing.Queue)
        target_fps: 目標 FPS (sleep に利用)
        simulate_latency_ms: 1フレーム当たりの擬似推論レイテンシ (sleep)
    """

    _LABELS: Sequence[str] = ("gesture_a", "gesture_b", "gesture_c")

    def __init__(
        self,
        camera_id: str,
        result_queue: _QueueLike,
        target_fps: int = 10,
        simulate_latency_ms: float = 2.0,
        control_queue: Optional[_QueueLike] = None,
        respond_to_ping: bool = True,
    ) -> None:
        if target_fps <= 0:
            raise ValueError("target_fps must be > 0")
        # 基本設定
        self.camera_id = camera_id
        self._q = result_queue
        self._target_fps = target_fps
        self._simulate_latency = simulate_latency_ms / 1000.0
        # 統計用
        self._stats = WorkerStats()
        self._start_monotonic_ns: Optional[int] = None
        # 制御メッセージ (PING 等)
        self._control_q = control_queue
        self._respond_to_ping = respond_to_ping
        self._stopping = False  # STOP 制御受信後 True

    @property
    def is_stopping(self) -> bool:
        return self._stopping

    # ---------------------------- 公開 API ---------------------------- #
    def run_loop(self, iterations: int) -> None:
        """指定フレーム数だけ生成して終了 (テスト用)。"""
        if iterations <= 0 or self._stopping:
            return
        first = self._start_monotonic_ns is None
        if first:
            self._start_monotonic_ns = perf_counter_ns()
        frame_interval = 1.0 / self._target_fps
        for i in range(iterations):
            if self._stopping:  # 早期終了
                break
            loop_start = perf_counter_ns()
            self._process_control()
            self._generate_one(i)
            # FPS 近似維持 (生成時間 + 推論擬似sleep を考慮)
            elapsed = (perf_counter_ns() - loop_start) / 1e9
            remaining = frame_interval - elapsed
            if remaining > 0:
                sleep(remaining)
        # 1秒以上経過 or 初回実行であれば統計メッセージをキューへ送信
        if self._start_monotonic_ns is not None:
            elapsed_total = (perf_counter_ns() - self._start_monotonic_ns) / 1e9
            if elapsed_total >= 1.0:
                try:
                    self._q.put_nowait(self.build_stats_message())
                except queue.Full:  # 統計は落としても致命でない
                    pass
                # 次窓へリセット
                self._start_monotonic_ns = perf_counter_ns()
                self._stats = WorkerStats()

    def build_stats_message(self) -> StatsMessage:
        elapsed_sec = 0.0
        if self._start_monotonic_ns is not None:
            elapsed_sec = (perf_counter_ns() - self._start_monotonic_ns) / 1e9
        return StatsMessage(
            camera_id=self.camera_id,
            fps=self._stats.fps(elapsed_sec),
            avg_latency_ms=self._stats.avg_latency(),
            drop_rate=self._stats.drop_rate(),
        )

    # ---------------------------- 内部処理 ---------------------------- #
    def _generate_one(self, index: int) -> None:
        # 擬似キャプチャ & 推論 (sleep でレイテンシ再現)
        t0 = perf_counter_ns()
        if self._simulate_latency > 0:
            sleep(self._simulate_latency)
        t1 = perf_counter_ns()
        latency_ms = (t1 - t0) / 1e6
        label = self._LABELS[index % len(self._LABELS)]
        rec = ResultRecord(
            camera_id=self.camera_id,
            timestamp_utc=utils_time.now_utc(),
            gesture_label=label,
            confidence=0.9,
            latency_ms=latency_ms,
        )
        self._emit(rec)
        self._stats.frames += 1
        self._stats.total_latency_ms += latency_ms

    def _emit(self, rec: ResultRecord) -> None:
        try:
            self._q.put_nowait(rec)
            return
        except queue.Full:
            # 古いものを1件破棄して再試行
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(rec)
                return
            except queue.Full:
                self._stats.drops += 1
                return

    # ---------------------------- 制御処理 ---------------------------- #
    def _process_control(self) -> None:
        if not self._control_q:
            return
        try:
            msg = self._control_q.get_nowait()
        except Exception:
            return
        if not isinstance(msg, ControlMessage):
            return
        if msg.type == CONTROL_PING and self._respond_to_ping:
            ping_id = msg.payload.get("id")
            try:
                self._q.put_nowait(
                    StatusUpdate(
                        camera_id=self.camera_id,
                        status="RUNNING",
                        attempts=0,
                        last_error=None,
                        ping_response=ping_id,
                    )
                )
            except queue.Full:
                pass
        elif msg.type == CONTROL_STOP:
            # Graceful 停止: 統計送信後 ExitNotice
            self._stopping = True
            try:
                # 中途でも現時点統計を送る (best-effort)
                self._q.put_nowait(self.build_stats_message())
            except queue.Full:
                pass
            try:
                self._q.put_nowait(ExitNotice(camera_id=self.camera_id, code=0, reason="STOP"))
            except queue.Full:
                pass


__all__ = ["CaptureInferenceWorker", "WorkerStats"]
