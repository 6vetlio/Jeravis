# Jarvis - Advanced Local AI Assistant

A powerful AI voice assistant with multi-model routing, vision analysis, autonomous thinking, and PC control. Jarvis supports both local and remote Ollama instances for flexible deployment.

## Features

### AI & Models
- **Multi-Model Routing**: Automatically selects best model based on query complexity
  - `qwen2.5:7b` - Tiny one-word prompts under 15 characters
  - `qwen2.5:14b` - Default conversational model
  - `qwen2.5:32b` - Long detailed analysis prompts over 300 characters
  - `qwen2.5-coder:32b-instruct-q4_K_M` - Coding/debug/error/bug/python/script/function/implement queries
  - `llava:latest` - Vision/image analysis
- **Smart Model Selection**: Routes normal conversation to 14B by default, with narrow rules for 7B, coder 32B, and large 32B
- **GPU Optimization**: Configurable GPU layer allocation per model
- **Model Unloading**: Automatically unloads models on app close to free RAM
- **External API Support**: OpenAI, Anthropic, Kimi, SWE API integration

### Voice & Audio
- **Voice Input**: Whisper-based speech recognition via SpeechRecognition
- **Voice Output**: Kokoro TTS with multiple voices and speed control
- **Interruptible**: Can be interrupted mid-speech with voice commands
- **Fuzzy Wake Word**: Supports aliases like "Dioris" for wake-word detection
- **Voice Speed Control**: Adjustable playback speed (1.0x, 1.5x, 2.0x, skip mode)
- **Microphone Selection**: Auto-selects from available microphones

### Vision & Screenshots
- **Screenshot Analysis**: Capture and analyze screenshots with vision model
- **Screenshot Verification**: Pre/post-action screenshots for PC action verification
- **Vision Toggle**: Enable/disable vision verification mode
- **Screenshot History**: View recent screenshots with descriptions

### Autonomous Mode
- **Independent Thinking**: Jarvis thinks proactively without user input
- **Custom Prompts**: Configurable autonomous thinking prompts
- **Circuit Breaker**: Auto-pauses after 3 consecutive errors to prevent loops
- **Manual Control**: Pause/resume autonomous mode via GUI
- **Thinking Display**: Live output streams into the embedded thinking panel and popup window

### Safety & Security
- **Sandbox Mode**: Simulates PC actions without execution
- **File Protection**: Configurable file operation safety
- **Action Confirmation**: Require confirmation before executing PC actions
- **Action Logging**: Detailed logging of all PC actions
- **Rollback Support**: Revert to previous settings if needed
- **Safety Mode Toggle**: Enable/disable safety guidelines

### PC Control
- **PowerShell Execution**: Execute commands on local machine
- **Network Isolation**: Sandbox network access for security
- **Action Queue**: Multi-task processing with queue management
- **Local or Remote Ollama**: Use local GPU or connect to remote Ollama instances (Vast.ai, cloud servers)
- **Smart Connection**: Auto-detects online Ollama and prompts user for local/remote choice on failure
- **File Operations**: Create, edit, save files via PC actions

### Memory & Knowledge
- **Persistent Memory**: Remembers facts across sessions via `memory.json`
- **Personality Learning**: Adapts personality based on user feedback
- **Key Moments**: Records important conversation moments
- **Conversation History**: Full chat history with timestamps
- **Memory Management**: Add, view, and manage stored facts

### GUI Features
- **Full Button Bar**: Roll, Net, Log, Conf, Mem, Model, DB, API, WS, Stats, Export, Mini, Sound, Theme, Cmds, Plugins, Search, Prompts, Undo, Vis
- **Theme System**: Multiple themes (Dark, Light, Cyberpunk) with custom theme support
- **Mini Mode**: Compact UI for reduced screen space
- **Sound Effects**: Toggle UI sound effects
- **Status Bar**: Real-time RAM/VRAM monitoring, safety status, autonomous mode status
- **Thinking Panel**: Embedded and popup thinking views with live streaming output
- **Quick Actions**: Predefined shortcuts for common tasks

### Advanced Features
- **Direct Skills**: Weather (wttr.in) and location (ipinfo.io) without LLM routing
- **Music Control**: Play/stop YouTube music via voice commands
- **Image Generation**: Generate images via Stable Diffusion
- **WebSocket Support**: Enable/disable WebSocket server for remote access
- **API Server**: Enable/disable Flask API for web interface
- **Database**: Persistent storage for extended functionality
- **Plugins**: Extensible plugin system
- **Voice Commands**: Custom voice command shortcuts
- **Search**: Search through conversation history
- **Export**: Export settings and conversation history

