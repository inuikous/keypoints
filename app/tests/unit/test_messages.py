"""messages モジュールの単体テスト。

目的: dataclass の不変性 / フィールド保持 / slots 動作の確認。
"""

import pytest

from app.scripts.core import messages as m


def test_control_message_basic() -> None:
    msg = m.ControlMessage(type=m.CONTROL_PING, payload={"ping_id": "abc"})
    assert msg.type == m.CONTROL_PING
    assert msg.payload["ping_id"] == "abc"


def test_status_update_immutability() -> None:
    su = m.StatusUpdate(camera_id="cam01", status="RUNNING", attempts=1)
    with pytest.raises(AttributeError):
        # frozen dataclass のため再代入不可
        su.status = "DOWN"  # type: ignore[attr-defined]


def test_stats_message_fields() -> None:
    st = m.StatsMessage(camera_id="cam01", fps=9.9, avg_latency_ms=12.3, drop_rate=0.1)
    assert st.fps == 9.9
    assert st.avg_latency_ms == 12.3
    assert st.drop_rate == 0.1


def test_exit_notice_repr() -> None:
    en = m.ExitNotice(camera_id="cam01", code=0, reason="ok")
    r = repr(en)
    assert "ExitNotice" in r and "cam01" in r
