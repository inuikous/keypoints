"""Orchestrator (v0.7 clean)

Features:
    - Graceful STOP with configurable stop_grace_wait_sec
    - Process join timeout fallback terminate/kill
    - Ping RTT (last_rtt_ms) tracking
    - simulate_hang_on_stop flag (process workers) for termination path tests
    - enable_central_logging placeholder (no-op for now)
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from multiprocessing import Event as MpEvent, Process, Queue as MpQueue, get_start_method, set_start_method
from queue import Empty, Queue
from threading import Event, Thread
from typing import Dict, Iterable, Optional, Union

from .aggregator import Aggregator, ResultRecord
from .messages import CONTROL_PING, CONTROL_STOP, ControlMessage, ExitNotice, StatsMessage, StatusUpdate
from .metrics import MetricsThread
from .worker import CaptureInferenceWorker
from .logging_setup import init_logging, configure_worker_logging  # added


@dataclass(slots=True)
class OrchestratorConfig:
    camera_ids: Iterable[str]
    result_queue_maxsize: int = 256
    target_fps: int = 10
    worker_latency_ms: float = 2.0
    aggregator_capacity: int = 1000
    use_process: bool = False
    ping_interval_sec: float = 5.0
    ping_timeout_sec: float = 10.0
    ping_loss_threshold: int = 3
    respond_to_ping: bool = True
    stop_grace_wait_sec: float = 0.05  # WAIT time after STOP before setting stop_event
    enable_central_logging: bool = False  # placeholder not implemented
    simulate_hang_on_stop: bool = False  # test helper for termination path


class Orchestrator:
    def __init__(self, cfg: OrchestratorConfig) -> None:
        self._cfg = cfg
        if cfg.use_process:
            try:  # pragma: no cover
                get_start_method()
            except RuntimeError:  # pragma: no cover
                set_start_method("spawn")
            self._result_q = MpQueue(maxsize=cfg.result_queue_maxsize)
        else:
            self._result_q = Queue(maxsize=cfg.result_queue_maxsize)
        # below lines must remain indented within __init__
        self._aggregator = Aggregator(capacity=cfg.aggregator_capacity)
        self._stop_event = Event()
        # internal holders (avoid newer syntax for max compatibility)
        self._dispatcher_thread = None
        self._metrics_thread = None
        self._ping_thread = None
        self._worker_threads = []
        self._worker_procs = []
        self._proc_stop_event = None
        self._control_queues = {}
        self._ping_state = {}
        self._exit_notices = {}
        self._logger = logging.getLogger(__name__)

    def start(self) -> None:
        if self._dispatcher_thread is not None:
            raise RuntimeError("Already started")
        # central logging (optional)
        if self._cfg.enable_central_logging and not getattr(self, "_log_listener", None):
            try:
                from pathlib import Path
                handler, listener, log_queue = init_logging(Path("logs"))
                self._log_listener = listener
                self._log_queue = log_queue
            except Exception:  # pragma: no cover
                pass
        self._dispatcher_thread = Thread(target=self._run_dispatcher, name="ResultDispatcher", daemon=True)
        self._dispatcher_thread.start()
        self._metrics_thread = MetricsThread(
            aggregator=self._aggregator,
            stop_event=self._stop_event,
            target_fps=self._cfg.target_fps,
            interval_s=1.0,
        )
        self._metrics_thread.start()
        self._ping_thread = Thread(target=self._run_ping_loop, name="PingThread", daemon=True)
        self._ping_thread.start()
        if self._cfg.use_process:
            self._spawn_process_workers()
        else:
            for cam in self._cfg.camera_ids:
                self._spawn_thread_worker(cam)

    def stop(self, timeout: float = 5.0) -> None:
        for cam, q in self._control_queues.items():
            try:
                q.put_nowait(ControlMessage(type=CONTROL_STOP, payload={}))
            except Exception:  # pragma: no cover
                pass
        time.sleep(self._cfg.stop_grace_wait_sec)
        for t in self._worker_threads:
            t.join(timeout=timeout)
            if t.is_alive():  # pragma: no cover
                self._logger.warning("worker thread join timeout", extra={"event": "WORKER_JOIN_TIMEOUT", "thread": t.name})
        for p in list(self._worker_procs):
            p.join(timeout)
            if p.is_alive():  # pragma: no cover
                self._logger.warning("worker process join timeout", extra={"event": "WORKER_JOIN_TIMEOUT", "proc_name": p.name})
                try:
                    p.terminate()
                    p.join(0.5)
                except Exception:  # pragma: no cover
                    pass
                if p.is_alive():  # pragma: no cover
                    self._logger.error(
                        "worker process still alive after terminate; killing", extra={"event": "WORKER_FORCE_KILL", "proc_name": p.name}
                    )
                    try:
                        p.kill()
                        p.join(0.2)
                    except Exception:  # pragma: no cover
                        pass
        self._stop_event.set()
        if self._proc_stop_event:
            self._proc_stop_event.set()
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=timeout)
        if self._metrics_thread:
            self._metrics_thread.join(timeout=timeout)
        if self._ping_thread:
            self._ping_thread.join(timeout=timeout)
        try:
            self._logger.info("shutdown complete", extra={"event": "SHUTDOWN_COMPLETE", "workers": len(self._control_queues)})
        finally:
            if getattr(self, "_log_listener", None):  # central logging cleanup
                try:
                    self._log_listener.stop()
                except Exception:
                    pass

    @property
    def aggregator(self) -> Aggregator:
        return self._aggregator

    @property
    def health_state(self) -> Dict[str, Dict[str, object]]:
        return {k: dict(v) for k, v in self._ping_state.items()}

    @property
    def exit_notices(self) -> Dict[str, ExitNotice]:
        return dict(self._exit_notices)

    @property
    def active_process_count(self) -> int:
        return sum(1 for p in self._worker_procs if p.is_alive())

    def _spawn_thread_worker(self, camera_id: str) -> None:
        self._control_queues[camera_id] = Queue(maxsize=16)
        self._ping_state[camera_id] = {
            "last_id": None,
            "sent_ts": None,
            "responded": True,
            "losses": 0,
            "down": False,
            "last_rtt_ms": None,
        }
        t = Thread(target=self._run_worker_stub, args=(camera_id,), name=f"Worker-{camera_id}", daemon=True)
        t.start()
        self._worker_threads.append(t)

    def _spawn_process_workers(self) -> None:  # pragma: no cover
        from .process_worker_entry import run_capture_inference_worker_process
        from multiprocessing import Queue as MpQueue

        self._proc_stop_event = MpEvent()
        for cam in self._cfg.camera_ids:
            ctrl_q = MpQueue(maxsize=16)
            self._control_queues[cam] = ctrl_q
            self._ping_state[cam] = {
                "last_id": None,
                "sent_ts": None,
                "responded": True,
                "losses": 0,
                "down": False,
                "last_rtt_ms": None,
            }
            extra_args = (
                cam,
                self._result_q,
                ctrl_q,
                self._proc_stop_event,
                self._cfg.target_fps,
                self._cfg.worker_latency_ms,
                self._cfg.respond_to_ping,
                self._cfg.simulate_hang_on_stop,
            )
            if getattr(self, "_log_queue", None):  # append log queue for worker side config
                extra_args = extra_args + (self._log_queue,)
            p = Process(target=run_capture_inference_worker_process, name=f"WProc-{cam}", args=extra_args, daemon=True)
            p.start()
            self._worker_procs.append(p)

    def _run_worker_stub(self, camera_id: str) -> None:  # pragma: no cover
        worker = CaptureInferenceWorker(
            camera_id,
            self._result_q,
            target_fps=self._cfg.target_fps,
            simulate_latency_ms=self._cfg.worker_latency_ms,
            control_queue=self._control_queues[camera_id],
            respond_to_ping=self._cfg.respond_to_ping,
        )
        while not self._stop_event.is_set():
            worker.run_loop(iterations=1)
            if getattr(worker, "is_stopping", False):
                break

    def _run_dispatcher(self) -> None:  # pragma: no cover
        while not self._stop_event.is_set():
            try:
                item = self._result_q.get(timeout=0.2)
            except Empty:
                continue
            if isinstance(item, ResultRecord):
                self._aggregator.push_result(item)
            elif isinstance(item, StatsMessage):
                self._aggregator.apply_stats_message(item)
            elif isinstance(item, StatusUpdate) and item.ping_response:
                st = self._ping_state.get(item.camera_id)
                if st and st.get("last_id") == item.ping_response:
                    sent_ts = st.get("sent_ts")
                    if isinstance(sent_ts, float):
                        rtt_ms = (time.monotonic() - sent_ts) * 1000.0
                        # 超高速(ほぼ同一 tick)の場合 0.0 になるのを避け、テスト容易性のため最小正値を与える
                        if rtt_ms <= 0.0:
                            rtt_ms = 0.001
                        st["last_rtt_ms"] = rtt_ms
                    st["responded"] = True
                    st["losses"] = 0
                    if st.get("down"):
                        st["down"] = False
                        self._logger.info(
                            "camera recovered after ping losses",
                            extra={"event": "CAMERA_RECOVER", "camera": item.camera_id},
                        )
            elif isinstance(item, ExitNotice):
                self._exit_notices[item.camera_id] = item

    def _run_ping_loop(self) -> None:  # pragma: no cover
        interval = self._cfg.ping_interval_sec
        timeout = self._cfg.ping_timeout_sec
        thresh = self._cfg.ping_loss_threshold
        while not self._stop_event.wait(interval):
            now = time.monotonic()
            for cam, q in self._control_queues.items():
                st = self._ping_state[cam]
                last_sent = st["sent_ts"]
                if st["last_id"] and not st["responded"] and isinstance(last_sent, float):
                    if now - last_sent > timeout:
                        st["losses"] = int(st["losses"]) + 1
                        st["responded"] = True
                        self._logger.warning(
                            "ping timeout (camera=%s losses=%s)", cam, st["losses"], extra={"event": "PING_TIMEOUT", "camera": cam}
                        )
                        if st["losses"] >= thresh and not st.get("down"):
                            st["down"] = True
                            self._logger.error(
                                "camera down (ping losses >= %s)", thresh, extra={"event": "CAMERA_DOWN", "camera": cam}
                            )
                            try:
                                self._result_q.put_nowait(
                                    StatusUpdate(camera_id=cam, status="DOWN", attempts=0, last_error="ping_timeout")
                                )
                            except Exception:
                                pass
                if st.get("responded", True):
                    ping_id = f"{cam}-{int(time.time()*1000)}"
                    try:
                        q.put_nowait(ControlMessage(type=CONTROL_PING, payload={"id": ping_id}))
                        st["last_id"] = ping_id
                        st["sent_ts"] = now
                        st["responded"] = False
                    except Exception:
                        self._logger.warning(
                            "control queue full (camera=%s)", cam, extra={"event": "PING_SEND_FAIL", "camera": cam}
                        )

__all__ = ["Orchestrator", "OrchestratorConfig"]