### Monitoring & Debugging
- **RAM/VRAM Monitoring**: Real-time system resource usage in status bar
- **Statistics**: View usage statistics and metrics
- **Debug Logging**: Detailed debug log for troubleshooting
- **Auto Copy**: Auto-copy conversation log to debug file
- **Error Handling**: Robust error handling with fallback mechanisms

## Requirements

- Python 3.11
- Ollama with models installed (qwen2.5:7b, qwen2.5:14b, qwen2.5:32b, qwen2.5-coder:32b-instruct-q4_K_M, llava:latest)
- Windows (PowerShell for PC control)
- Microphone
- RTX 4070 (12GB VRAM) or equivalent GPU recommended for large models
- 32GB RAM recommended for 32B models

## Installation

### Local Installation (Windows)
1. Install Ollama: https://ollama.com
2. Pull required models:
   ```powershell
   ollama pull qwen2.5:7b
   ollama pull qwen2.5:14b
   ollama pull qwen2.5:32b
   ollama pull qwen2.5-coder:32b-instruct-q4_K_M
   ollama pull llava:latest
   ```
3. Install Python dependencies:
   ```powershell
   pip install ollama kokoro-onnx sounddevice SpeechRecognition requests pyperclip pillow psutil
   ```
4. Download Kokoro TTS models (not included in repository due to size):
   - Download `kokoro-v1.0.onnx` (~325MB) and `voices-v1.0.bin` (~28MB)
   - Place both files in the same directory as `assistant_gui.py`
   - Model source: https://github.com/remsky/Kokoro-FastAPI

### Remote Server Setup (Linux/Vast.ai) - RECOMMENDED for 32B models

For running Ollama on a remote GPU server (e.g., Vast.ai, Akamai) with better performance:

1. SSH into your remote instance
2. Use the provided `system initialization.txt` script:
   ```bash
   bash "system initialization.txt"
   ```
   This will:
   - Update system packages
   - Install Ollama
   - Start Ollama on port 8081 (configurable)
   - Pull all required models
3. **Configure via GUI**: Open Jarvis → Settings → API Settings → enter your Ollama Host URL
   - Direct connection: `http://your-remote-ip:8081`
   - Bare host values like `your-remote-ip:8081` are normalized to `http://your-remote-ip:8081`
   - Trailing slashes are removed automatically
   - Empty host values fall back to `http://127.0.0.1:11434`
   - Or use SSH tunnel for security (see below)

4. **Jarvis startup behavior**:
   - Jarvis checks the configured Ollama host at startup
   - If the configured host is accessible, uses it automatically
   - If the configured host fails, shows GUI dialog with 3 options:
     - Start Local Ollama
     - Reconfigure Online URL
     - Continue Without Ollama (retry on first request)
   - Starting local Ollama switches the host to `http://127.0.0.1:11434`

**SSH Tunnel (more secure):**
```bash
ssh -p <ssh-port> root@remote-ip -L 8081:localhost:8081
```
Then use `OLLAMA_HOST = "http://127.0.0.1:8081"`

**Coding model pull command:**
```bash
ollama pull qwen2.5-coder:32b-instruct-q4_K_M
```

## Usage

### GUI Version (Recommended)
Run Jarvis with the full graphical interface:
```powershell
py -3.11 C:\Users\svet\Documents\GitHub\Жаравиз\assistant_gui.py
```

### CLI Version (No GUI)
Run Jarvis in the terminal:
```powershell
py -3.11 C:\Users\svet\Documents\GitHub\Жаравиз\assistant.py
```

### Voice Activation
Activate Jarvis by saying **"Jarvis"** or using fuzzy aliases:
- "Jervis"
- "Jarves"
- "Jarviss"
- "Dioris" (common misrecognition)

You can also type messages directly without the wake word.

## Jarvis Runtime Notes

### Ollama Host
Jarvis supports both local and remote Ollama. Configure the host in **Settings → API Settings → Ollama Host URL**.

Host values are normalized automatically:
- Missing `http://` or `https://` is treated as `http://`
- Trailing slash is removed
- Empty host falls back to `http://127.0.0.1:11434`

The normalized host is applied to the running process through `OLLAMA_HOST`.

### Startup Behavior
At launch, Jarvis tests the configured Ollama host.

- If the host responds, Jarvis uses it and warms the model in the background
- If the host fails, Jarvis offers to start local Ollama, reconfigure the online URL, or continue without Ollama
- Choosing local switches the runtime host to `http://127.0.0.1:11434`

### Model Routing
Jarvis routes prompts by intent. Coding keywords are checked first.

- Coding/debug/error/bug/python/script/function/implement queries → `qwen2.5-coder:32b-instruct-q4_K_M`
- Long detailed analysis over 300 characters containing detail/explain/analyze/comprehensive → `qwen2.5:32b`
- Tiny non-coding one-word prompts under 15 characters → `qwen2.5:7b`
- Normal conversation → `qwen2.5:14b`

