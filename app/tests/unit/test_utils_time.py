"""utils_time の単体テスト。

目的: UTC / monotonic / ISO 変換の基本動作と一貫性を確認。
"""

import re
from datetime import datetime, timezone

from app.scripts.core import utils_time as ut

ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$")


def test_now_utc_timezone() -> None:
    dt = ut.now_utc()
    assert dt.tzinfo == timezone.utc


def test_isoformat_utc_format() -> None:
    s = ut.isoformat_utc(datetime(2025, 1, 2, 3, 4, 5, 123456))
    assert ISO_PATTERN.match(s), s
    assert s.endswith("Z")


def test_monotonic_ns_increasing() -> None:
    a = ut.monotonic_ns()
    b = ut.monotonic_ns()
    assert b >= a


def test_perf_counter_ms_positive() -> None:
    v = ut.perf_counter_ms()
    assert v > 0.0
