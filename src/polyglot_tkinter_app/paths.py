from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = APP_ROOT / "assets"
LOGS_DIR = APP_ROOT / "logs"
OUTPUTS_DIR = APP_ROOT / "outputs"
HEADERS_DIR = APP_ROOT / "headers"


def asset_path(filename: str) -> str:
    return str(ASSETS_DIR / filename)


def ensure_runtime_dirs() -> None:
    for directory in (LOGS_DIR, OUTPUTS_DIR, HEADERS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
