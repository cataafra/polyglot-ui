from polyglot_tkinter_app.audio.devices import AudioDevice, AudioDeviceRegistry


def test_audio_device_from_info():
    device = AudioDevice.from_info(
        {
            "index": 3,
            "name": "Speakers",
            "maxInputChannels": 0,
            "maxOutputChannels": 2,
            "defaultSampleRate": 48000.0,
        }
    )

    assert device.index == 3
    assert device.name == "Speakers"
    assert device.input_channels == 0
    assert device.output_channels == 2
    assert device.sample_rate == 48000


def test_find_virtual_cable_output(monkeypatch):
    registry = AudioDeviceRegistry()
    monkeypatch.setattr(
        registry,
        "list_output_devices",
        lambda: [
            AudioDevice(index=1, name="Speakers", output_channels=2),
            AudioDevice(index=2, name="CABLE Input (VB-Audio Virtual Cable)", output_channels=2),
        ],
    )

    assert registry.find_virtual_cable_output().index == 2
