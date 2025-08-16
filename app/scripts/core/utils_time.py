"""時間/時刻関連ユーティリティ関数群。

設計方針:
- 全て UTC / monotonic を統一使用。
- テスト容易性のため関数単位でモック可能な薄いラッパ。
- ログ/メトリクスでの使用を想定し高精度 (ns) を保持。

例:
    >>> from app.scripts.core import utils_time as ut
    >>> ts = ut.now_utc()
    >>> ts.tzinfo is not None
    True
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Final

# NOTE: ここでタイムゾーンは UTC 固定 (設計方針に従う)
UTC: Final = timezone.utc


def now_utc() -> datetime:
    """現在の UTC 時刻 (timezone aware) を返す。

    Returns:
        datetime: UTC タイムゾーン付き現在日時。
    """
    return datetime.now(UTC)


def isoformat_utc(dt: datetime) -> str:
    """UTC datetime を ISO8601 (末尾 'Z') 文字列へ変換する。

    Args:
        dt (datetime): 変換対象。naive の場合は UTC と見なす。

    Returns:
        str: ISO8601 文字列 (例: 2025-01-02T03:04:05.123456Z)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def monotonic_ns() -> int:
    """モノトニックタイマー (ns) を返す。

    Returns:
        int: 起動からの経過ナノ秒 (単調増加)。
    """
    return time.monotonic_ns()


def perf_counter_ms() -> float:
    """高精度パフォーマンスカウンタをミリ秒(float)で返す。

    Returns:
        float: 経過時間 (ms)。
    """
    return time.perf_counter() * 1000.0


__all__ = [
    "now_utc",
    "isoformat_utc",
    "monotonic_ns",
    "perf_counter_ms",
]
