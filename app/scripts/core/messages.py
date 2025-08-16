"""IPC メッセージ dataclass 定義。

設計要点:
- frozen + slots によりイミュータブルかつ軽量。
- pickle シリアライズ前提 (後続で msgpack 交換可能) のためトップレベル定義。
- PING/PONG 応答は StatusUpdate.ping_response フィールドで表現。

拡張指針:
- 新規フィールド追加時は後方互換性を考慮 (受信側での default 処理)。
- 大量転送性能問題発生時は __getstate__ の最適化や msgpack 化を検討。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# Control 種別の定数 (typo 防止用)
CONTROL_START = "START"
CONTROL_STOP = "STOP"
CONTROL_RELOAD = "RELOAD"
CONTROL_PING = "PING"

StatusType = str  # 実装段階で Enum 化も検討可能


@dataclass(frozen=True, slots=True)
class ControlMessage:
    """親→子 制御メッセージ。

    Attributes:
        type (str): 制御種別 (START/STOP/RELOAD/PING)。
        payload (Dict[str, Any]): 付帯情報 (例: ping_id 等)。
    """

    type: str
    payload: Dict[str, Any]


@dataclass(frozen=True, slots=True)
class StatusUpdate:
    """子→親 状態通知メッセージ。

    Attributes:
        camera_id (str): カメラ識別子。
        status (str): 現在状態 (INIT/RUNNING/RETRYING/DOWN/EXITING)。
        attempts (int): 接続/再試行回数。
        last_error (Optional[str]): 直近エラー概要。
        ping_response (Optional[str]): 応答した ping_id (PONG 意味)。
    """

    camera_id: str
    status: StatusType
    attempts: int
    last_error: Optional[str] = None
    ping_response: Optional[str] = None


@dataclass(frozen=True, slots=True)
class StatsMessage:
    """子→親 周期統計メッセージ (1秒周期想定)。

    Attributes:
        camera_id (str): カメラ識別子。
        fps (float): 推定 FPS。
        avg_latency_ms (Optional[float]): 平均レイテンシ (ms)。
        drop_rate (Optional[float]): ドロップ率 (0.0-1.0)。
    """

    camera_id: str
    fps: float
    avg_latency_ms: Optional[float]
    drop_rate: Optional[float]


@dataclass(frozen=True, slots=True)
class ExitNotice:
    """子→親 終了通知。

    Attributes:
        camera_id (str): カメラ識別子。
        code (int): 終了コード (0=正常, それ以外は異常種別)。
        reason (str): 人間可読な理由メッセージ。
    """

    camera_id: str
    code: int
    reason: str


__all__ = [
    "CONTROL_START",
    "CONTROL_STOP",
    "CONTROL_RELOAD",
    "CONTROL_PING",
    "ControlMessage",
    "StatusUpdate",
    "StatsMessage",
    "ExitNotice",
]
