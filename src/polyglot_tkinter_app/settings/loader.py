from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polyglot_tkinter_app.settings.models import (
    ApiProfile,
    ApiSettings,
    AppSettings,
    AudioSettings,
    DemoSettings,
    GeneralSettings,
    GuiSettings,
    SemanticCacheSettings,
)


DEFAULT_CONFIG: dict[str, Any] = {
    "general": {"debug": True, "save_logs": True, "log_file": "logs/polyglot.log"},
    "api": {
        "profile": "local",
        "profiles": {
            "local": {"base_url": "https://localhost/", "verify_ssl": False},
            "aws": {
                "base_url": "https://ec2-16-171-104-203.eu-north-1.compute.amazonaws.com/",
                "verify_ssl": True,
            },
            "custom": {"base_url": "https://localhost/", "verify_ssl": False},
        },
        "health_endpoint": "health/",
        "process_endpoint": "process_memory/",
        "timeout_seconds": 120,
    },
    "semantic_cache": {
        "enabled": True,
        "source_language": "ron",
        "use_transcript_memory": True,
        "domain": "demo",
        "privacy_level": "transient",
        "strategy": "context",
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "frame_duration_ms": 30,
        "vad_aggressiveness": 3,
    },
    "demo": {"enabled": False, "output_mode": "speakers", "save_artifacts": True},
    "gui": {
        "main_menu": {"window_size": "900x660", "title": "Polyglot App"},
        "splash_screen": {"window_size": "400x400"},
        "default_theme": "dark",
        "colors": {
            "background": {"light": "#f0f0f0", "dark": "#1c1c1c"},
            "text": {"light": "#000000", "dark": "#ffffff"},
            "accent": "#00a9ad",
        },
    },
}


def load_settings(filepath: str | Path = "config.json") -> AppSettings:
    raw = _load_raw_config(filepath)
    config = _deep_merge(DEFAULT_CONFIG, _normalize_legacy_config(raw))

    profiles = {
        name: ApiProfile(
            base_url=str(values.get("base_url", "https://localhost/")),
            verify_ssl=_as_bool(values.get("verify_ssl", False)),
        )
        for name, values in config["api"]["profiles"].items()
    }

    gui = config["gui"]
    return AppSettings(
        general=GeneralSettings(
            debug=_as_bool(config["general"].get("debug", True)),
            save_logs=_as_bool(config["general"].get("save_logs", True)),
            log_file=str(config["general"].get("log_file", "logs/polyglot.log")),
        ),
        api=ApiSettings(
            profile=str(config["api"].get("profile", "local")),
            profiles=profiles,
            health_endpoint=_endpoint(config["api"].get("health_endpoint", "health/")),
            process_endpoint=_endpoint(config["api"].get("process_endpoint", "process_memory/")),
            timeout_seconds=float(config["api"].get("timeout_seconds", 120)),
        ),
        semantic_cache=SemanticCacheSettings(
            enabled=_as_bool(config["semantic_cache"].get("enabled", True)),
            source_language=str(config["semantic_cache"].get("source_language", "ron")),
            use_transcript_memory=_as_bool(config["semantic_cache"].get("use_transcript_memory", True)),
            domain=str(config["semantic_cache"].get("domain", "demo")),
            privacy_level=str(config["semantic_cache"].get("privacy_level", "transient")),
            strategy=str(config["semantic_cache"].get("strategy", "context")),
        ),
        audio=AudioSettings(
            sample_rate=int(config["audio"].get("sample_rate", 16000)),
            channels=int(config["audio"].get("channels", 1)),
            frame_duration_ms=int(config["audio"].get("frame_duration_ms", 30)),
            vad_aggressiveness=int(config["audio"].get("vad_aggressiveness", 3)),
        ),
        demo=DemoSettings(
            enabled=_as_bool(config["demo"].get("enabled", False)),
            output_mode=str(config["demo"].get("output_mode", "speakers")),
            save_artifacts=_as_bool(config["demo"].get("save_artifacts", True)),
        ),
        gui=GuiSettings(
            main_window_size=str(gui.get("main_menu", {}).get("window_size", "900x660")),
            splash_window_size=str(gui.get("splash_screen", {}).get("window_size", "400x400")),
            title=str(gui.get("main_menu", {}).get("title", "Polyglot App")),
            default_theme=str(gui.get("default_theme", "dark")),
            colors=dict(gui.get("colors", {})),
        ),
    )


def _load_raw_config(filepath: str | Path) -> dict[str, Any]:
    path = Path(filepath)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_legacy_config(raw: dict[str, Any]) -> dict[str, Any]:
    api = raw.get("api", {})
    if "profiles" in api:
        return raw

    normalized = dict(raw)
    if api:
        normalized["api"] = {
            **api,
            "profile": "local" if _as_bool(raw.get("general", {}).get("debug", True)) else "aws",
            "profiles": {
                "local": {
                    "base_url": api.get("base_url_local", "https://localhost/"),
                    "verify_ssl": False,
                },
                "aws": {
                    "base_url": api.get(
                        "base_url",
                        "https://ec2-16-171-104-203.eu-north-1.compute.amazonaws.com/",
                    ),
                    "verify_ssl": True,
                },
                "custom": {
                    "base_url": api.get("base_url_local", "https://localhost/"),
                    "verify_ssl": False,
                },
            },
        }
    return normalized


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _endpoint(value: Any) -> str:
    text = str(value).strip("/")
    return f"{text}/"
