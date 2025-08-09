"""共通例外クラス定義.

プロジェクト内で投げる独自例外はこの基底を継承して揃える。

使用指針:
    - 例外メッセージは『行為+対象+期待vs実際+次アクション』を意識
    - 原因の伝播には `raise <NewError>(...) from err` を活用
"""
from __future__ import annotations

class ProjectError(Exception):
    """全ての独自例外の基底."""

class ConfigurationError(ProjectError):
    """設定ファイルや必須パラメータ不備."""

class ValidationError(ProjectError):
    """入力値の検証失敗."""

class ExternalServiceError(ProjectError):
    """外部サービス呼び出し失敗."""
