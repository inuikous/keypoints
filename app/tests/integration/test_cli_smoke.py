"""CLI smoke integration test (MVP)。

短時間 (--duration 2) 実行し終了コード 0 / 統計出力を最低1回得ることを確認。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.timeout(10)
def test_cli_runs_and_outputs_stats(tmp_path: Path) -> None:
    # 簡易 XML (1 camera) を tmp に生成
    xml = tmp_path / "ApplicationConfig.xml"
    xml.write_text(
        """<ApplicationConfig>\n  <Cameras><Camera id='cam01' url='rtsp://dummy'/></Cameras>\n  <Model xml='m.xml' bin='m.bin' metadata='m.meta'/>\n  <Inference target_fps='5' device='AUTO'/>\n  <Retry connect_max_attempts='1' connect_backoff_sec='0.1'/>\n  <Buffer results_max_entries='50'/>\n  <Recording enabled='false' output_dir='results/rec'/>\n  <Export default_format='csv'/>\n  <Restart max_restarts_per_camera='1' restart_window_sec='60'/>\n  <Health ping_interval_sec='5' ping_timeout_sec='10' ping_loss_threshold='3'/>\n  <Perf latency_p95_target_ms='500' drop_rate_warn='0.1'/>\n  <GUI theme='dark'/>\n  <Logging dir='app/logs' level='INFO'/>\n</ApplicationConfig>\n""",
        encoding="utf-8",
    )
    cmd = [sys.executable, "-m", "app.main", "--config", str(xml), "--duration", "2"]
    # プロジェクトルート (本テストファイル位置: app/tests/integration) に戻して実行
    project_root = Path(__file__).resolve().parents[3]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
    assert proc.returncode == 0, proc.stderr
    assert "[STATS]" in proc.stdout
