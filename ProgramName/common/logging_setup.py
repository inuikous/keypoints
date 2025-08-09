"""ロギング初期化ユーティリティ.

シンプルなロガー構成を提供。必要に応じてJSONや構造化ログへ拡張。
"""
from __future__ import annotations

import logging
from logging import Logger

def init_logging(level: str = "INFO") -> None:
    """ルートロガーを初期化する.

    Args:
        level (str): ログレベル文字列 (DEBUG/INFO/...).
    """
    if logging.getLogger().handlers:
        return  # 再初期化回避
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

def get_logger(name: str) -> Logger:
    """名前付きロガーを取得."""
    return logging.getLogger(name)
