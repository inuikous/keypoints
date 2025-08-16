"""config.loader の単体テスト。"""

import textwrap
from pathlib import Path

import pytest

from app.scripts.config import loader
from app.scripts.core.errors import ConfigValidationError


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "cfg.xml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def test_load_success(tmp_path: Path) -> None:
    xml = """\
    <?xml version='1.0'?>
    <ApplicationConfig>
      <Cameras><Camera id='c1' url='rtsp://x'/></Cameras>
      <Model xml='m.xml' bin='m.bin' metadata='m.meta'/>
      <Inference target_fps='5' device='CPU'/>
      <Retry connect_max_attempts='2' connect_backoff_sec='0.5'/>
      <Buffer results_max_entries='10'/>
      <Recording enabled='true' output_dir='out'/>
      <Export default_format='csv'/>
      <Restart max_restarts_per_camera='3' restart_window_sec='300'/>
      <Health ping_interval_sec='5' ping_timeout_sec='10' ping_loss_threshold='3'/>
      <Perf latency_p95_target_ms='500' drop_rate_warn='0.05'/>
      <GUI theme='dark'/>
      <Logging dir='logs' level='INFO'/>
    </ApplicationConfig>
    """
    path = _write(tmp_path, xml)
    cfg = loader.load(path)
    assert cfg.inference.target_fps == 5
    assert cfg.cameras[0].id == "c1"


def test_missing_camera_raises(tmp_path: Path) -> None:
    xml = """\
    <ApplicationConfig>
      <Cameras></Cameras>
      <Model xml='m.xml' bin='m.bin' metadata='m.meta'/>
      <Inference target_fps='5' device='CPU'/>
      <Retry connect_max_attempts='2' connect_backoff_sec='0.5'/>
      <Buffer results_max_entries='10'/>
      <Recording enabled='true' output_dir='out'/>
      <Export default_format='csv'/>
      <Restart max_restarts_per_camera='3' restart_window_sec='300'/>
      <Health ping_interval_sec='5' ping_timeout_sec='10' ping_loss_threshold='3'/>
      <Perf latency_p95_target_ms='500' drop_rate_warn='0.05'/>
      <GUI theme='dark'/>
      <Logging dir='logs' level='INFO'/>
    </ApplicationConfig>
    """
    path = _write(tmp_path, xml)
    with pytest.raises(ConfigValidationError):
        loader.load(path)


def test_invalid_int_attr(tmp_path: Path) -> None:
    xml = """\
    <ApplicationConfig>
      <Cameras><Camera id='c1' url='rtsp://x'/></Cameras>
      <Model xml='m.xml' bin='m.bin' metadata='m.meta'/>
      <Inference target_fps='x' device='CPU'/>
      <Retry connect_max_attempts='2' connect_backoff_sec='0.5'/>
      <Buffer results_max_entries='10'/>
      <Recording enabled='true' output_dir='out'/>
      <Export default_format='csv'/>
      <Restart max_restarts_per_camera='3' restart_window_sec='300'/>
      <Health ping_interval_sec='5' ping_timeout_sec='10' ping_loss_threshold='3'/>
      <Perf latency_p95_target_ms='500' drop_rate_warn='0.05'/>
      <GUI theme='dark'/>
      <Logging dir='logs' level='INFO'/>
    </ApplicationConfig>
    """
    path = _write(tmp_path, xml)
    with pytest.raises(ConfigValidationError):
        loader.load(path)
