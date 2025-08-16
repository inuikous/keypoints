"""logging_setup 初期化テスト。"""

import json
import logging
from pathlib import Path

from app.scripts.core.logging_setup import JsonFormatter, init_logging


def test_init_logging(tmp_path: Path) -> None:
    handler, listener = init_logging(tmp_path, level="INFO")
    logger = logging.getLogger("test")
    logger.info("テストログ", extra={"event": "UNIT_TEST", "camera": "cam01"})
    # listener は非同期で処理するため flush を確実に行う
    listener.stop()
    # app.log が生成され JSON Lines 1 行以上含むこと
    log_file = tmp_path / "app.log"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "ログファイルが空"
    data = json.loads(lines[-1])
    assert data.get("event") == "UNIT_TEST"
    assert data.get("camera") == "cam01"


def test_json_formatter_exc() -> None:
    fmt = JsonFormatter()
    logger = logging.getLogger("exc_test")
    rec = logger.makeRecord(
        name="exc_test",
        level=logging.ERROR,
        fn="x",
        lno=1,
        msg="err",
        args=(),
        exc_info=(ValueError, ValueError("x"), None),
    )
    out = fmt.format(rec)
    assert "exc" in out
