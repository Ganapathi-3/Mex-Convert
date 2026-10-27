"""
Application configuration for Citrus Converter.

Provides both a dataclass-based ``AppConfig`` and a simpler dict-like
``Config`` wrapper that the GUI and CLI can use interchangeably.

Reads/writes a JSON config file at ~/.config/citrus-converter/config.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

_CONFIG_DIR = Path.home() / ".config" / "citrus-converter"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# Default values
_DEFAULTS = {
    "output_location": "same",
    "output_custom_path": "",
    "default_quality": 85,
    "theme": "dark",
    "notifications": True,
    "confirm_overwrite": True,
    "start_in_background": True,
    "navigation_sound": True,
}


class Config:
    """Simple dict-like configuration backed by a JSON file.

    Usage::

        cfg = Config()
        theme = cfg.get("theme", "dark")
        cfg.set("theme", "light")
        cfg.save()
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._load()

    def _load(self) -> None:
        """Load config from disk, merging with defaults."""
        if _CONFIG_FILE.exists():
            try:
                data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._data.update(data)
            except (json.JSONDecodeError, OSError):
                pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value (call ``save()`` to persist)."""
        self._data[key] = value

    def save(self) -> None:
        """Persist the current configuration to disk."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(
            json.dumps(self._data, indent=2) + "\n",
            encoding="utf-8",
        )

    def resolve_output_dir(self, input_path: str | Path) -> Path:
        """Return the output directory for a given input file.

        Returns:
            Path to the target directory.

        Raises:
            ValueError: If ``output_location`` is *ask* (the caller must
                        prompt the user first).
        """
        input_path = Path(input_path)
        mode = self.get("output_location", "same")

        if mode == "custom":
            custom = self.get("output_custom_path", "")
            if custom:
                out = Path(custom)
                out.mkdir(parents=True, exist_ok=True)
                return out

        if mode == "ask":
            raise ValueError(
                "output_location is 'ask' — the caller must prompt the user."
            )

        # Default: same folder as input
        return input_path.parent


# ── Legacy dataclass API (kept for compatibility) ────────────────────────────


@dataclass
class AppConfig:
    """Global application settings persisted as JSON (dataclass form)."""

    output_location: Literal["same", "custom", "ask"] = "same"
    custom_output_dir: str = ""
    default_quality: int = 85
    theme: Literal["light", "dark", "system"] = "dark"
    show_notifications: bool = True
    confirm_overwrite: bool = True

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from disk, creating defaults if missing."""
        if _CONFIG_FILE.exists():
            try:
                data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
                valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
                filtered = {k: v for k, v in data.items() if k in valid_keys}
                return cls(**filtered)
            except (json.JSONDecodeError, TypeError):
                cfg = cls()
                cfg.save()
                return cfg
        else:
            cfg = cls()
            cfg.save()
            return cfg

    def save(self) -> None:
        """Persist the current configuration to disk."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(
            json.dumps(asdict(self), indent=2) + "\n",
            encoding="utf-8",
        )
