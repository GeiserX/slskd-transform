"""Configuration loading for slskd-transform."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


DEFAULTS: dict[str, object] = {
    "host": "http://127.0.0.1:5030",
    "api_key": "",
    "verify_ssl": False,
    "music_dir": "./music",
    "source_dir": "./downloads",
    "destination_dir": "./organized",
    "duration_tolerance": 15,
    "num_threads": 5,
    "search_timeout": 60,
    "format": "flac",
    "recursive": False,
}

_ENV_MAP: dict[str, str] = {
    "SLSKD_HOST": "host",
    "SLSKD_API_KEY": "api_key",
    "SLSKD_VERIFY_SSL": "verify_ssl",
    "SLSKD_MUSIC_DIR": "music_dir",
    "SLSKD_SOURCE_DIR": "source_dir",
    "SLSKD_DESTINATION_DIR": "destination_dir",
    "SLSKD_DURATION_TOLERANCE": "duration_tolerance",
    "SLSKD_NUM_THREADS": "num_threads",
    "SLSKD_SEARCH_TIMEOUT": "search_timeout",
    "SLSKD_FORMAT": "format",
    "SLSKD_RECURSIVE": "recursive",
}

_BOOL_FIELDS = {"verify_ssl", "recursive"}
_INT_FIELDS = {"duration_tolerance", "num_threads", "search_timeout"}
_PATH_FIELDS = {"music_dir", "source_dir", "destination_dir"}


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class SlskdConfig:
    host: str = "http://127.0.0.1:5030"
    api_key: str = ""
    verify_ssl: bool = False
    music_dir: Path = Path("./music")
    source_dir: Path = Path("./downloads")
    destination_dir: Path = Path("./organized")
    duration_tolerance: int = 15
    num_threads: int = 5
    search_timeout: int = 60
    format: str = "flac"
    recursive: bool = False


def load_config(
    *,
    config_path: Path | None = None,
    cli_overrides: dict[str, object] | None = None,
) -> SlskdConfig:
    """Load configuration from YAML, env vars, and CLI overrides."""
    merged: dict[str, object] = dict(DEFAULTS)

    # Load YAML file
    file_data = _load_yaml(config_path)
    for key, value in file_data.items():
        if key in DEFAULTS:
            merged[key] = value

    # Overlay environment variables
    for env_var, field in _ENV_MAP.items():
        value = os.environ.get(env_var)
        if value is not None:
            merged[field] = value

    # Overlay CLI overrides
    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and key in DEFAULTS:
                merged[key] = value

    # Convert types
    for field in _BOOL_FIELDS:
        merged[field] = _parse_bool(merged[field])
    for field in _INT_FIELDS:
        merged[field] = int(merged[field])  # type: ignore[arg-type]
    for field in _PATH_FIELDS:
        merged[field] = Path(str(merged[field]))

    return SlskdConfig(**merged)  # type: ignore[arg-type]


def _load_yaml(config_path: Path | None) -> dict[str, object]:
    """Load YAML config from explicit path or auto-discovered locations."""
    if config_path is not None:
        return _read_yaml(config_path)

    # Auto-discover
    candidates = [
        Path("./config.yml"),
        Path.home() / ".config" / "slskd-transform" / "config.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return _read_yaml(candidate)

    return {}


def _read_yaml(path: Path) -> dict[str, object]:
    """Read and parse a YAML file. Returns empty dict on failure."""
    if yaml is None:
        return {}
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}
