"""集中ロギング初期化モジュール。

親プロセス:
    init_logging(log_dir, level) -> (log_queue, listener)
子プロセス:
    configure_worker_logging(log_queue)

JSON Lines フォーマット (例):
{"ts":"2025-08-16T00:00:00.123Z","level":"INFO","event":"STARTUP_COMPLETE","msg":"起動完了","pid":1234}
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

# ------------------------------ フォーマッタ ------------------------------ #


class JsonFormatter(logging.Formatter):
    """JSON Lines 形式でログを整形するフォーマッタ。"""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        data = {
            "ts": datetime.utcfromtimestamp(record.created)
            .replace(tzinfo=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "event": getattr(record, "event", None),
            "msg": record.getMessage(),
            "pid": record.process,
            "name": record.name,
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        # 追加メトリクス系 (存在時のみ)
        for k in ("camera", "latency_ms", "fps", "drop_rate"):
            v = getattr(record, k, None)
            if v is not None:
                data[k] = v
        return json.dumps(data, ensure_ascii=False)


# ------------------------------ 初期化関数 ------------------------------ #


def init_logging(
    log_dir: Path, level: str = "INFO"
) -> Tuple[logging.handlers.QueueHandler, logging.handlers.QueueListener]:
    """親プロセス用集中ロギング初期化。

    Args:
        log_dir (Path): ログディレクトリ。
        level (str): ルートログレベル。

    Returns:
        (QueueHandler, QueueListener): 子プロセス用ハンドラと listener。
    """
    from multiprocessing import Queue  # 遅延 import (起動時間最適化)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_queue: "Queue[logging.LogRecord]" = Queue()  # type: ignore[type-arg]

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(JsonFormatter())
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())

    listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
    listener.start()

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # 子プロセスから投入されるレコードを受け取るため QueueHandler を1つだけ root に登録
    root.handlers.clear()
    root.addHandler(logging.handlers.QueueHandler(log_queue))

    return root.handlers[0], listener


def configure_worker_logging(
    log_queue,
) -> None:  # noqa: ANN001 - multiprocess Queue 型は単純
    """子プロセス側ロギング設定。

    Args:
        log_queue: 親プロセスで生成された Queue インスタンス。
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(logging.handlers.QueueHandler(log_queue))


__all__ = ["init_logging", "configure_worker_logging", "JsonFormatter"]
