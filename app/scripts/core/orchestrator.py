"""Orchestrator MVP (Phase1 Task9).

目的:
- 単一 (後で複数) Worker スタブを起動し result_queue から結果を dispatcher thread で受信し Aggregator へ反映
- start/stop シーケンス最小実装
- マルチプロセス化は後続 (ここではスレッド内で Worker を直接呼ぶ簡易版)

将来拡張プレースホルダ:
- multiprocessing.Process 生成
- control pipe / ping / restart 策
- StatsMessage / ExitNotice 処理
"""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
from typing import Iterable, Optional

from .aggregator import Aggregator, ResultRecord
from .messages import StatsMessage
from .worker import CaptureInferenceWorker


@dataclass(slots=True)
class OrchestratorConfig:
    camera_ids: Iterable[str]
    result_queue_maxsize: int = 256
    target_fps: int = 10
    worker_latency_ms: float = 2.0
    aggregator_capacity: int = 1000


class Orchestrator:
    """MVP Orchestrator。

    Phase1 では簡易化し Worker は同一プロセス内で直接 run_loop() を別スレッド実行。
    結果は result_queue を介し dispatcher_thread が Aggregator.push_result。
    """

    def __init__(self, cfg: OrchestratorConfig) -> None:
        self._cfg = cfg
        self._result_q: Queue = Queue(maxsize=cfg.result_queue_maxsize)
        self._aggregator = Aggregator(capacity=cfg.aggregator_capacity)
        self._stop_event = Event()
        self._dispatcher_thread: Optional[Thread] = None
        self._worker_threads: list[Thread] = []

    # ------------------ 公開 API ------------------ #
    def start(self) -> None:
        if self._dispatcher_thread is not None:
            raise RuntimeError("Already started")
        # Dispatcher
        self._dispatcher_thread = Thread(
            target=self._run_dispatcher, name="ResultDispatcher", daemon=True
        )
        self._dispatcher_thread.start()
        # Workers
        for cam in self._cfg.camera_ids:
            t = Thread(
                target=self._run_worker_stub,
                args=(cam,),
                name=f"Worker-{cam}",
                daemon=True,
            )
            t.start()
            self._worker_threads.append(t)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        # Worker threads join
        for t in self._worker_threads:
            t.join(timeout=timeout)
        # Drain sentinel
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=timeout)

    @property
    def aggregator(self) -> Aggregator:
        return self._aggregator

    # ------------------ 内部 ------------------ #
    def _run_worker_stub(self, camera_id: str) -> None:
        worker = CaptureInferenceWorker(
            camera_id,
            self._result_q,
            target_fps=self._cfg.target_fps,
            simulate_latency_ms=self._cfg.worker_latency_ms,
        )
        # 簡易ループ: stop_event セットまで継続
        while not self._stop_event.is_set():
            worker.run_loop(iterations=1)  # 1 フレーム単位で生成
        # 終了時: 最終 StatsMessage (現状未使用)
        _ = worker.build_stats_message()

    def _run_dispatcher(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._result_q.get(timeout=0.2)
            except Empty:
                continue
            if isinstance(item, ResultRecord):
                self._aggregator.push_result(item)
            elif isinstance(item, StatsMessage):  # まだ利用しない
                pass
            # それ以外は無視


__all__ = ["Orchestrator", "OrchestratorConfig"]
