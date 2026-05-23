from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests
import urllib3


def send_request(url: str, audio_path: Path, language: str, endpoint: str = "process_memory") -> tuple[float, str]:
    start = time.perf_counter()
    with audio_path.open("rb") as handle:
        files = {"file": ("sample.wav", handle, "audio/wav")}
        data = {
            "language": language,
            "speaker_id": "0",
            "session_id": "performance-test",
            "domain": "demo",
            "privacy_level": "transient",
            "use_semantic_cache": "true",
            "cache_strategy": "context",
        }
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(f"{url.rstrip('/')}/{endpoint}", files=files, data=data, verify=False, timeout=120)
    response.raise_for_status()
    return time.perf_counter() - start, response.headers.get("X-Polyglot-Cache", "unknown")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local semantic-cache performance smoke test.")
    parser.add_argument("--url", default="https://localhost")
    parser.add_argument("--audio", default=str(Path(__file__).with_name("sample2.wav")))
    parser.add_argument("--language", default="ron")
    parser.add_argument("--iterations", type=int, default=2)
    args = parser.parse_args()

    audio_path = Path(args.audio)
    for index in range(args.iterations):
        elapsed, cache_status = send_request(args.url, audio_path, args.language)
        print(f"request={index + 1} cache={cache_status} elapsed={elapsed:.3f}s")


if __name__ == "__main__":
    main()
