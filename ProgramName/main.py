"""エントリーポイント.

This module serves as the application entry point.

Running example (Windows cmd):
    .venv\Scripts\python -m ProgramName.main

"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    """アプリケーションのメイン処理を実行する.

    Notes:
        現時点では雛形。実装は後続で追加する。
    """
    logger.info("Application started")
    # TODO: 実装を追加
    logger.info("Application finished")


if __name__ == "__main__":  # pragma: no cover
    main()
