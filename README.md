# Jarvis - Advanced Local AI Assistant

A powerful local AI voice assistant with multi-model routing, vision analysis, autonomous thinking, and PC control. Jarvis runs entirely on your local machine with no cloud dependencies for core functionality.

## Features

### AI & Models
- **Multi-Model Routing**: Automatically selects best model based on query complexity
  - `qwen2.5:7b` - Fast queries, weather, simple greetings
  - `qwen2.5:14b` - Medium complexity, general purpose
  - `qwen2.5:32b` - Complex/long queries, detailed analysis (last resort)
  - `qwen2.5-coder:32b-instruct-q4_K_M` - Coding/programming queries
  - `llava:latest` - Vision/image analysis
- **Smart Model Selection**: Routes coding queries to coding model, complex to 32b, fast to 7b
- **GPU Optimization**: Configurable GPU layer allocation per model (optimized for RTX 4070 12GB VRAM)
- **Model Unloading**: Automatically unloads models on app close to free RAM
- **External API Support**: OpenAI, Anthropic, Kimi, SWE API integration

### Voice & Audio
- **Voice Input**: Whisper-based speech recognition via SpeechRecognition
- **Voice Output**: Kokoro TTS with multiple voices and speed control
- **Interruptible**: Can be interrupted mid-speech with voice commands
- **Fuzzy Wake Word**: Supports aliases like "Dioris" for wake-word detection
- **Voice Speed Control**: Adjustable playback speed (1.0x, 1.5x, 2.0x, 3.0x, skip mode)
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
- **Thinking Display**: Real-time thinking process visualization

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
- **IDE Integration**: Built-in code editor with save/open functionality
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
- **Thinking Panel**: Separate window for thinking process visualization
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

## Model Configuration

### GPU Layer Allocation
Models are configured with specific GPU layer allocations optimized for RTX 4070 12GB VRAM:

```python
MODEL_CONFIG = {
    "qwen2.5:7b": {"num_gpu": 99, "num_thread": 8},
    "qwen2.5:14b": {"num_gpu": 99, "num_thread": 8},
    "qwen2.5:32b": {"num_gpu": 33, "num_thread": 8, "num_ctx": 2048},  # Reduced to prevent OOM
    "qwen2.5-coder:32b-instruct-q4_K_M": {"num_gpu": 33, "num_thread": 8, "num_ctx": 2048},
    "llava:latest": {"num_gpu": 99, "num_thread": 8},
}
```

### Smart Routing Logic
Queries are automatically routed to the appropriate model:
- **Simple queries** (< 20 chars, weather, greetings) → qwen2.5:7b
- **Coding queries** → qwen2.5-coder:32b-instruct-q4_K_M
- **Complex queries** (> 200 chars, "comprehensive", "in-depth") → qwen2.5:32b
- **Medium complexity** (> 100 chars, "explain", "analyze") → qwen2.5:14b
- **Default** → qwen2.5:14b

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

# Ollama Settings
OLLAMA_HOST = "http://127.0.0.1:11434"
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

### "Can't find my brain" Error
- Ensure Ollama is running: check if `ollama.exe` is accessible
- Verify models are installed: `ollama pull qwen2.5:7b`
- Check Ollama is accessible at `http://127.0.0.1:11434`

### Model OOM Crashes (Status 500)
- Large models (32B) may exceed VRAM on 8GB cards
- Jarvis automatically falls back to qwen2.5:7b on crash
- GPU layer allocation is reduced for 32B models to prevent OOM
- Use 14B model instead for medium complexity queries

### Voice Cutoffs
- If Jarvis cuts you off too early, adjust thresholds:
  - Increase `LISTEN_PHRASE_LIMIT_SECONDS` (currently 16)
  - Increase `pause_threshold` (currently 0.6)
  - Increase `non_speaking_duration` (currently 0.35)

### TTS Crashes
- Long responses are automatically truncated to `MAX_TTS_CHARS` (280)
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

### Phase 1: Critical Bug Fixes (Latest)
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