Jarvis receives the actual active model name in the system prompt:
`You are currently running on: <model>`

Fallback requests rebuild the prompt with the fallback model name, so model self-reporting stays accurate.

### Thinking Stream
The thinking panel streams live output during generation in both the embedded panel and popup window. If generation is cancelled, partial output remains visible and is marked interrupted.

### Persona
Jarvis uses a direct hard-rules system prompt. It should not end with customer-service closers, fake apologies, or filler. It answers what was asked, then stops.

## Model Configuration

### GPU Layer Allocation
Models are configured with specific GPU layer allocations in `config.py`:

```python
MODEL_CONFIG = {
    "qwen2.5:7b": {"num_gpu": 99, "num_thread": 12},
    "qwen2.5:14b": {"num_gpu": 99, "num_thread": 12},
    "qwen2.5:32b": {"num_gpu": 99, "num_thread": 12, "num_ctx": 4096},
    "qwen2.5-coder:32b-instruct-q4_K_M": {"num_gpu": 99, "num_thread": 12, "num_ctx": 4096},
    "llava:latest": {"num_gpu": 99, "num_thread": 12},
}
```

### Smart Routing Logic
Queries are automatically routed to the appropriate model:
- **Coding queries** containing `code`, `script`, `function`, `python`, `debug`, `implement`, `error`, or `bug` → `qwen2.5-coder:32b-instruct-q4_K_M`
- **Long detailed analysis** over 300 characters containing `detail`, `explain`, `analyze`, or `comprehensive` → `qwen2.5:32b`
- **Tiny non-coding one-word prompts** under 15 characters → `qwen2.5:7b`
- **Default conversation** → `qwen2.5:14b`

## Direct Skills

Jarvis bypasses the LLM for certain queries for faster, more accurate responses:

### Weather
- Ask: "What's the weather?" or "Jarvis what's the weather in London?"
- Uses wttr.in API with 4-second timeout
- Returns current conditions with temperature and feels-like

### Location
- Ask: "Where am I?" or "Jarvis what's my location?"
- Uses ipinfo.io API with 4-second timeout
- Returns city, region, country, coordinates, and timezone

## PC Control

Jarvis can execute PowerShell commands on your local machine. Prefix commands with `[PC_ACTION]:`:

```
Jarvis: [PC_ACTION]: Get-Process
```

### Safety Features
- **Sandbox Mode**: Simulates actions without execution
- **File Protection**: Configurable file operation safety
- **Action Confirmation**: Require confirmation before execution
- **Action Logging**: Detailed logging of all actions
- **Screenshot Verification**: Pre/post-action screenshots for verification

## Autonomous Mode

Jarvis can think independently without user input:

- **Proactive Thinking**: Thinks about what could help the user
- **Custom Prompts**: Configurable thinking prompts (proactive, reactive, creative)
- **Circuit Breaker**: Auto-pauses after 3 consecutive errors to prevent loops
- **Manual Control**: Pause/resume via Auto button in GUI
- **Thinking Display**: Real-time visualization of thinking process

## Configuration

Key constants in `assistant_gui.py`:

```python
# Models
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_SECONDARY_MODEL = "qwen2.5:14b"
OLLAMA_LARGE_MODEL = "qwen2.5:32b"
OLLAMA_CODING_MODEL = "qwen2.5-coder:32b-instruct-q4_K_M"
VISION_MODEL = "llava:latest"

# Ollama Settings (can also be set via GUI: Settings → API Settings)
OLLAMA_HOST = "http://127.0.0.1:11434"  # Or remote: http://your-server:8081
OLLAMA_KEEP_ALIVE = "5m"  # Keep model warm for 5 minutes
OLLAMA_RETRY_COUNT = 3

# Voice Settings
MIC_CALIBRATION_SECONDS = 0.6
LISTEN_TIMEOUT_SECONDS = 6
LISTEN_PHRASE_LIMIT_SECONDS = 16
MAX_TTS_CHARS = 280  # Cap spoken output to avoid Kokoro crashes
WAKE_WORD = "jarvis"
WAKE_WORD_SIMILARITY_THRESHOLD = 0.72
```

## Troubleshooting

### "Can't find my brain" / Connection Errors

**For Local Ollama:**
- Ensure Ollama is running: check if `ollama.exe` is accessible
- Verify models are installed: `ollama pull qwen2.5:7b`
- Check Ollama is accessible at `http://127.0.0.1:11434`

