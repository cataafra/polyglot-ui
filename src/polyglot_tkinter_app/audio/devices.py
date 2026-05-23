from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    input_channels: int = 0
    output_channels: int = 0
    sample_rate: int | None = None

    @classmethod
    def from_info(cls, info: dict[str, Any]) -> "AudioDevice":
        default_rate = info.get("defaultSampleRate")
        return cls(
            index=int(info.get("index", -1)),
            name=str(info.get("name", "Unknown device")),
            input_channels=int(info.get("maxInputChannels", 0)),
            output_channels=int(info.get("maxOutputChannels", 0)),
            sample_rate=int(default_rate) if default_rate else None,
        )

    def display_name(self) -> str:
        return self.name


class AudioDeviceRegistry:
    def list_input_devices(self) -> list[AudioDevice]:
        return [device for device in self._list_devices() if device.input_channels > 0]

    def list_output_devices(self) -> list[AudioDevice]:
        return [device for device in self._list_devices() if device.output_channels > 0]

    def get_default_input_device(self) -> AudioDevice | None:
        pyaudio = _load_pyaudio()
        p = pyaudio.PyAudio()
        try:
            return AudioDevice.from_info(p.get_default_input_device_info())
        except Exception:
            devices = self.list_input_devices()
            return devices[0] if devices else None
        finally:
            p.terminate()

    def get_default_output_device(self) -> AudioDevice | None:
        pyaudio = _load_pyaudio()
        p = pyaudio.PyAudio()
        try:
            return AudioDevice.from_info(p.get_default_output_device_info())
        except Exception:
            devices = self.list_output_devices()
            return devices[0] if devices else None
        finally:
            p.terminate()

    def find_virtual_cable_output(self) -> AudioDevice | None:
        for device in self.list_output_devices():
            name = device.name.lower()
            if "cable input" in name or "vb-audio" in name:
                return device
        return None

    def _list_devices(self) -> list[AudioDevice]:
        pyaudio = _load_pyaudio()
        p = pyaudio.PyAudio()
        try:
            return [AudioDevice.from_info(p.get_device_info_by_index(index)) for index in range(p.get_device_count())]
        finally:
            p.terminate()


def _load_pyaudio() -> Any:
    try:
        import pyaudio

        return pyaudio
    except ImportError as exc:
        raise RuntimeError("PyAudio is required for audio device discovery") from exc
