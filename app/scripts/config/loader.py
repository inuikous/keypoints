"""ApplicationConfig.xml ローダー。

責務:
- XML 解析 / 構造体(dataclass) 化
- 必須属性/範囲検証
- Config オブジェクト生成

設計メモ:
- 外部依存最小化のため標準ライブラリ ElementTree 使用。
- バリデーション失敗時は ConfigValidationError。
- 数値/float 変換エラーも同例外にラップ。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List

from app.scripts.core.errors import ConfigValidationError

# ------------------------------ dataclass 群 ------------------------------ #


@dataclass(frozen=True, slots=True)
class CameraConfig:
    id: str
    url: str


@dataclass(frozen=True, slots=True)
class ModelConfig:
    ir_xml: str
    ir_bin: str
    metadata: str


@dataclass(frozen=True, slots=True)
class InferenceConfig:
    target_fps: int
    device: str


@dataclass(frozen=True, slots=True)
class RetryConfig:
    connect_max_attempts: int
    connect_backoff_sec: float


@dataclass(frozen=True, slots=True)
class BufferConfig:
    results_max_entries: int


@dataclass(frozen=True, slots=True)
class RecordingConfig:
    enabled: bool
    output_dir: str


@dataclass(frozen=True, slots=True)
class ExportConfig:
    default_format: str


@dataclass(frozen=True, slots=True)
class RestartConfig:
    max_restarts_per_camera: int
    restart_window_sec: int


@dataclass(frozen=True, slots=True)
class HealthConfig:
    ping_interval_sec: int
    ping_timeout_sec: int
    ping_loss_threshold: int


@dataclass(frozen=True, slots=True)
class PerfConfig:
    latency_p95_target_ms: int
    drop_rate_warn: float


@dataclass(frozen=True, slots=True)
class GUIConfig:
    theme: str


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    dir: str
    level: str


@dataclass(frozen=True, slots=True)
class Config:
    cameras: List[CameraConfig]
    model: ModelConfig
    inference: InferenceConfig
    retry: RetryConfig
    buffer: BufferConfig
    recording: RecordingConfig
    export: ExportConfig
    restart: RestartConfig
    health: HealthConfig
    perf: PerfConfig
    gui: GUIConfig
    logging: LoggingConfig


# ------------------------------ ロード処理 ------------------------------ #


def load(path: Path) -> Config:  # noqa: D401 - Google Docstring では単純なので省略
    """ApplicationConfig.xml を読み込み Config を返す。

    Args:
        path (Path): XML ファイルパス。

    Returns:
        Config: 生成された設定オブジェクト。

    Raises:
        ConfigValidationError: 不正/不足/変換失敗。
        FileNotFoundError: ファイル不存在。
    """
    if not path.exists():
        raise FileNotFoundError(path)

    try:
        tree = ET.parse(path)
    except ET.ParseError as e:  # XML シンタックスエラー
        raise ConfigValidationError(f"XML パース失敗: {e}") from e

    root = tree.getroot()
    if root.tag != "ApplicationConfig":
        raise ConfigValidationError("ルート要素が ApplicationConfig ではありません")

    def _req(elem, name: str):  # 子要素取得
        child = elem.find(name)
        if child is None:
            raise ConfigValidationError(f"必須要素欠如: {name}")
        return child

    # Cameras
    cameras_elem = _req(root, "Cameras")
    camera_list: List[CameraConfig] = []
    for c in cameras_elem.findall("Camera"):
        cid = c.get("id")
        url = c.get("url")
        if not cid or not url:
            raise ConfigValidationError("Camera 要素に id/url が不足")
        camera_list.append(CameraConfig(id=cid, url=url))
    if not camera_list:
        raise ConfigValidationError("少なくとも1つの Camera が必要")

    # Model
    model_elem = _req(root, "Model")
    model = ModelConfig(
        ir_xml=_req_attr(model_elem, "xml"),
        ir_bin=_req_attr(model_elem, "bin"),
        metadata=_req_attr(model_elem, "metadata"),
    )

    # Inference
    inf_elem = _req(root, "Inference")
    inference = InferenceConfig(
        target_fps=_int_attr(inf_elem, "target_fps", min_value=1),
        device=_req_attr(inf_elem, "device"),
    )

    # Retry
    retry_elem = _req(root, "Retry")
    retry = RetryConfig(
        connect_max_attempts=_int_attr(retry_elem, "connect_max_attempts", min_value=0),
        connect_backoff_sec=_float_attr(
            retry_elem, "connect_backoff_sec", min_value=0.0
        ),
    )

    # Buffer
    buffer_elem = _req(root, "Buffer")
    buffer = BufferConfig(
        results_max_entries=_int_attr(buffer_elem, "results_max_entries", min_value=1),
    )

    # Recording
    rec_elem = _req(root, "Recording")
    recording = RecordingConfig(
        enabled=_bool_attr(rec_elem, "enabled"),
        output_dir=_req_attr(rec_elem, "output_dir"),
    )

    # Export
    exp_elem = _req(root, "Export")
    export = ExportConfig(default_format=_req_attr(exp_elem, "default_format"))

    # Restart
    res_elem = _req(root, "Restart")
    restart = RestartConfig(
        max_restarts_per_camera=_int_attr(
            res_elem, "max_restarts_per_camera", min_value=0
        ),
        restart_window_sec=_int_attr(res_elem, "restart_window_sec", min_value=1),
    )

    # Health
    health_elem = _req(root, "Health")
    health = HealthConfig(
        ping_interval_sec=_int_attr(health_elem, "ping_interval_sec", min_value=1),
        ping_timeout_sec=_int_attr(health_elem, "ping_timeout_sec", min_value=1),
        ping_loss_threshold=_int_attr(health_elem, "ping_loss_threshold", min_value=1),
    )

    # Perf
    perf_elem = _req(root, "Perf")
    perf = PerfConfig(
        latency_p95_target_ms=_int_attr(
            perf_elem, "latency_p95_target_ms", min_value=1
        ),
        drop_rate_warn=_float_attr(
            perf_elem, "drop_rate_warn", min_value=0.0, max_value=1.0
        ),
    )

    # GUI
    gui_elem = _req(root, "GUI")
    gui = GUIConfig(theme=_req_attr(gui_elem, "theme"))

    # Logging
    log_elem = _req(root, "Logging")
    logging_cfg = LoggingConfig(
        dir=_req_attr(log_elem, "dir"), level=_req_attr(log_elem, "level")
    )

    return Config(
        cameras=camera_list,
        model=model,
        inference=inference,
        retry=retry,
        buffer=buffer,
        recording=recording,
        export=export,
        restart=restart,
        health=health,
        perf=perf,
        gui=gui,
        logging=logging_cfg,
    )


# ------------------------------ 補助関数 ------------------------------ #


def _req_attr(elem, name: str) -> str:
    v = elem.get(name)
    if v is None or v == "":
        raise ConfigValidationError(f"属性 {name} が不足")
    return v


def _int_attr(
    elem, name: str, *, min_value: int | None = None, max_value: int | None = None
) -> int:
    raw = _req_attr(elem, name)
    try:
        val = int(raw)
    except ValueError as e:
        raise ConfigValidationError(f"属性 {name} は int である必要: '{raw}'") from e
    if min_value is not None and val < min_value:
        raise ConfigValidationError(f"属性 {name} が下限 {min_value} 未満: {val}")
    if max_value is not None and val > max_value:
        raise ConfigValidationError(f"属性 {name} が上限 {max_value} 超過: {val}")
    return val


def _float_attr(
    elem, name: str, *, min_value: float | None = None, max_value: float | None = None
) -> float:
    raw = _req_attr(elem, name)
    try:
        val = float(raw)
    except ValueError as e:
        raise ConfigValidationError(f"属性 {name} は float である必要: '{raw}'") from e
    if min_value is not None and val < min_value:
        raise ConfigValidationError(f"属性 {name} が下限 {min_value} 未満: {val}")
    if max_value is not None and val > max_value:
        raise ConfigValidationError(f"属性 {name} が上限 {max_value} 超過: {val}")
    return val


def _bool_attr(elem, name: str) -> bool:
    raw = _req_attr(elem, name).lower()
    if raw in {"true", "1", "yes"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    raise ConfigValidationError(f"属性 {name} は bool (true/false) である必要: '{raw}'")


__all__ = [
    "CameraConfig",
    "ModelConfig",
    "InferenceConfig",
    "RetryConfig",
    "BufferConfig",
    "RecordingConfig",
    "ExportConfig",
    "RestartConfig",
    "HealthConfig",
    "PerfConfig",
    "GUIConfig",
    "LoggingConfig",
    "Config",
    "load",
]
