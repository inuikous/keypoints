"""例外クラス定義。

設計方針:
- シンプルに Exception 継承。階層は現状不要。
- 重大度: ConfigValidationError / ModelLoadError は起動中断 (Fatal)。
- IPC/ストリーム系は再試行や再起動ポリシで扱うため軽量。
"""

from __future__ import annotations


class ConfigValidationError(Exception):
    """設定値が不正。致命的エラーとして起動中断。"""


class StreamConnectionError(Exception):
    """RTSP接続に失敗。再試行可能。"""


class ModelLoadError(Exception):
    """モデルロード致命的失敗。"""


class InferenceError(Exception):
    """単フレーム推論失敗 (継続可能)。"""


class IPCChannelError(Exception):
    """制御Pipe/Queue の異常 (切断/破損)。"""


__all__ = [
    "ConfigValidationError",
    "StreamConnectionError",
    "ModelLoadError",
    "InferenceError",
    "IPCChannelError",
]
