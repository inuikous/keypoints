"""Multiprocessing worker entry (v0.6+ updated).

Purpose:
    * Launch `CaptureInferenceWorker` in a separate process.
    * Support STOP via ControlMessage so that ExitNotice is emitted (parity with thread mode).
    * Retain compatibility with simple run loop used in tests.
"""
from __future__ import annotations

from time import sleep
from queue import Full

from .worker import CaptureInferenceWorker
from .messages import CONTROL_STOP


def run_capture_inference_worker_process(
    camera_id: str,
    result_queue,
    control_queue,
    stop_event,  # 互換: 旧 stop_event も併用 (緊急停止用)。通常は CONTROL_STOP を使用。
    target_fps: int,
    latency_ms: float,
    respond_to_ping: bool,
    simulate_hang_on_stop: bool = False,
    log_queue=None,
) -> None:
    # 中央ログ有効時: 親から渡された log_queue で設定
    if log_queue is not None:
        try:  # 遅延 import で起動コスト最小化
            from .logging_setup import configure_worker_logging

            configure_worker_logging(log_queue)
        except Exception:  # pragma: no cover
            pass
    worker = CaptureInferenceWorker(
        camera_id=camera_id,
        result_queue=result_queue,
        target_fps=target_fps,
        simulate_latency_ms=latency_ms,
        control_queue=control_queue,
        respond_to_ping=respond_to_ping,
    )
    frame_interval = 1.0 / target_fps
    # ループ: STOP ControlMessage を受けると worker._stopping が True になり run_loop() 側で抜ける。
    while not stop_event.is_set() and not getattr(worker, "is_stopping", False):
        worker.run_loop(iterations=1)
        sleep(min(0.001, frame_interval / 10))
    if simulate_hang_on_stop and not stop_event.is_set():  # テスト用: STOP 後に敢えてハング
        sleep(10)  # 十分長くして親側 terminate 経路を誘発
    # STOP 経路であれば Worker が自身で StatsMessage/ExitNotice を送信済み。
    # stop_event による強制終了経路 (緊急) の場合のみ最後の統計送信を試みる。
    if not getattr(worker, "is_stopping", False):
        try:
            result_queue.put_nowait(worker.build_stats_message())
        except Full:
            pass