**For Remote Ollama (Vast.ai, cloud servers):**
- Check that remote Ollama is running: `curl http://<IP>:<PORT>/api/tags`
- Verify the port is correct (Vast.ai often uses different exposed ports like 14342)
- Check firewall rules on remote server: `sudo ufw allow <PORT>/tcp`
- Ensure Ollama is listening on 0.0.0.0 (all interfaces), not just localhost
- Try SSH tunnel if direct connection fails: `ssh -p <SSH-PORT> root@<IP> -L 8081:localhost:8081 -N`
- **GUI Configuration**: Settings → API Settings → enter Ollama Host URL
- If startup check fails, Jarvis will show connection choice dialog with 3 options

### Model OOM Crashes (Status 500)
- Large models (32B) may exceed VRAM on 8GB cards
- Jarvis automatically falls back to qwen2.5:7b on crash
- Adjust `MODEL_CONFIG` if your GPU cannot keep the 32B models resident
- Use the 14B model for normal conversation when 32B is unnecessary

### Voice Cutoffs
- If Jarvis cuts you off too early, adjust thresholds:
  - Increase `LISTEN_PHRASE_LIMIT_SECONDS` (currently 16)
  - Increase `pause_threshold` (currently 0.6)
  - Increase `non_speaking_duration` (currently 0.35)

### TTS Crashes
- Long responses are automatically truncated to `MAX_TTS_CHARS` (280)
- TTS speed is clamped to Kokoro's valid range (`0.5` to `2.0`)
- The GUI speed cycle uses `1.0x`, `1.5x`, `2.0x`, and skip mode
- If TTS still crashes, reduce `MAX_TTS_CHARS` further

### Wake Word Not Detected
- Try the fuzzy aliases: "Jervis", "Jarves", "Jarviss", "Dioris"
- If needed, lower `WAKE_WORD_SIMILARITY_THRESHOLD` (currently 0.72)

### Weather/Location Not Working
- Check internet connectivity (wttr.in and ipinfo.io require network)
- Verify API services are accessible (no blocking)
- Check timeout settings: `WEATHER_TIMEOUT_SECONDS = 4`, `LOCATION_TIMEOUT_SECONDS = 4`

### High RAM Usage
- Models are kept in memory for 5 minutes after use (OLLAMA_KEEP_ALIVE)
- Jarvis automatically unloads models on app close
- Use smaller models (7B, 14B) for frequent queries
- 32B models require ~20GB RAM, ensure sufficient system memory

## Hardware Context

Tested on:
- Windows with RTX 4070 (12GB VRAM) and 32GB RAM
- Microphone: Steinberg UR22mkII (device index 1)
- Ollama executable path: `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`

## Development History

### Phase 3: Jarvis Polish Pass (Latest)
- Normal conversation now routes to `qwen2.5:14b`; `qwen2.5:7b` is only for tiny one-word prompts
- Coding routing is restricted to explicit coding/debug keywords
- The active model name is injected into the system prompt so Jarvis can report it accurately
- Thinking output streams live into the embedded panel and popup
- Cancelling generation keeps partial output visible and marks it interrupted
- Duplicate normal Jarvis messages were removed from the display path
- Kokoro TTS speed is clamped to the valid `0.5` to `2.0` range
- Ollama host values are normalized and applied to `OLLAMA_HOST`
- Jarvis uses the direct hard-rules persona prompt

### Phase 2: Remote Ollama Support
- Added remote Ollama instance support (Vast.ai, cloud servers)
- Rewrote all Ollama API calls to use direct HTTP requests via `requests` library
- Added `OLLAMA_HOST` environment variable configuration at startup
- Added startup connectivity check with GUI choice dialog (local/remote/retry)
- Removed automatic local Ollama startup (now user-choice via GUI)
- Added Ollama Host URL field to API Settings dialog
- Added connection test button using direct HTTP (not ollama library)
- Fixed automatic conversation history saving to `conversation_history.txt`
- Updated system initialization script with port 8081 and connection instructions

### Phase 1: Critical Bug Fixes
- Fixed thinking box streaming with chunk_callback and tkinter after(0)
- Fixed qwen2.5:32b VRAM OOM by reducing GPU layers and context window
- Demoted qwen2.5:32b to only trigger on explicitly complex queries
- Added llama runner crash (status 500) detection and fallback to qwen2.5:7b
- Added autonomous mode circuit breaker (pause after 3 consecutive errors)
- Confirmed codellama:34b removal (replaced with qwen2.5-coder:32b-instruct-q4_K_M)

### Previous Features
- Multi-model routing with smart selection
- RAM/VRAM monitoring in status bar
- Model unloading on app close
- GPU layer allocation optimization
- Connection reset error handling
- Autonomous mode with thinking display
- Sandbox mode and file protection
- Vision analysis with llava
- Screenshot verification system
- Theme system and mini mode
- Plugin system and voice commands
- WebSocket and API server support
- IDE integration with code editor

## License

Personal project for local AI assistant development.
