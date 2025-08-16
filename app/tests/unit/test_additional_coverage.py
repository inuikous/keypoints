"""追加カバレッジ向上テスト。

対象:
- config.loader: エラーパス (不正 bool, 不足要素)
- aggregator: capacity<=0 例外
- logging_setup: init_logging 異常引数 level (fallback)
- orchestrator: 二重 start 防止
- worker: target_fps<=0 例外
"""

from __future__ import annotations

import queue
from pathlib import Path

import pytest

from app.scripts.config import loader
from app.scripts.core.aggregator import Aggregator
from app.scripts.core.errors import ConfigValidationError
from app.scripts.core.logging_setup import init_logging
from app.scripts.core.orchestrator import Orchestrator, OrchestratorConfig
from app.scripts.core.worker import CaptureInferenceWorker


def test_loader_bool_error(tmp_path: Path) -> None:
    xml = tmp_path / "bad.xml"
    xml.write_text(
        """<ApplicationConfig>\n  <Cameras><Camera id='c' url='u'/></Cameras>\n  <Model xml='m.xml' bin='m.bin' metadata='m.meta'/>\n  <Inference target_fps='5' device='AUTO'/>\n  <Retry connect_max_attempts='1' connect_backoff_sec='0.1'/>\n  <Buffer results_max_entries='10'/>\n  <Recording enabled='notbool' output_dir='out'/>\n  <Export default_format='csv'/>\n  <Restart max_restarts_per_camera='1' restart_window_sec='60'/>\n  <Health ping_interval_sec='5' ping_timeout_sec='10' ping_loss_threshold='3'/>\n  <Perf latency_p95_target_ms='500' drop_rate_warn='0.1'/>\n  <GUI theme='dark'/>\n  <Logging dir='app/logs' level='INFO'/>\n</ApplicationConfig>\n""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigValidationError):
        loader.load(xml)


def test_loader_missing_element(tmp_path: Path) -> None:
    xml = tmp_path / "bad2.xml"
    xml.write_text("""<ApplicationConfig></ApplicationConfig>""", encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        loader.load(xml)


def test_aggregator_capacity_error() -> None:
    with pytest.raises(ValueError):
        Aggregator(0)


def test_logging_setup_level_fallback(tmp_path: Path) -> None:
    handler, listener = init_logging(tmp_path, level="NOT_A_LEVEL")
    listener.stop()
    assert handler is not None


def test_orchestrator_double_start() -> None:
    orch = Orchestrator(
        OrchestratorConfig(camera_ids=["x"], target_fps=1, worker_latency_ms=0.0)
    )
    orch.start()
    with pytest.raises(RuntimeError):
        orch.start()
    orch.stop()


def test_worker_invalid_fps() -> None:
    q = queue.Queue()
    with pytest.raises(ValueError):
        CaptureInferenceWorker("c", q, target_fps=0)
