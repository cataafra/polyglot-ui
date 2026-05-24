# Polyglot Tkinter App

Tkinter desktop client for the Polyglot speech-to-speech translation backend.

The normal user flow is intentionally simple: select a microphone, select the target language, start recording, and send translated audio to VB-Audio Cable. Demo Mode keeps the same dashboard style but exposes the controls needed to present the semantic-cache thesis work.

## Run

```powershell
python main.py
```

For the local Docker backend, `config.json` defaults to:

```text
https://localhost/process_memory/
```

with SSL verification disabled for the self-signed local certificate.

## Modes

- `User`: microphone input, target language/voice selection, automatic VB-Audio Cable output.
- `Demo`: adds output-device selection, backend profile, source speech language, transcript-memory toggle, cache strategy, domain/privacy fields, session reset, resend/replay controls, cache metrics, and a rolling event log.

## Demo Flow

1. Start the backend semantic stack.
2. Run `python main.py`.
3. Switch to `Demo`.
4. Select your microphone and speaker output.
5. Set `Source Speech` explicitly, for example Romanian when saying `câine`.
6. Keep semantic cache and transcript memory enabled with strategy `context`.
7. Record a phrase and wait for translated playback.
8. Repeat the same word naturally, or use `Resend Last Input` as a deterministic fallback.

The metrics card shows whether the response came from AI inference, audio exact reuse, transcript exact reuse, transcript vector reuse, or audio vector reuse, including separate lookup, transcript, inference, and total timing.

## Tests

```powershell
python -m pytest -q
```

Optional backend integration test:

```powershell
$env:POLYGLOT_RUN_INTEGRATION="1"
python -m pytest -q tests/integration
```

## Demo Artifacts

When Demo Mode artifact saving is enabled, the app writes:

```text
outputs/latest-input.wav
outputs/latest-output.wav
headers/latest-response.json
logs/polyglot.log
```
