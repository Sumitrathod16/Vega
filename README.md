# Vega

Vega is a voice-first desktop assistant powered by Ollama.

## Install on Windows

From this folder, run one command in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer creates `.venv`, installs Python dependencies, installs Ollama through `winget` when needed, and downloads the `llama3.2:3b` and `moondream` models.

Start Vega with:

```powershell
.\run.ps1
```

Ollama runs locally. Conversation history is stored in `~/.vega/memory.db`. To share history between devices, set the same `VEGA_USER_ID` and configure `VEGA_MEMORY_URL` for a shared memory service on every device.
