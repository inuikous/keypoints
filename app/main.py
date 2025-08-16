"""CLI エントリーポイント (Phase1 Task10)."""

from __future__ import annotations

import argparse
import signal
from pathlib import Path
from threading import Event
from time import sleep

from app.scripts.config import loader as config_loader
from app.scripts.core.logging_setup import init_logging
from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig

_shutdown_event = Event()


def _handle_sig(signum, frame):  # noqa: D401, ANN001
    _shutdown_event.set()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hand Gesture Analyzer MVP")
    p.add_argument("--config", required=True, help="Path to ApplicationConfig.xml")
    p.add_argument("--duration", type=int, default=10, help="Run seconds (MVP demo)")
    p.add_argument("--log-level", default="INFO", help="Logging level")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    cfg_path = Path(args.config)
    config = config_loader.load(cfg_path)

    # Logging (parent)
    _, listener = init_logging(Path(config.logging.dir), level=args.log_level)

    # Orchestrator (use simplified internal list of cameras)
    orch = Orchestrator(
        OrchestratorConfig(
            camera_ids=[c.id for c in config.cameras],
            target_fps=config.inference.target_fps,
            worker_latency_ms=2.0,
            aggregator_capacity=config.buffer.results_max_entries,
        )
    )
    orch.start()

    for sig in (signal.SIGINT, signal.SIGTERM):  # Ctrl+C 等
        signal.signal(sig, _handle_sig)

    # Demo loop (duration or earlier shutdown)
    remaining = args.duration
    while remaining > 0 and not _shutdown_event.is_set():
        sleep(1)
        remaining -= 1
        # 簡易統計出力
        snap = orch.aggregator.snapshot_stats()
        if snap:
            print("[STATS]", snap)

    orch.stop()
    listener.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
